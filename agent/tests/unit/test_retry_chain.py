import unittest
from datetime import datetime, timezone, timedelta

from services.task_service import TaskService
from tests.base import DatabaseTestCase


class TestRetryChainTracking(DatabaseTestCase):

    def setUp(self):
        super().setUp()
        self.service = TaskService(self.session)
        self.base_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    def test_enrich_with_retry_info_finds_parent(self):
        original_event = self.create_task_event_db(
            task_id="original-123",
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=self.base_time,
            exception="ValueError: test error"
        )

        retry_event_db = self.create_task_event_db(
            task_id="retry-456",
            task_name="tasks.example",
            event_type="task-started",
            timestamp=self.base_time + timedelta(seconds=5)
        )

        self.create_retry_relationship(
            task_id="retry-456",
            original_id="original-123",
            retry_chain=[],
            total_retries=0
        )

        retry_event = self.service._db_to_task_event(retry_event_db)
        self.service._enrich_task_with_retry_info(retry_event)

        self.assertIsNotNone(retry_event.retry_of)
        self.assertEqual(retry_event.retry_of.task_id, "original-123")
        self.assertTrue(retry_event.is_retry)

    def test_retry_chain_multiple_levels(self):
        self.create_task_event_db(
            task_id="original-1",
            event_type="task-failed",
            timestamp=self.base_time
        )

        self.create_task_event_db(
            task_id="retry-1",
            event_type="task-failed",
            timestamp=self.base_time + timedelta(seconds=5)
        )

        retry_2_db = self.create_task_event_db(
            task_id="retry-2",
            event_type="task-started",
            timestamp=self.base_time + timedelta(seconds=10)
        )

        self.create_retry_relationship(
            task_id="retry-1",
            original_id="original-1",
            retry_chain=[],
            total_retries=0
        )
        self.create_retry_relationship(
            task_id="retry-2",
            original_id="retry-1",
            retry_chain=[],
            total_retries=0
        )

        retry_2_event = self.service._db_to_task_event(retry_2_db)
        self.service._enrich_task_with_retry_info(retry_2_event)

        self.assertIsNotNone(retry_2_event.retry_of)
        self.assertEqual(retry_2_event.retry_of.task_id, "retry-1")
        self.assertTrue(retry_2_event.is_retry)

    def test_original_task_has_no_parent(self):
        original_db = self.create_task_event_db(
            task_id="original-1",
            event_type="task-succeeded",
            timestamp=self.base_time
        )

        original_event = self.service._db_to_task_event(original_db)
        self.service._enrich_task_with_retry_info(original_event)

        self.assertIsNone(original_event.retry_of)
        self.assertFalse(original_event.is_retry)

    def test_retried_by_lists_child_retries(self):
        original_db = self.create_task_event_db(
            task_id="original-1",
            event_type="task-failed",
            timestamp=self.base_time
        )

        self.create_task_event_db(
            task_id="retry-1",
            event_type="task-failed",
            timestamp=self.base_time + timedelta(seconds=5)
        )
        self.create_task_event_db(
            task_id="retry-2",
            event_type="task-started",
            timestamp=self.base_time + timedelta(seconds=10)
        )

        self.create_retry_relationship(
            task_id="retry-1",
            original_id="original-1",
            retry_chain=[],
            total_retries=0
        )
        self.create_retry_relationship(
            task_id="retry-2",
            original_id="original-1",
            retry_chain=[],
            total_retries=0
        )

        self.create_retry_relationship(
            task_id="original-1",
            original_id="original-1",
            retry_chain=["retry-1", "retry-2"],
            total_retries=2
        )

        original_event = self.service._db_to_task_event(original_db)
        self.service._enrich_task_with_retry_info(original_event)

        self.assertEqual(len(original_event.retried_by), 2)
        retry_ids = {task.task_id for task in original_event.retried_by}
        self.assertEqual(retry_ids, {"retry-1", "retry-2"})

    def test_bulk_enrich_multiple_tasks(self):
        task_1_db = self.create_task_event_db(
            task_id="task-1",
            event_type="task-succeeded",
            timestamp=self.base_time
        )
        task_2_db = self.create_task_event_db(
            task_id="task-2",
            event_type="task-started",
            timestamp=self.base_time + timedelta(seconds=5)
        )

        self.create_task_event_db(
            task_id="original-2",
            event_type="task-failed",
            timestamp=self.base_time
        )
        self.create_retry_relationship(
            task_id="task-2",
            original_id="original-2"
        )

        events = [
            self.service._db_to_task_event(task_1_db),
            self.service._db_to_task_event(task_2_db)
        ]
        self.service._bulk_enrich_with_retry_info(events)

        self.assertIsNone(events[0].retry_of)
        self.assertFalse(events[0].is_retry)

        self.assertIsNotNone(events[1].retry_of)
        self.assertEqual(events[1].retry_of.task_id, "original-2")
        self.assertTrue(events[1].is_retry)

    def test_orphaned_task_retry(self):
        orphaned_db = self.create_task_event_db(
            task_id="orphaned-1",
            event_type="task-started",
            timestamp=self.base_time,
            is_orphan=True,
            orphaned_at=self.base_time + timedelta(seconds=30)
        )

        retry_db = self.create_task_event_db(
            task_id="retry-orphan-1",
            event_type="task-succeeded",
            timestamp=self.base_time + timedelta(seconds=60)
        )

        self.create_retry_relationship(
            task_id="retry-orphan-1",
            original_id="orphaned-1"
        )

        retry_event = self.service._db_to_task_event(retry_db)
        self.service._enrich_task_with_retry_info(retry_event)

        self.assertIsNotNone(retry_event.retry_of)
        self.assertEqual(retry_event.retry_of.task_id, "orphaned-1")
        self.assertTrue(retry_event.is_retry)
        self.assertTrue(retry_event.retry_of.is_orphan)

    def test_retry_relationship_missing_parent(self):
        retry_db = self.create_task_event_db(
            task_id="retry-1",
            event_type="task-started",
            timestamp=self.base_time
        )

        self.create_retry_relationship(
            task_id="retry-1",
            original_id="missing-original",
            retry_chain=[],
            total_retries=0
        )

        retry_event = self.service._db_to_task_event(retry_db)
        self.service._enrich_task_with_retry_info(retry_event)

        self.assertTrue(retry_event.is_retry)
        self.assertIsNone(retry_event.retry_of)

    def test_circular_reference_prevention(self):
        original_db = self.create_task_event_db(
            task_id="original-1",
            event_type="task-failed",
            timestamp=self.base_time
        )

        retry_db = self.create_task_event_db(
            task_id="retry-1",
            event_type="task-started",
            timestamp=self.base_time + timedelta(seconds=5)
        )

        self.create_retry_relationship(
            task_id="retry-1",
            original_id="original-1"
        )
        self.create_retry_relationship(
            task_id="original-1",
            original_id="original-1",
            retry_chain=["retry-1"]
        )

        retry_event = self.service._db_to_task_event(retry_db)
        self.service._enrich_task_with_retry_info(retry_event)

        self.assertIsNotNone(retry_event.retry_of)
        self.assertIsNone(retry_event.retry_of.retry_of)
        self.assertEqual(retry_event.retry_of.retried_by, [])

    def test_empty_retry_chain(self):
        task_db = self.create_task_event_db(
            task_id="task-1",
            event_type="task-succeeded",
            timestamp=self.base_time
        )

        self.create_retry_relationship(
            task_id="task-1",
            original_id="task-1",
            retry_chain=[],
            total_retries=0
        )

        task_event = self.service._db_to_task_event(task_db)
        self.service._enrich_task_with_retry_info(task_event)

        self.assertEqual(task_event.retried_by, [])
        self.assertIsNone(task_event.retry_of)

    def test_retry_preserves_task_details(self):
        self.create_task_event_db(
            task_id="original-1",
            task_name="tasks.complex_task",
            event_type="task-failed",
            timestamp=self.base_time,
            hostname="worker1",
            routing_key="celery",
            queue="default",
            runtime=15.5,
            exception="TimeoutError",
            args=[1, 2, 3],
            kwargs={"key": "value"}
        )

        retry_db = self.create_task_event_db(
            task_id="retry-1",
            task_name="tasks.complex_task",
            event_type="task-started",
            timestamp=self.base_time + timedelta(seconds=5)
        )

        self.create_retry_relationship(
            task_id="retry-1",
            original_id="original-1"
        )

        retry_event = self.service._db_to_task_event(retry_db)
        self.service._enrich_task_with_retry_info(retry_event)

        parent = retry_event.retry_of
        self.assertEqual(parent.task_name, "tasks.complex_task")
        self.assertEqual(parent.hostname, "worker1")
        self.assertEqual(parent.runtime, 15.5)
        self.assertEqual(parent.exception, "TimeoutError")

        import json
        if isinstance(parent.args, str):
            self.assertEqual(json.loads(parent.args), [1, 2, 3])
        else:
            self.assertEqual(parent.args, [1, 2, 3])
        if isinstance(parent.kwargs, str):
            self.assertEqual(json.loads(parent.kwargs), {"key": "value"})
        else:
            self.assertEqual(parent.kwargs, {"key": "value"})


if __name__ == '__main__':
    unittest.main()
