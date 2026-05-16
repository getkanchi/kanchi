import asyncio
from datetime import datetime, timezone
from unittest.mock import Mock

from database import AuditLogDB
from models import ActionConfig, TaskEvent, TriggerConfig, WorkflowDefinition
from services.workflow_executor import WorkflowExecutor
from tests.base import DatabaseTestCase


class TestWorkflowAuditLogging(DatabaseTestCase):
    def test_workflow_executor_records_action_and_execution_audit_entries(self):
        self.create_task_event_db(
            task_id="task-123",
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=datetime(2026, 4, 30, 12, 0, tzinfo=timezone.utc),
        )

        monitor_instance = Mock()
        monitor_instance.app = Mock()
        monitor_instance.app.send_task = Mock(return_value=None)

        workflow = WorkflowDefinition(
            id="workflow-123",
            name="Retry failed task",
            trigger=TriggerConfig(type="task.failed", config={}),
            actions=[
                ActionConfig(
                    type="task.retry",
                    params={"max_retries": 3},
                    continue_on_failure=False,
                )
            ],
        )

        context = {
            "task_id": "task-123",
            "task_name": "tasks.example",
            "root_id": "task-123",
            "args": [],
            "kwargs": {},
        }
        event = TaskEvent(
            task_id="task-123",
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=datetime(2026, 4, 30, 12, 0, tzinfo=timezone.utc),
        )

        executor = WorkflowExecutor(
            session=self.session,
            db_manager=None,
            monitor_instance=monitor_instance,
        )

        asyncio.run(executor.execute_workflow(workflow, context, event))

        entries = self.session.query(AuditLogDB).order_by(AuditLogDB.id.asc()).all()
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].action_type, "workflow.action.task.retry")
        self.assertEqual(entries[0].status, "success")
        self.assertEqual(entries[0].task_id, "task-123")
        self.assertEqual(entries[1].action_type, "workflow.execution")
        self.assertEqual(entries[1].status, "success")
