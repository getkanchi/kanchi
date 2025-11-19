"""Tests for workflow circuit breaker preventing infinite loops."""

import unittest
import uuid
from datetime import datetime, timezone, timedelta

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from tests.base import DatabaseTestCase
from services.workflow_service import WorkflowService
from database import WorkflowDB, WorkflowExecutionDB
from models import (
    WorkflowDefinition,
    TriggerConfig,
    ActionConfig,
    CircuitBreakerConfig
)


class TestWorkflowCircuitBreaker(DatabaseTestCase):
    """Test cases for workflow circuit breaker preventing infinite loops."""

    def setUp(self):
        super().setUp()
        self.workflow_service = WorkflowService(self.session)

    def _create_test_workflow(
        self,
        name="Test Workflow",
        circuit_breaker_config=None
    ) -> WorkflowDefinition:
        """Helper to create a test workflow."""
        workflow_db = WorkflowDB(
            id=str(uuid.uuid4()),
            name=name,
            enabled=True,
            trigger_type="task.failed",
            trigger_config={},
            actions=[{"type": "task.retry", "params": {}}],
            priority=100,
            circuit_breaker_config=circuit_breaker_config
        )
        self.session.add(workflow_db)
        self.session.commit()
        return self.workflow_service._db_to_workflow(workflow_db)

    def test_circuit_breaker_open_prevents_execution(self):
        """Test that circuit breaker prevents execution when limit is reached."""
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
        context = {"root_id": root_id, "task_id": str(uuid.uuid4())}

        for i in range(3):
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

        state = self.workflow_service.is_circuit_breaker_open(workflow, context)

        self.assertTrue(state.is_open)
        self.assertIsNotNone(state.reason)
        self.assertIn("Circuit breaker open", state.reason)
        self.assertIn("3 executions", state.reason)
        self.assertEqual(state.key, root_id)
        self.assertEqual(state.field, "root_id")

    def test_circuit_breaker_closed_under_limit(self):
        """Test that circuit breaker allows execution when under limit."""
        circuit_breaker = CircuitBreakerConfig(
            enabled=True,
            max_executions=5,
            window_seconds=300,
            context_field="root_id"
        )

        workflow = self._create_test_workflow(
            circuit_breaker_config=circuit_breaker.dict()
        )

        root_id = str(uuid.uuid4())
        context = {"root_id": root_id, "task_id": str(uuid.uuid4())}

        for i in range(3):
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

        state = self.workflow_service.is_circuit_breaker_open(workflow, context)

        self.assertFalse(state.is_open)
        self.assertIsNone(state.reason)
        self.assertEqual(state.key, root_id)

    def test_circuit_breaker_respects_time_window(self):
        """Test that circuit breaker only counts executions within time window."""
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
        context = {"root_id": root_id, "task_id": str(uuid.uuid4())}

        old_time = datetime.now(timezone.utc) - timedelta(seconds=400)
        for i in range(3):
            execution = WorkflowExecutionDB(
                workflow_id=workflow.id,
                trigger_type="task.failed",
                trigger_event=context,
                status="completed",
                circuit_breaker_key=root_id,
                triggered_at=old_time
            )
            self.session.add(execution)
        self.session.commit()

        state = self.workflow_service.is_circuit_breaker_open(
            workflow, context
        )

        self.assertFalse(state.is_open)
        self.assertIsNone(state.reason)

    def test_circuit_breaker_disabled_always_allows(self):
        """Test that disabled circuit breaker always allows execution."""
        circuit_breaker = CircuitBreakerConfig(
            enabled=False,
            max_executions=1,
            window_seconds=300
        )

        workflow = self._create_test_workflow(
            circuit_breaker_config=circuit_breaker.dict()
        )

        root_id = str(uuid.uuid4())
        context = {"root_id": root_id, "task_id": str(uuid.uuid4())}

        for i in range(10):
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

        state = self.workflow_service.is_circuit_breaker_open(
            workflow, context
        )

        self.assertFalse(state.is_open)
        self.assertIsNone(state.reason)

    def test_circuit_breaker_fallback_to_task_id(self):
        """Test that circuit breaker falls back to task_id when context_field is missing."""
        circuit_breaker = CircuitBreakerConfig(
            enabled=True,
            max_executions=2,
            window_seconds=300,
            context_field="custom_field"
        )

        workflow = self._create_test_workflow(
            circuit_breaker_config=circuit_breaker.dict()
        )

        task_id = str(uuid.uuid4())
        context = {"task_id": task_id}

        key, field = self.workflow_service.resolve_circuit_breaker_key(
            workflow, context
        )

        self.assertEqual(key, task_id)
        self.assertIn(field, ["custom_field", "root_id", "task_id"])

    def test_circuit_breaker_with_different_keys_separate_limits(self):
        """Test that different circuit breaker keys have separate limits."""
        circuit_breaker = CircuitBreakerConfig(
            enabled=True,
            max_executions=2,
            window_seconds=300,
            context_field="root_id"
        )

        workflow = self._create_test_workflow(
            circuit_breaker_config=circuit_breaker.dict()
        )

        root_id_1 = str(uuid.uuid4())
        root_id_2 = str(uuid.uuid4())

        for root_id in [root_id_1, root_id_2]:
            for i in range(2):
                execution = WorkflowExecutionDB(
                    workflow_id=workflow.id,
                    trigger_type="task.failed",
                    trigger_event={"root_id": root_id},
                    status="completed",
                    circuit_breaker_key=root_id,
                    triggered_at=datetime.now(timezone.utc)
                )
                self.session.add(execution)
        self.session.commit()

        state_1 = self.workflow_service.is_circuit_breaker_open(
            workflow, {"root_id": root_id_1, "task_id": str(uuid.uuid4())}
        )
        state_2 = self.workflow_service.is_circuit_breaker_open(
            workflow, {"root_id": root_id_2, "task_id": str(uuid.uuid4())}
        )

        self.assertTrue(state_1.is_open)
        self.assertTrue(state_2.is_open)

        root_id_3 = str(uuid.uuid4())
        state_3 = self.workflow_service.is_circuit_breaker_open(
            workflow, {"root_id": root_id_3, "task_id": str(uuid.uuid4())}
        )
        self.assertFalse(state_3.is_open)

    def test_circuit_breaker_skip_records_execution(self):
        """Test that circuit breaker skip creates execution record."""
        circuit_breaker = CircuitBreakerConfig(
            enabled=True,
            max_executions=1,
            window_seconds=300,
            context_field="root_id"
        )

        workflow = self._create_test_workflow(
            circuit_breaker_config=circuit_breaker.dict()
        )

        root_id = str(uuid.uuid4())
        context = {"root_id": root_id, "task_id": str(uuid.uuid4())}

        self.workflow_service.record_circuit_breaker_skip(
            workflow=workflow,
            trigger_type="task.failed",
            trigger_event=context,
            workflow_snapshot=workflow.model_dump(mode='json'),
            circuit_breaker_key=root_id,
            reason="Circuit breaker test"
        )

        execution = self.session.query(WorkflowExecutionDB).filter_by(
            workflow_id=workflow.id,
            status="circuit_open"
        ).first()

        self.assertIsNotNone(execution)
        self.assertEqual(execution.circuit_breaker_key, root_id)
        self.assertEqual(execution.status, "circuit_open")
        self.assertIn("Circuit breaker test", execution.error_message)

    def test_no_circuit_breaker_config_allows_execution(self):
        """Test that workflows without circuit breaker config always allow execution."""
        workflow = self._create_test_workflow(circuit_breaker_config=None)

        context = {"task_id": str(uuid.uuid4()), "root_id": str(uuid.uuid4())}

        for i in range(100):
            execution = WorkflowExecutionDB(
                workflow_id=workflow.id,
                trigger_type="task.failed",
                trigger_event=context,
                status="completed",
                triggered_at=datetime.now(timezone.utc)
            )
            self.session.add(execution)
        self.session.commit()

        state = self.workflow_service.is_circuit_breaker_open(
            workflow, context
        )

        self.assertFalse(state.is_open)
        self.assertIsNone(state.reason)
        self.assertIsNone(state.key)
        self.assertIsNone(state.field)


if __name__ == '__main__':
    unittest.main()
