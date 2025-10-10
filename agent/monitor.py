"""Simplified Celery event monitor."""

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

from celery import Celery

from models import TaskEvent, WorkerEvent

logger = logging.getLogger(__name__)


class CeleryEventMonitor:
    """Monitor Celery events and handle them simply."""

    def __init__(self, broker_url: str = "amqp://guest@localhost//"):
        self.broker_url = broker_url
        self.app = Celery(broker=broker_url, task_send_sent_event=True)
        self.state = None
        self.task_callback: Optional[Callable] = None
        self.worker_callback: Optional[Callable] = None
        self.workers: Dict[str, Dict[str, Any]] = {}

    def set_task_callback(self, callback: Callable[[TaskEvent], None]):
        """Set callback for task events."""
        self.task_callback = callback

    def set_worker_callback(self, callback: Callable[[WorkerEvent], None]):
        """Set callback for worker events."""
        self.worker_callback = callback

    def _handle_task_event(self, event: Dict[str, Any]):
        """Handle task events."""
        try:
            if self.state:
                self.state.event(event)

            # Get task name from event or state
            task_name = event.get("name", "unknown")
            task_id = event.get("uuid", "")
            event_type = event.get("type", "")
            

            if self.state and task_id:
                task = self.state.tasks.get(task_id)
                if task and hasattr(task, "name"):
                    task_name = task.name

            # Create event object
            task_event = TaskEvent.from_celery_event(event, task_name)

            # Log event
            logger.info(f"Task {event_type}: {task_name}[{task_id}]")

            # Send to callback
            if self.task_callback:
                self.task_callback(task_event)

        except Exception as e:
            logger.error(f"Error handling task event: {e}", exc_info=True)

    def _handle_worker_event(self, event: Dict[str, Any], event_type: str):
        """Handle worker events."""
        try:
            hostname = event.get("hostname", "unknown")
            # Use current server time (UTC) instead of worker timestamp to avoid timezone issues
            # Worker clocks may be misconfigured or in different timezones (e.g., Docker containers)
            # The receive time is more reliable for monitoring purposes
            timestamp = datetime.now(timezone.utc)

            # Update worker state
            if hostname not in self.workers:
                self.workers[hostname] = {}

            if event_type == "worker-online":
                self.workers[hostname].update(
                    {
                        "status": "online",
                        "timestamp": timestamp,
                        "sw_ident": event.get("sw_ident"),
                        "sw_ver": event.get("sw_ver"),
                        "sw_sys": event.get("sw_sys"),
                    }
                )
                logger.info(f"Worker online: {hostname}")

            elif event_type == "worker-offline":
                self.workers[hostname].update({"status": "offline", "timestamp": timestamp})
                logger.warning(f"Worker offline: {hostname}")

            elif event_type == "worker-heartbeat":
                self.workers[hostname].update(
                    {
                        "status": "online",
                        "timestamp": timestamp,
                        "active": event.get("active", 0),
                        "processed": event.get("processed", 0),
                        "pool": event.get("pool"),
                        "loadavg": event.get("loadavg"),
                        "freq": event.get("freq"),
                    }
                )
                logger.debug(f"Worker heartbeat: {hostname} - Active: {event.get('active', 0)}")

            # Create and send worker event
            if self.worker_callback:
                worker_event = WorkerEvent.from_celery_event(event)
                self.worker_callback(worker_event)

        except Exception as e:
            logger.error(f"Error handling worker event: {e}", exc_info=True)

    def get_workers_info(self) -> Dict[str, Dict[str, Any]]:
        """Get current worker states."""
        return self.workers.copy()

    def start_monitoring(self):
        """Start monitoring Celery events."""
        logger.info(f"Starting Celery event monitor - Broker: {self.broker_url}")

        self.state = self.app.events.State()

        try:
            with self.app.connection() as connection:
                handlers = {
                    "task-sent": self._handle_task_event,
                    "task-received": self._handle_task_event,
                    "task-started": self._handle_task_event,
                    "task-succeeded": self._handle_task_event,
                    "task-failed": self._handle_task_event,
                    "task-retried": self._handle_task_event,
                    "task-revoked": self._handle_task_event,
                    "worker-online": lambda event: self._handle_worker_event(
                        event, "worker-online"
                    ),
                    "worker-offline": lambda event: self._handle_worker_event(
                        event, "worker-offline"
                    ),
                    "worker-heartbeat": lambda event: self._handle_worker_event(
                        event, "worker-heartbeat"
                    ),
                }

                recv = self.app.events.Receiver(connection, handlers=handlers)

                logger.info("Monitoring Celery events... Press Ctrl+C to stop")
                recv.capture(limit=None, timeout=None, wakeup=True)

        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Error in event monitoring: {e}", exc_info=True)
            raise
