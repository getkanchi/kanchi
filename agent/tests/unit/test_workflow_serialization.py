"""Tests for workflow JSON serialization (issue #43).

This test suite validates the fix for the mappingproxy JSON serialization error
that occurred when storing workflow executions in the database. The issue was
caused by using the deprecated Pydantic v1 `.dict()` method instead of the
Pydantic v2 `.model_dump(mode='json')` method.

In Pydantic v2:
- .dict() is deprecated and may include non-JSON-serializable objects
- .model_dump(mode='json') properly serializes all types including Enums
- The 'json' mode ensures compatibility with JSON/database storage

The original error:
  TypeError: Object of type mappingproxy is not JSON serializable

See: https://github.com/getkanchi/kanchi/issues/43
"""

import unittest
import uuid
import json
import warnings
from datetime import datetime, timezone

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
    ConditionGroup,
    Condition,
    ConditionOperator,
    CircuitBreakerConfig
)


class TestWorkflowSerialization(DatabaseTestCase):
    """Test cases for workflow JSON serialization bug fix (issue #43)."""

    def setUp(self):
        super().setUp()
        self.workflow_service = WorkflowService(self.session)

    def _create_test_workflow(self) -> WorkflowDefinition:
        """Create a test workflow with conditions to ensure complex serialization."""
        workflow_db = WorkflowDB(
            id=str(uuid.uuid4()),
            name="Test Workflow",
            enabled=True,
            trigger_type="task.succeeded",
            trigger_config={},
            conditions={
                "operator": "AND",
                "conditions": [
                    {
                        "field": "task_name",
                        "operator": "equals",
                        "value": "test_task"
                    }
                ]
            },
            actions=[
                {
                    "type": "slack.send_message",
                    "params": {"message": "Task succeeded"}
                }
            ],
            priority=100,
            circuit_breaker_config={
                "failure_threshold": 5,
                "window_seconds": 300,
                "key_template": "{root_id}"
            }
        )
        self.session.add(workflow_db)
        self.session.commit()
        return self.workflow_service._db_to_workflow(workflow_db)

    def test_workflow_snapshot_is_json_serializable(self):
        """Test that workflow snapshot can be serialized to JSON without mappingproxy errors."""
        workflow = self._create_test_workflow()

        # This is the key operation that was failing with workflow.dict()
        # model_dump(mode='json') should properly serialize including Enums
        workflow_snapshot = workflow.model_dump(mode='json')

        # Verify it can be serialized to JSON (this would fail with mappingproxy)
        try:
            json_str = json.dumps(workflow_snapshot)
            self.assertIsNotNone(json_str)
            self.assertIsInstance(json_str, str)
        except TypeError as e:
            self.fail(f"Workflow snapshot is not JSON serializable: {e}")

        # Verify we can deserialize it back
        deserialized = json.loads(json_str)
        self.assertEqual(deserialized['name'], workflow.name)
        self.assertEqual(deserialized['trigger']['type'], 'task.succeeded')

    def test_workflow_execution_record_with_snapshot(self):
        """Test that workflow execution can be recorded with snapshot in database."""
        workflow = self._create_test_workflow()
        context = {
            "task_id": str(uuid.uuid4()),
            "task_name": "test_task",
            "status": "succeeded"
        }

        # Record workflow execution start - this calls model_dump internally
        execution_id = self.workflow_service.record_workflow_execution_start(
            workflow_id=workflow.id,
            trigger_type="task.succeeded",
            trigger_event=context,
            workflow_snapshot=workflow.model_dump(mode='json'),
            circuit_breaker_key=None
        )

        # Verify the execution was recorded
        execution = self.session.query(WorkflowExecutionDB).filter_by(
            id=execution_id
        ).first()

        self.assertIsNotNone(execution)
        self.assertEqual(execution.workflow_id, workflow.id)
        self.assertEqual(execution.trigger_type, 'task.succeeded')

        # Verify the workflow snapshot was stored correctly
        self.assertIsNotNone(execution.workflow_snapshot)
        self.assertEqual(execution.workflow_snapshot['name'], workflow.name)

        # Verify trigger event was stored
        self.assertIsNotNone(execution.trigger_event)
        self.assertEqual(execution.trigger_event['task_name'], 'test_task')

    def test_circuit_breaker_skip_with_snapshot(self):
        """Test that circuit breaker skip can be recorded with workflow snapshot."""
        workflow = self._create_test_workflow()
        context = {
            "root_id": str(uuid.uuid4()),
            "task_id": str(uuid.uuid4())
        }

        # Record circuit breaker skip - this also uses model_dump
        self.workflow_service.record_circuit_breaker_skip(
            workflow=workflow,
            trigger_type="task.succeeded",
            trigger_event=context,
            workflow_snapshot=workflow.model_dump(mode='json'),
            circuit_breaker_key=context['root_id'],
            reason="Circuit breaker test"
        )

        # Verify the skip was recorded
        execution = self.session.query(WorkflowExecutionDB).filter_by(
            workflow_id=workflow.id,
            status="circuit_open"
        ).first()

        self.assertIsNotNone(execution)
        self.assertEqual(execution.circuit_breaker_key, context['root_id'])
        self.assertEqual(execution.error_message, "Circuit breaker test")

        # Verify the workflow snapshot is present and correct
        self.assertIsNotNone(execution.workflow_snapshot)
        self.assertEqual(execution.workflow_snapshot['name'], workflow.name)

    def test_enum_serialization_in_conditions(self):
        """Test that Enum operators in conditions are properly serialized."""
        workflow = self._create_test_workflow()

        # Get the workflow snapshot
        workflow_snapshot = workflow.model_dump(mode='json')

        # Verify conditions are present and operators are serialized as strings
        self.assertIn('conditions', workflow_snapshot)
        conditions = workflow_snapshot['conditions']['conditions']
        self.assertGreater(len(conditions), 0)

        # Verify the operator is serialized as a string value, not Enum object
        operator = conditions[0]['operator']
        self.assertIsInstance(operator, str)
        self.assertEqual(operator, 'equals')

        # Ensure it can be JSON serialized
        try:
            json.dumps(workflow_snapshot)
        except TypeError as e:
            self.fail(f"Conditions with Enum operators not JSON serializable: {e}")

    def test_deprecated_dict_method_shows_warning(self):
        """Test that .dict() is deprecated and model_dump should be used instead."""
        workflow = self._create_test_workflow()

        # The old .dict() method should produce a deprecation warning
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _ = workflow.dict()

            # Check that a deprecation warning was issued
            self.assertGreater(len(w), 0,
                "Expected deprecation warning for .dict() method")
            self.assertTrue(
                any('deprecated' in str(warning.message).lower() for warning in w),
                "Expected deprecation warning message"
            )

        # The new model_dump(mode='json') should not produce warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _ = workflow.model_dump(mode='json')

            # Filter out unrelated warnings
            pydantic_warnings = [warning for warning in w
                               if 'pydantic' in str(warning.message).lower()]
            self.assertEqual(len(pydantic_warnings), 0,
                f"model_dump should not produce warnings, got: {pydantic_warnings}")

    def test_model_dump_json_mode_vs_default(self):
        """Test that mode='json' properly serializes complex types."""
        workflow = self._create_test_workflow()

        # Without mode='json', some types may not be properly serialized
        default_dump = workflow.model_dump()

        # With mode='json', everything is JSON-serializable
        json_dump = workflow.model_dump(mode='json')

        # Both should be dict-like, but json mode ensures JSON compatibility
        self.assertIsInstance(default_dump, dict)
        self.assertIsInstance(json_dump, dict)

        # The json mode dump should be fully JSON serializable
        try:
            json_str = json.dumps(json_dump)
            self.assertIsNotNone(json_str)
        except TypeError as e:
            self.fail(f"mode='json' dump should be JSON serializable: {e}")

        # Verify enum is properly converted to string in json mode
        if json_dump.get('conditions'):
            operator = json_dump['conditions']['conditions'][0]['operator']
            self.assertIsInstance(operator, str,
                "Enum should be serialized as string in json mode")


if __name__ == '__main__':
    unittest.main()
