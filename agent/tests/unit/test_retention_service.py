import unittest
from datetime import date, datetime, timedelta, timezone

from database import TaskDailyStatsDB, TaskProgressDB, UserSessionDB, WorkflowExecutionDB
from services.retention_service import RetentionService
from tests.base import DatabaseTestCase


class TestRetentionService(DatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.service = RetentionService(self.session)

    def test_cleanup_dry_run_counts_without_deleting(self):
        now = datetime.now(timezone.utc)
        self.create_task_event_db(task_id="old-task", timestamp=now - timedelta(days=45))
        self.create_task_event_db(task_id="new-task", timestamp=now - timedelta(days=2))
        self.create_worker_event_db(hostname="old-worker", timestamp=now - timedelta(days=45))

        self.session.add(TaskProgressDB(task_id="old-task", task_name="tasks.old", progress=0.1, timestamp=now - timedelta(days=30)))
        self.session.add(WorkflowExecutionDB(workflow_id="wf-1", trigger_type="task.failed", trigger_event={}, status="completed", triggered_at=now - timedelta(days=40)))
        self.session.add(TaskDailyStatsDB(task_name="tasks.old", date=date.today() - timedelta(days=400)))
        self.session.add(UserSessionDB(session_id="session-old", last_active=now - timedelta(days=31), created_at=now - timedelta(days=31), preferences={}))
        self.session.commit()

        result = self.service.cleanup(dry_run=True)

        self.assertTrue(result.dry_run)
        self.assertEqual(result.total_deleted, 6)
        self.assertEqual(self.session.query(TaskProgressDB).count(), 1)
        self.assertEqual(self.session.query(WorkflowExecutionDB).count(), 1)
        self.assertEqual(self.session.query(UserSessionDB).count(), 1)

    def test_cleanup_deletes_rows_older_than_policy(self):
        now = datetime.now(timezone.utc)
        self.create_task_event_db(task_id="old-task", timestamp=now - timedelta(days=45))
        self.create_task_event_db(task_id="new-task", timestamp=now - timedelta(days=1))
        self.session.add(TaskProgressDB(task_id="old-task", task_name="tasks.old", progress=0.2, timestamp=now - timedelta(days=20)))
        self.session.add(TaskProgressDB(task_id="new-task", task_name="tasks.new", progress=0.8, timestamp=now - timedelta(days=1)))
        self.session.add(UserSessionDB(session_id="session-old", last_active=now - timedelta(days=60), created_at=now - timedelta(days=60), preferences={}))
        self.session.add(UserSessionDB(session_id="session-new", last_active=now - timedelta(days=1), created_at=now - timedelta(days=1), preferences={}))
        self.session.commit()

        result = self.service.cleanup(dry_run=False)

        self.assertFalse(result.dry_run)
        self.assertEqual(self.get_task_events_by_id("old-task"), [])
        self.assertEqual(len(self.get_task_events_by_id("new-task")), 1)
        self.assertEqual(self.session.query(TaskProgressDB).count(), 1)
        self.assertEqual(self.session.query(UserSessionDB).count(), 1)
        self.assertGreaterEqual(result.total_deleted, 3)


if __name__ == "__main__":
    unittest.main()
