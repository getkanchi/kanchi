import json
import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from database import TaskProgressDB, TaskProgressLatestDB, TaskStepsDB
from models import TaskProgressEvent, TaskStepsEvent, StepDefinition
from utils.payload_sanitizer import sanitize_payload

logger = logging.getLogger(__name__)


def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class ProgressService:
    """Service for persisting and retrieving task progress and steps."""

    def __init__(self, session: Session):
        self.session = session

    def save_progress_event(self, progress_event: TaskProgressEvent) -> TaskProgressDB:
        try:
            meta, _ = sanitize_payload(progress_event.meta or {})
            db_event = TaskProgressDB(
                task_id=progress_event.task_id,
                task_name=progress_event.task_name,
                progress=progress_event.progress,
                step_key=progress_event.step_key,
                message=progress_event.message,
                meta=meta if isinstance(meta, dict) else {},
                timestamp=_ensure_utc(progress_event.timestamp),
            )
            self.session.add(db_event)
            self.session.flush()

            self._upsert_latest(db_event)

            self.session.commit()
            return db_event
        except Exception as exc:  # pylint: disable=broad-except
            self.session.rollback()
            logger.error("Failed to save progress event %s: %s", progress_event.task_id, exc)
            raise

    def save_steps_event(self, steps_event: TaskStepsEvent) -> TaskStepsDB:
        try:
            steps_data = [step.model_dump() for step in steps_event.steps]
            meta_steps, _ = sanitize_payload(steps_data)
            steps_json = meta_steps if isinstance(meta_steps, list) else []

            existing = self.session.query(TaskStepsDB).filter_by(task_id=steps_event.task_id).one_or_none()
            if existing:
                existing.steps = steps_json
                existing.task_name = steps_event.task_name
                existing.defined_at = _ensure_utc(steps_event.timestamp)
                record = existing
            else:
                record = TaskStepsDB(
                    task_id=steps_event.task_id,
                    task_name=steps_event.task_name,
                    steps=steps_json,
                    defined_at=_ensure_utc(steps_event.timestamp),
                )
                self.session.add(record)

            self.session.commit()
            return record
        except Exception as exc:  # pylint: disable=broad-except
            self.session.rollback()
            logger.error("Failed to save step definitions for %s: %s", steps_event.task_id, exc)
            raise

    def get_latest_progress(self, task_id: str) -> Optional[TaskProgressEvent]:
        latest = (
            self.session.query(TaskProgressLatestDB)
            .filter_by(task_id=task_id)
            .one_or_none()
        )
        if not latest:
            return None
        return TaskProgressEvent(
            task_id=latest.task_id,
            task_name=latest.task_name,
            progress=latest.progress,
            step_key=latest.step_key,
            message=latest.message,
            meta=latest.meta or {},
            timestamp=_ensure_utc(latest.updated_at) or datetime.now(timezone.utc),
        )

    def get_progress_history(self, task_id: str, limit: int = 100) -> List[TaskProgressEvent]:
        events = (
            self.session.query(TaskProgressDB)
            .filter_by(task_id=task_id)
            .order_by(TaskProgressDB.timestamp.desc())
            .limit(limit)
            .all()
        )
        return [
            TaskProgressEvent(
                task_id=e.task_id,
                task_name=e.task_name,
                progress=e.progress,
                step_key=e.step_key,
                message=e.message,
                meta=e.meta or {},
                timestamp=_ensure_utc(e.timestamp) or datetime.now(timezone.utc),
            )
            for e in events
        ]

    def get_steps(self, task_id: str) -> List[StepDefinition]:
        record = (
            self.session.query(TaskStepsDB)
            .filter_by(task_id=task_id)
            .one_or_none()
        )
        if not record:
            return []

        try:
            steps_raw = record.steps or []
            # Ensure proper dict/list structure
            if isinstance(steps_raw, str):
                steps_raw = json.loads(steps_raw)
            steps: List[StepDefinition] = []
            for step in steps_raw:
                if not isinstance(step, dict):
                    continue
                key = step.get("key")
                label = step.get("label")
                if not key or not label:
                    continue
                steps.append(
                    StepDefinition(
                        key=key,
                        label=label,
                        description=step.get("description"),
                        total=step.get("total"),
                        order=step.get("order"),
                    )
                )
            return steps
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to parse steps for task %s: %s", task_id, exc)
            return []

    def _upsert_latest(self, event_db: TaskProgressDB) -> None:
        existing = (
            self.session.query(TaskProgressLatestDB)
            .filter_by(task_id=event_db.task_id)
            .one_or_none()
        )

        if not existing:
            self.session.add(
                TaskProgressLatestDB(
                    task_id=event_db.task_id,
                    task_name=event_db.task_name,
                    progress=event_db.progress,
                    step_key=event_db.step_key,
                    message=event_db.message,
                    meta=event_db.meta,
                    updated_at=_ensure_utc(event_db.timestamp),
                )
            )
            return

        new_ts = _ensure_utc(event_db.timestamp)
        current_ts = _ensure_utc(existing.updated_at)

        if current_ts and new_ts and new_ts <= current_ts:
            return

        existing.task_name = event_db.task_name
        existing.progress = event_db.progress
        existing.step_key = event_db.step_key
        existing.message = event_db.message
        existing.meta = event_db.meta
        existing.updated_at = new_ts or datetime.now(timezone.utc)
