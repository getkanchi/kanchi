"""Task retry action handler."""

import ast
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Tuple, Optional

from .base import ActionHandler
from models import ActionResult, TaskEvent
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
            args, kwargs = self._resolve_call_signature(context, task_events)

            max_retries = params.get("max_retries", 10)
            current_retry_count = self._count_workflow_retries(task_id, original_task.root_id)

            if current_retry_count >= max_retries:
                return ActionResult(
                    action_type="task.retry",
                    status="failed",
                    error_message=(
                        f"Max retry limit reached ({current_retry_count}/{max_retries}). "
                        f"Task {task_id} will not be retried to prevent infinite loops."
                    ),
                    result={
                        "task_id": task_id,
                        "root_id": original_task.root_id,
                        "retry_count": current_retry_count,
                        "max_retries": max_retries
                    },
                    duration_ms=int((datetime.now() - start_time).total_seconds() * 1000)
                )

            queue_name = original_task.queue if original_task.queue else 'default'
            new_task_id = str(uuid.uuid4())

            task_service.create_retry_relationship(task_id, new_task_id)
            self.session.commit()

            delay_seconds = params.get("delay_seconds", 0)
            countdown = delay_seconds if delay_seconds > 0 else None

            # CRITICAL: Preserve root_id across retries for circuit breaker tracking
            # Use the original task's root_id, or its task_id if root_id is not set
            preserved_root_id = original_task.root_id if original_task.root_id else task_id

            self.monitor_instance.app.send_task(
                original_task.task_name,
                args=args,
                kwargs=kwargs,
                queue=queue_name,
                task_id=new_task_id,
                root_id=preserved_root_id,  # This makes circuit breaker work!
                countdown=countdown
            )

            duration = int((datetime.now() - start_time).total_seconds() * 1000)

            logger.info(
                "Workflow action retried task %s -> %s (retry %d/%d, args=%s kwargs=%s)",
                task_id,
                new_task_id,
                current_retry_count + 1,
                max_retries,
                args,
                kwargs,
            )

            return ActionResult(
                action_type="task.retry",
                status="success",
                result={
                    "original_task_id": task_id,
                    "new_task_id": new_task_id,
                    "task_name": original_task.task_name,
                    "queue": queue_name,
                    "delay_seconds": delay_seconds,
                    "retry_count": current_retry_count + 1,
                    "max_retries": max_retries,
                    "args": args,
                    "kwargs": kwargs
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
        """Validate retry action parameters."""
        if "delay_seconds" in params:
            if not isinstance(params["delay_seconds"], (int, float)):
                return False, "delay_seconds must be a number"
            if params["delay_seconds"] < 0:
                return False, "delay_seconds cannot be negative"

        if "max_retries" in params:
            if not isinstance(params["max_retries"], int):
                return False, "max_retries must be an integer"
            if params["max_retries"] < 1:
                return False, "max_retries must be at least 1"
            if params["max_retries"] > 100:
                return False, "max_retries cannot exceed 100 (safety limit)"

        return True, ""

    def _resolve_call_signature(
        self,
        context: Dict[str, Any],
        task_events: List[TaskEvent]
    ) -> Tuple[tuple, dict]:
        """Prefer context args, then walk task history until we find a usable call signature."""
        args = self._parse_args(context.get("args"))
        kwargs = self._parse_kwargs(context.get("kwargs"))

        if args or kwargs:
            return args, kwargs

        for event in reversed(task_events):
            args = self._parse_args(event.args)
            kwargs = self._parse_kwargs(event.kwargs)
            if args or kwargs:
                return args, kwargs

        return (), {}

    def _parse_args(self, raw_value: Any) -> tuple:
        """Convert stored args (JSON string/list/tuple) to tuple."""
        if raw_value in (None, "", "()", "[]"):
            return ()

        parsed = self._deserialize_value(raw_value, [])
        if parsed in (None, "", (), [], "()", "[]"):
            return ()

        if isinstance(parsed, tuple):
            return parsed
        if isinstance(parsed, list):
            return tuple(parsed)
        return (parsed,)

    def _parse_kwargs(self, raw_value: Any) -> dict:
        """Convert stored kwargs (JSON string/dict) to dict."""
        if raw_value in (None, "", "{}"):
            return {}

        parsed = self._deserialize_value(raw_value, {})
        if isinstance(parsed, dict):
            return parsed
        return {}

    def _deserialize_value(self, raw_value: Any, default: Any) -> Any:
        """Attempt JSON first, then literal eval, else fallback."""
        if isinstance(raw_value, (list, dict, tuple)):
            return raw_value

        if isinstance(raw_value, str):
            text = raw_value.strip()
            if not text:
                return default

            try:
                return json.loads(text)
            except (ValueError, json.JSONDecodeError):
                try:
                    return ast.literal_eval(text)
                except (ValueError, SyntaxError):
                    return default

        return raw_value if raw_value is not None else default

    def _count_workflow_retries(self, task_id: str, root_id: Optional[str]) -> int:
        """
        Count how many times this task chain has been retried by workflows.

        Walks back through the retry chain to count total depth.
        """
        if not root_id:
            root_id = task_id

        try:
            from database import RetryRelationshipDB

            retry_depth = 0
            current_id = task_id
            visited = set()

            while current_id and current_id not in visited:
                visited.add(current_id)

                rel = self.session.query(RetryRelationshipDB).filter(
                    RetryRelationshipDB.task_id == current_id
                ).first()

                if not rel:
                    break

                if rel.task_id == rel.original_id:
                    break

                retry_depth += 1
                current_id = rel.original_id

            return retry_depth

        except Exception as e:
            logger.warning(f"Error counting workflow retries: {e}")
            return 0
