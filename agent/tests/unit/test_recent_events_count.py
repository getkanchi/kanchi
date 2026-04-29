import unittest
from datetime import datetime, timezone, timedelta

from database import TaskLatestDB
from services.task_service import TaskService
from tests.base import DatabaseTestCase


class TestRecentEventsCount(DatabaseTestCase):

    def setUp(self):
        super().setUp()
        self.service = TaskService(self.session)
        self.base_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    def _add_latest(self, task_id, event_type="task-succeeded", offset_seconds=0):
        """Helper: insert one row into task_latest."""
        row = TaskLatestDB(
            task_id=task_id,
            event_id=abs(hash(task_id)) % 2_000_000,
            task_name="tasks.bench",
            event_type=event_type,
            timestamp=self.base_time + timedelta(seconds=offset_seconds),
            resolved=False,
        )
        self.session.add(row)
        self.session.commit()
        return row

    def test_total_events_matches_row_count(self):
        """pagination.total equals the number of rows in task_latest."""
        for i in range(5):
            self._add_latest(f"task-{i}", offset_seconds=i)

        result = self.service.get_recent_events(limit=100, page=0)

        self.assertEqual(result["pagination"]["total"], 5)

    def test_total_events_respects_filters(self):
        """pagination.total reflects the filtered subset, not the full table."""
        for i in range(3):
            self._add_latest(f"task-ok-{i}", event_type="task-succeeded", offset_seconds=i)
        for i in range(2):
            self._add_latest(f"task-fail-{i}", event_type="task-failed", offset_seconds=10 + i)

        result = self.service.get_recent_events(
            limit=100, page=0, filter_state="SUCCESS"
        )

        self.assertEqual(result["pagination"]["total"], 3)

    def test_total_pages_derives_from_count_and_limit(self):
        """total_pages is ceil(total / limit)."""
        for i in range(7):
            self._add_latest(f"task-{i}", offset_seconds=i)

        result = self.service.get_recent_events(limit=3, page=0)

        self.assertEqual(result["pagination"]["total"], 7)
        self.assertEqual(result["pagination"]["total_pages"], 3)  # ceil(7/3) = 3


if __name__ == "__main__":
    unittest.main()
