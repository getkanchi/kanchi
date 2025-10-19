"""Task retry action handler."""

import logging
import uuid
from typing import Dict, Any
from datetime import datetime

from .base import ActionHandler
from models import ActionResult
from services.task_service import TaskService

logger = logging.getLogger(__name__)


class RetryActionHandler(ActionHandler):
    """Handler for retrying tasks."""

    async def execute(self, context: Dict[str, Any], params: Dict[str, Any]) -> ActionResult:
        """Retry a task."""
        start_time = datetime.now()

        try:
            is_valid, error = self.validate_params(params)
            if not is_valid:
                return ActionResult(
                    action_type="task.retry",
                    status="failed",
                    error_message=error,
                    duration_ms=0
                )

            task_id = context.get("task_id")
            if not task_id:
                return ActionResult(
                    action_type="task.retry",
                    status="failed",
                    error_message="No task_id in context",
                    duration_ms=0
                )

            if not self.monitor_instance:
                return ActionResult(
                    action_type="task.retry",
                    status="failed",
                    error_message="Celery monitor not available",
                    duration_ms=0
                )

            task_service = TaskService(self.session)
            task_events = task_service.get_task_events(task_id)

            if not task_events:
                return ActionResult(
                    action_type="task.retry",
                    status="failed",
                    error_message=f"Task not found: {task_id}",
                    duration_ms=0
                )

            original_task = task_events[-1]

            import ast
            try:
                args = ast.literal_eval(original_task.args) if original_task.args and original_task.args != "()" else ()
                kwargs = ast.literal_eval(original_task.kwargs) if original_task.kwargs and original_task.kwargs != "{}" else {}
            except (ValueError, SyntaxError):
                args = ()
                kwargs = {}

            queue_name = original_task.queue if original_task.queue else 'default'
            new_task_id = str(uuid.uuid4())

            task_service.create_retry_relationship(task_id, new_task_id)
            self.session.commit()

            delay_seconds = params.get("delay_seconds", 0)
            countdown = delay_seconds if delay_seconds > 0 else None

            result = self.monitor_instance.app.send_task(
                original_task.task_name,
                args=args,
                kwargs=kwargs,
                queue=queue_name,
                task_id=new_task_id,
                countdown=countdown
            )

            duration = int((datetime.now() - start_time).total_seconds() * 1000)

            logger.info(f"Workflow action retried task {task_id} -> {new_task_id}")

            return ActionResult(
                action_type="task.retry",
                status="success",
                result={
                    "original_task_id": task_id,
                    "new_task_id": new_task_id,
                    "task_name": original_task.task_name,
                    "queue": queue_name,
                    "delay_seconds": delay_seconds
                },
                duration_ms=duration
            )

        except Exception as e:
            logger.error(f"Task retry failed: {e}", exc_info=True)
            duration = int((datetime.now() - start_time).total_seconds() * 1000)
            return ActionResult(
                action_type="task.retry",
                status="failed",
                error_message=str(e),
                duration_ms=duration
            )

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, str]:
        """Validate retry action parameters. All parameters are optional."""
        if "delay_seconds" in params:
            if not isinstance(params["delay_seconds"], (int, float)):
                return False, "delay_seconds must be a number"
            if params["delay_seconds"] < 0:
                return False, "delay_seconds cannot be negative"

        return True, ""
