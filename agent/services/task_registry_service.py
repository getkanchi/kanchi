"""Task registry service for auto-discovery and management of Celery tasks."""

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from database import TaskRegistryDB, TaskEventDB
from models import TaskRegistryResponse, TaskRegistryUpdate, TaskRegistryStats

logger = logging.getLogger(__name__)


class TaskRegistryService:
    """Service for managing task registry with in-memory cache."""

    # Class-level in-memory cache (shared across all instances)
    _cache: set = set()
    _cache_initialized: bool = False

    def __init__(self, session: Session):
        self.session = session

        # Initialize cache on first instantiation
        if not TaskRegistryService._cache_initialized:
            self._load_cache()
            TaskRegistryService._cache_initialized = True

    def _load_cache(self):
        """Load all task names into in-memory cache on startup."""
        try:
            task_names = self.session.query(TaskRegistryDB.name).all()
            TaskRegistryService._cache = {name[0] for name in task_names}
            logger.info(f"Task registry cache initialized with {len(TaskRegistryService._cache)} tasks")
        except Exception as e:
            logger.error(f"Error loading task registry cache: {e}", exc_info=True)
            TaskRegistryService._cache = set()

    def ensure_task_registered(self, task_name: str) -> TaskRegistryDB:
        """
        Ensure task is registered. Auto-discover if not found.

        Uses in-memory cache for fast lookups. Only hits DB on cache miss.
        """
        # Fast path: check in-memory cache
        if task_name in TaskRegistryService._cache:
            # Update last_seen timestamp
            self._update_last_seen(task_name)
            return None  # No need to return the full object for performance

        # Slow path: not in cache, check DB
        existing_task = self.session.query(TaskRegistryDB).filter(
            TaskRegistryDB.name == task_name
        ).first()

        if existing_task:
            # Found in DB but not in cache - add to cache
            TaskRegistryService._cache.add(task_name)
            self._update_last_seen(task_name)
            logger.info(f"Task '{task_name}' found in DB, added to cache")
            return existing_task

        # Not in DB - auto-register
        new_task = self._register_new_task(task_name)
        TaskRegistryService._cache.add(task_name)
        logger.info(f"Auto-discovered new task: '{task_name}'")
        return new_task

    def _register_new_task(self, task_name: str) -> TaskRegistryDB:
        """Register a new task in the database."""
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

    def _update_last_seen(self, task_name: str):
        """Update last_seen timestamp for a task."""
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

    def _apply_environment_filter(self, query):
        """
        Apply environment filtering to a TaskEventDB query.

        Args:
            query: SQLAlchemy query on TaskEventDB

        Returns:
            Filtered query
        """
        # Import here to avoid circular dependency
        from services.environment_service import EnvironmentService

        env_service = EnvironmentService(self.session)
        active_env = env_service.get_active_environment()

        # No active environment = no filtering
        if not active_env:
            return query

        # Build filter conditions
        filter_conditions = []

        # Filter by queue patterns
        if active_env.queue_patterns:
            queue_conditions = []
            for pattern in active_env.queue_patterns:
                # Convert wildcard pattern to SQL LIKE pattern
                like_pattern = pattern.replace('*', '%').replace('?', '_')
                queue_conditions.append(TaskEventDB.queue.like(like_pattern))
            if queue_conditions:
                filter_conditions.append(or_(*queue_conditions))

        # Filter by worker patterns
        if active_env.worker_patterns:
            worker_conditions = []
            for pattern in active_env.worker_patterns:
                # Convert wildcard pattern to SQL LIKE pattern
                like_pattern = pattern.replace('*', '%').replace('?', '_')
                worker_conditions.append(TaskEventDB.hostname.like(like_pattern))
            if worker_conditions:
                filter_conditions.append(or_(*worker_conditions))

        # Apply filters (OR logic: match queue OR worker pattern)
        if filter_conditions:
            query = query.filter(or_(*filter_conditions))

        return query

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
        """
        query = self.session.query(TaskRegistryDB)

        # Apply filters
        if name_filter:
            query = query.filter(TaskRegistryDB.name.ilike(f'%{name_filter}%'))

        if tag:
            # JSON array contains check
            # For SQLite: use JSON_EXTRACT or simple string matching
            # This approach works for both SQLite and PostgreSQL
            from sqlalchemy import cast, String
            query = query.filter(cast(TaskRegistryDB.tags, String).contains(f'"{tag}"'))

        tasks = query.order_by(TaskRegistryDB.last_seen.desc()).all()
        return [TaskRegistryResponse.model_validate(task) for task in tasks]

    def get_task(self, task_name: str) -> Optional[TaskRegistryResponse]:
        """Get a specific task by name."""
        task = self.session.query(TaskRegistryDB).filter(
            TaskRegistryDB.name == task_name
        ).first()

        if task:
            return TaskRegistryResponse.model_validate(task)
        return None

    def update_task(self, task_name: str, update_data: TaskRegistryUpdate) -> Optional[TaskRegistryResponse]:
        """
        Update task metadata (human_readable_name, description, tags).

        Returns updated task or None if not found.
        """
        task = self.session.query(TaskRegistryDB).filter(
            TaskRegistryDB.name == task_name
        ).first()

        if not task:
            return None

        # Update fields if provided
        if update_data.human_readable_name is not None:
            task.human_readable_name = update_data.human_readable_name

        if update_data.description is not None:
            task.description = update_data.description

        if update_data.tags is not None:
            task.tags = update_data.tags

        task.updated_at = datetime.now(timezone.utc)

        self.session.commit()
        return TaskRegistryResponse.model_validate(task)

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
        """
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        # Build base query with filters
        base_query = self.session.query(TaskEventDB).filter(
            and_(
                TaskEventDB.task_name == task_name,
                TaskEventDB.timestamp >= since
            )
        )

        # Apply environment filtering
        base_query = self._apply_environment_filter(base_query)

        # Use database aggregation to calculate stats in a single query
        # This is much faster than fetching all rows and processing in Python
        from sqlalchemy import case

        stats_query = base_query.with_entities(
            func.count(func.distinct(TaskEventDB.task_id)).label('total_executions'),
            func.sum(case((TaskEventDB.event_type == 'task-succeeded', 1), else_=0)).label('succeeded'),
            func.sum(case((TaskEventDB.event_type == 'task-failed', 1), else_=0)).label('failed'),
            func.sum(case((TaskEventDB.event_type == 'task-received', 1), else_=0)).label('pending'),
            func.sum(case((TaskEventDB.event_type == 'task-retried', 1), else_=0)).label('retried'),
            func.avg(case((TaskEventDB.runtime.isnot(None), TaskEventDB.runtime), else_=None)).label('avg_runtime'),
            func.max(TaskEventDB.timestamp).label('last_execution')
        )

        result = stats_query.one()

        return TaskRegistryStats(
            task_name=task_name,
            total_executions=result.total_executions or 0,
            succeeded=result.succeeded or 0,
            failed=result.failed or 0,
            pending=result.pending or 0,
            retried=result.retried or 0,
            avg_runtime=float(result.avg_runtime) if result.avg_runtime else None,
            last_execution=result.last_execution
        )

    def get_all_tags(self) -> List[str]:
        """Get all unique tags across all tasks."""
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
    ):
        """
        Get execution timeline with time buckets for visualizing task frequency.
        Uses database aggregation for optimal performance.

        Args:
            task_name: The task name to get timeline for
            hours: Number of hours to look back (default: 24)
            bucket_size_minutes: Size of each time bucket in minutes (default: 60)

        Returns:
            Dict with timeline data including bucketed execution counts
        """
        from models import TaskTimelineResponse, TimelineBucket
        from sqlalchemy import cast, Integer, literal

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)
        bucket_seconds = bucket_size_minutes * 60
        num_buckets = int((hours * 60) / bucket_size_minutes)

        # Build base query with filters
        base_query = self.session.query(TaskEventDB).filter(
            and_(
                TaskEventDB.task_name == task_name,
                TaskEventDB.timestamp >= start_time,
                TaskEventDB.timestamp <= end_time
            )
        )

        # Apply environment filtering
        base_query = self._apply_environment_filter(base_query)

        # Calculate bucket index for each event in the database
        # SQLite: Use strftime to get Unix timestamp, then calculate bucket
        # PostgreSQL: Use extract(epoch from timestamp)

        # For SQLite compatibility, we use a simpler approach:
        # Cast timestamp difference to seconds and divide by bucket size
        base_query_cte = base_query.add_columns(
            # Calculate seconds from start_time
            cast(
                (func.julianday(TaskEventDB.timestamp) - func.julianday(literal(start_time))) * 86400,
                Integer
            ).label('seconds_from_start')
        ).subquery()

        # Now aggregate by bucket
        from sqlalchemy import case as sql_case

        bucket_query = self.session.query(
            # Calculate bucket index
            cast(base_query_cte.c.seconds_from_start / bucket_seconds, Integer).label('bucket_index'),
            # Count unique task_ids for task-received events
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
        ).group_by('bucket_index').all()

        # Create a mapping of bucket_index to stats
        bucket_stats = {
            result.bucket_index: {
                'total_executions': result.total_executions or 0,
                'succeeded': result.succeeded or 0,
                'failed': result.failed or 0,
                'retried': result.retried or 0
            }
            for result in bucket_query
        }

        # Initialize all buckets (including empty ones)
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
        logger.info(f"Timeline for {task_name}: Returning {len(non_empty_buckets)}/{len(timeline_buckets)} non-empty buckets")

        return TaskTimelineResponse(
            task_name=task_name,
            start_time=start_time,
            end_time=end_time,
            bucket_size_minutes=bucket_size_minutes,
            buckets=timeline_buckets
        )
