"""Service layer for worker-related operations."""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import WorkerEventDB
from models import WorkerEvent, WorkerInfo


class WorkerService:
    """Service for managing worker events and information."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def save_worker_event(self, worker_event: WorkerEvent) -> WorkerEventDB:
        """Save a worker event to the database."""
        # Map event_type to status
        status_map = {
            'worker-online': 'online',
            'worker-offline': 'offline', 
            'worker-heartbeat': 'active'
        }
        status = status_map.get(worker_event.event_type, 'unknown')
        
        worker_event_db = WorkerEventDB(
            hostname=worker_event.hostname,
            event_type=worker_event.event_type,
            timestamp=worker_event.timestamp,
            status=status,
            active_tasks=worker_event.active if hasattr(worker_event, 'active') else None,
            processed=worker_event.processed if hasattr(worker_event, 'processed') else None
        )
        self.session.add(worker_event_db)
        self.session.commit()
        return worker_event_db
    
    def get_recent_worker_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent worker events."""
        events_db = self.session.query(WorkerEventDB).order_by(desc(WorkerEventDB.timestamp)).limit(limit).all()
        return [event.to_dict() for event in events_db]