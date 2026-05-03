import unittest
from datetime import datetime, timezone, timedelta

from database import TaskProgressLatestDB
from services.task_service import TaskService
from tests.base import DatabaseTestCase


class TestTriageRecommendations(DatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.service = TaskService(self.session)
        self.base_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    def _successful_baseline(self, task_name: str, runtimes: list[float]):
        for idx, runtime in enumerate(runtimes):
            self.create_task_event_db(
                task_id=f"baseline-{task_name}-{idx}",
                task_name=task_name,
                event_type="task-succeeded",
                timestamp=self.base_time - timedelta(hours=6, minutes=idx),
                runtime=runtime,
            )

    def _active_task(self, task_id: str, task_name: str, started_seconds_ago: int, hostname: str = "worker-1"):
        self.create_task_event_db(
            task_id=task_id,
            task_name=task_name,
            event_type="task-started",
            timestamp=self.base_time - timedelta(seconds=started_seconds_ago),
            hostname=hostname,
        )

    def test_prioritizes_stalled_and_orphaned_recommendations(self):
        self._active_task("stalled-1", "tasks.sync", started_seconds_ago=900, hostname="worker-a")
        self.session.add(TaskProgressLatestDB(
            task_id="stalled-1",
            task_name="tasks.sync",
            progress=55,
            message="Waiting",
            updated_at=self.base_time - timedelta(seconds=700),
        ))
        self.session.commit()

        self.create_task_event_db(
            task_id="orphan-1",
            task_name="tasks.cleanup",
            event_type="task-started",
            timestamp=self.base_time - timedelta(minutes=20),
            hostname="worker-b",
            is_orphan=True,
            orphaned_at=self.base_time - timedelta(minutes=5),
        )

        recommendations = self.service.get_triage_recommendations(now=self.base_time)

        self.assertEqual(recommendations[0].recommendation_type, "orphaned_task")
        self.assertEqual(recommendations[1].recommendation_type, "stalled_progress")
        self.assertTrue(all(item.severity == "critical" for item in recommendations[:2]))

    def test_detects_repeating_failures_for_same_task_family(self):
        for idx in range(3):
            self.create_task_event_db(
                task_id=f"failed-{idx}",
                task_name="tasks.billing.sync",
                event_type="task-failed",
                timestamp=self.base_time - timedelta(minutes=idx),
                hostname="worker-c",
                exception="boom",
            )

        recommendations = self.service.get_triage_recommendations(now=self.base_time, failed_hours=24)

        repeating = next(item for item in recommendations if item.recommendation_type == "repeating_failures")
        self.assertEqual(repeating.task_name, "tasks.billing.sync")
        self.assertEqual(len(repeating.supporting_task_ids), 3)
        self.assertEqual(repeating.severity, "warning")

    def test_detects_long_running_recommendation(self):
        self._successful_baseline("tasks.reports.generate", [20.0, 22.0, 18.0])
        self._active_task("long-1", "tasks.reports.generate", started_seconds_ago=360, hostname="worker-z")

        recommendations = self.service.get_triage_recommendations(now=self.base_time)

        long_running = next(item for item in recommendations if item.recommendation_type == "long_running")
        self.assertEqual(long_running.task_id, "long-1")
        self.assertEqual(long_running.severity, "info")


if __name__ == "__main__":
    unittest.main()
