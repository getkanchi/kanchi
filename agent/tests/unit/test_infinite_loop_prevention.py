"""Integration tests for preventing infinite workflow retry loops."""

import unittest
import uuid
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from tests.base import DatabaseTestCase
from services.actions.retry_action import RetryActionHandler
from services.workflow_service import WorkflowService
from services.task_service import TaskService
from database import WorkflowDB, WorkflowExecutionDB
from models import CircuitBreakerConfig


class TestInfiniteLoopPrevention(DatabaseTestCase):
    """Integration tests ensuring infinite loops cannot occur."""

    def setUp(self):
        super().setUp()
        self.task_service = TaskService(self.session)
        self.workflow_service = WorkflowService(self.session)
        self.retry_handler = RetryActionHandler(self.session, None, None)

        self.mock_monitor = Mock()
        self.mock_monitor.app = Mock()
        self.mock_monitor.app.send_task = Mock()
        self.retry_handler.monitor_instance = self.mock_monitor

    def test_scenario_failed_task_retry_loop_with_max_retries(self):
        """
        Scenario: A task fails repeatedly, workflow retries it each time.
        Expected: Stops after max_retries is reached.
        """
        root_id = str(uuid.uuid4())
        original_task_id = str(uuid.uuid4())

        self.create_task_event_db(
            task_id=original_task_id,
            task_name="tasks.always_fails",
            event_type="task-failed",
            root_id=root_id,
            queue="default"
        )

        max_retries = 3
        current_task_id = original_task_id

        for attempt in range(max_retries + 2):
            context = {"task_id": current_task_id, "root_id": root_id}
            params = {"max_retries": max_retries}

            result = self._run_async(
                self.retry_handler.execute(context, params)
            )

            if attempt < max_retries:
                self.assertEqual(result.status, "success",
                    f"Attempt {attempt + 1} should succeed")

                new_task_id = result.result["new_task_id"]

                self.create_task_event_db(
                    task_id=new_task_id,
                    task_name="tasks.always_fails",
                    event_type="task-failed",
                    root_id=root_id,
                    queue="default"
                )

                current_task_id = new_task_id
            else:
                self.assertEqual(result.status, "failed",
                    f"Attempt {attempt + 1} should be blocked")
                self.assertIn("Max retry limit reached", result.error_message)
                break

        total_send_task_calls = self.mock_monitor.app.send_task.call_count
        self.assertEqual(total_send_task_calls, max_retries,
            f"Should only retry {max_retries} times")

    def test_scenario_circuit_breaker_stops_rapid_retries(self):
        """
        Scenario: Workflow rapidly retries the same task chain.
        Expected: Circuit breaker opens after threshold, preventing further execution.
        """
        circuit_breaker = CircuitBreakerConfig(
            enabled=True,
            max_executions=3,
            window_seconds=300,
            context_field="root_id"
        )

        workflow = self._create_test_workflow(
            circuit_breaker_config=circuit_breaker.dict()
        )

        root_id = str(uuid.uuid4())

        for i in range(5):
            context = {"root_id": root_id, "task_id": str(uuid.uuid4())}

            state = self.workflow_service.is_circuit_breaker_open(
                workflow, context
            )

            if i < 3:
                self.assertFalse(state.is_open, f"Iteration {i}: Circuit should be closed")

                execution = WorkflowExecutionDB(
                    workflow_id=workflow.id,
                    trigger_type="task.failed",
                    trigger_event=context,
                    status="completed",
                    circuit_breaker_key=root_id,
                    triggered_at=datetime.now(timezone.utc)
                )
                self.session.add(execution)
                self.session.commit()
            else:
                self.assertTrue(state.is_open, f"Iteration {i}: Circuit should be open")
                self.assertIsNotNone(state.reason)

    def test_scenario_combined_max_retries_and_circuit_breaker(self):
        """
        Scenario: Both max_retries and circuit breaker are active.
        Expected: Either limit stops the loop.
        """
        circuit_breaker = CircuitBreakerConfig(
            enabled=True,
            max_executions=2,
            window_seconds=300,
            context_field="root_id"
        )

        workflow = self._create_test_workflow(
            circuit_breaker_config=circuit_breaker.dict()
        )

        root_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())

        self.create_task_event_db(
            task_id=task_id,
            task_name="tasks.test",
            event_type="task-failed",
            root_id=root_id,
            queue="default"
        )

        max_retries = 5
        execution_count = 0

        for i in range(10):
            context = {"root_id": root_id, "task_id": task_id}

            state = self.workflow_service.is_circuit_breaker_open(
                workflow, context
            )

            if state.is_open:
                break

            params = {"max_retries": max_retries}
            result = self._run_async(
                self.retry_handler.execute(context, params)
            )

            if result.status == "failed":
                break

            execution_count += 1

            execution = WorkflowExecutionDB(
                workflow_id=workflow.id,
                trigger_type="task.failed",
                trigger_event=context,
                status="completed",
                circuit_breaker_key=root_id,
                triggered_at=datetime.now(timezone.utc)
            )
            self.session.add(execution)
            self.session.commit()

            new_task_id = result.result["new_task_id"]
            self.create_task_event_db(
                task_id=new_task_id,
                task_name="tasks.test",
                event_type="task-failed",
                root_id=root_id,
                queue="default"
            )
            task_id = new_task_id

        self.assertLessEqual(execution_count, 2,
            "Circuit breaker should stop after 2 executions")

    def test_scenario_different_task_chains_independent_limits(self):
        """
        Scenario: Multiple independent task chains fail and retry.
        Expected: Each chain has its own retry limits.
        """
        max_retries = 3

        chains = []
        for i in range(3):
            root_id = str(uuid.uuid4())
            task_id = str(uuid.uuid4())

            self.create_task_event_db(
                task_id=task_id,
                task_name=f"tasks.chain_{i}",
                event_type="task-failed",
                root_id=root_id,
                queue="default"
            )

            chains.append({"root_id": root_id, "task_id": task_id, "attempts": 0})

        for chain in chains:
            for attempt in range(max_retries + 1):
                context = {"task_id": chain["task_id"], "root_id": chain["root_id"]}
                params = {"max_retries": max_retries}

                result = self._run_async(
                    self.retry_handler.execute(context, params)
                )

                if attempt < max_retries:
                    self.assertEqual(result.status, "success")
                    chain["attempts"] += 1

                    new_task_id = result.result["new_task_id"]
                    self.create_task_event_db(
                        task_id=new_task_id,
                        task_name=f"tasks.chain_{chains.index(chain)}",
                        event_type="task-failed",
                        root_id=chain["root_id"],
                        queue="default"
                    )
                    chain["task_id"] = new_task_id
                else:
                    self.assertEqual(result.status, "failed")

        for chain in chains:
            self.assertEqual(chain["attempts"], max_retries,
                "Each chain should reach its max_retries independently")

    def test_scenario_workflow_disabled_prevents_retries(self):
        """
        Scenario: Workflow is disabled after starting infinite loop.
        Expected: No more retries occur after disabling.
        """
        workflow = self._create_test_workflow()

        self.assertTrue(workflow.enabled)

        workflow_db = self.session.query(WorkflowDB).filter_by(id=workflow.id).first()
        workflow_db.enabled = False
        self.session.commit()

        can_execute, reason = self.workflow_service.can_execute_workflow(workflow.id)

        self.assertFalse(can_execute)
        self.assertEqual(reason, "Workflow is disabled")

    def _create_test_workflow(self, circuit_breaker_config=None):
        """Helper to create a test workflow."""
        workflow_db = WorkflowDB(
            id=str(uuid.uuid4()),
            name="Test Retry Workflow",
            enabled=True,
            trigger_type="task.failed",
            trigger_config={},
            actions=[{"type": "task.retry", "params": {"max_retries": 10}}],
            priority=100,
            circuit_breaker_config=circuit_breaker_config
        )
        self.session.add(workflow_db)
        self.session.commit()
        return self.workflow_service._db_to_workflow(workflow_db)

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
