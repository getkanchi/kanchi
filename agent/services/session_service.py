"""Service for managing anonymous user sessions."""

import logging
from typing import Optional
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

from database import UserSessionDB
from models import UserSessionResponse, UserSessionCreate, UserSessionUpdate

logger = logging.getLogger(__name__)


class SessionService:
    """Service for user session operations."""

    def __init__(self, session: Session):
        self.session = session

    def get_or_create_session(
        self,
        session_id: str,
        *,
        user_id: Optional[str] = None,
        auth_provider: Optional[str] = None,
    ) -> UserSessionResponse:
        """
        Get an existing session or create a new one.
        This is the main entry point for session management.
        """
        session_db = self.session.query(UserSessionDB).filter(
            UserSessionDB.session_id == session_id
        ).first()

        if session_db:
            self._ensure_session_owner(session_db, user_id, auth_provider)
            session_db.last_active = datetime.now(timezone.utc)
            self.session.commit()
            self.session.refresh(session_db)
            logger.debug(f"Retrieved existing session: {session_id}")
        else:
            session_db = UserSessionDB(
                session_id=session_id,
                active_environment_id=None,
                preferences={},
                created_at=datetime.now(timezone.utc),
                last_active=datetime.now(timezone.utc),
                user_id=user_id,
                auth_provider=auth_provider,
            )
            self.session.add(session_db)
            self.session.commit()
            self.session.refresh(session_db)
            logger.info(f"Created new session: {session_id}")

        return UserSessionResponse.model_validate(session_db)

    def get_session(
        self,
        session_id: str,
        *,
        user_id: Optional[str] = None,
    ) -> Optional[UserSessionResponse]:
        """Get session by ID."""
        session_db = self.session.query(UserSessionDB).filter(
            UserSessionDB.session_id == session_id
        ).first()

        if session_db:
            self._ensure_session_owner(session_db, user_id, None)
            return UserSessionResponse.model_validate(session_db)
        return None

    def update_session(
        self,
        session_id: str,
        session_update: UserSessionUpdate,
        *,
        user_id: Optional[str] = None,
    ) -> Optional[UserSessionResponse]:
        """Update session preferences."""
        session_db = self.session.query(UserSessionDB).filter(
            UserSessionDB.session_id == session_id
        ).first()

        if not session_db:
            return None

        self._ensure_session_owner(session_db, user_id, None)

        if session_update.active_environment_id is not None:
            session_db.active_environment_id = session_update.active_environment_id

        if session_update.preferences is not None:
            current_prefs = session_db.preferences or {}
            current_prefs.update(session_update.preferences)
            session_db.preferences = current_prefs

        session_db.last_active = datetime.now(timezone.utc)

        self.session.commit()
        self.session.refresh(session_db)

        logger.info(f"Updated session: {session_id}")
        return UserSessionResponse.model_validate(session_db)

    def set_active_environment(
        self,
        session_id: str,
        environment_id: Optional[str],
        *,
        user_id: Optional[str] = None,
    ) -> Optional[UserSessionResponse]:
        """Set the active environment for a session."""
        session_db = self.session.query(UserSessionDB).filter(
            UserSessionDB.session_id == session_id
        ).first()

        if not session_db:
            return None

        self._ensure_session_owner(session_db, user_id, None)

        session_db.active_environment_id = environment_id
        session_db.last_active = datetime.now(timezone.utc)

        self.session.commit()
        self.session.refresh(session_db)

        logger.info(
            f"Set active environment for session {session_id}: {environment_id}"
        )
        return UserSessionResponse.model_validate(session_db)

    def get_active_environment_id(self, session_id: str, *, user_id: Optional[str] = None) -> Optional[str]:
        """Get the active environment ID for a session."""
        session_db = self.session.query(UserSessionDB).filter(
            UserSessionDB.session_id == session_id
        ).first()

        if session_db:
            self._ensure_session_owner(session_db, user_id, None)
            return session_db.active_environment_id
        return None

    def cleanup_inactive_sessions(self, days: int = 30) -> int:
        """
        Delete sessions that haven't been active for specified days.
        Returns the number of sessions deleted.
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        deleted_count = self.session.query(UserSessionDB).filter(
            UserSessionDB.last_active < cutoff_date
        ).delete()

        self.session.commit()

        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} inactive sessions")

        return deleted_count

    def delete_session(self, session_id: str, *, user_id: Optional[str] = None) -> bool:
        """Delete a session."""
        session_db = self.session.query(UserSessionDB).filter(
            UserSessionDB.session_id == session_id
        ).first()

        if not session_db:
            return False

        self._ensure_session_owner(session_db, user_id, None)

        self.session.delete(session_db)
        self.session.commit()

        logger.info(f"Deleted session: {session_id}")
        return True

    # ------------------------------------------------------------------
    def _ensure_session_owner(
        self,
        session_db: UserSessionDB,
        user_id: Optional[str],
        auth_provider: Optional[str],
    ) -> None:
        if user_id is None:
            return

        if session_db.user_id and session_db.user_id != user_id:
            raise PermissionError("Session belongs to a different user")

        if not session_db.user_id:
            session_db.user_id = user_id

        if auth_provider and not session_db.auth_provider:
            session_db.auth_provider = auth_provider
