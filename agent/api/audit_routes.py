"""API routes for audit log queries."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from config import Config
from models import AuditLogListResponse
from security.dependencies import get_auth_dependency
from services.audit_service import AuditLogService


def create_router(app_state) -> APIRouter:
    """Create audit router with dependency injection."""
    router = APIRouter(prefix="/api", tags=["audit"])

    config = app_state.config or Config.from_env()
    require_user_dep = get_auth_dependency(app_state, require=True)

    if config.auth_enabled:
        router.dependencies.append(Depends(require_user_dep))

    def get_db() -> Session:
        if not app_state.db_manager:
            raise HTTPException(status_code=500, detail="Database not initialized")
        with app_state.db_manager.get_session() as session:
            yield session

    @router.get("/audit-logs", response_model=AuditLogListResponse)
    async def list_audit_logs(
        limit: int = Query(default=100, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
        search: Optional[str] = None,
        source: Optional[str] = None,
        status: Optional[str] = None,
        action_type: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        task_id: Optional[str] = None,
        actor: Optional[str] = None,
        session: Session = Depends(get_db),
    ):
        """Search and filter audit log entries."""
        service = AuditLogService(session)
        return service.list_entries(
            limit=limit,
            offset=offset,
            search=search,
            source=source,
            status=status,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            workflow_id=workflow_id,
            task_id=task_id,
            actor=actor,
        )

    @router.get("/tasks/{task_id}/audit", response_model=AuditLogListResponse)
    async def get_task_audit_logs(
        task_id: str,
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
        session: Session = Depends(get_db),
    ):
        """Get audit entries related to a task."""
        return AuditLogService(session).get_task_entries(task_id, limit=limit, offset=offset)

    @router.get("/workflows/{workflow_id}/audit", response_model=AuditLogListResponse)
    async def get_workflow_audit_logs(
        workflow_id: str,
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
        session: Session = Depends(get_db),
    ):
        """Get audit entries related to a workflow."""
        return AuditLogService(session).get_workflow_entries(
            workflow_id,
            limit=limit,
            offset=offset,
        )

    return router
