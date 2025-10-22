"""Shared workflow metadata for triggers and actions."""

TRIGGER_METADATA = [
    {
        "type": "task.sent",
        "label": "Task Sent",
        "description": "Task dispatched to the broker",
        "category": "task",
    },
    {
        "type": "task.received",
        "label": "Task Received",
        "description": "Worker received the task",
        "category": "task",
    },
    {
        "type": "task.started",
        "label": "Task Started",
        "description": "Task execution began",
        "category": "task",
    },
    {
        "type": "task.succeeded",
        "label": "Task Succeeded",
        "description": "Task finished successfully",
        "category": "task",
    },
    {
        "type": "task.failed",
        "label": "Task Failed",
        "description": "Task raised an exception",
        "category": "task",
    },
    {
        "type": "task.retried",
        "label": "Task Retried",
        "description": "Celery retried the task",
        "category": "task",
    },
    {
        "type": "task.revoked",
        "label": "Task Revoked",
        "description": "Task was revoked or cancelled",
        "category": "task",
    },
    {
        "type": "task.orphaned",
        "label": "Task Orphaned",
        "description": "Worker disappeared while processing the task",
        "category": "task",
    },
    {
        "type": "worker.online",
        "label": "Worker Online",
        "description": "Worker joined the cluster",
        "category": "worker",
    },
    {
        "type": "worker.offline",
        "label": "Worker Offline",
        "description": "Worker left the cluster",
        "category": "worker",
    },
    {
        "type": "worker.heartbeat",
        "label": "Worker Heartbeat Missed",
        "description": "Heartbeat stopped for a worker",
        "category": "worker",
    },
]

EVENT_TRIGGER_MAP = {
    "task-sent": "task.sent",
    "task-received": "task.received",
    "task-started": "task.started",
    "task-succeeded": "task.succeeded",
    "task-failed": "task.failed",
    "task-retried": "task.retried",
    "task-revoked": "task.revoked",
    "task-orphaned": "task.orphaned",
    "worker-online": "worker.online",
    "worker-offline": "worker.offline",
    "worker-heartbeat": "worker.heartbeat",
}
