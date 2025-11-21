"""Service layer for task-related operations."""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, or_, and_, func, String, cast, Integer, literal

from database import TaskEventDB, RetryRelationshipDB
from models import TaskEvent
from constants import TaskState, EventType, STATE_TO_EVENT_MAP, ACTIVE_EVENT_TYPES
from services.utils import EnvironmentFilter, GenericFilter, parse_filter_string
from utils.payload_sanitizer import find_placeholder_paths

logger = logging.getLogger(__name__)


class TaskService:
    """Service for managing task events and statistics."""

    def __init__(self, session: Session, active_env=None):
        self.session = session
        self.active_env = active_env

    def save_task_event(self, task_event: TaskEvent) -> TaskEventDB:
        """
        Save a task event to the database.

        Args:
            task_event: Task event to save

        Returns:
            Saved database model

        Raises:
            Exception: If database operation fails
        """
        try:
            routing_key, queue = self._inherit_queue_info(task_event)
            args, kwargs = self._parse_task_arguments(task_event)
            self._log_payload_truncation(task_event, args, kwargs, task_event.result)

            task_event_db = self._create_task_event_db(
                task_event, routing_key, queue, args, kwargs
            )

            self.session.add(task_event_db)
            self.session.commit()
            return task_event_db

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to save task event {task_event.task_id[:8]}: {e}")
            raise

    def get_task_events(self, task_id: str) -> List[TaskEvent]:
        """
        Get all events for a specific task.

        Args:
            task_id: Task ID to retrieve events for

        Returns:
            List of task events ordered by timestamp
        """
        events_db = (
            self.session.query(TaskEventDB)
            .filter_by(task_id=task_id)
            .order_by(TaskEventDB.timestamp)
            .all()
        )

        events = [self._db_to_task_event(event_db) for event_db in events_db]

        if events:
            self._bulk_enrich_with_retry_info([events[0]])
            for i in range(1, len(events)):
                events[i].retry_of = events[0].retry_of
                events[i].retried_by = events[0].retried_by
                events[i].is_retry = events[0].is_retry
                events[i].has_retries = events[0].has_retries
                events[i].retry_count = events[0].retry_count

        return events

    def get_recent_events(
        self,
        limit: int = 100,
        page: int = 0,
        aggregate: bool = True,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
        search: Optional[str] = None,
        filters: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        filter_state: Optional[str] = None,
        filter_worker: Optional[str] = None,
        filter_task: Optional[str] = None,
        filter_queue: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get recent task events with filtering and pagination.

        Args:
            limit: Maximum number of events per page
            page: Page number (0-indexed)
            aggregate: If True, show only latest event per task
            sort_by: Column to sort by
            sort_order: Sort order (asc or desc)
            search: Search term for full-text search
            filters: Filter string in format "field:operator:value;..."
            start_time: ISO format start time filter
            end_time: ISO format end time filter
            filter_state: Legacy state filter
            filter_worker: Legacy worker filter
            filter_task: Legacy task name filter
            filter_queue: Legacy queue filter

        Returns:
            Dictionary with 'data' (list of events) and 'pagination' (metadata)
        """
        if aggregate:
            events, total_events = self._get_aggregated_events(
                limit, page, sort_by, sort_order,
                filters, start_time, end_time,
                filter_state, filter_worker, filter_task, filter_queue, search
            )
        else:
            events, total_events = self._get_all_events(
                limit, page, sort_by, sort_order,
                filters, start_time, end_time,
                filter_state, filter_worker, filter_task, filter_queue, search
            )

        total_pages = (total_events + limit - 1) // limit if limit > 0 else 1

        return {
            "data": events,
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
        """
        Get currently active tasks.

        Returns:
            List of tasks with latest event being started/received/sent
        """
        latest_events_query = self.session.query(
            TaskEventDB.task_id,
            func.max(TaskEventDB.timestamp).label('max_timestamp')
        )

        env_filtered_query = self.session.query(TaskEventDB.task_id)
        env_filtered_query = EnvironmentFilter.apply(env_filtered_query, self.active_env)
        env_conditions = env_filtered_query.whereclause

        if env_conditions is not None:
            latest_events_query = latest_events_query.filter(env_conditions)

        latest_events = latest_events_query.group_by(TaskEventDB.task_id).subquery()

        active_events_db = (
            self.session.query(TaskEventDB)
            .join(
                latest_events,
                and_(
                    TaskEventDB.task_id == latest_events.c.task_id,
                    TaskEventDB.timestamp == latest_events.c.max_timestamp
                )
            )
            .filter(TaskEventDB.event_type.in_([et.value for et in ACTIVE_EVENT_TYPES]))
            .all()
        )

        events = [self._db_to_task_event(event_db) for event_db in active_events_db]
        self._bulk_enrich_with_retry_info(events)

        return events

    def get_recent_failed_tasks(
        self,
        hours: int = 24,
        limit: int = 50,
        exclude_retried: bool = True
    ) -> List[TaskEvent]:
        """
        Get failed tasks in the last ``hours`` where the latest event is a failure.

        Args:
            hours: Lookback window in hours (default 24)
            limit: Maximum number of tasks to return (default 50)
            exclude_retried: If True, exclude tasks that have already been retried

        Returns:
            List of failed task events ordered by most recent failure first
        """
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        latest_subquery = (
            self.session.query(
                TaskEventDB.task_id,
                func.max(TaskEventDB.timestamp).label('max_timestamp')
            )
            .filter(TaskEventDB.timestamp >= since)
        )

        env_filtered_query = self.session.query(TaskEventDB.task_id)
        env_filtered_query = EnvironmentFilter.apply(env_filtered_query, self.active_env)
        env_conditions = env_filtered_query.whereclause

        if env_conditions is not None:
            latest_subquery = latest_subquery.filter(env_conditions)

        latest_subquery = latest_subquery.group_by(TaskEventDB.task_id).subquery()

        query = (
            self.session.query(TaskEventDB)
            .join(
                latest_subquery,
                and_(
                    TaskEventDB.task_id == latest_subquery.c.task_id,
                    TaskEventDB.timestamp == latest_subquery.c.max_timestamp
                )
            )
            .filter(
                TaskEventDB.event_type == EventType.TASK_FAILED.value,
                TaskEventDB.timestamp >= since
            )
        )

        if exclude_retried:
            query = query.filter(
                or_(TaskEventDB.has_retries.is_(False), TaskEventDB.has_retries.is_(None))
            )

        query = query.order_by(TaskEventDB.timestamp.desc())

        if limit and limit > 0:
            query = query.limit(limit)

        events_db = query.all()

        events = [self._db_to_task_event(event_db) for event_db in events_db]
        self._bulk_enrich_with_retry_info(events)

        return events

    def create_retry_relationship(
        self,
        original_task_id: str,
        new_task_id: str,
        retried_by: str = "system"
    ):
        """
        Create a retry relationship between tasks.

        Args:
            original_task_id: Original task ID
            new_task_id: New retry task ID
            retried_by: Source of retry (default: "system")

        Raises:
            Exception: If database operation fails
        """
        try:
            new_retry_rel = RetryRelationshipDB(
                task_id=new_task_id,
                original_id=original_task_id,
                retry_chain=[],
                total_retries=0
            )
            self.session.add(new_retry_rel)

            parent_rel = (
                self.session.query(RetryRelationshipDB)
                .filter_by(task_id=original_task_id)
                .first()
            )

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

            original_events = (
                self.session.query(TaskEventDB)
                .filter_by(task_id=original_task_id)
                .all()
            )

            for event in original_events:
                existing_retries = json.loads(event.retried_by) if event.retried_by else []
                existing_retries.append(new_task_id)

                event.retried_by = json.dumps(existing_retries)
                event.has_retries = True
                event.retry_count = len(existing_retries)

            self.session.commit()

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to create retry relationship: {e}")
            raise

    def mark_new_task_as_retry(self, new_task_id: str, original_task_id: str):
        """
        Mark events for a new task as being a retry of the original task.

        Args:
            new_task_id: New retry task ID
            original_task_id: Original task ID

        Raises:
            Exception: If database operation fails
        """
        try:
            new_events = (
                self.session.query(TaskEventDB)
                .filter_by(task_id=new_task_id)
                .all()
            )

            for event in new_events:
                event.retry_of = original_task_id
                event.is_retry = True

            if new_events:
                self.session.commit()

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to mark task as retry: {e}")
            raise

    def get_task_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics for dashboard display.

        Returns:
            Dictionary with event distribution and recent activity stats
        """
        event_stats = (
            self.session.query(
                TaskEventDB.event_type,
                func.count(TaskEventDB.id).label('total_events'),
                func.count(func.distinct(TaskEventDB.task_id)).label('unique_tasks')
            )
            .group_by(TaskEventDB.event_type)
            .all()
        )

        recent_activity = (
            self.session.query(func.count(TaskEventDB.id).label('last_hour_events'))
            .filter(TaskEventDB.timestamp >= func.datetime('now', '-1 hour'))
            .scalar()
        )

        return {
            'event_distribution': [
                {
                    'event_type': stat.event_type,
                    'total_events': stat.total_events,
                    'unique_tasks': stat.unique_tasks
                }
                for stat in event_stats
            ],
            'recent_activity': recent_activity or 0
        }

    def _inherit_queue_info(self, task_event: TaskEvent) -> Tuple[str, str]:
        """
        Inherit queue information from previous task-sent event if not present.

        Args:
            task_event: Task event to process

        Returns:
            Tuple of (routing_key, queue)
        """
        routing_key = task_event.routing_key
        queue = task_event.queue

        if not routing_key or routing_key == 'default':
            existing_sent_event = (
                self.session.query(TaskEventDB)
                .filter_by(task_id=task_event.task_id, event_type=EventType.TASK_SENT.value)
                .first()
            )

            if existing_sent_event and existing_sent_event.routing_key:
                routing_key = existing_sent_event.routing_key
                queue = existing_sent_event.queue

        return routing_key, queue

    def _log_payload_truncation(
        self,
        task_event: TaskEvent,
        args: Any,
        kwargs: Any,
        result: Any,
    ) -> None:
        """
        Surface detailed logging whenever Celery truncated parts of the payload.
        """
        truncated_segments = []
        for field_name, value in (("args", args), ("kwargs", kwargs), ("result", result)):
            if value is None:
                continue
            placeholder_paths = find_placeholder_paths(value)
            if placeholder_paths:
                truncated_segments.append((field_name, placeholder_paths))

        if not truncated_segments:
            return

        details = "; ".join(
            f"{field} @ {', '.join(paths)}" for field, paths in truncated_segments
        )
        logger.warning(
            "Celery truncated payload data for task %s (%s). %s. "
            "Increase celery.amqp args/kwargs repr limits or serialize large structures "
            "before enqueuing if you need full visibility.",
            task_event.task_id,
            task_event.task_name,
            details
        )

    def _parse_task_arguments(self, task_event: TaskEvent) -> Tuple[Any, Any]:
        """
        Parse and inherit task arguments from previous events if needed.

        Args:
            task_event: Task event to process

        Returns:
            Tuple of (args, kwargs) as Python objects
        """
        args = self._parse_json_field(task_event.args, default=[])
        kwargs = self._parse_json_field(task_event.kwargs, default={})

        args_empty = not args or args in [(), [], "()", "[]"]
        kwargs_empty = not kwargs or kwargs in ({}, "{}", "{}")

        if args_empty and kwargs_empty:
            existing_received_event = (
                self.session.query(TaskEventDB)
                .filter_by(task_id=task_event.task_id, event_type=EventType.TASK_RECEIVED.value)
                .first()
            )

            if existing_received_event:
                if existing_received_event.args:
                    args = existing_received_event.args
                if existing_received_event.kwargs:
                    kwargs = existing_received_event.kwargs

        return args, kwargs

    def _parse_json_field(self, field_value: Any, default: Any) -> Any:
        """
        Parse a JSON field that might be a string or already a Python object.

        Args:
            field_value: Value to parse
            default: Default value if parsing fails

        Returns:
            Parsed Python object
        """
        if isinstance(field_value, (list, dict)):
            return field_value

        if isinstance(field_value, str):
            try:
                return json.loads(field_value)
            except (json.JSONDecodeError, ValueError):
                return field_value

        return field_value if field_value is not None else default

    def _create_task_event_db(
        self,
        task_event: TaskEvent,
        routing_key: str,
        queue: str,
        args: Any,
        kwargs: Any
    ) -> TaskEventDB:
        """
        Create a TaskEventDB model from a TaskEvent.

        Args:
            task_event: Source task event
            routing_key: Resolved routing key
            queue: Resolved queue
            args: Parsed args
            kwargs: Parsed kwargs

        Returns:
            TaskEventDB instance ready for insertion
        """
        return TaskEventDB(
            task_id=task_event.task_id,
            task_name=task_event.task_name,
            event_type=task_event.event_type,
            timestamp=task_event.timestamp,
            hostname=task_event.hostname,
            worker_name=task_event.worker_name,
            queue=queue,
            exchange=task_event.exchange,
            routing_key=routing_key,
            root_id=task_event.root_id,
            parent_id=task_event.parent_id,
            args=args,
            kwargs=kwargs,
            retries=task_event.retries,
            eta=task_event.eta,
            expires=task_event.expires,
            result=(
                task_event.result
                if isinstance(task_event.result, (list, dict))
                else str(task_event.result) if task_event.result else None
            ),
            runtime=task_event.runtime,
            exception=task_event.exception,
            traceback=task_event.traceback,
            retry_of=task_event.retry_of.task_id if task_event.retry_of else None,
            retried_by=(
                json.dumps([t.task_id for t in task_event.retried_by])
                if task_event.retried_by else None
            ),
            is_retry=task_event.is_retry,
            has_retries=task_event.has_retries,
            retry_count=task_event.retry_count
        )

    def _db_to_task_event(self, event_db: TaskEventDB) -> TaskEvent:
        """
        Convert database model to TaskEvent object.

        Args:
            event_db: Database model

        Returns:
            TaskEvent object
        """
        args_str = json.dumps(event_db.args) if event_db.args is not None else "()"
        kwargs_str = json.dumps(event_db.kwargs) if event_db.kwargs is not None else "{}"

        task_event = TaskEvent(
            task_id=event_db.task_id,
            task_name=event_db.task_name,
            event_type=event_db.event_type,
            timestamp=event_db.timestamp,
            hostname=event_db.hostname,
            worker_name=event_db.worker_name,
            queue=event_db.queue,
            exchange=event_db.exchange or "",
            routing_key=event_db.routing_key or "",
            root_id=event_db.root_id,
            parent_id=event_db.parent_id,
            args=args_str,
            kwargs=kwargs_str,
            retries=event_db.retries,
            eta=event_db.eta,
            expires=event_db.expires,
            result=event_db.result,
            runtime=event_db.runtime,
            exception=event_db.exception,
            traceback=event_db.traceback
        )

        task_event.is_orphan = event_db.is_orphan or False
        task_event.orphaned_at = event_db.orphaned_at

        return task_event

    def _enrich_task_with_retry_info(self, task_event: TaskEvent):
        """
        Enrich a single task event with retry relationship information.

        Args:
            task_event: Task event to enrich
        """
        self._bulk_enrich_with_retry_info([task_event])

    def _bulk_enrich_with_retry_info(self, events: List[TaskEvent]):
        """
        Bulk enrich multiple task events with retry information in a single query.

        Populates nested TaskEvent objects for retry_of and retried_by (1 level only).
        Circular references are prevented by setting nested objects' retry_of and retried_by to None/[].

        Args:
            events: List of task events to enrich
        """
        if not events:
            return

        task_ids = [event.task_id for event in events]

        retry_relationships = (
            self.session.query(RetryRelationshipDB)
            .filter(RetryRelationshipDB.task_id.in_(task_ids))
            .all()
        )

        retry_map = {rel.task_id: rel for rel in retry_relationships}

        parent_task_ids = set()
        retry_task_ids = set()

        for event in events:
            retry_rel = retry_map.get(event.task_id)
            if retry_rel:
                if retry_rel.original_id != event.task_id:
                    parent_task_ids.add(retry_rel.original_id)
                if retry_rel.retry_chain:
                    retry_task_ids.update(retry_rel.retry_chain)

        all_related_task_ids = parent_task_ids | retry_task_ids
        related_tasks_map = {}

        if all_related_task_ids:
            related_tasks_map = self._fetch_related_tasks(all_related_task_ids)

        for event in events:
            retry_rel = retry_map.get(event.task_id)
            if retry_rel:
                self._populate_retry_info(event, retry_rel, related_tasks_map)
            else:
                self._set_default_retry_info(event)

    def _fetch_related_tasks(self, task_ids: set) -> Dict[str, TaskEvent]:
        """
        Fetch latest events for related tasks in bulk.

        Args:
            task_ids: Set of task IDs to fetch

        Returns:
            Dictionary mapping task_id to TaskEvent
        """
        latest_events_subquery = (
            self.session.query(
                TaskEventDB.task_id,
                func.max(TaskEventDB.timestamp).label('max_timestamp')
            )
            .filter(TaskEventDB.task_id.in_(task_ids))
            .group_by(TaskEventDB.task_id)
            .subquery()
        )

        related_events_db = (
            self.session.query(TaskEventDB)
            .join(
                latest_events_subquery,
                and_(
                    TaskEventDB.task_id == latest_events_subquery.c.task_id,
                    TaskEventDB.timestamp == latest_events_subquery.c.max_timestamp
                )
            )
            .all()
        )

        related_tasks_map = {}
        for event_db in related_events_db:
            task_event = self._db_to_task_event(event_db)
            task_event.retry_of = None
            task_event.retried_by = []
            related_tasks_map[event_db.task_id] = task_event

        return related_tasks_map

    def _populate_retry_info(
        self,
        event: TaskEvent,
        retry_rel: RetryRelationshipDB,
        related_tasks_map: Dict[str, TaskEvent]
    ):
        """
        Populate retry information for an event.

        Args:
            event: Task event to populate
            retry_rel: Retry relationship from database
            related_tasks_map: Map of related task events
        """
        if retry_rel.original_id != event.task_id:
            parent_task = related_tasks_map.get(retry_rel.original_id)
            if not parent_task:
                parent_task = self._fetch_single_task(retry_rel.original_id)
            event.retry_of = parent_task
            event.is_retry = True
        else:
            event.retry_of = None
            event.is_retry = False

        if retry_rel.retry_chain:
            event.retried_by = []
            for retry_id in retry_rel.retry_chain:
                retry_task = related_tasks_map.get(retry_id)
                if not retry_task:
                    retry_task = self._fetch_single_task(retry_id)
                if retry_task:
                    event.retried_by.append(retry_task)
            event.has_retries = len(event.retried_by) > 0
        else:
            event.retried_by = []
            event.has_retries = False

        event.retry_count = retry_rel.total_retries

    def _fetch_single_task(self, task_id: str) -> Optional[TaskEvent]:
        """
        Fetch a single task event (fallback for missing bulk fetch).

        Args:
            task_id: Task ID to fetch

        Returns:
            TaskEvent or None if not found
        """
        event_db = (
            self.session.query(TaskEventDB)
            .filter_by(task_id=task_id)
            .order_by(TaskEventDB.timestamp.desc())
            .first()
        )

        if event_db:
            task_event = self._db_to_task_event(event_db)
            task_event.retry_of = None
            task_event.retried_by = []
            return task_event

        return None

    def _set_default_retry_info(self, event: TaskEvent):
        """
        Set default retry information when no relationship exists.

        Args:
            event: Task event to set defaults on
        """
        event.retry_of = None
        event.retried_by = []
        event.is_retry = False
        event.has_retries = False
        event.retry_count = 0

    def _get_all_events(
        self,
        limit: int,
        page: int,
        sort_by: Optional[str],
        sort_order: str,
        filters: Optional[str],
        start_time: Optional[str],
        end_time: Optional[str],
        filter_state: Optional[str],
        filter_worker: Optional[str],
        filter_task: Optional[str],
        filter_queue: Optional[str],
        search: Optional[str]
    ) -> Tuple[List[TaskEvent], int]:
        """
        Get all task events (non-aggregated) with filtering and pagination.

        Args:
            See get_recent_events for parameter descriptions

        Returns:
            Tuple of (events list, total count)
        """
        query = self.session.query(TaskEventDB)
        query = EnvironmentFilter.apply(query, self.active_env)
        query = self._apply_all_filters(
            query, filters, start_time, end_time,
            filter_state, filter_worker, filter_task, filter_queue, search
        )
        query = self._apply_sorting(query, sort_by, sort_order)

        total_events = query.count()
        start_idx = page * limit
        events_db = query.offset(start_idx).limit(limit).all()

        events = [self._db_to_task_event(event_db) for event_db in events_db]
        self._bulk_enrich_with_retry_info(events)

        return events, total_events

    def _get_aggregated_events(
        self,
        limit: int,
        page: int,
        sort_by: Optional[str],
        sort_order: str,
        filters: Optional[str],
        start_time: Optional[str],
        end_time: Optional[str],
        filter_state: Optional[str],
        filter_worker: Optional[str],
        filter_task: Optional[str],
        filter_queue: Optional[str],
        search: Optional[str]
    ) -> Tuple[List[TaskEvent], int]:
        """
        Get aggregated task events (latest per task) with filtering and pagination.

        Args:
            See get_recent_events for parameter descriptions

        Returns:
            Tuple of (events list, total count)
        """
        base_query = self.session.query(TaskEventDB)
        base_query = EnvironmentFilter.apply(base_query, self.active_env)
        base_query = self._apply_time_filters(base_query, start_time, end_time)

        latest_events_subquery = (
            base_query.with_entities(
                TaskEventDB.id.label("id"),
                TaskEventDB.task_id.label("task_id"),
                func.row_number().over(
                    partition_by=TaskEventDB.task_id,
                    order_by=[TaskEventDB.timestamp.desc(), TaskEventDB.id.desc()],
                ).label("row_number"),
            )
        ).subquery()

        main_query = (
            self.session.query(TaskEventDB)
            .join(latest_events_subquery, TaskEventDB.id == latest_events_subquery.c.id)
            .filter(latest_events_subquery.c.row_number == 1)
        )

        main_query = self._apply_content_filters(
            main_query, filters, filter_state, filter_worker, filter_task, filter_queue, search
        )
        main_query = self._apply_sorting(main_query, sort_by, sort_order)

        total_events = main_query.count()
        start_idx = page * limit
        events_db = main_query.offset(start_idx).limit(limit).all()

        events = [self._db_to_task_event(event_db) for event_db in events_db]
        self._bulk_enrich_with_retry_info(events)

        return events, total_events

    def _apply_all_filters(
        self,
        query,
        filters: Optional[str],
        start_time: Optional[str],
        end_time: Optional[str],
        filter_state: Optional[str],
        filter_worker: Optional[str],
        filter_task: Optional[str],
        filter_queue: Optional[str],
        search: Optional[str]
    ):
        """Apply all filters to a query."""
        query = self._apply_time_filters(query, start_time, end_time)
        query = self._apply_content_filters(
            query, filters, filter_state, filter_worker, filter_task, filter_queue, search
        )
        return query

    def _apply_time_filters(self, query, start_time: Optional[str], end_time: Optional[str]):
        """Apply time range filters to a query."""
        if start_time:
            try:
                from dateutil import parser
                start_dt = parser.isoparse(start_time)
                query = query.filter(TaskEventDB.timestamp >= start_dt)
            except (ValueError, ImportError) as e:
                logger.error(f"Failed to parse start_time: {start_time}, error: {e}")

        if end_time:
            try:
                from dateutil import parser
                end_dt = parser.isoparse(end_time)
                query = query.filter(TaskEventDB.timestamp <= end_dt)
            except (ValueError, ImportError) as e:
                logger.error(f"Failed to parse end_time: {end_time}, error: {e}")

        return query

    def _apply_content_filters(
        self,
        query,
        filters: Optional[str],
        filter_state: Optional[str],
        filter_worker: Optional[str],
        filter_task: Optional[str],
        filter_queue: Optional[str],
        search: Optional[str]
    ):
        """Apply content filters (state, worker, task, queue, search) to a query."""
        parsed_filters = parse_filter_string(filters) if filters else []

        for filter_obj in parsed_filters:
            query = self._apply_single_filter(query, filter_obj)

        if filter_state:
            query = self._apply_state_filter(query, 'is', [filter_state])

        if filter_worker:
            query = GenericFilter.apply(
                query, TaskEventDB.hostname, 'contains', [filter_worker]
            )

        if filter_task:
            query = GenericFilter.apply(
                query, TaskEventDB.task_name, 'contains', [filter_task]
            )

        if filter_queue:
            query = GenericFilter.apply(
                query, TaskEventDB.routing_key, 'contains', [filter_queue]
            )

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    TaskEventDB.task_name.ilike(search_pattern),
                    TaskEventDB.task_id.ilike(search_pattern),
                    TaskEventDB.hostname.ilike(search_pattern),
                    TaskEventDB.event_type.ilike(search_pattern),
                    func.cast(TaskEventDB.args, String).ilike(search_pattern),
                    func.cast(TaskEventDB.kwargs, String).ilike(search_pattern)
                )
            )

        return query

    def _apply_single_filter(self, query, filter_obj: Dict[str, Any]):
        """Apply a single parsed filter to the query."""
        field = filter_obj['field']
        operator = filter_obj['operator']
        values = filter_obj['values']

        if field == 'state':
            return self._apply_state_filter(query, operator, values)
        elif field == 'worker':
            return GenericFilter.apply(query, TaskEventDB.hostname, operator, values)
        elif field == 'task':
            return GenericFilter.apply(query, TaskEventDB.task_name, operator, values)
        elif field == 'queue':
            return GenericFilter.apply(query, TaskEventDB.routing_key, operator, values)
        elif field == 'id':
            return GenericFilter.apply(query, TaskEventDB.task_id, operator, values)

        return query

    def _apply_state_filter(self, query, operator: str, values: List[str]):
        """Apply state filter with operator support."""
        def state_to_event_type(state: str) -> Optional[str]:
            try:
                task_state = TaskState(state.upper())
                event_type = STATE_TO_EVENT_MAP.get(task_state)
                return event_type.value if event_type else None
            except (ValueError, KeyError):
                return None

        return GenericFilter.apply(
            query, TaskEventDB.event_type, operator, values, state_to_event_type
        )

    def _apply_sorting(self, query, sort_by: Optional[str], sort_order: str):
        """Apply sorting to a query."""
        if sort_by:
            sort_column = getattr(TaskEventDB, sort_by, None)
            if sort_column:
                if sort_order == "desc":
                    query = query.order_by(desc(sort_column))
                else:
                    query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(TaskEventDB.timestamp), desc(TaskEventDB.id))

        return query
