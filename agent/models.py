from typing import Any, Dict, Optional, List, Union, Literal
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone, date
import json
from pydantic import BaseModel, Field


@dataclass
class TaskEvent:
    """Represents a Celery task event"""
    task_id: str
    task_name: str
    event_type: str  # 'task-sent', 'task-received', 'task-started', 'task-succeeded', 'task-failed', 'task-retried', 'task-revoked'
    timestamp: datetime
    args: str = "()"
    kwargs: str = "{}"
    retries: int = 0
    eta: Optional[str] = None
    expires: Optional[str] = None
    hostname: Optional[str] = None
    worker_name: Optional[str] = None
    queue: Optional[str] = None
    exchange: str = ""
    routing_key: str = ""
    root_id: Optional[str] = None
    parent_id: Optional[str] = None
    result: Optional[Any] = None
    runtime: Optional[float] = None
    exception: Optional[str] = None
    traceback: Optional[str] = None
    retry_of: Optional['TaskEvent'] = None  # Parent task object (1 level up only, no grandparents)
    retried_by: List['TaskEvent'] = field(default_factory=list)  # Child retry tasks (1 level down only, no grandchildren)
    is_retry: bool = False
    has_retries: bool = False
    retry_count: int = 0
    is_orphan: bool = False
    orphaned_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization with nested task objects"""
        data = asdict(self)

        # Helper to ensure UTC timezone in ISO format
        def ensure_utc_iso(dt):
            if dt is None:
                return None
            if isinstance(dt, datetime):
                # If naive, treat as UTC
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.isoformat()
            return dt

        # Ensure routing_key is never None (TaskEventResponse expects a string)
        if data.get('routing_key') is None:
            data['routing_key'] = 'default'

        # Ensure queue is never None
        if data.get('queue') is None:
            data['queue'] = None  # Keep as None, TaskEventResponse allows Optional[str]

        # Convert datetime to ISO format string with timezone
        data['timestamp'] = ensure_utc_iso(data['timestamp'])
        data['orphaned_at'] = ensure_utc_iso(data.get('orphaned_at'))

        # Parse args/kwargs from JSON strings back to Python objects
        # This ensures WebSocket clients receive proper JSON objects, not stringified JSON
        if isinstance(data.get('args'), str):
            try:
                data['args'] = json.loads(data['args'])
            except (json.JSONDecodeError, ValueError):
                data['args'] = []  # Default to empty list if parsing fails

        if isinstance(data.get('kwargs'), str):
            try:
                data['kwargs'] = json.loads(data['kwargs'])
            except (json.JSONDecodeError, ValueError):
                data['kwargs'] = {}  # Default to empty dict if parsing fails

        if data.get('retry_of') and isinstance(data['retry_of'], dict):
            data['retry_of']['timestamp'] = ensure_utc_iso(data['retry_of'].get('timestamp'))
            data['retry_of']['orphaned_at'] = ensure_utc_iso(data['retry_of'].get('orphaned_at'))

            # Ensure routing_key is never None for nested objects
            if data['retry_of'].get('routing_key') is None:
                data['retry_of']['routing_key'] = 'default'

            # Parse nested retry_of args/kwargs too
            if isinstance(data['retry_of'].get('args'), str):
                try:
                    data['retry_of']['args'] = json.loads(data['retry_of']['args'])
                except (json.JSONDecodeError, ValueError):
                    data['retry_of']['args'] = []
            if isinstance(data['retry_of'].get('kwargs'), str):
                try:
                    data['retry_of']['kwargs'] = json.loads(data['retry_of']['kwargs'])
                except (json.JSONDecodeError, ValueError):
                    data['retry_of']['kwargs'] = {}

        if data.get('retried_by'):
            for retry_task in data['retried_by']:
                if isinstance(retry_task, dict):
                    retry_task['timestamp'] = ensure_utc_iso(retry_task.get('timestamp'))
                    retry_task['orphaned_at'] = ensure_utc_iso(retry_task.get('orphaned_at'))

                    # Ensure routing_key is never None for nested objects
                    if retry_task.get('routing_key') is None:
                        retry_task['routing_key'] = 'default'

                    # Parse nested retried_by args/kwargs too
                    if isinstance(retry_task.get('args'), str):
                        try:
                            retry_task['args'] = json.loads(retry_task['args'])
                        except (json.JSONDecodeError, ValueError):
                            retry_task['args'] = []
                    if isinstance(retry_task.get('kwargs'), str):
                        try:
                            retry_task['kwargs'] = json.loads(retry_task['kwargs'])
                        except (json.JSONDecodeError, ValueError):
                            retry_task['kwargs'] = {}

        return data
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_celery_event(cls, event: dict, task_name: Optional[str] = None) -> 'TaskEvent':
        """Create TaskEvent from Celery event data.

        NOTE: We use the current server time (UTC) instead of the timestamp from the Celery event
        because worker clocks may be misconfigured or out of sync. The receive time is more reliable
        for monitoring purposes.

        NOTE: Only task-sent events contain routing information (queue, exchange, routing_key).
        All other event types will have these fields as None/empty. Use a JOIN query to get
        routing info from the task-sent event when querying other event types.
        """
        import logging
        logger = logging.getLogger(__name__)

        # Extract event type from the event
        event_type = event.get('type', 'unknown')

        # Get task info
        task_id = event.get('uuid', '')

        # Handle different event types
        # Celery sends args/kwargs as STRING representations of Python objects
        # e.g., "({'key': 'value'},)" for args, "{'key': 'value'}" for kwargs
        # We need to: 1) Parse string to Python object, 2) Convert to JSON
        import ast

        kwargs_data = event.get('kwargs', {})
        args_data = event.get('args', ())

        # Parse and convert kwargs
        try:
            # If it's a string, parse it as Python literal
            if isinstance(kwargs_data, str):
                kwargs_obj = ast.literal_eval(kwargs_data) if kwargs_data and kwargs_data != '{}' else {}
            else:
                kwargs_obj = kwargs_data
            kwargs_str = json.dumps(kwargs_obj)
        except (ValueError, SyntaxError, TypeError):
            # If parsing fails, keep as-is
            kwargs_str = kwargs_data if isinstance(kwargs_data, str) else str(kwargs_data)

        # Parse and convert args
        try:
            # If it's a string, parse it as Python literal
            if isinstance(args_data, str):
                args_obj = ast.literal_eval(args_data) if args_data and args_data != '()' else []
            else:
                args_obj = args_data

            # Convert tuple to list for JSON serialization
            if isinstance(args_obj, tuple):
                args_obj = list(args_obj)
            args_str = json.dumps(args_obj)
        except (ValueError, SyntaxError, TypeError):
            # If parsing fails, keep as-is
            args_str = args_data if isinstance(args_data, str) else str(args_data)
            

        return cls(
            task_id=task_id,
            task_name=task_name or event.get('name', 'unknown'),
            event_type=event_type,
            # Use server receive time instead of worker's timestamp to avoid clock skew issues
            timestamp=datetime.now(timezone.utc),
            args=args_str,
            kwargs=kwargs_str,
            retries=event.get('retries', 0),
            eta=event.get('eta'),
            expires=event.get('expires'),
            hostname=event.get('hostname'),
            # Routing info: only present in task-sent events, None/empty for others
            queue=event.get('queue'),
            exchange=event.get('exchange') or '',
            routing_key=event.get('routing_key') or '',
            root_id=event.get('root_id', task_id),
            parent_id=event.get('parent_id'),
            result=event.get('result'),
            runtime=event.get('runtime'),
            exception=event.get('exception'),
            traceback=event.get('traceback')
        )


@dataclass 
class TaskInfo:
    """Extended task information from Celery state tracking"""
    uuid: str
    name: str
    args: str
    kwargs: str
    retries: int
    result: Optional[Any]
    runtime: Optional[float]
    exchange: str
    routing_key: str
    root_id: str
    
    @classmethod
    def from_celery_task(cls, task) -> 'TaskInfo':
        """Create TaskInfo from Celery task state object"""
        import ast
        info = task.info() if hasattr(task, 'info') else {}

        # Parse and convert args (same logic as TaskEvent)
        args_data = info.get('args', ())
        try:
            if isinstance(args_data, str):
                args_obj = ast.literal_eval(args_data) if args_data and args_data != '()' else []
            else:
                args_obj = args_data

            if isinstance(args_obj, tuple):
                args_obj = list(args_obj)
            args_str = json.dumps(args_obj)
        except (ValueError, SyntaxError, TypeError):
            args_str = args_data if isinstance(args_data, str) else str(args_data)

        # Parse and convert kwargs (same logic as TaskEvent)
        kwargs_data = info.get('kwargs', {})
        try:
            if isinstance(kwargs_data, str):
                kwargs_obj = ast.literal_eval(kwargs_data) if kwargs_data and kwargs_data != '{}' else {}
            else:
                kwargs_obj = kwargs_data
            kwargs_str = json.dumps(kwargs_obj)
        except (ValueError, SyntaxError, TypeError):
            kwargs_str = kwargs_data if isinstance(kwargs_data, str) else str(kwargs_data)

        return cls(
            uuid=task.uuid if hasattr(task, 'uuid') else '',
            name=task.name if hasattr(task, 'name') else 'unknown',
            args=args_str,
            kwargs=kwargs_str,
            retries=info.get('retries', 0),
            result=str(info.get('result', '')),
            runtime=info.get('runtime'),
            exchange=info.get('exchange', ''),
            routing_key=info.get('routing_key', ''),
            root_id=info.get('root_id', task.uuid if hasattr(task, 'uuid') else '')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


# Pydantic models for FastAPI
class TaskEventResponse(BaseModel):
    """Pydantic model for API responses with nested retry relationships"""
    task_id: str
    task_name: str
    event_type: str
    timestamp: datetime
    args: Any = []  # Can be list, dict, or any JSON-serializable type
    kwargs: Dict[str, Any] = Field(default_factory=dict)
    retries: int = 0
    eta: Optional[str] = None
    expires: Optional[str] = None
    hostname: Optional[str] = None
    exchange: str = ""
    routing_key: str = "default"
    root_id: Optional[str] = None
    parent_id: Optional[str] = None
    result: Optional[Any] = None
    runtime: Optional[float] = None
    exception: Optional[str] = None
    traceback: Optional[str] = None
    retry_of: Optional['TaskEventResponse'] = None  # Nested parent task object
    retried_by: List['TaskEventResponse'] = Field(default_factory=list)  # Nested retry task objects
    is_retry: bool = False
    has_retries: bool = False
    retry_count: int = 0
    is_orphan: bool = False
    orphaned_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.replace(tzinfo=timezone.utc).isoformat() if v and v.tzinfo is None else (v.isoformat() if v else None)
        }

    @classmethod
    def from_task_event(cls, task_event: TaskEvent) -> 'TaskEventResponse':
        """Create from TaskEvent dataclass"""
        return cls(**task_event.to_dict())


TaskEventResponse.model_rebuild()


class WorkerInfo(BaseModel):
    """Worker information model"""
    hostname: str
    status: str  # 'online', 'offline', 'heartbeat'
    timestamp: datetime
    active_tasks: int = 0
    processed_tasks: int = 0
    sw_ident: Optional[str] = None
    sw_ver: Optional[str] = None
    sw_sys: Optional[str] = None
    loadavg: Optional[List[float]] = None
    freq: Optional[float] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.replace(tzinfo=timezone.utc).isoformat() if v.tzinfo is None else v.isoformat()
        }


class WorkerEvent(BaseModel):
    """Worker event model"""
    hostname: str
    event_type: str  # 'worker-online', 'worker-offline', 'worker-heartbeat'
    timestamp: datetime
    active: Optional[int] = None
    processed: Optional[int] = None
    pool: Optional[Dict[str, Any]] = None
    loadavg: Optional[List[float]] = None
    freq: Optional[float] = None
    sw_ident: Optional[str] = None
    sw_ver: Optional[str] = None
    sw_sys: Optional[str] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.replace(tzinfo=timezone.utc).isoformat() if v.tzinfo is None else v.isoformat()
        }
    
    @classmethod
    def from_celery_event(cls, event: dict) -> 'WorkerEvent':
        """Create WorkerEvent from Celery worker event"""
        event_type = event.get('type', 'unknown')

        return cls(
            hostname=event.get('hostname', 'unknown'),
            event_type=event_type,
            timestamp=datetime.fromtimestamp(event.get('timestamp', datetime.now(timezone.utc).timestamp()), tz=timezone.utc),
            active=event.get('active'),
            processed=event.get('processed'),
            pool=event.get('pool'),
            loadavg=event.get('loadavg'),
            freq=event.get('freq'),
            sw_ident=event.get('sw_ident'),
            sw_ver=event.get('sw_ver'),
            sw_sys=event.get('sw_sys')
        )


class ConnectionInfo(BaseModel):
    """WebSocket connection info"""
    status: str
    timestamp: datetime
    message: str
    total_connections: int = 0


class SubscriptionRequest(BaseModel):
    """WebSocket subscription request"""
    event_types: Optional[List[str]] = None
    task_names: Optional[List[str]] = None


class SubscriptionResponse(BaseModel):
    """WebSocket subscription response"""
    status: str
    filters: dict
    timestamp: datetime


class LogEntry(BaseModel):
    """Log entry from frontend"""
    level: str
    message: str
    timestamp: Optional[datetime] = None
    context: Optional[Dict[str, Any]] = None


class TaskRegistryResponse(BaseModel):
    """Task registry API response model"""
    id: str
    name: str
    human_readable_name: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    first_seen: datetime
    last_seen: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.replace(tzinfo=timezone.utc).isoformat() if v.tzinfo is None else v.isoformat()
        }


class TaskRegistryUpdate(BaseModel):
    """Task registry update request model"""
    human_readable_name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class TaskRegistryStats(BaseModel):
    """Statistics for a specific task"""
    task_name: str
    total_executions: int = 0
    succeeded: int = 0
    failed: int = 0
    pending: int = 0
    retried: int = 0
    avg_runtime: Optional[float] = None
    last_execution: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.replace(tzinfo=timezone.utc).isoformat() if v and v.tzinfo is None else (v.isoformat() if v else None)
        }


class TaskDailyStatsResponse(BaseModel):
    """Daily statistics response model"""
    task_name: str
    date: date
    total_executions: int = 0
    succeeded: int = 0
    failed: int = 0
    pending: int = 0
    retried: int = 0
    revoked: int = 0
    orphaned: int = 0
    avg_runtime: Optional[float] = None
    min_runtime: Optional[float] = None
    max_runtime: Optional[float] = None
    p50_runtime: Optional[float] = None
    p95_runtime: Optional[float] = None
    p99_runtime: Optional[float] = None
    first_execution: Optional[datetime] = None
    last_execution: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.replace(tzinfo=timezone.utc).isoformat() if v and v.tzinfo is None else (v.isoformat() if v else None),
            date: lambda v: v.isoformat()
        }


class EnvironmentResponse(BaseModel):
    """Environment API response model"""
    id: str
    name: str
    description: Optional[str] = None
    queue_patterns: List[str] = Field(default_factory=list)
    worker_patterns: List[str] = Field(default_factory=list)
    is_active: bool = False
    is_default: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.replace(tzinfo=timezone.utc).isoformat() if v.tzinfo is None else v.isoformat()
        }


class EnvironmentCreate(BaseModel):
    """Environment creation request model"""
    name: str
    description: Optional[str] = None
    queue_patterns: List[str] = Field(default_factory=list)
    worker_patterns: List[str] = Field(default_factory=list)
    is_default: bool = False


class EnvironmentUpdate(BaseModel):
    """Environment update request model"""
    name: Optional[str] = None
    description: Optional[str] = None
    queue_patterns: Optional[List[str]] = None
    worker_patterns: Optional[List[str]] = None
    is_default: Optional[bool] = None


class TimelineBucket(BaseModel):
    """Single time bucket in timeline"""
    timestamp: datetime
    total_executions: int = 0
    succeeded: int = 0
    failed: int = 0
    retried: int = 0

    class Config:
        json_encoders = {
            datetime: lambda v: v.replace(tzinfo=timezone.utc).isoformat() if v.tzinfo is None else v.isoformat()
        }


class TaskTimelineResponse(BaseModel):
    """Timeline response showing execution frequency over time"""
    task_name: str
    start_time: datetime
    end_time: datetime
    bucket_size_minutes: int
    buckets: List[TimelineBucket]

    class Config:
        json_encoders = {
            datetime: lambda v: v.replace(tzinfo=timezone.utc).isoformat() if v.tzinfo is None else v.isoformat()
        }


# WebSocket Message Models
class PingMessage(BaseModel):
    """WebSocket ping message"""
    type: Literal["ping"] = "ping"


class PongResponse(BaseModel):
    """WebSocket pong response"""
    type: Literal["pong"] = "pong"
    timestamp: datetime


class SubscribeMessage(BaseModel):
    """WebSocket subscribe message"""
    type: Literal["subscribe"] = "subscribe"
    filters: Optional[Dict[str, List[str]]] = Field(default_factory=dict)


class SetModeMessage(BaseModel):
    """WebSocket set mode message"""
    type: Literal["set_mode"] = "set_mode"
    mode: Literal["live", "static"]


class ModeChangedResponse(BaseModel):
    """WebSocket mode changed response"""
    type: Literal["mode_changed"] = "mode_changed"
    mode: Literal["live", "static"]
    timestamp: datetime
    events_count: Optional[int] = None


class GetStoredMessage(BaseModel):
    """WebSocket get stored events message"""
    type: Literal["get_stored"] = "get_stored"
    limit: Optional[int] = None


class StoredEventsResponse(BaseModel):
    """WebSocket stored events response"""
    type: Literal["stored_events_sent"] = "stored_events_sent"
    count: int
    timestamp: datetime


# Union type for all incoming WebSocket messages
WebSocketMessage = Union[
    PingMessage,
    SubscribeMessage,
    SetModeMessage,
    GetStoredMessage
]

# Union type for all outgoing WebSocket responses
WebSocketResponse = Union[
    PongResponse,
    SubscriptionResponse,
    ModeChangedResponse,
    StoredEventsResponse,
    ConnectionInfo,
    TaskEventResponse
]
