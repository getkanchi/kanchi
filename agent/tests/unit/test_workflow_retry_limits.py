"""Tests for workflow retry action infinite loop prevention."""

import unittest
import uuid
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from tests.base import DatabaseTestCase
from services.actions.retry_action import RetryActionHandler
from services.task_service import TaskService
from models import ActionResult


class TestWorkflowRetryLimits(DatabaseTestCase):
    """Test cases for preventing infinite retry loops."""

    def setUp(self):
        super().setUp()
        self.task_service = TaskService(self.session)
        self.retry_handler = RetryActionHandler(self.session, None, None)

        self.mock_monitor = Mock()
        self.mock_monitor.app = Mock()
        self.mock_monitor.app.send_task = Mock()
        self.retry_handler.monitor_instance = self.mock_monitor

    def test_validate_max_retries_param(self):
        """Test validation of max_retries parameter."""
        valid, error = self.retry_handler.validate_params({"max_retries": 5})
        self.assertTrue(valid)
        self.assertEqual(error, "")

        valid, error = self.retry_handler.validate_params({"max_retries": "not_a_number"})
        self.assertFalse(valid)
        self.assertIn("must be an integer", error)

        valid, error = self.retry_handler.validate_params({"max_retries": 0})
        self.assertFalse(valid)
        self.assertIn("at least 1", error)

        valid, error = self.retry_handler.validate_params({"max_retries": 101})
        self.assertFalse(valid)
        self.assertIn("cannot exceed 100", error)

    def test_max_retries_default_is_10(self):
        """Test that default max_retries is 10."""
        task_id = str(uuid.uuid4())
        root_id = str(uuid.uuid4())

        self.create_task_event_db(
            task_id=task_id,
            task_name="tasks.test",
            event_type="task-failed",
            root_id=root_id,
            queue="default"
        )

        current_task_id = task_id
        for i in range(10):
            retry_id = str(uuid.uuid4())
            self.create_task_event_db(
                task_id=retry_id,
                task_name="tasks.test",
                event_type="task-failed",
                root_id=root_id,
                queue="default"
            )
            self.task_service.create_retry_relationship(current_task_id, retry_id)
            current_task_id = retry_id

        context = {"task_id": current_task_id}
        params = {}

        result = self._run_async(
            self.retry_handler.execute(context, params)
        )

        self.assertEqual(result.status, "failed")
        self.assertIn("Max retry limit reached", result.error_message)
        self.assertIn("10/10", result.error_message)

    def test_max_retries_prevents_infinite_loop(self):
        """Test that max_retries prevents infinite retry loops."""
        task_id = str(uuid.uuid4())
        root_id = str(uuid.uuid4())

        self.create_task_event_db(
            task_id=task_id,
            task_name="tasks.infinite_loop",
            event_type="task-failed",
            root_id=root_id,
            queue="default",
            args=[1, 2, 3],
            kwargs={"foo": "bar"}
        )

        current_task_id = task_id
        for i in range(5):
            retry_id = str(uuid.uuid4())
            self.create_task_event_db(
                task_id=retry_id,
                task_name="tasks.infinite_loop",
                event_type="task-failed",
                root_id=root_id,
                queue="default",
                args=[1, 2, 3],
                kwargs={"foo": "bar"}
            )
            self.task_service.create_retry_relationship(current_task_id, retry_id)
            current_task_id = retry_id

        context = {"task_id": current_task_id}
        params = {"max_retries": 5}

        result = self._run_async(
            self.retry_handler.execute(context, params)
        )

        self.assertEqual(result.status, "failed")
        self.assertIn("Max retry limit reached", result.error_message)
        self.assertIn("5/5", result.error_message)
        self.assertEqual(result.result["retry_count"], 5)
        self.assertEqual(result.result["max_retries"], 5)

        self.mock_monitor.app.send_task.assert_not_called()

    def test_retry_allowed_under_limit(self):
        """Test that retry is allowed when under the limit."""
        task_id = str(uuid.uuid4())
        root_id = str(uuid.uuid4())

        self.create_task_event_db(
            task_id=task_id,
            task_name="tasks.test",
            event_type="task-failed",
            root_id=root_id,
            queue="default",
            args=[1, 2, 3],
            kwargs={"foo": "bar"}
        )

        current_task_id = task_id
        for i in range(2):
            retry_id = str(uuid.uuid4())
            self.create_task_event_db(
                task_id=retry_id,
                task_name="tasks.test",
                event_type="task-failed",
                root_id=root_id,
                queue="default",
                args=[1, 2, 3],
                kwargs={"foo": "bar"}
            )
            self.task_service.create_retry_relationship(current_task_id, retry_id)
            current_task_id = retry_id

        context = {"task_id": current_task_id}
        params = {"max_retries": 5}

        result = self._run_async(
            self.retry_handler.execute(context, params)
        )

        self.assertEqual(result.status, "success")
        self.assertEqual(result.result["retry_count"], 3)
        self.assertEqual(result.result["max_retries"], 5)
        self.mock_monitor.app.send_task.assert_called_once()

    def test_retry_count_tracks_across_root_id(self):
        """Test that retry count tracks all tasks with the same root_id."""
        root_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())

        self.create_task_event_db(
            task_id=task_id,
            task_name="tasks.test",
            event_type="task-started",
            root_id=root_id,
            queue="default"
        )

        current_task_id = task_id
        for i in range(4):
            retry_id = str(uuid.uuid4())
            self.create_task_event_db(
                task_id=retry_id,
                task_name="tasks.test",
                event_type="task-failed",
                root_id=root_id,
                queue="default"
            )
            self.task_service.create_retry_relationship(current_task_id, retry_id)
            current_task_id = retry_id

        retry_count = self.retry_handler._count_workflow_retries(current_task_id, root_id)

        self.assertEqual(retry_count, 4)

    def test_retry_count_handles_missing_root_id(self):
        """Test that retry count works when root_id is None."""
        task_id = str(uuid.uuid4())

        self.create_task_event_db(
            task_id=task_id,
            task_name="tasks.test",
            event_type="task-failed",
            root_id=None,
            queue="default"
        )

        retry_count = self.retry_handler._count_workflow_retries(task_id, None)
        self.assertEqual(retry_count, 0)

    def test_custom_max_retries_honored(self):
        """Test that custom max_retries values are honored."""
        task_id = str(uuid.uuid4())
        root_id = str(uuid.uuid4())

        self.create_task_event_db(
            task_id=task_id,
            task_name="tasks.test",
            event_type="task-failed",
            root_id=root_id,
            queue="default"
        )

        current_task_id = task_id
        for i in range(3):
            retry_id = str(uuid.uuid4())
            self.create_task_event_db(
                task_id=retry_id,
                task_name="tasks.test",
                event_type="task-failed",
                root_id=root_id,
                queue="default"
            )
            self.task_service.create_retry_relationship(current_task_id, retry_id)
            current_task_id = retry_id

        context = {"task_id": current_task_id}
        params = {"max_retries": 3}

        result = self._run_async(
            self.retry_handler.execute(context, params)
        )

        self.assertEqual(result.status, "failed")
        self.assertIn("Max retry limit reached", result.error_message)

    def test_retry_count_error_handling(self):
        """Test that retry count method handles errors gracefully."""
        task_id = str(uuid.uuid4())

        with patch.object(self.session, 'query', side_effect=Exception("Database error")):
            retry_count = self.retry_handler._count_workflow_retries(task_id, None)
            self.assertEqual(retry_count, 0)

    def _run_async(self, coro):
        """Helper to run async functions in tests."""
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


if __name__ == '__main__':
    unittest.main()
