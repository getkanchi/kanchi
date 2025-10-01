"""Event handling logic for Celery events."""

import asyncio
import logging
import threading
from typing import Optional

from models import TaskEvent, WorkerEvent
from services import TaskService, StatsService, WorkerService
from connection_manager import ConnectionManager
from database import DatabaseManager

logger = logging.getLogger(__name__)


class EventHandler:
    """Handle incoming Celery events and broadcast to clients."""
    
    def __init__(self, db_manager: DatabaseManager, connection_manager: ConnectionManager):
        self.db_manager = db_manager
        self.connection_manager = connection_manager
        self.recent_broadcast_cache = []
        self.max_broadcast_cache = 50
    
    async def handle_task_event(self, task_event: TaskEvent):
        """Handle a task event: save to DB, update stats, and broadcast."""
        try:
            # Save to database and update stats
            with self.db_manager.get_session() as session:
                task_service = TaskService(session)
                stats_service = StatsService(session)
                
                # Enrich with retry info before saving
                task_service._enrich_task_with_retry_info(task_event)
                
                # Save event
                task_service.save_task_event(task_event)
                
                # Update statistics
                stats_service.update_stats(task_event.event_type)
            
            # Keep small cache for immediate broadcasting
            self.recent_broadcast_cache.append(task_event)
            if len(self.recent_broadcast_cache) > self.max_broadcast_cache:
                self.recent_broadcast_cache.pop(0)
            
            # Broadcast to WebSocket clients
            await self.connection_manager.broadcast(task_event)
            
        except Exception as e:
            logger.error(f"Error handling task event: {e}", exc_info=True)
    
    async def handle_worker_event(self, worker_event: WorkerEvent):
        """Handle a worker event: save to DB and broadcast."""
        try:
            # Save to database
            with self.db_manager.get_session() as session:
                worker_service = WorkerService(session)
                worker_service.save_worker_event(worker_event)
            
            # Broadcast to connected clients
            await self._broadcast_worker_event(worker_event)
            
        except Exception as e:
            logger.error(f"Error handling worker event: {e}", exc_info=True)
    
    async def _broadcast_worker_event(self, worker_event: WorkerEvent):
        """Broadcast worker event to WebSocket clients."""
        message = worker_event.model_dump_json()
        disconnected = []
        
        for connection in self.connection_manager.active_connections:
            try:
                if self.connection_manager.client_modes.get(connection, 'live') == 'live':
                    await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting worker event to client: {e}")
                disconnected.append(connection)
        
        for connection in disconnected:
            self.connection_manager.disconnect(connection)
    
    def sync_handle_task_event(self, task_event: TaskEvent):
        """Sync wrapper for handling task events (for use in threads)."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.handle_task_event(task_event))
            loop.close()
        except Exception as e:
            logger.error(f"Error in sync task event handler: {e}")
    
    def sync_handle_worker_event(self, worker_event: WorkerEvent):
        """Sync wrapper for handling worker events (for use in threads)."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.handle_worker_event(worker_event))
            loop.close()
        except Exception as e:
            logger.error(f"Error in sync worker event handler: {e}")