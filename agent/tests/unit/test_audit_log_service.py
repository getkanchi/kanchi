from services.audit_service import AuditLogService
from tests.base import DatabaseTestCase


class TestAuditLogService(DatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.service = AuditLogService(self.session)

    def test_task_lookup_matches_primary_and_related_retry_task(self):
        self.service.record_entry(
            source="manual",
            action_type="task.retry",
            status="success",
            actor_type="user",
            actor_id="user-1",
            actor_name="operator@example.com",
            target_type="task",
            target_id="task-original",
            target_label="tasks.example",
            task_id="task-original",
            related_task_id="task-rerun",
            result_summary="Manual retry created task-rerun",
            details={"new_task_id": "task-rerun"},
        )

        original_entries = self.service.get_task_entries("task-original")
        rerun_entries = self.service.get_task_entries("task-rerun")

        self.assertEqual(original_entries.total, 1)
        self.assertEqual(rerun_entries.total, 1)
        self.assertEqual(original_entries.items[0].action_type, "task.retry")
        self.assertEqual(rerun_entries.items[0].related_task_id, "task-rerun")
