"""Built-in workflow templates for common operational scenarios."""

WORKFLOW_TEMPLATES = [
    {
        "id": "repeated-task-failure",
        "name": "Repeated task failure escalation",
        "description": "Start from a failed-task trigger that retries once and leaves room for a Slack escalation.",
        "scenario": "Repeated task failure",
        "recommended_for": ["task.failed", "task.retried"],
        "workflow": {
            "name": "Repeated task failure escalation",
            "description": "Retry a failing task once and optionally notify Slack if the pattern keeps repeating.",
            "enabled": True,
            "trigger": {"type": "task.failed", "config": {}},
            "conditions": {
                "operator": "AND",
                "conditions": [
                    {"field": "retry_count", "operator": "gte", "value": 1},
                ],
            },
            "actions": [
                {
                    "type": "task.retry",
                    "params": {"delay_seconds": 60},
                    "continue_on_failure": False,
                },
                {
                    "type": "slack.notify",
                    "params": {
                        "config_id": "",
                        "template": "🚨 {{task_name}} keeps failing on {{queue}} (task {{task_id}})",
                        "color": "#d92d20",
                    },
                    "continue_on_failure": True,
                },
            ],
            "priority": 180,
            "cooldown_seconds": 300,
            "max_executions_per_hour": 10,
            "circuit_breaker": {
                "enabled": True,
                "max_executions": 3,
                "window_seconds": 900,
                "context_field": "task_name",
            },
        },
    },
    {
        "id": "orphaned-task-recovery",
        "name": "Orphaned task recovery",
        "description": "React to orphaned tasks with a guarded retry and operator notification placeholder.",
        "scenario": "Orphaned task detected",
        "recommended_for": ["task.orphaned"],
        "workflow": {
            "name": "Orphaned task recovery",
            "description": "Retry orphaned tasks after a short delay and capture the event for operator follow-up.",
            "enabled": True,
            "trigger": {"type": "task.orphaned", "config": {}},
            "conditions": None,
            "actions": [
                {
                    "type": "task.retry",
                    "params": {"delay_seconds": 120},
                    "continue_on_failure": False,
                },
                {
                    "type": "slack.notify",
                    "params": {
                        "config_id": "",
                        "template": "🧵 Orphaned task {{task_name}} on worker {{worker_name}} was retried automatically.",
                        "color": "#f59e0b",
                    },
                    "continue_on_failure": True,
                },
            ],
            "priority": 170,
            "cooldown_seconds": 180,
            "max_executions_per_hour": 6,
            "circuit_breaker": {
                "enabled": True,
                "max_executions": 2,
                "window_seconds": 600,
                "context_field": "task_name",
            },
        },
    },
    {
        "id": "worker-offline-alert",
        "name": "Worker offline alert",
        "description": "Page operators when a worker drops offline with a worker-scoped circuit breaker.",
        "scenario": "Worker offline",
        "recommended_for": ["worker.offline", "worker.heartbeat"],
        "workflow": {
            "name": "Worker offline alert",
            "description": "Notify operators when a worker goes offline or misses heartbeats.",
            "enabled": True,
            "trigger": {"type": "worker.offline", "config": {}},
            "conditions": None,
            "actions": [
                {
                    "type": "slack.notify",
                    "params": {
                        "config_id": "",
                        "template": "🛑 Worker {{worker_name}} is offline. Check queue {{queue}} and active tasks.",
                        "color": "#d92d20",
                    },
                    "continue_on_failure": False,
                },
            ],
            "priority": 220,
            "cooldown_seconds": 300,
            "max_executions_per_hour": 12,
            "circuit_breaker": {
                "enabled": True,
                "max_executions": 1,
                "window_seconds": 900,
                "context_field": "worker_name",
            },
        },
    },
    {
        "id": "long-running-task-followup",
        "name": "Long-running task follow-up",
        "description": "Use when a task-started stream should notify after an unusually long runtime window.",
        "scenario": "Long-running task",
        "recommended_for": ["task.started"],
        "workflow": {
            "name": "Long-running task follow-up",
            "description": "Alert on tasks that have been running longer than an agreed threshold.",
            "enabled": True,
            "trigger": {"type": "task.started", "config": {}},
            "conditions": {
                "operator": "AND",
                "conditions": [
                    {"field": "runtime", "operator": "gte", "value": 300},
                ],
            },
            "actions": [
                {
                    "type": "slack.notify",
                    "params": {
                        "config_id": "",
                        "template": "⏱️ {{task_name}} has been running longer than expected on {{queue}}.",
                        "color": "#7c3aed",
                    },
                    "continue_on_failure": False,
                },
            ],
            "priority": 150,
            "cooldown_seconds": 600,
            "max_executions_per_hour": 8,
            "circuit_breaker": {
                "enabled": True,
                "max_executions": 1,
                "window_seconds": 1800,
                "context_field": "task_name",
            },
        },
    },
    {
        "id": "error-rate-spike-escalation",
        "name": "Error-rate spike escalation",
        "description": "Use a high-priority failed-task template when many similar failures pile up quickly.",
        "scenario": "Error-rate spike",
        "recommended_for": ["task.failed"],
        "workflow": {
            "name": "Error-rate spike escalation",
            "description": "Escalate when the same task family starts failing rapidly.",
            "enabled": True,
            "trigger": {"type": "task.failed", "config": {}},
            "conditions": {
                "operator": "AND",
                "conditions": [
                    {"field": "retry_count", "operator": "gte", "value": 3},
                ],
            },
            "actions": [
                {
                    "type": "slack.notify",
                    "params": {
                        "config_id": "",
                        "template": "📈 Error-rate spike for {{task_name}} on {{queue}}. Recent exception: {{exception}}",
                        "color": "#d92d20",
                    },
                    "continue_on_failure": False,
                },
            ],
            "priority": 250,
            "cooldown_seconds": 120,
            "max_executions_per_hour": 20,
            "circuit_breaker": {
                "enabled": True,
                "max_executions": 2,
                "window_seconds": 900,
                "context_field": "task_name",
            },
        },
    },
]
