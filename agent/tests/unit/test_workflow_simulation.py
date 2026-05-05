"""Tests for workflow dry-run simulation."""

import unittest
from datetime import datetime, timezone

from services.action_config_service import ActionConfigService
from services.workflow_simulation_service import WorkflowSimulationService
from models import WorkflowCreateRequest, TriggerConfig, ActionConfig, ConditionGroup, Condition, ActionConfigCreateRequest
from database import TaskEventDB, RetryRelationshipDB
from tests.base import ServiceTestCase


class TestWorkflowSimulationService(ServiceTestCase):
    def setUp(self):
        super().setUp()
        self.config_service = ActionConfigService(self.session)
        self.config = self.config_service.create_config(
            ActionConfigCreateRequest(
                name="Ops Slack",
                description="",
                action_type="slack.notify",
                config={"webhook_url": "https://hooks.slack.test/services/demo"},
            )
        )
        self.service = WorkflowSimulationService(self.session)

    def test_simulation_previews_actions_and_persists_history(self):
        workflow = WorkflowCreateRequest(
            name="Alert on failed payments",
            trigger=TriggerConfig(type="task.failed", config={}),
            conditions=ConditionGroup(
                operator="AND",
                conditions=[Condition(field="task_name", operator="equals", value="payments.charge")],
            ),
            actions=[
                ActionConfig(
                    type="slack.notify",
                    params={
                        "config_id": self.config.id,
                        "template": "Task {{task_name}} failed for {{task_id}}",
                    },
                )
            ],
        )

        result = self.service.simulate(
            workflow,
            {"task_id": "task-1", "task_name": "payments.charge", "event_type": "task.failed"},
        )

        self.assertTrue(result.conditions_met)
        self.assertTrue(result.would_execute)
        self.assertEqual(result.action_previews[0].status, "would_execute")
        self.assertIn("payments.charge", result.action_previews[0].details["message"])
        self.assertEqual(len(result.simulation_history), 1)
        self.assertEqual(result.simulation_history[0].workflow_name, workflow.name)

    def test_simulation_warns_for_broad_rule_and_blocks_invalid_action(self):
        workflow = WorkflowCreateRequest(
            name="Immediate retry all failures",
            trigger=TriggerConfig(type="task.failed", config={}),
            actions=[ActionConfig(type="task.retry", params={"delay_seconds": 0})],
        )

        result = self.service.simulate(
            workflow,
            {"task_name": "payments.charge", "event_type": "task.failed"},
        )

        self.assertTrue(any("No conditions configured" in warning for warning in result.warnings))
        self.assertTrue(any("missing task_id" in warning for warning in result.warnings))
        self.assertEqual(result.action_previews[0].status, "blocked")
        self.assertIn("No task_id", result.action_previews[0].summary)

    def test_retry_preview_uses_task_history_when_present(self):
        now = datetime.now(timezone.utc)
        self.session.add(TaskEventDB(
            task_id="task-2",
            task_name="reports.generate",
            event_type="task.failed",
            timestamp=now,
            queue="priority",
            root_id="root-2",
        ))
        self.session.commit()

        workflow = WorkflowCreateRequest(
            name="Retry stuck report",
            trigger=TriggerConfig(type="task.failed", config={}),
            conditions=ConditionGroup(operator="AND", conditions=[]),
            actions=[ActionConfig(type="task.retry", params={"delay_seconds": 30, "max_retries": 3})],
        )

        result = self.service.simulate(
            workflow,
            {"task_id": "task-2", "task_name": "reports.generate", "event_type": "task.failed"},
        )

        self.assertEqual(result.action_previews[0].status, "would_execute")
        self.assertEqual(result.action_previews[0].details["queue"], "priority")
        self.assertEqual(result.action_previews[0].details["current_retry_depth"], 0)

    def test_retry_preview_blocks_when_retry_cap_is_already_reached(self):
        now = datetime.now(timezone.utc)
        self.session.add(TaskEventDB(
            task_id="task-3",
            task_name="reports.generate",
            event_type="task.failed",
            timestamp=now,
            queue="priority",
            root_id="root-3",
        ))
        self.session.add(RetryRelationshipDB(task_id="task-3", original_id="retry-2"))
        self.session.add(RetryRelationshipDB(task_id="retry-2", original_id="retry-1"))
        self.session.add(RetryRelationshipDB(task_id="retry-1", original_id="root-3"))
        self.session.commit()

        workflow = WorkflowCreateRequest(
            name="Retry capped report",
            trigger=TriggerConfig(type="task.failed", config={}),
            conditions=ConditionGroup(operator="AND", conditions=[]),
            actions=[ActionConfig(type="task.retry", params={"delay_seconds": 30, "max_retries": 3})],
        )

        result = self.service.simulate(
            workflow,
            {"task_id": "task-3", "task_name": "reports.generate", "event_type": "task.failed"},
        )

        self.assertEqual(result.action_previews[0].status, "blocked")
        self.assertIn("Retry cap already reached", result.action_previews[0].summary)
        self.assertEqual(result.action_previews[0].details["current_retry_depth"], 3)

    def test_retry_preview_blocks_from_context_when_history_is_missing(self):
        workflow = WorkflowCreateRequest(
            name="Retry capped by context",
            trigger=TriggerConfig(type="task.failed", config={}),
            conditions=ConditionGroup(operator="AND", conditions=[]),
            actions=[ActionConfig(type="task.retry", params={"delay_seconds": 30, "max_retries": 3})],
        )

        result = self.service.simulate(
            workflow,
            {
                "task_id": "task-missing",
                "task_name": "reports.generate",
                "event_type": "task.failed",
                "retry_count": 3,
            },
        )

        self.assertEqual(result.action_previews[0].status, "blocked")
        self.assertIn("Would NOT enqueue a retry", result.action_previews[0].summary)
        self.assertEqual(result.action_previews[0].details["current_retry_depth"], 3)
        self.assertTrue(any("would be rejected" in warning for warning in result.action_previews[0].warnings))


if __name__ == "__main__":
    unittest.main()
