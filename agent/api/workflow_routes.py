"""API routes for workflow management."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import (
    WorkflowDefinition,
    WorkflowCreateRequest,
    WorkflowUpdateRequest,
    WorkflowExecutionRecord
)
from services.workflow_service import WorkflowService
from services.action_executor import ActionExecutor
from services.workflow_catalog import TRIGGER_METADATA
from services.audit_service import AuditLogService, get_actor_for_user
from config import Config
from security.auth import AuthenticatedUser
from security.dependencies import get_auth_dependency


def create_router(app_state) -> APIRouter:
    """Create workflow router with dependency injection."""
    router = APIRouter(prefix="/api/workflows", tags=["workflows"])

    config = app_state.config or Config.from_env()
    require_user_dep = get_auth_dependency(app_state, require=True)
    optional_user_dep = get_auth_dependency(app_state, require=False)

    if config.auth_enabled:
        router.dependencies.append(Depends(require_user_dep))

    def get_db() -> Session:
        """FastAPI dependency for database sessions."""
        if not app_state.db_manager:
            raise HTTPException(status_code=500, detail="Database not initialized")
        with app_state.db_manager.get_session() as session:
            yield session

    @router.get("/metadata")
    async def get_workflow_metadata():
        """Expose supported triggers and actions."""
        return {
            "triggers": TRIGGER_METADATA,
            "actions": ActionExecutor.get_action_catalog()
        }

    # ==================== Workflow CRUD ====================

    @router.post("", response_model=WorkflowDefinition, status_code=201)
    async def create_workflow(
        workflow_data: WorkflowCreateRequest,
        session: Session = Depends(get_db),
        current_user: Optional[AuthenticatedUser] = Depends(optional_user_dep),
    ):
        """Create a new workflow."""
        workflow_service = WorkflowService(session)
        try:
            workflow = workflow_service.create_workflow(workflow_data)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        AuditLogService(session).record_safe_entry(
            source="manual",
            action_type="workflow.created",
            status="success",
            target_type="workflow",
            target_id=workflow.id or "",
            target_label=workflow.name,
            workflow_id=workflow.id,
            result_summary="Workflow created",
            details={
                "trigger_type": workflow.trigger.type,
                "action_types": [action.type for action in workflow.actions],
            },
            **get_actor_for_user(current_user),
        )
        return workflow

    @router.get("", response_model=List[WorkflowDefinition])
    async def list_workflows(
        enabled_only: bool = False,
        trigger_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        session: Session = Depends(get_db)
    ):
        """List all workflows with optional filtering."""
        workflow_service = WorkflowService(session)
        workflows = workflow_service.list_workflows(
            enabled_only=enabled_only,
            trigger_type=trigger_type,
            limit=limit,
            offset=offset
        )
        return workflows

    @router.get("/{workflow_id}", response_model=WorkflowDefinition)
    async def get_workflow(
        workflow_id: str,
        session: Session = Depends(get_db)
    ):
        """Get a specific workflow by ID."""
        workflow_service = WorkflowService(session)
        workflow = workflow_service.get_workflow(workflow_id)

        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        return workflow

    @router.put("/{workflow_id}", response_model=WorkflowDefinition)
    async def update_workflow(
        workflow_id: str,
        updates: WorkflowUpdateRequest,
        session: Session = Depends(get_db),
        current_user: Optional[AuthenticatedUser] = Depends(optional_user_dep),
    ):
        """Update an existing workflow."""
        workflow_service = WorkflowService(session)
        try:
            workflow = workflow_service.update_workflow(workflow_id, updates)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        AuditLogService(session).record_safe_entry(
            source="manual",
            action_type="workflow.updated",
            status="success",
            target_type="workflow",
            target_id=workflow_id,
            target_label=workflow.name,
            workflow_id=workflow_id,
            result_summary="Workflow updated",
            details=updates.model_dump(exclude_unset=True),
            **get_actor_for_user(current_user),
        )
        return workflow

    @router.delete("/{workflow_id}", status_code=204)
    async def delete_workflow(
        workflow_id: str,
        session: Session = Depends(get_db),
        current_user: Optional[AuthenticatedUser] = Depends(optional_user_dep),
    ):
        """Delete a workflow."""
        workflow_service = WorkflowService(session)
        existing = workflow_service.get_workflow(workflow_id)
        success = workflow_service.delete_workflow(workflow_id)

        if not success:
            raise HTTPException(status_code=404, detail="Workflow not found")

        AuditLogService(session).record_safe_entry(
            source="manual",
            action_type="workflow.deleted",
            status="success",
            target_type="workflow",
            target_id=workflow_id,
            target_label=existing.name if existing else None,
            workflow_id=workflow_id,
            result_summary="Workflow deleted",
            details={},
            **get_actor_for_user(current_user),
        )

    # ==================== Workflow Executions ====================

    @router.get("/{workflow_id}/executions", response_model=List[WorkflowExecutionRecord])
    async def get_workflow_executions(
        workflow_id: str,
        limit: int = 100,
        offset: int = 0,
        session: Session = Depends(get_db)
    ):
        """Get execution history for a workflow."""
        workflow_service = WorkflowService(session)

        # Verify workflow exists
        workflow = workflow_service.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        executions = workflow_service.get_workflow_executions(
            workflow_id=workflow_id,
            limit=limit,
            offset=offset
        )

        return executions

    @router.get("/executions/recent", response_model=List[WorkflowExecutionRecord])
    async def get_recent_executions(
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        session: Session = Depends(get_db)
    ):
        """Get recent workflow executions across all workflows."""
        workflow_service = WorkflowService(session)
        executions = workflow_service.get_workflow_executions(
            status=status,
            limit=limit,
            offset=offset
        )
        return executions

    # ==================== Workflow Testing ====================

    @router.post("/{workflow_id}/test")
    async def test_workflow(
        workflow_id: str,
        test_context: dict,
        session: Session = Depends(get_db)
    ):
        """
        Test a workflow with sample data.

        This simulates workflow execution without actually triggering actions.
        Useful for debugging condition evaluation.
        """
        from services.workflow_engine import WorkflowEngine

        workflow_service = WorkflowService(session)
        workflow = workflow_service.get_workflow(workflow_id)

        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        # Create workflow engine instance
        engine = WorkflowEngine(
            db_manager=app_state.db_manager,
            monitor_instance=app_state.monitor_instance
        )

        # Evaluate conditions
        conditions_met = engine._evaluate_conditions(workflow, test_context)

        return {
            "workflow_id": workflow_id,
            "workflow_name": workflow.name,
            "test_context": test_context,
            "conditions_met": conditions_met,
            "would_execute": conditions_met,
            "actions": [action.type for action in workflow.actions]
        }

    return router
