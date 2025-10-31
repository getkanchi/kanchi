"""API routes for action configuration management."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import (
    ActionConfigDefinition,
    ActionConfigCreateRequest,
    ActionConfigUpdateRequest
)
from services.action_config_service import ActionConfigService
from config import Config
from security.dependencies import get_auth_dependency


def create_router(app_state) -> APIRouter:
    """Create action config router with dependency injection."""
    router = APIRouter(prefix="/api/action-configs", tags=["action-configs"])

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

    @router.post("", response_model=ActionConfigDefinition, status_code=201)
    async def create_action_config(
        config_data: ActionConfigCreateRequest,
        session: Session = Depends(get_db)
    ):
        """Create a new action configuration (e.g., Slack webhook)."""
        config_service = ActionConfigService(session)
        config = config_service.create_config(config_data)
        return config

    @router.get("", response_model=List[ActionConfigDefinition])
    async def list_action_configs(
        action_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        session: Session = Depends(get_db)
    ):
        """List all action configurations."""
        config_service = ActionConfigService(session)
        configs = config_service.list_configs(
            action_type=action_type,
            limit=limit,
            offset=offset
        )
        return configs

    @router.get("/{config_id}", response_model=ActionConfigDefinition)
    async def get_action_config(
        config_id: str,
        session: Session = Depends(get_db)
    ):
        """Get a specific action configuration."""
        config_service = ActionConfigService(session)
        config = config_service.get_config(config_id)

        if not config:
            raise HTTPException(status_code=404, detail="Action config not found")

        return config

    @router.put("/{config_id}", response_model=ActionConfigDefinition)
    async def update_action_config(
        config_id: str,
        updates: ActionConfigUpdateRequest,
        session: Session = Depends(get_db)
    ):
        """Update an action configuration."""
        config_service = ActionConfigService(session)
        config = config_service.update_config(config_id, updates)

        if not config:
            raise HTTPException(status_code=404, detail="Action config not found")

        return config

    @router.delete("/{config_id}", status_code=204)
    async def delete_action_config(
        config_id: str,
        session: Session = Depends(get_db)
    ):
        """Delete an action configuration."""
        config_service = ActionConfigService(session)
        success = config_service.delete_config(config_id)

        if not success:
            raise HTTPException(status_code=404, detail="Action config not found")

    return router
