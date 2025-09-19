import asyncio
import websockets
import json
import logging
from typing import Set, Optional
from datetime import datetime
from models import TaskEvent

logger = logging.getLogger(__name__)


class WebSocketServer:
    """WebSocket server for broadcasting Celery events"""
    
    def __init__(self, host: str = 'localhost', port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.server: Optional[websockets.WebSocketServer] = None
        self._stop = False
        
    async def register_client(self, websocket: websockets.WebSocketServerProtocol):
        """Register a new WebSocket client"""
        self.clients.add(websocket)
        client_address = websocket.remote_address
        logger.info(f"Client connected: {client_address}")
        
        # Send welcome message
        welcome_msg = {
            "type": "connection",
            "status": "connected",
            "timestamp": datetime.now().isoformat(),
            "message": "Connected to Celery Event Monitor"
        }
        await websocket.send(json.dumps(welcome_msg))
        
    async def unregister_client(self, websocket: websockets.WebSocketServerProtocol):
        """Unregister a WebSocket client"""
        if websocket in self.clients:
            self.clients.remove(websocket)
            client_address = websocket.remote_address
            logger.info(f"Client disconnected: {client_address}")
    
    async def broadcast_event(self, task_event: TaskEvent):
        """Broadcast a task event to all connected clients"""
        if not self.clients:
            return
        
        message = task_event.to_json()
        
        # Send to all connected clients
        disconnected_clients = set()
        for client in self.clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            await self.unregister_client(client)
    
    def broadcast_event_sync(self, task_event: TaskEvent):
        """Synchronous wrapper for broadcasting events (called from Celery monitor thread)"""
        try:
            # Create a new event loop for this thread if needed
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Schedule the broadcast
            asyncio.create_task(self.broadcast_event(task_event))
        except Exception as e:
            logger.error(f"Error in sync broadcast: {e}")
    
    async def handle_client(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """Handle a WebSocket client connection"""
        await self.register_client(websocket)
        
        try:
            # Keep connection alive and handle any incoming messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    
                    # Handle ping/pong for keepalive
                    if data.get('type') == 'ping':
                        pong_msg = {
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        }
                        await websocket.send(json.dumps(pong_msg))
                    
                    # Handle subscription requests (for future filtering)
                    elif data.get('type') == 'subscribe':
                        # Could implement filtering by task name, event type, etc.
                        ack_msg = {
                            "type": "subscription",
                            "status": "acknowledged",
                            "filters": data.get('filters', {}),
                            "timestamp": datetime.now().isoformat()
                        }
                        await websocket.send(json.dumps(ack_msg))
                    
                    else:
                        logger.debug(f"Received message from client: {data}")
                        
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received: {message}")
                except Exception as e:
                    logger.error(f"Error handling client message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            logger.error(f"Error in client handler: {e}")
        finally:
            await self.unregister_client(websocket)
    
    async def start_server(self):
        """Start the WebSocket server"""
        logger.info(f"Starting WebSocket server on ws://{self.host}:{self.port}")
        
        self.server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port
        )
        
        logger.info(f"WebSocket server running on ws://{self.host}:{self.port}")
        
        # Keep server running
        await asyncio.Future()  # Run forever until cancelled
    
    def stop_server(self):
        """Stop the WebSocket server"""
        self._stop = True
        if self.server:
            self.server.close()
            logger.info("WebSocket server stopped")
