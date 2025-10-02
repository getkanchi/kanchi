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

logger = logging.getLogger(__name__)


class ApplicationState:
    """Container for application state and dependencies."""
    def __init__(self):
        self.db_manager: Optional[DatabaseManager] = None
        self.connection_manager: Optional[ConnectionManager] = None
        self.event_handler: Optional[EventHandler] = None
        self.monitor_instance: Optional[CeleryEventMonitor] = None
        self.monitor_thread: Optional[threading.Thread] = None


# Application state instance
app_state = ApplicationState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await initialize_application()
    yield
    # Shutdown
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

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Import and include routers with dependencies
    from api.task_routes import create_router as create_task_router
    from api.worker_routes import create_router as create_worker_router
    from api.websocket_routes import create_router as create_websocket_router
    
    app.include_router(create_task_router(app_state))
    app.include_router(create_worker_router(app_state))
    app.include_router(create_websocket_router(app_state))

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
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format=config.log_format
    )
    
    # Initialize database
    app_state.db_manager = DatabaseManager(config.database_url)
    app_state.db_manager.create_tables()
    logger.info(f"Database initialized with URL: {config.database_url}")
    
    # Initialize stats if not exists
    with app_state.db_manager.get_session() as session:
        from database import TaskStatsDB
        stats = session.query(TaskStatsDB).filter_by(id=1).first()
        if not stats:
            stats = TaskStatsDB(id=1)
            session.add(stats)
            session.commit()
    
    # Initialize connection manager
    app_state.connection_manager = ConnectionManager()
    
    # Initialize event handler
    app_state.event_handler = EventHandler(app_state.db_manager, app_state.connection_manager)
    
    # Start Celery monitor
    start_monitor(config)


def start_monitor(config: Config):
    """Start the Celery event monitor."""
    if app_state.monitor_thread and app_state.monitor_thread.is_alive():
        logger.warning("Monitor already running")
        return
    
    logger.info(f"Starting Celery monitor with broker: {config.broker_url}")
    app_state.monitor_instance = CeleryEventMonitor(config.broker_url)
    
    # Set simplified callbacks
    app_state.monitor_instance.set_task_callback(app_state.event_handler.handle_task_event)
    app_state.monitor_instance.set_worker_callback(app_state.event_handler.handle_worker_event)
    
    # Start monitoring in a separate thread
    app_state.monitor_thread = threading.Thread(target=app_state.monitor_instance.start_monitoring)
    app_state.monitor_thread.daemon = True
    app_state.monitor_thread.start()


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


# Create the app instance for external use
app = create_app()


if __name__ == "__main__":
    start_server()