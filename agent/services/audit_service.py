"""Service for audit log persistence and querying."""

import logging
from typing import Any, Dict, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Query, Session

from database import AuditLogDB
from models import AuditLogActor, AuditLogEntry, AuditLogListResponse
from security.auth import AuthenticatedUser

logger = logging.getLogger(__name__)


class AuditLogService:
    """Manage audit log writes and queries."""

    def __init__(self, session: Session):
        self.session = session

    def record_entry(
        self,
        *,
        source: str,
        action_type: str,
        status: str,
        actor_type: str,
        actor_name: str,
        target_type: str,
        target_id: str,
        actor_id: Optional[str] = None,
        target_label: Optional[str] = None,
        task_id: Optional[str] = None,
        related_task_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        execution_id: Optional[int] = None,
        reason: Optional[str] = None,
        result_summary: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        commit: bool = True,
    ) -> AuditLogEntry:
        """Persist an audit entry and return the API model."""
        entry_db = AuditLogDB(
            source=source,
            action_type=action_type,
            status=status,
            actor_type=actor_type,
            actor_id=actor_id,
            actor_name=actor_name,
            target_type=target_type,
            target_id=target_id,
            target_label=target_label,
            task_id=task_id,
            related_task_id=related_task_id,
            workflow_id=workflow_id,
            execution_id=execution_id,
            reason=reason,
            result_summary=result_summary,
            details=details or {},
        )
        self.session.add(entry_db)

        if commit:
            self.session.commit()
            self.session.refresh(entry_db)
        else:
            self.session.flush()

        return self._db_to_entry(entry_db)

    def record_safe_entry(self, **kwargs) -> Optional[AuditLogEntry]:
        """Best-effort audit recording that never raises to the caller."""
        try:
            return self.record_entry(**kwargs)
        except Exception as exc:
            self.session.rollback()
            logger.error("Failed to persist audit log entry: %s", exc, exc_info=True)
            return None

    def list_entries(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        search: Optional[str] = None,
        source: Optional[str] = None,
        status: Optional[str] = None,
        action_type: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        task_id: Optional[str] = None,
        actor: Optional[str] = None,
    ) -> AuditLogListResponse:
        """Return filtered audit log entries."""
        query = self.session.query(AuditLogDB)
        query = self._apply_filters(
            query,
            search=search,
            source=source,
            status=status,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            workflow_id=workflow_id,
            task_id=task_id,
            actor=actor,
        )

        total = query.order_by(None).count()
        rows = (
            query.order_by(AuditLogDB.timestamp.desc(), AuditLogDB.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return AuditLogListResponse(total=total, items=[self._db_to_entry(row) for row in rows])

    def get_task_entries(self, task_id: str, *, limit: int = 50, offset: int = 0) -> AuditLogListResponse:
        """Get audit entries related to a task, including retry descendants."""
        return self.list_entries(task_id=task_id, limit=limit, offset=offset)

    def get_workflow_entries(
        self,
        workflow_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> AuditLogListResponse:
        """Get audit entries related to a workflow."""
        return self.list_entries(workflow_id=workflow_id, limit=limit, offset=offset)

    def _apply_filters(
        self,
        query: Query,
        *,
        search: Optional[str],
        source: Optional[str],
        status: Optional[str],
        action_type: Optional[str],
        target_type: Optional[str],
        target_id: Optional[str],
        workflow_id: Optional[str],
        task_id: Optional[str],
        actor: Optional[str],
    ) -> Query:
        if source:
            query = query.filter(AuditLogDB.source == source)

        if status:
            query = query.filter(AuditLogDB.status == status)

        if action_type:
            query = query.filter(AuditLogDB.action_type == action_type)

        if target_type:
            query = query.filter(AuditLogDB.target_type == target_type)

        if target_id:
            query = query.filter(AuditLogDB.target_id == target_id)

        if workflow_id:
            query = query.filter(AuditLogDB.workflow_id == workflow_id)

        if task_id:
            query = query.filter(
                or_(
                    AuditLogDB.task_id == task_id,
                    AuditLogDB.related_task_id == task_id,
                    and_(AuditLogDB.target_type == "task", AuditLogDB.target_id == task_id),
                )
            )

        if actor:
            pattern = f"%{actor.strip()}%"
            if pattern != "%%":
                query = query.filter(
                    or_(
                        AuditLogDB.actor_name.ilike(pattern),
                        AuditLogDB.actor_id.ilike(pattern),
                    )
                )

        if search:
            pattern = f"%{search.strip()}%"
            if pattern != "%%":
                query = query.filter(
                    or_(
                        AuditLogDB.action_type.ilike(pattern),
                        AuditLogDB.actor_name.ilike(pattern),
                        AuditLogDB.target_id.ilike(pattern),
                        AuditLogDB.target_label.ilike(pattern),
                        AuditLogDB.reason.ilike(pattern),
                        AuditLogDB.result_summary.ilike(pattern),
                    )
                )

        return query

    def _db_to_entry(self, row: AuditLogDB) -> AuditLogEntry:
        return AuditLogEntry(
            id=row.id,
            timestamp=row.timestamp,
            source=row.source,
            action_type=row.action_type,
            status=row.status,
            actor=AuditLogActor(
                type=row.actor_type,
                id=row.actor_id,
                name=row.actor_name,
            ),
            target_type=row.target_type,
            target_id=row.target_id,
            target_label=row.target_label,
            task_id=row.task_id,
            related_task_id=row.related_task_id,
            workflow_id=row.workflow_id,
            execution_id=row.execution_id,
            reason=row.reason,
            result_summary=row.result_summary,
            details=row.details or {},
        )


def get_actor_for_user(
    current_user: Optional[AuthenticatedUser],
    *,
    fallback_name: Optional[str] = None,
) -> Dict[str, Optional[str]]:
    """Normalize request user context into audit actor fields."""
    if isinstance(current_user, AuthenticatedUser):
        return {
            "actor_type": "user",
            "actor_id": current_user.id,
            "actor_name": current_user.email or current_user.name or fallback_name or current_user.id,
        }

    return {
        "actor_type": "operator",
        "actor_id": None,
        "actor_name": fallback_name or "anonymous",
    }
