"""Workflow executor for running workflow actions."""

import logging
import traceback
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from models import TaskEvent, WorkerEvent, WorkflowDefinition
from services.workflow_service import WorkflowService
from services.action_executor import ActionExecutor

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
        event: TaskEvent | WorkerEvent
    ):
        """Execute a workflow's actions."""
        workflow_service = WorkflowService(self.session)

        # Create execution record
        execution_id = workflow_service.record_workflow_execution_start(
            workflow_id=workflow.id,
            trigger_type=workflow.trigger.type,
            trigger_event=context,
            workflow_snapshot=workflow.dict()
        )

        logger.info(f"Started workflow execution: {workflow.name} (execution_id={execution_id})")

        action_results = []
        overall_status = "completed"
        error_message = None
        stack_trace = None

        try:
            # Execute actions in order
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

                # Execute action
                result = await action_executor.execute(
                    action_type=action_config.type,
                    context=context,
                    params=action_config.params
                )

                # Store result
                action_results.append({
                    "action_type": result.action_type,
                    "status": result.status,
                    "result": result.result,
                    "error_message": result.error_message,
                    "duration_ms": result.duration_ms
                })

                # Handle failure
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

            # Update workflow stats
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
            # Update execution record
            workflow_service.update_workflow_execution(
                execution_id=execution_id,
                status=overall_status,
                actions_executed=action_results,
                error_message=error_message,
                stack_trace=stack_trace
            )
