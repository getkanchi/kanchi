import ast
import json
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from utils.payload_sanitizer import sanitize_payload


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
    rerun_of: Optional['TaskEvent'] = None
    rerun_by: List['TaskEvent'] = Field(default_factory=list)
    is_rerun: bool = False
    has_reruns: bool = False
    rerun_count: int = 0
    is_orphan: bool = False
    orphaned_at: Optional[datetime] = None
    resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    submitted_rerun_args: Optional[List[Any]] = None
    submitted_rerun_kwargs: Optional[Dict[str, Any]] = None
    submitted_rerun_kind: Optional[str] = None

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
            sanitized, _ = sanitize_payload(v)
            if isinstance(sanitized, list):
                return sanitized
            return [] if sanitized is None else [sanitized]
        if isinstance(v, tuple):
            sanitized, _ = sanitize_payload(list(v))
            if isinstance(sanitized, list):
                return sanitized
            return [] if sanitized is None else [sanitized]
        if isinstance(v, str):
            try:
                if not v or v == '()':
                    parsed = []
                else:
                    try:
                        parsed = json.loads(v)
                    except (json.JSONDecodeError, ValueError):
                        parsed = ast.literal_eval(v)
                if isinstance(parsed, tuple):
                    parsed = list(parsed)
                elif not isinstance(parsed, list):
                    parsed = []
                sanitized, _ = sanitize_payload(parsed)
                return sanitized if isinstance(sanitized, list) else []
            except (TypeError, ValueError, SyntaxError):
                return []
        sanitized, _ = sanitize_payload(v)
        return sanitized if isinstance(sanitized, list) else []

    @field_validator('kwargs', mode='before')
    @classmethod
    def validate_kwargs(cls, v):
        if v is None:
            return {}
        if isinstance(v, dict):
            sanitized, _ = sanitize_payload(v)
            return sanitized if isinstance(sanitized, dict) else {}
        if isinstance(v, str):
            try:
                if not v or v == '{}':
                    parsed = {}
                else:
                    try:
                        parsed = json.loads(v)
                    except (json.JSONDecodeError, ValueError):
                        parsed = ast.literal_eval(v)
                sanitized, _ = sanitize_payload(
                    parsed if isinstance(parsed, dict) else {}
                )
                return sanitized if isinstance(sanitized, dict) else {}
            except (TypeError, ValueError, SyntaxError):
                return {}
        sanitized, _ = sanitize_payload(v)
        return sanitized if isinstance(sanitized, dict) else {}

    @field_validator('timestamp', 'orphaned_at', 'resolved_at', mode='before')
    @classmethod
    def validate_datetime(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
        return v

    @field_validator('result', mode='before')
    @classmethod
    def sanitize_result(cls, v):
        sanitized, _ = sanitize_payload(v)
        return sanitized


TaskEvent.model_rebuild()


class StepDefinition(BaseModel):
    """Single step definition for task progress."""
    key: str
    label: str
    description: Optional[str] = None
    total: Optional[int] = None
    order: Optional[int] = None


class TaskStepsEvent(BaseModel):
    """Progress steps definition event."""
    task_id: str
    task_name: str
    steps: List[StepDefinition]
    timestamp: datetime
    event_type: Literal["kanchi-task-steps"] = "kanchi-task-steps"

    model_config = {
        'json_encoders': {
            datetime: lambda v: v.isoformat() if v else None
        }
    }


class TaskProgressEvent(BaseModel):
    """Task progress update event."""
    task_id: str
    task_name: str
    progress: float
    timestamp: datetime
    step_key: Optional[str] = None
    message: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    event_type: Literal["kanchi-task-progress"] = "kanchi-task-progress"

    model_config = {
        'json_encoders': {
            datetime: lambda v: v.isoformat() if v else None
        }
    }

    @classmethod
    def from_celery_event(cls, event: dict) -> 'TaskProgressEvent':
        sanitized_meta, _ = sanitize_payload(event.get('meta'))
        ts_value = event.get('timestamp')
        if isinstance(ts_value, (int, float)):
            ts = datetime.fromtimestamp(ts_value, tz=timezone.utc)
        elif isinstance(ts_value, str):
            try:
                ts = datetime.fromisoformat(ts_value)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
            except Exception:
                ts = datetime.now(timezone.utc)
        else:
            ts = datetime.now(timezone.utc)
        return cls(
            task_id=event.get('task_id', ''),
            task_name=event.get('task_name', ''),
            progress=float(event.get('progress', 0)),
            timestamp=ts,
            step_key=event.get('step_key'),
            message=event.get('message'),
            meta=sanitized_meta if isinstance(sanitized_meta, dict) else None,
        )


class TaskProgressSnapshot(BaseModel):
    """Aggregate view of progress and steps for a task."""
    task_id: str
    latest: Optional[TaskProgressEvent] = None
    steps: List[StepDefinition] = Field(default_factory=list)
    history: List[TaskProgressEvent] = Field(default_factory=list)


class TaskActionType(str, Enum):
    """Supported user-initiated task actions."""

    RERUN = "rerun"
    RESOLVE = "resolve"
    UNRESOLVE = "unresolve"


class TaskActionStatus(str, Enum):
    """Overall persisted status for a task action."""

    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"


class TaskActionItemOutcome(str, Enum):
    """Per-task outcome for a task action item."""

    PENDING = "pending"
    CHANGED = "changed"
    NOOP = "noop"
    CREATED = "created"
    SKIPPED_UNAVAILABLE = "skipped_unavailable"
    USER_SKIPPED = "user_skipped"
    BLOCKED_SKIPPED = "blocked_skipped"
    FAILED = "failed"


class RerunReviewState(str, Enum):
    """Availability state for a manual rerun review item."""

    REPLAYABLE = "replayable"
    REPAIRABLE = "repairable"
    BLOCKED = "blocked"


class RerunSubmitDecision(str, Enum):
    """Per-task decision made in the rerun review drawer."""

    SUBMIT = "submit"
    USER_SKIP = "user_skip"
    BLOCKED_SKIP = "blocked_skip"


class RerunKind(str, Enum):
    """Audit category for submitted manual rerun inputs."""

    REPLAY = "replay"
    EDITED_OVERRIDE = "edited_override"
    REPAIRED_OVERRIDE = "repaired_override"


class RerunUnavailableReason(str, Enum):
    """Reasons a task cannot be manually rerun."""

    TASK_NOT_FOUND = "task_not_found"
    MISSING_TASK_NAME = "missing_task_name"
    TRUNCATED_PAYLOAD = "truncated_payload"
    UNPARSEABLE_PAYLOAD = "unparseable_payload"
    MONITOR_UNAVAILABLE = "monitor_unavailable"


class RerunInputIssue(BaseModel):
    """Path-addressed rerun input issue."""

    path: str
    reason_code: str
    message: str


class RerunSubmissionTarget(BaseModel):
    """Read-only task identity and routing target for manual rerun submission."""

    task_name: Optional[str] = None
    queue: Optional[str] = None
    routing_key: Optional[str] = None
    exchange: Optional[str] = None


class RerunInputBaseline(BaseModel):
    """Starting rerun inputs shown to the user."""

    args: List[Any] = Field(default_factory=list)
    kwargs: Dict[str, Any] = Field(default_factory=dict)
    source: str = "observed_task_inputs"
    source_version: Optional[str] = None


class TaskActionCreateRequest(BaseModel):
    """Create and execute a task action."""

    action_type: TaskActionType
    task_ids: List[str] = Field(min_length=1)


class RerunPreflightRequest(BaseModel):
    """Preflight manual rerun availability for selected tasks."""

    task_ids: List[str] = Field(min_length=1)


class RerunPreflightItem(BaseModel):
    """Per-task rerun preflight result."""

    task_id: str
    task_name: Optional[str] = None
    ready: bool = False
    review_state: RerunReviewState = RerunReviewState.BLOCKED
    reason_code: Optional[str] = None
    reason: Optional[str] = None
    task: Optional[TaskEvent] = None
    baseline: RerunInputBaseline = Field(default_factory=RerunInputBaseline)
    target: RerunSubmissionTarget = Field(default_factory=RerunSubmissionTarget)
    required_replacements: List[RerunInputIssue] = Field(default_factory=list)
    fingerprint: Optional[str] = None


class RerunPreflightResponse(BaseModel):
    """Rerun preflight summary."""

    total: int
    ready_count: int
    unavailable_count: int
    replayable_count: int = 0
    repairable_count: int = 0
    blocked_count: int = 0
    max_selection_size: int
    items: List[RerunPreflightItem] = Field(default_factory=list)


class RerunSubmitItem(BaseModel):
    """A single rerun review decision submitted by the frontend."""

    task_id: str
    decision: RerunSubmitDecision
    fingerprint: str
    args: Optional[List[Any]] = None
    kwargs: Optional[Dict[str, Any]] = None


class RerunSubmitRequest(BaseModel):
    """Submit a manual rerun review."""

    items: List[RerunSubmitItem] = Field(min_length=1)


class TaskActionItem(BaseModel):
    """Per-task action item response."""

    id: int
    action_id: str
    original_task_id: str
    original_task_name: Optional[str] = None
    outcome: TaskActionItemOutcome
    reason_code: Optional[str] = None
    reason: Optional[str] = None
    rerun_task_id: Optional[str] = None
    rerun_task_name: Optional[str] = None
    rerun_task: Optional[TaskEvent] = None
    attempted_task_id: Optional[str] = None
    submitted_args: Optional[List[Any]] = None
    submitted_kwargs: Optional[Dict[str, Any]] = None
    rerun_kind: Optional[RerunKind] = None
    skip_category: Optional[str] = None
    review_fingerprint: Optional[str] = None
    target_queue: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        'from_attributes': True,
        'json_encoders': {
            datetime: lambda v: v.isoformat() if v else None
        }
    }


