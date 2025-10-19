import logging
from datetime import datetime
from typing import List

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from database import TaskEventDB
from models import TaskEvent
from constants import NON_TERMINAL_EVENT_TYPES, EventType

logger = logging.getLogger(__name__)


class OrphanDetectionService:

    def __init__(self, session: Session):
        self.session = session

    def find_and_mark_orphaned_tasks(
        self,
        hostname: str,
        orphaned_at: datetime,
        grace_period_seconds: int = 2
    ) -> List[TaskEventDB]:
        latest_events_subquery = self._build_latest_events_subquery(hostname)
        orphaned_tasks = self._find_non_terminal_tasks(latest_events_subquery)

        if orphaned_tasks:
            self._mark_tasks_as_orphaned(orphaned_tasks, orphaned_at, grace_period_seconds)
        else:
            logger.info(f"No tasks to orphan for offline worker {hostname}")

        return orphaned_tasks

    def _build_latest_events_subquery(self, hostname: str):
        return self.session.query(
            TaskEventDB.task_id,
            func.max(TaskEventDB.timestamp).label('max_timestamp')
        ).filter(
            TaskEventDB.hostname == hostname
        ).group_by(TaskEventDB.task_id).subquery()

    def _find_non_terminal_tasks(self, latest_events_subquery) -> List[TaskEventDB]:
        non_terminal_values = [et.value for et in NON_TERMINAL_EVENT_TYPES]
        return self.session.query(TaskEventDB).join(
            latest_events_subquery,
            and_(
                TaskEventDB.task_id == latest_events_subquery.c.task_id,
                TaskEventDB.timestamp == latest_events_subquery.c.max_timestamp,
                TaskEventDB.event_type.in_(non_terminal_values),
                TaskEventDB.is_orphan.is_(False)
            )
        ).all()

    def _mark_tasks_as_orphaned(
        self,
        orphaned_tasks: List[TaskEventDB],
        orphaned_at: datetime,
        grace_period_seconds: int
    ):
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
        Create orphan event objects from orphaned tasks.

        Args:
            orphaned_tasks: List of orphaned task database objects
            orphaned_at: Timestamp when tasks were orphaned

        Returns:
            List of TaskEvent objects for orphaned tasks
        """
        orphan_events = []

        for task in orphaned_tasks:
            orphan_event = TaskEvent(
                task_id=task.task_id,
                task_name=task.task_name,
                event_type=EventType.TASK_ORPHANED.value,
                hostname=task.hostname,
                timestamp=orphaned_at,
                routing_key=task.routing_key,
                args=task.args,
                kwargs=task.kwargs
            )
            orphan_events.append(orphan_event)

        return orphan_events

    def broadcast_orphan_events(
        self,
        orphaned_tasks: List[TaskEventDB],
        orphaned_at: datetime,
        connection_manager
    ):
        """
        Create and broadcast orphan events to WebSocket clients.

        Args:
            orphaned_tasks: List of orphaned task database objects
            orphaned_at: Timestamp when tasks were orphaned
            connection_manager: ConnectionManager instance for broadcasting
        """
        orphan_events = self.create_orphan_events(orphaned_tasks, orphaned_at)

        for orphan_event in orphan_events:
            logger.info(f"Broadcasting orphan event for task {orphan_event.task_id}")
            connection_manager.queue_broadcast(orphan_event)
