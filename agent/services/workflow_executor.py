"""Workflow executor for running workflow actions."""

import logging
import traceback
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from models import TaskEvent, WorkerEvent, WorkflowDefinition
from services.workflow_service import WorkflowService
from services.action_executor import ActionExecutor
from services.audit_service import AuditLogService

logger = logging.getLogger(__name__)


class WorkflowExecutor:
    """Executes workflow actions and manages execution lifecycle."""

    def __init__(self, session: Session, db_manager, monitor_instance=None):
        self.session = session
        self.db_manager = db_manager
        self.monitor_instance = monitor_instance

    async def execute_workflow(
        self,
        workflow: WorkflowDefinition,
        context: Dict[str, Any],
        event: TaskEvent | WorkerEvent,
        circuit_breaker_key: Optional[str] = None
    ):
        """Execute a workflow's actions."""
        workflow_service = WorkflowService(self.session)

        if circuit_breaker_key is None:
            circuit_breaker_key, _ = workflow_service.resolve_circuit_breaker_key(workflow, context)

        execution_id = workflow_service.record_workflow_execution_start(
            workflow_id=workflow.id,
            trigger_type=workflow.trigger.type,
            trigger_event=context,
            workflow_snapshot=workflow.model_dump(),
            circuit_breaker_key=circuit_breaker_key
        )

        logger.info(f"Started workflow execution: {workflow.name} (execution_id={execution_id})")

        action_results = []
        overall_status = "completed"
        error_message = None
        stack_trace = None
        audit_service = AuditLogService(self.session)

        try:
            action_executor = ActionExecutor(
                session=self.session,
                db_manager=self.db_manager,
                monitor_instance=self.monitor_instance
            )

            for idx, action_config in enumerate(workflow.actions):
                logger.info(
                    f"Executing action {idx+1}/{len(workflow.actions)}: "
                    f"{action_config.type} (workflow={workflow.name})"
                )

                result = await action_executor.execute(
                    action_type=action_config.type,
                    context=context,
                    params=action_config.params
                )

                action_results.append({
                    "action_type": result.action_type,
                    "status": result.status,
                    "result": result.result,
                    "error_message": result.error_message,
                    "duration_ms": result.duration_ms
                })

                target = self._resolve_action_target(workflow, context, result.result)
                audit_service.record_safe_entry(
                    source="workflow",
                    action_type=f"workflow.action.{result.action_type}",
                    status=result.status,
                    actor_type="workflow",
                    actor_id=workflow.id,
                    actor_name=workflow.name,
                    target_type=target["target_type"],
                    target_id=target["target_id"],
                    target_label=target.get("target_label"),
                    task_id=target.get("task_id"),
                    related_task_id=target.get("related_task_id"),
                    workflow_id=workflow.id,
                    execution_id=execution_id,
                    reason=result.error_message,
                    result_summary=self._summarize_action_result(result),
                    details={
                        "trigger_type": workflow.trigger.type,
                        "params": action_config.params,
                        "result": result.result or {},
                    },
                )

                if result.status == "failed":
                    logger.warning(
                        f"Action failed: {action_config.type} - {result.error_message} "
                        f"(workflow={workflow.name})"
                    )

                    if not action_config.continue_on_failure:
                        logger.info(f"Stopping workflow execution due to action failure")
                        overall_status = "failed"
                        error_message = f"Action {action_config.type} failed: {result.error_message}"
                        break

            workflow_service.update_workflow_stats(
                workflow_id=workflow.id,
                success=(overall_status == "completed")
            )

            logger.info(
                f"Completed workflow execution: {workflow.name} "
                f"(status={overall_status}, actions={len(action_results)})"
            )

        except Exception as e:
            overall_status = "failed"
            error_message = str(e)
            stack_trace = traceback.format_exc()
            logger.error(
                f"Workflow execution error: {workflow.name} - {e}",
                exc_info=True
            )

        finally:
            workflow_service.update_workflow_execution(
                execution_id=execution_id,
                status=overall_status,
                actions_executed=action_results,
                error_message=error_message,
                stack_trace=stack_trace
            )
            audit_service.record_safe_entry(
                source="workflow",
                action_type="workflow.execution",
                status="success" if overall_status == "completed" else "failed",
                actor_type="workflow",
                actor_id=workflow.id,
                actor_name=workflow.name,
                target_type="workflow",
                target_id=workflow.id or "",
                target_label=workflow.name,
                task_id=context.get("task_id"),
                workflow_id=workflow.id,
                execution_id=execution_id,
                reason=error_message,
                result_summary=self._summarize_workflow_result(action_results, overall_status),
                details={
                    "trigger_type": workflow.trigger.type,
                    "actions_executed": action_results,
                    "circuit_breaker_key": circuit_breaker_key,
                },
            )

    @staticmethod
    def _resolve_action_target(
        workflow: WorkflowDefinition,
        context: Dict[str, Any],
        result: Optional[Dict[str, Any]],
    ) -> Dict[str, Optional[str]]:
        """Resolve the primary target for an action audit entry."""
        result = result or {}

        if result.get("original_task_id"):
            return {
                "target_type": "task",
                "target_id": result["original_task_id"],
                "target_label": result.get("task_name") or context.get("task_name"),
                "task_id": result["original_task_id"],
                "related_task_id": result.get("new_task_id"),
            }

        if context.get("task_id"):
            return {
                "target_type": "task",
                "target_id": context["task_id"],
                "target_label": context.get("task_name"),
                "task_id": context["task_id"],
                "related_task_id": None,
            }

        if context.get("hostname"):
            return {
                "target_type": "worker",
                "target_id": context["hostname"],
                "target_label": context["hostname"],
                "task_id": None,
                "related_task_id": None,
            }

        return {
            "target_type": "workflow",
            "target_id": workflow.id,
            "target_label": workflow.name,
            "task_id": None,
            "related_task_id": None,
        }

    @staticmethod
    def _summarize_action_result(result) -> str:
        if result.status == "success":
            return f"{result.action_type} completed"
        if result.status == "skipped":
            return f"{result.action_type} skipped"
        return f"{result.action_type} failed"

    @staticmethod
    def _summarize_workflow_result(action_results: list[Dict[str, Any]], overall_status: str) -> str:
        successful = len([item for item in action_results if item.get("status") == "success"])
        failed = len([item for item in action_results if item.get("status") == "failed"])
        if overall_status == "completed":
            return f"Workflow completed with {successful} successful action(s)"
        if failed:
            return f"Workflow failed after {failed} failed action(s)"
        return "Workflow failed"
