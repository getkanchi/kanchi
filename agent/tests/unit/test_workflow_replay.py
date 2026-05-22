"""Tests for workflow historical replay preview."""

import os
import sys
import uuid
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from tests.base import DatabaseTestCase
from database import WorkflowDB
from models import WorkflowReplayRequest
from services.workflow_service import WorkflowService


class TestWorkflowReplay(DatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.workflow_service = WorkflowService(self.session)

    def _create_workflow(self, trigger_type="task.failed", conditions=None):
        workflow = WorkflowDB(
            id=str(uuid.uuid4()),
            name="Replay test workflow",
            enabled=True,
            trigger_type=trigger_type,
            trigger_config={},
            conditions=conditions,
            actions=[{"type": "task.retry", "params": {}}],
        )
        self.session.add(workflow)
        self.session.commit()
        return self.workflow_service.get_workflow(workflow.id)

    def test_replay_matches_condition_filtered_task_events(self):
        now = datetime.now(timezone.utc)
        self.create_task_event_db(
            task_id="task-1",
            task_name="tasks.alpha",
            event_type="task-failed",
            timestamp=now - timedelta(minutes=10),
            hostname="worker-a",
            exception="Boom",
        )
        self.create_task_event_db(
            task_id="task-2",
            task_name="tasks.beta",
            event_type="task-failed",
            timestamp=now - timedelta(minutes=5),
            hostname="worker-b",
            exception="Ignore",
        )

        workflow = self._create_workflow(conditions={
            "operator": "AND",
            "conditions": [
                {"field": "task_name", "operator": "equals", "value": "tasks.alpha"}
            ]
        })

        result = self.workflow_service.replay_workflow(workflow, WorkflowReplayRequest(
            start_time=now - timedelta(hours=1),
            end_time=now,
            limit=10,
            dry_run=True,
        ))

        self.assertEqual(result.scanned_count, 2)
        self.assertEqual(result.matched_count, 1)
        self.assertEqual(result.matches[0].task_id, "task-1")
        self.assertEqual(result.matches[0].task_name, "tasks.alpha")

    def test_replay_matches_worker_events(self):
        now = datetime.now(timezone.utc)
        self.create_worker_event_db(
            hostname="worker-critical",
            event_type="worker-offline",
            timestamp=now - timedelta(minutes=3),
            status="offline",
        )
        self.create_worker_event_db(
            hostname="worker-ok",
            event_type="worker-online",
            timestamp=now - timedelta(minutes=1),
            status="online",
        )

        workflow = self._create_workflow(trigger_type="worker.offline")
        result = self.workflow_service.replay_workflow(workflow, WorkflowReplayRequest(
            start_time=now - timedelta(hours=1),
            end_time=now,
            limit=10,
            dry_run=True,
        ))

        self.assertEqual(result.scanned_count, 1)
        self.assertEqual(result.matched_count, 1)
        self.assertEqual(result.matches[0].hostname, "worker-critical")

    def test_replay_rejects_invalid_time_range(self):
        workflow = self._create_workflow()
        now = datetime.now(timezone.utc)

        with self.assertRaises(ValueError):
            self.workflow_service.replay_workflow(workflow, WorkflowReplayRequest(
                start_time=now,
                end_time=now - timedelta(hours=1),
                limit=10,
                dry_run=True,
            ))


if __name__ == '__main__':
    unittest.main()
