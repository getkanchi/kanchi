from datetime import datetime, timedelta, timezone

from models import TaskEvent, TaskSuppressionRuleCreate
from services.suppression_service import SuppressionService
from tests.base import DatabaseTestCase


class TestTaskSuppression(DatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.service = SuppressionService(self.session)

    def _failed_event(self, task_name="tasks.noisy", exception="Timeout"):
        return TaskEvent(
            task_id="task-1",
            task_name=task_name,
            event_type="task-failed",
            timestamp=datetime.now(timezone.utc),
            exception=exception,
        )

    def test_matches_active_rule(self):
        rule = self.service.create_rule(TaskSuppressionRuleCreate(task_name="tasks.noisy", reason="Known noisy", exception_contains="Timeout"))
        event = self._failed_event()

        matched = self.service.match_rule(event)

        self.assertIsNotNone(matched)
        self.assertEqual(matched.id, rule.id)

    def test_expired_rule_is_ignored(self):
        self.service.create_rule(TaskSuppressionRuleCreate(
            task_name="tasks.noisy",
            reason="Expired",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        ))

        self.assertIsNone(self.service.match_rule(self._failed_event(exception="anything")))

    def test_annotate_events_counts_suppressed(self):
        self.service.create_rule(TaskSuppressionRuleCreate(task_name="tasks.noisy", reason="Known noisy"))
        events = [self._failed_event(), self._failed_event(task_name="tasks.real")]

        metrics = self.service.annotate_events(events)

        self.assertTrue(events[0].suppressed)
        self.assertFalse(events[1].suppressed)
        self.assertEqual(metrics.suppressed_count, 1)
        self.assertEqual(metrics.active_count, 1)
