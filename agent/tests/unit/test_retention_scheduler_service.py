import unittest
from datetime import datetime, timedelta, timezone

from models import RetentionLastRun, RetentionScheduleConfig
from services.retention_scheduler_service import RetentionSchedulerService


class TestRetentionSchedulerService(unittest.TestCase):
    def test_daily_schedule_is_due_after_run_time_when_not_run_today(self):
        now = datetime(2026, 5, 16, 4, 0, tzinfo=timezone.utc)
        last_run = RetentionLastRun(
            status="success",
            finished_at=now - timedelta(days=1),
            total_deleted=0,
        )

        schedule = RetentionScheduleConfig(preset="daily", hour=3, minute=0)
        self.assertTrue(RetentionSchedulerService.is_due(schedule, last_run, now))

    def test_daily_schedule_is_not_due_before_run_time(self):
        now = datetime(2026, 5, 16, 2, 59, tzinfo=timezone.utc)
        schedule = RetentionScheduleConfig(preset="daily", hour=3, minute=0)

        self.assertFalse(RetentionSchedulerService.is_due(schedule, RetentionLastRun(), now))

    def test_daily_schedule_runs_only_once_per_scheduled_time(self):
        now = datetime(2026, 5, 16, 4, 0, tzinfo=timezone.utc)
        last_run = RetentionLastRun(
            status="success",
            finished_at=datetime(2026, 5, 16, 3, 1, tzinfo=timezone.utc),
            total_deleted=0,
        )
        schedule = RetentionScheduleConfig(preset="daily", hour=3, minute=0)

        self.assertFalse(RetentionSchedulerService.is_due(schedule, last_run, now))

    def test_hourly_schedule_is_due_after_minute_when_not_run_this_hour(self):
        now = datetime(2026, 5, 16, 4, 43, tzinfo=timezone.utc)
        last_run = RetentionLastRun(
            status="success",
            finished_at=datetime(2026, 5, 16, 3, 50, tzinfo=timezone.utc),
            total_deleted=0,
        )
        schedule = RetentionScheduleConfig(preset="hourly", minute=30)

        self.assertTrue(RetentionSchedulerService.is_due(schedule, last_run, now))

    def test_hourly_schedule_is_not_due_before_minute(self):
        now = datetime(2026, 5, 16, 4, 29, tzinfo=timezone.utc)
        schedule = RetentionScheduleConfig(preset="hourly", minute=30)

        self.assertFalse(RetentionSchedulerService.is_due(schedule, RetentionLastRun(), now))

    def test_weekly_schedule_requires_matching_weekday(self):
        now = datetime(2026, 5, 16, 4, 0, tzinfo=timezone.utc)  # Saturday
        schedule = RetentionScheduleConfig(preset="weekly", weekday=0, hour=3, minute=0)

        self.assertFalse(RetentionSchedulerService.is_due(schedule, RetentionLastRun(), now))

    def test_weekly_schedule_is_due_on_matching_weekday_after_time(self):
        now = datetime(2026, 5, 18, 4, 0, tzinfo=timezone.utc)  # Monday
        last_run = RetentionLastRun(
            status="success",
            finished_at=datetime(2026, 5, 11, 3, 1, tzinfo=timezone.utc),
            total_deleted=0,
        )
        schedule = RetentionScheduleConfig(preset="weekly", weekday=0, hour=3, minute=0)

        self.assertTrue(RetentionSchedulerService.is_due(schedule, last_run, now))

    def test_monthly_schedule_is_due_on_configured_day_after_time(self):
        now = datetime(2026, 5, 16, 4, 0, tzinfo=timezone.utc)
        last_run = RetentionLastRun(
            status="success",
            finished_at=datetime(2026, 4, 16, 3, 1, tzinfo=timezone.utc),
            total_deleted=0,
        )
        schedule = RetentionScheduleConfig(preset="monthly", month_day=16, hour=3, minute=0)

        self.assertTrue(RetentionSchedulerService.is_due(schedule, last_run, now))

    def test_monthly_schedule_clamps_day_to_last_day_of_month(self):
        now = datetime(2026, 2, 28, 4, 0, tzinfo=timezone.utc)
        schedule = RetentionScheduleConfig(preset="monthly", month_day=31, hour=3, minute=0)

        self.assertTrue(RetentionSchedulerService.is_due(schedule, RetentionLastRun(), now))


if __name__ == "__main__":
    unittest.main()
