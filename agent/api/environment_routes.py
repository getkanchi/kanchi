"""API routes for environment management."""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from models import EnvironmentResponse, EnvironmentCreate, EnvironmentUpdate
from services import EnvironmentService
from config import Config
from security.dependencies import get_auth_dependency

logger = logging.getLogger(__name__)


def create_router(app_state) -> APIRouter:
    """Create environment router with dependency injection."""
    router = APIRouter(prefix="/api/environments", tags=["environments"])

    config = app_state.config or Config.from_env()
    require_user_dep = get_auth_dependency(app_state, require=True)

    if config.auth_enabled:
        router.dependencies.append(Depends(require_user_dep))

    def get_db() -> Session:
        """FastAPI dependency for database sessions."""
        if not app_state.db_manager:
            raise HTTPException(status_code=500, detail="Database not initialized")
        with app_state.db_manager.get_session() as session:
            yield session

    @router.post("", response_model=EnvironmentResponse, status_code=201)
    async def create_environment(
        env_create: EnvironmentCreate,
        session: Session = Depends(get_db)
    ):
        """Create a new environment."""
        try:
            service = EnvironmentService(session)
            return service.create_environment(env_create)
        except Exception as e:
            logger.error(f"Error creating environment: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("", response_model=List[EnvironmentResponse])
    async def list_environments(session: Session = Depends(get_db)):
        """List all environments."""
        try:
            service = EnvironmentService(session)
            return service.list_environments()
        except Exception as e:
            logger.error(f"Error listing environments: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/{env_id}", response_model=EnvironmentResponse)
    async def get_environment(env_id: str, session: Session = Depends(get_db)):
        """Get environment by ID."""
        try:
            service = EnvironmentService(session)
            env = service.get_environment(env_id)
            if not env:
                raise HTTPException(status_code=404, detail="Environment not found")
            return env
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting environment: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @router.patch("/{env_id}", response_model=EnvironmentResponse)
    async def update_environment(
        env_id: str,
        env_update: EnvironmentUpdate,
        session: Session = Depends(get_db)
    ):
        """Update an environment."""
        try:
            service = EnvironmentService(session)
            env = service.update_environment(env_id, env_update)
            if not env:
                raise HTTPException(status_code=404, detail="Environment not found")
            return env
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating environment: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @router.delete("/{env_id}", status_code=204)
    async def delete_environment(env_id: str, session: Session = Depends(get_db)):
        """Delete an environment."""
        try:
            service = EnvironmentService(session)
            if not service.delete_environment(env_id):
                raise HTTPException(
                    status_code=400,
                    detail="Cannot delete environment (not found)"
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting environment: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    return router
