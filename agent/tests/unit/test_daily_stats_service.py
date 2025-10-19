import unittest
from datetime import datetime, timezone, timedelta, date

from services.daily_stats_service import DailyStatsService
from models import TaskEvent
from tests.base import DatabaseTestCase


class TestDailyStatsService(DatabaseTestCase):

    def setUp(self):
        super().setUp()
        self.service = DailyStatsService(self.session)
        self.base_time = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)

    def test_update_daily_stats_creates_new_record(self):
        task_event = self.create_task_event(
            task_id="task-1",
            task_name="tasks.example",
            event_type="task-received",
            timestamp=self.base_time
        )

        self.service.update_daily_stats(task_event)

        stats = self.service.get_stats_for_date("tasks.example", date(2024, 6, 15))
        self.assertIsNotNone(stats)
        self.assertEqual(stats.task_name, "tasks.example")
        self.assertEqual(stats.total_executions, 1)
        self.assertEqual(stats.pending, 1)

    def test_update_daily_stats_increments_total_executions_on_received(self):
        task_event = self.create_task_event(
            task_name="tasks.example",
            event_type="task-received",
            timestamp=self.base_time
        )

        self.service.update_daily_stats(task_event)
        stats = self.service.get_stats_for_date("tasks.example", date(2024, 6, 15))

        self.assertEqual(stats.total_executions, 1)
        self.assertEqual(stats.pending, 1)

    def test_update_daily_stats_increments_succeeded(self):
        task_received = self.create_task_event(
            task_id="task-1",
            task_name="tasks.example",
            event_type="task-received",
            timestamp=self.base_time
        )
        self.service.update_daily_stats(task_received)

        task_succeeded = self.create_task_event(
            task_id="task-1",
            task_name="tasks.example",
            event_type="task-succeeded",
            timestamp=self.base_time + timedelta(seconds=5),
            runtime=2.5
        )
        self.service.update_daily_stats(task_succeeded)

        stats = self.service.get_stats_for_date("tasks.example", date(2024, 6, 15))
        self.assertEqual(stats.succeeded, 1)
        self.assertEqual(stats.pending, 0)

    def test_update_daily_stats_increments_failed(self):
        task_received = self.create_task_event(
            task_name="tasks.example",
            event_type="task-received",
            timestamp=self.base_time
        )
        self.service.update_daily_stats(task_received)

        task_failed = self.create_task_event(
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=self.base_time + timedelta(seconds=5)
        )
        self.service.update_daily_stats(task_failed)

        stats = self.service.get_stats_for_date("tasks.example", date(2024, 6, 15))
        self.assertEqual(stats.failed, 1)
        self.assertEqual(stats.pending, 0)

    def test_update_daily_stats_increments_retried(self):
        task_event = self.create_task_event(
            task_name="tasks.example",
            event_type="task-retried",
            timestamp=self.base_time
        )

        self.service.update_daily_stats(task_event)

        stats = self.service.get_stats_for_date("tasks.example", date(2024, 6, 15))
        self.assertEqual(stats.retried, 1)

    def test_update_daily_stats_increments_revoked(self):
        task_received = self.create_task_event(
            task_name="tasks.example",
            event_type="task-received",
            timestamp=self.base_time
        )
        self.service.update_daily_stats(task_received)

        task_revoked = self.create_task_event(
            task_name="tasks.example",
            event_type="task-revoked",
            timestamp=self.base_time + timedelta(seconds=5)
        )
        self.service.update_daily_stats(task_revoked)

        stats = self.service.get_stats_for_date("tasks.example", date(2024, 6, 15))
        self.assertEqual(stats.revoked, 1)
        self.assertEqual(stats.pending, 0)

    def test_update_daily_stats_increments_orphaned(self):
        task_event = self.create_task_event(
            task_name="tasks.example",
            event_type="task-started",
            timestamp=self.base_time,
            is_orphan=True
        )

        self.service.update_daily_stats(task_event)

        stats = self.service.get_stats_for_date("tasks.example", date(2024, 6, 15))
        self.assertEqual(stats.orphaned, 1)

    def test_update_daily_stats_updates_runtime_stats(self):
        task_event = self.create_task_event(
            task_name="tasks.example",
            event_type="task-succeeded",
            timestamp=self.base_time,
            runtime=5.5
        )

        self.service.update_daily_stats(task_event)

        stats = self.service.get_stats_for_date("tasks.example", date(2024, 6, 15))
        self.assertEqual(stats.min_runtime, 5.5)
        self.assertEqual(stats.max_runtime, 5.5)
        self.assertEqual(stats.avg_runtime, 5.5)

    def test_update_daily_stats_calculates_min_runtime(self):
        self.service.update_daily_stats(self.create_task_event(
            task_name="tasks.example",
            event_type="task-succeeded",
            timestamp=self.base_time,
            runtime=10.0
        ))
        self.service.update_daily_stats(self.create_task_event(
            task_name="tasks.example",
            event_type="task-succeeded",
            timestamp=self.base_time + timedelta(seconds=1),
            runtime=5.0
        ))

        stats = self.service.get_stats_for_date("tasks.example", date(2024, 6, 15))
        self.assertEqual(stats.min_runtime, 5.0)

    def test_update_daily_stats_calculates_max_runtime(self):
        self.service.update_daily_stats(self.create_task_event(
            task_name="tasks.example",
            event_type="task-succeeded",
            timestamp=self.base_time,
            runtime=5.0
        ))
        self.service.update_daily_stats(self.create_task_event(
            task_name="tasks.example",
            event_type="task-succeeded",
            timestamp=self.base_time + timedelta(seconds=1),
            runtime=10.0
        ))

        stats = self.service.get_stats_for_date("tasks.example", date(2024, 6, 15))
        self.assertEqual(stats.max_runtime, 10.0)

    def test_update_daily_stats_calculates_avg_runtime(self):
        self.service.update_daily_stats(self.create_task_event(
            task_name="tasks.example",
            event_type="task-succeeded",
            timestamp=self.base_time,
            runtime=6.0
        ))
        self.service.update_daily_stats(self.create_task_event(
            task_name="tasks.example",
            event_type="task-succeeded",
            timestamp=self.base_time + timedelta(seconds=1),
            runtime=8.0
        ))
        self.service.update_daily_stats(self.create_task_event(
            task_name="tasks.example",
            event_type="task-succeeded",
            timestamp=self.base_time + timedelta(seconds=2),
            runtime=10.0
        ))

        stats = self.service.get_stats_for_date("tasks.example", date(2024, 6, 15))
        self.assertGreater(stats.avg_runtime, 6.0)
        self.assertLess(stats.avg_runtime, 10.0)

    def test_update_daily_stats_updates_first_execution(self):
        early_event = self.create_task_event(
            task_name="tasks.example",
            event_type="task-received",
            timestamp=self.base_time
        )
        self.service.update_daily_stats(early_event)

        later_event = self.create_task_event(
            task_name="tasks.example",
            event_type="task-received",
            timestamp=self.base_time + timedelta(hours=1)
        )
        self.service.update_daily_stats(later_event)

        stats = self.service.get_stats_for_date("tasks.example", date(2024, 6, 15))
        self.assertEqual(stats.first_execution.replace(tzinfo=timezone.utc), self.base_time)

    def test_update_daily_stats_updates_last_execution(self):
        early_event = self.create_task_event(
            task_name="tasks.example",
            event_type="task-received",
            timestamp=self.base_time
        )
        self.service.update_daily_stats(early_event)

        later_time = self.base_time + timedelta(hours=2)
        later_event = self.create_task_event(
            task_name="tasks.example",
            event_type="task-received",
            timestamp=later_time
        )
        self.service.update_daily_stats(later_event)

        stats = self.service.get_stats_for_date("tasks.example", date(2024, 6, 15))
        self.assertEqual(stats.last_execution.replace(tzinfo=timezone.utc), later_time)

    def test_update_daily_stats_separates_different_tasks(self):
        task1 = self.create_task_event(
            task_name="tasks.task1",
            event_type="task-received",
            timestamp=self.base_time
        )
        task2 = self.create_task_event(
            task_name="tasks.task2",
            event_type="task-received",
            timestamp=self.base_time
        )

        self.service.update_daily_stats(task1)
        self.service.update_daily_stats(task2)

        stats1 = self.service.get_stats_for_date("tasks.task1", date(2024, 6, 15))
        stats2 = self.service.get_stats_for_date("tasks.task2", date(2024, 6, 15))

        self.assertEqual(stats1.task_name, "tasks.task1")
        self.assertEqual(stats2.task_name, "tasks.task2")
        self.assertEqual(stats1.total_executions, 1)
        self.assertEqual(stats2.total_executions, 1)

    def test_update_daily_stats_separates_different_dates(self):
        day1_event = self.create_task_event(
            task_name="tasks.example",
            event_type="task-received",
            timestamp=datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        )
        day2_event = self.create_task_event(
            task_name="tasks.example",
            event_type="task-received",
            timestamp=datetime(2024, 6, 16, 12, 0, 0, tzinfo=timezone.utc)
        )

        self.service.update_daily_stats(day1_event)
        self.service.update_daily_stats(day2_event)

        stats_day1 = self.service.get_stats_for_date("tasks.example", date(2024, 6, 15))
        stats_day2 = self.service.get_stats_for_date("tasks.example", date(2024, 6, 16))

        self.assertEqual(stats_day1.total_executions, 1)
        self.assertEqual(stats_day2.total_executions, 1)

    def test_get_daily_stats_without_date_filters(self):
        for i in range(5):
            event = self.create_task_event(
                task_name="tasks.example",
                event_type="task-received",
                timestamp=self.base_time + timedelta(days=i)
            )
            self.service.update_daily_stats(event)

        stats = self.service.get_daily_stats("tasks.example")

        self.assertEqual(len(stats), 5)

    def test_get_daily_stats_with_start_date_filter(self):
        for i in range(5):
            event = self.create_task_event(
                task_name="tasks.example",
                event_type="task-received",
                timestamp=self.base_time + timedelta(days=i)
            )
            self.service.update_daily_stats(event)

        start_date = date(2024, 6, 17)
        stats = self.service.get_daily_stats("tasks.example", start_date=start_date)

        self.assertEqual(len(stats), 3)

    def test_get_daily_stats_with_end_date_filter(self):
        for i in range(5):
            event = self.create_task_event(
                task_name="tasks.example",
                event_type="task-received",
                timestamp=self.base_time + timedelta(days=i)
            )
            self.service.update_daily_stats(event)

        end_date = date(2024, 6, 17)
        stats = self.service.get_daily_stats("tasks.example", end_date=end_date)

        self.assertEqual(len(stats), 3)

    def test_get_daily_stats_with_limit(self):
        for i in range(10):
            event = self.create_task_event(
                task_name="tasks.example",
                event_type="task-received",
                timestamp=self.base_time + timedelta(days=i)
            )
            self.service.update_daily_stats(event)

        stats = self.service.get_daily_stats("tasks.example", limit=5)

        self.assertEqual(len(stats), 5)

    def test_get_daily_stats_ordered_by_date_descending(self):
        for i in range(3):
            event = self.create_task_event(
                task_name="tasks.example",
                event_type="task-received",
                timestamp=self.base_time + timedelta(days=i)
            )
            self.service.update_daily_stats(event)

        stats = self.service.get_daily_stats("tasks.example")

        self.assertEqual(stats[0].date, date(2024, 6, 17))
        self.assertEqual(stats[1].date, date(2024, 6, 16))
        self.assertEqual(stats[2].date, date(2024, 6, 15))

    def test_get_stats_for_date_not_found_returns_none(self):
        result = self.service.get_stats_for_date("tasks.nonexistent", date(2024, 6, 15))
        self.assertIsNone(result)

    def test_get_all_tasks_stats_for_date(self):
        task1 = self.create_task_event(
            task_name="tasks.task1",
            event_type="task-received",
            timestamp=self.base_time
        )
        task2 = self.create_task_event(
            task_name="tasks.task2",
            event_type="task-received",
            timestamp=self.base_time
        )

        self.service.update_daily_stats(task1)
        self.service.update_daily_stats(task2)

        stats = self.service.get_all_tasks_stats_for_date(date(2024, 6, 15))

        self.assertEqual(len(stats), 2)
        task_names = {s.task_name for s in stats}
        self.assertEqual(task_names, {"tasks.task1", "tasks.task2"})

    def test_get_all_tasks_stats_for_date_ordered_by_executions(self):
        for i in range(5):
            self.service.update_daily_stats(self.create_task_event(
                task_name="tasks.high_volume",
                event_type="task-received",
                timestamp=self.base_time + timedelta(seconds=i)
            ))

        self.service.update_daily_stats(self.create_task_event(
            task_name="tasks.low_volume",
            event_type="task-received",
            timestamp=self.base_time
        ))

        stats = self.service.get_all_tasks_stats_for_date(date(2024, 6, 15))

        self.assertEqual(stats[0].task_name, "tasks.high_volume")
        self.assertEqual(stats[0].total_executions, 5)
        self.assertEqual(stats[1].task_name, "tasks.low_volume")
        self.assertEqual(stats[1].total_executions, 1)

    def test_get_task_trend_summary_basic(self):
        for i in range(3):
            event = self.create_task_event(
                task_name="tasks.example",
                event_type="task-received",
                timestamp=datetime.now(timezone.utc) - timedelta(days=i)
            )
            self.service.update_daily_stats(event)

        summary = self.service.get_task_trend_summary("tasks.example", days=7)

        self.assertEqual(summary['task_name'], "tasks.example")
        self.assertEqual(summary['days'], 7)
        self.assertEqual(summary['total_executions'], 3)

    def test_get_task_trend_summary_calculates_success_rate(self):
        today = datetime.now(timezone.utc).date()
        base = datetime.now(timezone.utc)

        for i in range(8):
            self.service.update_daily_stats(self.create_task_event(
                task_name="tasks.example",
                event_type="task-received",
                timestamp=base - timedelta(days=i % 3)
            ))

        for i in range(6):
            self.service.update_daily_stats(self.create_task_event(
                task_name="tasks.example",
                event_type="task-succeeded",
                timestamp=base - timedelta(days=i % 3),
                runtime=1.0
            ))

        for i in range(2):
            self.service.update_daily_stats(self.create_task_event(
                task_name="tasks.example",
                event_type="task-failed",
                timestamp=base - timedelta(days=i % 3)
            ))

        summary = self.service.get_task_trend_summary("tasks.example", days=7)

        self.assertEqual(summary['total_succeeded'], 6)
        self.assertEqual(summary['total_failed'], 2)
        self.assertEqual(summary['avg_success_rate'], 75.0)
        self.assertEqual(summary['avg_failure_rate'], 25.0)

    def test_get_task_trend_summary_calculates_avg_runtime(self):
        base = datetime.now(timezone.utc)

        self.service.update_daily_stats(self.create_task_event(
            task_name="tasks.example",
            event_type="task-succeeded",
            timestamp=base,
            runtime=5.0
        ))
        self.service.update_daily_stats(self.create_task_event(
            task_name="tasks.example",
            event_type="task-succeeded",
            timestamp=base - timedelta(days=1),
            runtime=3.0
        ))

        summary = self.service.get_task_trend_summary("tasks.example", days=7)

        self.assertIsNotNone(summary['avg_runtime'])
        self.assertGreater(summary['avg_runtime'], 0)

    def test_get_task_trend_summary_no_data_returns_zeros(self):
        summary = self.service.get_task_trend_summary("tasks.nonexistent", days=7)

        self.assertEqual(summary['task_name'], "tasks.nonexistent")
        self.assertEqual(summary['total_executions'], 0)
        self.assertEqual(summary['avg_success_rate'], 0)
        self.assertEqual(summary['avg_failure_rate'], 0)
        self.assertIsNone(summary['avg_runtime'])

    def test_update_daily_stats_handles_naive_datetime(self):
        naive_time = datetime(2024, 6, 15, 12, 0, 0)
        task_event = self.create_task_event(
            task_name="tasks.example",
            event_type="task-received",
            timestamp=naive_time
        )

        self.service.update_daily_stats(task_event)

        stats = self.service.get_stats_for_date("tasks.example", date(2024, 6, 15))
        self.assertIsNotNone(stats)


if __name__ == '__main__':
    unittest.main()
