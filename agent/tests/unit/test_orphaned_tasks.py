import unittest
from datetime import datetime, timezone, timedelta

from database import RetryRelationshipDB, TaskEventDB
from services.task_service import TaskService
from tests.base import DatabaseTestCase


class TestGetUnretriedOrphanedTasks(DatabaseTestCase):

    def setUp(self):
        super().setUp()
        self.service = TaskService(self.session)
        self.base_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    def _orphaned(self, task_id, event_type="task-started", offset_seconds=0):
        """Helper: create a task_events row marked as orphaned."""
        return self.create_task_event_db(
            task_id=task_id,
            event_type=event_type,
            timestamp=self.base_time + timedelta(seconds=offset_seconds),
            is_orphan=True,
            orphaned_at=self.base_time + timedelta(seconds=offset_seconds),
        )

    def test_returns_orphaned_task_with_no_retry_and_no_final_state(self):
        """Orphaned task with no retry chain and no final-state event is included."""
        self._orphaned("task-1")

        result = self.service.get_unretried_orphaned_tasks()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].task_id, "task-1")

    def test_excludes_task_with_retry_chain(self):
        """Orphaned task that has been retried (non-empty retry_chain) is excluded."""
        self._orphaned("task-retried")
        self.session.add(RetryRelationshipDB(
            task_id="task-retried",
            original_id="task-retried",
            retry_chain=["task-new-1"],
            total_retries=1,
        ))
        self.session.commit()

        result = self.service.get_unretried_orphaned_tasks()

        self.assertEqual(len(result), 0)

    def test_excludes_task_with_final_state_event(self):
        """Orphaned task that also has a task-succeeded event is excluded."""
        self._orphaned("task-done", event_type="task-started")
        self.create_task_event_db(
            task_id="task-done",
            event_type="task-succeeded",
            timestamp=self.base_time + timedelta(seconds=10),
        )

        result = self.service.get_unretried_orphaned_tasks()

        self.assertEqual(len(result), 0)

    def test_mixed_set_returns_only_qualifying_tasks(self):
        """Only tasks with no retry chain and no final-state event are returned."""
        # Should be returned
        self._orphaned("task-ok", offset_seconds=0)

        # Should be excluded: has retry chain
        self._orphaned("task-retried", offset_seconds=1)
        self.session.add(RetryRelationshipDB(
            task_id="task-retried",
            original_id="task-retried",
            retry_chain=["task-new"],
            total_retries=1,
        ))

        # Should be excluded: has final-state event
        self._orphaned("task-done", offset_seconds=2)
        self.create_task_event_db(
            task_id="task-done",
            event_type="task-failed",
            timestamp=self.base_time + timedelta(seconds=30),
        )
        self.session.commit()

        result = self.service.get_unretried_orphaned_tasks()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].task_id, "task-ok")


if __name__ == "__main__":
    unittest.main()
