from typing import Any, Dict, Optional, List, Union, Literal
from datetime import datetime, timezone, date
from enum import Enum
import ast
from pydantic import BaseModel, Field, field_validator


class TaskEvent(BaseModel):
    """Represents a Celery task event"""
    task_id: str
    task_name: str
    event_type: str
    timestamp: datetime
    args: list = Field(default_factory=list)
    kwargs: dict = Field(default_factory=dict)
    retries: int = 0
    eta: Optional[str] = None
    expires: Optional[str] = None
    hostname: Optional[str] = None
    worker_name: Optional[str] = None
    queue: Optional[str] = None
    exchange: str = ""
    routing_key: str = "default"
    root_id: Optional[str] = None
    parent_id: Optional[str] = None
    result: Optional[Any] = None
    runtime: Optional[float] = None
    exception: Optional[str] = None
    traceback: Optional[str] = None
    retry_of: Optional['TaskEvent'] = None
    retried_by: List['TaskEvent'] = Field(default_factory=list)
    is_retry: bool = False
    has_retries: bool = False
    retry_count: int = 0
    is_orphan: bool = False
    orphaned_at: Optional[datetime] = None

    model_config = {
        'from_attributes': True,
        'json_encoders': {
            datetime: lambda v: v.isoformat() if v else None
        }
    }

    @classmethod
    def from_celery_event(cls, event: dict, task_name: Optional[str] = None) -> 'TaskEvent':
        return cls(
            task_id=event.get('uuid', ''),
            task_name=task_name or event.get('name', 'unknown'),
            event_type=event.get('type', 'unknown'),
            timestamp=datetime.now(timezone.utc),
            args=event.get('args'),
            kwargs=event.get('kwargs'),
            retries=event.get('retries', 0),
            eta=event.get('eta'),
            expires=event.get('expires'),
            hostname=event.get('hostname'),
            queue=event.get('queue'),
            exchange=event.get('exchange') or '',
            routing_key=event.get('routing_key') or 'default',
            root_id=event.get('root_id', event.get('uuid', '')),
            parent_id=event.get('parent_id'),
            result=event.get('result'),
            runtime=event.get('runtime'),
            exception=event.get('exception'),
            traceback=event.get('traceback'),
        )

    @field_validator('args', mode='before')
    @classmethod
    def validate_args(cls, v):
        if v is None:
            return []
        if isinstance(v, list):
            return v
        if isinstance(v, tuple):
            return list(v)
        if isinstance(v, str):
            try:
                parsed = ast.literal_eval(v) if v and v != '()' else []
                return list(parsed) if isinstance(parsed, tuple) else (parsed if isinstance(parsed, list) else [])
            except:
                return []
        return []

    @field_validator('kwargs', mode='before')
    @classmethod
    def validate_kwargs(cls, v):
        if v is None:
            return {}
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            try:
                return ast.literal_eval(v) if v and v != '{}' else {}
            except:
                return {}
        return {}

    @field_validator('timestamp', 'orphaned_at', mode='before')
    @classmethod
    def validate_datetime(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
        return v


TaskEvent.model_rebuild()


class WorkerInfo(BaseModel):
    """Worker information model"""
    hostname: str
    status: str
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
    event_type: str
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


class UserSessionResponse(BaseModel):
    """User session API response model"""
    session_id: str
    active_environment_id: Optional[str] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    last_active: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.replace(tzinfo=timezone.utc).isoformat() if v.tzinfo is None else v.isoformat()
        }


class UserSessionCreate(BaseModel):
    """User session creation request model"""
    session_id: str
    active_environment_id: Optional[str] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)


class UserSessionUpdate(BaseModel):
    """User session update request model"""
    active_environment_id: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


class UserInfo(BaseModel):
    """Authenticated user information returned to clients."""
    id: str
    email: str
    provider: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None


class AuthTokens(BaseModel):
    """Token bundle returned after login/refresh."""
    access_token: str
    refresh_token: str
    token_type: Literal['bearer'] = 'bearer'
    expires_in: int
    refresh_expires_in: int
    session_id: str


class AuthConfigResponse(BaseModel):
    """Backend authentication configuration."""
    auth_enabled: bool
    basic_enabled: bool
    oauth_providers: List[str] = Field(default_factory=list)
    allowed_email_patterns: List[str] = Field(default_factory=list)


class LoginResponse(BaseModel):
    """Login response payload."""
    user: UserInfo
    tokens: AuthTokens
    provider: str


class BasicLoginRequest(BaseModel):
    """Basic authentication request payload."""
    username: str
    password: str
    session_id: Optional[str] = None