class TaskActionSummary(BaseModel):
    """Compact persisted task action summary."""

    id: str
    action_type: TaskActionType
    status: TaskActionStatus
    initiated_by_user_id: Optional[str] = None
    initiated_by: Optional[str] = None
    initiated_session_id: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    original_task_ids: List[str] = Field(default_factory=list)
    selection_size: int = 0
    item_total: int = 0
    item_changed: int = 0
    item_noop: int = 0
    item_created: int = 0
    item_skipped: int = 0
    item_failed: int = 0
    summary: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        'from_attributes': True,
        'json_encoders': {
            datetime: lambda v: v.isoformat() if v else None
        }
    }


class TaskActionDetail(TaskActionSummary):
    """Task action with item rows and live rerun lifecycle summary."""

    items: List[TaskActionItem] = Field(default_factory=list)
    rerun_lifecycle_counts: Dict[str, int] = Field(default_factory=dict)


class TaskActionListResponse(BaseModel):
    """Paginated task action list response."""

    data: List[TaskActionSummary]
    max_selection_size: int


class TaskActionWebSocketEvent(TaskActionDetail):
    """WebSocket message for task action updates."""

    event_type: Literal["kanchi-task-action"] = "kanchi-task-action"


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


class AppSetting(BaseModel):
    """Database-backed application setting."""
    key: str
    value: Any
    value_type: Literal["string", "number", "boolean", "json"] = "string"
    label: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.replace(tzinfo=timezone.utc).isoformat() if v.tzinfo is None else v.isoformat()
        }


