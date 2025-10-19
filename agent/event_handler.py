import logging
from datetime import datetime, timezone

from connection_manager import ConnectionManager
from database import DatabaseManager
from models import TaskEvent, WorkerEvent
from constants import EventType
from services import (
    OrphanDetectionService,
    TaskService,
    WorkerService,
    TaskRegistryService,
    DailyStatsService
)

logger = logging.getLogger(__name__)


class EventHandler:
    def __init__(self, db_manager: DatabaseManager, connection_manager: ConnectionManager, workflow_engine=None):
        self.db_manager = db_manager
        self.connection_manager = connection_manager
        self.workflow_engine = workflow_engine

    def handle_task_event(self, task_event: TaskEvent):
        try:
            with self.db_manager.get_session() as session:
                registry_service = TaskRegistryService(session)
                registry_service.ensure_task_registered(task_event.task_name)

                task_service = TaskService(session)
                daily_stats_service = DailyStatsService(session)

                task_service._enrich_task_with_retry_info(task_event)
                task_service.save_task_event(task_event)
                daily_stats_service.update_daily_stats(task_event)

            self.connection_manager.queue_broadcast(task_event)

            if self.workflow_engine:
                self.workflow_engine.process_event(task_event)

        except Exception as e:
            logger.error(f"Error handling task event {task_event.task_id}: {e}", exc_info=True)

    def handle_worker_event(self, worker_event: WorkerEvent):
        try:
            with self.db_manager.get_session() as session:
                if worker_event.event_type == EventType.WORKER_OFFLINE.value:
                    logger.info(f"Worker {worker_event.hostname} went offline, marking tasks as orphaned")
                    orphaned_at = datetime.now(timezone.utc)
                    self._mark_tasks_as_orphaned(session, worker_event.hostname, orphaned_at)

            self.connection_manager.queue_worker_broadcast(worker_event)

            if self.workflow_engine:
                self.workflow_engine.process_event(worker_event)

        except Exception as e:
            logger.error(f"Error handling worker event {worker_event.hostname}: {e}", exc_info=True)

    def _mark_tasks_as_orphaned(
        self,
        session,
        hostname: str,
        orphaned_at: datetime,
        grace_period_seconds: int = 2
    ):
        try:
            import time

            if grace_period_seconds > 0:
                time.sleep(grace_period_seconds)

            orphan_service = OrphanDetectionService(session)
            orphaned_tasks = orphan_service.find_and_mark_orphaned_tasks(
                hostname=hostname,
                orphaned_at=orphaned_at,
                grace_period_seconds=grace_period_seconds
            )

            if orphaned_tasks:
                orphan_service.broadcast_orphan_events(
                    orphaned_tasks, orphaned_at, self.connection_manager
                )

        except Exception as e:
            logger.error(f"Error marking tasks as orphaned for worker {hostname}: {e}", exc_info=True)
            session.rollback()
