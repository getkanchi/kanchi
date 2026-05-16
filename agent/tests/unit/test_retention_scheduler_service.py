import unittest
from datetime import datetime, timedelta, timezone

from models import RetentionLastRun
from services.retention_scheduler_service import RetentionSchedulerService


class TestRetentionSchedulerService(unittest.TestCase):
    def test_daily_schedule_is_due_after_run_time_when_not_run_today(self):
        now = datetime(2026, 5, 16, 4, 0, tzinfo=timezone.utc)
        last_run = RetentionLastRun(
            status="success",
            finished_at=now - timedelta(days=1),
            total_deleted=0,
        )

        self.assertTrue(RetentionSchedulerService.is_due("daily", "03:00", last_run, now))

    def test_daily_schedule_is_not_due_before_run_time(self):
        now = datetime(2026, 5, 16, 2, 59, tzinfo=timezone.utc)

        self.assertFalse(RetentionSchedulerService.is_due("daily", "03:00", RetentionLastRun(), now))

    def test_weekly_schedule_waits_seven_days(self):
        now = datetime(2026, 5, 16, 4, 0, tzinfo=timezone.utc)
        last_run = RetentionLastRun(
            status="success",
            finished_at=now - timedelta(days=6, hours=23),
            total_deleted=0,
        )

        self.assertFalse(RetentionSchedulerService.is_due("weekly", "03:00", last_run, now))


if __name__ == "__main__":
    unittest.main()
