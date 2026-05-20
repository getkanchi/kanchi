"""Service for persisted user-initiated task actions."""

from __future__ import annotations

# ruff: noqa: UP006, UP007
import ast
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from database import (
    TaskActionDB,
    TaskActionItemDB,
    TaskEventDB,
    TaskLatestDB,
    TaskRerunRelationshipDB,
    TaskResolutionDB,
)
from models import (
    RerunPreflightItem,
    RerunPreflightResponse,
    RerunUnavailableReason,
    TaskActionDetail,
    TaskActionItem,
    TaskActionItemOutcome,
    TaskActionStatus,
    TaskActionSummary,
    TaskActionType,
    TaskActionWebSocketEvent,
    TaskEvent,
)
from services.task_service import TaskService
from services.utils import EnvironmentFilter
from utils.payload_sanitizer import contains_placeholder

logger = logging.getLogger(__name__)


class TaskActionValidationError(ValueError):
    """Raised when a task action request is invalid."""


class TaskActionService:
    """Create, execute, and read persisted task actions."""

    def __init__(
        self,
        session: Session,
        *,
        monitor_instance=None,
        connection_manager=None,
        max_selection_size: int = 100,
        active_env=None,
    ):
        self.session = session
        self.monitor_instance = monitor_instance
        self.connection_manager = connection_manager
        self.max_selection_size = max(1, int(max_selection_size or 100))
        self.active_env = active_env
        self.task_service = TaskService(session, active_env=active_env)

    def preflight_rerun(self, task_ids: Sequence[str]) -> RerunPreflightResponse:
        ids = self._normalize_task_ids(task_ids)
        self._validate_selection_size(ids)

        items = [self._preflight_rerun_item(task_id) for task_id in ids]
        ready_count = sum(1 for item in items if item.ready)
        return RerunPreflightResponse(
            total=len(items),
            ready_count=ready_count,
            unavailable_count=len(items) - ready_count,
            max_selection_size=self.max_selection_size,
            items=items,
        )

    def create_action(
        self,
        *,
        action_type: TaskActionType,
        task_ids: Sequence[str],
        initiated_by: Optional[str] = None,
        initiated_by_user_id: Optional[str] = None,
        initiated_session_id: Optional[str] = None,
    ) -> TaskActionDetail:
        ids = self._normalize_task_ids(task_ids)
        self._validate_selection_size(ids)

        if action_type == TaskActionType.RERUN:
            preflight = self.preflight_rerun(ids)
            if preflight.ready_count == 0:
                raise TaskActionValidationError("No selected tasks can be rerun.")

        now = datetime.now(timezone.utc)
        action = TaskActionDB(
            id=str(uuid.uuid4()),
            action_type=action_type.value,
            status=TaskActionStatus.RUNNING.value,
            initiated_by_user_id=initiated_by_user_id,
            initiated_by=initiated_by or "anonymous",
            initiated_session_id=initiated_session_id,
            created_at=now,
            started_at=now,
            original_task_ids=list(ids),
            selection_size=len(ids),
            item_total=len(ids),
            summary={},
        )
        self.session.add(action)
        self.session.flush()

        if action_type == TaskActionType.RESOLVE:
            self._execute_resolution_action(action, ids, resolve=True, resolved_by=initiated_by)
        elif action_type == TaskActionType.UNRESOLVE:
            self._execute_resolution_action(action, ids, resolve=False, resolved_by=initiated_by)
        elif action_type == TaskActionType.RERUN:
            self._execute_rerun_action(action, ids, initiated_by=initiated_by)
        else:
            raise TaskActionValidationError(f"Unsupported task action: {action_type}")

        self._finalize_action(action)
        self.session.commit()
        detail = self.get_action(action.id)
        self._broadcast(detail)
        return detail

    def list_actions(self, limit: int = 20) -> List[TaskActionSummary]:
        rows = (
            self.session.query(TaskActionDB)
            .order_by(TaskActionDB.created_at.desc())
            .limit(max(1, min(limit, 100)))
            .all()
        )
        return [self._action_to_summary(row) for row in rows]

    def get_action(self, action_id: str) -> TaskActionDetail:
        action = (
            self.session.query(TaskActionDB)
            .filter(TaskActionDB.id == action_id)
            .one_or_none()
        )
        if not action:
            raise KeyError(action_id)

        items_db = (
            self.session.query(TaskActionItemDB)
            .filter(TaskActionItemDB.action_id == action_id)
            .order_by(TaskActionItemDB.id.asc())
            .all()
        )
        rerun_task_ids = [item.rerun_task_id for item in items_db if item.rerun_task_id]
        rerun_tasks = self._fetch_task_events_by_id(rerun_task_ids)

        items = [
            self._item_to_model(item, rerun_tasks.get(item.rerun_task_id or ""))
            for item in items_db
        ]
        summary = self._action_to_summary(action)
        return TaskActionDetail(
            **summary.model_dump(),
            items=items,
            rerun_lifecycle_counts=self._rerun_lifecycle_counts(rerun_tasks.values()),
        )

    def _execute_resolution_action(
        self,
        action: TaskActionDB,
        task_ids: Sequence[str],
        *,
        resolve: bool,
        resolved_by: Optional[str],
    ) -> None:
        for task_id in task_ids:
            latest = self._find_latest_row(task_id)
            if not latest:
                self._add_item(
                    action,
                    original_task_id=task_id,
                    outcome=TaskActionItemOutcome.FAILED,
                    reason_code="task_not_found",
                    reason="Task not found.",
                )
                continue

            task_name = latest.task_name
            existing = (
                self.session.query(TaskResolutionDB)
                .filter(TaskResolutionDB.task_id == task_id)
                .one_or_none()
            )

            if resolve:
                if existing and existing.resolved:
                    self._add_item(
                        action,
                        original_task_id=task_id,
                        original_task_name=task_name,
                        outcome=TaskActionItemOutcome.NOOP,
                        reason="Task was already resolved.",
                    )
                    continue

                now = datetime.now(timezone.utc)
                if existing:
                    existing.resolved = True
                    existing.resolved_at = now
                    existing.resolved_by = resolved_by or existing.resolved_by
                else:
                    self.session.add(TaskResolutionDB(
                        task_id=task_id,
                        resolved=True,
                        resolved_at=now,
                        resolved_by=resolved_by,
                    ))
                self._update_latest_resolution(task_id, True, resolved_by, now)
                self._add_item(
                    action,
                    original_task_id=task_id,
                    original_task_name=task_name,
                    outcome=TaskActionItemOutcome.CHANGED,
                )
                continue

            if existing and existing.resolved:
                self.session.delete(existing)
                self._update_latest_resolution(task_id, False, None, None)
                self._add_item(
                    action,
                    original_task_id=task_id,
                    original_task_name=task_name,
                    outcome=TaskActionItemOutcome.CHANGED,
                )
            else:
                self._update_latest_resolution(task_id, False, None, None)
                self._add_item(
                    action,
                    original_task_id=task_id,
                    original_task_name=task_name,
                    outcome=TaskActionItemOutcome.NOOP,
                    reason="Task was already unresolved.",
                )

    def _execute_rerun_action(
        self,
        action: TaskActionDB,
        task_ids: Sequence[str],
        *,
        initiated_by: Optional[str],
    ) -> None:
        for task_id in task_ids:
            preflight = self._preflight_rerun_item(task_id)
            if not preflight.ready:
                self._add_item(
                    action,
                    original_task_id=task_id,
                    original_task_name=preflight.task_name,
                    outcome=TaskActionItemOutcome.SKIPPED_UNAVAILABLE,
                    reason_code=preflight.reason_code,
                    reason=preflight.reason,
                )
                continue

            latest = self._find_latest_row(task_id)
            args, kwargs = self._resolve_call_signature(latest)
            queue_name = latest.queue or latest.routing_key or "default"
            rerun_task_id = str(uuid.uuid4())
            relationship = None

            try:
                relationship = TaskRerunRelationshipDB(
                    original_task_id=task_id,
                    rerun_task_id=rerun_task_id,
                    action_id=action.id,
                    created_by=initiated_by,
                )
                self.session.add(relationship)
                self.session.flush()
                self.monitor_instance.app.send_task(
                    latest.task_name,
                    args=args,
                    kwargs=kwargs,
                    queue=queue_name,
                    task_id=rerun_task_id,
                )
                self._add_item(
                    action,
                    original_task_id=task_id,
                    original_task_name=latest.task_name,
                    outcome=TaskActionItemOutcome.CREATED,
                    rerun_task_id=rerun_task_id,
                    rerun_task_name=latest.task_name,
                )
            except Exception as exc:  # pylint: disable=broad-except
                logger.error("Failed to rerun task %s: %s", task_id, exc, exc_info=True)
                if relationship is not None:
                    self.session.delete(relationship)
                self._add_item(
                    action,
                    original_task_id=task_id,
                    original_task_name=latest.task_name,
                    outcome=TaskActionItemOutcome.FAILED,
                    reason_code="send_failed",
                    reason=str(exc),
                )

    def _preflight_rerun_item(self, task_id: str) -> RerunPreflightItem:
        latest = self._find_latest_row(task_id)
        if not latest:
            return RerunPreflightItem(
                task_id=task_id,
                ready=False,
                reason_code=RerunUnavailableReason.TASK_NOT_FOUND.value,
                reason="Task not found.",
            )

        if not latest.task_name or latest.task_name == "unknown":
            return RerunPreflightItem(
                task_id=task_id,
                task_name=latest.task_name,
                ready=False,
                reason_code=RerunUnavailableReason.MISSING_TASK_NAME.value,
                reason="Kanchi does not have the original task name.",
                task=self._row_to_task_event(latest),
            )

        if not self.monitor_instance or not getattr(self.monitor_instance, "app", None):
            return RerunPreflightItem(
                task_id=task_id,
                task_name=latest.task_name,
                ready=False,
                reason_code=RerunUnavailableReason.MONITOR_UNAVAILABLE.value,
                reason="Celery monitor is not available.",
                task=self._row_to_task_event(latest),
            )

        try:
            args, kwargs = self._resolve_call_signature(latest)
        except ValueError:
            return RerunPreflightItem(
                task_id=task_id,
                task_name=latest.task_name,
                ready=False,
                reason_code=RerunUnavailableReason.UNPARSEABLE_PAYLOAD.value,
                reason="Kanchi could not reconstruct the task arguments.",
                task=self._row_to_task_event(latest),
            )

        if contains_placeholder(args) or contains_placeholder(kwargs):
            return RerunPreflightItem(
                task_id=task_id,
                task_name=latest.task_name,
                ready=False,
                reason_code=RerunUnavailableReason.TRUNCATED_PAYLOAD.value,
                reason="Captured task arguments were truncated before reaching Kanchi.",
                task=self._row_to_task_event(latest),
            )

        return RerunPreflightItem(
            task_id=task_id,
            task_name=latest.task_name,
            ready=True,
            task=self._row_to_task_event(latest),
        )

    def _normalize_task_ids(self, task_ids: Sequence[str]) -> List[str]:
        normalized: List[str] = []
        seen = set()
        for task_id in task_ids:
            value = str(task_id or "").strip()
            if not value or value in seen:
                continue
            normalized.append(value)
            seen.add(value)
        if not normalized:
            raise TaskActionValidationError("At least one task id is required.")
        return normalized

    def _validate_selection_size(self, task_ids: Sequence[str]) -> None:
        if len(task_ids) > self.max_selection_size:
            raise TaskActionValidationError(
                f"Select at most {self.max_selection_size} tasks for one action."
            )

    def _find_latest_row(self, task_id: str):
        latest_query = self.session.query(TaskLatestDB).filter(TaskLatestDB.task_id == task_id)
        latest_query = EnvironmentFilter.apply(latest_query, self.active_env, model=TaskLatestDB)
        latest = latest_query.one_or_none()
        if latest:
            return latest

        event_query = self.session.query(TaskEventDB).filter(TaskEventDB.task_id == task_id)
        event_query = EnvironmentFilter.apply(event_query, self.active_env)
        return event_query.order_by(TaskEventDB.timestamp.desc(), TaskEventDB.id.desc()).first()

    def _row_to_task_event(self, row) -> Optional[TaskEvent]:
        if not row:
            return None
        event = self.task_service._db_to_task_event(row)
        self.task_service._bulk_enrich_with_retry_info([event])
        self.task_service._attach_resolution_info([event])
        if hasattr(self.task_service, "_bulk_enrich_with_rerun_info"):
            self.task_service._bulk_enrich_with_rerun_info([event])
        return event

    def _fetch_task_events_by_id(self, task_ids: Iterable[str]) -> Dict[str, TaskEvent]:
        ids = [task_id for task_id in task_ids if task_id]
        if not ids:
            return {}
        events: Dict[str, TaskEvent] = {}
        latest_query = self.session.query(TaskLatestDB).filter(TaskLatestDB.task_id.in_(ids))
        latest_query = EnvironmentFilter.apply(latest_query, self.active_env, model=TaskLatestDB)
        rows = latest_query.all()
        for row in rows:
            task = self._row_to_task_event(row)
            if task:
                events[row.task_id] = task
        missing = [task_id for task_id in ids if task_id not in events]
        if missing:
            latest_subquery = (
                self.session.query(
                    TaskEventDB.task_id,
                    func.max(TaskEventDB.timestamp).label("max_timestamp"),
                )
                .filter(TaskEventDB.task_id.in_(missing))
                .group_by(TaskEventDB.task_id)
                .subquery()
            )
            event_query = self.session.query(TaskEventDB).join(
                latest_subquery,
                (TaskEventDB.task_id == latest_subquery.c.task_id) &
                (TaskEventDB.timestamp == latest_subquery.c.max_timestamp),
            )
            event_query = EnvironmentFilter.apply(event_query, self.active_env)
            rows = event_query.all()
            for row in rows:
                task = self._row_to_task_event(row)
                if task:
                    events[row.task_id] = task
        return events

    def _resolve_call_signature(self, row) -> Tuple[tuple, dict]:
        args = self._parse_args(getattr(row, "args", None))
        kwargs = self._parse_kwargs(getattr(row, "kwargs", None))

        if args or kwargs:
            return args, kwargs

        received = (
            self.session.query(TaskEventDB)
            .filter(
                TaskEventDB.task_id == row.task_id,
                or_(
                    TaskEventDB.args.isnot(None),
                    TaskEventDB.kwargs.isnot(None),
                ),
            )
            .order_by(TaskEventDB.timestamp.asc(), TaskEventDB.id.asc())
            .first()
        )
        if received:
            args = self._parse_args(received.args)
            kwargs = self._parse_kwargs(received.kwargs)

        return args, kwargs

    def _parse_args(self, raw_value: Any) -> tuple:
        if raw_value in (None, "", "()", "[]"):
            return ()
        parsed = self._deserialize_value(raw_value, [])
        if parsed in (None, "", (), [], "()", "[]"):
            return ()
        if isinstance(parsed, tuple):
            return parsed
        if isinstance(parsed, list):
            return tuple(parsed)
        return (parsed,)

    def _parse_kwargs(self, raw_value: Any) -> dict:
        if raw_value in (None, "", "{}"):
            return {}
        parsed = self._deserialize_value(raw_value, {})
        if isinstance(parsed, dict):
            return parsed
        raise ValueError("kwargs are not a dict")

    def _deserialize_value(self, raw_value: Any, default: Any) -> Any:
        if isinstance(raw_value, (list, dict, tuple)):
            return raw_value
        if isinstance(raw_value, str):
            text = raw_value.strip()
            if not text:
                return default
            try:
                return json.loads(text)
            except (ValueError, json.JSONDecodeError):
                try:
                    return ast.literal_eval(text)
                except (ValueError, SyntaxError) as exc:
                    raise ValueError("Unable to parse stored task payload") from exc
        return raw_value if raw_value is not None else default

    def _update_latest_resolution(
        self,
        task_id: str,
        resolved: bool,
        resolved_by: Optional[str],
        resolved_at: Optional[datetime],
    ) -> None:
        latest = (
            self.session.query(TaskLatestDB)
            .filter(TaskLatestDB.task_id == task_id)
            .one_or_none()
        )
        if latest:
            latest.resolved = resolved
            latest.resolved_by = resolved_by
            latest.resolved_at = resolved_at

    def _add_item(
        self,
        action: TaskActionDB,
        *,
        original_task_id: str,
        outcome: TaskActionItemOutcome,
        original_task_name: Optional[str] = None,
        reason_code: Optional[str] = None,
        reason: Optional[str] = None,
        rerun_task_id: Optional[str] = None,
        rerun_task_name: Optional[str] = None,
    ) -> TaskActionItemDB:
        item = TaskActionItemDB(
            action_id=action.id,
            original_task_id=original_task_id,
            original_task_name=original_task_name,
            outcome=outcome.value,
            reason_code=reason_code,
            reason=reason,
            rerun_task_id=rerun_task_id,
            rerun_task_name=rerun_task_name,
        )
        self.session.add(item)
        self.session.flush()
        return item

    def _finalize_action(self, action: TaskActionDB) -> None:
        items = (
            self.session.query(TaskActionItemDB)
            .filter(TaskActionItemDB.action_id == action.id)
            .all()
        )
        counts = {outcome.value: 0 for outcome in TaskActionItemOutcome}
        for item in items:
            counts[item.outcome] = counts.get(item.outcome, 0) + 1

        failed = counts.get(TaskActionItemOutcome.FAILED.value, 0)
        skipped = counts.get(TaskActionItemOutcome.SKIPPED_UNAVAILABLE.value, 0)
        successful = (
            counts.get(TaskActionItemOutcome.CHANGED.value, 0) +
            counts.get(TaskActionItemOutcome.NOOP.value, 0) +
            counts.get(TaskActionItemOutcome.CREATED.value, 0)
        )

        action.item_total = len(items)
        action.item_changed = counts.get(TaskActionItemOutcome.CHANGED.value, 0)
        action.item_noop = counts.get(TaskActionItemOutcome.NOOP.value, 0)
        action.item_created = counts.get(TaskActionItemOutcome.CREATED.value, 0)
        action.item_skipped = skipped
        action.item_failed = failed
        action.completed_at = datetime.now(timezone.utc)
        action.summary = {
            "outcomes": counts,
            "created_reruns": action.item_created,
        }

        if failed == 0 and skipped == 0:
            action.status = TaskActionStatus.COMPLETED.value
        elif successful > 0:
            action.status = TaskActionStatus.PARTIAL_SUCCESS.value
        else:
            action.status = TaskActionStatus.FAILED.value

    def _action_to_summary(self, action: TaskActionDB) -> TaskActionSummary:
        return TaskActionSummary(
            id=action.id,
            action_type=TaskActionType(action.action_type),
            status=TaskActionStatus(action.status),
            initiated_by_user_id=action.initiated_by_user_id,
            initiated_by=action.initiated_by,
            initiated_session_id=action.initiated_session_id,
            created_at=action.created_at,
            started_at=action.started_at,
            completed_at=action.completed_at,
            original_task_ids=action.original_task_ids or [],
            selection_size=action.selection_size or 0,
            item_total=action.item_total or 0,
            item_changed=action.item_changed or 0,
            item_noop=action.item_noop or 0,
            item_created=action.item_created or 0,
            item_skipped=action.item_skipped or 0,
            item_failed=action.item_failed or 0,
            summary=action.summary or {},
        )

    def _item_to_model(
        self,
        item: TaskActionItemDB,
        rerun_task: Optional[TaskEvent] = None,
    ) -> TaskActionItem:
        return TaskActionItem(
            id=item.id,
            action_id=item.action_id,
            original_task_id=item.original_task_id,
            original_task_name=item.original_task_name,
            outcome=TaskActionItemOutcome(item.outcome),
            reason_code=item.reason_code,
            reason=item.reason,
            rerun_task_id=item.rerun_task_id,
            rerun_task_name=item.rerun_task_name,
            rerun_task=rerun_task,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    def _rerun_lifecycle_counts(self, tasks: Iterable[TaskEvent]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for task in tasks:
            event_type = task.event_type or "unknown"
            counts[event_type] = counts.get(event_type, 0) + 1
        return counts

    def _broadcast(self, detail: TaskActionDetail) -> None:
        if not self.connection_manager:
            return
        event = TaskActionWebSocketEvent(**detail.model_dump())
        queue_method = getattr(self.connection_manager, "queue_task_action_broadcast", None)
        if queue_method:
            queue_method(event)
