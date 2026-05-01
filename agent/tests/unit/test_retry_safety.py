from datetime import datetime, timezone

from database import RetryRelationshipDB
from services.task_service import TaskService
from tests.base import DatabaseTestCase


class TestRetrySafety(DatabaseTestCase):
    def test_preview_blocks_retry_when_attempt_cap_reached(self):
        self.create_task_event_db(
            task_id="failed-1",
            task_name="tasks.billing.sync",
            event_type="task-failed",
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            queue="billing",
            exception="timeout",
        )
        self.session.add(RetryRelationshipDB(
            task_id="failed-1",
            original_id="failed-1",
            retry_chain=["retry-1", "retry-2", "retry-3"],
            total_retries=3,
        ))
        self.session.commit()

        preview = TaskService(self.session).get_retry_impact_preview("failed-1", max_attempts=3)

        self.assertFalse(preview.allowed)
        self.assertEqual(preview.retry_count, 3)
        self.assertEqual(preview.remaining_attempts, 0)
        self.assertIn("max_attempts_reached", [warning.code for warning in preview.warnings])

    def test_preview_warns_on_repeating_failure_family_and_orphaned_task(self):
        for idx in range(3):
            self.create_task_event_db(
                task_id=f"failed-{idx}",
                task_name="tasks.import.sync",
                event_type="task-failed",
                timestamp=datetime(2024, 1, 1, 12, idx, 0, tzinfo=timezone.utc),
                exception="upstream unavailable",
                is_orphan=idx == 2,
            )

        preview = TaskService(self.session).get_retry_impact_preview("failed-2", max_attempts=5)

        self.assertTrue(preview.allowed)
        warning_codes = [warning.code for warning in preview.warnings]
        self.assertIn("repeating_failure_family", warning_codes)
        self.assertIn("orphaned_worker", warning_codes)
