"""Slack notification action handler."""

import logging
import aiohttp
from typing import Dict, Any
from datetime import datetime

from .base import ActionHandler
from .notification_policy import NotificationPolicyHelper
from models import ActionResult
from services.action_config_service import ActionConfigService

logger = logging.getLogger(__name__)


class SlackActionHandler(ActionHandler):
    """Handler for Slack notifications."""

    async def execute(self, context: Dict[str, Any], params: Dict[str, Any]) -> ActionResult:
        """Send Slack notification."""
        start_time = datetime.now()

        try:
            is_valid, error = self.validate_params(params)
            if not is_valid:
                return ActionResult(
                    action_type="slack.notify",
                    status="failed",
                    error_message=error,
                    duration_ms=0
                )

            policy_helper = NotificationPolicyHelper(self.session)
            should_send, policy_metadata, resolved_params = policy_helper.evaluate(
                "slack.notify",
                context,
                params,
                self.render_template,
            )

            if not should_send:
                return ActionResult(
                    action_type="slack.notify",
                    status="skipped",
                    result=policy_metadata,
                    duration_ms=int((datetime.now() - start_time).total_seconds() * 1000)
                )

            config_service = ActionConfigService(self.session)
            config = config_service.get_config(resolved_params["config_id"])

            if not config:
                return ActionResult(
                    action_type="slack.notify",
                    status="failed",
                    error_message=f"Action config not found: {resolved_params['config_id']}",
                    duration_ms=0
                )

            webhook_url = config.config.get("webhook_url")
            if not webhook_url:
                return ActionResult(
                    action_type="slack.notify",
                    status="failed",
                    error_message="Webhook URL not configured",
                    duration_ms=0
                )

            message = self.render_template(resolved_params.get("template", ""), context)

            payload = self._build_slack_payload(
                message=message,
                channel=resolved_params.get("channel"),
                username=resolved_params.get("username", "Kanchi Alert"),
                icon_emoji=resolved_params.get("icon_emoji", ":robot_face:"),
                color=resolved_params.get("color", "#36a64f"),
                include_context=resolved_params.get("include_context", True),
                context=context if resolved_params.get("include_context", True) else None
            )

            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return ActionResult(
                            action_type="slack.notify",
                            status="failed",
                            error_message=f"Slack API error: {response.status} - {error_text}",
                            duration_ms=int((datetime.now() - start_time).total_seconds() * 1000)
                        )

            config_service.increment_usage(config.id)

            duration = int((datetime.now() - start_time).total_seconds() * 1000)

            return ActionResult(
                action_type="slack.notify",
                status="success",
                result={
                    "message": message,
                    "webhook_url": webhook_url[:30] + "...",  # Truncate for security
                    "channel": resolved_params.get("channel"),
                    "notification_key": policy_metadata.get("notification_key"),
                    "stage": policy_metadata.get("stage", "initial"),
                    "severity": policy_metadata.get("severity"),
                },
                duration_ms=duration
            )

        except Exception as e:
            logger.error(f"Slack notification failed: {e}", exc_info=True)
            duration = int((datetime.now() - start_time).total_seconds() * 1000)
            return ActionResult(
                action_type="slack.notify",
                status="failed",
                error_message=str(e),
                duration_ms=duration
            )

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, str]:
        """Validate Slack action parameters."""
        if "config_id" not in params:
            return False, "Missing required parameter: config_id"

        if "template" not in params:
            return False, "Missing required parameter: template"

        return True, ""

    def preview(self, context: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        policy_helper = NotificationPolicyHelper(self.session)
        preview = policy_helper.build_preview(context, params, self.render_template)
        resolved = dict(params)
        for key in ("template", "channel", "color", "config_id"):
            if preview.get(key):
                resolved[key] = preview[key]
        message = self.render_template(resolved.get("template", ""), context)
        return {
            **preview,
            "message": message,
            "channel": resolved.get("channel"),
            "color": resolved.get("color", "#36a64f"),
        }

    def _build_slack_payload(
        self,
        message: str,
        channel: str = None,
        username: str = "Kanchi",
        icon_emoji: str = ":robot_face:",
        color: str = "#36a64f",
        include_context: bool = True,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Build Slack message payload with rich formatting."""
        payload = {
            "username": username,
            "icon_emoji": icon_emoji
        }

        if channel:
            payload["channel"] = channel

        attachment = {
            "color": color,
            "text": message,
            "footer": "Kanchi Workflow Automation",
            "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
            "ts": int(datetime.now().timestamp())
        }

        if include_context and context:
            fields = []

            if "task_id" in context:
                fields.append({
                    "title": "Task ID",
                    "value": f"`{context['task_id']}`",
                    "short": True
                })

            if "task_name" in context:
                fields.append({
                    "title": "Task Name",
                    "value": context["task_name"],
                    "short": True
                })

            if "event_type" in context:
                fields.append({
                    "title": "Event",
                    "value": context["event_type"],
                    "short": True
                })

            if "queue" in context:
                fields.append({
                    "title": "Queue",
                    "value": context["queue"],
                    "short": True
                })

            if "retry_count" in context and context["retry_count"] > 0:
                fields.append({
                    "title": "Retries",
                    "value": str(context["retry_count"]),
                    "short": True
                })

            if "exception" in context and context["exception"]:
                fields.append({
                    "title": "Error",
                    "value": f"```{context['exception'][:200]}```",
                    "short": False
                })

            if fields:
                attachment["fields"] = fields

        payload["attachments"] = [attachment]

        return payload
