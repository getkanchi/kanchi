"""Shared notification policy helpers for workflow notification actions."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import and_
from sqlalchemy.orm import Session

from database import WorkflowExecutionDB

SEVERITY_ORDER = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "critical": 3,
}


class NotificationPolicyHelper:
    """Evaluate notification policy fields stored on workflow action params."""

    def __init__(self, session: Session):
        self.session = session

    def evaluate(
        self,
        action_type: str,
        context: Dict[str, Any],
        params: Dict[str, Any],
        render_template,
    ) -> Tuple[bool, Dict[str, Any], Dict[str, Any]]:
        policy = params.get("notification_policy") or {}
        metadata: Dict[str, Any] = {"stage": "initial", "severity": self._get_severity(context)}
        merged_params = dict(params)

        severity = metadata["severity"]
        min_severity = policy.get("minimum_severity")
        if min_severity and self._severity_rank(severity) < self._severity_rank(min_severity):
            metadata["skip_reason"] = f"Severity {severity} below {min_severity}"
            return False, metadata, merged_params

        duration_seconds = self._get_duration_seconds(context)
        metadata["duration_seconds"] = duration_seconds
        min_duration = policy.get("minimum_duration_seconds")
        if min_duration and duration_seconds < int(min_duration):
            metadata["skip_reason"] = f"Duration {duration_seconds}s below {int(min_duration)}s"
            return False, metadata, merged_params

        stage = self._select_stage(policy, duration_seconds, severity)
        if stage:
            metadata["stage"] = stage.get("name") or "escalated"
            for key in ("template", "channel", "color", "config_id"):
                if stage.get(key):
                    merged_params[key] = stage[key]

        dedupe_window = int(policy.get("dedupe_window_seconds") or 0)
        dedupe_template = policy.get("dedupe_key_template") or "{{task_name}}:{{event_type}}:{{task_id}}"
        dedupe_key = render_template(dedupe_template, context)
        notification_key = f"{action_type}:{metadata['stage']}:{dedupe_key}"
        metadata["notification_key"] = notification_key
        metadata["dedupe_window_seconds"] = dedupe_window

        if dedupe_window > 0 and self._was_recently_sent(context, action_type, notification_key, dedupe_window):
            metadata["skip_reason"] = f"Notification suppressed for {dedupe_window}s dedupe window"
            return False, metadata, merged_params

        return True, metadata, merged_params

    def build_preview(self, context: Dict[str, Any], params: Dict[str, Any], render_template) -> Dict[str, Any]:
        should_send, metadata, resolved = self.evaluate("preview", context, params, render_template)
        return {
            "would_send": should_send,
            "stage": metadata.get("stage", "initial"),
            "severity": metadata.get("severity"),
            "duration_seconds": metadata.get("duration_seconds"),
            "skip_reason": metadata.get("skip_reason"),
            "template": resolved.get("template"),
            "channel": resolved.get("channel"),
            "color": resolved.get("color"),
            "config_id": resolved.get("config_id"),
        }

    def _select_stage(self, policy: Dict[str, Any], duration_seconds: int, severity: str) -> Optional[Dict[str, Any]]:
        steps = policy.get("escalation_steps") or []
        selected = None
        for step in steps:
            after = int(step.get("after_seconds") or 0)
            step_min_severity = step.get("minimum_severity")
            if duration_seconds < after:
                continue
            if step_min_severity and self._severity_rank(severity) < self._severity_rank(step_min_severity):
                continue
            if selected is None or after >= int(selected.get("after_seconds") or 0):
                selected = step
        return selected

    def _get_severity(self, context: Dict[str, Any]) -> str:
        severity = str(context.get("severity") or "low").strip().lower()
        return severity if severity in SEVERITY_ORDER else "low"

    def _get_duration_seconds(self, context: Dict[str, Any]) -> int:
        duration = context.get("duration_seconds")
        if isinstance(duration, (int, float)):
            return max(0, int(duration))
        runtime = context.get("runtime")
        if isinstance(runtime, (int, float)):
            return max(0, int(runtime))
        return 0

    def _severity_rank(self, severity: str) -> int:
        return SEVERITY_ORDER.get(str(severity).lower(), 0)

    def _was_recently_sent(self, context: Dict[str, Any], action_type: str, notification_key: str, window_seconds: int) -> bool:
        workflow = context.get("_workflow") or {}
        workflow_id = workflow.get("id")
        if not workflow_id:
            return False

        cutoff = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
        recent_executions = self.session.query(WorkflowExecutionDB).filter(
            and_(
                WorkflowExecutionDB.workflow_id == workflow_id,
                WorkflowExecutionDB.triggered_at >= cutoff,
            )
        ).all()

        for execution in recent_executions:
            for action in execution.actions_executed or []:
                if action.get("action_type") != action_type or action.get("status") != "success":
                    continue
                result = action.get("result") or {}
                if result.get("notification_key") == notification_key:
                    return True
        return False