class AppSettingUpdate(BaseModel):
    """Create/update payload for an application setting."""
    value: Any
    value_type: Optional[Literal["string", "number", "boolean", "json"]] = None
    label: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None


class TaskIssueConfig(BaseModel):
    """Configuration for the task issue summary section."""
    lookback_hours: int = Field(default=24, ge=1, le=168)


class DataRetentionConfig(BaseModel):
    """Retention policy for stored operational data."""
    task_successful_days: int = Field(default=14, ge=1, le=3650)
    task_unsuccessful_days: int = Field(default=30, ge=1, le=3650)
    worker_events_days: int = Field(default=30, ge=1, le=3650)
    workflow_executions_days: int = Field(default=30, ge=1, le=3650)
    task_daily_stats_days: int = Field(default=365, ge=1, le=3650)
    inactive_sessions_days: int = Field(default=30, ge=1, le=3650)


class RetentionScheduleConfig(BaseModel):
    """Automatic retention cleanup schedule."""
    enabled: bool = False
    preset: Literal["hourly", "daily", "weekly", "monthly"] = "daily"
    hour: int = Field(default=3, ge=0, le=23)
    minute: int = Field(default=0, ge=0, le=59)
    weekday: int = Field(default=0, ge=0, le=6)
    month_day: int = Field(default=1, ge=1, le=31)
    timezone: Literal["UTC"] = "UTC"


class RetentionCleanupResult(BaseModel):
    """Result for a single retention target cleanup."""
    key: str
    label: str
    retention_days: int = Field(ge=1)
    deleted: int = Field(ge=0)


class RetentionCleanupResponse(BaseModel):
    """Summary of a retention cleanup run."""
    dry_run: bool = False
    total_deleted: int = Field(ge=0)
    policy: DataRetentionConfig
    results: List[RetentionCleanupResult] = Field(default_factory=list)


class RetentionLastRun(BaseModel):
    """Last automatic retention cleanup run status."""
    status: Literal["never", "success", "error", "running"] = "never"
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    total_deleted: int = Field(default=0, ge=0)
    dry_run: bool = False
    error: Optional[str] = None
    results: List[RetentionCleanupResult] = Field(default_factory=list)


class AppConfigSnapshot(BaseModel):
    """Grouped configuration snapshot returned to clients."""
    task_issue_summary: TaskIssueConfig
    data_retention: DataRetentionConfig
    retention_schedule: RetentionScheduleConfig = Field(default_factory=RetentionScheduleConfig)
    retention_last_run: RetentionLastRun = Field(default_factory=RetentionLastRun)


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
