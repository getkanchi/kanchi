"""Retention policy cleanup service for operational database tables."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, List

from sqlalchemy.orm import Session

from database import (
    TaskDailyStatsDB,
    TaskEventDB,
    TaskProgressDB,
    UserSessionDB,
    WorkerEventDB,
    WorkflowExecutionDB,
)
from models import DataRetentionConfig, RetentionCleanupResponse, RetentionCleanupResult
from services.app_config_service import AppConfigService


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
            results=results,
        )


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


RETENTION_TARGETS: List[RetentionTarget] = [
    RetentionTarget(
        key="task_events",
        label="Task events",
        retention_days=lambda policy: policy.task_events_days,
        apply=_delete_by_datetime(TaskEventDB, "timestamp"),
    ),
    RetentionTarget(
        key="task_progress",
        label="Task progress events",
        retention_days=lambda policy: policy.task_progress_days,
        apply=_delete_by_datetime(TaskProgressDB, "timestamp"),
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
