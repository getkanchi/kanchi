from celery import Celery
from typing import Dict, Any, Callable, Optional
import logging
from datetime import datetime
from models import TaskEvent, TaskInfo, WorkerEvent

logger = logging.getLogger(__name__)


class CeleryEventMonitor:
    """Monitor Celery events and handle them"""
    
    def __init__(self, broker_url: str = 'amqp://guest@localhost//'):
        self.broker_url = broker_url
        self.app = Celery(broker=broker_url)
        self.state = None
        self.event_handlers: Dict[str, Callable] = {}
        self.broadcast_callback: Optional[Callable] = None
        self.worker_broadcast_callback: Optional[Callable] = None
        self.workers: Dict[str, Dict[str, Any]] = {}  # Track worker states
        self.task_args_cache: Dict[str, Dict[str, str]] = {}  # Cache args/kwargs from task-received events
        
    def set_broadcast_callback(self, callback: Callable[[TaskEvent], None]):
        """Set callback for broadcasting events over WebSocket"""
        self.broadcast_callback = callback
        
    def _handle_event(self, event: Dict[str, Any]):
        """Generic event handler"""
        try:
            # Update state
            if self.state:
                self.state.event(event)
            
            # Get task info from state if available
            task = None
            task_name = event.get('name', 'unknown')
            task_id = event.get('uuid', '')
            
            if self.state and 'uuid' in event:
                task = self.state.tasks.get(event['uuid'])
                if task and hasattr(task, 'name'):
                    task_name = task.name
            
            # Handle args/kwargs caching - task-received events have the full args/kwargs
            if event.get('type') == 'task-received' and task_id:
                # Cache args/kwargs from task-received event
                args_data = event.get('args', ())
                kwargs_data = event.get('kwargs', {})
                args_str = str(args_data) if isinstance(args_data, (list, tuple)) else str(args_data)
                kwargs_str = str(kwargs_data) if isinstance(kwargs_data, dict) else str(kwargs_data)
                
                self.task_args_cache[task_id] = {
                    'args': args_str,
                    'kwargs': kwargs_str
                }
            
            # Create TaskEvent, but enhance it with cached args/kwargs if available
            task_event = TaskEvent.from_celery_event(event, task_name)
            
            # If this task has cached args/kwargs and the current event doesn't have them, use cached ones
            if task_id in self.task_args_cache:
                cached = self.task_args_cache[task_id]
                # Only override if current event has empty args/kwargs
                if task_event.args == "()" and cached['args'] != "()":
                    task_event.args = cached['args']
                if task_event.kwargs == "{}" and cached['kwargs'] != "{}":
                    task_event.kwargs = cached['kwargs']
            
            # Log the event
            logger.info(f"Event: {task_event.event_type} - Task: {task_name}[{task_event.task_id}]")
            
            # Broadcast via WebSocket if callback is set
            if self.broadcast_callback:
                self.broadcast_callback(task_event)
                
            # Call specific event handler if registered
            event_type = event.get('type', '')
            if event_type in self.event_handlers:
                self.event_handlers[event_type](task_event, task)
                
        except Exception as e:
            logger.error(f"Error handling event: {e}", exc_info=True)
    
    def _handle_task_succeeded(self, event: Dict[str, Any]):
        """Handle successful task completion"""
        self._handle_event(event)
        
        if self.state and 'uuid' in event:
            task = self.state.tasks.get(event['uuid'])
            if task:
                task_info = TaskInfo.from_celery_task(task)
                logger.info(f"TASK SUCCEEDED: {task_info.name}[{task_info.uuid}] - Result: {task_info.result}")
    
    def _handle_task_failed(self, event: Dict[str, Any]):
        """Handle task failure"""
        self._handle_event(event)
        
        if self.state and 'uuid' in event:
            task = self.state.tasks.get(event['uuid'])
            if task:
                task_info = TaskInfo.from_celery_task(task)
                logger.error(f"TASK FAILED: {task_info.name}[{task_info.uuid}] - Info: {task.info()}")
    
    def _handle_task_started(self, event: Dict[str, Any]):
        """Handle task start"""
        self._handle_event(event)
        
        if self.state and 'uuid' in event:
            task = self.state.tasks.get(event['uuid'])
            if task:
                logger.info(f"TASK STARTED: {task.name if hasattr(task, 'name') else 'unknown'}[{event['uuid']}]")
    
    def _handle_task_sent(self, event: Dict[str, Any]):
        """Handle task sent event"""
        self._handle_event(event)
        logger.debug(f"Task sent: {event.get('name', 'unknown')}[{event.get('uuid', '')}]")
    
    def _handle_task_received(self, event: Dict[str, Any]):
        """Handle task received event"""
        self._handle_event(event)
        logger.debug(f"Task received: {event.get('name', 'unknown')}[{event.get('uuid', '')}]")
    
    def _handle_task_retried(self, event: Dict[str, Any]):
        """Handle task retry"""
        self._handle_event(event)
        
        if self.state and 'uuid' in event:
            task = self.state.tasks.get(event['uuid'])
            if task:
                logger.warning(f"TASK RETRIED: {task.name if hasattr(task, 'name') else 'unknown'}[{event['uuid']}]")
    
    def _handle_task_revoked(self, event: Dict[str, Any]):
        """Handle task revocation"""
        self._handle_event(event)
        
        if self.state and 'uuid' in event:
            task = self.state.tasks.get(event['uuid'])
            if task:
                logger.warning(f"TASK REVOKED: {task.name if hasattr(task, 'name') else 'unknown'}[{event['uuid']}]")
    
    def set_worker_broadcast_callback(self, callback: Callable[[WorkerEvent], None]):
        """Set callback for broadcasting worker events over WebSocket"""
        self.worker_broadcast_callback = callback
    
    def _handle_worker_online(self, event: Dict[str, Any]):
        """Handle worker coming online"""
        hostname = event.get('hostname', 'unknown')
        logger.info(f"WORKER ONLINE: {hostname}")
        
        # Update worker state
        self.workers[hostname] = {
            'status': 'online',
            'timestamp': datetime.fromtimestamp(event.get('timestamp', datetime.now().timestamp())),
            'sw_ident': event.get('sw_ident'),
            'sw_ver': event.get('sw_ver'),
            'sw_sys': event.get('sw_sys')
        }
        
        # Create and broadcast worker event
        if self.worker_broadcast_callback:
            worker_event = WorkerEvent.from_celery_event(event)
            self.worker_broadcast_callback(worker_event)
    
    def _handle_worker_offline(self, event: Dict[str, Any]):
        """Handle worker going offline"""
        hostname = event.get('hostname', 'unknown')
        logger.warning(f"WORKER OFFLINE: {hostname}")
        
        # Update worker state
        if hostname in self.workers:
            self.workers[hostname]['status'] = 'offline'
            self.workers[hostname]['timestamp'] = datetime.fromtimestamp(event.get('timestamp', datetime.now().timestamp()))
        
        # Create and broadcast worker event
        if self.worker_broadcast_callback:
            worker_event = WorkerEvent.from_celery_event(event)
            self.worker_broadcast_callback(worker_event)
    
    def _handle_worker_heartbeat(self, event: Dict[str, Any]):
        """Handle worker heartbeat"""
        hostname = event.get('hostname', 'unknown')
        logger.debug(f"WORKER HEARTBEAT: {hostname} - Active: {event.get('active', 0)}, Processed: {event.get('processed', 0)}")
        
        # Update worker state with heartbeat data
        if hostname not in self.workers:
            self.workers[hostname] = {}
        
        self.workers[hostname].update({
            'status': 'online',
            'timestamp': datetime.fromtimestamp(event.get('timestamp', datetime.now().timestamp())),
            'active': event.get('active', 0),
            'processed': event.get('processed', 0),
            'pool': event.get('pool'),
            'loadavg': event.get('loadavg'),
            'freq': event.get('freq'),
            'sw_ident': event.get('sw_ident'),
            'sw_ver': event.get('sw_ver'),
            'sw_sys': event.get('sw_sys')
        })
        
        # Create and broadcast worker event
        if self.worker_broadcast_callback:
            worker_event = WorkerEvent.from_celery_event(event)
            self.worker_broadcast_callback(worker_event)
    
    def get_workers_info(self) -> Dict[str, Dict[str, Any]]:
        """Get current worker states"""
        return self.workers.copy()
    
    def register_handler(self, event_type: str, handler: Callable[[TaskEvent, Any], None]):
        """Register a custom event handler"""
        self.event_handlers[event_type] = handler
    
    def start_monitoring(self):
        """Start monitoring Celery events"""
        logger.info(f"Starting Celery event monitor - Broker: {self.broker_url}")
        
        # Initialize state tracking
        self.state = self.app.events.State()
        
        try:
            with self.app.connection() as connection:
                # Set up event handlers
                handlers = {
                    'task-sent': self._handle_task_sent,
                    'task-received': self._handle_task_received,
                    'task-started': self._handle_task_started,
                    'task-succeeded': self._handle_task_succeeded,
                    'task-failed': self._handle_task_failed,
                    'task-retried': self._handle_task_retried,
                    'task-revoked': self._handle_task_revoked,
                    'worker-online': self._handle_worker_online,
                    'worker-offline': self._handle_worker_offline,
                    'worker-heartbeat': self._handle_worker_heartbeat,
                    '*': self.state.event,  # Update state for all events
                }
                
                # Create receiver
                recv = self.app.events.Receiver(connection, handlers=handlers)
                
                # Start capturing events
                logger.info("Monitoring Celery events... Press Ctrl+C to stop")
                recv.capture(limit=None, timeout=None, wakeup=True)
                
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Error in event monitoring: {e}", exc_info=True)
            raise
