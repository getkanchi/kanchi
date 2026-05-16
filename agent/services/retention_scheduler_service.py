"""Automatic retention cleanup scheduler."""

from __future__ import annotations

import logging
import threading
from datetime import datetime, time, timedelta, timezone
from typing import Optional

from database import DatabaseManager
from models import RetentionLastRun
from services.app_config_service import AppConfigService
from services.retention_service import RetentionService

logger = logging.getLogger(__name__)


class RetentionSchedulerService:
    """Run retention cleanup automatically when the persisted schedule is due."""

    def __init__(self, db_manager: DatabaseManager, poll_interval_seconds: int = 60):
        self.db_manager = db_manager
        self.poll_interval_seconds = poll_interval_seconds
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            logger.warning("Retention scheduler already running")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="retention-scheduler", daemon=True)
        self._thread.start()
        logger.info("Retention scheduler started")

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        logger.info("Retention scheduler stopped")

    def run_once_if_due(self, now: Optional[datetime] = None) -> bool:
        """Run cleanup once when enabled and due. Returns True when cleanup ran."""
        now = now or datetime.now(timezone.utc)
        with self.db_manager.get_session() as session:
            config_service = AppConfigService(session)
            schedule = config_service.get_retention_schedule_config()
            last_run = config_service.get_retention_last_run()

        if not schedule.enabled or not self.is_due(schedule.frequency, schedule.run_at, last_run, now):
            return False

        self.run_cleanup()
        return True

    def run_cleanup(self):
        """Run one live retention cleanup."""
        started_at = datetime.now(timezone.utc)
        try:
            with self.db_manager.get_session() as session:
                config_service = AppConfigService(session)
                config_service.set_retention_last_run(
                    RetentionLastRun(status="running", started_at=started_at, total_deleted=0)
                )

            with self.db_manager.get_session() as session:
                result = RetentionService(session).cleanup(dry_run=False)
                finished_at = datetime.now(timezone.utc)
                AppConfigService(session).set_retention_last_run(
                    RetentionLastRun(
                        status="success",
                        started_at=started_at,
                        finished_at=finished_at,
                        total_deleted=result.total_deleted,
                        dry_run=False,
                        results=result.results,
                    )
                )
                logger.info("Automatic retention cleanup deleted %s rows", result.total_deleted)
                return result
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Automatic retention cleanup failed: %s", exc, exc_info=True)
            with self.db_manager.get_session() as session:
                AppConfigService(session).set_retention_last_run(
                    RetentionLastRun(
                        status="error",
                        started_at=started_at,
                        finished_at=datetime.now(timezone.utc),
                        error=str(exc),
                    )
            )
            return None

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.run_once_if_due()
            except Exception as exc:  # pylint: disable=broad-except
                logger.error("Retention scheduler check failed: %s", exc, exc_info=True)
            self._stop_event.wait(self.poll_interval_seconds)

    @staticmethod
    def is_due(frequency: str, run_at: str, last_run: RetentionLastRun, now: datetime) -> bool:
        """Return whether a schedule is due at the given UTC time."""
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        hour, minute = [int(part) for part in run_at.split(":", 1)]
        scheduled_today = datetime.combine(now.date(), time(hour=hour, minute=minute), tzinfo=timezone.utc)
        if now < scheduled_today:
            return False

        finished_at = last_run.finished_at or last_run.started_at
        if finished_at is None:
            return True
        if finished_at.tzinfo is None:
            finished_at = finished_at.replace(tzinfo=timezone.utc)

        if frequency == "weekly":
            return finished_at <= now - timedelta(days=7)
        return finished_at.date() < now.date()
