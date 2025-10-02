"""Simplified event handling for Celery events."""

import logging

from connection_manager import ConnectionManager
from database import DatabaseManager
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

            # Broadcast to WebSocket
            self.connection_manager.queue_worker_broadcast(worker_event)

        except Exception as e:
            logger.error(f"Error handling worker event {worker_event.hostname}: {e}", exc_info=True)
