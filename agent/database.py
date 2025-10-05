"""Database models and session management for Kanchi."""

from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, DateTime, JSON, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
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
    timestamp = Column(DateTime, nullable=False, index=True)
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
    orphaned_at = Column(DateTime)
    
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
            'exchange': self.exchange,
            'routing_key': self.routing_key,
            'root_id': self.root_id,
            'parent_id': self.parent_id,
            'args': self.args,
            'kwargs': self.kwargs,
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
    timestamp = Column(DateTime, nullable=False, index=True)
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


class TaskStatsDB(Base):
    """SQLAlchemy model for task statistics."""
    __tablename__ = 'task_stats'

    id = Column(Integer, primary_key=True, default=1)  # Single row for global stats
    total_tasks = Column(Integer, default=0)
    succeeded = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    pending = Column(Integer, default=0)
    retried = Column(Integer, default=0)
    active = Column(Integer, default=0)
    last_updated = Column(DateTime, default=utc_now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'total_tasks': self.total_tasks,
            'succeeded': self.succeeded,
            'failed': self.failed,
            'pending': self.pending,
            'retried': self.retried,
            'active': self.active,
            'last_updated': ensure_utc_isoformat(self.last_updated),
        }


class RetryRelationshipDB(Base):
    """SQLAlchemy model for retry relationships."""
    __tablename__ = 'retry_relationships'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(255), nullable=False, unique=True, index=True)
    original_id = Column(String(255), nullable=False, index=True)
    retry_chain = Column(JSON)  # List of task IDs in retry chain
    total_retries = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    __table_args__ = (
        Index('idx_retry_bulk_lookup', 'task_id', 'original_id'),
    )


class DatabaseManager:
    """Manage database connections and sessions."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        is_sqlite = database_url.startswith('sqlite')

        if is_sqlite:
            self.engine = create_engine(
                database_url,
                poolclass=StaticPool,
                pool_pre_ping=True,
                echo=False,
                connect_args={"check_same_thread": False},
                isolation_level="READ UNCOMMITTED"
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
