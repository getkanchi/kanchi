import unittest
from datetime import datetime, timezone, timedelta

from services.task_service import TaskService
from tests.base import DatabaseTestCase


class TestTaskServiceRecentFailedTasks(DatabaseTestCase):

    def setUp(self):
        super().setUp()
        self.service = TaskService(self.session)
        self.now = datetime.now(timezone.utc)

    def test_returns_only_recent_failed_tasks(self):
        recent_failure_time = self.now - timedelta(hours=1)
        old_failure_time = self.now - timedelta(hours=48)

        self.create_task_event_db(
            task_id="failed-recent",
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=recent_failure_time
        )
        self.create_task_event_db(
            task_id="failed-old",
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=old_failure_time
        )
        self.create_task_event_db(
            task_id="succeeded-recent",
            task_name="tasks.example",
            event_type="task-succeeded",
            timestamp=self.now
        )

        results = self.service.get_recent_failed_tasks(hours=24, limit=10)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].task_id, "failed-recent")

    def test_excludes_retried_failures_by_default(self):
        recent_time = self.now - timedelta(minutes=30)

        self.create_task_event_db(
            task_id="failed-unretried",
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=recent_time,
            has_retries=False,
            retried_by=None
        )
        self.create_task_event_db(
            task_id="failed-retried",
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=recent_time - timedelta(minutes=1),
            has_retries=True,
            retried_by='["child-task"]'
        )

        results = self.service.get_recent_failed_tasks(hours=24)
        task_ids = {task.task_id for task in results}

        self.assertIn("failed-unretried", task_ids)
        self.assertNotIn("failed-retried", task_ids)

        results_including_retried = self.service.get_recent_failed_tasks(
            hours=24,
            exclude_retried=False
        )
        task_ids_including = {task.task_id for task in results_including_retried}

        self.assertIn("failed-retried", task_ids_including)

    def test_results_respect_limit_and_order(self):
        for index in range(3):
            self.create_task_event_db(
                task_id=f"failed-{index}",
                task_name="tasks.example",
                event_type="task-failed",
                timestamp=self.now - timedelta(hours=index)
            )

        results = self.service.get_recent_failed_tasks(hours=24, limit=2)
        ordered_ids = [task.task_id for task in results]

        self.assertEqual(len(ordered_ids), 2)
        self.assertEqual(ordered_ids, ["failed-0", "failed-1"])


if __name__ == "__main__":
    unittest.main()
