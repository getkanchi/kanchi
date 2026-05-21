"""Automatic retention cleanup scheduler."""

from __future__ import annotations

import logging
import threading
from calendar import monthrange
from datetime import datetime, time, timezone
from typing import Optional

from database import DatabaseManager
from models import RetentionLastRun, RetentionScheduleConfig
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

        logger.info(
            "Retention scheduler poll: now=%s enabled=%s preset=%s hour=%s minute=%s "
            "weekday=%s month_day=%s timezone=%s "
            "last_status=%s last_started_at=%s last_finished_at=%s",
            now.isoformat(),
            schedule.enabled,
            schedule.preset,
            schedule.hour,
            schedule.minute,
            schedule.weekday,
            schedule.month_day,
            schedule.timezone,
            last_run.status,
            last_run.started_at.isoformat() if last_run.started_at else None,
            last_run.finished_at.isoformat() if last_run.finished_at else None,
        )

        if not schedule.enabled:
            logger.info("Retention scheduler skipped: automatic cleanup is disabled")
            return False

        if not self.is_due(schedule, last_run, now):
            return False

        logger.info("Retention scheduler due: starting automatic cleanup")
        self.run_cleanup()
        return True

    def run_cleanup(self):
        """Run one live retention cleanup."""
        started_at = datetime.now(timezone.utc)
        logger.info("Automatic retention cleanup starting: started_at=%s", started_at.isoformat())
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
                logger.info(
                    "Automatic retention cleanup finished: started_at=%s finished_at=%s "
                    "total_deleted=%s",
                    started_at.isoformat(),
                    finished_at.isoformat(),
                    result.total_deleted,
                )
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
    def is_due(schedule: RetentionScheduleConfig, last_run: RetentionLastRun, now: datetime) -> bool:
        """Return whether a schedule is due at the given UTC time."""
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        finished_at = RetentionSchedulerService._finished_at(last_run)
        if schedule.preset == "hourly":
            scheduled_at = now.replace(minute=schedule.minute, second=0, microsecond=0)
            if now < scheduled_at:
                logger.info(
                    "Retention scheduler skipped: current time is before scheduled minute "
                    "now=%s scheduled_this_hour=%s",
                    now.isoformat(),
                    scheduled_at.isoformat(),
                )
                return False
            return RetentionSchedulerService._is_after_last_run(scheduled_at, finished_at)

        scheduled_today = datetime.combine(
            now.date(),
            time(hour=schedule.hour, minute=schedule.minute),
            tzinfo=timezone.utc,
        )
        if schedule.preset == "daily":
            if now < scheduled_today:
                logger.info(
                    "Retention scheduler skipped: current time is before scheduled time "
                    "now=%s scheduled_today=%s",
                    now.isoformat(),
                    scheduled_today.isoformat(),
                )
                return False
            return RetentionSchedulerService._is_after_last_run(scheduled_today, finished_at)

        if schedule.preset == "weekly":
            if now.weekday() != schedule.weekday:
                logger.info(
                    "Retention scheduler skipped: current weekday does not match schedule "
                    "now=%s current_weekday=%s scheduled_weekday=%s",
                    now.isoformat(),
                    now.weekday(),
                    schedule.weekday,
                )
                return False
            if now < scheduled_today:
                logger.info(
                    "Retention scheduler skipped: current time is before scheduled weekly time "
                    "now=%s scheduled_today=%s",
                    now.isoformat(),
                    scheduled_today.isoformat(),
                )
                return False
            return RetentionSchedulerService._is_after_last_run(scheduled_today, finished_at)

        scheduled_day = min(schedule.month_day, monthrange(now.year, now.month)[1])
        if now.day != scheduled_day:
            logger.info(
                "Retention scheduler skipped: current month day does not match schedule "
                "now=%s current_day=%s scheduled_day=%s configured_month_day=%s",
                now.isoformat(),
                now.day,
                scheduled_day,
                schedule.month_day,
            )
            return False
        if now < scheduled_today:
            logger.info(
                "Retention scheduler skipped: current time is before scheduled monthly time "
                "now=%s scheduled_today=%s",
                now.isoformat(),
                scheduled_today.isoformat(),
            )
            return False
        return RetentionSchedulerService._is_after_last_run(scheduled_today, finished_at)

    @staticmethod
    def _finished_at(last_run: RetentionLastRun) -> Optional[datetime]:
        finished_at = last_run.finished_at or last_run.started_at
        if finished_at and finished_at.tzinfo is None:
            return finished_at.replace(tzinfo=timezone.utc)
        return finished_at

    @staticmethod
    def _is_after_last_run(scheduled_at: datetime, finished_at: Optional[datetime]) -> bool:
        if finished_at is None:
            logger.info("Retention scheduler due: no previous automatic cleanup run recorded")
            return True
        if finished_at < scheduled_at:
            logger.info(
                "Retention scheduler due: scheduled run has not completed "
                "scheduled_at=%s last_finished_at=%s",
                scheduled_at.isoformat(),
                finished_at.isoformat(),
            )
            return True
        logger.info(
            "Retention scheduler skipped: scheduled run already completed "
            "scheduled_at=%s last_finished_at=%s",
            scheduled_at.isoformat(),
            finished_at.isoformat(),
        )
        return False
