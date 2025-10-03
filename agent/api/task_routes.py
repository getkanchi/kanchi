"""API routes for task-related endpoints."""

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
        """Get tasks that have been marked as orphaned."""
        orphaned_events = session.query(TaskEventDB).filter(
            TaskEventDB.is_orphan == True
        ).order_by(TaskEventDB.orphaned_at.desc()).all()
        return [TaskEventResponse.from_task_event(event) for event in orphaned_events]


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
        
        # Get the latest event for the task
        original_task = task_events[-1]
        
        # Check if this is an orphaned task and mark it as no longer orphaned
        orphaned_task = session.query(TaskEventDB).filter_by(
            task_id=task_id,
            is_orphan=True
        ).first()
        
        if orphaned_task:
            # Mark all events for this task as no longer orphaned
            session.query(TaskEventDB).filter_by(task_id=task_id).update({
                'is_orphan': False,
                'orphaned_at': None
            })
            session.commit()
        
        try:
            # Parse args and kwargs
            import ast
            args = ast.literal_eval(original_task.args) if original_task.args and original_task.args != "()" else ()
            kwargs = ast.literal_eval(original_task.kwargs) if original_task.kwargs and original_task.kwargs != "{}" else {}
        except (ValueError, SyntaxError):
            args = ()
            kwargs = {}
        
        # Retry the task
        queue_name = original_task.routing_key if original_task.routing_key else 'default'
        
        result = app_state.monitor_instance.app.send_task(
            original_task.task_name,
            args=args,
            kwargs=kwargs,
            queue=queue_name
        )
        
        new_task_id = str(result.id)
        
        # Store retry relationship
        task_service.create_retry_relationship(task_id, new_task_id)
        
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