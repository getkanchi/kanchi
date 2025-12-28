"""API routes for task-related endpoints."""

import logging
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from services import TaskService, EnvironmentService, SessionService, AppConfigService, ProgressService
from database import TaskEventDB
from models import TaskEvent, TaskProgressSnapshot
from database import ensure_utc_isoformat
from config import Config
from security.auth import AuthenticatedUser
from security.dependencies import get_auth_dependency

logger = logging.getLogger(__name__)


class ResolveTaskRequest(BaseModel):
    resolved_by: Optional[str] = None


def create_router(app_state) -> APIRouter:
    """Create task router with dependency injection."""
    router = APIRouter(prefix="/api", tags=["tasks"])

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

    async def get_active_env(
        session: Session = Depends(get_db),
        x_session_id: Optional[str] = Header(None),
        current_user: Optional[AuthenticatedUser] = Depends(optional_user_dep)
    ):
        """Dependency to get active environment from session."""
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

        env_service = EnvironmentService(session)
        return env_service.get_environment(env_id)


    @router.get("/events/recent", response_model=Dict[str, Any])
    async def get_recent_events(
        limit: int = 100,
        page: int = 0,
        aggregate: bool = True,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
        search: Optional[str] = None,
        filters: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        filter_state: Optional[str] = None,
        filter_worker: Optional[str] = None,
        filter_task: Optional[str] = None,
        filter_queue: Optional[str] = None,
        session: Session = Depends(get_db),
        active_env = Depends(get_active_env)
    ):
        """Get recent task events with filtering and pagination."""
        logger.info(f"API /events/recent called with session env={active_env.name if active_env else 'None'}")

        task_service = TaskService(session, active_env=active_env)
        return task_service.get_recent_events(
            limit=limit,
            page=page,
            aggregate=aggregate,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filters=filters,
            start_time=start_time,
            end_time=end_time,
            filter_state=filter_state,
            filter_worker=filter_worker,
            filter_task=filter_task,
            filter_queue=filter_queue
        )


    @router.get("/events/{task_id}", response_model=List[TaskEvent])
    async def get_task_events(task_id: str, session: Session = Depends(get_db)):
        """Get all events for a specific task."""
        task_service = TaskService(session)
        task_events = task_service.get_task_events(task_id)

        if not task_events:
            raise HTTPException(status_code=404, detail="Task not found")

        return task_events

    @router.get("/tasks/{task_id}/progress", response_model=TaskProgressSnapshot)
    async def get_task_progress(task_id: str, session: Session = Depends(get_db)):
        """Get latest progress, steps, and recent history for a task."""
        progress_service = ProgressService(session)
        latest = progress_service.get_latest_progress(task_id)
        steps = progress_service.get_steps(task_id)
        history = progress_service.get_progress_history(task_id)

        return TaskProgressSnapshot(
            task_id=task_id,
            latest=latest,
            steps=steps,
            history=history,
        )


    @router.get("/tasks/active", response_model=List[TaskEvent])
    async def get_active_tasks(
        session: Session = Depends(get_db),
        active_env = Depends(get_active_env)
    ):
        """Get currently active tasks."""
        task_service = TaskService(session, active_env=active_env)
        active_events = task_service.get_active_tasks()
        return active_events


    @router.get("/tasks/orphaned", response_model=List[TaskEvent])
    async def get_orphaned_tasks(
        session: Session = Depends(get_db),
        active_env = Depends(get_active_env)
    ):
        """Get tasks that have been marked as orphaned and NOT yet retried."""
        from sqlalchemy import func, and_, or_
        from database import RetryRelationshipDB

        FINAL_STATES = {'task-succeeded', 'task-failed', 'task-revoked', 'task-rejected', 'task-retried'}

        latest_orphaned_subquery = session.query(
            TaskEventDB.task_id,
            func.max(TaskEventDB.timestamp).label('max_timestamp')
        ).filter(
            TaskEventDB.is_orphan == True
        )

        if active_env:
            env_conditions = []

            if active_env.queue_patterns:
                queue_conditions = []
                for pattern in active_env.queue_patterns:
                    sql_pattern = pattern.replace('*', '%').replace('?', '_')
                    queue_conditions.append(TaskEventDB.queue.like(sql_pattern))
                if queue_conditions:
                    env_conditions.append(or_(*queue_conditions))

            if active_env.worker_patterns:
                worker_conditions = []
                for pattern in active_env.worker_patterns:
                    sql_pattern = pattern.replace('*', '%').replace('?', '_')
                    worker_conditions.append(TaskEventDB.hostname.like(sql_pattern))
                if worker_conditions:
                    env_conditions.append(or_(*worker_conditions))

            if env_conditions:
                latest_orphaned_subquery = latest_orphaned_subquery.filter(or_(*env_conditions))

        latest_orphaned_subquery = latest_orphaned_subquery.group_by(TaskEventDB.task_id).subquery()

        orphaned_events_db = session.query(TaskEventDB).join(
            latest_orphaned_subquery,
            and_(
                TaskEventDB.task_id == latest_orphaned_subquery.c.task_id,
                TaskEventDB.timestamp == latest_orphaned_subquery.c.max_timestamp
            )
        ).order_by(TaskEventDB.orphaned_at.desc()).all()

        task_service = TaskService(session)
        orphaned_events = [task_service._db_to_task_event(event_db) for event_db in orphaned_events_db]
        task_service._bulk_enrich_with_retry_info(orphaned_events)
        task_service._attach_resolution_info(orphaned_events)

        unretried_orphaned = []
        for event in orphaned_events:
            # Check if task has been retried
            retry_rel = session.query(RetryRelationshipDB).filter_by(task_id=event.task_id).first()
            if retry_rel and retry_rel.retry_chain and len(retry_rel.retry_chain) > 0:
                continue

            # Check if task has any final state events
            has_final_state = session.query(TaskEventDB).filter(
                TaskEventDB.task_id == event.task_id,
                TaskEventDB.event_type.in_(FINAL_STATES)
            ).first() is not None

            if not has_final_state:
                unretried_orphaned.append(event)

        return unretried_orphaned

    @router.get("/tasks/failed/recent", response_model=List[TaskEvent])
    async def get_recent_failed_tasks(
        hours: Optional[int] = Query(
            default=None,
            ge=1,
            le=168,
            description="Lookback window in hours (defaults to configured value)"
        ),
        limit: int = 50,
        include_retried: bool = False,
        session: Session = Depends(get_db),
        active_env = Depends(get_active_env)
    ):
        """Get failed tasks within the last ``hours`` window."""
        task_service = TaskService(session, active_env=active_env)
        config_service = AppConfigService(session)
        lookback_hours = hours if hours is not None else config_service.get_task_issue_lookback_hours()
        failed_tasks = task_service.get_recent_failed_tasks(
            hours=lookback_hours,
            limit=limit,
            exclude_retried=not include_retried
        )
        return failed_tasks


    @router.post("/tasks/{task_id}/resolve")
    async def resolve_task(
        task_id: str,
        payload: Optional[ResolveTaskRequest] = None,
        session: Session = Depends(get_db),
        current_user: Optional[AuthenticatedUser] = Depends(optional_user_dep)
    ):
        """Manually mark a task as resolved without altering its state."""
        task_service = TaskService(session)
        task_events = task_service.get_task_events(task_id)
        if not task_events:
            raise HTTPException(status_code=404, detail="Task not found")

        resolved_by = payload.resolved_by if payload else None
        if config.auth_enabled and isinstance(current_user, AuthenticatedUser):
            resolved_by = resolved_by or current_user.email or current_user.name

        resolution = task_service.set_task_resolution(task_id, resolved_by)
        return {
            "task_id": task_id,
            "resolved": True,
            "resolved_by": resolution.resolved_by,
            "resolved_at": ensure_utc_isoformat(resolution.resolved_at) if resolution.resolved_at else None,
        }


    @router.delete("/tasks/{task_id}/resolve")
    async def clear_task_resolution(
        task_id: str,
        session: Session = Depends(get_db),
    ):
        """Remove manual resolution mark from a task."""
        task_service = TaskService(session)
        task_events = task_service.get_task_events(task_id)
        if not task_events:
            raise HTTPException(status_code=404, detail="Task not found")

        task_service.clear_task_resolution(task_id)
        return {
            "task_id": task_id,
            "resolved": False,
            "resolved_by": None,
            "resolved_at": None,
        }


    @router.post("/tasks/{task_id}/retry")
    async def retry_task(task_id: str, session: Session = Depends(get_db)):
        """Retry a failed task by creating a new task with the same parameters."""
        if not app_state.monitor_instance:
            raise HTTPException(status_code=500, detail="Monitor not initialized")

        task_service = TaskService(session)

        # Find the original task
        task_events = task_service.get_task_events(task_id)
        if not task_events:
            raise HTTPException(status_code=404, detail="Task not found")

        original_task = task_events[-1]

        orphaned_task = session.query(TaskEventDB).filter_by(
            task_id=task_id,
            is_orphan=True
        ).first()

        args = tuple(original_task.args) if original_task.args else ()
        kwargs = original_task.kwargs if original_task.kwargs else {}

        queue_name = original_task.queue if original_task.queue else 'default'

        new_task_id = str(uuid.uuid4())

        task_service.create_retry_relationship(task_id, new_task_id)
        session.commit()

        result = app_state.monitor_instance.app.send_task(
            original_task.task_name,
            args=args,
            kwargs=kwargs,
            queue=queue_name,
            task_id=new_task_id  # Use our pre-generated ID
        )
        
        return {
            "status": "success",
            "message": "Task retried successfully",
            "original_task_id": task_id,
            "new_task_id": new_task_id,
            "task_name": original_task.task_name,
            "was_orphaned": orphaned_task is not None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    return router
