"""Service layer for worker-related operations."""

import logging
from typing import List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import WorkerEventDB
from models import WorkerEvent, WorkerInfo
from constants import WORKER_STATUS_MAP

logger = logging.getLogger(__name__)


class WorkerService:
    """Service for managing worker events and information."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save_worker_event(self, worker_event: WorkerEvent) -> WorkerEventDB:
        """
        Save a worker event to the database.

        Args:
            worker_event: Worker event to save

        Returns:
            Saved database model

        Raises:
            Exception: If database operation fails
        """
        try:
            status = WORKER_STATUS_MAP.get(worker_event.event_type, 'unknown')

            worker_event_db = WorkerEventDB(
                hostname=worker_event.hostname,
                event_type=worker_event.event_type,
                timestamp=worker_event.timestamp,
                status=status,
                active_tasks=getattr(worker_event, 'active', None),
                processed=getattr(worker_event, 'processed', None)
            )

            self.session.add(worker_event_db)
            self.session.commit()
            return worker_event_db

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to save worker event for {worker_event.hostname}: {e}")
            raise

    def get_recent_worker_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent worker events.

        Args:
            limit: Maximum number of events to return

        Returns:
            List of worker event dictionaries
        """
        events_db = (
            self.session.query(WorkerEventDB)
            .order_by(desc(WorkerEventDB.timestamp))
            .limit(limit)
            .all()
        )
        return [event.to_dict() for event in events_db]
