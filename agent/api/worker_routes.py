"""API routes for worker-related endpoints."""

from datetime import datetime, timezone
from typing import List, Optional, Literal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from services import WorkerService
from models import WorkerInfo, QueueWorkerSurfaceResponse, QueueWorkerNote
from config import Config
from security.dependencies import get_auth_dependency


def create_router(app_state) -> APIRouter:
    """Create worker router with dependency injection."""
    router = APIRouter(prefix="/api", tags=["workers"])

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

    class OperatorNoteRequest(BaseModel):
        entity_type: Literal['queue', 'worker']
        entity_key: str = Field(min_length=1, max_length=255)
        note: str = Field(min_length=1, max_length=4000)
        author: Optional[str] = Field(default=None, max_length=255)


    @router.get("/workers", response_model=List[WorkerInfo])
    async def get_workers():
        """Get information about all workers."""
        if not app_state.monitor_instance:
            return []

        workers_data = app_state.monitor_instance.get_workers_info()
        worker_list = []

        for hostname, data in workers_data.items():
            worker_info = WorkerInfo(
                hostname=hostname,
                status=data.get('status', 'unknown'),
                timestamp=data.get('timestamp', datetime.now(timezone.utc)),
                active_tasks=data.get('active', 0),
                processed_tasks=data.get('processed', 0),
                sw_ident=data.get('sw_ident'),
                sw_ver=data.get('sw_ver'),
                sw_sys=data.get('sw_sys'),
                loadavg=data.get('loadavg'),
                freq=data.get('freq')
            )
            worker_list.append(worker_info)

        return worker_list


    @router.get("/workers/events/recent")
    async def get_recent_worker_events(limit: int = 50, session: Session = Depends(get_db)):
        """Get recent worker events."""
        worker_service = WorkerService(session)
        return worker_service.get_recent_worker_events(limit)

    @router.get("/worker-operations", response_model=QueueWorkerSurfaceResponse)
    async def get_queue_worker_surface(session: Session = Depends(get_db)):
        """Get queue/worker operational summaries and contextual notes."""
        worker_service = WorkerService(session)
        workers_data = app_state.monitor_instance.get_workers_info() if app_state.monitor_instance else {}
        return worker_service.get_queue_worker_surface(workers_data)

    @router.post("/workers/notes", response_model=QueueWorkerNote)
    async def save_operator_note(payload: OperatorNoteRequest, session: Session = Depends(get_db)):
        """Create or update an operator note for a queue or worker."""
        worker_service = WorkerService(session)
        return worker_service.save_operator_note(
            entity_type=payload.entity_type,
            entity_key=payload.entity_key,
            note=payload.note,
            author=payload.author,
        )

    @router.get("/workers/{hostname}", response_model=WorkerInfo)
    async def get_worker(hostname: str):
        """Get information about a specific worker."""
        if not app_state.monitor_instance:
            raise HTTPException(status_code=404, detail="Monitor not initialized")

        workers_data = app_state.monitor_instance.get_workers_info()
        if hostname not in workers_data:
            raise HTTPException(status_code=404, detail="Worker not found")

        data = workers_data[hostname]
        return WorkerInfo(
            hostname=hostname,
            status=data.get('status', 'unknown'),
            timestamp=data.get('timestamp', datetime.now(timezone.utc)),
            active_tasks=data.get('active', 0),
            processed_tasks=data.get('processed', 0),
            sw_ident=data.get('sw_ident'),
            sw_ver=data.get('sw_ver'),
            sw_sys=data.get('sw_sys'),
            loadavg=data.get('loadavg'),
            freq=data.get('freq')
        )

    return router
