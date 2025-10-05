"""API routes for task-related endpoints."""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from services import TaskService, StatsService
from database import TaskEventDB
from models import TaskEventResponse, TaskStats


def create_router(app_state) -> APIRouter:
    """Create task router with dependency injection."""
    router = APIRouter(prefix="/api", tags=["tasks"])

    def get_db() -> Session:
        """FastAPI dependency for database sessions."""
        if not app_state.db_manager:
            raise HTTPException(status_code=500, detail="Database not initialized")
        with app_state.db_manager.get_session() as session:
            yield session


    @router.get("/stats", response_model=TaskStats)
    async def get_task_stats(session: Session = Depends(get_db)):
        """Get current task statistics."""
        stats_service = StatsService(session)
        return stats_service.get_stats()


    @router.get("/events/recent", response_model=Dict[str, Any])
    async def get_recent_events(
        limit: int = 100,
        page: int = 0,
        aggregate: bool = True,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
        search: Optional[str] = None,
        filter_state: Optional[str] = None,
        filter_worker: Optional[str] = None,
        filter_task: Optional[str] = None,
        filter_queue: Optional[str] = None,
        session: Session = Depends(get_db)
    ):
        """Get recent task events with filtering and pagination."""
        task_service = TaskService(session)
        
        return task_service.get_recent_events(
            limit=limit,
            page=page,
            aggregate=aggregate,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            filter_state=filter_state,
            filter_worker=filter_worker,
            filter_task=filter_task,
            filter_queue=filter_queue
        )


    @router.get("/events/{task_id}", response_model=List[TaskEventResponse])
    async def get_task_events(task_id: str, session: Session = Depends(get_db)):
        """Get all events for a specific task."""
        task_service = TaskService(session)
        task_events = task_service.get_task_events(task_id)
        
        if not task_events:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return [TaskEventResponse.from_task_event(event) for event in task_events]


    @router.get("/tasks/active", response_model=List[TaskEventResponse])
    async def get_active_tasks(session: Session = Depends(get_db)):
        """Get currently active tasks."""
        task_service = TaskService(session)
        active_events = task_service.get_active_tasks()
        return [TaskEventResponse.from_task_event(event) for event in active_events]


    @router.get("/tasks/orphaned", response_model=List[TaskEventResponse])
    async def get_orphaned_tasks(session: Session = Depends(get_db)):
        """Get tasks that have been marked as orphaned and NOT yet retried."""
        from sqlalchemy import func, and_
        from database import RetryRelationshipDB

        latest_orphaned_subquery = session.query(
            TaskEventDB.task_id,
            func.max(TaskEventDB.timestamp).label('max_timestamp')
        ).filter(
            TaskEventDB.is_orphan == True
        ).group_by(TaskEventDB.task_id).subquery()

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

        unretried_orphaned = []
        for event in orphaned_events:
            retry_rel = session.query(RetryRelationshipDB).filter_by(task_id=event.task_id).first()
            if not retry_rel or not retry_rel.retry_chain or len(retry_rel.retry_chain) == 0:
                unretried_orphaned.append(event)

        return [TaskEventResponse.from_task_event(event) for event in unretried_orphaned]


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
        
        try:
            import ast
            args = ast.literal_eval(original_task.args) if original_task.args and original_task.args != "()" else ()
            kwargs = ast.literal_eval(original_task.kwargs) if original_task.kwargs and original_task.kwargs != "{}" else {}
        except (ValueError, SyntaxError):
            args = ()
            kwargs = {}

        queue_name = original_task.routing_key if original_task.routing_key else 'default'

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
            "timestamp": datetime.now().isoformat()
        }

    return router
