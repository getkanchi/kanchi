"""Main FastAPI application for Celery Event Monitor."""

import logging
import threading
from typing import Any, Dict, Optional
import uvicorn
from contextlib import asynccontextmanager
import sys
import platform
from datetime import datetime, timezone

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from config import Config
from database import DatabaseManager
from connection_manager import ConnectionManager
from event_handler import EventHandler
from monitor import CeleryEventMonitor
from worker_health_monitor import WorkerHealthMonitor
from security.auth import AuthManager
from security.dependencies import build_auth_dependencies, get_auth_dependency

logger = logging.getLogger(__name__)

# Track application start time for uptime calculation
APP_START_TIME = datetime.now(timezone.utc)


class ApplicationState:
    """Container for application state and dependencies."""
    def __init__(self):
        self.db_manager: Optional[DatabaseManager] = None
        self.connection_manager: Optional[ConnectionManager] = None
        self.event_handler: Optional[EventHandler] = None
        self.monitor_instance: Optional[CeleryEventMonitor] = None
        self.monitor_thread: Optional[threading.Thread] = None
        self.health_monitor: Optional[WorkerHealthMonitor] = None
        self.workflow_engine = None
        self.config: Optional[Config] = None
        self.auth_manager = None
        self.auth_dependencies = None


app_state = ApplicationState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await initialize_application()
    yield
    # Shutdown
    if app_state.health_monitor:
        app_state.health_monitor.stop()
    if app_state.connection_manager:
        await app_state.connection_manager.stop_background_broadcaster()
    if app_state.monitor_thread and app_state.monitor_thread.is_alive():
        logger.info("Shutting down monitor thread")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    config = Config.from_env()
    app_state.config = config

    app = FastAPI(
        title="Celery Event Monitor",
        description="Real-time monitoring of Celery task events with WebSocket broadcasting",
        version="0.1.0",
        lifespan=lifespan
    )

    allowed_origins = config.allowed_origins or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=config.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if config.allowed_hosts:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=config.allowed_hosts)

    from api.task_routes import create_router as create_task_router
    from api.worker_routes import create_router as create_worker_router
    from api.websocket_routes import create_router as create_websocket_router
    from api.log_routes import create_router as create_log_router
    from api.registry_routes import create_router as create_registry_router
    from api.environment_routes import create_router as create_environment_router
    from api.session_routes import create_router as create_session_router
    from api.workflow_routes import create_router as create_workflow_router
    from api.action_config_routes import create_router as create_action_config_router
    from api.auth_routes import create_router as create_auth_router

    app.include_router(create_task_router(app_state))
    app.include_router(create_worker_router(app_state))
    app.include_router(create_websocket_router(app_state))
    app.include_router(create_log_router(app_state))
    app.include_router(create_registry_router(app_state))
    app.include_router(create_environment_router(app_state))
    app.include_router(create_session_router(app_state))
    app.include_router(create_workflow_router(app_state))
    app.include_router(create_action_config_router(app_state))
    app.include_router(create_auth_router(app_state))

    require_user_dep = get_auth_dependency(app_state, require=True)

    def mask_broker_url(broker_url_full: Optional[str]) -> Optional[str]:
        if not broker_url_full:
            return None
        if '@' in broker_url_full:
            try:
                protocol, rest = broker_url_full.split('://', 1)
                if '@' in rest:
                    _, host_part = rest.split('@', 1)
                    return f"{protocol}://***@{host_part}"
                return broker_url_full
            except (ValueError, IndexError) as exc:
                logger.warning("Failed to mask broker URL: %s", exc)
                return broker_url_full
        return broker_url_full

    def collect_health_metrics(include_database: bool = False) -> Dict[str, Any]:
        workers_count = len(app_state.monitor_instance.get_workers_info()) if app_state.monitor_instance else 0
        uptime_seconds = int((datetime.now(timezone.utc) - APP_START_TIME).total_seconds())
        config_ref = app_state.config or Config.from_env()

        broker_url_full = None
        if app_state.monitor_instance and app_state.monitor_instance.broker_url:
            broker_url_full = app_state.monitor_instance.broker_url
        elif config_ref.broker_url:
            broker_url_full = config_ref.broker_url
        else:
            broker_url_full = "amqp://guest@localhost//"

        base_stats: Dict[str, Any] = {
            "status": "healthy",
            "monitor_running": app_state.monitor_thread.is_alive() if app_state.monitor_thread else False,
            "connections": len(app_state.connection_manager.active_connections) if app_state.connection_manager else 0,
            "workers": workers_count,
            "uptime_seconds": uptime_seconds,
            "python_version": sys.version.split()[0],
            "system": platform.system(),
            "platform": platform.platform(),
            "api_version": app.version,
            "development_mode": config_ref.development_mode,
            "log_level": config_ref.log_level,
            "broker_url": mask_broker_url(broker_url_full),
        }

        if include_database and app_state.db_manager:
            from sqlalchemy import text

            total_tasks = 0
            first_task_timestamp = None
            try:
                with app_state.db_manager.get_session() as session:
                    result = session.execute(
                        text("""
                            SELECT COUNT(DISTINCT task_id)
                            FROM task_events
                            WHERE event_type IN ('task-succeeded', 'task-failed', 'task-revoked')
                        """)
                    )
                    total_tasks = result.scalar() or 0

                    result = session.execute(text("SELECT MIN(timestamp) FROM task_events"))
                    first_task_timestamp = result.scalar()
            except Exception as exc:  # pylint: disable=broad-except
                logger.error("Error fetching task statistics: %s", exc)

            base_stats.update(
                {
                    "database_url": app_state.db_manager.engine.url.render_as_string(hide_password=True),
                    "total_tasks_processed": total_tasks,
                    "first_task_at": first_task_timestamp if first_task_timestamp else None,
                }
            )

        return base_stats

    @app.get("/api/health")
    async def health_check():
        """Public health endpoint without sensitive data."""
        return collect_health_metrics(include_database=False)

    @app.get("/api/health/details")
    async def health_details(current_user=Depends(require_user_dep)):
        """Detailed health information (authentication required when enabled)."""
        return collect_health_metrics(include_database=True)

    return app


