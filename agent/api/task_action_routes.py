"""Internal UI routes for persisted task actions."""

# ruff: noqa: B008

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from config import Config
from models import (
    RerunPreflightRequest,
    RerunPreflightResponse,
    RerunSubmitRequest,
    TaskActionCreateRequest,
    TaskActionDetail,
    TaskActionListResponse,
    TaskActionType,
)
from security.auth import AuthenticatedUser
from security.dependencies import get_auth_dependency
from services import EnvironmentService, SessionService
from services.task_action_service import TaskActionService, TaskActionValidationError

logger = logging.getLogger(__name__)


def create_router(app_state) -> APIRouter:
    """Create internal task action router with dependency injection."""
    router = APIRouter(prefix="/api", tags=["task-actions"])

    config = app_state.config or Config.from_env()
    optional_user_dep = get_auth_dependency(app_state, require=False)
    require_user_dep = get_auth_dependency(app_state, require=True)

    if config.auth_enabled:
        router.dependencies.append(Depends(require_user_dep))

    def get_db() -> Session:
        if not app_state.db_manager:
            raise HTTPException(status_code=500, detail="Database not initialized")
        with app_state.db_manager.get_session() as session:
            yield session

    async def get_active_env(
        session: Session = Depends(get_db),
        x_session_id: Optional[str] = Header(None),
        current_user: Optional[AuthenticatedUser] = Depends(optional_user_dep),
    ):
        if not x_session_id:
            return None
        session_service = SessionService(session)
        user_id = current_user.id if isinstance(current_user, AuthenticatedUser) else None
        try:
            env_id = session_service.get_active_environment_id(x_session_id, user_id=user_id)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        if not env_id:
            return None
        return EnvironmentService(session).get_environment(env_id)

    def build_service(session: Session, active_env=None) -> TaskActionService:
        return TaskActionService(
            session,
            monitor_instance=app_state.monitor_instance,
            connection_manager=app_state.connection_manager,
            max_selection_size=config.task_action_max_selection,
            active_env=active_env,
        )

    def actor(current_user: Optional[AuthenticatedUser]) -> Dict[str, Optional[str]]:
        if isinstance(current_user, AuthenticatedUser):
            return {
                "initiated_by_user_id": current_user.id,
                "initiated_by": current_user.email or current_user.name or "anonymous",
            }
        return {"initiated_by_user_id": None, "initiated_by": "anonymous"}

    @router.post(
        "/task-actions/rerun/preflight",
        response_model=RerunPreflightResponse,
        include_in_schema=False,
    )
    async def preflight_rerun_review(
        payload: RerunPreflightRequest,
        session: Session = Depends(get_db),
        active_env=Depends(get_active_env),
    ):
        service = build_service(session, active_env)
        try:
            return service.preflight_rerun(payload.task_ids)
        except TaskActionValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @router.post(
        "/task-actions/preflight",
        response_model=RerunPreflightResponse,
        include_in_schema=False,
    )
    async def preflight_task_action(
        payload: RerunPreflightRequest,
        session: Session = Depends(get_db),
        active_env=Depends(get_active_env),
    ):
        service = build_service(session, active_env)
        try:
            return service.preflight_rerun(payload.task_ids)
        except TaskActionValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @router.post(
        "/task-actions/rerun",
        response_model=TaskActionDetail,
        include_in_schema=False,
    )
    async def submit_rerun_review(
        payload: RerunSubmitRequest,
        session: Session = Depends(get_db),
        x_session_id: Optional[str] = Header(None),
        current_user: Optional[AuthenticatedUser] = Depends(optional_user_dep),
        active_env=Depends(get_active_env),
    ):
        service = build_service(session, active_env)
        try:
            return service.submit_rerun_review(
                items=payload.items,
                initiated_session_id=x_session_id,
                **actor(current_user),
            )
        except TaskActionValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @router.post(
        "/task-actions",
        response_model=TaskActionDetail,
        include_in_schema=False,
    )
    async def create_task_action(
        payload: TaskActionCreateRequest,
        session: Session = Depends(get_db),
        x_session_id: Optional[str] = Header(None),
        current_user: Optional[AuthenticatedUser] = Depends(optional_user_dep),
        active_env=Depends(get_active_env),
    ):
        service = build_service(session, active_env)
        try:
            return service.create_action(
                action_type=payload.action_type,
                task_ids=payload.task_ids,
                initiated_session_id=x_session_id,
                **actor(current_user),
            )
        except TaskActionValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @router.get(
        "/task-actions",
        response_model=TaskActionListResponse,
        include_in_schema=False,
    )
    async def list_task_actions(
        limit: int = Query(default=20, ge=1, le=100),
        session: Session = Depends(get_db),
        active_env=Depends(get_active_env),
    ):
        service = build_service(session, active_env)
        return TaskActionListResponse(
            data=service.list_actions(limit=limit),
            max_selection_size=config.task_action_max_selection,
        )

    @router.get(
        "/task-actions/config",
        response_model=Dict[str, Any],
        include_in_schema=False,
    )
    async def get_task_action_config():
        return {"max_selection_size": config.task_action_max_selection}

    @router.get(
        "/task-actions/{action_id}",
        response_model=TaskActionDetail,
        include_in_schema=False,
    )
    async def get_task_action(
        action_id: str,
        session: Session = Depends(get_db),
        active_env=Depends(get_active_env),
    ):
        service = build_service(session, active_env)
        try:
            return service.get_action(action_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Task action not found") from exc

    @router.post(
        "/tasks/{task_id}/rerun/preflight",
        response_model=RerunPreflightResponse,
        include_in_schema=False,
    )
    async def preflight_single_rerun(
        task_id: str,
        session: Session = Depends(get_db),
        active_env=Depends(get_active_env),
    ):
        service = build_service(session, active_env)
        return service.preflight_rerun([task_id])

    @router.post(
        "/tasks/{task_id}/rerun",
        response_model=TaskActionDetail,
        include_in_schema=False,
    )
    async def rerun_single_task(
        task_id: str,
        session: Session = Depends(get_db),
        x_session_id: Optional[str] = Header(None),
        current_user: Optional[AuthenticatedUser] = Depends(optional_user_dep),
        active_env=Depends(get_active_env),
    ):
        service = build_service(session, active_env)
        try:
            return service.create_action(
                action_type=TaskActionType.RERUN,
                task_ids=[task_id],
                initiated_session_id=x_session_id,
                **actor(current_user),
            )
        except TaskActionValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    return router
