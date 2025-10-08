"""Main FastAPI application for Celery Event Monitor."""

import logging
import threading
from typing import Optional
import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import Config
from database import DatabaseManager
from connection_manager import ConnectionManager
from event_handler import EventHandler
from monitor import CeleryEventMonitor
from worker_health_monitor import WorkerHealthMonitor

logger = logging.getLogger(__name__)


class ApplicationState:
    """Container for application state and dependencies."""
    def __init__(self):
        self.db_manager: Optional[DatabaseManager] = None
        self.connection_manager: Optional[ConnectionManager] = None
        self.event_handler: Optional[EventHandler] = None
        self.monitor_instance: Optional[CeleryEventMonitor] = None
        self.monitor_thread: Optional[threading.Thread] = None
        self.health_monitor: Optional[WorkerHealthMonitor] = None


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
    app = FastAPI(
        title="Celery Event Monitor",
        description="Real-time monitoring of Celery task events with WebSocket broadcasting",
        version="0.1.0",
        lifespan=lifespan
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from api.task_routes import create_router as create_task_router
    from api.worker_routes import create_router as create_worker_router
    from api.websocket_routes import create_router as create_websocket_router
    from api.log_routes import create_router as create_log_router
    from api.registry_routes import create_router as create_registry_router

    app.include_router(create_task_router(app_state))
    app.include_router(create_worker_router(app_state))
    app.include_router(create_websocket_router(app_state))
    app.include_router(create_log_router(app_state))
    app.include_router(create_registry_router(app_state))

    @app.get("/api/health")
    async def health_check():
        """Health check endpoint."""
        workers_count = len(app_state.monitor_instance.get_workers_info()) if app_state.monitor_instance else 0
        return {
            "status": "healthy",
            "monitor_running": app_state.monitor_thread.is_alive() if app_state.monitor_thread else False,
            "connections": len(app_state.connection_manager.active_connections) if app_state.connection_manager else 0,
            "workers": workers_count,
            "database_url": app_state.db_manager.engine.url.render_as_string(hide_password=True) if app_state.db_manager else None
        }

    return app


async def initialize_application():
    """Initialize all application components."""
    config = Config.from_env()

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
    
    app_state.event_handler = EventHandler(app_state.db_manager, app_state.connection_manager)
    
    start_monitor(config)
    
    start_health_monitor()


def start_monitor(config: Config):
    """Start the Celery event monitor."""
    if app_state.monitor_thread and app_state.monitor_thread.is_alive():
        logger.warning("Monitor already running")
        return
    
    logger.info(f"Starting Celery monitor with broker: {config.broker_url}")
    app_state.monitor_instance = CeleryEventMonitor(config.broker_url)
    
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
