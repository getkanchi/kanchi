import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from services.retention_scheduler import RetentionScheduler


class _FakeSessionContext:
    def __enter__(self):
        return object()

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeDBManager:
    def get_session(self):
        return _FakeSessionContext()


class TestRetentionScheduler(unittest.TestCase):
    def test_disabled_scheduler_reports_no_next_run(self):
        scheduler = RetentionScheduler(_FakeDBManager(), enabled=False, interval_hours=24)

        status = scheduler.get_status()

        self.assertFalse(status.enabled)
        self.assertIsNone(status.next_run_at)
        self.assertFalse(scheduler.is_alive())

    def test_scheduler_runs_cleanup_and_updates_status(self):
        scheduler = RetentionScheduler(_FakeDBManager(), enabled=True, interval_hours=1, interval_seconds=1)

        with patch('services.retention_scheduler.RetentionService') as retention_service_cls:
            retention_service_cls.return_value.cleanup.return_value = SimpleNamespace(total_deleted=7)

            scheduler.start()
            thread = scheduler._thread
            self.assertIsNotNone(thread)
            thread.join(timeout=2.5)
            scheduler.stop()
            thread.join(timeout=1)

        status = scheduler.get_status()

        self.assertIsNotNone(status.last_run_at)
        self.assertIsNotNone(status.last_completed_at)
        self.assertEqual(status.last_deleted_rows, 7)
        self.assertIsNone(status.last_error)
        self.assertIsInstance(status.next_run_at, datetime)
        self.assertGreater(status.next_run_at, status.last_completed_at)
        self.assertFalse(scheduler.is_alive())


if __name__ == '__main__':
    unittest.main()
