from typing import Any, Dict, Optional, List, Union, Literal
from dataclasses import dataclass, asdict, field
from datetime import datetime
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
    retry_of: Optional[str] = None
    retried_by: List[str] = field(default_factory=list)
    is_retry: bool = False
    has_retries: bool = False
    retry_count: int = 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert datetime to ISO format string
        if isinstance(data['timestamp'], datetime):
            data['timestamp'] = data['timestamp'].isoformat()
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_celery_event(cls, event: dict, task_name: Optional[str] = None) -> 'TaskEvent':
        """Create TaskEvent from Celery event data"""
        # Extract event type from the event
        event_type = event.get('type', 'unknown')
        
        # Get task info
        task_id = event.get('uuid', '')
        
        # Handle different event types
        kwargs_data = event.get('kwargs', {})
        if isinstance(kwargs_data, dict):
            kwargs_str = str(kwargs_data)
        else:
            kwargs_str = str(kwargs_data)
            
        args_data = event.get('args', ())
        if isinstance(args_data, (list, tuple)):
            args_str = str(args_data)
        else:
            args_str = str(args_data)
            
        
        return cls(
            task_id=task_id,
            task_name=task_name or event.get('name', 'unknown'),
            event_type=event_type,
            timestamp=datetime.fromtimestamp(event.get('timestamp', datetime.now().timestamp())),
            args=args_str,
            kwargs=kwargs_str,
            retries=event.get('retries', 0),
            eta=event.get('eta'),
            expires=event.get('expires'),
            hostname=event.get('hostname'),
            exchange=event.get('exchange', ''),
            routing_key=event.get('routing_key', ''),
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
        info = task.info() if hasattr(task, 'info') else {}
        
        return cls(
            uuid=task.uuid if hasattr(task, 'uuid') else '',
            name=task.name if hasattr(task, 'name') else 'unknown',
            args=str(info.get('args', '()')),
            kwargs=str(info.get('kwargs', '{}')),
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
    """Pydantic model for API responses"""
    task_id: str
    task_name: str
    event_type: str
    timestamp: datetime
    args: str = "()"
    kwargs: str = "{}"
    retries: int = 0
    eta: Optional[str] = None
    expires: Optional[str] = None
    hostname: Optional[str] = None
    exchange: str = ""
    routing_key: str = ""
    root_id: Optional[str] = None
    parent_id: Optional[str] = None
    result: Optional[Any] = None
    runtime: Optional[float] = None
    exception: Optional[str] = None
    traceback: Optional[str] = None
    retry_of: Optional[str] = None
    retried_by: List[str] = Field(default_factory=list)
    is_retry: bool = False
    has_retries: bool = False
    retry_count: int = 0

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    @classmethod
    def from_task_event(cls, task_event: TaskEvent) -> 'TaskEventResponse':
        """Create from TaskEvent dataclass"""
        return cls(**task_event.to_dict())


class TaskStats(BaseModel):
    """Task statistics model"""
    total_tasks: int = 0
    succeeded: int = 0
    failed: int = 0
    pending: int = 0
    retried: int = 0
    active: int = 0


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
            datetime: lambda v: v.isoformat()
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
            datetime: lambda v: v.isoformat()
        }
    
    @classmethod
    def from_celery_event(cls, event: dict) -> 'WorkerEvent':
        """Create WorkerEvent from Celery worker event"""
        event_type = event.get('type', 'unknown')
        
        return cls(
            hostname=event.get('hostname', 'unknown'),
            event_type=event_type,
            timestamp=datetime.fromtimestamp(event.get('timestamp', datetime.now().timestamp())),
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
