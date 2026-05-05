import os
import tempfile
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.task_routes import create_router
from database import Base, DatabaseManager, RetryRelationshipDB, TaskEventDB
from tests.base import DatabaseTestCase


class TestBulkTaskActionRoute(DatabaseTestCase):
    def setUp(self):
        super().setUp()
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        self.db_path = tmp.name
        self.db_manager = DatabaseManager(f"sqlite:///{self.db_path}")
        Base.metadata.create_all(self.db_manager.engine)

        with self.db_manager.get_session() as session:
            session.add(TaskEventDB(
                task_id="failed-1",
                task_name="tasks.sync",
                event_type="task-failed",
                timestamp=datetime.now(timezone.utc),
                queue="priority",
            ))

        self.mock_monitor = SimpleNamespace(app=SimpleNamespace(send_task=Mock(side_effect=RuntimeError("queue down"))))
        app_state = SimpleNamespace(config=None, db_manager=self.db_manager, monitor_instance=self.mock_monitor)

        app = FastAPI()
        app.include_router(create_router(app_state))
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.db_manager.engine.dispose()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
        super().tearDown()

    def test_retry_failure_does_not_persist_relationship(self):
        response = self.client.post(
            "/api/tasks/bulk-action",
            json={
                "action": "retry",
                "dry_run": False,
                "task_ids": ["failed-1"],
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["failure_count"], 1)
        self.assertEqual(body["results"][0]["status"], "failed")
        self.mock_monitor.app.send_task.assert_called_once()

        with self.db_manager.get_session() as session:
            self.assertEqual(session.query(RetryRelationshipDB).count(), 0)
