"""Action executor that routes to specific action handlers."""

import logging
from typing import Dict, Any, Type
from sqlalchemy.orm import Session

from services.actions.base import ActionHandler
from services.actions.slack_action import SlackActionHandler
from services.actions.retry_action import RetryActionHandler
from models import ActionResult

logger = logging.getLogger(__name__)


class ActionExecutor:
    """Executes workflow actions by routing to specific handlers."""

    ACTION_HANDLERS: Dict[str, Type[ActionHandler]] = {
        "slack.notify": SlackActionHandler,
        "task.retry": RetryActionHandler,
    }
    ACTION_CATALOG = {
        "slack.notify": {
            "type": "slack.notify",
            "label": "Slack Notification",
            "description": "Send a templated message to Slack",
            "category": "notification",
        },
        "task.retry": {
            "type": "task.retry",
            "label": "Retry Task",
            "description": "Retry the Celery task with optional delay",
            "category": "task",
        },
    }

    def __init__(self, session: Session, db_manager, monitor_instance=None):
        self.session = session
        self.db_manager = db_manager
        self.monitor_instance = monitor_instance

    async def execute(
        self,
        action_type: str,
        context: Dict[str, Any],
        params: Dict[str, Any]
    ) -> ActionResult:
        """
        Execute an action.

        Args:
            action_type: Type of action (e.g., "slack.notify")
            context: Execution context with event data
            params: Action-specific parameters

        Returns:
            ActionResult with execution status
        """
        handler_class = self.ACTION_HANDLERS.get(action_type)

        if not handler_class:
            logger.error(f"Unknown action type: {action_type}")
            return ActionResult(
                action_type=action_type,
                status="failed",
                error_message=f"Unknown action type: {action_type}",
                duration_ms=0
            )

        handler = handler_class(
            session=self.session,
            db_manager=self.db_manager,
            monitor_instance=self.monitor_instance
        )

        try:
            result = await handler.execute(context, params)
            return result
        except Exception as e:
            logger.error(f"Action execution failed: {action_type} - {e}", exc_info=True)
            return ActionResult(
                action_type=action_type,
                status="failed",
                error_message=str(e),
                duration_ms=0
            )

    @classmethod
    def get_supported_actions(cls) -> list[str]:
        """Get list of supported action types."""
        return list(cls.ACTION_HANDLERS.keys())

    @classmethod
    def get_action_catalog(cls) -> list[dict[str, str]]:
        """Return metadata for supported actions."""
        return [cls.ACTION_CATALOG[action] for action in cls.get_supported_actions() if action in cls.ACTION_CATALOG]

    @classmethod
    def register_action_handler(cls, action_type: str, handler_class: Type[ActionHandler]):
        """Register a new action handler (for extensibility)."""
        cls.ACTION_HANDLERS[action_type] = handler_class
        logger.info(f"Registered action handler: {action_type}")
