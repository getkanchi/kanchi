"""Dry-run workflow simulation helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from models import (
    AppSettingUpdate,
    WorkflowCreateRequest,
    WorkflowDefinition,
    WorkflowSimulationActionPreview,
    WorkflowSimulationRecord,
    WorkflowSimulationResponse,
)
from services.action_config_service import ActionConfigService
from services.app_config_service import AppConfigService
from services.task_service import TaskService
from services.workflow_engine import WorkflowEngine
from services.workflow_service import WorkflowService
from services.actions.retry_action import RetryActionHandler
from services.actions.slack_action import SlackActionHandler


class WorkflowSimulationService:
    """Evaluate workflows safely without executing actions."""

    HISTORY_LIMIT = 10

    def __init__(self, session, db_manager=None, monitor_instance=None):
        self.session = session
        self.db_manager = db_manager
        self.monitor_instance = monitor_instance
        self.workflow_service = WorkflowService(session)
        self.workflow_engine = WorkflowEngine(db_manager=db_manager, monitor_instance=monitor_instance)
        self.action_config_service = ActionConfigService(session)
        self.app_config_service = AppConfigService(session)
        self.task_service = TaskService(session)

    def simulate(self, workflow_data: WorkflowCreateRequest, test_context: dict[str, Any]) -> WorkflowSimulationResponse:
        actions = self.workflow_service._coerce_actions(workflow_data.actions)
        self.workflow_service._validate_workflow_definition(workflow_data.trigger, actions)

        workflow = WorkflowDefinition(
            name=workflow_data.name,
            description=workflow_data.description,
            enabled=workflow_data.enabled,
            trigger=workflow_data.trigger,
            conditions=workflow_data.conditions,
            actions=actions,
            priority=workflow_data.priority,
            max_executions_per_hour=workflow_data.max_executions_per_hour,
            cooldown_seconds=workflow_data.cooldown_seconds,
            circuit_breaker=workflow_data.circuit_breaker,
        )

        conditions_met = self.workflow_engine._evaluate_conditions(workflow, test_context)
        warnings = self._collect_warnings(workflow_data, test_context)
        action_previews = self._build_action_previews(workflow_data, test_context, conditions_met)
        would_execute = conditions_met and any(preview.status == "would_execute" for preview in action_previews)

        record = WorkflowSimulationRecord(
            simulated_at=datetime.now(timezone.utc),
            workflow_name=workflow.name,
            trigger_type=workflow.trigger.type,
            conditions_met=conditions_met,
            would_execute=would_execute,
            warnings=warnings,
            action_previews=action_previews,
        )
        history = self._store_history(workflow.name, workflow.trigger.type, record)

        return WorkflowSimulationResponse(
            workflow_name=workflow.name,
            trigger_type=workflow.trigger.type,
            test_context=test_context,
            conditions_met=conditions_met,
            would_execute=would_execute,
            warnings=warnings,
            action_previews=action_previews,
            simulation_history=history,
        )

    def _collect_warnings(self, workflow_data: WorkflowCreateRequest, test_context: dict[str, Any]) -> list[str]:
        warnings: list[str] = []
        if not workflow_data.conditions or not workflow_data.conditions.conditions:
            warnings.append("No conditions configured: this workflow will match every event for the selected trigger.")
        if workflow_data.trigger.type in {"task.failed", "task.orphaned", "worker.offline"} and len(workflow_data.actions) > 1:
            warnings.append("Multiple actions on a high-signal trigger can create noisy or risky automation when an incident spikes.")
        for action in workflow_data.actions:
            if action.type == "task.retry":
                if action.params.get("delay_seconds", 0) == 0:
                    warnings.append("Retry action runs immediately; consider adding a delay to avoid retry storms.")
                if action.params.get("max_retries") in (None, ""):
                    warnings.append("Retry action has no custom retry cap; it will fall back to the default handler limit.")
            if action.type == "slack.notify" and not action.params.get("channel"):
                warnings.append("Slack notification relies on the webhook default channel because no explicit channel override is set.")
        if workflow_data.trigger.type.startswith("task.") and "task_id" not in test_context:
            warnings.append("Test context is missing task_id, so task-linked actions may be blocked in the dry run.")
        return warnings

    def _build_action_previews(self, workflow_data: WorkflowCreateRequest, test_context: dict[str, Any], conditions_met: bool) -> list[WorkflowSimulationActionPreview]:
        previews: list[WorkflowSimulationActionPreview] = []
        for action in workflow_data.actions:
            if not conditions_met:
                previews.append(WorkflowSimulationActionPreview(
                    action_type=action.type,
                    status="blocked",
                    summary="Conditions did not match, so this action would not run.",
                ))
                continue
            if action.type == "slack.notify":
                previews.append(self._preview_slack_action(action.params, test_context))
            elif action.type == "task.retry":
                previews.append(self._preview_retry_action(action.params, test_context))
            else:
                previews.append(WorkflowSimulationActionPreview(
                    action_type=action.type,
                    status="blocked",
                    summary="Unsupported action type for dry-run preview.",
                ))
        return previews

    def _preview_slack_action(self, params: dict[str, Any], test_context: dict[str, Any]) -> WorkflowSimulationActionPreview:
        handler = SlackActionHandler(self.session, self.db_manager, self.monitor_instance)
        is_valid, error = handler.validate_params(params)
        if not is_valid:
            return WorkflowSimulationActionPreview(
                action_type="slack.notify",
                status="blocked",
                summary=error,
            )

        config = self.action_config_service.get_config(params["config_id"])
        if not config:
            return WorkflowSimulationActionPreview(
                action_type="slack.notify",
                status="blocked",
                summary=f"Action config not found: {params['config_id']}",
            )

        rendered = handler.render_template(params.get("template", ""), test_context)
        warnings: list[str] = []
        if len(rendered) > 280:
            warnings.append("Rendered Slack message is fairly long and may be noisy in production.")

        return WorkflowSimulationActionPreview(
            action_type="slack.notify",
            status="would_execute",
            summary="Would send a Slack notification.",
            details={
                "config_name": config.name,
                "channel": params.get("channel") or "(webhook default)",
                "message": rendered,
            },
            warnings=warnings,
        )

    def _preview_retry_action(self, params: dict[str, Any], test_context: dict[str, Any]) -> WorkflowSimulationActionPreview:
        handler = RetryActionHandler(self.session, self.db_manager, self.monitor_instance)
        is_valid, error = handler.validate_params(params)
        if not is_valid:
            return WorkflowSimulationActionPreview(
                action_type="task.retry",
                status="blocked",
                summary=error,
            )

        task_id = test_context.get("task_id")
        if not task_id:
            return WorkflowSimulationActionPreview(
                action_type="task.retry",
                status="blocked",
                summary="No task_id in test context, so retry safety could not be evaluated.",
            )

        task_events = self.task_service.get_task_events(task_id)
        warnings: list[str] = []
        details: dict[str, Any] = {
            "task_id": task_id,
            "delay_seconds": params.get("delay_seconds", 0),
            "max_retries": params.get("max_retries", 10),
        }
        if task_events:
            original_task = task_events[-1]
            current_retry_count = handler.count_workflow_retries(task_id, original_task.root_id)
            details.update({
                "task_name": original_task.task_name,
                "queue": original_task.queue or "default",
                "current_retry_depth": current_retry_count,
            })
            if current_retry_count >= details["max_retries"]:
                return WorkflowSimulationActionPreview(
                    action_type="task.retry",
                    status="blocked",
                    summary="Retry cap already reached for this task chain.",
                    details=details,
                    warnings=[
                        f"Workflow retries are already at {current_retry_count}/{details['max_retries']}; a real execution would be rejected."
                    ],
                )
            if current_retry_count + 1 >= details["max_retries"]:
                warnings.append("This dry run is near the retry cap; later real executions may be blocked soon.")
        else:
            warnings.append("Task history was not found in the database; retry preview is based only on the provided context.")
            details["task_name"] = test_context.get("task_name")
            details["queue"] = test_context.get("queue") or "default"

        return WorkflowSimulationActionPreview(
            action_type="task.retry",
            status="would_execute",
            summary="Would enqueue a retry for the matching task.",
            details=details,
            warnings=warnings,
        )

    def _history_key(self, workflow_name: str, trigger_type: str) -> str:
        slug = f"{workflow_name}:{trigger_type}".lower().replace(" ", "-")
        return f"workflow_simulations.{slug}"

    def _store_history(self, workflow_name: str, trigger_type: str, record: WorkflowSimulationRecord) -> list[WorkflowSimulationRecord]:
        key = self._history_key(workflow_name, trigger_type)
        current = self.app_config_service.get_setting_value(key, default=[])
        items = current if isinstance(current, list) else []
        items.insert(0, record.model_dump(mode="json"))
        items = items[: self.HISTORY_LIMIT]
        self.app_config_service.upsert_setting(
            key,
            AppSettingUpdate(
                value=items,
                value_type="json",
                label="Workflow simulation history",
                description="Recent dry-run workflow simulations.",
                category="workflow_simulations",
            ),
        )
        return [WorkflowSimulationRecord(**item) for item in items]
