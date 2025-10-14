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


def create_router(app_state) -> APIRouter:
    """Create workflow router with dependency injection."""
    router = APIRouter(prefix="/api/workflows", tags=["workflows"])

    def get_db() -> Session:
        """FastAPI dependency for database sessions."""
        if not app_state.db_manager:
            raise HTTPException(status_code=500, detail="Database not initialized")
        with app_state.db_manager.get_session() as session:
            yield session

    # ==================== Workflow CRUD ====================

    @router.post("", response_model=WorkflowDefinition, status_code=201)
    async def create_workflow(
        workflow_data: WorkflowCreateRequest,
        session: Session = Depends(get_db)
    ):
        """Create a new workflow."""
        workflow_service = WorkflowService(session)
        workflow = workflow_service.create_workflow(workflow_data)
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
        session: Session = Depends(get_db)
    ):
        """Update an existing workflow."""
        workflow_service = WorkflowService(session)
        workflow = workflow_service.update_workflow(workflow_id, updates)

        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        return workflow

    @router.delete("/{workflow_id}", status_code=204)
    async def delete_workflow(
        workflow_id: str,
        session: Session = Depends(get_db)
    ):
        """Delete a workflow."""
        workflow_service = WorkflowService(session)
        success = workflow_service.delete_workflow(workflow_id)

        if not success:
            raise HTTPException(status_code=404, detail="Workflow not found")

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
