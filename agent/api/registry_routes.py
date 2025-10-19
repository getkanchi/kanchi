"""API routes for task registry endpoints."""

from typing import List, Optional
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session

from services import TaskRegistryService, DailyStatsService, SessionService, EnvironmentService
from models import (
    TaskRegistryResponse,
    TaskRegistryUpdate,
    TaskRegistryStats,
    TaskDailyStatsResponse,
    TaskTimelineResponse
)


def create_router(app_state) -> APIRouter:
    """Create task registry router with dependency injection."""
    router = APIRouter(prefix="/api/registry", tags=["registry"])

    def get_db() -> Session:
        """FastAPI dependency for database sessions."""
        if not app_state.db_manager:
            raise HTTPException(status_code=500, detail="Database not initialized")
        with app_state.db_manager.get_session() as session:
            yield session

    async def get_active_env(
        session: Session = Depends(get_db),
        x_session_id: Optional[str] = Header(None)
    ):
        """Dependency to get active environment from session."""
        if not x_session_id:
            return None

        session_service = SessionService(session)
        env_id = session_service.get_active_environment_id(x_session_id)

        if not env_id:
            return None

        env_service = EnvironmentService(session)
        return env_service.get_environment(env_id)

    @router.get("/tasks", response_model=List[TaskRegistryResponse])
    async def list_tasks(
        tag: Optional[str] = None,
        name: Optional[str] = None,
        session: Session = Depends(get_db),
        active_env = Depends(get_active_env)
    ):
        """
        List all registered tasks with optional filters.

        Args:
            tag: Filter by tag (case-insensitive partial match)
            name: Filter by task name (case-insensitive partial match)
        """
        registry_service = TaskRegistryService(session, active_env=active_env)
        return registry_service.list_tasks(tag=tag, name_filter=name)

    @router.get("/tasks/{task_name}", response_model=TaskRegistryResponse)
    async def get_task(
        task_name: str,
        session: Session = Depends(get_db),
        active_env = Depends(get_active_env)
    ):
        """
        Get details about a specific task.

        Args:
            task_name: The name of the task to retrieve
        """
        registry_service = TaskRegistryService(session, active_env=active_env)
        task = registry_service.get_task(task_name)

        if not task:
            raise HTTPException(status_code=404, detail=f"Task '{task_name}' not found")

        return task

    @router.put("/tasks/{task_name}", response_model=TaskRegistryResponse)
    async def update_task(
        task_name: str,
        update_data: TaskRegistryUpdate,
        session: Session = Depends(get_db),
        active_env = Depends(get_active_env)
    ):
        """
        Update task metadata (human_readable_name, description, tags).

        Args:
            task_name: The name of the task to update
            update_data: The fields to update
        """
        registry_service = TaskRegistryService(session, active_env=active_env)
        updated_task = registry_service.update_task(task_name, update_data)

        if not updated_task:
            raise HTTPException(status_code=404, detail=f"Task '{task_name}' not found")

        return updated_task

    @router.get("/tasks/{task_name}/stats", response_model=TaskRegistryStats)
    async def get_task_stats(
        task_name: str,
        hours: int = 24,
        session: Session = Depends(get_db),
        active_env = Depends(get_active_env)
    ):
        """
        Get statistics for a specific task.

        Args:
            task_name: The name of the task
            hours: Number of hours to look back (default: 24)
        """
        registry_service = TaskRegistryService(session, active_env=active_env)

        # Verify task exists
        task = registry_service.get_task(task_name)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task '{task_name}' not found")

        return registry_service.get_task_stats(task_name, hours=hours)

    @router.get("/tasks/{task_name}/timeline", response_model=TaskTimelineResponse)
    async def get_task_timeline(
        task_name: str,
        hours: int = Query(24, description="Number of hours to look back"),
        bucket_size_minutes: int = Query(60, description="Bucket size in minutes (e.g., 60 for 1-hour buckets)"),
        session: Session = Depends(get_db),
        active_env = Depends(get_active_env)
    ):
        """
        Get execution timeline for visualizing task frequency over time.

        Args:
            task_name: The name of the task
            hours: Number of hours to look back (default: 24)
            bucket_size_minutes: Size of each time bucket in minutes (default: 60)
        """
        registry_service = TaskRegistryService(session, active_env=active_env)

        # Verify task exists
        task = registry_service.get_task(task_name)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task '{task_name}' not found")

        return registry_service.get_task_timeline(
            task_name,
            hours=hours,
            bucket_size_minutes=bucket_size_minutes
        )

    @router.get("/tags", response_model=List[str])
    async def get_all_tags(
        session: Session = Depends(get_db),
        active_env = Depends(get_active_env)
    ):
        """Get all unique tags across all tasks."""
        registry_service = TaskRegistryService(session, active_env=active_env)
        return registry_service.get_all_tags()

    @router.get("/tasks/{task_name}/daily-stats", response_model=List[TaskDailyStatsResponse])
    async def get_task_daily_stats(
        task_name: str,
        start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
        end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
        days: Optional[int] = Query(30, description="Number of days to look back (if no dates specified)"),
        session: Session = Depends(get_db),
        active_env = Depends(get_active_env)
    ):
        """
        Get daily statistics for a task.

        Args:
            task_name: The name of the task
            start_date: Optional start date
            end_date: Optional end date
            days: Number of days to look back (default: 30, used if no dates specified)
        """
        # Verify task exists
        registry_service = TaskRegistryService(session, active_env=active_env)
        task = registry_service.get_task(task_name)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task '{task_name}' not found")

        # If no dates specified, use last N days
        if not start_date and not end_date:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days - 1)

        daily_stats_service = DailyStatsService(session)
        return daily_stats_service.get_daily_stats(
            task_name,
            start_date=start_date,
            end_date=end_date,
            limit=days if days else 30
        )

    @router.get("/tasks/{task_name}/trend", response_model=dict)
    async def get_task_trend(
        task_name: str,
        days: int = Query(7, description="Number of days to analyze"),
        session: Session = Depends(get_db),
        active_env = Depends(get_active_env)
    ):
        """
        Get trend summary for a task over the last N days.

        Returns:
            Summary with success rates, failure rates, and average runtime
        """
        registry_service = TaskRegistryService(session, active_env=active_env)
        task = registry_service.get_task(task_name)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task '{task_name}' not found")

        daily_stats_service = DailyStatsService(session)
        return daily_stats_service.get_task_trend_summary(task_name, days=days)

    @router.get("/daily-stats/{target_date}", response_model=List[TaskDailyStatsResponse])
    async def get_all_tasks_stats_for_date(
        target_date: date,
        session: Session = Depends(get_db)
    ):
        """
        Get statistics for all tasks on a specific date.

        Args:
            target_date: The date to get stats for (YYYY-MM-DD)
        """
        daily_stats_service = DailyStatsService(session)
        return daily_stats_service.get_all_tasks_stats_for_date(target_date)

    return router