class RefreshRequest(BaseModel):
    """Refresh token request payload."""
    refresh_token: str


class LogoutRequest(BaseModel):
    """Logout request payload."""
    session_id: Optional[str] = None


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


class ConditionOperator(str, Enum):
    """Supported condition operators."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    IN = "in"
    NOT_IN = "not_in"
    MATCHES = "matches"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    GREATER_EQUAL = "gte"
    LESS_EQUAL = "lte"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"


class TriggerConfig(BaseModel):
    """Base trigger configuration."""
    type: str
    config: Dict[str, Any] = Field(default_factory=dict)


class Condition(BaseModel):
    """Single condition for workflow filtering."""
    field: str
    operator: ConditionOperator
    value: Any


class ConditionGroup(BaseModel):
    """Group of conditions with AND/OR logic."""
    operator: Literal["AND", "OR"] = "AND"
    conditions: List[Condition] = Field(default_factory=list)


class CircuitBreakerConfig(BaseModel):
    """Configuration for workflow-level circuit breaking."""
    enabled: bool = True
    max_executions: int = Field(default=1, ge=1, description="Number of executions allowed per window")
    window_seconds: int = Field(default=300, ge=1, description="Sliding window size in seconds")
    context_field: Optional[str] = Field(
        default=None,
        description="Event context field used to group executions (e.g., root_id, task_id)"
    )

    @field_validator('context_field')
    @classmethod
    def validate_context_field(cls, v):
        if v is None:
            return v
        value = v.strip()
        if not value:
            raise ValueError("context_field cannot be empty")
        return value


class CircuitBreakerState(BaseModel):
    """Result of circuit breaker check."""
    is_open: bool
    reason: Optional[str] = None
    key: Optional[str] = None
    field: Optional[str] = None


class ActionConfig(BaseModel):
    """Configuration for a single action."""
    type: str
    config_id: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)
    continue_on_failure: bool = True


class ActionResult(BaseModel):
    """Result of action execution."""
    action_type: str
    status: Literal["success", "failed", "skipped"]
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    duration_ms: int = 0


class WorkflowDefinition(BaseModel):
    """Complete workflow definition."""
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    enabled: bool = True

    trigger: TriggerConfig
    conditions: Optional[ConditionGroup] = None
    actions: List[ActionConfig]

    priority: int = 100
    max_executions_per_hour: Optional[int] = None
    cooldown_seconds: int = 0
    circuit_breaker: Optional[CircuitBreakerConfig] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None

    execution_count: int = 0
    last_executed_at: Optional[datetime] = None
    success_count: int = 0
    failure_count: int = 0

    class Config:
        from_attributes = True


class WorkflowCreateRequest(BaseModel):
    """Request model for creating a workflow."""
    name: str
    description: Optional[str] = None
    enabled: bool = True
    trigger: TriggerConfig
    conditions: Optional[ConditionGroup] = None
    actions: List[ActionConfig]
    priority: int = 100
    max_executions_per_hour: Optional[int] = None
    cooldown_seconds: int = 0
    circuit_breaker: Optional[CircuitBreakerConfig] = None


class WorkflowUpdateRequest(BaseModel):
    """Request model for updating a workflow."""
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    trigger: Optional[TriggerConfig] = None
    conditions: Optional[ConditionGroup] = None
    actions: Optional[List[ActionConfig]] = None
    priority: Optional[int] = None
    max_executions_per_hour: Optional[int] = None
    cooldown_seconds: Optional[int] = None
    circuit_breaker: Optional[CircuitBreakerConfig] = None


class WorkflowExecutionRecord(BaseModel):
    """Execution history record."""
    id: int
    workflow_id: str
    triggered_at: datetime
    trigger_type: str
    trigger_event: Dict[str, Any]
    status: Literal["pending", "running", "completed", "failed", "rate_limited", "circuit_open"]
    actions_executed: Optional[List[Dict[str, Any]]] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    workflow_snapshot: Optional[Dict[str, Any]] = None
    circuit_breaker_key: Optional[str] = None

    class Config:
        from_attributes = True


class ActionConfigDefinition(BaseModel):
    """Reusable action configuration."""
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    action_type: str
    config: Dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    usage_count: int = 0
    last_used_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ActionConfigCreateRequest(BaseModel):
    """Request model for creating action config."""
    name: str
    description: Optional[str] = None
    action_type: str
    config: Dict[str, Any]


class ActionConfigUpdateRequest(BaseModel):
    """Request model for updating action config."""
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
