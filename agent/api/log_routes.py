"""API routes for logging endpoints."""

import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException

from models import LogEntry
from config import Config


def create_router(app_state) -> APIRouter:
    """Create log router with dependency injection."""
    router = APIRouter(prefix="/api/logs", tags=["logs"])

    @router.post("/frontend")
    async def log_frontend_message(log_entry: LogEntry):
        """Receive log messages from frontend and write to unified log file (only in development mode)."""
        # Check if development mode is enabled
        config = Config.from_env()
        if not config.development_mode:
            return {
                "status": "disabled",
                "message": "Logging is only available in development mode",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        try:
            # Get the unified logger
            logger = logging.getLogger("kanchi.frontend")

            # Map log level string to logging level
            level_map = {
                "debug": logging.DEBUG,
                "info": logging.INFO,
                "warning": logging.WARNING,
                "warn": logging.WARNING,
                "error": logging.ERROR,
                "critical": logging.CRITICAL,
            }

            level = level_map.get(log_entry.level.lower(), logging.INFO)

            # Format the message with context if provided
            message = log_entry.message
            if log_entry.context:
                message = f"{message} | Context: {log_entry.context}"

            # Log with the appropriate level
            logger.log(level, message)

            return {
                "status": "success",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to log message: {str(e)}")

    return router
