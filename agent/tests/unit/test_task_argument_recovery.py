import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock

import anyio
from fastapi import FastAPI

from api.task_action_routes import create_router as create_task_action_router
from config import Config
from database import Base, DatabaseManager, TaskEventDB, TaskLatestDB
from models import TaskActionType, TaskEvent
from services.task_action_service import TaskActionService
from services.task_service import TaskService
from tests.base import DatabaseTestCase


async def post_json(app, path: str, payload: dict):
    body = json.dumps(payload).encode("utf-8")
    messages = []
    received = False
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "method": "POST",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": [
            (b"host", b"testserver"),
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode()),
        ],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }

    async def receive():
        nonlocal received
        if received:
            return {"type": "http.disconnect"}
        received = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message):
        messages.append(message)

    await app(scope, receive, send)

    start = next(message for message in messages if message["type"] == "http.response.start")
    response_body = b"".join(
        message.get("body", b"")
        for message in messages
        if message["type"] == "http.response.body"
    )
    return start["status"], json.loads(response_body.decode("utf-8"))


class TestTaskArgumentRecovery(DatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.base_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        self.metadata_kwargs = {
            "__start_time": "2024-01-01T12:00:00Z",
            "__user_profile_code": "profile-123",
            "sentry-trace": "trace-id",
        }

    def test_failed_event_with_metadata_kwargs_inherits_received_args_for_rerun(self):
        task_id = "task-with-positional-args"
        task_service = TaskService(self.session)

        task_service.save_task_event(
            self.create_task_event(
                task_id=task_id,
                task_name="tasks.requires_idto",
                event_type="task-received",
                timestamp=self.base_time,
                args=[8675309],
                kwargs={},
                queue="critical",
                routing_key="critical",
            )
        )
        task_service.save_task_event(
            self.create_task_event(
                task_id=task_id,
                task_name="tasks.requires_idto",
                event_type="task-failed",
                timestamp=self.base_time + timedelta(seconds=5),
                args=[],
                kwargs=self.metadata_kwargs,
                exception="TypeError: boom",
                routing_key="default",
            )
        )

        failed_event = (
            self.session.query(TaskEventDB)
            .filter_by(task_id=task_id, event_type="task-failed")
            .one()
        )
        latest = self.session.query(TaskLatestDB).filter_by(task_id=task_id).one()

        self.assertEqual(failed_event.args, [8675309])
        self.assertEqual(failed_event.kwargs, self.metadata_kwargs)
        self.assertEqual(latest.args, [8675309])
        self.assertEqual(latest.kwargs, self.metadata_kwargs)

        send_task = Mock()
        action_service = TaskActionService(
            self.session,
            monitor_instance=SimpleNamespace(app=SimpleNamespace(send_task=send_task)),
        )

        action = action_service.create_action(
            action_type=TaskActionType.RERUN,
            task_ids=[task_id],
            initiated_by="tester",
        )

        self.assertEqual(action.item_created, 1)
        send_task.assert_called_once()
        _, kwargs = send_task.call_args
        self.assertEqual(kwargs["args"], [8675309])
        self.assertEqual(kwargs["kwargs"], self.metadata_kwargs)

    def test_rerun_recovers_args_from_received_when_latest_snapshot_lost_them(self):
        task_id = "task-with-corrupted-latest"
        received = self.create_task_event_db(
            task_id=task_id,
            task_name="tasks.requires_idto",
            event_type="task-received",
            timestamp=self.base_time,
            args=[42],
            kwargs={},
            queue="critical",
            routing_key="critical",
        )
        failed = self.create_task_event_db(
            task_id=task_id,
            task_name="tasks.requires_idto",
            event_type="task-failed",
            timestamp=self.base_time + timedelta(seconds=5),
            args=[],
            kwargs=self.metadata_kwargs,
            exception="TypeError: boom",
            queue="critical",
            routing_key="critical",
        )
        self.session.add(
            TaskLatestDB(
                task_id=task_id,
                event_id=failed.id,
                task_name=failed.task_name,
                event_type=failed.event_type,
                timestamp=failed.timestamp,
                hostname=failed.hostname,
                queue=failed.queue,
                routing_key=failed.routing_key,
                args=[],
                kwargs=self.metadata_kwargs,
                exception=failed.exception,
            )
        )
        self.session.commit()
        self.assertEqual(received.args, [42])

        send_task = Mock()
        action_service = TaskActionService(
            self.session,
            monitor_instance=SimpleNamespace(app=SimpleNamespace(send_task=send_task)),
        )

        action_service.create_action(
            action_type=TaskActionType.RERUN,
            task_ids=[task_id],
            initiated_by="tester",
        )

        send_task.assert_called_once()
        _, kwargs = send_task.call_args
        self.assertEqual(kwargs["args"], [42])
        self.assertEqual(kwargs["kwargs"], self.metadata_kwargs)

    def test_task_event_accepts_json_string_args_and_kwargs(self):
        event = TaskEvent(
            task_id="task-json-payload",
            task_name="tasks.example",
            event_type="task-received",
            timestamp=self.base_time,
            args='[true, null, "idto-1"]',
            kwargs='{"dry_run": true}',
        )

        self.assertEqual(event.args, [True, None, "idto-1"])
        self.assertEqual(event.kwargs, {"dry_run": True})

    def test_rerun_api_route_preserves_received_args_after_failed_metadata_event(self):
        task_id = "task-route-e2e"
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        db_manager = DatabaseManager(f"sqlite:///{db_path}")
        Base.metadata.create_all(db_manager.engine)
        self.addCleanup(db_manager.engine.dispose)
        self.addCleanup(lambda: os.path.exists(db_path) and os.unlink(db_path))

        with db_manager.get_session() as session:
            task_service = TaskService(session)
            task_service.save_task_event(
                self.create_task_event(
                    task_id=task_id,
                    task_name="tasks.requires_idto",
                    event_type="task-received",
                    timestamp=self.base_time,
                    args=[314],
                    kwargs={},
                    queue="critical",
                    routing_key="critical",
                )
            )
            task_service.save_task_event(
                self.create_task_event(
                    task_id=task_id,
                    task_name="tasks.requires_idto",
                    event_type="task-failed",
                    timestamp=self.base_time + timedelta(seconds=5),
                    args=[],
                    kwargs=self.metadata_kwargs,
                    exception="TypeError: boom",
                    queue="critical",
                    routing_key="critical",
                )
            )

        send_task = Mock()
        app_state = SimpleNamespace(
            config=Config(),
            db_manager=db_manager,
            monitor_instance=SimpleNamespace(app=SimpleNamespace(send_task=send_task)),
            connection_manager=None,
            auth_dependencies=None,
        )
        app = FastAPI()
        app.include_router(create_task_action_router(app_state))

        status, response = anyio.run(post_json, app, f"/api/tasks/{task_id}/rerun", {})

        self.assertEqual(status, 200)
        self.assertEqual(response["item_created"], 1)
        send_task.assert_called_once()
        _, kwargs = send_task.call_args
        self.assertEqual(kwargs["args"], [314])
        self.assertEqual(kwargs["kwargs"], self.metadata_kwargs)


if __name__ == "__main__":
    unittest.main()
