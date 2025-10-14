"""WebSocket routes and related endpoints."""

import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any

from models import (
    ConnectionInfo, PongResponse, SubscriptionResponse, ModeChangedResponse,
    StoredEventsResponse, PingMessage, SubscribeMessage, SetModeMessage, 
    GetStoredMessage, TaskEventResponse
)

logger = logging.getLogger(__name__)


def _matches_filters(event_data: Any, filters: Dict[str, Any]) -> bool:
    """Check if event data matches the given filters."""
    if not filters:
        return True
    
    # Convert event data to dict if it's a Pydantic model
    if hasattr(event_data, 'model_dump'):
        event_dict = event_data.model_dump()
    elif hasattr(event_data, 'dict'):
        event_dict = event_data.dict()
    else:
        event_dict = event_data if isinstance(event_data, dict) else {}
    
    # Apply filters
    for filter_key, filter_value in filters.items():
        if filter_key in event_dict:
            event_value = event_dict[filter_key]
            # Support both exact match and contains for string fields
            if isinstance(filter_value, str) and isinstance(event_value, str):
                if filter_value.lower() not in event_value.lower():
                    return False
            elif event_value != filter_value:
                return False
        else:
            # If filter key doesn't exist in event, filter doesn't match
            return False
    
    return True


def create_router(app_state) -> APIRouter:
    """Create websocket router with dependency injection."""
    router = APIRouter(tags=["websocket"])


    @router.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time event streaming."""
        if not app_state.connection_manager:
            await websocket.close(code=1011, reason="Server not initialized")
            return
        
        await app_state.connection_manager.connect(websocket)
        
        welcome = ConnectionInfo(
            status="connected",
            timestamp=datetime.now(timezone.utc),
            message="Connected to Celery Event Monitor",
            total_connections=len(app_state.connection_manager.active_connections)
        )
        await app_state.connection_manager.send_personal_message(welcome.model_dump_json(), websocket)
        
        try:
            while True:
                data = await websocket.receive_text()
                
                try:
                    message = json.loads(data)
                    
                    if message.get('type') == 'ping':
                        pong_response = PongResponse(timestamp=datetime.now(timezone.utc))
                        await app_state.connection_manager.send_personal_message(pong_response.model_dump_json(), websocket)
                    
                    elif message.get('type') == 'subscribe':
                        filters = message.get('filters', {})
                        app_state.connection_manager.set_client_filters(websocket, filters)

                        response = SubscriptionResponse(
                            status="acknowledged",
                            filters=filters,
                            timestamp=datetime.now(timezone.utc)
                        )
                        await app_state.connection_manager.send_personal_message(response.model_dump_json(), websocket)
                    
                    elif message.get('type') == 'set_mode':
                        await handle_set_mode(websocket, message)
                    
                    elif message.get('type') == 'get_stored':
                        await handle_get_stored(websocket, message)
                    
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received: {data}")
        
        except WebSocketDisconnect:
            app_state.connection_manager.disconnect(websocket)


    async def handle_set_mode(websocket: WebSocket, message: Dict[str, Any]):
        """Handle set_mode WebSocket message."""
        mode = message.get('mode', 'live')
        app_state.connection_manager.set_client_mode(websocket, mode)
        
        events_sent = 0
        if mode == 'static' and app_state.db_manager:
            from services import TaskService, EnvironmentService
            with app_state.db_manager.get_session() as session:
                # Get active environment for filtering
                env_service = EnvironmentService(session)
                active_env = env_service.get_active_environment()

                task_service = TaskService(session, active_env=active_env)
                # Get recent events (will be filtered by active environment)
                recent_data = task_service.get_recent_events(limit=100, page=0)
                for event_data in recent_data["data"]:
                    filters = app_state.connection_manager.client_filters.get(websocket, {})
                    # Apply client filters
                    if _matches_filters(event_data, filters):
                        await app_state.connection_manager.send_personal_message(
                            event_data.model_dump_json(), 
                            websocket
                        )
                        events_sent += 1
        
        mode_response = ModeChangedResponse(
            mode=mode,
            timestamp=datetime.now(timezone.utc),
            events_count=events_sent if mode == 'static' else None
        )
        await app_state.connection_manager.send_personal_message(mode_response.model_dump_json(), websocket)


    async def handle_get_stored(websocket: WebSocket, message: Dict[str, Any]):
        """Handle get_stored WebSocket message."""
        limit = message.get('limit', 1000)
        events_sent = 0

        if app_state.db_manager:
            from services import TaskService, EnvironmentService
            with app_state.db_manager.get_session() as session:
                # Get active environment for filtering
                env_service = EnvironmentService(session)
                active_env = env_service.get_active_environment()

                task_service = TaskService(session, active_env=active_env)
                recent_data = task_service.get_recent_events(limit=limit, page=0)
                for event_data in recent_data["data"]:
                    filters = app_state.connection_manager.client_filters.get(websocket, {})
                    # Apply client filters
                    if _matches_filters(event_data, filters):
                        await app_state.connection_manager.send_personal_message(
                            event_data.model_dump_json(), 
                            websocket
                        )
                        events_sent += 1
        
        stored_response = StoredEventsResponse(
            count=events_sent,
            timestamp=datetime.now(timezone.utc)
        )
        await app_state.connection_manager.send_personal_message(stored_response.model_dump_json(), websocket)


    @router.get("/api/websocket/message-types")
    async def get_websocket_message_types():
        """Get schema information for WebSocket message types."""
        return {
            "incoming_messages": {
                "ping": PingMessage.model_json_schema(),
                "subscribe": SubscribeMessage.model_json_schema(),
                "set_mode": SetModeMessage.model_json_schema(),
                "get_stored": GetStoredMessage.model_json_schema()
            },
            "outgoing_messages": {
                "pong": PongResponse.model_json_schema(),
                "subscription_response": SubscriptionResponse.model_json_schema(),
                "mode_changed": ModeChangedResponse.model_json_schema(),
                "stored_events_sent": StoredEventsResponse.model_json_schema(),
                "connection_info": ConnectionInfo.model_json_schema(),
                "task_event": TaskEventResponse.model_json_schema()
            }
        }

    return router