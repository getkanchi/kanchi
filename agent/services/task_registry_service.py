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
        events = self.session.query(TaskEventDB).filter(
            and_(
                TaskEventDB.task_name == task_name,
                TaskEventDB.timestamp >= since
            )
        ).all()

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
