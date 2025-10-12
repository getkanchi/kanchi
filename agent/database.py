"""Database models and session management for Kanchi."""

from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, DateTime, Date, JSON, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool, NullPool
from contextlib import contextmanager
import json

Base = declarative_base()


def utc_now():
    """Return current UTC time with timezone info."""
    return datetime.now(timezone.utc)


def ensure_utc_isoformat(dt: datetime) -> str:
    """
    Convert datetime to ISO format string with UTC timezone.
    If datetime is naive, assume it's UTC and add timezone info.
    """
    if dt is None:
        return None
    # If naive (no timezone), treat as UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


class TaskEventDB(Base):
    """SQLAlchemy model for task events."""
    __tablename__ = 'task_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(255), nullable=False, index=True)
    task_name = Column(String(255), index=True)
    event_type = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    hostname = Column(String(255))
    worker_name = Column(String(255))
    queue = Column(String(255))
    exchange = Column(String(255))
    routing_key = Column(String(255))
    
    root_id = Column(String(255), index=True)
    parent_id = Column(String(255), index=True)
    
    args = Column(JSON)
    kwargs = Column(JSON)
    retries = Column(Integer, default=0)
    eta = Column(String(50))
    expires = Column(String(50))
    
    result = Column(JSON)
    runtime = Column(Float)
    exception = Column(Text)
    traceback = Column(Text)
    
    retry_of = Column(String(255), index=True)
    retried_by = Column(Text)  # JSON serialized list
    is_retry = Column(Boolean, default=False)
    has_retries = Column(Boolean, default=False)
    retry_count = Column(Integer, default=0)
    
    is_orphan = Column(Boolean, default=False, index=True)
    orphaned_at = Column(DateTime(timezone=True))
    
    __table_args__ = (
        Index('idx_task_timestamp', 'task_id', 'timestamp'),
        Index('idx_event_type_timestamp', 'event_type', 'timestamp'),
        Index('idx_recent_events_optimized', 'timestamp', 'event_type', 'task_id'),
        Index('idx_aggregation_optimized', 'task_id', 'timestamp', 'event_type'),
        Index('idx_orphan_lookup', 'is_orphan', 'orphaned_at'),
        Index('idx_hostname_routing', 'hostname', 'routing_key', 'timestamp'),
        Index('idx_task_name_search', 'task_name', 'timestamp'),
        Index('idx_retry_tracking', 'task_id', 'is_retry', 'retry_of'),
        Index('idx_active_tasks', 'event_type', 'timestamp'),
        Index('idx_routing_key_timestamp', 'routing_key', 'timestamp'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'task_id': self.task_id,
            'task_name': self.task_name,
            'event_type': self.event_type,
            'timestamp': ensure_utc_isoformat(self.timestamp),
            'hostname': self.hostname,
            'worker_name': self.worker_name,
            'queue': self.queue,
            'exchange': self.exchange or "",
            'routing_key': self.routing_key,
            'root_id': self.root_id,
            'parent_id': self.parent_id,
            'args': self.args if self.args is not None else [],
            'kwargs': self.kwargs if self.kwargs is not None else {},
            'retries': self.retries,
            'eta': self.eta,
            'expires': self.expires,
            'result': self.result,
            'runtime': self.runtime,
            'exception': self.exception,
            'traceback': self.traceback,
            'retry_of': self.retry_of,
            'retried_by': json.loads(self.retried_by) if self.retried_by else [],
            'is_retry': self.is_retry,
            'has_retries': self.has_retries,
            'retry_count': self.retry_count,
            'is_orphan': self.is_orphan,
            'orphaned_at': ensure_utc_isoformat(self.orphaned_at),
        }


class WorkerEventDB(Base):
    """SQLAlchemy model for worker events."""
    __tablename__ = 'worker_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    hostname = Column(String(255), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(String(50))
    active_tasks = Column(JSON)
    processed = Column(Integer, default=0)

    __table_args__ = (
        Index('idx_worker_status', 'hostname', 'event_type', 'timestamp'),
        Index('idx_worker_heartbeat', 'hostname', 'timestamp'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'hostname': self.hostname,
            'event_type': self.event_type,
            'timestamp': ensure_utc_isoformat(self.timestamp),
            'status': self.status,
            'active_tasks': self.active_tasks,
            'processed': self.processed,
        }


class RetryRelationshipDB(Base):
    """SQLAlchemy model for retry relationships."""
    __tablename__ = 'retry_relationships'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(255), nullable=False, unique=True, index=True)
    original_id = Column(String(255), nullable=False, index=True)
    retry_chain = Column(JSON)  # List of task IDs in retry chain
    total_retries = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    __table_args__ = (
        Index('idx_retry_bulk_lookup', 'task_id', 'original_id'),
    )


class TaskRegistryDB(Base):
    """SQLAlchemy model for task registry."""
    __tablename__ = 'task_registry'

    id = Column(String(36), primary_key=True)  # UUID
    name = Column(String(255), unique=True, nullable=False, index=True)
    human_readable_name = Column(String(255))
    description = Column(Text)
    tags = Column(JSON)  # Array of strings
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    first_seen = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_seen = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        Index('idx_task_name_lookup', 'name'),
        Index('idx_last_seen', 'last_seen'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'name': self.name,
            'human_readable_name': self.human_readable_name,
            'description': self.description,
            'tags': self.tags or [],
            'created_at': ensure_utc_isoformat(self.created_at),
            'updated_at': ensure_utc_isoformat(self.updated_at),
            'first_seen': ensure_utc_isoformat(self.first_seen),
            'last_seen': ensure_utc_isoformat(self.last_seen),
        }


class TaskDailyStatsDB(Base):
    """Daily aggregated statistics per task."""
    __tablename__ = 'task_daily_stats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_name = Column(String(255), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    # Execution counts
    total_executions = Column(Integer, default=0)
    succeeded = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    pending = Column(Integer, default=0)
    retried = Column(Integer, default=0)
    revoked = Column(Integer, default=0)
    orphaned = Column(Integer, default=0)

    # Performance metrics
    avg_runtime = Column(Float)
    min_runtime = Column(Float)
    max_runtime = Column(Float)
    p50_runtime = Column(Float)  # Median
    p95_runtime = Column(Float)  # 95th percentile
    p99_runtime = Column(Float)  # 99th percentile

    # Timestamps
    first_execution = Column(DateTime(timezone=True))
    last_execution = Column(DateTime(timezone=True))

    # Metadata
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        Index('idx_unique_task_date', 'task_name', 'date', unique=True),
        Index('idx_task_name_date_range', 'task_name', 'date'),
        Index('idx_date_lookup', 'date'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'task_name': self.task_name,
            'date': self.date.isoformat() if self.date else None,
            'total_executions': self.total_executions,
            'succeeded': self.succeeded,
            'failed': self.failed,
            'pending': self.pending,
            'retried': self.retried,
            'revoked': self.revoked,
            'orphaned': self.orphaned,
            'avg_runtime': self.avg_runtime,
            'min_runtime': self.min_runtime,
            'max_runtime': self.max_runtime,
            'p50_runtime': self.p50_runtime,
            'p95_runtime': self.p95_runtime,
            'p99_runtime': self.p99_runtime,
            'first_execution': ensure_utc_isoformat(self.first_execution),
            'last_execution': ensure_utc_isoformat(self.last_execution),
        }


class EnvironmentDB(Base):
    """SQLAlchemy model for environment filters."""
    __tablename__ = 'environments'

    id = Column(String(36), primary_key=True)  # UUID
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text)

    # Filter patterns (JSON arrays of wildcard patterns)
    queue_patterns = Column(JSON)  # e.g., ["prod-*", "staging-queue-?"]
    worker_patterns = Column(JSON)  # e.g., ["worker-*.prod.com", "celery@prod-*"]

    # State
    is_active = Column(Boolean, default=False, index=True)
    is_default = Column(Boolean, default=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        Index('idx_env_active', 'is_active'),
        Index('idx_env_default', 'is_default'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'queue_patterns': self.queue_patterns or [],
            'worker_patterns': self.worker_patterns or [],
            'is_active': self.is_active,
            'is_default': self.is_default,
            'created_at': ensure_utc_isoformat(self.created_at),
            'updated_at': ensure_utc_isoformat(self.updated_at),
        }


class DatabaseManager:
    """Manage database connections and sessions."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        is_sqlite = database_url.startswith('sqlite')

        if is_sqlite:
            # Use NullPool to create a new connection per thread
            # This prevents thread-safety issues and segfaults with SQLite
            self.engine = create_engine(
                database_url,
                poolclass=NullPool,  # No connection pooling - new connection per use
                pool_pre_ping=True,
                echo=False,
                connect_args={
                    "check_same_thread": False,  # Allow cross-thread usage
                    "timeout": 30.0,  # Wait up to 30s for database locks
                },
                # Use SQLite's default isolation level (DEFERRED)
                # READ UNCOMMITTED is not properly supported by SQLite
            )
        else:
            self.engine = create_engine(
                database_url,
                pool_size=20,
                max_overflow=30,
                pool_recycle=3600,
                pool_timeout=30,
                pool_pre_ping=True,
                echo=False
            )

        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def run_migrations(self):
        """Run Alembic migrations to upgrade database to latest version."""
        from alembic.config import Config as AlembicConfig
        from alembic import command
        import os

        current_dir = os.path.dirname(os.path.abspath(__file__))
        alembic_ini_path = os.path.join(current_dir, 'alembic.ini')
        alembic_cfg = AlembicConfig(alembic_ini_path)
        alembic_cfg.set_main_option('sqlalchemy.url', self.database_url)
        command.upgrade(alembic_cfg, 'head')

    @contextmanager
    def get_session(self) -> Session:
        """Get a database session context manager."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
