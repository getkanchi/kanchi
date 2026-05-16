"""Retention policy cleanup service for operational database tables."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import threading
from typing import Callable, List

from sqlalchemy import and_, not_, select
from sqlalchemy.orm import Session

from constants import EventType
from database import (
    TaskDailyStatsDB,
    TaskEventDB,
    TaskLatestDB,
    TaskProgressDB,
    TaskProgressLatestDB,
    TaskStepsDB,
    UserSessionDB,
    WorkerEventDB,
    WorkflowExecutionDB,
)
from models import DataRetentionConfig, RetentionCleanupResponse, RetentionCleanupResult
from services.app_config_service import AppConfigService

_cleanup_lock = threading.Lock()


@dataclass(frozen=True)
class RetentionTarget:
    key: str
    label: str
    retention_days: Callable[[DataRetentionConfig], int]
    apply: Callable[[Session, datetime, bool], int]


class RetentionService:
    """Calculate and execute retention cleanup against persisted data."""

    def __init__(self, session: Session):
        self.session = session
        self.config_service = AppConfigService(session)

    def get_policy(self) -> DataRetentionConfig:
        return self.config_service.get_data_retention_config()

    def cleanup(self, *, dry_run: bool = False) -> RetentionCleanupResponse:
        if not _cleanup_lock.acquire(blocking=False):
            raise RuntimeError("Retention cleanup is already running")

        try:
            policy = self.get_policy()
            now = datetime.now(timezone.utc)
            results: List[RetentionCleanupResult] = []

            for target in RETENTION_TARGETS:
                retention_days = target.retention_days(policy)
                cutoff = now - timedelta(days=retention_days)
                deleted = target.apply(self.session, cutoff, dry_run)
                results.append(
                    RetentionCleanupResult(
                        key=target.key,
                        label=target.label,
                        retention_days=retention_days,
                        deleted=deleted,
                    )
                )

            if dry_run:
                self.session.rollback()
            else:
                self.session.commit()

            return RetentionCleanupResponse(
                dry_run=dry_run,
                total_deleted=sum(item.deleted for item in results),
                policy=policy,
                results=results,
            )
        finally:
            _cleanup_lock.release()


def _delete_by_datetime(model, column_name: str):
    def apply(session: Session, cutoff: datetime, dry_run: bool) -> int:
        query = session.query(model).filter(getattr(model, column_name) < cutoff)
        if dry_run:
            return query.count()
        return query.delete(synchronize_session=False)

    return apply


def _delete_daily_stats(session: Session, cutoff: datetime, dry_run: bool) -> int:
    query = session.query(TaskDailyStatsDB).filter(TaskDailyStatsDB.date < cutoff.date())
    if dry_run:
        return query.count()
    return query.delete(synchronize_session=False)


def _successful_task_filter(model):
    return and_(
        model.event_type == EventType.TASK_SUCCEEDED,
        model.is_orphan.is_(False),
    )


def _expired_task_family_cleanup(model, time_column: str, successful: bool):
    def apply(session: Session, cutoff: datetime, dry_run: bool) -> int:
        latest_query = session.query(TaskLatestDB.task_id).filter(TaskLatestDB.timestamp < cutoff)
        if successful:
            latest_query = latest_query.filter(_successful_task_filter(TaskLatestDB))
        else:
            latest_query = latest_query.filter(not_(_successful_task_filter(TaskLatestDB)))
        expired_task_ids = latest_query.subquery()

        query = session.query(model).filter(
            getattr(model, time_column) < cutoff,
            model.task_id.in_(select(expired_task_ids.c.task_id)),
        )
        if dry_run:
            return query.count()
        return query.delete(synchronize_session=False)

    return apply


def _expired_task_latest_cleanup(successful: bool):
    def apply(session: Session, cutoff: datetime, dry_run: bool) -> int:
        query = session.query(TaskLatestDB).filter(TaskLatestDB.timestamp < cutoff)
        if successful:
            query = query.filter(_successful_task_filter(TaskLatestDB))
        else:
            query = query.filter(not_(_successful_task_filter(TaskLatestDB)))
        if dry_run:
            return query.count()
        return query.delete(synchronize_session=False)

    return apply


RETENTION_TARGETS: List[RetentionTarget] = [
    RetentionTarget(
        key="task_events_successful",
        label="Successful task events",
        retention_days=lambda policy: policy.task_successful_days,
        apply=_expired_task_family_cleanup(TaskEventDB, "timestamp", True),
    ),
    RetentionTarget(
        key="task_events_unsuccessful",
        label="Unsuccessful task events",
        retention_days=lambda policy: policy.task_unsuccessful_days,
        apply=_expired_task_family_cleanup(TaskEventDB, "timestamp", False),
    ),
    RetentionTarget(
        key="task_progress_successful",
        label="Successful task progress events",
        retention_days=lambda policy: policy.task_successful_days,
        apply=_expired_task_family_cleanup(TaskProgressDB, "timestamp", True),
    ),
    RetentionTarget(
        key="task_progress_unsuccessful",
        label="Unsuccessful task progress events",
        retention_days=lambda policy: policy.task_unsuccessful_days,
        apply=_expired_task_family_cleanup(TaskProgressDB, "timestamp", False),
    ),
    RetentionTarget(
        key="task_progress_latest_successful",
        label="Successful task progress snapshots",
        retention_days=lambda policy: policy.task_successful_days,
        apply=_expired_task_family_cleanup(TaskProgressLatestDB, "updated_at", True),
    ),
    RetentionTarget(
        key="task_progress_latest_unsuccessful",
        label="Unsuccessful task progress snapshots",
        retention_days=lambda policy: policy.task_unsuccessful_days,
        apply=_expired_task_family_cleanup(TaskProgressLatestDB, "updated_at", False),
    ),
    RetentionTarget(
        key="task_steps_successful",
        label="Successful task step definitions",
        retention_days=lambda policy: policy.task_successful_days,
        apply=_expired_task_family_cleanup(TaskStepsDB, "defined_at", True),
    ),
    RetentionTarget(
        key="task_steps_unsuccessful",
        label="Unsuccessful task step definitions",
        retention_days=lambda policy: policy.task_unsuccessful_days,
        apply=_expired_task_family_cleanup(TaskStepsDB, "defined_at", False),
    ),
    RetentionTarget(
        key="task_latest_successful",
        label="Successful task snapshots",
        retention_days=lambda policy: policy.task_successful_days,
        apply=_expired_task_latest_cleanup(True),
    ),
    RetentionTarget(
        key="task_latest_unsuccessful",
        label="Unsuccessful task snapshots",
        retention_days=lambda policy: policy.task_unsuccessful_days,
        apply=_expired_task_latest_cleanup(False),
    ),
    RetentionTarget(
        key="worker_events",
        label="Worker events",
        retention_days=lambda policy: policy.worker_events_days,
        apply=_delete_by_datetime(WorkerEventDB, "timestamp"),
    ),
    RetentionTarget(
        key="workflow_executions",
        label="Workflow executions",
        retention_days=lambda policy: policy.workflow_executions_days,
        apply=_delete_by_datetime(WorkflowExecutionDB, "triggered_at"),
    ),
    RetentionTarget(
        key="task_daily_stats",
        label="Task daily stats",
        retention_days=lambda policy: policy.task_daily_stats_days,
        apply=_delete_daily_stats,
    ),
    RetentionTarget(
        key="inactive_sessions",
        label="Inactive sessions",
        retention_days=lambda policy: policy.inactive_sessions_days,
        apply=_delete_by_datetime(UserSessionDB, "last_active"),
    ),
]
