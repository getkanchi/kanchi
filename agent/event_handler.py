"""Simplified event handling for Celery events."""

import logging
from datetime import datetime, timezone

from connection_manager import ConnectionManager
from database import DatabaseManager
from models import TaskEvent, WorkerEvent
from services import (
    OrphanDetectionService,
    TaskService,
    WorkerService,
    TaskRegistryService,
    DailyStatsService
)

logger = logging.getLogger(__name__)


class EventHandler:
    """Simple, synchronous event handler for Celery events."""

    def __init__(self, db_manager: DatabaseManager, connection_manager: ConnectionManager, workflow_engine=None):
        self.db_manager = db_manager
        self.connection_manager = connection_manager
        self.workflow_engine = workflow_engine

    def handle_task_event(self, task_event: TaskEvent):
        """Handle task event: save to DB and broadcast to WebSocket."""
        try:
            with self.db_manager.get_session() as session:
                # Ensure task is registered (auto-discovery)
                registry_service = TaskRegistryService(session)
                registry_service.ensure_task_registered(task_event.task_name)

                task_service = TaskService(session)
                daily_stats_service = DailyStatsService(session)

                task_service._enrich_task_with_retry_info(task_event)
                if task_event.retry_of:
                    logger.info(f"✓ Task {task_event.task_id[:8]} enriched: is_retry={task_event.is_retry}, retry_of={task_event.retry_of.task_id[:8]}")
                else:
                    logger.warning(f"✗ Task {task_event.task_id[:8]} enriched but NO parent found: is_retry={task_event.is_retry}")

                # Always save to DB regardless of environment filter
                # Environment filtering is applied only on read operations
                task_service.save_task_event(task_event)

                # Update daily statistics
                daily_stats_service.update_daily_stats(task_event)

            # Broadcast to all WebSocket clients
            # Clients can filter based on their active environment
            self.connection_manager.queue_broadcast(task_event)

            # Trigger workflow evaluation
            if self.workflow_engine:
                self.workflow_engine.process_event(task_event)

        except Exception as e:
            logger.error(f"Error handling task event {task_event.task_id}: {e}", exc_info=True)

    def handle_worker_event(self, worker_event: WorkerEvent):
        """Handle worker event: broadcast to WebSocket and handle orphan detection."""
        try:
            with self.db_manager.get_session() as session:
                # If worker went offline, mark its running tasks as orphaned
                # Always process worker events regardless of environment filter
                if worker_event.event_type == 'worker-offline':
                    logger.info(
                        f"Worker {worker_event.hostname} went offline, "
                        f"marking tasks as orphaned"
                    )
                    # Use current server time, not worker timestamp (worker clock may be wrong)
                    orphaned_at = datetime.now(timezone.utc)
                    self._mark_tasks_as_orphaned(session, worker_event.hostname, orphaned_at)

            # Broadcast to all WebSocket clients
            # Clients can filter based on their active environment
            self.connection_manager.queue_worker_broadcast(worker_event)

            # Trigger workflow evaluation
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
        """
        Mark all running tasks on a worker as orphaned after grace period.

        This method waits for the grace period to allow late completion events
        to arrive, then detects and marks orphaned tasks.

        Args:
            session: Database session
            hostname: Worker hostname
            orphaned_at: Timestamp when worker went offline
            grace_period_seconds: Seconds to wait before marking tasks (default: 2)
        """
        try:
            import time

            if grace_period_seconds > 0:
                logger.debug(
                    f"Waiting {grace_period_seconds}s grace period for worker {hostname}"
                )
                time.sleep(grace_period_seconds)

            orphan_service = OrphanDetectionService(session)
            orphaned_tasks = orphan_service.find_and_mark_orphaned_tasks(
                hostname=hostname,
                orphaned_at=orphaned_at,
                grace_period_seconds=grace_period_seconds
            )

            # Broadcast orphan events via WebSocket
            if orphaned_tasks:
                self._broadcast_orphan_events(
                    orphan_service, orphaned_tasks, orphaned_at
                )

        except Exception as e:
            logger.error(
                f"Error marking tasks as orphaned for worker {hostname}: {e}",
                exc_info=True
            )
            session.rollback()

    def _broadcast_orphan_events(
        self,
        orphan_service: OrphanDetectionService,
        orphaned_tasks,
        orphaned_at: datetime
    ):
        """Broadcast orphan events to WebSocket clients."""
        orphan_events = orphan_service.create_orphan_events(
            orphaned_tasks=orphaned_tasks,
            orphaned_at=orphaned_at
        )

        for orphan_event in orphan_events:
            logger.info(f"Broadcasting orphan event for task {orphan_event.task_id}")
            self.connection_manager.queue_broadcast(orphan_event)
