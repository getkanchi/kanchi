"""WebSocket connection management with async queue handling."""

import asyncio
import logging
from typing import Dict, List, Optional

from fastapi import WebSocket

from models import TaskEvent, WorkerEvent

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections with queued message broadcasting."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.client_filters: Dict[WebSocket, dict] = {}
        self.client_modes: Dict[WebSocket, str] = {}
        self.message_queue: Optional[asyncio.Queue] = None
        self._broadcast_task = None
        self._running = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def start_background_broadcaster(self):
        """Start the background task that processes queued messages."""
        if self._broadcast_task is None and not self._running:
            self._running = True
            self._loop = asyncio.get_event_loop()
            self.message_queue = asyncio.Queue()
            self._broadcast_task = asyncio.create_task(self._background_broadcaster())
            logger.info("Background broadcaster started")

    async def _background_broadcaster(self):
        """Background task that processes the message queue."""
        while self._running:
            try:
                # Use asyncio.Queue.get() with timeout to allow clean shutdown
                try:
                    message_type, data = await asyncio.wait_for(
                        self.message_queue.get(),
                        timeout=0.1
                    )

                    if message_type == "task":
                        await self._broadcast_task_event(data)
                    elif message_type == "worker":
                        await self._broadcast_worker_event(data)

                except asyncio.TimeoutError:
                    # No message available, continue loop
                    continue

            except Exception as e:
                logger.error(f"Error in background broadcaster: {e}", exc_info=True)
                await asyncio.sleep(0.1)

    async def stop_background_broadcaster(self):
        """Stop the background broadcaster."""
        self._running = False
        if self._broadcast_task:
            self._broadcast_task.cancel()
            try:
                await self._broadcast_task
            except asyncio.CancelledError:
                pass
            self._broadcast_task = None

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.client_filters[websocket] = {}
        self.client_modes[websocket] = "live"
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")

        # Start broadcaster if this is the first connection
        if len(self.active_connections) == 1:
            self.start_background_broadcaster()

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.client_filters:
            del self.client_filters[websocket]
        if websocket in self.client_modes:
            del self.client_modes[websocket]
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")

    def queue_broadcast(self, task_event: TaskEvent):
        """
        Queue a task event for broadcasting (thread-safe, called from sync context).

        Uses call_soon_threadsafe to safely schedule the put operation on the event loop.
        This prevents segfaults when daemon threads (Celery monitor, worker health monitor)
        try to broadcast events to the async WebSocket handler.
        """
        if self.active_connections and self._loop and self.message_queue:
            try:
                # Thread-safe way to put into asyncio.Queue from daemon thread
                self._loop.call_soon_threadsafe(
                    self.message_queue.put_nowait, ("task", task_event)
                )
            except Exception as e:
                logger.error(f"Error queuing task event: {e}", exc_info=True)

    def queue_worker_broadcast(self, worker_event: WorkerEvent):
        """
        Queue a worker event for broadcasting (thread-safe, called from sync context).

        Uses call_soon_threadsafe to safely schedule the put operation on the event loop.
        This prevents segfaults when daemon threads (Celery monitor, worker health monitor)
        try to broadcast events to the async WebSocket handler.
        """
        if self.active_connections and self._loop and self.message_queue:
            try:
                # Thread-safe way to put into asyncio.Queue from daemon thread
                self._loop.call_soon_threadsafe(
                    self.message_queue.put_nowait, ("worker", worker_event)
                )
            except Exception as e:
                logger.error(f"Error queuing worker event: {e}", exc_info=True)

    async def _broadcast_task_event(self, task_event: TaskEvent):
        """Broadcast a task event to all connected clients."""
        if not self.active_connections:
            return

        message = task_event.to_json()
        disconnected = []

        for connection in self.active_connections:
            try:
                if self.client_modes.get(connection, "live") != "live":
                    continue

                filters = self.client_filters.get(connection, {})
                if self._should_send_to_client(task_event, filters):
                    await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)

    async def _broadcast_worker_event(self, worker_event: WorkerEvent):
        """Broadcast worker event to WebSocket clients."""
        if not self.active_connections:
            return

        message = worker_event.model_dump_json()
        disconnected = []

        for connection in self.active_connections:
            try:
                if self.client_modes.get(connection, "live") == "live":
                    await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting worker event to client: {e}")
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)

    def _should_send_to_client(self, task_event: TaskEvent, filters: dict) -> bool:
        """Check if an event should be sent to a client based on their filters."""
        if not filters:
            return True

        event_types = filters.get("event_types", [])
        if event_types and task_event.event_type not in event_types:
            return False

        task_names = filters.get("task_names", [])
        if task_names and task_event.task_name not in task_names:
            return False

        return True

    def set_client_filters(self, websocket: WebSocket, filters: dict):
        """Set filters for a specific client."""
        self.client_filters[websocket] = filters

    def set_client_mode(self, websocket: WebSocket, mode: str):
        """Set mode for a specific client."""
        if mode in ["live", "static"]:
            self.client_modes[websocket] = mode
            logger.info(f"Client mode set to: {mode}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific client."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message to client: {e}")
            self.disconnect(websocket)
