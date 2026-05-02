import unittest
from datetime import datetime, timezone, timedelta

from database import TaskResolutionDB
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

    def test_classifies_new_recurring_and_regressed_failures(self):
        base_exception = "ValueError: boom"

        self.create_task_event_db(
            task_id="prior-recurring",
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=self.now - timedelta(hours=30),
            exception=base_exception,
        )
        self.create_task_event_db(
            task_id="prior-regressed",
            task_name="tasks.other",
            event_type="task-failed",
            timestamp=self.now - timedelta(hours=28),
            exception="TimeoutError: upstream",
        )
        self.service.set_task_resolution("prior-regressed", resolved_by="tester")
        resolution = (
            self.session.query(TaskResolutionDB)
            .filter(TaskResolutionDB.task_id == "prior-regressed")
            .one()
        )
        resolution.resolved_at = self.now - timedelta(hours=20)
        self.service._update_task_latest_resolution(
            "prior-regressed",
            True,
            "tester",
            resolution.resolved_at,
        )
        self.session.commit()
        self.create_task_event_db(
            task_id="current-new",
            task_name="tasks.brand_new",
            event_type="task-failed",
            timestamp=self.now - timedelta(minutes=20),
            exception="LookupError: never seen",
        )
        self.create_task_event_db(
            task_id="current-recurring",
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=self.now - timedelta(minutes=10),
            exception=base_exception,
        )
        self.create_task_event_db(
            task_id="current-regressed",
            task_name="tasks.other",
            event_type="task-failed",
            timestamp=self.now - timedelta(minutes=5),
            exception="TimeoutError: upstream",
        )

        results = self.service.get_recent_failed_tasks(hours=24, novelty_lookback_hours=168, sort_by="novelty")
        by_id = {task.task_id: task for task in results}

        self.assertEqual(by_id["current-new"].failure_novelty_status, "new")
        self.assertEqual(by_id["current-recurring"].failure_novelty_status, "recurring")
        self.assertEqual(by_id["current-regressed"].failure_novelty_status, "regressed")
        self.assertEqual(results[0].task_id, "current-new")
        self.assertEqual(results[1].task_id, "current-regressed")

    def test_filters_by_novelty_status(self):
        self.create_task_event_db(
            task_id="prior-known",
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=self.now - timedelta(hours=30),
            exception="RuntimeError: repeated",
        )
        self.create_task_event_db(
            task_id="current-known",
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=self.now - timedelta(minutes=15),
            exception="RuntimeError: repeated",
        )
        self.create_task_event_db(
            task_id="current-new",
            task_name="tasks.unique",
            event_type="task-failed",
            timestamp=self.now - timedelta(minutes=5),
            exception="KeyError: fresh",
        )

        results = self.service.get_recent_failed_tasks(
            hours=24,
            novelty_status="new",
            novelty_lookback_hours=168,
        )

        self.assertEqual([task.task_id for task in results], ["current-new"])

    def test_novelty_sorting_applies_before_limit(self):
        self.create_task_event_db(
            task_id="recent-recurring-prior",
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=self.now - timedelta(hours=30),
            exception="RuntimeError: repeated",
        )
        self.create_task_event_db(
            task_id="recent-recurring-current",
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=self.now - timedelta(minutes=3),
            exception="RuntimeError: repeated",
        )
        self.create_task_event_db(
            task_id="slightly-older-new",
            task_name="tasks.unique",
            event_type="task-failed",
            timestamp=self.now - timedelta(minutes=6),
            exception="LookupError: fresh",
        )

        results = self.service.get_recent_failed_tasks(
            hours=24,
            limit=1,
            novelty_lookback_hours=168,
            sort_by="novelty",
        )

        self.assertEqual([task.task_id for task in results], ["slightly-older-new"])

    def test_regressed_only_when_latest_prior_occurrence_was_resolved(self):
        self.create_task_event_db(
            task_id="prior-resolved",
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=self.now - timedelta(hours=10),
            exception="RuntimeError: repeated",
        )
        self.service.set_task_resolution("prior-resolved", resolved_by="tester")
        self.create_task_event_db(
            task_id="prior-unresolved",
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=self.now - timedelta(hours=2),
            exception="RuntimeError: repeated",
        )
        self.create_task_event_db(
            task_id="current-failure",
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=self.now - timedelta(minutes=5),
            exception="RuntimeError: repeated",
        )

        results = self.service.get_recent_failed_tasks(hours=24, novelty_lookback_hours=168)
        by_id = {task.task_id: task for task in results}

        self.assertEqual(by_id["current-failure"].failure_novelty_status, "recurring")


if __name__ == "__main__":
    unittest.main()
