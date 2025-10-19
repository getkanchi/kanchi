"""Workflow engine for evaluating and executing workflows."""

import logging
import asyncio
import re
import threading
from typing import Dict, Any

from models import (
    TaskEvent,
    WorkerEvent,
    WorkflowDefinition,
    Condition,
    ConditionOperator
)
from services.workflow_service import WorkflowService
from services.workflow_executor import WorkflowExecutor

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """Engine for processing events and triggering workflows."""

    EVENT_TRIGGER_MAP = {
        "task-sent": "task.sent",
        "task-received": "task.received",
        "task-started": "task.started",
        "task-succeeded": "task.succeeded",
        "task-failed": "task.failed",
        "task-retried": "task.retried",
        "task-revoked": "task.revoked",
        "task-orphaned": "task.orphaned",
        "worker-online": "worker.online",
        "worker-offline": "worker.offline",
        "worker-heartbeat": "worker.heartbeat",
    }

    def __init__(self, db_manager, monitor_instance=None):
        self.db_manager = db_manager
        self.monitor_instance = monitor_instance

    def process_event(self, event: TaskEvent | WorkerEvent):
        """
        Process an event and trigger matching workflows.

        This is called synchronously from EventHandler, but workflows
        are executed asynchronously to avoid blocking.
        """
        try:
            trigger_type = self.EVENT_TRIGGER_MAP.get(event.event_type, None)

            if not trigger_type:
                return

            context = event.model_dump()

            thread = threading.Thread(
                target=self._run_async_workflow_evaluation,
                args=(trigger_type, context, event),
                daemon=True
            )
            thread.start()

        except Exception as e:
            logger.error(f"Error processing event for workflows: {e}", exc_info=True)

    def _run_async_workflow_evaluation(
        self,
        trigger_type: str,
        context: Dict[str, Any],
        event: TaskEvent | WorkerEvent
    ):
        """Run async workflow evaluation in a new event loop."""
        try:
            asyncio.run(self._evaluate_and_execute_workflows(trigger_type, context, event))
        except Exception as e:
            logger.error(f"Error running workflow evaluation: {e}", exc_info=True)

    async def _evaluate_and_execute_workflows(
        self,
        trigger_type: str,
        context: Dict[str, Any],
        event: TaskEvent | WorkerEvent
    ):
        """Evaluate and execute matching workflows (async)."""
        with self.db_manager.get_session() as session:
            workflow_service = WorkflowService(session)

            workflows = workflow_service.get_active_workflows_for_trigger(trigger_type)

            if not workflows:
                return

            logger.debug(f"Found {len(workflows)} workflows for trigger {trigger_type}")

            for workflow in workflows:
                try:
                    can_execute, reason = workflow_service.can_execute_workflow(workflow.id)

                    if not can_execute:
                        logger.debug(f"Skipping workflow {workflow.name}: {reason}")
                        continue

                    if not self._evaluate_conditions(workflow, context):
                        logger.debug(f"Workflow conditions not met: {workflow.name}")
                        continue

                    logger.info(f"Executing workflow: {workflow.name} (trigger={trigger_type})")

                    executor = WorkflowExecutor(
                        session=session,
                        db_manager=self.db_manager,
                        monitor_instance=self.monitor_instance
                    )

                    await executor.execute_workflow(workflow, context, event)

                except Exception as e:
                    logger.error(f"Error evaluating workflow {workflow.name}: {e}", exc_info=True)

    def _evaluate_conditions(
        self,
        workflow: WorkflowDefinition,
        context: Dict[str, Any]
    ) -> bool:
        if not workflow.conditions:
            return True

        return self._evaluate_condition_group(workflow.conditions, context)

    def _evaluate_condition_group(
        self,
        condition_group,
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate a group of conditions with AND/OR logic."""
        if not condition_group.conditions:
            return True

        results = [
            self._evaluate_single_condition(cond, context)
            for cond in condition_group.conditions
        ]

        if condition_group.operator == "AND":
            return all(results)
        else:  # OR
            return any(results)

    def _evaluate_single_condition(
        self,
        condition: Condition,
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate a single condition."""
        field_value = context.get(condition.field)

        if field_value is None:
            return condition.operator == ConditionOperator.NOT_EQUALS

        operator = condition.operator
        expected_value = condition.value

        try:
            if operator == ConditionOperator.EQUALS:
                return field_value == expected_value

            elif operator == ConditionOperator.NOT_EQUALS:
                return field_value != expected_value

            elif operator == ConditionOperator.IN:
                return field_value in expected_value

            elif operator == ConditionOperator.NOT_IN:
                return field_value not in expected_value

            elif operator == ConditionOperator.MATCHES:
                pattern = re.compile(expected_value)
                return bool(pattern.search(str(field_value)))

            elif operator == ConditionOperator.GREATER_THAN:
                return float(field_value) > float(expected_value)

            elif operator == ConditionOperator.LESS_THAN:
                return float(field_value) < float(expected_value)

            elif operator == ConditionOperator.GREATER_EQUAL:
                return float(field_value) >= float(expected_value)

            elif operator == ConditionOperator.LESS_EQUAL:
                return float(field_value) <= float(expected_value)

            elif operator == ConditionOperator.CONTAINS:
                return expected_value in str(field_value)

            elif operator == ConditionOperator.STARTS_WITH:
                return str(field_value).startswith(expected_value)

            elif operator == ConditionOperator.ENDS_WITH:
                return str(field_value).endswith(expected_value)

            else:
                logger.warning(f"Unknown operator: {operator}")
                return False

        except Exception as e:
            logger.error(f"Error evaluating condition: {e}", exc_info=True)
            return False
