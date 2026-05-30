import unittest
from datetime import datetime, timedelta, timezone

from database import RetryRelationshipDB, TaskRerunRelationshipDB
from services.task_registry_service import TaskRegistryService
from tests.base import DatabaseTestCase


class TestTaskRegistryServiceStats(DatabaseTestCase):

    def setUp(self):
        super().setUp()
        self.service = TaskRegistryService(self.session)
        self.now = datetime.now(timezone.utc)

    def test_failed_stat_counts_unaddressed_failures(self):
        self.create_task_event_db(
            task_id="failed-unaddressed",
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=self.now - timedelta(minutes=30),
        )

        stats = self.service.get_task_stats("tasks.example", hours=24)

        self.assertEqual(stats.failed, 1)

    def test_failed_stat_excludes_celery_retried_failures(self):
        self.create_task_event_db(
            task_id="failed-retried",
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=self.now - timedelta(minutes=30),
        )
        self.session.add(RetryRelationshipDB(
            task_id="failed-retried",
            original_id="failed-retried",
            retry_chain=["retry-child"],
            total_retries=1,
        ))
        self.session.commit()

        stats = self.service.get_task_stats("tasks.example", hours=24)

        self.assertEqual(stats.failed, 0)

    def test_failed_stat_excludes_manually_rerun_failures(self):
        self.create_task_event_db(
            task_id="failed-rerun",
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=self.now - timedelta(minutes=30),
        )
        self.session.add(TaskRerunRelationshipDB(
            original_task_id="failed-rerun",
            rerun_task_id="rerun-child",
            created_by="tester",
        ))
        self.session.commit()

        stats = self.service.get_task_stats("tasks.example", hours=24)

        self.assertEqual(stats.failed, 0)

    def test_failed_rerun_child_counts_as_its_own_unaddressed_failure(self):
        self.create_task_event_db(
            task_id="failed-rerun",
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=self.now - timedelta(minutes=30),
        )
        self.create_task_event_db(
            task_id="rerun-child",
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=self.now - timedelta(minutes=20),
        )
        self.session.add(TaskRerunRelationshipDB(
            original_task_id="failed-rerun",
            rerun_task_id="rerun-child",
            created_by="tester",
        ))
        self.session.commit()

        stats = self.service.get_task_stats("tasks.example", hours=24)

        self.assertEqual(stats.failed, 1)


if __name__ == "__main__":
    unittest.main()