async def initialize_application():
    """Initialize all application components."""
    config = Config.from_env()
    app_state.config = config

    # Set up unified logging to file (only in development mode)
    if config.development_mode:
        # Clean the log file on startup
        with open(config.log_file, 'w') as f:
            f.write('')

        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, config.log_level),
            format='%(asctime)s [BACKEND] %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(config.log_file),
                logging.StreamHandler()
            ]
        )

        # Configure frontend logger
        frontend_logger = logging.getLogger('kanchi.frontend')
        frontend_logger.setLevel(getattr(logging, config.log_level))
        # Create file handler with custom format for frontend logs
        fh = logging.FileHandler(config.log_file)
        fh.setFormatter(logging.Formatter('%(asctime)s [FRONTEND] %(levelname)s - %(message)s'))
        frontend_logger.addHandler(fh)
        frontend_logger.propagate = False  # Don't propagate to root logger

        logger.info("Development mode enabled - unified logging active")
    else:
        # Production mode - standard logging without file output
        logging.basicConfig(
            level=getattr(logging, config.log_level),
            format=config.log_format
        )

    app_state.db_manager = DatabaseManager(config.database_url)
    logger.info(f"Running database migrations for: {config.database_url}")
    app_state.db_manager.run_migrations()
    logger.info(f"Database migrations completed")

    app_state.connection_manager = ConnectionManager()

    # Initialize authentication helpers
    app_state.auth_manager = AuthManager(config)
    app_state.auth_dependencies = build_auth_dependencies(
        config,
        app_state.db_manager,
        app_state.auth_manager,
    )

    # Initialize workflow engine
    from services.workflow_engine import WorkflowEngine
    app_state.workflow_engine = WorkflowEngine(
        db_manager=app_state.db_manager,
        monitor_instance=None  # Will be set after monitor starts
    )

    # Pass workflow engine to event handler
    app_state.event_handler = EventHandler(
        app_state.db_manager,
        app_state.connection_manager,
        app_state.workflow_engine
    )

    start_monitor(config)

    # Set monitor instance on workflow engine after it's created
    app_state.workflow_engine.monitor_instance = app_state.monitor_instance

    start_health_monitor()


def start_monitor(config: Config):
    """Start the Celery event monitor."""
    if app_state.monitor_thread and app_state.monitor_thread.is_alive():
        logger.warning("Monitor already running")
        return
    
    logger.info(f"Starting Celery monitor with broker: {config.broker_url}")
    app_state.monitor_instance = CeleryEventMonitor(
        broker_url=config.broker_url,
        allow_pickle_serialization=config.enable_pickle_serialization,
    )
    
    app_state.monitor_instance.set_task_callback(app_state.event_handler.handle_task_event)
    app_state.monitor_instance.set_worker_callback(app_state.event_handler.handle_worker_event)
    
    app_state.monitor_thread = threading.Thread(target=app_state.monitor_instance.start_monitoring)
    app_state.monitor_thread.daemon = True
    app_state.monitor_thread.start()


def start_health_monitor():
    """Start the worker health monitor."""
    if app_state.health_monitor:
        logger.warning("Health monitor already running")
        return
        
    app_state.health_monitor = WorkerHealthMonitor(
        app_state.monitor_instance,
        app_state.db_manager,
        app_state.event_handler
    )
    app_state.health_monitor.start()


def start_server():
    """Start the FastAPI server."""
    config = Config.from_env()
    app = create_app()
    
    uvicorn.run(
        app,
        host=config.ws_host,
        port=config.ws_port,
        log_level=config.log_level.lower(),
        reload=False
    )


app = create_app()


if __name__ == "__main__":
    start_server()
