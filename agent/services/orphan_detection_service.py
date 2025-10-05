"""Orphan detection service for identifying and marking orphaned tasks."""

import logging
from datetime import datetime
from typing import List

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from database import TaskEventDB
from models import TaskEvent

logger = logging.getLogger(__name__)

# Non-terminal event types that indicate a task is still running
NON_TERMINAL_EVENTS = ['task-started', 'task-received', 'task-sent']


class OrphanDetectionService:
    """
    Service for detecting and marking orphaned tasks.

    Orphaned tasks are tasks that were running on a worker when it went offline
    and never completed. This service uses database-level aggregation to accurately
    identify such tasks by checking their latest event state.
    """

    def __init__(self, session: Session):
        self.session = session

    def find_and_mark_orphaned_tasks(
        self,
        hostname: str,
        orphaned_at: datetime,
        grace_period_seconds: int = 2
    ) -> List[TaskEventDB]:
        """
        Find and mark all orphaned tasks for a specific worker.

        This method uses database-level aggregation to find the latest event for each
        task on the specified worker. Tasks whose latest event is non-terminal (still
        running) are marked as orphaned.

        Note: The caller should wait for the grace period before calling this method
        to allow any late-arriving completion events to be processed.

        Args:
            hostname: Worker hostname that went offline
            orphaned_at: Timestamp when worker went offline
            grace_period_seconds: Grace period duration (for logging only, caller should wait)

        Returns:
            List of orphaned task events (latest event for each orphaned task)
        """
        # Build subquery to find latest event timestamp per task
        latest_events_subquery = self._build_latest_events_subquery(hostname)

        # Find tasks with non-terminal latest event
        orphaned_tasks = self._find_non_terminal_tasks(latest_events_subquery)

        # Mark all events for orphaned tasks
        if orphaned_tasks:
            self._mark_tasks_as_orphaned(orphaned_tasks, orphaned_at, grace_period_seconds)
        else:
            logger.info(f"No tasks to orphan for offline worker {hostname}")

        return orphaned_tasks

    def _build_latest_events_subquery(self, hostname: str):
        """Build subquery to find latest event timestamp per task for a worker."""
        return self.session.query(
            TaskEventDB.task_id,
            func.max(TaskEventDB.timestamp).label('max_timestamp')
        ).filter(
            TaskEventDB.hostname == hostname
        ).group_by(TaskEventDB.task_id).subquery()

    def _find_non_terminal_tasks(self, latest_events_subquery) -> List[TaskEventDB]:
        """Find tasks where latest event is non-terminal (still running)."""
        return self.session.query(TaskEventDB).join(
            latest_events_subquery,
            and_(
                TaskEventDB.task_id == latest_events_subquery.c.task_id,
                TaskEventDB.timestamp == latest_events_subquery.c.max_timestamp,
                TaskEventDB.event_type.in_(NON_TERMINAL_EVENTS),
                TaskEventDB.is_orphan.is_(False)  # Don't re-orphan
            )
        ).all()

    def _mark_tasks_as_orphaned(
        self,
        orphaned_tasks: List[TaskEventDB],
        orphaned_at: datetime,
        grace_period_seconds: int
    ):
        """Mark all events for orphaned tasks in the database."""
        task_ids = [task.task_id for task in orphaned_tasks]

        self.session.query(TaskEventDB).filter(
            TaskEventDB.task_id.in_(task_ids)
        ).update({
            'is_orphan': True,
            'orphaned_at': orphaned_at
        }, synchronize_session=False)

        self.session.commit()

        logger.info(
            f"Marked {len(orphaned_tasks)} tasks as orphaned for offline worker "
            f"(grace period: {grace_period_seconds}s)"
        )

    def create_orphan_events(
        self,
        orphaned_tasks: List[TaskEventDB],
        orphaned_at: datetime
    ) -> List[TaskEvent]:
        """
        Create orphan events for broadcasting via WebSocket.

        Args:
            orphaned_tasks: List of orphaned task database records
            orphaned_at: Timestamp when tasks were orphaned

        Returns:
            List of TaskEvent objects for broadcasting
        """
        orphan_events = []

        for task in orphaned_tasks:
            orphan_event = TaskEvent(
                task_id=task.task_id,
                task_name=task.task_name,
                event_type='task-orphaned',
                hostname=task.hostname,
                timestamp=orphaned_at,
                routing_key=task.routing_key,
                args=task.args,
                kwargs=task.kwargs
            )
            orphan_events.append(orphan_event)

        return orphan_events
