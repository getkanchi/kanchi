from datetime import datetime, timezone

from database import TaskAnnotationDB
from services.task_service import TaskService
from models import BulkTaskActionRequest
from tests.base import DatabaseTestCase


class TestBulkTaskActions(DatabaseTestCase):
    def test_preview_reports_executable_skipped_and_missing_tasks(self):
        self.create_task_event_db(
            task_id="failed-1",
            task_name="tasks.sync",
            event_type="task-failed",
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )
        self.create_task_event_db(
            task_id="started-1",
            task_name="tasks.sync",
            event_type="task-started",
            timestamp=datetime(2024, 1, 1, 12, 1, 0, tzinfo=timezone.utc),
        )

        result = TaskService(self.session).preview_bulk_task_action(BulkTaskActionRequest(
            action="retry",
            dry_run=True,
            task_ids=["failed-1", "started-1", "missing-1"],
        ))

        self.assertEqual(result.requested_count, 3)
        self.assertEqual(result.executable_count, 1)
        statuses = {item.task_id: item.status for item in result.results}
        self.assertEqual(statuses["failed-1"], "pending")
        self.assertEqual(statuses["started-1"], "skipped")
        self.assertEqual(statuses["missing-1"], "failed")

    def test_execute_resolve_reports_partial_success(self):
        self.create_task_event_db(
            task_id="failed-1",
            task_name="tasks.sync",
            event_type="task-failed",
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        result = TaskService(self.session).execute_bulk_task_action(BulkTaskActionRequest(
            action="resolve",
            dry_run=False,
            task_ids=["failed-1", "missing-1"],
            operator="operator@example.test",
        ))

        self.assertEqual(result.success_count, 1)
        self.assertEqual(result.failure_count, 1)
        self.assertTrue(TaskService(self.session).get_task_resolution("failed-1").resolved)

    def test_annotate_requires_comment(self):
        self.create_task_event_db(task_id="failed-1", event_type="task-failed")

        result = TaskService(self.session).preview_bulk_task_action(BulkTaskActionRequest(
            action="annotate",
            dry_run=True,
            task_ids=["failed-1"],
        ))

        self.assertEqual(result.executable_count, 0)
        self.assertEqual(result.results[0].status, "skipped")

    def test_execute_annotate_persists_annotation(self):
        self.create_task_event_db(task_id="failed-1", event_type="task-failed")

        result = TaskService(self.session).execute_bulk_task_action(BulkTaskActionRequest(
            action="annotate",
            dry_run=False,
            task_ids=["failed-1"],
            comment="Operator note",
            operator="operator@example.test",
        ))

        self.assertEqual(result.success_count, 1)
        annotations = self.session.query(TaskAnnotationDB).filter_by(task_id="failed-1").all()
        self.assertEqual(len(annotations), 1)
        self.assertEqual(annotations[0].comment, "Operator note")
        self.assertEqual(annotations[0].operator, "operator@example.test")
