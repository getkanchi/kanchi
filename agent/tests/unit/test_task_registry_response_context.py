import unittest
from datetime import datetime, timezone, timedelta

from database import TaskRegistryDB
from models import TaskRegistryUpdate
from services.task_registry_service import TaskRegistryService
from services.task_service import TaskService
from tests.base import DatabaseTestCase


class TestTaskRegistryResponseContext(DatabaseTestCase):

    def setUp(self):
        super().setUp()
        TaskRegistryService._cache = set()
        TaskRegistryService._cache_initialized = False
        self.registry_service = TaskRegistryService(self.session)
        self.task_service = TaskService(self.session)
        self.now = datetime.now(timezone.utc)

    def test_update_task_persists_response_context_metadata(self):
        self.registry_service.ensure_task_registered("tasks.alerting.sync")

        updated = self.registry_service.update_task(
            "tasks.alerting.sync",
            TaskRegistryUpdate(
                runbook_url=" https://docs.example.com/runbooks/alerting-sync ",
                severity_default="critical",
                response_notes=" Check upstream dependencies before retrying. ",
            ),
        )

        self.assertIsNotNone(updated)
        self.assertEqual(updated.runbook_url, "https://docs.example.com/runbooks/alerting-sync")
        self.assertEqual(updated.severity_default, "critical")
        self.assertEqual(updated.response_notes, "Check upstream dependencies before retrying.")

        cleared = self.registry_service.update_task(
            "tasks.alerting.sync",
            TaskRegistryUpdate(
                runbook_url="",
                response_notes="",
            ),
        )

        self.assertIsNotNone(cleared)
        self.assertIsNone(cleared.runbook_url)
        self.assertIsNone(cleared.response_notes)

    def test_get_task_events_attach_response_context(self):
        registry = TaskRegistryDB(
            id="registry-1",
            name="tasks.alerting.sync",
            runbook_url="https://docs.example.com/runbooks/alerting-sync",
            severity_default="critical",
            response_notes="Check the upstream queue before retrying.",
            tags=[],
            created_at=self.now,
            updated_at=self.now,
            first_seen=self.now,
            last_seen=self.now,
        )
        self.session.add(registry)
        self.session.commit()

        self.create_task_event_db(
            task_id="task-1",
            task_name="tasks.alerting.sync",
            event_type="task-received",
            timestamp=self.now - timedelta(minutes=2),
        )
        self.create_task_event_db(
            task_id="task-1",
            task_name="tasks.alerting.sync",
            event_type="task-failed",
            timestamp=self.now - timedelta(minutes=1),
            exception="boom",
        )

        events = self.task_service.get_task_events("task-1")

        self.assertEqual(len(events), 2)
        for event in events:
            self.assertEqual(event.runbook_url, "https://docs.example.com/runbooks/alerting-sync")
            self.assertEqual(event.severity_default, "critical")
            self.assertEqual(event.response_notes, "Check the upstream queue before retrying.")

    def test_recent_failed_tasks_attach_response_context(self):
        registry = TaskRegistryDB(
            id="registry-2",
            name="tasks.example",
            runbook_url="https://docs.example.com/runbooks/example",
            severity_default="warning",
            response_notes="Validate the dependency health before requeueing.",
            tags=[],
            created_at=self.now,
            updated_at=self.now,
            first_seen=self.now,
            last_seen=self.now,
        )
        self.session.add(registry)
        self.session.commit()

        self.create_task_event_db(
            task_id="failed-recent",
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=self.now - timedelta(minutes=5),
            exception="dependency timeout",
        )

        results = self.task_service.get_recent_failed_tasks(hours=24, limit=10)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].runbook_url, "https://docs.example.com/runbooks/example")
        self.assertEqual(results[0].severity_default, "warning")
        self.assertEqual(results[0].response_notes, "Validate the dependency health before requeueing.")


if __name__ == "__main__":
    unittest.main()
