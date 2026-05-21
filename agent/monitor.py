"""Simplified Celery event monitor."""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

from celery import Celery

from models import TaskEvent, WorkerEvent
from models import TaskProgressEvent, TaskStepsEvent
from constants import EventType
from config import mask_sensitive_url

logger = logging.getLogger(__name__)

_RECONNECT_BASE_DELAY = 1    # seconds
_RECONNECT_MAX_DELAY  = 60   # seconds
_RECONNECT_MULTIPLIER = 2


class CeleryEventMonitor:
    """Monitor Celery events and handle them simply."""

    def __init__(
        self,
        broker_url: str = "amqp://guest@localhost//",
        allow_pickle_serialization: bool = False,
    ):
        self.broker_url = broker_url
        self.app = Celery(broker=broker_url, task_send_sent_event=True)
        self.app.conf.update(
            accept_content=["json"],
            task_serializer="json",
            result_serializer="json",
            event_serializer="json",
        )

        if allow_pickle_serialization:
            self.app.conf.accept_content.append("application/x-python-serialize")
            logger.warning(
                "Pickle deserialization ENABLED for Celery monitor; "
                "only use when all message producers are trusted."
            )

        self.state = None
        self.task_callback: Optional[Callable] = None
        self.worker_callback: Optional[Callable] = None
        self.progress_callback: Optional[Callable] = None
        self.steps_callback: Optional[Callable] = None
        self.workers: Dict[str, Dict[str, Any]] = {}
        self._stop = False

    def set_task_callback(self, callback: Callable[[TaskEvent], None]):
        """Set callback for task events."""
        self.task_callback = callback

    def set_worker_callback(self, callback: Callable[[WorkerEvent], None]):
        """Set callback for worker events."""
        self.worker_callback = callback

    def set_progress_callback(self, callback: Callable[[TaskProgressEvent], None]):
        """Set callback for task progress events."""
        self.progress_callback = callback

    def set_steps_callback(self, callback: Callable[[TaskStepsEvent], None]):
        """Set callback for task steps events."""
        self.steps_callback = callback

    def _handle_task_event(self, event: Dict[str, Any]):
        """Handle task events."""
        try:
            if self.state:
                self.state.event(event)

            task_name = event.get("name", "unknown")
            task_id = event.get("uuid", "")
            event_type = event.get("type", "")
            

            if self.state and task_id:
                task = self.state.tasks.get(task_id)
                if task and hasattr(task, "name"):
                    task_name = task.name

            task_event = TaskEvent.from_celery_event(event, task_name)

            logger.debug(f"Task {event_type}: {task_name}[{task_id}]")

            if self.task_callback:
                self.task_callback(task_event)

        except Exception as e:
            logger.error(f"Error handling task event: {e}", exc_info=True)

    def _handle_progress_event(self, event: Dict[str, Any]):
        """Handle custom task progress events."""
        try:
            progress_event = TaskProgressEvent.from_celery_event(event)
            if self.progress_callback:
                self.progress_callback(progress_event)
        except Exception as exc:
            logger.error(f"Error handling progress event: {exc}", exc_info=True)

    def _handle_steps_event(self, event: Dict[str, Any]):
        """Handle custom task steps events."""
        try:
            steps = event.get("steps") or []
            ts_value = event.get("timestamp")
            if isinstance(ts_value, (int, float)):
                ts = datetime.fromtimestamp(ts_value, tz=timezone.utc)
            else:
                ts = datetime.now(timezone.utc)
            steps_event = TaskStepsEvent(
                task_id=event.get("task_id", ""),
                task_name=event.get("task_name", ""),
                steps=steps,
                timestamp=ts,
            )
            if self.steps_callback:
                self.steps_callback(steps_event)
        except Exception as exc:
            logger.error(f"Error handling steps event: {exc}", exc_info=True)

    def _handle_worker_event(self, event: Dict[str, Any], event_type: str):
        """Handle worker events."""
        try:
            hostname = event.get("hostname", "unknown")
            timestamp = datetime.now(timezone.utc)

            if hostname not in self.workers:
                self.workers[hostname] = {}

            if event_type == EventType.WORKER_ONLINE.value:
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

            elif event_type == EventType.WORKER_OFFLINE.value:
                self.workers[hostname].update({"status": "offline", "timestamp": timestamp})
                logger.warning(f"Worker offline: {hostname}")

            elif event_type == EventType.WORKER_HEARTBEAT.value:
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

            if self.worker_callback:
                worker_event = WorkerEvent.from_celery_event(event)
                self.worker_callback(worker_event)

        except Exception as e:
            logger.error(f"Error handling worker event: {e}", exc_info=True)

    def get_workers_info(self) -> Dict[str, Dict[str, Any]]:
        """Get current worker states."""
        return self.workers.copy()

    def stop(self):
        """Signal the monitor loop to stop reconnecting and exit cleanly."""
        self._stop = True

    def _run_once(self):
        """Open one broker connection and capture events until it closes."""
        with self.app.connection() as connection:
            handlers = {
                EventType.TASK_SENT.value: self._handle_task_event,
                EventType.TASK_RECEIVED.value: self._handle_task_event,
                EventType.TASK_STARTED.value: self._handle_task_event,
                EventType.TASK_SUCCEEDED.value: self._handle_task_event,
                EventType.TASK_FAILED.value: self._handle_task_event,
                EventType.TASK_RETRIED.value: self._handle_task_event,
                EventType.TASK_REVOKED.value: self._handle_task_event,
                EventType.WORKER_ONLINE.value: lambda event: self._handle_worker_event(
                    event, EventType.WORKER_ONLINE.value
                ),
                EventType.WORKER_OFFLINE.value: lambda event: self._handle_worker_event(
                    event, EventType.WORKER_OFFLINE.value
                ),
                EventType.WORKER_HEARTBEAT.value: lambda event: self._handle_worker_event(
                    event, EventType.WORKER_HEARTBEAT.value
                ),
                EventType.TASK_PROGRESS.value: self._handle_progress_event,
                EventType.TASK_STEPS.value: self._handle_steps_event,
            }
            recv = self.app.events.Receiver(connection, handlers=handlers)
            logger.info("Monitoring Celery events...")
            recv.capture(limit=None, timeout=None, wakeup=True)

    def start_monitoring(self):
        """Start monitoring Celery events, reconnecting automatically on broker disconnects.

        Uses exponential backoff (1s → 60s) between reconnect attempts so that
        a flapping broker does not spin the thread at full speed.  The loop only
        exits when ``stop()`` is called or a ``KeyboardInterrupt`` is received.
        """
        logger.info(
            "Starting Celery event monitor - Broker: %s",
            mask_sensitive_url(self.broker_url),
        )
        delay = _RECONNECT_BASE_DELAY

        while not self._stop:
            # Fresh State on every (re)connect: stale in-memory worker data is
            # discarded and rebuilt from the first heartbeats after reconnection.
            self.state = self.app.events.State()
            try:
                self._run_once()
                # recv.capture() returns without raising only when the broker
                # closed the connection cleanly (e.g. graceful broker restart).
                # Reconnect just as we would for an error.
                if not self._stop:
                    logger.warning(
                        "Event stream closed by broker; reconnecting in %ds...",
                        _RECONNECT_BASE_DELAY,
                    )
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as exc:
                if self._stop:
                    break
                logger.error(
                    "Error in event monitoring, reconnecting in %ds: %s",
                    delay,
                    exc,
                )
            else:
                # Clean close: reset backoff so the next reconnect is fast.
                delay = _RECONNECT_BASE_DELAY
                if not self._stop:
                    time.sleep(delay)
                continue

            if not self._stop:
                time.sleep(delay)
                delay = min(delay * _RECONNECT_MULTIPLIER, _RECONNECT_MAX_DELAY)
