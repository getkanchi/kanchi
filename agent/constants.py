"""Constants and enums for Kanchi task monitoring system."""

from enum import Enum


class TaskState(str, Enum):
    """Task states as exposed in the API."""

    PENDING = "PENDING"
    RECEIVED = "RECEIVED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    RETRY = "RETRY"
    REVOKED = "REVOKED"
    ORPHANED = "ORPHANED"


class EventType(str, Enum):
    """Celery event types."""

    TASK_SENT = "task-sent"
    TASK_RECEIVED = "task-received"
    TASK_STARTED = "task-started"
    TASK_SUCCEEDED = "task-succeeded"
    TASK_FAILED = "task-failed"
    TASK_RETRIED = "task-retried"
    TASK_REVOKED = "task-revoked"
    TASK_ORPHANED = "task-orphaned"
    WORKER_ONLINE = "worker-online"
    WORKER_OFFLINE = "worker-offline"
    WORKER_HEARTBEAT = "worker-heartbeat"


STATE_TO_EVENT_MAP = {
    TaskState.PENDING: EventType.TASK_SENT,
    TaskState.RECEIVED: EventType.TASK_RECEIVED,
    TaskState.RUNNING: EventType.TASK_STARTED,
    TaskState.SUCCESS: EventType.TASK_SUCCEEDED,
    TaskState.FAILED: EventType.TASK_FAILED,
    TaskState.RETRY: EventType.TASK_RETRIED,
    TaskState.REVOKED: EventType.TASK_REVOKED,
    TaskState.ORPHANED: EventType.TASK_ORPHANED,
}


ACTIVE_EVENT_TYPES = [
    EventType.TASK_STARTED,
    EventType.TASK_RECEIVED,
    EventType.TASK_SENT,
]


COMPLETED_EVENT_TYPES = [
    EventType.TASK_SUCCEEDED,
    EventType.TASK_FAILED,
    EventType.TASK_REVOKED,
]

NON_TERMINAL_EVENT_TYPES = [
    EventType.TASK_STARTED,
    EventType.TASK_RECEIVED,
    EventType.TASK_SENT,
]

WORKER_STATUS_MAP = {
    EventType.WORKER_ONLINE: "online",
    EventType.WORKER_OFFLINE: "offline",
    EventType.WORKER_HEARTBEAT: "active",
}
