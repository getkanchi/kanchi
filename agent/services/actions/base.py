"""Base class for action handlers."""

from abc import ABC, abstractmethod
from typing import Dict, Any
from models import ActionResult


class ActionHandler(ABC):
    """Base class for all action handlers."""

    def __init__(self, session, db_manager, monitor_instance=None):
        """
        Initialize action handler.

        Args:
            session: Database session
            db_manager: DatabaseManager instance
            monitor_instance: CeleryEventMonitor instance (for task operations)
        """
        self.session = session
        self.db_manager = db_manager
        self.monitor_instance = monitor_instance

    @abstractmethod
    async def execute(self, context: Dict[str, Any], params: Dict[str, Any]) -> ActionResult:
        """
        Execute the action.

        Args:
            context: Event context (task_event, worker_event, etc.)
            params: Action-specific parameters from workflow definition

        Returns:
            ActionResult with status and result data
        """
        pass

    @abstractmethod
    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate action parameters.

        Returns:
            (is_valid, error_message)
        """
        pass

    def render_template(self, template: str, context: Dict[str, Any]) -> str:
        """
        Render a template string with context variables.

        Supports simple {{variable}} syntax.
        """
        result = template
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
        return result
