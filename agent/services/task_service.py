"""Service layer for task-related operations."""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, or_, and_, func

from database import TaskEventDB, TaskStatsDB, RetryRelationshipDB
from models import TaskEvent, TaskEventResponse, TaskStats


class TaskService:
    """Service for managing task events and statistics."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def save_task_event(self, task_event: TaskEvent) -> TaskEventDB:
        """Save a task event to the database."""
        task_event_db = TaskEventDB(
            task_id=task_event.task_id,
            task_name=task_event.task_name,
            event_type=task_event.event_type,
            timestamp=task_event.timestamp,
            hostname=task_event.hostname,
            worker_name=task_event.worker_name,
            queue=task_event.queue,
            exchange=task_event.exchange,
            routing_key=task_event.routing_key,
            root_id=task_event.root_id,
            parent_id=task_event.parent_id,
            args=task_event.args if isinstance(task_event.args, (list, dict)) else str(task_event.args),
            kwargs=task_event.kwargs if isinstance(task_event.kwargs, dict) else str(task_event.kwargs),
            retries=task_event.retries,
            eta=task_event.eta,
            expires=task_event.expires,
            result=task_event.result if isinstance(task_event.result, (list, dict)) else str(task_event.result) if task_event.result else None,
            runtime=task_event.runtime,
            exception=task_event.exception,
            traceback=task_event.traceback,
            retry_of=task_event.retry_of,
            retried_by=json.dumps(task_event.retried_by) if task_event.retried_by else None,
            is_retry=task_event.is_retry,
            has_retries=task_event.has_retries,
            retry_count=task_event.retry_count
        )
        self.session.add(task_event_db)
        self.session.commit()
        return task_event_db
    
    def get_task_events(self, task_id: str) -> List[TaskEvent]:
        """Get all events for a specific task."""
        events_db = self.session.query(TaskEventDB).filter_by(task_id=task_id).order_by(TaskEventDB.timestamp).all()
        return [self._db_to_task_event(event_db) for event_db in events_db]
    
    def get_recent_events(
        self,
        limit: int = 100,
        page: int = 0,
        aggregate: bool = True,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
        search: Optional[str] = None,
        filter_state: Optional[str] = None,
        filter_worker: Optional[str] = None,
        filter_task: Optional[str] = None,
        filter_queue: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get recent task events with filtering and pagination."""
        query = self.session.query(TaskEventDB)
        
        # Apply filters
        if filter_state:
            state_to_event_type = {
                'PENDING': 'task-sent',
                'RECEIVED': 'task-received',
                'RUNNING': 'task-started',
                'SUCCESS': 'task-succeeded',
                'FAILED': 'task-failed',
                'RETRY': 'task-retried',
                'REVOKED': 'task-revoked'
            }
            event_type_filter = state_to_event_type.get(filter_state.upper())
            if event_type_filter:
                query = query.filter(TaskEventDB.event_type == event_type_filter)
        
        if filter_worker:
            query = query.filter(TaskEventDB.hostname.ilike(f"%{filter_worker}%"))
        
        if filter_task:
            query = query.filter(TaskEventDB.task_name.ilike(f"%{filter_task}%"))
        
        if filter_queue:
            query = query.filter(TaskEventDB.routing_key.ilike(f"%{filter_queue}%"))
        
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    TaskEventDB.task_name.ilike(search_pattern),
                    TaskEventDB.task_id.ilike(search_pattern),
                    TaskEventDB.hostname.ilike(search_pattern),
                    TaskEventDB.event_type.ilike(search_pattern)
                )
            )
        
        # For aggregation, we need to get ALL events first, then aggregate, then paginate
        if aggregate:
            # Get all events for aggregation
            all_events_db = query.order_by(desc(TaskEventDB.timestamp)).all()
            
            # Convert to TaskEvent objects
            all_events = [self._db_to_task_event(event_db) for event_db in all_events_db]
            
            # Enrich with retry information
            for event in all_events:
                self._enrich_task_with_retry_info(event)
            
            # Apply aggregation
            aggregated_events = self._aggregate_task_events(all_events)
            
            # Apply sorting to aggregated events
            if sort_by:
                reverse = (sort_order == "desc")
                if sort_by == "task_name":
                    aggregated_events.sort(key=lambda e: e.task_name or "", reverse=reverse)
                elif sort_by == "event_type":
                    aggregated_events.sort(key=lambda e: e.event_type or "", reverse=reverse)
                elif sort_by == "timestamp":
                    aggregated_events.sort(key=lambda e: e.timestamp, reverse=reverse)
                elif sort_by == "runtime":
                    aggregated_events.sort(key=lambda e: e.runtime or 0, reverse=reverse)
                elif sort_by == "retries":
                    aggregated_events.sort(key=lambda e: e.retries or 0, reverse=reverse)
                elif sort_by == "hostname":
                    aggregated_events.sort(key=lambda e: e.hostname or "", reverse=reverse)
            
            # Calculate pagination for aggregated results
            total_events = len(aggregated_events)
            start_idx = page * limit
            end_idx = start_idx + limit
            events = aggregated_events[start_idx:end_idx]
        else:
            # Apply sorting for non-aggregated events
            if sort_by:
                sort_column = getattr(TaskEventDB, sort_by, None)
                if sort_column:
                    if sort_order == "desc":
                        query = query.order_by(desc(sort_column))
                    else:
                        query = query.order_by(asc(sort_column))
            else:
                query = query.order_by(desc(TaskEventDB.timestamp))
            
            # Get total count
            total_events = query.count()
            
            # Apply pagination
            start_idx = page * limit
            events_db = query.offset(start_idx).limit(limit).all()
            
            # Convert to TaskEvent objects
            events = [self._db_to_task_event(event_db) for event_db in events_db]
            
            # Enrich with retry information
            for event in events:
                self._enrich_task_with_retry_info(event)
        
        total_pages = (total_events + limit - 1) // limit if limit > 0 else 1
        
        return {
            "data": [TaskEventResponse.from_task_event(event) for event in events],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_events,
                "total_pages": total_pages,
                "has_next": page < total_pages - 1,
                "has_prev": page > 0
            }
        }
    
    def get_active_tasks(self) -> List[TaskEvent]:
        """Get currently active tasks."""
        # Find active tasks: latest event is started/received/sent and not finished
        latest_events = self.session.query(
            TaskEventDB.task_id,
            func.max(TaskEventDB.timestamp).label('max_timestamp')
        ).group_by(TaskEventDB.task_id).subquery()
        
        active_events_db = self.session.query(TaskEventDB).join(
            latest_events,
            and_(
                TaskEventDB.task_id == latest_events.c.task_id,
                TaskEventDB.timestamp == latest_events.c.max_timestamp
            )
        ).filter(
            TaskEventDB.event_type.in_(['task-started', 'task-received', 'task-sent'])
        ).all()
        
        events = [self._db_to_task_event(event_db) for event_db in active_events_db]
        
        for event in events:
            self._enrich_task_with_retry_info(event)
        
        return events
    
    def create_retry_relationship(self, original_task_id: str, new_task_id: str):
        """Create a retry relationship between tasks."""
        # Create or update retry relationship for new task
        new_retry_rel = RetryRelationshipDB(
            task_id=new_task_id,
            original_id=original_task_id,
            retry_chain=[original_task_id],
            total_retries=1
        )
        self.session.add(new_retry_rel)
        
        # Update parent task's retry relationship
        parent_rel = self.session.query(RetryRelationshipDB).filter_by(task_id=original_task_id).first()
        if parent_rel:
            if parent_rel.retry_chain:
                parent_rel.retry_chain.append(new_task_id)
            else:
                parent_rel.retry_chain = [new_task_id]
            parent_rel.total_retries += 1
        else:
            parent_rel = RetryRelationshipDB(
                task_id=original_task_id,
                original_id=original_task_id,
                retry_chain=[new_task_id],
                total_retries=1
            )
            self.session.add(parent_rel)
        
        self.session.commit()
    
    def _db_to_task_event(self, event_db: TaskEventDB) -> TaskEvent:
        """Convert database model to TaskEvent object."""
        return TaskEvent(
            task_id=event_db.task_id,
            task_name=event_db.task_name,
            event_type=event_db.event_type,
            timestamp=event_db.timestamp,
            hostname=event_db.hostname,
            worker_name=event_db.worker_name,
            queue=event_db.queue,
            exchange=event_db.exchange,
            routing_key=event_db.routing_key,
            root_id=event_db.root_id,
            parent_id=event_db.parent_id,
            args=event_db.args,
            kwargs=event_db.kwargs,
            retries=event_db.retries,
            eta=event_db.eta,
            expires=event_db.expires,
            result=event_db.result,
            runtime=event_db.runtime,
            exception=event_db.exception,
            traceback=event_db.traceback
        )
    
    def _enrich_task_with_retry_info(self, task_event: TaskEvent):
        """Enrich task event with retry relationship information."""
        retry_rel = self.session.query(RetryRelationshipDB).filter_by(task_id=task_event.task_id).first()
        if retry_rel:
            task_event.retry_of = retry_rel.original_id if retry_rel.original_id != task_event.task_id else None
            task_event.retried_by = retry_rel.retry_chain if retry_rel.retry_chain else []
            task_event.is_retry = retry_rel.original_id != task_event.task_id
            task_event.has_retries = len(retry_rel.retry_chain) > 0 if retry_rel.retry_chain else False
            task_event.retry_count = retry_rel.total_retries
        else:
            # Set default values if no retry relationship found
            task_event.retry_of = None
            task_event.retried_by = []
            task_event.is_retry = False
            task_event.has_retries = False
            task_event.retry_count = 0
    
    def _aggregate_task_events(self, events: List[TaskEvent]) -> List[TaskEvent]:
        """Aggregate task events by task_id, showing only the latest state per task."""
        task_aggregation = {}
        for event in events:
            task_id = event.task_id
            if task_id not in task_aggregation:
                task_aggregation[task_id] = []
            task_aggregation[task_id].append(event)
        
        aggregated_tasks = []
        
        for task_id, task_events in task_aggregation.items():
            task_events.sort(key=lambda e: e.timestamp)
            
            latest_event = task_events[-1]
            aggregated_task = TaskEvent(
                task_id=task_id,
                task_name=latest_event.task_name,
                event_type=latest_event.event_type,  # Use latest status
                timestamp=latest_event.timestamp,    # Use latest timestamp
                args=latest_event.args,
                kwargs=latest_event.kwargs,
                retries=latest_event.retries,
                eta=latest_event.eta,
                expires=latest_event.expires,
                hostname=latest_event.hostname,
                worker_name=latest_event.worker_name,
                queue=latest_event.queue,
                exchange=latest_event.exchange,
                routing_key=latest_event.routing_key,
                root_id=latest_event.root_id,
                parent_id=latest_event.parent_id,
                result=latest_event.result,
                runtime=latest_event.runtime,
                exception=latest_event.exception,
                traceback=latest_event.traceback,
                retry_of=latest_event.retry_of,
                retried_by=latest_event.retried_by,
                is_retry=latest_event.is_retry,
                has_retries=latest_event.has_retries,
                retry_count=latest_event.retry_count
            )
            
            aggregated_tasks.append(aggregated_task)
        
        aggregated_tasks.sort(key=lambda e: e.timestamp, reverse=True)
        return aggregated_tasks


