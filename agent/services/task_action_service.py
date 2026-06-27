"""Service for persisted user-initiated task actions."""

from __future__ import annotations

# ruff: noqa: UP006, UP007
import ast
import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from sqlalchemy import case, func
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
    RerunInputBaseline,
    RerunInputIssue,
    RerunKind,
    RerunPreflightItem,
    RerunPreflightResponse,
    RerunReviewState,
    RerunSubmissionTarget,
    RerunSubmitDecision,
    RerunSubmitItem,
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
from utils.payload_sanitizer import contains_placeholder, find_placeholder_paths

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
        replayable_count = sum(
            1 for item in items if item.review_state == RerunReviewState.REPLAYABLE
        )
        repairable_count = sum(
            1 for item in items if item.review_state == RerunReviewState.REPAIRABLE
        )
        blocked_count = sum(
            1 for item in items if item.review_state == RerunReviewState.BLOCKED
        )
        return RerunPreflightResponse(
            total=len(items),
            ready_count=ready_count,
            unavailable_count=len(items) - ready_count,
            replayable_count=replayable_count,
            repairable_count=repairable_count,
            blocked_count=blocked_count,
            max_selection_size=self.max_selection_size,
            items=items,
        )

    def submit_rerun_review(
        self,
        *,
        items: Sequence[RerunSubmitItem],
        initiated_by: Optional[str] = None,
        initiated_by_user_id: Optional[str] = None,
        initiated_session_id: Optional[str] = None,
    ) -> TaskActionDetail:
        submit_items = list(items)
        ids = self._normalize_task_ids([item.task_id for item in submit_items])
        self._validate_selection_size(ids)

        if len(ids) != len(submit_items):
            raise TaskActionValidationError("Each rerun review item must reference a unique task.")

        preflight_items = {
            item.task_id: self._preflight_rerun_item(item.task_id)
            for item in submit_items
        }
        prepared = []
        submit_count = 0

        for item in submit_items:
            preflight = preflight_items[item.task_id]
            if not preflight.fingerprint or item.fingerprint != preflight.fingerprint:
                raise TaskActionValidationError(
                    f"This review for task {item.task_id} is out of date. Refresh and review again."
                )

            if item.decision == RerunSubmitDecision.BLOCKED_SKIP:
                if preflight.review_state != RerunReviewState.BLOCKED:
                    raise TaskActionValidationError(
                        f"Task {item.task_id} can still be reviewed, so Kanchi cannot "
                        "skip it as unavailable."
                    )
                prepared.append((item, preflight, None, None, None))
                continue

            if item.decision == RerunSubmitDecision.USER_SKIP:
                if len(submit_items) == 1:
                    raise TaskActionValidationError(
                        "A single task that needs input cannot be skipped; cancel the "
                        "review instead."
                    )
                if preflight.review_state != RerunReviewState.REPAIRABLE:
                    raise TaskActionValidationError(
                        f"Only tasks that need input can be skipped by you. Task "
                        f"{item.task_id} does not need input."
                    )
                prepared.append((item, preflight, None, None, None))
                continue

            if item.decision != RerunSubmitDecision.SUBMIT:
                raise TaskActionValidationError("This rerun decision is not supported.")

            if preflight.review_state == RerunReviewState.BLOCKED:
                raise TaskActionValidationError(
                    f"Task {item.task_id} cannot be rerun from the captured data."
                )

            args, kwargs = self._validate_rerun_inputs(item)
            rerun_kind = self._classify_rerun_kind(preflight, args, kwargs)
            prepared.append((item, preflight, args, kwargs, rerun_kind))
            submit_count += 1

        if submit_count == 0:
            raise TaskActionValidationError("No selected tasks are ready to rerun.")

        now = datetime.now(timezone.utc)
        action = TaskActionDB(
            id=str(uuid.uuid4()),
            action_type=TaskActionType.RERUN.value,
            status=TaskActionStatus.RUNNING.value,
            initiated_by_user_id=initiated_by_user_id,
            initiated_by=initiated_by or "anonymous",
            initiated_session_id=initiated_session_id,
            created_at=now,
            started_at=now,
            original_task_ids=ids,
            selection_size=len(ids),
            item_total=len(ids),
            summary={},
        )
        self.session.add(action)
        self.session.flush()

        self._execute_rerun_submit_items(action, prepared, initiated_by=initiated_by)
        self._finalize_action(action)
        self.session.commit()
        detail = self.get_action(action.id)
        self._broadcast(detail)
        return detail

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
                    reason="Kanchi could not find this task.",
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
            args = list(preflight.baseline.args)
            kwargs = dict(preflight.baseline.kwargs)
            queue_name = preflight.target.queue or preflight.target.routing_key or "default"
            rerun_task_id = str(uuid.uuid4())

            try:
                self.monitor_instance.app.send_task(
                    latest.task_name,
                    args=args,
                    kwargs=kwargs,
                    queue=queue_name,
                    task_id=rerun_task_id,
                )
                self.session.add(TaskRerunRelationshipDB(
                    original_task_id=task_id,
                    rerun_task_id=rerun_task_id,
                    action_id=action.id,
                    created_by=initiated_by,
                ))
                self.session.flush()
                self._add_item(
                    action,
                    original_task_id=task_id,
                    original_task_name=latest.task_name,
                    outcome=TaskActionItemOutcome.CREATED,
                    rerun_task_id=rerun_task_id,
                    rerun_task_name=latest.task_name,
                    attempted_task_id=rerun_task_id,
                    submitted_args=args,
                    submitted_kwargs=kwargs,
                    rerun_kind=RerunKind.REPLAY,
                    review_fingerprint=preflight.fingerprint,
                    target_queue=queue_name,
                )
            except Exception as exc:  # pylint: disable=broad-except
                logger.error("Failed to rerun task %s: %s", task_id, exc, exc_info=True)
                self._add_item(
                    action,
                    original_task_id=task_id,
                    original_task_name=latest.task_name,
                    outcome=TaskActionItemOutcome.FAILED,
                    reason_code="send_failed",
                    reason=str(exc),
                    attempted_task_id=rerun_task_id,
                    submitted_args=args,
                    submitted_kwargs=kwargs,
                    rerun_kind=RerunKind.REPLAY,
                    review_fingerprint=preflight.fingerprint,
                    target_queue=queue_name,
                )

    def _execute_rerun_submit_items(
        self,
        action: TaskActionDB,
        prepared_items,
        *,
        initiated_by: Optional[str],
    ) -> None:
        for item, preflight, args, kwargs, rerun_kind in prepared_items:
            if item.decision == RerunSubmitDecision.USER_SKIP:
                self._add_item(
                    action,
                    original_task_id=item.task_id,
                    original_task_name=preflight.task_name,
                    outcome=TaskActionItemOutcome.USER_SKIPPED,
                    reason_code="user_skipped",
                    reason="Repairable task was intentionally skipped.",
                    skip_category="user_skipped",
                    review_fingerprint=preflight.fingerprint,
                )
                continue

            if item.decision == RerunSubmitDecision.BLOCKED_SKIP:
                self._add_item(
                    action,
                    original_task_id=item.task_id,
                    original_task_name=preflight.task_name,
                    outcome=TaskActionItemOutcome.BLOCKED_SKIPPED,
                    reason_code=preflight.reason_code,
                    reason=preflight.reason or "Task is blocked from manual rerun.",
                    skip_category="blocked_skipped",
                    review_fingerprint=preflight.fingerprint,
                )
                continue

            if not self._find_latest_row(item.task_id):
                self._add_item(
                    action,
                    original_task_id=item.task_id,
                    original_task_name=preflight.task_name,
                    outcome=TaskActionItemOutcome.FAILED,
                    reason_code="task_not_found",
                    reason="Kanchi could not find this task before sending the rerun.",
                    submitted_args=args,
                    submitted_kwargs=kwargs,
                    rerun_kind=rerun_kind,
                    review_fingerprint=preflight.fingerprint,
                )
                continue

            queue_name = preflight.target.queue or preflight.target.routing_key or "default"
            attempted_task_id = str(uuid.uuid4())
            try:
                self.monitor_instance.app.send_task(
                    preflight.target.task_name,
                    args=args,
                    kwargs=kwargs,
                    queue=queue_name,
                    task_id=attempted_task_id,
                )
                self.session.add(TaskRerunRelationshipDB(
                    original_task_id=item.task_id,
                    rerun_task_id=attempted_task_id,
                    action_id=action.id,
                    created_by=initiated_by,
                ))
                self.session.flush()
                self._add_item(
                    action,
                    original_task_id=item.task_id,
                    original_task_name=preflight.task_name,
                    outcome=TaskActionItemOutcome.CREATED,
                    rerun_task_id=attempted_task_id,
                    rerun_task_name=preflight.target.task_name,
                    attempted_task_id=attempted_task_id,
                    submitted_args=args,
                    submitted_kwargs=kwargs,
                    rerun_kind=rerun_kind,
                    review_fingerprint=preflight.fingerprint,
                    target_queue=queue_name,
                )
            except Exception as exc:  # pylint: disable=broad-except
                logger.error("Failed to rerun task %s: %s", item.task_id, exc, exc_info=True)
                self._add_item(
                    action,
                    original_task_id=item.task_id,
                    original_task_name=preflight.task_name,
                    outcome=TaskActionItemOutcome.FAILED,
                    reason_code="send_failed",
                    reason=str(exc),
                    attempted_task_id=attempted_task_id,
                    submitted_args=args,
                    submitted_kwargs=kwargs,
                    rerun_kind=rerun_kind,
                    review_fingerprint=preflight.fingerprint,
                    target_queue=queue_name,
                )

    def _preflight_rerun_item(self, task_id: str) -> RerunPreflightItem:
        latest = self._find_latest_row(task_id)
        if not latest:
            item = RerunPreflightItem(
                task_id=task_id,
                ready=False,
                review_state=RerunReviewState.BLOCKED,
                reason_code=RerunUnavailableReason.TASK_NOT_FOUND.value,
                reason="Kanchi could not find this task.",
            )
            item.fingerprint = self._fingerprint_preflight_item(item)
            return item

        if not latest.task_name or latest.task_name == "unknown":
            item = RerunPreflightItem(
                task_id=task_id,
                task_name=latest.task_name,
                ready=False,
                review_state=RerunReviewState.BLOCKED,
                reason_code=RerunUnavailableReason.MISSING_TASK_NAME.value,
                reason="Kanchi does not have the original task name.",
                task=self._row_to_task_event(latest),
                target=self._build_submission_target(latest),
            )
            item.fingerprint = self._fingerprint_preflight_item(item)
            return item

        if not self.monitor_instance or not getattr(self.monitor_instance, "app", None):
            item = RerunPreflightItem(
                task_id=task_id,
                task_name=latest.task_name,
                ready=False,
                review_state=RerunReviewState.BLOCKED,
                reason_code=RerunUnavailableReason.MONITOR_UNAVAILABLE.value,
                reason="Celery monitor is not available.",
                task=self._row_to_task_event(latest),
                target=self._build_submission_target(latest),
            )
            item.fingerprint = self._fingerprint_preflight_item(item)
            return item

        required_replacements: List[RerunInputIssue] = []
        try:
            baseline = self._resolve_rerun_baseline(latest)
        except ValueError:
            baseline = RerunInputBaseline(
                args=[],
                kwargs={},
                source="unparseable_observed_task_inputs",
                source_version=self._row_source_version(latest),
            )
            required_replacements.append(RerunInputIssue(
                path="$",
                reason_code=RerunUnavailableReason.UNPARSEABLE_PAYLOAD.value,
                message="Kanchi could not read the captured task inputs.",
            ))

        for path in find_placeholder_paths({
            "args": baseline.args,
            "kwargs": baseline.kwargs,
        }):
            required_replacements.append(RerunInputIssue(
                path=path,
                reason_code=RerunUnavailableReason.TRUNCATED_PAYLOAD.value,
                message=(
                    "Replace the truncated value, or set it to JSON null if that is "
                    "intentional."
                ),
            ))

        if required_replacements:
            item = RerunPreflightItem(
                task_id=task_id,
                task_name=latest.task_name,
                ready=False,
                review_state=RerunReviewState.REPAIRABLE,
                reason_code=required_replacements[0].reason_code,
                reason="Some captured inputs need your review before Kanchi can rerun this task.",
                task=self._row_to_task_event(latest),
                baseline=baseline,
                target=self._build_submission_target(latest),
                required_replacements=required_replacements,
            )
            item.fingerprint = self._fingerprint_preflight_item(item)
            return item

        item = RerunPreflightItem(
            task_id=task_id,
            task_name=latest.task_name,
            ready=True,
            review_state=RerunReviewState.REPLAYABLE,
            task=self._row_to_task_event(latest),
            baseline=baseline,
            target=self._build_submission_target(latest),
        )
        item.fingerprint = self._fingerprint_preflight_item(item)
        return item

    def _build_submission_target(self, row) -> RerunSubmissionTarget:
        return RerunSubmissionTarget(
            task_name=getattr(row, "task_name", None),
            queue=getattr(row, "queue", None) or getattr(row, "routing_key", None) or "default",
            routing_key=getattr(row, "routing_key", None) or "default",
            exchange=getattr(row, "exchange", None) or "",
        )

    def _resolve_rerun_baseline(self, row) -> RerunInputBaseline:
        submitted_item = (
            self.session.query(TaskActionItemDB)
            .filter(
                TaskActionItemDB.rerun_task_id == row.task_id,
                TaskActionItemDB.outcome == TaskActionItemOutcome.CREATED.value,
                TaskActionItemDB.submitted_args.isnot(None),
                TaskActionItemDB.submitted_kwargs.isnot(None),
            )
            .order_by(TaskActionItemDB.created_at.desc(), TaskActionItemDB.id.desc())
            .first()
        )
        if submitted_item:
            return RerunInputBaseline(
                args=self._as_args_list(submitted_item.submitted_args),
                kwargs=self._as_kwargs_dict(submitted_item.submitted_kwargs),
                source="submitted_rerun_inputs",
                source_version=f"task_action_item:{submitted_item.id}:{submitted_item.updated_at}",
            )

        args, kwargs = self._resolve_call_signature(row)
        return RerunInputBaseline(
            args=list(args),
            kwargs=dict(kwargs),
            source="observed_task_inputs",
            source_version=self._row_source_version(row),
        )

    def _row_source_version(self, row) -> str:
        row_id = getattr(row, "event_id", None) or getattr(row, "id", None) or ""
        timestamp = getattr(row, "timestamp", None)
        return f"{row.__class__.__name__}:{row_id}:{timestamp}"

    def _fingerprint_preflight_item(self, item: RerunPreflightItem) -> str:
        payload = {
            "task_id": item.task_id,
            "task_name": item.task_name,
            "review_state": item.review_state.value,
            "target": item.target.model_dump(),
            "baseline": item.baseline.model_dump(),
            "required_replacements": [
                issue.model_dump() for issue in item.required_replacements
            ],
        }
        encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def _validate_rerun_inputs(self, item: RerunSubmitItem) -> Tuple[List[Any], Dict[str, Any]]:
        if item.args is None or item.kwargs is None:
            raise TaskActionValidationError(
                f"Task {item.task_id} needs both positional and keyword arguments."
            )
        if not isinstance(item.args, list):
            raise TaskActionValidationError(
                f"Task {item.task_id} positional arguments must be a JSON array."
            )
        if not isinstance(item.kwargs, dict):
            raise TaskActionValidationError(
                f"Task {item.task_id} keyword arguments must be a JSON object."
            )

        args = self._json_round_trip(
            item.args,
            f"Task {item.task_id} positional arguments",
        )
        kwargs = self._json_round_trip(
            item.kwargs,
            f"Task {item.task_id} keyword arguments",
        )
        if not isinstance(args, list) or not isinstance(kwargs, dict):
            raise TaskActionValidationError(
                f"Task {item.task_id} needs positional arguments as an array and "
                "keyword arguments as an object."
            )
        if contains_placeholder(args) or contains_placeholder(kwargs):
            raise TaskActionValidationError(
                f"Task {item.task_id} still has values that need replacement."
            )
        return args, kwargs

    def _json_round_trip(self, value: Any, label: str) -> Any:
        try:
            return json.loads(json.dumps(value, allow_nan=False))
        except (TypeError, ValueError) as exc:
            raise TaskActionValidationError(f"{label} must be JSON-compatible.") from exc

    def _classify_rerun_kind(
        self,
        preflight: RerunPreflightItem,
        args: List[Any],
        kwargs: Dict[str, Any],
    ) -> RerunKind:
        if preflight.review_state == RerunReviewState.REPAIRABLE:
            return RerunKind.REPAIRED_OVERRIDE

        baseline_args = self._json_round_trip(preflight.baseline.args, "Baseline args")
        baseline_kwargs = self._json_round_trip(preflight.baseline.kwargs, "Baseline kwargs")
        if baseline_args == args and baseline_kwargs == kwargs:
            return RerunKind.REPLAY
        return RerunKind.EDITED_OVERRIDE

    def _as_args_list(self, value: Any) -> List[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return list(value)
        return [value]

    def _as_kwargs_dict(self, value: Any) -> Dict[str, Any]:
        if isinstance(value, dict):
            return value
        return {}

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

        if not args or not kwargs:
            recovered_args, recovered_kwargs = self._find_prior_call_signature_parts(
                row.task_id,
                need_args=not args,
                need_kwargs=not kwargs,
            )
            if not args and recovered_args:
                args = recovered_args
            if not kwargs and recovered_kwargs:
                kwargs = recovered_kwargs

        return args, kwargs

    def _find_prior_call_signature_parts(
        self,
        task_id: str,
        *,
        need_args: bool,
        need_kwargs: bool,
    ) -> Tuple[Optional[tuple], Optional[dict]]:
        if not need_args and not need_kwargs:
            return None, None

        rows = (
            self.session.query(TaskEventDB)
            .filter(TaskEventDB.task_id == task_id)
            .order_by(
                case((TaskEventDB.event_type == "task-received", 0), else_=1),
                TaskEventDB.timestamp.asc(),
                TaskEventDB.id.asc(),
            )
            .all()
        )

        recovered_args = None
        recovered_kwargs = None
        for event in rows:
            if need_args and recovered_args is None:
                candidate_args = self._parse_args(event.args)
                if candidate_args:
                    recovered_args = candidate_args

            if need_kwargs and recovered_kwargs is None:
                candidate_kwargs = self._parse_kwargs(event.kwargs)
                if candidate_kwargs:
                    recovered_kwargs = candidate_kwargs

            if (not need_args or recovered_args is not None) and (
                not need_kwargs or recovered_kwargs is not None
            ):
                break

        return recovered_args, recovered_kwargs

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
        attempted_task_id: Optional[str] = None,
        submitted_args: Optional[List[Any]] = None,
        submitted_kwargs: Optional[Dict[str, Any]] = None,
        rerun_kind: Optional[RerunKind] = None,
        skip_category: Optional[str] = None,
        review_fingerprint: Optional[str] = None,
        target_queue: Optional[str] = None,
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
            attempted_task_id=attempted_task_id,
            submitted_args=submitted_args,
            submitted_kwargs=submitted_kwargs,
            rerun_kind=rerun_kind.value if isinstance(rerun_kind, RerunKind) else rerun_kind,
            skip_category=skip_category,
            review_fingerprint=review_fingerprint,
            target_queue=target_queue,
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
        legacy_skipped = counts.get(TaskActionItemOutcome.SKIPPED_UNAVAILABLE.value, 0)
        user_skipped = counts.get(TaskActionItemOutcome.USER_SKIPPED.value, 0)
        blocked_skipped = counts.get(TaskActionItemOutcome.BLOCKED_SKIPPED.value, 0)
        skipped = legacy_skipped + user_skipped + blocked_skipped
        successful = (
            counts.get(TaskActionItemOutcome.CHANGED.value, 0) +
            counts.get(TaskActionItemOutcome.NOOP.value, 0) +
            counts.get(TaskActionItemOutcome.CREATED.value, 0)
        )
        rerun_kinds: Dict[str, int] = {}
        skip_categories: Dict[str, int] = {}
        for item in items:
            if item.rerun_kind:
                rerun_kinds[item.rerun_kind] = rerun_kinds.get(item.rerun_kind, 0) + 1
            if item.skip_category:
                skip_categories[item.skip_category] = skip_categories.get(item.skip_category, 0) + 1

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
            "rerun_kinds": rerun_kinds,
            "skip_categories": skip_categories,
            "user_skipped": user_skipped,
            "blocked_skipped": blocked_skipped,
            "send_failed": sum(
                1
                for item in items
                if item.outcome == TaskActionItemOutcome.FAILED.value
                and item.reason_code == "send_failed"
            ),
        }

        if failed == 0 and legacy_skipped == 0 and blocked_skipped == 0:
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
            attempted_task_id=item.attempted_task_id,
            submitted_args=item.submitted_args,
            submitted_kwargs=item.submitted_kwargs,
            rerun_kind=RerunKind(item.rerun_kind) if item.rerun_kind else None,
            skip_category=item.skip_category,
            review_fingerprint=item.review_fingerprint,
            target_queue=item.target_queue,
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
