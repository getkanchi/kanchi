"""Service for managing daily task statistics."""

import logging
from datetime import datetime, timezone, date
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import TaskDailyStatsDB
from models import TaskEvent, TaskDailyStatsResponse

logger = logging.getLogger(__name__)


class DailyStatsService:
    """Service for aggregating and managing daily task statistics."""

    def __init__(self, session: Session):
        self.session = session

    def update_daily_stats(self, task_event: TaskEvent):
        """
        Update daily statistics for a task based on incoming event.

        This is called in real-time as events arrive.
        """
        # Get the date for this event (UTC)
        event_date = task_event.timestamp.date()
        task_name = task_event.task_name

        # Get or create daily stats record
        stats = self.session.query(TaskDailyStatsDB).filter(
            TaskDailyStatsDB.task_name == task_name,
            TaskDailyStatsDB.date == event_date
        ).first()

        if not stats:
            stats = TaskDailyStatsDB(
                task_name=task_name,
                date=event_date,
                total_executions=0,
                succeeded=0,
                failed=0,
                pending=0,
                retried=0,
                revoked=0,
                orphaned=0,
                first_execution=task_event.timestamp,
                last_execution=task_event.timestamp
            )
            self.session.add(stats)

        # Update counters based on event type
        event_type = task_event.event_type

        if event_type == 'task-received':
            # New execution starting
            stats.total_executions += 1
            stats.pending += 1
        elif event_type == 'task-succeeded':
            stats.succeeded += 1
            # Decrement pending if it was counted
            if stats.pending > 0:
                stats.pending -= 1
        elif event_type == 'task-failed':
            stats.failed += 1
            if stats.pending > 0:
                stats.pending -= 1
        elif event_type == 'task-retried':
            stats.retried += 1
        elif event_type == 'task-revoked':
            stats.revoked += 1
            if stats.pending > 0:
                stats.pending -= 1

        # Handle orphaned tasks
        if task_event.is_orphan:
            stats.orphaned += 1

        # Update runtime statistics
        if task_event.runtime is not None:
            self._update_runtime_stats(stats, task_event.runtime)

        # Update timestamps (ensure timezone-aware comparison)
        event_ts = task_event.timestamp
        if event_ts.tzinfo is None:
            event_ts = event_ts.replace(tzinfo=timezone.utc)

        if stats.first_execution is None:
            stats.first_execution = event_ts
        else:
            # Ensure DB timestamp is timezone-aware
            first_exec = stats.first_execution
            if first_exec.tzinfo is None:
                first_exec = first_exec.replace(tzinfo=timezone.utc)
            if event_ts < first_exec:
                stats.first_execution = event_ts

        if stats.last_execution is None:
            stats.last_execution = event_ts
        else:
            # Ensure DB timestamp is timezone-aware
            last_exec = stats.last_execution
            if last_exec.tzinfo is None:
                last_exec = last_exec.replace(tzinfo=timezone.utc)
            if event_ts > last_exec:
                stats.last_execution = event_ts

        stats.updated_at = datetime.now(timezone.utc)

        try:
            self.session.commit()
        except Exception as e:
            logger.error(f"Error updating daily stats for {task_name} on {event_date}: {e}")
            self.session.rollback()
            raise

    def _update_runtime_stats(self, stats: TaskDailyStatsDB, runtime: float):
        """
        Update runtime statistics (avg, min, max, percentiles).

        For percentiles, we use a simple approximation since we don't store
        all individual runtimes. For accurate percentiles, you'd need to
        query the raw task_events table.
        """
        # Update min/max
        if stats.min_runtime is None or runtime < stats.min_runtime:
            stats.min_runtime = runtime
        if stats.max_runtime is None or runtime > stats.max_runtime:
            stats.max_runtime = runtime

        # Update average (incremental)
        # New average = (old_avg * old_count + new_value) / (old_count + 1)
        if stats.avg_runtime is None:
            stats.avg_runtime = runtime
        else:
            # Estimate count from succeeded tasks
            count = stats.succeeded
            if count > 0:
                stats.avg_runtime = ((stats.avg_runtime * count) + runtime) / (count + 1)
            else:
                stats.avg_runtime = runtime

    def get_daily_stats(
        self,
        task_name: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 30
    ) -> List[TaskDailyStatsResponse]:
        """
        Get daily statistics for a task within a date range.

        Args:
            task_name: The task to get stats for
            start_date: Optional start date (inclusive)
            end_date: Optional end date (inclusive)
            limit: Maximum number of days to return (default: 30)
        """
        query = self.session.query(TaskDailyStatsDB).filter(
            TaskDailyStatsDB.task_name == task_name
        )

        if start_date:
            query = query.filter(TaskDailyStatsDB.date >= start_date)
        if end_date:
            query = query.filter(TaskDailyStatsDB.date <= end_date)

        stats = query.order_by(TaskDailyStatsDB.date.desc()).limit(limit).all()
        return [TaskDailyStatsResponse.model_validate(s) for s in stats]

    def get_stats_for_date(
        self,
        task_name: str,
        target_date: date
    ) -> Optional[TaskDailyStatsResponse]:
        """Get statistics for a specific task on a specific date."""
        stats = self.session.query(TaskDailyStatsDB).filter(
            TaskDailyStatsDB.task_name == task_name,
            TaskDailyStatsDB.date == target_date
        ).first()

        if stats:
            return TaskDailyStatsResponse.model_validate(stats)
        return None

    def get_all_tasks_stats_for_date(
        self,
        target_date: date
    ) -> List[TaskDailyStatsResponse]:
        """Get statistics for all tasks on a specific date."""
        stats = self.session.query(TaskDailyStatsDB).filter(
            TaskDailyStatsDB.date == target_date
        ).order_by(TaskDailyStatsDB.total_executions.desc()).all()

        return [TaskDailyStatsResponse.model_validate(s) for s in stats]

    def get_task_trend_summary(
        self,
        task_name: str,
        days: int = 7
    ) -> dict:
        """
        Get a summary of trends for a task over the last N days.

        Returns metrics like:
        - Total executions
        - Success rate
        - Failure rate
        - Average runtime trend
        """
        from datetime import timedelta
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=days - 1)

        stats = self.get_daily_stats(task_name, start_date, end_date, limit=days)

        if not stats:
            return {
                'task_name': task_name,
                'days': days,
                'total_executions': 0,
                'avg_success_rate': 0,
                'avg_failure_rate': 0,
                'avg_runtime': None
            }

        total_executions = sum(s.total_executions for s in stats)
        total_succeeded = sum(s.succeeded for s in stats)
        total_failed = sum(s.failed for s in stats)

        # Calculate average runtime across days
        runtimes = [s.avg_runtime for s in stats if s.avg_runtime is not None]
        avg_runtime = sum(runtimes) / len(runtimes) if runtimes else None

        success_rate = (total_succeeded / total_executions * 100) if total_executions > 0 else 0
        failure_rate = (total_failed / total_executions * 100) if total_executions > 0 else 0

        return {
            'task_name': task_name,
            'days': days,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_executions': total_executions,
            'total_succeeded': total_succeeded,
            'total_failed': total_failed,
            'avg_success_rate': round(success_rate, 2),
            'avg_failure_rate': round(failure_rate, 2),
            'avg_runtime': avg_runtime
        }