class StatsService:
    """Service for managing task statistics."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_stats(self) -> TaskStats:
        """Get current task statistics."""
        stats = self.session.query(TaskStatsDB).filter_by(id=1).first()
        if not stats:
            return TaskStats()
        
        return TaskStats(
            total_tasks=stats.total_tasks,
            succeeded=stats.succeeded,
            failed=stats.failed,
            pending=stats.pending,
            retried=stats.retried,
            active=stats.active
        )
    
    def update_stats(self, event_type: str):
        """Update statistics based on event type."""
        stats = self.session.query(TaskStatsDB).filter_by(id=1).first()
        if not stats:
            stats = TaskStatsDB(id=1)
            self.session.add(stats)
        
        stats.total_tasks += 1
        
        if event_type == 'task-succeeded':
            stats.succeeded += 1
            if stats.active > 0:
                stats.active -= 1
        elif event_type == 'task-failed':
            stats.failed += 1
            if stats.active > 0:
                stats.active -= 1
        elif event_type == 'task-retried':
            stats.retried += 1
        elif event_type == 'task-started':
            stats.active += 1
        elif event_type == 'task-sent':
            stats.pending += 1
        elif event_type == 'task-received':
            if stats.pending > 0:
                stats.pending -= 1
        
        stats.last_updated = datetime.utcnow()
        self.session.commit()