"""Background scheduler for automatic retention cleanup."""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from database import DatabaseManager
from models import RetentionCleanupResponse
from .retention_service import RetentionService

logger = logging.getLogger(__name__)


@dataclass
class RetentionScheduleStatus:
    enabled: bool
    interval_hours: int
    next_run_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    last_completed_at: Optional[datetime] = None
    last_duration_seconds: Optional[float] = None
    last_deleted_rows: Optional[int] = None
    last_error: Optional[str] = None


class RetentionScheduler:
    """Run retention cleanup on a fixed interval in the background."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        *,
        enabled: bool = True,
        interval_hours: int = 24,
        interval_seconds: Optional[int] = None,
    ):
        self.db_manager = db_manager
        self.enabled = enabled
        self.interval_hours = max(1, interval_hours)
        self.interval = timedelta(seconds=max(1, interval_seconds)) if interval_seconds else timedelta(hours=self.interval_hours)
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        now = datetime.now(timezone.utc)
        self._status = RetentionScheduleStatus(
            enabled=enabled,
            interval_hours=self.interval_hours,
            next_run_at=now + self.interval if enabled else None,
        )

    def start(self) -> None:
        if not self.enabled:
            logger.info("Automatic retention cleanup scheduler disabled")
            return
        if self._thread and self._thread.is_alive():
            logger.warning("Retention cleanup scheduler already running")
            return

        self._thread = threading.Thread(target=self._run_loop, name="retention-cleanup-scheduler", daemon=True)
        self._thread.start()
        logger.info("Automatic retention cleanup scheduler started (interval=%ss)", int(self.interval.total_seconds()))

    def stop(self) -> None:
        self._stop_event.set()

    def is_alive(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def get_status(self) -> RetentionScheduleStatus:
        with self._lock:
            return RetentionScheduleStatus(**self._status.__dict__)

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            with self._lock:
                next_run_at = self._status.next_run_at or (datetime.now(timezone.utc) + self.interval)
                self._status.next_run_at = next_run_at

            wait_seconds = max(0.0, (next_run_at - datetime.now(timezone.utc)).total_seconds())
            if self._stop_event.wait(wait_seconds):
                return

            started_at = datetime.now(timezone.utc)
            deleted_rows: Optional[int] = None
            error: Optional[str] = None

            try:
                with self.db_manager.get_session() as session:
                    result: RetentionCleanupResponse = RetentionService(session).cleanup(dry_run=False)
                    deleted_rows = result.total_deleted
                logger.info("Automatic retention cleanup completed, deleted %s rows", deleted_rows)
            except Exception as exc:  # pylint: disable=broad-except
                error = str(exc)
                logger.error("Automatic retention cleanup failed: %s", exc, exc_info=True)

            finished_at = datetime.now(timezone.utc)
            with self._lock:
                self._status.last_run_at = started_at
                self._status.last_completed_at = finished_at
                self._status.last_duration_seconds = round((finished_at - started_at).total_seconds(), 3)
                self._status.last_deleted_rows = deleted_rows
                self._status.last_error = error
                self._status.next_run_at = finished_at + self.interval
