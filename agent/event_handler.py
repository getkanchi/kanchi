"""Simplified event handling for Celery events."""

import logging
from datetime import datetime

from connection_manager import ConnectionManager
from database import DatabaseManager
from database import TaskEventDB
from models import TaskEvent, WorkerEvent
from services import StatsService, TaskService, WorkerService

logger = logging.getLogger(__name__)


class EventHandler:
    """Simple, synchronous event handler for Celery events."""

    def __init__(self, db_manager: DatabaseManager, connection_manager: ConnectionManager):
        self.db_manager = db_manager
        self.connection_manager = connection_manager

    def handle_task_event(self, task_event: TaskEvent):
        """Handle task event: save to DB and broadcast to WebSocket."""
        try:
            # Save to database
            with self.db_manager.get_session() as session:
                task_service = TaskService(session)
                stats_service = StatsService(session)

                task_service._enrich_task_with_retry_info(task_event)
                task_service.save_task_event(task_event)
                stats_service.update_stats(task_event.event_type)

            # Broadcast to WebSocket
            self.connection_manager.queue_broadcast(task_event)

        except Exception as e:
            logger.error(f"Error handling task event {task_event.task_id}: {e}", exc_info=True)

    def handle_worker_event(self, worker_event: WorkerEvent):
        """Handle worker event: save to DB and broadcast to WebSocket."""
        try:
            # Save to database
            with self.db_manager.get_session() as session:
                worker_service = WorkerService(session)
                worker_service.save_worker_event(worker_event)
                
                # If worker went offline, mark its running tasks as orphaned
                if worker_event.event_type == 'worker-offline':
                    logger.info(f"Worker {worker_event.hostname} went offline, marking tasks as orphaned")
                    self._mark_tasks_as_orphaned(session, worker_event.hostname, worker_event.timestamp or datetime.utcnow())

            # Broadcast to WebSocket
            self.connection_manager.queue_worker_broadcast(worker_event)

        except Exception as e:
            logger.error(f"Error handling worker event {worker_event.hostname}: {e}", exc_info=True)

    def _mark_tasks_as_orphaned(self, session, hostname: str, orphaned_at: datetime):
        """Mark all running tasks on a worker as orphaned."""
        try:
            # Find tasks that are currently running on this worker
            running_tasks = session.query(TaskEventDB).filter(
                TaskEventDB.hostname == hostname,
                TaskEventDB.event_type == 'task-started'
            ).all()
            
            orphaned_tasks = []
            
            # Check which tasks haven't been completed yet
            for task in running_tasks:
                # Check if this task has any completion events
                completed = session.query(TaskEventDB).filter(
                    TaskEventDB.task_id == task.task_id,
                    TaskEventDB.event_type.in_(['task-succeeded', 'task-failed', 'task-revoked'])
                ).first()
                
                if not completed:
                    # Mark as orphaned
                    session.query(TaskEventDB).filter(
                        TaskEventDB.task_id == task.task_id
                    ).update({
                        'is_orphan': True,
                        'orphaned_at': orphaned_at
                    })
                    orphaned_tasks.append(task)
            
            session.commit()
            
            # Broadcast orphan events via WebSocket
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
                logger.info(f"EventHandler broadcasting orphan event for task {task.task_id}")
                self.connection_manager.queue_broadcast(orphan_event)
            
            logger.info(f"Marked {len(orphaned_tasks)} tasks as orphaned for offline worker {hostname}")
            
        except Exception as e:
            logger.error(f"Error marking tasks as orphaned for worker {hostname}: {e}", exc_info=True)
            session.rollback()
