import unittest
from datetime import datetime, timezone, timedelta

from database import TaskProgressLatestDB
from services.task_service import TaskService
from tests.base import DatabaseTestCase


class TestTaskRuntimeAnomalies(DatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.service = TaskService(self.session)
        self.base_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    def _successful_baseline(self, task_name: str, runtimes: list[float]):
        for idx, runtime in enumerate(runtimes):
            self.create_task_event_db(
                task_id=f"baseline-{idx}",
                task_name=task_name,
                event_type="task-succeeded",
                timestamp=self.base_time - timedelta(hours=2, minutes=idx),
                runtime=runtime,
            )

    def _active_task(self, task_id: str, task_name: str, started_seconds_ago: int, hostname: str = "worker-1"):
        return self.create_task_event_db(
            task_id=task_id,
            task_name=task_name,
            event_type="task-started",
            timestamp=self.base_time - timedelta(seconds=started_seconds_ago),
            hostname=hostname,
        )

    def test_flags_long_running_task_against_task_family_baseline(self):
        self._successful_baseline("tasks.reports.generate", [20.0, 22.0, 18.0])
        self._active_task("active-1", "tasks.reports.generate", started_seconds_ago=360)

        anomalies = self.service.get_runtime_anomalies(
            now=self.base_time,
            min_long_running_seconds=30,
        )

        self.assertEqual(len(anomalies), 1)
        anomaly = anomalies[0]
        self.assertEqual(anomaly.task.task_id, "active-1")
        self.assertEqual(anomaly.anomaly_type, "long_running")
        self.assertAlmostEqual(anomaly.baseline_runtime_seconds, 20.0, places=1)
        self.assertEqual(anomaly.worker_active_task_count, 1)

    def test_flags_stalled_progress_for_active_task(self):
        self._active_task("active-2", "tasks.import.sync", started_seconds_ago=600, hostname="worker-2")
        self.session.add(TaskProgressLatestDB(
            task_id="active-2",
            task_name="tasks.import.sync",
            progress=45,
            message="Halfway there",
            updated_at=self.base_time - timedelta(seconds=420),
        ))
        self.session.commit()

        anomalies = self.service.get_runtime_anomalies(
            now=self.base_time,
            stalled_progress_seconds=300,
        )

        self.assertEqual(len(anomalies), 1)
        anomaly = anomalies[0]
        self.assertEqual(anomaly.anomaly_type, "stalled_progress")
        self.assertEqual(anomaly.task.task_id, "active-2")
        self.assertAlmostEqual(anomaly.progress_age_seconds, 420.0, places=1)

    def test_skips_long_running_classification_without_enough_baseline_samples(self):
        self._successful_baseline("tasks.cleanup", [12.0, 15.0])
        self._active_task("active-3", "tasks.cleanup", started_seconds_ago=900)

        anomalies = self.service.get_runtime_anomalies(
            now=self.base_time,
            min_long_running_seconds=30,
        )

        self.assertEqual(anomalies, [])

    def test_counts_other_active_tasks_on_same_worker(self):
        self._successful_baseline("tasks.reports.generate", [20.0, 22.0, 18.0])
        self._active_task("active-4", "tasks.reports.generate", started_seconds_ago=360, hostname="worker-3")
        self._active_task("active-5", "tasks.other", started_seconds_ago=60, hostname="worker-3")

        anomalies = self.service.get_runtime_anomalies(
            now=self.base_time,
            min_long_running_seconds=30,
        )

        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0].worker_active_task_count, 2)


if __name__ == "__main__":
    unittest.main()
