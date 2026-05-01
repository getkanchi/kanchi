"""Service layer for worker-related operations."""

import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import WorkerEventDB, TaskLatestDB, AppSettingDB
from models import WorkerEvent, QueueHealthSummary, QueueWorkerNote, WorkerOperationalSummary, QueueWorkerSurfaceResponse
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

    def get_queue_worker_surface(self, workers_data: Optional[Dict[str, Dict[str, Any]]] = None) -> QueueWorkerSurfaceResponse:
        workers_data = workers_data or {}
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)

        active_rows = (
            self.session.query(TaskLatestDB)
            .filter(TaskLatestDB.event_type.in_(['task-received', 'task-started']))
            .all()
        )
        recent_failures = (
            self.session.query(TaskLatestDB)
            .filter(TaskLatestDB.event_type == 'task-failed', TaskLatestDB.timestamp >= one_hour_ago)
            .all()
        )
        recent_successes = (
            self.session.query(TaskLatestDB)
            .filter(TaskLatestDB.event_type == 'task-succeeded', TaskLatestDB.timestamp >= one_hour_ago)
            .all()
        )

        queue_active_counts: Dict[str, int] = defaultdict(int)
        queue_workers: Dict[str, set[str]] = defaultdict(set)
        worker_active_queues: Dict[str, set[str]] = defaultdict(set)
        worker_active_counts: Dict[str, int] = defaultdict(int)
        for row in active_rows:
            queue_name = row.queue or row.routing_key or 'default'
            queue_active_counts[queue_name] += 1
            if row.hostname:
                queue_workers[queue_name].add(row.hostname)
                worker_active_queues[row.hostname].add(queue_name)
                worker_active_counts[row.hostname] += 1

        queue_failure_counts: Dict[str, int] = defaultdict(int)
        worker_failure_counts: Dict[str, int] = defaultdict(int)
        for row in recent_failures:
            queue_name = row.queue or row.routing_key or 'default'
            queue_failure_counts[queue_name] += 1
            if row.hostname:
                worker_failure_counts[row.hostname] += 1

        queue_throughput_counts: Dict[str, int] = defaultdict(int)
        for row in recent_successes:
            queue_name = row.queue or row.routing_key or 'default'
            queue_throughput_counts[queue_name] += 1

        queue_names = set(queue_active_counts) | set(queue_failure_counts) | set(queue_throughput_counts)
        queue_summaries: List[QueueHealthSummary] = []
        for queue_name in sorted(queue_names):
            active = queue_active_counts.get(queue_name, 0)
            failures = queue_failure_counts.get(queue_name, 0)
            throughput = queue_throughput_counts.get(queue_name, 0)
            if failures >= 3:
                status = 'critical'
                summary = f'{failures} failures in the last hour'
            elif active >= 5 and throughput == 0:
                status = 'warning'
                summary = f'{active} active tasks with no completions in the last hour'
            else:
                status = 'healthy'
                summary = f'{throughput} completions in the last hour'
            queue_summaries.append(QueueHealthSummary(
                queue_name=queue_name,
                active_tasks=active,
                recent_failures=failures,
                throughput_last_hour=throughput,
                workers=sorted(queue_workers.get(queue_name, set())),
                status=status,
                summary=summary,
            ))

        worker_summaries: List[WorkerOperationalSummary] = []
        for hostname, data in sorted(workers_data.items()):
            maintenance_state = data.get('maintenance_state') or data.get('maintenance')
            drain_state = data.get('drain_state') or data.get('drain')
            active_tasks = int(data.get('active', 0) or 0)
            recent_failures_count = worker_failure_counts.get(hostname, 0)
            summary = 'Online and processing normally'
            if data.get('status') == 'offline':
                summary = 'Offline or heartbeat missing'
            elif drain_state:
                summary = f'Drain state: {drain_state}'
            elif maintenance_state:
                summary = f'Maintenance state: {maintenance_state}'
            elif recent_failures_count:
                summary = f'{recent_failures_count} recent failures tied to this worker'
            worker_summaries.append(WorkerOperationalSummary(
                hostname=hostname,
                status=data.get('status', 'unknown'),
                active_tasks=active_tasks,
                processed_tasks=int(data.get('processed', 0) or 0),
                recent_failures=recent_failures_count,
                active_queues=sorted(worker_active_queues.get(hostname, set())),
                maintenance_state=maintenance_state,
                drain_state=drain_state,
                summary=summary,
            ))

        note_rows = (
            self.session.query(AppSettingDB)
            .filter(AppSettingDB.key.like('operator_notes.%'))
            .order_by(desc(AppSettingDB.updated_at))
            .all()
        )
        notes: List[QueueWorkerNote] = []
        for row in note_rows:
            value = row.value or {}
            entity_type = value.get('entity_type')
            entity_key = value.get('entity_key')
            note = value.get('note')
            if entity_type in {'queue', 'worker'} and entity_key and note:
                notes.append(QueueWorkerNote(
                    entity_type=entity_type,
                    entity_key=entity_key,
                    note=note,
                    author=value.get('author'),
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                ))

        return QueueWorkerSurfaceResponse(queues=queue_summaries, workers=worker_summaries, notes=notes)

    def save_operator_note(self, entity_type: str, entity_key: str, note: str, author: Optional[str] = None) -> QueueWorkerNote:
        key = f'operator_notes.{entity_type}.{entity_key}'
        existing = self.session.query(AppSettingDB).filter_by(key=key).first()
        value = {
            'entity_type': entity_type,
            'entity_key': entity_key,
            'note': note,
            'author': author,
        }
        if existing:
            existing.value = value
            existing.value_type = 'json'
            existing.category = 'operator_notes'
            existing.label = f'{entity_type}:{entity_key}'
            existing.description = 'Operator note for queue/worker incident context'
            row = existing
        else:
            row = AppSettingDB(
                key=key,
                value=value,
                value_type='json',
                category='operator_notes',
                label=f'{entity_type}:{entity_key}',
                description='Operator note for queue/worker incident context',
            )
            self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return QueueWorkerNote(
            entity_type=entity_type,
            entity_key=entity_key,
            note=note,
            author=author,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
