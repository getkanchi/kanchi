from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import logging
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional
import uvicorn

from models import (
    TaskEvent, TaskEventResponse, TaskStats, ConnectionInfo, 
    SubscriptionRequest, SubscriptionResponse, WebSocketMessage, WebSocketResponse,
    PongResponse, ModeChangedResponse, StoredEventsResponse,
    PingMessage, SubscribeMessage, SetModeMessage, GetStoredMessage,
    WorkerEvent, WorkerInfo
)
from monitor import CeleryEventMonitor
from config import Config

logger = logging.getLogger(__name__)

# Global state
monitor_instance: Optional[CeleryEventMonitor] = None
monitor_thread: Optional[threading.Thread] = None
task_stats = TaskStats()
recent_events: List[TaskEvent] = []
recent_worker_events: List[WorkerEvent] = []
MAX_RECENT_EVENTS = 1000
MAX_WORKER_EVENTS = 100


class ConnectionManager:
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.client_filters: Dict[WebSocket, dict] = {}
        self.client_modes: Dict[WebSocket, str] = {}  # 'live' or 'static'
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.client_filters[websocket] = {}
        self.client_modes[websocket] = 'live'
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.client_filters:
            del self.client_filters[websocket]
        if websocket in self.client_modes:
            del self.client_modes[websocket]
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message to client: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, task_event: TaskEvent):
        if not self.active_connections:
            return
        
        message = task_event.to_json()
        disconnected = []
        
        for connection in self.active_connections:
            try:
                if self.client_modes.get(connection, 'live') != 'live':
                    continue
                    
                filters = self.client_filters.get(connection, {})
                if self._should_send_to_client(task_event, filters):
                    await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)
        
        for connection in disconnected:
            self.disconnect(connection)
    
    def _should_send_to_client(self, task_event: TaskEvent, filters: dict) -> bool:
        if not filters:
            return True
        
        event_types = filters.get('event_types', [])
        if event_types and task_event.event_type not in event_types:
            return False
        
        task_names = filters.get('task_names', [])
        if task_names and task_event.task_name not in task_names:
            return False
        
        return True
    
    def set_client_filters(self, websocket: WebSocket, filters: dict):
        self.client_filters[websocket] = filters
    
    def set_client_mode(self, websocket: WebSocket, mode: str):
        if mode in ['live', 'static']:
            self.client_modes[websocket] = mode
            logger.info(f"Client mode set to: {mode}")


# Global connection manager
manager = ConnectionManager()

# Create FastAPI app
app = FastAPI(
    title="Celery Event Monitor",
    description="Real-time monitoring of Celery task events with WebSocket broadcasting",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_config() -> Config:
    return Config.from_env()


def update_stats(task_event: TaskEvent):
    global task_stats, recent_events
    
    task_stats.total_tasks += 1
    
    if task_event.event_type == 'task-succeeded':
        task_stats.succeeded += 1
    elif task_event.event_type == 'task-failed':
        task_stats.failed += 1
    elif task_event.event_type == 'task-retried':
        task_stats.retried += 1
    elif task_event.event_type == 'task-started':
        task_stats.active += 1
    elif task_event.event_type in ['task-succeeded', 'task-failed']:
        task_stats.active = max(0, task_stats.active - 1)
    
    recent_events.append(task_event)
    if len(recent_events) > MAX_RECENT_EVENTS:
        recent_events.pop(0)


async def broadcast_event(task_event: TaskEvent):
    update_stats(task_event)
    await manager.broadcast(task_event)


async def broadcast_worker_event(worker_event: WorkerEvent):
    global recent_worker_events
    
    recent_worker_events.append(worker_event)
    if len(recent_worker_events) > MAX_WORKER_EVENTS:
        recent_worker_events.pop(0)
    
    message = worker_event.model_dump_json()
    disconnected = []
    
    for connection in manager.active_connections:
        try:
            if manager.client_modes.get(connection, 'live') == 'live':
                await connection.send_text(message)
        except Exception as e:
            logger.error(f"Error broadcasting worker event to client: {e}")
            disconnected.append(connection)
    
    for connection in disconnected:
        manager.disconnect(connection)


def start_monitor(config: Config):
    global monitor_instance, monitor_thread
    
    if monitor_thread and monitor_thread.is_alive():
        logger.warning("Monitor already running")
        return
    
    logger.info(f"Starting Celery monitor with broker: {config.broker_url}")
    monitor_instance = CeleryEventMonitor(config.broker_url)
    
    def sync_broadcast(task_event: TaskEvent):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(broadcast_event(task_event))
            loop.close()
        except Exception as e:
            logger.error(f"Error in sync broadcast: {e}")
    
    monitor_instance.set_broadcast_callback(sync_broadcast)
    
    def sync_worker_broadcast(worker_event: WorkerEvent):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(broadcast_worker_event(worker_event))
            loop.close()
        except Exception as e:
            logger.error(f"Error in sync worker broadcast: {e}")
    
    monitor_instance.set_worker_broadcast_callback(sync_worker_broadcast)
    
    monitor_thread = threading.Thread(target=monitor_instance.start_monitoring)
    monitor_thread.daemon = True
    monitor_thread.start()


@app.on_event("startup")
async def startup_event():
    config = Config.from_env()
    
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format=config.log_format
    )
    
    start_monitor(config)


