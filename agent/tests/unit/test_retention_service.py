import unittest
from datetime import date, datetime, timedelta, timezone

from constants import EventType
from database import (
    TaskDailyStatsDB,
    TaskLatestDB,
    TaskProgressDB,
    TaskProgressLatestDB,
    TaskStepsDB,
    UserSessionDB,
    WorkflowExecutionDB,
)
from services.retention_service import RetentionService
from tests.base import DatabaseTestCase


class TestRetentionService(DatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.service = RetentionService(self.session)

    def _create_task_family(self, *, task_id: str, age_days: int, event_type: str, is_orphan: bool = False):
        timestamp = datetime.now(timezone.utc) - timedelta(days=age_days)
        self.create_task_event_db(
            task_id=task_id,
            task_name=f"tasks.{task_id}",
            event_type=event_type,
            timestamp=timestamp,
            is_orphan=is_orphan,
        )
        self.session.add(
            TaskLatestDB(
                task_id=task_id,
                event_id=1,
                task_name=f"tasks.{task_id}",
                event_type=event_type,
                timestamp=timestamp,
                is_orphan=is_orphan,
                resolved=False,
                has_retries=False,
                retry_count=0,
            )
        )
        self.session.add(TaskProgressDB(task_id=task_id, task_name=f"tasks.{task_id}", progress=0.5, timestamp=timestamp))
        self.session.add(TaskProgressLatestDB(task_id=task_id, task_name=f"tasks.{task_id}", progress=0.5, updated_at=timestamp))
        self.session.add(TaskStepsDB(task_id=task_id, task_name=f"tasks.{task_id}", steps=[{"key": "one"}], defined_at=timestamp))

    def test_cleanup_dry_run_counts_unsuccessful_tasks_separately(self):
        now = datetime.now(timezone.utc)
        self._create_task_family(task_id="old-success", age_days=20, event_type=EventType.TASK_SUCCEEDED)
        self._create_task_family(task_id="old-failed", age_days=20, event_type=EventType.TASK_FAILED)
        self.create_worker_event_db(hostname="old-worker", timestamp=now - timedelta(days=45))
        self.session.add(WorkflowExecutionDB(workflow_id="wf-1", trigger_type="task.failed", trigger_event={}, status="completed", triggered_at=now - timedelta(days=40)))
        self.session.add(TaskDailyStatsDB(task_name="tasks.old", date=date.today() - timedelta(days=400)))
        self.session.add(UserSessionDB(session_id="session-old", last_active=now - timedelta(days=31), created_at=now - timedelta(days=31), preferences={}))
        self.session.commit()

        result = self.service.cleanup(dry_run=True)
        counts = {item.key: item.deleted for item in result.results}

        self.assertTrue(result.dry_run)
        self.assertEqual(counts["task_events_successful"], 1)
        self.assertEqual(counts["task_events_unsuccessful"], 0)
        self.assertEqual(counts["task_progress_successful"], 1)
        self.assertEqual(counts["task_latest_successful"], 1)
        self.assertEqual(counts["task_latest_unsuccessful"], 0)
        self.assertEqual(self.session.query(TaskProgressDB).count(), 2)
        self.assertEqual(self.session.query(WorkflowExecutionDB).count(), 1)
        self.assertEqual(self.session.query(UserSessionDB).count(), 1)

    def test_cleanup_deletes_successful_tasks_before_unsuccessful_ones(self):
        now = datetime.now(timezone.utc)
        self._create_task_family(task_id="old-success", age_days=20, event_type=EventType.TASK_SUCCEEDED)
        self._create_task_family(task_id="old-failed", age_days=20, event_type=EventType.TASK_FAILED)
        self._create_task_family(task_id="very-old-failed", age_days=45, event_type=EventType.TASK_FAILED)
        self.session.add(UserSessionDB(session_id="session-old", last_active=now - timedelta(days=60), created_at=now - timedelta(days=60), preferences={}))
        self.session.add(UserSessionDB(session_id="session-new", last_active=now - timedelta(days=1), created_at=now - timedelta(days=1), preferences={}))
        self.session.commit()

        result = self.service.cleanup(dry_run=False)

        self.assertFalse(result.dry_run)
        self.assertEqual(self.get_task_events_by_id("old-success"), [])
        self.assertEqual(len(self.get_task_events_by_id("old-failed")), 1)
        self.assertEqual(self.get_task_events_by_id("very-old-failed"), [])
        remaining_latest_ids = {row.task_id for row in self.session.query(TaskLatestDB).all()}
        self.assertEqual(remaining_latest_ids, {"old-failed"})
        self.assertEqual(self.session.query(TaskProgressDB).count(), 1)
        self.assertEqual(self.session.query(UserSessionDB).count(), 1)
        self.assertGreaterEqual(result.total_deleted, 11)


if __name__ == "__main__":
    unittest.main()
