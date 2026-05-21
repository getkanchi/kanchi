"""API routes for application configuration."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config import Config
from models import AppSetting, AppSettingUpdate, AppConfigSnapshot
from services import AppConfigService
from security.dependencies import get_auth_dependency

logger = logging.getLogger(__name__)


def create_router(app_state) -> APIRouter:
    """Create configuration router with dependency injection."""
    router = APIRouter(prefix="/api/config", tags=["config"])

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

    def get_config_service(session: Session = Depends(get_db)) -> AppConfigService:
        return AppConfigService(session)

    @router.get("", response_model=AppConfigSnapshot)
    async def get_config_snapshot(
        config_service: AppConfigService = Depends(get_config_service)
    ):
        """Get grouped application configuration with defaults applied."""
        return config_service.get_config_snapshot()

    @router.get("/settings", response_model=List[AppSetting])
    async def list_settings(config_service: AppConfigService = Depends(get_config_service)):
        """List all application settings."""
        return config_service.list_settings()

    @router.get("/settings/{key}", response_model=AppSetting)
    async def get_setting(
        key: str,
        config_service: AppConfigService = Depends(get_config_service)
    ):
        """Get a single application setting."""
        setting = config_service.get_setting(key)
        if not setting:
            raise HTTPException(status_code=404, detail="Setting not found")
        return setting

    @router.put("/settings/{key}", response_model=AppSetting)
    async def upsert_setting(
        key: str,
        payload: AppSettingUpdate,
        config_service: AppConfigService = Depends(get_config_service)
    ):
        """Create or update an application setting."""
        try:
            return config_service.upsert_setting(key, payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to upsert setting %s: %s", key, exc, exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to update setting") from exc

    @router.delete("/settings/{key}", status_code=204)
    async def delete_setting(
        key: str,
        config_service: AppConfigService = Depends(get_config_service)
    ):
        """Delete a setting (falls back to default)."""
        deleted = config_service.delete_setting(key)
        if not deleted:
            raise HTTPException(status_code=404, detail="Setting not found")
        return None

    return router