@app.get("/", response_class=HTMLResponse)
async def get_home():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Celery Event Monitor</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .event { margin: 10px 0; padding: 10px; border-left: 3px solid #007acc; background: #f5f5f5; }
            .succeeded { border-left-color: #28a745; }
            .failed { border-left-color: #dc3545; }
            .started { border-left-color: #ffc107; }
            #status { margin: 20px 0; font-weight: bold; }
            #events { max-height: 500px; overflow-y: auto; }
        </style>
    </head>
    <body>
        <h1>Celery Event Monitor</h1>
        <div id="status">Connecting...</div>
        <div id="events"></div>
        
        <script>
            const ws = new WebSocket(`ws://${window.location.host}/ws`);
            const status = document.getElementById('status');
            const events = document.getElementById('events');
            
            ws.onopen = function(event) {
                status.textContent = 'Connected to Celery Event Monitor';
                status.style.color = 'green';
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                
                if (data.type === 'connection') {
                    return;
                }
                
                if (data.task_id) {
                    const eventDiv = document.createElement('div');
                    eventDiv.className = `event ${data.event_type.replace('task-', '')}`;
                    eventDiv.innerHTML = `
                        <strong>${data.event_type}</strong>: ${data.task_name}[${data.task_id.substring(0, 8)}...]<br>
                        <small>Time: ${new Date(data.timestamp).toLocaleString()}</small>
                        ${data.runtime ? `<br><small>Runtime: ${data.runtime.toFixed(2)}s</small>` : ''}
                        ${data.result ? `<br><small>Result: ${JSON.stringify(data.result).substring(0, 100)}...</small>` : ''}
                    `;
                    events.insertBefore(eventDiv, events.firstChild);
                    
                    // Keep only last 50 events
                    while (events.children.length > 50) {
                        events.removeChild(events.lastChild);
                    }
                }
            };
            
            ws.onclose = function(event) {
                status.textContent = 'Disconnected';
                status.style.color = 'red';
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    welcome = ConnectionInfo(
        status="connected",
        timestamp=datetime.now(),
        message="Connected to Celery Event Monitor",
        total_connections=len(manager.active_connections)
    )
    await manager.send_personal_message(welcome.model_dump_json(), websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                if message.get('type') == 'ping':
                    pong_response = PongResponse(timestamp=datetime.now())
                    await manager.send_personal_message(pong_response.model_dump_json(), websocket)
                
                elif message.get('type') == 'subscribe':
                    filters = message.get('filters', {})
                    manager.set_client_filters(websocket, filters)
                    
                    response = SubscriptionResponse(
                        status="acknowledged",
                        filters=filters,
                        timestamp=datetime.now()
                    )
                    await manager.send_personal_message(response.model_dump_json(), websocket)
                
                elif message.get('type') == 'set_mode':
                    mode = message.get('mode', 'live')
                    manager.set_client_mode(websocket, mode)
                    
                    events_sent = 0
                    if mode == 'static':
                        for event in recent_events:
                            filters = manager.client_filters.get(websocket, {})
                            if manager._should_send_to_client(event, filters):
                                await manager.send_personal_message(event.to_json(), websocket)
                                events_sent += 1
                    
                    mode_response = ModeChangedResponse(
                        mode=mode,
                        timestamp=datetime.now(),
                        events_count=events_sent if mode == 'static' else None
                    )
                    await manager.send_personal_message(mode_response.model_dump_json(), websocket)
                
                elif message.get('type') == 'get_stored':
                    limit = message.get('limit', MAX_RECENT_EVENTS)
                    events_to_send = recent_events[-limit:] if limit < len(recent_events) else recent_events
                    
                    events_sent = 0
                    for event in events_to_send:
                        filters = manager.client_filters.get(websocket, {})
                        if manager._should_send_to_client(event, filters):
                            await manager.send_personal_message(event.to_json(), websocket)
                            events_sent += 1
                    
                    stored_response = StoredEventsResponse(
                        count=events_sent,
                        timestamp=datetime.now()
                    )
                    await manager.send_personal_message(stored_response.model_dump_json(), websocket)
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {data}")
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/api/stats", response_model=TaskStats)
async def get_task_stats():
    return task_stats


def aggregate_task_events(events: List[TaskEvent]) -> List[TaskEvent]:
    task_aggregation = {}
    for event in events:
        task_id = event.task_id
        if task_id not in task_aggregation:
            task_aggregation[task_id] = []
        task_aggregation[task_id].append(event)
    
    aggregated_tasks = []
    
    for task_id, task_events in task_aggregation.items():
        task_events.sort(key=lambda e: e.timestamp)
        
        latest_event = task_events[-1]
        aggregated_task = TaskEvent(
            task_id=task_id,
            task_name=latest_event.task_name,
            event_type=latest_event.event_type,  # Use latest status
            timestamp=latest_event.timestamp,    # Use latest timestamp
            args=latest_event.args,
            kwargs=latest_event.kwargs,
            retries=latest_event.retries,
            eta=latest_event.eta,
            expires=latest_event.expires,
            hostname=latest_event.hostname,
            exchange=latest_event.exchange,
            routing_key=latest_event.routing_key,
            root_id=latest_event.root_id,
            parent_id=latest_event.parent_id,
            result=latest_event.result,
            runtime=latest_event.runtime,
            exception=latest_event.exception,
            traceback=latest_event.traceback
        )
        
        for event in task_events:
            if event.event_type == 'task-started' and hasattr(event, 'started_at'):
                aggregated_task.started_at = event.timestamp
                break
            elif event.event_type == 'task-received' and not hasattr(aggregated_task, 'started_at'):
                aggregated_task.started_at = event.timestamp
        
        aggregated_tasks.append(aggregated_task)
    
    aggregated_tasks.sort(key=lambda e: e.timestamp, reverse=True)
    return aggregated_tasks


@app.get("/api/events/recent", response_model=Dict[str, Any])
async def get_recent_events(
    limit: int = 100, 
    page: int = 0, 
    aggregate: bool = True,
    sort_by: Optional[str] = None,
    sort_order: str = "desc",
    search: Optional[str] = None,
    filter_state: Optional[str] = None,
    filter_worker: Optional[str] = None,
    filter_task: Optional[str] = None,
    filter_queue: Optional[str] = None
):
    
    if aggregate:
        aggregated_events = aggregate_task_events(recent_events)
        
        if search:
            search_lower = search.lower()
            filtered_events = []
            for e in aggregated_events:
                if ((e.task_name and search_lower in e.task_name.lower()) or
                    (e.event_type and search_lower in e.event_type.lower()) or
                    (e.hostname and search_lower in e.hostname.lower()) or
                    (e.args and search_lower in str(e.args).lower()) or
                    (e.kwargs and search_lower in str(e.kwargs).lower()) or
                    (e.task_id and search_lower in e.task_id.lower()) or
                    (e.result and search_lower in str(e.result).lower())):
                    filtered_events.append(e)
            aggregated_events = filtered_events
        
        if filter_state:
            state_to_event_type = {
                'PENDING': 'task-sent',
                'RECEIVED': 'task-received',
                'RUNNING': 'task-started',
                'SUCCESS': 'task-succeeded',
                'FAILED': 'task-failed',
                'RETRY': 'task-retried',
                'REVOKED': 'task-revoked'
            }
            event_type_filter = state_to_event_type.get(filter_state.upper())
            if event_type_filter:
                aggregated_events = [e for e in aggregated_events if e.event_type == event_type_filter]
        
        if filter_worker:
            aggregated_events = [e for e in aggregated_events if e.hostname and filter_worker.lower() in e.hostname.lower()]
        
        if filter_task:
            aggregated_events = [e for e in aggregated_events if e.task_name and filter_task.lower() in e.task_name.lower()]
        
        if filter_queue:
            aggregated_events = [e for e in aggregated_events if e.routing_key and filter_queue.lower() in e.routing_key.lower()]
        
        if sort_by:
            reverse = (sort_order == "desc")
            if sort_by == "task_name":
                aggregated_events.sort(key=lambda e: e.task_name or "", reverse=reverse)
            elif sort_by == "event_type":
                aggregated_events.sort(key=lambda e: e.event_type or "", reverse=reverse)
            elif sort_by == "timestamp":
                aggregated_events.sort(key=lambda e: e.timestamp, reverse=reverse)
            elif sort_by == "runtime":
                aggregated_events.sort(key=lambda e: e.runtime or 0, reverse=reverse)
            elif sort_by == "retries":
                aggregated_events.sort(key=lambda e: e.retries or 0, reverse=reverse)
            elif sort_by == "hostname":
                aggregated_events.sort(key=lambda e: e.hostname or "", reverse=reverse)
        else:
            aggregated_events.sort(key=lambda e: e.timestamp, reverse=True)
        
        total_events = len(aggregated_events)
        start_idx = page * limit
        end_idx = start_idx + limit
        paginated_events = aggregated_events[start_idx:end_idx]
    else:
        events = list(reversed(recent_events))
        
        if search:
            search_lower = search.lower()
            filtered_events = []
            for e in events:
                if ((e.task_name and search_lower in e.task_name.lower()) or
                    (e.event_type and search_lower in e.event_type.lower()) or
                    (e.hostname and search_lower in e.hostname.lower()) or
                    (e.args and search_lower in str(e.args).lower()) or
                    (e.kwargs and search_lower in str(e.kwargs).lower()) or
                    (e.task_id and search_lower in e.task_id.lower()) or
                    (e.result and search_lower in str(e.result).lower())):
                    filtered_events.append(e)
            events = filtered_events
        
        if sort_by:
            reverse = (sort_order == "desc")
            if sort_by == "task_name":
                events.sort(key=lambda e: e.task_name or "", reverse=reverse)
            elif sort_by == "event_type":
                events.sort(key=lambda e: e.event_type or "", reverse=reverse)
            elif sort_by == "timestamp":
                events.sort(key=lambda e: e.timestamp, reverse=reverse)
            elif sort_by == "runtime":
                events.sort(key=lambda e: e.runtime or 0, reverse=reverse)
            elif sort_by == "retries":
                events.sort(key=lambda e: e.retries or 0, reverse=reverse)
            elif sort_by == "hostname":
                events.sort(key=lambda e: e.hostname or "", reverse=reverse)
        
        total_events = len(events)
        start_idx = page * limit
        end_idx = start_idx + limit
        paginated_events = events[start_idx:end_idx]
    
    total_pages = (total_events + limit - 1) // limit if limit > 0 else 1
    
    return {
        "data": [TaskEventResponse.from_task_event(event) for event in paginated_events],
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_events,
            "total_pages": total_pages,
            "has_next": page < total_pages - 1,
            "has_prev": page > 0
        }
    }


@app.get("/api/events/{task_id}", response_model=List[TaskEventResponse])
async def get_task_events(task_id: str):
    task_events = [event for event in recent_events if event.task_id == task_id]
    if not task_events:
        raise HTTPException(status_code=404, detail="Task not found")
    return [TaskEventResponse.from_task_event(event) for event in task_events]


@app.get("/api/tasks/active", response_model=List[TaskEventResponse])
async def get_active_tasks():
    active_task_ids = set()
    finished_task_ids = set()
    
    for event in recent_events:
        if event.event_type == 'task-started':
            active_task_ids.add(event.task_id)
        elif event.event_type in ['task-succeeded', 'task-failed']:
            finished_task_ids.add(event.task_id)
    
    active_ids = active_task_ids - finished_task_ids
    active_events = [event for event in recent_events 
                    if event.task_id in active_ids and event.event_type == 'task-started']
    
    return [TaskEventResponse.from_task_event(event) for event in active_events]


@app.get("/api/workers", response_model=List[WorkerInfo])
async def get_workers():
    if not monitor_instance:
        return []
    
    workers_data = monitor_instance.get_workers_info()
    worker_list = []
    
    for hostname, data in workers_data.items():
        worker_info = WorkerInfo(
            hostname=hostname,
            status=data.get('status', 'unknown'),
            timestamp=data.get('timestamp', datetime.now()),
            active_tasks=data.get('active', 0),
            processed_tasks=data.get('processed', 0),
            sw_ident=data.get('sw_ident'),
            sw_ver=data.get('sw_ver'),
            sw_sys=data.get('sw_sys'),
            loadavg=data.get('loadavg'),
            freq=data.get('freq')
        )
        worker_list.append(worker_info)
    
    return worker_list


@app.get("/api/workers/{hostname}", response_model=WorkerInfo)
async def get_worker(hostname: str):
    if not monitor_instance:
        raise HTTPException(status_code=404, detail="Monitor not initialized")
    
    workers_data = monitor_instance.get_workers_info()
    if hostname not in workers_data:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    data = workers_data[hostname]
    return WorkerInfo(
        hostname=hostname,
        status=data.get('status', 'unknown'),
        timestamp=data.get('timestamp', datetime.now()),
        active_tasks=data.get('active', 0),
        processed_tasks=data.get('processed', 0),
        sw_ident=data.get('sw_ident'),
        sw_ver=data.get('sw_ver'),
        sw_sys=data.get('sw_sys'),
        loadavg=data.get('loadavg'),
        freq=data.get('freq')
    )


@app.get("/api/workers/events/recent")
async def get_recent_worker_events(limit: int = 50):
    limited_events = recent_worker_events[-limit:] if limit < len(recent_worker_events) else recent_worker_events
    return [event.model_dump() for event in limited_events]


@app.get("/api/health")
async def health_check():
    workers_count = len(monitor_instance.get_workers_info()) if monitor_instance else 0
    return {
        "status": "healthy",
        "monitor_running": monitor_thread.is_alive() if monitor_thread else False,
        "connections": len(manager.active_connections),
        "workers": workers_count,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/websocket/message-types")
async def get_websocket_message_types():
    return {
        "incoming_messages": {
            "ping": PingMessage.model_json_schema(),
            "subscribe": SubscribeMessage.model_json_schema(),
            "set_mode": SetModeMessage.model_json_schema(),
            "get_stored": GetStoredMessage.model_json_schema()
        },
        "outgoing_messages": {
            "pong": PongResponse.model_json_schema(),
            "subscription_response": SubscriptionResponse.model_json_schema(),
            "mode_changed": ModeChangedResponse.model_json_schema(),
            "stored_events_sent": StoredEventsResponse.model_json_schema(),
            "connection_info": ConnectionInfo.model_json_schema(),
            "task_event": TaskEventResponse.model_json_schema()
        }
    }


def start_server():
    config = Config.from_env()
    uvicorn.run(
        "app:app",
        host=config.ws_host,
        port=config.ws_port,
        log_level=config.log_level.lower(),
        reload=False
    )


if __name__ == "__main__":
    start_server()