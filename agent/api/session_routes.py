"""API routes for session management."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session

from models import UserSessionResponse, UserSessionUpdate
from services import SessionService
from config import Config
from security.auth import AuthenticatedUser
from security.dependencies import get_auth_dependency

logger = logging.getLogger(__name__)


def create_router(app_state) -> APIRouter:
    """Create session router with dependency injection."""
    router = APIRouter(prefix="/api/sessions", tags=["sessions"])

    config = app_state.config or Config.from_env()
    require_user_dep = get_auth_dependency(app_state, require=True)
    optional_user_dep = get_auth_dependency(app_state, require=False)

    def get_db() -> Session:
        """FastAPI dependency for database sessions."""
        if not app_state.db_manager:
            raise HTTPException(status_code=500, detail="Database not initialized")
        with app_state.db_manager.get_session() as session:
            yield session

    def get_session_id(x_session_id: Optional[str] = Header(None)) -> Optional[str]:
        """Extract session ID from header."""
        return x_session_id

    @router.post("/init", response_model=UserSessionResponse, status_code=200)
    async def initialize_session(
        session_id: str = Depends(get_session_id),
        db_session: Session = Depends(get_db),
        current_user: Optional[AuthenticatedUser] = Depends(optional_user_dep)
    ):
        """
        Initialize or retrieve a session.
        If session_id is provided in header, retrieves existing or creates new.
        """
        if not session_id:
            raise HTTPException(
                status_code=400,
                detail="session_id required in X-Session-Id header"
            )

        try:
            service = SessionService(db_session)
            user_id = current_user.id if (config.auth_enabled and isinstance(current_user, AuthenticatedUser)) else None
            auth_provider = current_user.provider if (config.auth_enabled and isinstance(current_user, AuthenticatedUser)) else None
            return service.get_or_create_session(
                session_id,
                user_id=user_id,
                auth_provider=auth_provider,
            )
        except Exception as e:
            logger.error(f"Error initializing session: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/me", response_model=UserSessionResponse)
    async def get_current_session(
        session_id: str = Depends(get_session_id),
        db_session: Session = Depends(get_db),
        current_user: Optional[AuthenticatedUser] = Depends(optional_user_dep)
    ):
        """Get current session info."""
        if not session_id:
            raise HTTPException(
                status_code=400,
                detail="session_id required in X-Session-Id header"
            )

        if config.auth_enabled and not isinstance(current_user, AuthenticatedUser):
            raise HTTPException(status_code=401, detail="Authentication required")

        try:
            service = SessionService(db_session)
            user_id = current_user.id if isinstance(current_user, AuthenticatedUser) else None
            session = service.get_session(session_id, user_id=user_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            return session
        except HTTPException:
            raise
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except Exception as e:
            logger.error(f"Error getting session: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @router.patch("/me", response_model=UserSessionResponse)
    async def update_current_session(
        session_update: UserSessionUpdate,
        session_id: str = Depends(get_session_id),
        db_session: Session = Depends(get_db),
        current_user: Optional[AuthenticatedUser] = Depends(optional_user_dep)
    ):
        """Update current session preferences."""
        if not session_id:
            raise HTTPException(
                status_code=400,
                detail="session_id required in X-Session-Id header"
            )

        if config.auth_enabled and not isinstance(current_user, AuthenticatedUser):
            raise HTTPException(status_code=401, detail="Authentication required")

        try:
            service = SessionService(db_session)
            user_id = current_user.id if isinstance(current_user, AuthenticatedUser) else None
            session = service.update_session(session_id, session_update, user_id=user_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            return session
        except HTTPException:
            raise
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except Exception as e:
            logger.error(f"Error updating session: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/me/environment/{environment_id}", response_model=UserSessionResponse)
    async def set_session_environment(
        environment_id: str,
        session_id: str = Depends(get_session_id),
        db_session: Session = Depends(get_db),
        current_user: Optional[AuthenticatedUser] = Depends(optional_user_dep)
    ):
        """Set active environment for current session."""
        if not session_id:
            raise HTTPException(
                status_code=400,
                detail="session_id required in X-Session-Id header"
            )

        if config.auth_enabled and not isinstance(current_user, AuthenticatedUser):
            raise HTTPException(status_code=401, detail="Authentication required")

        try:
            service = SessionService(db_session)
            user_id = current_user.id if isinstance(current_user, AuthenticatedUser) else None
            session = service.set_active_environment(session_id, environment_id, user_id=user_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            return session
        except HTTPException:
            raise
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except Exception as e:
            logger.error(f"Error setting environment: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @router.delete("/me/environment", response_model=UserSessionResponse)
    async def clear_session_environment(
        session_id: str = Depends(get_session_id),
        db_session: Session = Depends(get_db),
        current_user: Optional[AuthenticatedUser] = Depends(optional_user_dep)
    ):
        """Clear active environment for current session (show all)."""
        if not session_id:
            raise HTTPException(
                status_code=400,
                detail="session_id required in X-Session-Id header"
            )

        if config.auth_enabled and not isinstance(current_user, AuthenticatedUser):
            raise HTTPException(status_code=401, detail="Authentication required")

        try:
            service = SessionService(db_session)
            user_id = current_user.id if isinstance(current_user, AuthenticatedUser) else None
            session = service.set_active_environment(session_id, None, user_id=user_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            return session
        except HTTPException:
            raise
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except Exception as e:
            logger.error(f"Error clearing environment: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    return router
