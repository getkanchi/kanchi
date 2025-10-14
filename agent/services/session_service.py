"""Service for managing anonymous user sessions."""

import logging
from typing import Optional
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

from database import UserSessionDB
from models import UserSessionResponse, UserSessionCreate, UserSessionUpdate

logger = logging.getLogger(__name__)


class SessionService:
    """Service for anonymous user session operations."""

    def __init__(self, session: Session):
        self.session = session

    def get_or_create_session(self, session_id: str) -> UserSessionResponse:
        """
        Get an existing session or create a new one.
        This is the main entry point for session management.
        """
        session_db = self.session.query(UserSessionDB).filter(
            UserSessionDB.session_id == session_id
        ).first()

        if session_db:
            # Update last_active timestamp
            session_db.last_active = datetime.now(timezone.utc)
            self.session.commit()
            self.session.refresh(session_db)
            logger.debug(f"Retrieved existing session: {session_id}")
        else:
            # Create new session
            session_db = UserSessionDB(
                session_id=session_id,
                active_environment_id=None,
                preferences={},
                created_at=datetime.now(timezone.utc),
                last_active=datetime.now(timezone.utc)
            )
            self.session.add(session_db)
            self.session.commit()
            self.session.refresh(session_db)
            logger.info(f"Created new session: {session_id}")

        return UserSessionResponse.model_validate(session_db)

    def get_session(self, session_id: str) -> Optional[UserSessionResponse]:
        """Get session by ID."""
        session_db = self.session.query(UserSessionDB).filter(
            UserSessionDB.session_id == session_id
        ).first()

        if session_db:
            return UserSessionResponse.model_validate(session_db)
        return None

    def update_session(
        self,
        session_id: str,
        session_update: UserSessionUpdate
    ) -> Optional[UserSessionResponse]:
        """Update session preferences."""
        session_db = self.session.query(UserSessionDB).filter(
            UserSessionDB.session_id == session_id
        ).first()

        if not session_db:
            return None

        # Update fields
        if session_update.active_environment_id is not None:
            session_db.active_environment_id = session_update.active_environment_id

        if session_update.preferences is not None:
            # Merge preferences instead of replacing
            current_prefs = session_db.preferences or {}
            current_prefs.update(session_update.preferences)
            session_db.preferences = current_prefs

        # Update last_active
        session_db.last_active = datetime.now(timezone.utc)

        self.session.commit()
        self.session.refresh(session_db)

        logger.info(f"Updated session: {session_id}")
        return UserSessionResponse.model_validate(session_db)

    def set_active_environment(
        self,
        session_id: str,
        environment_id: Optional[str]
    ) -> Optional[UserSessionResponse]:
        """Set the active environment for a session."""
        session_db = self.session.query(UserSessionDB).filter(
            UserSessionDB.session_id == session_id
        ).first()

        if not session_db:
            return None

        session_db.active_environment_id = environment_id
        session_db.last_active = datetime.now(timezone.utc)

        self.session.commit()
        self.session.refresh(session_db)

        logger.info(
            f"Set active environment for session {session_id}: {environment_id}"
        )
        return UserSessionResponse.model_validate(session_db)

    def get_active_environment_id(self, session_id: str) -> Optional[str]:
        """Get the active environment ID for a session."""
        session_db = self.session.query(UserSessionDB).filter(
            UserSessionDB.session_id == session_id
        ).first()

        if session_db:
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

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        session_db = self.session.query(UserSessionDB).filter(
            UserSessionDB.session_id == session_id
        ).first()

        if not session_db:
            return False

        self.session.delete(session_db)
        self.session.commit()

        logger.info(f"Deleted session: {session_id}")
        return True
