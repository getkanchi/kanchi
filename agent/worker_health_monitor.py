"""Worker health monitoring for detecting offline workers."""

import logging
import threading
import time
from datetime import datetime, timedelta, timezone

from database import DatabaseManager
from event_handler import EventHandler
from services import OrphanDetectionService

logger = logging.getLogger(__name__)


class WorkerHealthMonitor:
    """Monitors worker health by checking heartbeat timestamps."""

    def __init__(self, monitor_instance, db_manager: DatabaseManager, event_handler: EventHandler):
        self.monitor_instance = monitor_instance
        self.db_manager = db_manager
        self.event_handler = event_handler
        self.running = False
        self.thread = None

        self.check_interval = 15
        self.worker_timeout = 30
        self.orphan_grace_period = 2

    def start(self):
        """Start the health monitor in a background thread."""
        if self.running:
            logger.warning("Worker health monitor already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_monitor, daemon=True)
        self.thread.start()
        logger.info(
            f"Worker health monitor started (timeout: {self.worker_timeout}s, "
            f"interval: {self.check_interval}s, grace period: {self.orphan_grace_period}s)"
        )

    def stop(self):
        """Stop the health monitor."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Worker health monitor stopped")

    def _run_monitor(self):
        """Main monitoring loop."""
        while self.running:
            try:
                self._check_worker_health()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in worker health monitor: {e}", exc_info=True)
                time.sleep(self.check_interval)

    def _check_worker_health(self):
        """Check all workers for staleness and mark offline workers."""
        current_time = datetime.now(timezone.utc)
        timeout_threshold = current_time - timedelta(seconds=self.worker_timeout)

        workers = self.monitor_instance.get_workers_info()
        offline_workers = []

        for hostname, worker_data in workers.items():
            last_seen = worker_data.get('timestamp')
            current_status = worker_data.get('status', 'unknown')

            if last_seen and isinstance(last_seen, datetime):
                if last_seen < timeout_threshold and current_status == 'online':
                    logger.warning(f"Worker {hostname} appears offline (last seen: {last_seen})")

                    workers[hostname]['status'] = 'offline'
                    offline_workers.append(hostname)
                    self._mark_worker_tasks_as_orphaned(hostname, current_time)

        if offline_workers:
            logger.info(f"Marked {len(offline_workers)} workers as offline: {offline_workers}")

    def _mark_worker_tasks_as_orphaned(self, hostname: str, orphaned_at: datetime):
        """
        Mark all running tasks on a worker as orphaned.

        Note: This method is called by the health monitor when it detects a worker
        has not sent a heartbeat within the timeout period. Unlike the event handler,
        the health monitor waits before calling this method, so the grace period has
        already passed.

        Args:
            hostname: Worker hostname
            orphaned_at: Timestamp when worker was detected as offline
        """
        try:
            with self.db_manager.get_session() as session:
                orphan_service = OrphanDetectionService(session)

                orphaned_tasks = orphan_service.find_and_mark_orphaned_tasks(
                    hostname=hostname,
                    orphaned_at=orphaned_at,
                    grace_period_seconds=self.orphan_grace_period
                )

                if orphaned_tasks:
                    orphan_service.broadcast_orphan_events(
                        orphaned_tasks, orphaned_at, self.event_handler.connection_manager
                    )

        except Exception as e:
            logger.error(
                f"Error marking tasks as orphaned for worker {hostname}: {e}",
                exc_info=True
            )
