"""API routes for session management."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session

from models import UserSessionResponse, UserSessionUpdate
from services import SessionService

logger = logging.getLogger(__name__)


def create_router(app_state) -> APIRouter:
    """Create session router with dependency injection."""
    router = APIRouter(prefix="/api/sessions", tags=["sessions"])

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
        db_session: Session = Depends(get_db)
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
            return service.get_or_create_session(session_id)
        except Exception as e:
            logger.error(f"Error initializing session: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/me", response_model=UserSessionResponse)
    async def get_current_session(
        session_id: str = Depends(get_session_id),
        db_session: Session = Depends(get_db)
    ):
        """Get current session info."""
        if not session_id:
            raise HTTPException(
                status_code=400,
                detail="session_id required in X-Session-Id header"
            )

        try:
            service = SessionService(db_session)
            session = service.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            return session
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting session: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @router.patch("/me", response_model=UserSessionResponse)
    async def update_current_session(
        session_update: UserSessionUpdate,
        session_id: str = Depends(get_session_id),
        db_session: Session = Depends(get_db)
    ):
        """Update current session preferences."""
        if not session_id:
            raise HTTPException(
                status_code=400,
                detail="session_id required in X-Session-Id header"
            )

        try:
            service = SessionService(db_session)
            session = service.update_session(session_id, session_update)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            return session
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating session: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/me/environment/{environment_id}", response_model=UserSessionResponse)
    async def set_session_environment(
        environment_id: str,
        session_id: str = Depends(get_session_id),
        db_session: Session = Depends(get_db)
    ):
        """Set active environment for current session."""
        if not session_id:
            raise HTTPException(
                status_code=400,
                detail="session_id required in X-Session-Id header"
            )

        try:
            service = SessionService(db_session)
            session = service.set_active_environment(session_id, environment_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            return session
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error setting environment: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @router.delete("/me/environment", response_model=UserSessionResponse)
    async def clear_session_environment(
        session_id: str = Depends(get_session_id),
        db_session: Session = Depends(get_db)
    ):
        """Clear active environment for current session (show all)."""
        if not session_id:
            raise HTTPException(
                status_code=400,
                detail="session_id required in X-Session-Id header"
            )

        try:
            service = SessionService(db_session)
            session = service.set_active_environment(session_id, None)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            return session
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error clearing environment: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    return router
