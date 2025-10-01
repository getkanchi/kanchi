"""Database models and session management for Kanchi."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, DateTime, JSON, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import json

Base = declarative_base()


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
    
    # Task hierarchy
    root_id = Column(String(255), index=True)
    parent_id = Column(String(255), index=True)
    
    # Task parameters - stored as JSON
    args = Column(JSON)
    kwargs = Column(JSON)
    retries = Column(Integer, default=0)
    eta = Column(String(50))
    expires = Column(String(50))
    
    # Results
    result = Column(JSON)
    runtime = Column(Float)
    exception = Column(Text)
    traceback = Column(Text)
    
    # Retry tracking
    retry_of = Column(String(255), index=True)
    retried_by = Column(Text)  # JSON serialized list
    is_retry = Column(Boolean, default=False)
    has_retries = Column(Boolean, default=False)
    retry_count = Column(Integer, default=0)
    
    # Composite index for common queries
    __table_args__ = (
        Index('idx_task_timestamp', 'task_id', 'timestamp'),
        Index('idx_event_type_timestamp', 'event_type', 'timestamp'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'task_id': self.task_id,
            'task_name': self.task_name,
            'event_type': self.event_type,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
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
            'retried_by': self.retried_by,
            'is_retry': self.is_retry,
            'has_retries': self.has_retries,
            'retry_count': self.retry_count,
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'hostname': self.hostname,
            'event_type': self.event_type,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
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
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'total_tasks': self.total_tasks,
            'succeeded': self.succeeded,
            'failed': self.failed,
            'pending': self.pending,
            'retried': self.retried,
            'active': self.active,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
        }


class RetryRelationshipDB(Base):
    """SQLAlchemy model for retry relationships."""
    __tablename__ = 'retry_relationships'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(255), nullable=False, unique=True, index=True)
    original_id = Column(String(255), nullable=False, index=True)
    retry_chain = Column(JSON)  # List of task IDs in retry chain
    total_retries = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DatabaseManager:
    """Manage database connections and sessions."""
    
    def __init__(self, database_url: str):
        """Initialize database manager.
        
        Args:
            database_url: SQLAlchemy database URL (e.g., 'sqlite:///kanchi.db', 'postgresql://...')
        """
        self.engine = create_engine(
            database_url,
            pool_pre_ping=True,  # Verify connections before using
            echo=False  # Set to True for SQL debugging
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        """Create all tables in the database."""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Drop all tables in the database."""
        Base.metadata.drop_all(bind=self.engine)
    
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
    
    def get_session_dependency(self) -> Session:
        """FastAPI dependency for getting a database session."""
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()