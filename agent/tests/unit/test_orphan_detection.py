import unittest
from datetime import datetime, timezone, timedelta

from services.orphan_detection_service import OrphanDetectionService
from tests.base import DatabaseTestCase


class TestOrphanDetectionService(DatabaseTestCase):

    def setUp(self):
        super().setUp()
        self.service = OrphanDetectionService(self.session)
        self.base_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    def test_find_orphaned_tasks_basic(self):
        self.create_task_event_db(
            task_id="orphan-1",
            event_type="task-received",
            timestamp=self.base_time,
            hostname="worker1"
        )
        self.create_task_event_db(
            task_id="orphan-1",
            event_type="task-started",
            timestamp=self.base_time + timedelta(seconds=1),
            hostname="worker1"
        )

        orphaned_at = self.base_time + timedelta(seconds=10)
        orphaned_tasks = self.service.find_and_mark_orphaned_tasks(
            hostname="worker1",
            orphaned_at=orphaned_at
        )

        self.assertEqual(len(orphaned_tasks), 1)
        self.assertEqual(orphaned_tasks[0].task_id, "orphan-1")
        self.assertEqual(orphaned_tasks[0].event_type, "task-started")

        events = self.get_task_events_by_id("orphan-1")
        for event in events:
            self.assertTrue(event.is_orphan)
            expected_time = orphaned_at.replace(tzinfo=None, microsecond=0)
            actual_time = event.orphaned_at.replace(tzinfo=None, microsecond=0)
            self.assertEqual(actual_time, expected_time)

    def test_orphan_detection_ignores_completed_tasks(self):
        self.create_task_event_db(
            task_id="completed-1",
            event_type="task-received",
            timestamp=self.base_time,
            hostname="worker1"
        )
        self.create_task_event_db(
            task_id="completed-1",
            event_type="task-started",
            timestamp=self.base_time + timedelta(seconds=1),
            hostname="worker1"
        )
        self.create_task_event_db(
            task_id="completed-1",
            event_type="task-succeeded",
            timestamp=self.base_time + timedelta(seconds=5),
            hostname="worker1",
            runtime=4.0
        )

        orphaned_tasks = self.service.find_and_mark_orphaned_tasks(
            hostname="worker1",
            orphaned_at=self.base_time + timedelta(seconds=10)
        )

        self.assertEqual(len(orphaned_tasks), 0)

        events = self.get_task_events_by_id("completed-1")
        for event in events:
            self.assertFalse(event.is_orphan)

    def test_orphan_detection_ignores_failed_tasks(self):
        self.create_task_event_db(
            task_id="failed-1",
            event_type="task-started",
            timestamp=self.base_time,
            hostname="worker1"
        )
        self.create_task_event_db(
            task_id="failed-1",
            event_type="task-failed",
            timestamp=self.base_time + timedelta(seconds=2),
            hostname="worker1",
            exception="ValueError: test error"
        )

        orphaned_tasks = self.service.find_and_mark_orphaned_tasks(
            hostname="worker1",
            orphaned_at=self.base_time + timedelta(seconds=10)
        )

        self.assertEqual(len(orphaned_tasks), 0)

    def test_orphan_detection_by_hostname(self):
        self.create_task_event_db(
            task_id="task-worker1",
            event_type="task-started",
            timestamp=self.base_time,
            hostname="worker1"
        )
        self.create_task_event_db(
            task_id="task-worker2",
            event_type="task-started",
            timestamp=self.base_time,
            hostname="worker2"
        )

        orphaned_tasks = self.service.find_and_mark_orphaned_tasks(
            hostname="worker1",
            orphaned_at=self.base_time + timedelta(seconds=10)
        )

        self.assertEqual(len(orphaned_tasks), 1)
        self.assertEqual(orphaned_tasks[0].task_id, "task-worker1")

        worker1_events = self.get_task_events_by_id("task-worker1")
        for event in worker1_events:
            self.assertTrue(event.is_orphan)

        worker2_events = self.get_task_events_by_id("task-worker2")
        for event in worker2_events:
            self.assertFalse(event.is_orphan)

    def test_orphan_detection_multiple_tasks(self):
        for i in range(5):
            self.create_task_event_db(
                task_id=f"orphan-{i}",
                event_type="task-started",
                timestamp=self.base_time + timedelta(seconds=i),
                hostname="worker1"
            )

        orphaned_tasks = self.service.find_and_mark_orphaned_tasks(
            hostname="worker1",
            orphaned_at=self.base_time + timedelta(seconds=10)
        )

        self.assertEqual(len(orphaned_tasks), 5)
        orphaned_ids = {task.task_id for task in orphaned_tasks}
        self.assertEqual(orphaned_ids, {f"orphan-{i}" for i in range(5)})

    def test_orphan_detection_doesnt_remark_already_orphaned(self):
        first_orphan_time = self.base_time
        self.create_task_event_db(
            task_id="orphan-1",
            event_type="task-started",
            timestamp=self.base_time,
            hostname="worker1",
            is_orphan=True,
            orphaned_at=first_orphan_time
        )

        second_orphan_time = self.base_time + timedelta(seconds=20)
        orphaned_tasks = self.service.find_and_mark_orphaned_tasks(
            hostname="worker1",
            orphaned_at=second_orphan_time
        )

        self.assertEqual(len(orphaned_tasks), 0)

        event = self.get_task_events_by_id("orphan-1")[0]
        expected_time = first_orphan_time.replace(tzinfo=None, microsecond=0)
        actual_time = event.orphaned_at.replace(tzinfo=None, microsecond=0)
        self.assertEqual(actual_time, expected_time)

    def test_orphan_detection_with_task_sent_event(self):
        self.create_task_event_db(
            task_id="sent-only",
            event_type="task-sent",
            timestamp=self.base_time,
            hostname="worker1"
        )

        orphaned_tasks = self.service.find_and_mark_orphaned_tasks(
            hostname="worker1",
            orphaned_at=self.base_time + timedelta(seconds=10)
        )

        self.assertEqual(len(orphaned_tasks), 1)
        self.assertEqual(orphaned_tasks[0].event_type, "task-sent")

    def test_orphan_detection_with_task_received_event(self):
        self.create_task_event_db(
            task_id="received-only",
            event_type="task-received",
            timestamp=self.base_time,
            hostname="worker1"
        )

        orphaned_tasks = self.service.find_and_mark_orphaned_tasks(
            hostname="worker1",
            orphaned_at=self.base_time + timedelta(seconds=10)
        )

        self.assertEqual(len(orphaned_tasks), 1)
        self.assertEqual(orphaned_tasks[0].event_type, "task-received")

    def test_create_orphan_events(self):
        self.create_task_event_db(
            task_id="orphan-1",
            task_name="tasks.example",
            event_type="task-started",
            timestamp=self.base_time,
            hostname="worker1",
            routing_key="celery",
            args=[1, 2, 3],
            kwargs={"key": "value"}
        )

        orphaned_tasks = self.service.find_and_mark_orphaned_tasks(
            hostname="worker1",
            orphaned_at=self.base_time + timedelta(seconds=10)
        )

        orphaned_at = self.base_time + timedelta(seconds=10)
        orphan_events = self.service.create_orphan_events(orphaned_tasks, orphaned_at)

        self.assertEqual(len(orphan_events), 1)
        event = orphan_events[0]

        self.assertEqual(event.task_id, "orphan-1")
        self.assertEqual(event.task_name, "tasks.example")
        self.assertEqual(event.event_type, "task-orphaned")
        self.assertEqual(event.hostname, "worker1")
        self.assertEqual(event.timestamp, orphaned_at)
        self.assertEqual(event.routing_key, "celery")
        self.assertEqual(event.args, [1, 2, 3])
        self.assertEqual(event.kwargs, {"key": "value"})

    def test_orphan_detection_picks_latest_event(self):
        self.create_task_event_db(
            task_id="task-1",
            event_type="task-received",
            timestamp=self.base_time,
            hostname="worker1"
        )
        self.create_task_event_db(
            task_id="task-1",
            event_type="task-started",
            timestamp=self.base_time + timedelta(seconds=1),
            hostname="worker1"
        )
        self.create_task_event_db(
            task_id="task-1",
            event_type="task-succeeded",
            timestamp=self.base_time + timedelta(seconds=5),
            hostname="worker1"
        )

        self.create_task_event_db(
            task_id="task-2",
            event_type="task-received",
            timestamp=self.base_time,
            hostname="worker1"
        )
        self.create_task_event_db(
            task_id="task-2",
            event_type="task-started",
            timestamp=self.base_time + timedelta(seconds=1),
            hostname="worker1"
        )

        orphaned_tasks = self.service.find_and_mark_orphaned_tasks(
            hostname="worker1",
            orphaned_at=self.base_time + timedelta(seconds=10)
        )

        self.assertEqual(len(orphaned_tasks), 1)
        self.assertEqual(orphaned_tasks[0].task_id, "task-2")


if __name__ == '__main__':
    unittest.main()
