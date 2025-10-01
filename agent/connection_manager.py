"""WebSocket connection management."""

import logging
from typing import List, Dict
from fastapi import WebSocket

from models import TaskEvent

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections and message broadcasting."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.client_filters: Dict[WebSocket, dict] = {}
        self.client_modes: Dict[WebSocket, str] = {}  # 'live' or 'static'
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.client_filters[websocket] = {}
        self.client_modes[websocket] = 'live'
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.client_filters:
            del self.client_filters[websocket]
        if websocket in self.client_modes:
            del self.client_modes[websocket]
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific client."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message to client: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, task_event: TaskEvent):
        """Broadcast a task event to all connected clients."""
        if not self.active_connections:
            return
        
        message = task_event.to_json()
        disconnected = []
        
        for connection in self.active_connections:
            try:
                if self.client_modes.get(connection, 'live') != 'live':
                    continue
                    
                filters = self.client_filters.get(connection, {})
                if self._should_send_to_client(task_event, filters):
                    await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)
        
        for connection in disconnected:
            self.disconnect(connection)
    
    def _should_send_to_client(self, task_event: TaskEvent, filters: dict) -> bool:
        """Check if an event should be sent to a client based on their filters."""
        if not filters:
            return True
        
        event_types = filters.get('event_types', [])
        if event_types and task_event.event_type not in event_types:
            return False
        
        task_names = filters.get('task_names', [])
        if task_names and task_event.task_name not in task_names:
            return False
        
        return True
    
    def set_client_filters(self, websocket: WebSocket, filters: dict):
        """Set filters for a specific client."""
        self.client_filters[websocket] = filters
    
    def set_client_mode(self, websocket: WebSocket, mode: str):
        """Set mode for a specific client."""
        if mode in ['live', 'static']:
            self.client_modes[websocket] = mode
            logger.info(f"Client mode set to: {mode}")