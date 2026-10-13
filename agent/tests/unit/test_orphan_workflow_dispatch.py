from contextlib import nullcontext
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, call, patch

from event_handler import EventHandler
from models import WorkerEvent
from tests.base import DatabaseTestCase
from worker_health_monitor import WorkerHealthMonitor


class TestOrphanWorkflowDispatch(DatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.now = datetime.now(timezone.utc)
        self.db_manager = Mock()
        self.db_manager.get_session.side_effect = lambda: nullcontext(self.session)
        self.connections = Mock()
        self.workflows = Mock()
        self.handler = EventHandler(self.db_manager, self.connections, self.workflows)
        self.monitor = Mock()
        self.monitor.get_workers_info.return_value = {
            "worker1": {
                "status": "online",
                "timestamp": self.now - timedelta(seconds=60),
            }
        }
        self.health_monitor = WorkerHealthMonitor(self.monitor, self.db_manager, self.handler)
        self.worker_event = WorkerEvent(
            hostname="worker1",
            event_type="worker-offline",
            timestamp=self.now,
        )
        for task_id in ("orphan-1", "orphan-2"):
            self.create_task_event_db(task_id=task_id, timestamp=self.now)
        self.create_task_event_db(task_id="completed", event_type="task-succeeded")
        self.create_task_event_db(task_id="already-orphaned", is_orphan=True)
        self.create_task_event_db(task_id="other-worker", hostname="worker2")

    def detect_orphans(self, path):
        if path == "offline":
            with patch("time.sleep"):
                self.handler.handle_worker_event(self.worker_event)
        else:
            self.health_monitor._check_worker_health()

    def assert_orphan_dispatch(self, path):
        self.detect_orphans(path)
        events = [args.args[0] for args in self.connections.queue_broadcast.call_args_list]
        self.assertEqual({event.task_id for event in events}, {"orphan-1", "orphan-2"})
        self.assertEqual(len(events), 2)
        for event in events:
            self.assertEqual(event.event_type, "task-orphaned")
            self.assertEqual(event.task_name, "tasks.example")
            self.assertEqual(event.hostname, "worker1")
            self.assertTrue(self.get_task_events_by_id(event.task_id)[0].is_orphan)

        expected_calls = [call(event) for event in events]
        if path == "offline":
            expected_calls.append(call(self.worker_event))
        self.assertEqual(self.workflows.process_event.call_args_list, expected_calls)

        self.connections.reset_mock()
        self.workflows.reset_mock()
        # Both detection paths must skip tasks already marked by the first detection.
        self.detect_orphans("offline")
        self.detect_orphans("heartbeat")
        self.connections.queue_broadcast.assert_not_called()
        self.workflows.process_event.assert_called_once_with(self.worker_event)

    def test_worker_offline_dispatches_orphans_to_workflows(self):
        self.assert_orphan_dispatch("offline")

    def test_heartbeat_timeout_dispatches_orphans_to_workflows(self):
        self.assert_orphan_dispatch("heartbeat")

    def test_worker_offline_without_workflow_engine_still_broadcasts(self):
        self.handler.workflow_engine = None
        self.detect_orphans("offline")
        self.assertEqual(self.connections.queue_broadcast.call_count, 2)

    def test_heartbeat_timeout_without_workflow_engine_still_broadcasts(self):
        self.handler.workflow_engine = None
        self.detect_orphans("heartbeat")
        self.assertEqual(self.connections.queue_broadcast.call_count, 2)
