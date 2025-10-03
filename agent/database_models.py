"""
SQLAlchemy database models for Kanchi monitoring system.
Migrates from in-memory storage to persistent SQL database.
"""

from sqlalchemy import (
    Column, String, DateTime, Integer, Float, Text, Boolean, 
    ForeignKey, Index, JSON, event, or_
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json

Base = declarative_base()


class TaskEvent(Base):
    """Core task event model - optimized for high-volume inserts and queries"""
    __tablename__ = 'task_events'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Core task identification
    task_id = Column(String(36), nullable=False, index=True)
    task_name = Column(String(255), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)
    
    # Task parameters and routing
    args = Column(Text, default="()")
    kwargs = Column(Text, default="{}")
    routing_key = Column(String(255), default="", index=True)
    exchange = Column(String(255), default="")
    hostname = Column(String(255), index=True)
    
    # Task lifecycle
    retries = Column(Integer, default=0)
    eta = Column(String(255))
    expires = Column(String(255))
    
    # Task hierarchy
    root_id = Column(String(36))
    parent_id = Column(String(36))
    
    # Results and execution
    result = Column(Text)
    runtime = Column(Float)
    exception = Column(Text)
    traceback = Column(Text)
    
    # Retry tracking (enhanced from current system)
    retry_of = Column(String(36), index=True)
    is_retry = Column(Boolean, default=False, index=True)
    has_retries = Column(Boolean, default=False, index=True)
    retry_count = Column(Integer, default=0)
    
    # Orphan task tracking
    is_orphan = Column(Boolean, default=False, index=True)
    orphaned_at = Column(DateTime)
    
    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_task_timestamp', 'task_id', 'timestamp'),
        Index('idx_event_type_timestamp', 'event_type', 'timestamp'),
        Index('idx_hostname_timestamp', 'hostname', 'timestamp'),
        Index('idx_task_name_timestamp', 'task_name', 'timestamp'),
        Index('idx_retry_tracking', 'task_id', 'is_retry', 'retry_of'),
        Index('idx_active_tasks', 'event_type', 'timestamp'),
        Index('idx_routing_key_timestamp', 'routing_key', 'timestamp'),
        Index('idx_orphan_tasks', 'is_orphan', 'orphaned_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'task_id': self.task_id,
            'task_name': self.task_name,
            'event_type': self.event_type,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'args': self.args,
            'kwargs': self.kwargs,
            'retries': self.retries,
            'eta': self.eta,
            'expires': self.expires,
            'hostname': self.hostname,
            'exchange': self.exchange,
            'routing_key': self.routing_key,
            'root_id': self.root_id,
            'parent_id': self.parent_id,
            'result': self.result,
            'runtime': self.runtime,
            'exception': self.exception,
            'traceback': self.traceback,
            'retry_of': self.retry_of,
            'is_retry': self.is_retry,
            'has_retries': self.has_retries,
            'retry_count': self.retry_count,
            'is_orphan': self.is_orphan,
            'orphaned_at': self.orphaned_at.isoformat() if self.orphaned_at else None,
        }
    
    @classmethod
    def from_celery_event(cls, event: dict, task_name: Optional[str] = None) -> 'TaskEvent':
        """Create TaskEvent from Celery event data"""
        event_type = event.get('type', 'unknown')
        task_id = event.get('uuid', '')
        
        kwargs_data = event.get('kwargs', {})
        kwargs_str = str(kwargs_data) if isinstance(kwargs_data, dict) else str(kwargs_data)
        
        args_data = event.get('args', ())
        args_str = str(args_data) if isinstance(args_data, (list, tuple)) else str(args_data)
        
        return cls(
            task_id=task_id,
            task_name=task_name or event.get('name', 'unknown'),
            event_type=event_type,
            timestamp=datetime.fromtimestamp(event.get('timestamp', datetime.now().timestamp())),
            args=args_str,
            kwargs=kwargs_str,
            retries=event.get('retries', 0),
            eta=event.get('eta'),
            expires=event.get('expires'),
            hostname=event.get('hostname'),
            exchange=event.get('exchange', ''),
            routing_key=event.get('routing_key') or event.get('queue') or 'default',
            root_id=event.get('root_id', task_id),
            parent_id=event.get('parent_id'),
            result=str(event.get('result')) if event.get('result') is not None else None,
            runtime=event.get('runtime'),
            exception=event.get('exception'),
            traceback=event.get('traceback')
        )


class WorkerEvent(Base):
    """Worker status and heartbeat events"""
    __tablename__ = 'worker_events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    hostname = Column(String(255), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)
    
    # Worker performance metrics
    active_tasks = Column(Integer, default=0)
    processed_tasks = Column(Integer, default=0)
    
    # System information
    sw_ident = Column(String(255))
    sw_ver = Column(String(100))
    sw_sys = Column(String(255))
    
    # Load metrics (stored as JSON)
    loadavg = Column(JSON)
    freq = Column(Float)
    pool_info = Column(JSON)
    
    __table_args__ = (
        Index('idx_worker_status', 'hostname', 'event_type', 'timestamp'),
        Index('idx_worker_heartbeat', 'hostname', 'timestamp'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'hostname': self.hostname,
            'event_type': self.event_type,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'active_tasks': self.active_tasks,
            'processed_tasks': self.processed_tasks,
            'sw_ident': self.sw_ident,
            'sw_ver': self.sw_ver,
            'sw_sys': self.sw_sys,
            'loadavg': self.loadavg,
            'freq': self.freq,
            'pool_info': self.pool_info,
        }
    
    @classmethod
    def from_celery_event(cls, event: dict) -> 'WorkerEvent':
        """Create WorkerEvent from Celery worker event"""
        return cls(
            hostname=event.get('hostname', 'unknown'),
            event_type=event.get('type', 'unknown'),
            timestamp=datetime.fromtimestamp(event.get('timestamp', datetime.now().timestamp())),
            active_tasks=event.get('active', 0),
            processed_tasks=event.get('processed', 0),
            sw_ident=event.get('sw_ident'),
            sw_ver=event.get('sw_ver'),
            sw_sys=event.get('sw_sys'),
            loadavg=event.get('loadavg'),
            freq=event.get('freq'),
            pool_info=event.get('pool')
        )


class TaskAggregation(Base):
    """Pre-computed task aggregations for performance"""
    __tablename__ = 'task_aggregations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(36), nullable=False, unique=True, index=True)
    task_name = Column(String(255), nullable=False, index=True)
    
    # Latest status
    latest_event_type = Column(String(50), nullable=False, index=True)
    latest_timestamp = Column(DateTime, nullable=False, index=True)
    
    # Lifecycle timestamps
    sent_at = Column(DateTime)
    received_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Final result
    final_result = Column(Text)
    final_runtime = Column(Float)
    final_exception = Column(Text)
    
    # Execution context
    hostname = Column(String(255), index=True)
    routing_key = Column(String(255), index=True)
    args = Column(Text)
    kwargs = Column(Text)
    
    # Retry information
    retry_count = Column(Integer, default=0)
    is_retry = Column(Boolean, default=False, index=True)
    original_task_id = Column(String(36), index=True)
    
    # Orphan tracking
    is_orphan = Column(Boolean, default=False, index=True)
    orphaned_at = Column(DateTime)
    
    # Computed fields
    total_runtime = Column(Float)
    queue_time = Column(Float)
    
    __table_args__ = (
        Index('idx_task_status', 'latest_event_type', 'latest_timestamp'),
        Index('idx_task_completion', 'completed_at', 'latest_event_type'),
        Index('idx_retry_analysis', 'original_task_id', 'retry_count'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'task_id': self.task_id,
            'task_name': self.task_name,
            'latest_event_type': self.latest_event_type,
            'latest_timestamp': self.latest_timestamp.isoformat() if self.latest_timestamp else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'received_at': self.received_at.isoformat() if self.received_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'final_result': self.final_result,
            'final_runtime': self.final_runtime,
            'final_exception': self.final_exception,
            'hostname': self.hostname,
            'routing_key': self.routing_key,
            'args': self.args,
            'kwargs': self.kwargs,
            'retry_count': self.retry_count,
            'is_retry': self.is_retry,
            'original_task_id': self.original_task_id,
            'is_orphan': self.is_orphan,
            'orphaned_at': self.orphaned_at.isoformat() if self.orphaned_at else None,
            'total_runtime': self.total_runtime,
            'queue_time': self.queue_time,
        }


class TaskStats(Base):
    """Persistent task statistics with time-based bucketing"""
    __tablename__ = 'task_stats'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    time_bucket = Column(DateTime, nullable=False, index=True)
    bucket_type = Column(String(10), nullable=False, index=True)  # 'hour', 'day'
    
    # Counters
    total_tasks = Column(Integer, default=0)
    succeeded = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    retried = Column(Integer, default=0)
    active = Column(Integer, default=0)
    pending = Column(Integer, default=0)
    
    # Performance metrics
    avg_runtime = Column(Float)
    max_runtime = Column(Float)
    min_runtime = Column(Float)
    
    # Task type breakdown (JSON)
    task_type_counts = Column(JSON)
    worker_counts = Column(JSON)
    
    __table_args__ = (
        Index('idx_stats_time', 'bucket_type', 'time_bucket'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'time_bucket': self.time_bucket.isoformat() if self.time_bucket else None,
            'bucket_type': self.bucket_type,
            'total_tasks': self.total_tasks,
            'succeeded': self.succeeded,
            'failed': self.failed,
            'retried': self.retried,
            'active': self.active,
            'pending': self.pending,
            'avg_runtime': self.avg_runtime,
            'max_runtime': self.max_runtime,
            'min_runtime': self.min_runtime,
            'task_type_counts': self.task_type_counts,
            'worker_counts': self.worker_counts,
        }


class RetryChain(Base):
    """Explicit retry relationship tracking"""
    __tablename__ = 'retry_chains'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    original_task_id = Column(String(36), nullable=False, index=True)
    retry_task_id = Column(String(36), nullable=False, index=True)
    retry_number = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Retry reason/trigger
    retry_reason = Column(String(255))  # 'manual', 'automatic', 'system'
    retry_by = Column(String(255))      # User/system that triggered retry
    
    __table_args__ = (
        Index('idx_retry_original', 'original_task_id', 'retry_number'),
        Index('idx_retry_chain', 'retry_task_id'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'original_task_id': self.original_task_id,
            'retry_task_id': self.retry_task_id,
            'retry_number': self.retry_number,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'retry_reason': self.retry_reason,
            'retry_by': self.retry_by,
        }


class OptimizedQueries:
    """Optimized database queries for common patterns"""
    
    @staticmethod
    def get_recent_events_paginated(session, limit=100, offset=0, 
                                   filters=None, search=None, sort_by=None, sort_order='desc'):
        """Optimized recent events query with filtering and search"""
        query = session.query(TaskEvent)
        
        # Apply filters
        if filters:
            if filters.get('event_type'):
                query = query.filter(TaskEvent.event_type == filters['event_type'])
            if filters.get('task_name'):
                query = query.filter(TaskEvent.task_name.ilike(f"%{filters['task_name']}%"))
            if filters.get('hostname'):
                query = query.filter(TaskEvent.hostname == filters['hostname'])
            if filters.get('routing_key'):
                query = query.filter(TaskEvent.routing_key.ilike(f"%{filters['routing_key']}%"))
        
        # Apply search across multiple fields
        if search:
            search_filter = or_(
                TaskEvent.task_name.ilike(f"%{search}%"),
                TaskEvent.task_id.ilike(f"%{search}%"),
                TaskEvent.args.ilike(f"%{search}%"),
                TaskEvent.kwargs.ilike(f"%{search}%"),
                TaskEvent.hostname.ilike(f"%{search}%"),
                TaskEvent.event_type.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # Apply sorting
        if sort_by:
            sort_column = getattr(TaskEvent, sort_by, TaskEvent.timestamp)
            if sort_order == 'desc':
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(TaskEvent.timestamp.desc())
        
        # Apply pagination
        return query.offset(offset).limit(limit).all()
    
    @staticmethod
    def get_events_count(session, filters=None, search=None):
        """Get total count of events matching filters"""
        query = session.query(TaskEvent)
        
        if filters:
            if filters.get('event_type'):
                query = query.filter(TaskEvent.event_type == filters['event_type'])
            if filters.get('task_name'):
                query = query.filter(TaskEvent.task_name.ilike(f"%{filters['task_name']}%"))
            if filters.get('hostname'):
                query = query.filter(TaskEvent.hostname == filters['hostname'])
        
        if search:
            search_filter = or_(
                TaskEvent.task_name.ilike(f"%{search}%"),
                TaskEvent.task_id.ilike(f"%{search}%"),
                TaskEvent.args.ilike(f"%{search}%"),
                TaskEvent.kwargs.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        return query.count()
    
    @staticmethod
    def get_task_events(session, task_id: str):
        """Get all events for a specific task"""
        return session.query(TaskEvent).filter(
            TaskEvent.task_id == task_id
        ).order_by(TaskEvent.timestamp.asc()).all()
    
    @staticmethod
    def get_active_tasks(session):
        """Get currently active tasks"""
        # Find tasks that started but haven't completed
        subquery = session.query(TaskEvent.task_id).filter(
            TaskEvent.event_type.in_(['task-succeeded', 'task-failed', 'task-revoked'])
        ).subquery()
        
        return session.query(TaskEvent).filter(
            TaskEvent.event_type == 'task-started',
            ~TaskEvent.task_id.in_(subquery)
        ).all()
    
    @staticmethod
    def get_retry_chain(session, original_task_id: str):
        """Get full retry chain for a task"""
        return session.query(RetryChain).filter(
            RetryChain.original_task_id == original_task_id
        ).order_by(RetryChain.retry_number).all()
    
    @staticmethod
    def get_orphaned_tasks(session):
        """Get tasks that are marked as orphaned"""
        return session.query(TaskEvent).filter(
            TaskEvent.is_orphan == True
        ).order_by(TaskEvent.orphaned_at.desc()).all()
    
    @staticmethod
    def mark_tasks_as_orphaned(session, hostname: str, orphaned_at: datetime):
        """Mark all running tasks on a worker as orphaned"""
        # Find tasks that are running on this worker
        running_task_ids = session.query(TaskEvent.task_id).filter(
            TaskEvent.hostname == hostname,
            TaskEvent.event_type == 'task-started'
        ).subquery()
        
        # Check which of these don't have completion events
        completed_task_ids = session.query(TaskEvent.task_id).filter(
            TaskEvent.task_id.in_(running_task_ids),
            TaskEvent.event_type.in_(['task-succeeded', 'task-failed', 'task-revoked'])
        ).subquery()
        
        # Mark uncompleted tasks as orphaned
        session.query(TaskEvent).filter(
            TaskEvent.hostname == hostname,
            TaskEvent.task_id.in_(running_task_ids),
            ~TaskEvent.task_id.in_(completed_task_ids)
        ).update({
            'is_orphan': True,
            'orphaned_at': orphaned_at
        }, synchronize_session=False)
        
        session.commit()
    
    @staticmethod
    def get_current_stats(session):
        """Get current task statistics"""
        from sqlalchemy import func
        
        # Calculate real-time statistics
        stats = session.query(
            func.count(TaskEvent.id).label('total'),
            func.sum(func.case([(TaskEvent.event_type == 'task-succeeded', 1)], else_=0)).label('succeeded'),
            func.sum(func.case([(TaskEvent.event_type == 'task-failed', 1)], else_=0)).label('failed'),
            func.sum(func.case([(TaskEvent.event_type == 'task-retried', 1)], else_=0)).label('retried'),
        ).first()
        
        # Count active tasks
        active_count = len(OptimizedQueries.get_active_tasks(session))
        
        return {
            'total_tasks': stats.total or 0,
            'succeeded': stats.succeeded or 0,
            'failed': stats.failed or 0,
            'retried': stats.retried or 0,
            'active': active_count,
            'pending': 0  # Would need more complex logic to determine pending
        }


class BatchEventInserter:
    """High-performance batch insertion for events"""
    
    def __init__(self, session, batch_size=1000):
        self.session = session
        self.batch_size = batch_size
        self.task_events_batch = []
        self.worker_events_batch = []
        
    def add_task_event(self, event_data: Dict[str, Any]):
        """Add task event to batch"""
        self.task_events_batch.append(event_data)
        if len(self.task_events_batch) >= self.batch_size:
            self.flush_task_events()
            
    def add_worker_event(self, event_data: Dict[str, Any]):
        """Add worker event to batch"""
        self.worker_events_batch.append(event_data)
        if len(self.worker_events_batch) >= self.batch_size:
            self.flush_worker_events()
            
    def flush_task_events(self):
        """Flush task events batch to database"""
        if self.task_events_batch:
            self.session.bulk_insert_mappings(TaskEvent, self.task_events_batch)
            self.task_events_batch.clear()
            self.session.commit()
            
    def flush_worker_events(self):
        """Flush worker events batch to database"""
        if self.worker_events_batch:
            self.session.bulk_insert_mappings(WorkerEvent, self.worker_events_batch)
            self.worker_events_batch.clear()
            self.session.commit()
    
    def flush_all(self):
        """Flush all pending batches"""
        self.flush_task_events()
        self.flush_worker_events()


class DataRetentionManager:
    """Manages data retention and cleanup policies"""
    
    def __init__(self, session, retention_days=30):
        self.session = session
        self.retention_days = retention_days
        
    def cleanup_old_events(self, batch_size=10000):
        """Remove events older than retention period"""
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
        
        # Delete old task events in batches
        while True:
            old_events = self.session.query(TaskEvent).filter(
                TaskEvent.timestamp < cutoff_date
            ).limit(batch_size).all()
            
            if not old_events:
                break
                
            for event in old_events:
                self.session.delete(event)
            self.session.commit()
        
        # Delete old worker events
        while True:
            old_worker_events = self.session.query(WorkerEvent).filter(
                WorkerEvent.timestamp < cutoff_date
            ).limit(batch_size).all()
            
            if not old_worker_events:
                break
                
            for event in old_worker_events:
                self.session.delete(event)
            self.session.commit()
    
    def cleanup_old_stats(self):
        """Clean up old hourly stats, keeping only daily aggregations"""
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        
        old_hourly_stats = self.session.query(TaskStats).filter(
            TaskStats.bucket_type == 'hour',
            TaskStats.time_bucket < cutoff_date
        ).all()
        
        for stat in old_hourly_stats:
            self.session.delete(stat)
        
        self.session.commit()