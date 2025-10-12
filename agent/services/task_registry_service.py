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

        Args:
            task_name: The task name to get stats for
            hours: Number of hours to look back (default: 24)
        """
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        # Get all events for this task in the time window
        query = self.session.query(TaskEventDB).filter(
            and_(
                TaskEventDB.task_name == task_name,
                TaskEventDB.timestamp >= since
            )
        )

        # Apply environment filtering
        query = self._apply_environment_filter(query)
        events = query.all()

        # Calculate stats
        total_executions = 0
        succeeded = 0
        failed = 0
        pending = 0
        retried = 0
        runtimes = []
        last_execution = None

        # Track unique task IDs to count executions
        task_ids = set()

        for event in events:
            task_ids.add(event.task_id)

            if event.event_type == 'task-succeeded':
                succeeded += 1
                if event.runtime:
                    runtimes.append(event.runtime)
            elif event.event_type == 'task-failed':
                failed += 1
            elif event.event_type == 'task-received':
                pending += 1
            elif event.event_type == 'task-retried':
                retried += 1

            # Track last execution
            if last_execution is None or event.timestamp > last_execution:
                last_execution = event.timestamp

        total_executions = len(task_ids)
        avg_runtime = sum(runtimes) / len(runtimes) if runtimes else None

        return TaskRegistryStats(
            task_name=task_name,
            total_executions=total_executions,
            succeeded=succeeded,
            failed=failed,
            pending=pending,
            retried=retried,
            avg_runtime=avg_runtime,
            last_execution=last_execution
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

        Args:
            task_name: The task name to get timeline for
            hours: Number of hours to look back (default: 24)
            bucket_size_minutes: Size of each time bucket in minutes (default: 60)

        Returns:
            Dict with timeline data including bucketed execution counts
        """
        from models import TaskTimelineResponse, TimelineBucket

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)

        # Get all events for this task in the time window
        query = self.session.query(TaskEventDB).filter(
            and_(
                TaskEventDB.task_name == task_name,
                TaskEventDB.timestamp >= start_time,
                TaskEventDB.timestamp <= end_time
            )
        ).order_by(TaskEventDB.timestamp)

        # Apply environment filtering
        query = self._apply_environment_filter(query)
        events = query.all()

        logger.info(f"Timeline for {task_name}: Found {len(events)} events in time window ({start_time} to {end_time})")

        # Create time buckets
        bucket_delta = timedelta(minutes=bucket_size_minutes)
        num_buckets = int((hours * 60) / bucket_size_minutes)

        # Initialize buckets
        buckets = []
        current_bucket_start = start_time

        for i in range(num_buckets):
            buckets.append({
                'timestamp': current_bucket_start,
                'total_executions': 0,
                'succeeded': 0,
                'failed': 0,
                'retried': 0,
                'task_ids': set()  # Track unique task IDs per bucket
            })
            current_bucket_start += bucket_delta

        # Assign events to buckets
        event_type_counts = {}
        bucketed_events = 0
        for event in events:
            # Track event types
            event_type_counts[event.event_type] = event_type_counts.get(event.event_type, 0) + 1

            # Normalize timestamp to UTC if naive (SQLite compatibility)
            event_ts = event.timestamp
            if event_ts.tzinfo is None:
                event_ts = event_ts.replace(tzinfo=timezone.utc)

            # Find which bucket this event belongs to
            time_diff = event_ts - start_time
            bucket_index = int(time_diff.total_seconds() / (bucket_size_minutes * 60))

            if 0 <= bucket_index < num_buckets:
                bucketed_events += 1
                bucket = buckets[bucket_index]

                # Count unique task executions (task-received events)
                if event.event_type == 'task-received':
                    bucket['task_ids'].add(event.task_id)
                    bucket['total_executions'] += 1

                # Count outcomes
                if event.event_type == 'task-succeeded':
                    bucket['succeeded'] += 1
                elif event.event_type == 'task-failed':
                    bucket['failed'] += 1
                elif event.event_type == 'task-retried':
                    bucket['retried'] += 1

        logger.info(f"Timeline for {task_name}: Event types: {event_type_counts}, Bucketed: {bucketed_events}/{len(events)}")

        # Convert to response format (remove task_ids set)
        timeline_buckets = [
            TimelineBucket(
                timestamp=bucket['timestamp'],
                total_executions=bucket['total_executions'],
                succeeded=bucket['succeeded'],
                failed=bucket['failed'],
                retried=bucket['retried']
            )
            for bucket in buckets
        ]

        # Log summary of buckets with data
        non_empty_buckets = [b for b in timeline_buckets if b.total_executions > 0]
        logger.info(f"Timeline for {task_name}: Returning {len(non_empty_buckets)}/{len(timeline_buckets)} non-empty buckets")

        return TaskTimelineResponse(
            task_name=task_name,
            start_time=start_time,
            end_time=end_time,
            bucket_size_minutes=bucket_size_minutes,
            buckets=timeline_buckets
        )
