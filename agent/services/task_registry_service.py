"""Task registry service for auto-discovery and management of Celery tasks."""

import logging
import uuid
import threading
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, cast, String, case

from database import TaskRegistryDB, TaskEventDB, RetryRelationshipDB
from models import (
    TaskRegistryResponse,
    TaskRegistryUpdate,
    TaskRegistryStats,
    TaskTimelineResponse,
    TimelineBucket
)
from services.utils import EnvironmentFilter

logger = logging.getLogger(__name__)


class TaskRegistryService:
    """Service for managing task registry with thread-safe in-memory cache."""

    _cache: set = set()
    _cache_initialized: bool = False
    _cache_lock = threading.Lock()

    def __init__(self, session: Session, active_env=None):
        self.session = session
        self.active_env = active_env

        with TaskRegistryService._cache_lock:
            if not TaskRegistryService._cache_initialized:
                self._load_cache()
                TaskRegistryService._cache_initialized = True

    def _load_cache(self):
        """
        Load all task names into in-memory cache on startup.

        Note: This method should only be called while holding _cache_lock.
        """
        try:
            task_names = self.session.query(TaskRegistryDB.name).all()
            TaskRegistryService._cache = {name[0] for name in task_names}
            logger.info(
                f"Task registry cache initialized with {len(TaskRegistryService._cache)} tasks"
            )
        except Exception as e:
            logger.error(f"Error loading task registry cache: {e}", exc_info=True)
            TaskRegistryService._cache = set()

    def ensure_task_registered(self, task_name: str) -> TaskRegistryDB:
        """
        Ensure task is registered. Auto-discover if not found.

        Uses in-memory cache for fast lookups. Only hits DB on cache miss.

        Args:
            task_name: Name of task to register

        Returns:
            TaskRegistryDB object if newly registered or found in DB, None if found in cache

        Note: Returns None for cache hits to avoid unnecessary DB queries.
        Callers should not rely on the return value for logic, only for logging.
        """
        if task_name in TaskRegistryService._cache:
            try:
                self._update_last_seen(task_name)
            except Exception as e:
                logger.warning(f"Failed to update last_seen for {task_name}: {e}")
            return None

        existing_task = (
            self.session.query(TaskRegistryDB)
            .filter(TaskRegistryDB.name == task_name)
            .first()
        )

        if existing_task:
            with TaskRegistryService._cache_lock:
                TaskRegistryService._cache.add(task_name)
            self._update_last_seen(task_name)
            logger.info(f"Task '{task_name}' found in DB, added to cache")
            return existing_task

        new_task = self._register_new_task(task_name)
        with TaskRegistryService._cache_lock:
            TaskRegistryService._cache.add(task_name)
        logger.info(f"Auto-discovered new task: '{task_name}'")
        return new_task

    def list_tasks(
        self,
        tag: Optional[str] = None,
        name_filter: Optional[str] = None
    ) -> List[TaskRegistryResponse]:
        """
        List all registered tasks with optional filters.

        Args:
            tag: Filter by tag (case-insensitive partial match)
            name_filter: Filter by task name (case-insensitive partial match)

        Returns:
            List of task registry responses ordered by last_seen descending
        """
        query = self.session.query(TaskRegistryDB)

        if name_filter:
            query = query.filter(TaskRegistryDB.name.ilike(f'%{name_filter}%'))

        if tag:
            query = query.filter(cast(TaskRegistryDB.tags, String).contains(f'"{tag}"'))

        tasks = query.order_by(TaskRegistryDB.last_seen.desc()).all()
        return [TaskRegistryResponse.model_validate(task) for task in tasks]

    def get_task(self, task_name: str) -> Optional[TaskRegistryResponse]:
        """
        Get a specific task by name.

        Args:
            task_name: Name of task to retrieve

        Returns:
            TaskRegistryResponse or None if not found
        """
        task = (
            self.session.query(TaskRegistryDB)
            .filter(TaskRegistryDB.name == task_name)
            .first()
        )

        if task:
            return TaskRegistryResponse.model_validate(task)
        return None

    def update_task(
        self,
        task_name: str,
        update_data: TaskRegistryUpdate
    ) -> Optional[TaskRegistryResponse]:
        """
        Update task metadata (human_readable_name, description, tags).

        Args:
            task_name: Name of task to update
            update_data: Update data containing fields to change

        Returns:
            Updated task or None if not found

        Raises:
            Exception: If database operation fails
        """
        try:
            task = (
                self.session.query(TaskRegistryDB)
                .filter(TaskRegistryDB.name == task_name)
                .first()
            )

            if not task:
                return None

            if update_data.human_readable_name is not None:
                task.human_readable_name = update_data.human_readable_name

            if update_data.description is not None:
                task.description = update_data.description

            if update_data.tags is not None:
                task.tags = update_data.tags

            task.updated_at = datetime.now(timezone.utc)

            self.session.commit()
            return TaskRegistryResponse.model_validate(task)

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to update task {task_name}: {e}")
            raise

    def get_task_stats(
        self,
        task_name: str,
        hours: int = 24
    ) -> TaskRegistryStats:
        """
        Get statistics for a specific task over the last N hours.
        Uses database aggregation for optimal performance.

        Args:
            task_name: The task name to get stats for
            hours: Number of hours to look back (default: 24)

        Returns:
            TaskRegistryStats object with execution statistics
        """
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        base_query = self.session.query(TaskEventDB).filter(
            and_(
                TaskEventDB.task_name == task_name,
                TaskEventDB.timestamp >= since
            )
        )

        base_query = EnvironmentFilter.apply(base_query, self.active_env)

        stats_query = base_query.with_entities(
            func.count(func.distinct(TaskEventDB.task_id)).label('total_executions'),
            func.sum(
                case((TaskEventDB.event_type == 'task-succeeded', 1), else_=0)
            ).label('succeeded'),
            func.sum(
                case((TaskEventDB.event_type == 'task-received', 1), else_=0)
            ).label('pending'),
            func.sum(
                case((TaskEventDB.event_type == 'task-retried', 1), else_=0)
            ).label('retried'),
            func.avg(
                case((TaskEventDB.runtime.isnot(None), TaskEventDB.runtime), else_=None)
            ).label('avg_runtime'),
            func.max(TaskEventDB.timestamp).label('last_execution')
        )

        result = stats_query.one()

        failed_task_ids = (
            base_query
            .filter(TaskEventDB.event_type == 'task-failed')
            .with_entities(TaskEventDB.task_id)
            .distinct()
            .all()
        )
        failed_task_ids = {row[0] for row in failed_task_ids}

        if not failed_task_ids:
            unretried_failures = 0
        else:
            retry_relationships = (
                self.session.query(RetryRelationshipDB)
                .filter(RetryRelationshipDB.task_id.in_(failed_task_ids))
                .all()
            )

            retried_task_ids = {
                rel.task_id for rel in retry_relationships if rel.total_retries > 0
            }

            unretried_failures = len(failed_task_ids - retried_task_ids)

        return TaskRegistryStats(
            task_name=task_name,
            total_executions=result.total_executions or 0,
            succeeded=result.succeeded or 0,
            failed=unretried_failures,
            pending=result.pending or 0,
            retried=result.retried or 0,
            avg_runtime=float(result.avg_runtime) if result.avg_runtime else None,
            last_execution=result.last_execution
        )

    def get_all_tags(self) -> List[str]:
        """
        Get all unique tags across all tasks.

        Returns:
            Sorted list of unique tags
        """
        tasks = self.session.query(TaskRegistryDB.tags).all()
        all_tags = set()

        for (tags,) in tasks:
            if tags:
                all_tags.update(tags)

        return sorted(list(all_tags))

    def get_task_timeline(
        self,
        task_name: str,
        hours: int = 24,
        bucket_size_minutes: int = 60
    ) -> TaskTimelineResponse:
        """
        Get execution timeline with time buckets for visualizing task frequency.
        Uses database aggregation for optimal performance.

        Args:
            task_name: The task name to get timeline for
            hours: Number of hours to look back (default: 24)
            bucket_size_minutes: Size of each time bucket in minutes (default: 60)

        Returns:
            TaskTimelineResponse with bucketed execution counts
        """
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)
        bucket_seconds = bucket_size_minutes * 60
        num_buckets = int((hours * 60) / bucket_size_minutes)

        base_query = self.session.query(TaskEventDB).filter(
            and_(
                TaskEventDB.task_name == task_name,
                TaskEventDB.timestamp >= start_time,
                TaskEventDB.timestamp <= end_time
            )
        )

        base_query = EnvironmentFilter.apply(base_query, self.active_env)

        from sqlalchemy import cast, Integer, literal

        base_query_cte = base_query.add_columns(
            cast(
                (func.julianday(TaskEventDB.timestamp) - func.julianday(literal(start_time))) * 86400,
                Integer
            ).label('seconds_from_start')
        ).subquery()

        from sqlalchemy import case as sql_case

        bucket_query = (
            self.session.query(
                cast(base_query_cte.c.seconds_from_start / bucket_seconds, Integer).label('bucket_index'),
                func.sum(
                    sql_case(
                        (base_query_cte.c.event_type == 'task-received', 1),
                        else_=0
                    )
                ).label('total_executions'),
                func.sum(
                    sql_case(
                        (base_query_cte.c.event_type == 'task-succeeded', 1),
                        else_=0
                    )
                ).label('succeeded'),
                func.sum(
                    sql_case(
                        (base_query_cte.c.event_type == 'task-failed', 1),
                        else_=0
                    )
                ).label('failed'),
                func.sum(
                    sql_case(
                        (base_query_cte.c.event_type == 'task-retried', 1),
                        else_=0
                    )
                ).label('retried')
            )
            .group_by('bucket_index')
            .all()
        )

        bucket_stats = {
            result.bucket_index: {
                'total_executions': result.total_executions or 0,
                'succeeded': result.succeeded or 0,
                'failed': result.failed or 0,
                'retried': result.retried or 0
            }
            for result in bucket_query
        }

        timeline_buckets = []
        current_bucket_start = start_time
        bucket_delta = timedelta(minutes=bucket_size_minutes)

        for i in range(num_buckets):
            stats = bucket_stats.get(i, {
                'total_executions': 0,
                'succeeded': 0,
                'failed': 0,
                'retried': 0
            })

            timeline_buckets.append(
                TimelineBucket(
                    timestamp=current_bucket_start,
                    total_executions=stats['total_executions'],
                    succeeded=stats['succeeded'],
                    failed=stats['failed'],
                    retried=stats['retried']
                )
            )
            current_bucket_start += bucket_delta

        non_empty_buckets = [b for b in timeline_buckets if b.total_executions > 0]
        logger.info(
            f"Timeline for {task_name}: "
            f"Returning {len(non_empty_buckets)}/{len(timeline_buckets)} non-empty buckets"
        )

        return TaskTimelineResponse(
            task_name=task_name,
            start_time=start_time,
            end_time=end_time,
            bucket_size_minutes=bucket_size_minutes,
            buckets=timeline_buckets
        )

    def _register_new_task(self, task_name: str) -> TaskRegistryDB:
        """
        Register a new task in the database.

        Args:
            task_name: Name of task to register

        Returns:
            Newly created TaskRegistryDB object

        Raises:
            Exception: If database operation fails
        """
        try:
            now = datetime.now(timezone.utc)
            new_task = TaskRegistryDB(
                id=str(uuid.uuid4()),
                name=task_name,
                created_at=now,
                updated_at=now,
                first_seen=now,
                last_seen=now,
                tags=[]
            )
            self.session.add(new_task)
            self.session.commit()
            return new_task

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to register new task {task_name}: {e}")
            raise

    def _update_last_seen(self, task_name: str):
        """
        Update last_seen timestamp for a task.

        Args:
            task_name: Name of task to update

        Note: Failures are logged but not raised to avoid breaking the main flow.
        """
        try:
            self.session.query(TaskRegistryDB).filter(
                TaskRegistryDB.name == task_name
            ).update({
                'last_seen': datetime.now(timezone.utc)
            })
            self.session.commit()
        except Exception as e:
            logger.error(f"Error updating last_seen for task '{task_name}': {e}")
            self.session.rollback()
