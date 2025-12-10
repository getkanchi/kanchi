"""Database models and session management for Kanchi."""

from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Date,
    JSON,
    Text,
    Index,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
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


class TaskLatestDB(Base):
    """
    Snapshot of the latest event per task for high-performance aggregated queries.

    This keeps only one row per task_id and mirrors the fields needed by the
    recent-events endpoint without requiring window functions over the full
    task_events table.
    """
    __tablename__ = 'task_latest'

    task_id = Column(String(255), primary_key=True)
    event_id = Column(Integer, nullable=False)

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
    retried_by = Column(Text)  # JSON serialized list of task IDs
    is_retry = Column(Boolean, default=False)
    has_retries = Column(Boolean, default=False)
    retry_count = Column(Integer, default=0)

    is_orphan = Column(Boolean, default=False, index=True)
    orphaned_at = Column(DateTime(timezone=True))
    resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime(timezone=True))
    resolved_by = Column(String(255))

    __table_args__ = (
        Index('idx_task_latest_timestamp', 'timestamp', 'task_id'),
        Index('idx_task_latest_hostname_ts', 'hostname', 'timestamp'),
        Index('idx_task_latest_routing_ts', 'routing_key', 'timestamp'),
        Index('idx_task_latest_event_type_ts', 'event_type', 'timestamp'),
    )

class TaskResolutionDB(Base):
    """Tracks manual resolution state per task."""
    __tablename__ = 'task_resolutions'

    task_id = Column(String(255), primary_key=True)
    resolved = Column(Boolean, default=True, nullable=False)
    resolved_at = Column(DateTime(timezone=True))
    resolved_by = Column(String(255))

    __table_args__ = (
        Index('idx_task_resolved_flag', 'resolved'),
    )

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


class UserDB(Base):
    """SQLAlchemy model for authenticated users."""
    __tablename__ = 'users'

    id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255))
    provider = Column(String(50), nullable=False, index=True)
    provider_account_id = Column(String(255), index=True)
    avatar_url = Column(String(512))
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    last_login_at = Column(DateTime(timezone=True))

    sessions = relationship("UserSessionDB", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_users_provider_email', 'provider', 'email'),
        UniqueConstraint('provider', 'provider_account_id', name='uq_users_provider_account'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'provider': self.provider,
            'provider_account_id': self.provider_account_id,
            'avatar_url': self.avatar_url,
            'is_active': self.is_active,
            'created_at': ensure_utc_isoformat(self.created_at),
            'updated_at': ensure_utc_isoformat(self.updated_at),
            'last_login_at': ensure_utc_isoformat(self.last_login_at),
        }


class UserSessionDB(Base):
    """SQLAlchemy model for anonymous user sessions."""
    __tablename__ = 'user_sessions'

    session_id = Column(String(36), primary_key=True)  # UUID

    user_id = Column(String(36), ForeignKey('users.id', ondelete='SET NULL'), index=True, nullable=True)
    auth_provider = Column(String(50), index=True)

    access_token_hash = Column(String(128), index=True, nullable=True)
    refresh_token_hash = Column(String(128), index=True, nullable=True)
    access_token_expires_at = Column(DateTime(timezone=True))
    refresh_token_expires_at = Column(DateTime(timezone=True))
    token_scopes = Column(JSON, default=list)

    # User preferences
    active_environment_id = Column(String(36), index=True)  # FK to environments.id (nullable)
    preferences = Column(JSON, default=dict)  # Flexible JSON for various settings

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_active = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False, index=True)

    user = relationship("UserDB", back_populates="sessions")

    __table_args__ = (
        Index('idx_session_last_active', 'last_active'),
        Index('idx_session_user', 'user_id'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'session_id': self.session_id,
            'active_environment_id': self.active_environment_id,
            'user_id': self.user_id,
            'auth_provider': self.auth_provider,
            'preferences': self.preferences or {},
            'created_at': ensure_utc_isoformat(self.created_at),
            'last_active': ensure_utc_isoformat(self.last_active),
            'access_token_expires_at': ensure_utc_isoformat(self.access_token_expires_at),
            'refresh_token_expires_at': ensure_utc_isoformat(self.refresh_token_expires_at),
            'token_scopes': self.token_scopes or [],
        }


class WorkflowDB(Base):
    """SQLAlchemy model for workflows."""
    __tablename__ = 'workflows'

    id = Column(String(36), primary_key=True)  # UUID
    name = Column(String(255), nullable=False)
    description = Column(Text)
    enabled = Column(Boolean, default=True)

    # Trigger configuration
    trigger_type = Column(String(50), nullable=False, index=True)
    trigger_config = Column(JSON)

    # Condition filters (JSON)
    conditions = Column(JSON)

    # Actions to execute (JSON array)
    actions = Column(JSON, nullable=False)
    circuit_breaker_config = Column(JSON)

    # Execution settings
    priority = Column(Integer, default=100, index=True)
    max_executions_per_hour = Column(Integer)
    cooldown_seconds = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    created_by = Column(String(255))

    # Statistics (denormalized for performance)
    execution_count = Column(Integer, default=0)
    last_executed_at = Column(DateTime(timezone=True))
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)

    __table_args__ = (
        Index('idx_workflows_enabled', 'enabled'),
        Index('idx_workflows_enabled_trigger', 'enabled', 'trigger_type'),
        Index('idx_workflows_priority', 'priority'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'enabled': self.enabled,
            'trigger_type': self.trigger_type,
            'trigger_config': self.trigger_config or {},
            'conditions': self.conditions,
            'actions': self.actions,
            'circuit_breaker': self.circuit_breaker_config,
            'priority': self.priority,
            'max_executions_per_hour': self.max_executions_per_hour,
            'cooldown_seconds': self.cooldown_seconds,
            'created_at': ensure_utc_isoformat(self.created_at),
            'updated_at': ensure_utc_isoformat(self.updated_at),
            'created_by': self.created_by,
            'execution_count': self.execution_count,
            'last_executed_at': ensure_utc_isoformat(self.last_executed_at),
            'success_count': self.success_count,
            'failure_count': self.failure_count,
        }


class WorkflowExecutionDB(Base):
    """SQLAlchemy model for workflow executions."""
    __tablename__ = 'workflow_executions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_id = Column(String(36), nullable=False, index=True)

    # Trigger context
    triggered_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    trigger_type = Column(String(50), nullable=False, index=True)
    trigger_event = Column(JSON, nullable=False)

    # Execution status
    status = Column(String(20), nullable=False, index=True)  # "pending", "running", "completed", "failed", "rate_limited"

    # Results
    actions_executed = Column(JSON)
    error_message = Column(Text)
    stack_trace = Column(Text)

    # Performance
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_ms = Column(Integer)
    circuit_breaker_key = Column(String(255), index=True)

    # Context for debugging
    workflow_snapshot = Column(JSON)

    __table_args__ = (
        Index('idx_workflow_exec_workflow_id', 'workflow_id'),
        Index('idx_workflow_exec_workflow_time', 'workflow_id', 'triggered_at'),
        Index('idx_workflow_exec_status', 'status', 'triggered_at'),
        Index('idx_workflow_exec_circuit_key', 'workflow_id', 'circuit_breaker_key', 'triggered_at'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'workflow_id': self.workflow_id,
            'triggered_at': ensure_utc_isoformat(self.triggered_at),
            'trigger_type': self.trigger_type,
            'trigger_event': self.trigger_event,
            'status': self.status,
            'actions_executed': self.actions_executed,
            'error_message': self.error_message,
            'stack_trace': self.stack_trace,
            'started_at': ensure_utc_isoformat(self.started_at),
            'completed_at': ensure_utc_isoformat(self.completed_at),
            'duration_ms': self.duration_ms,
            'workflow_snapshot': self.workflow_snapshot,
            'circuit_breaker_key': self.circuit_breaker_key,
        }


class ActionConfigDB(Base):
    """SQLAlchemy model for action configurations."""
    __tablename__ = 'action_configs'

    id = Column(String(36), primary_key=True)  # UUID
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text)

    # Action type
    action_type = Column(String(50), nullable=False, index=True)

    # Configuration (encrypted sensitive fields)
    config = Column(JSON, nullable=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    created_by = Column(String(255))

    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True))

    __table_args__ = (
        Index('idx_action_configs_action_type', 'action_type'),
        Index('idx_action_configs_name', 'name'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'action_type': self.action_type,
            'config': self.config,
            'created_at': ensure_utc_isoformat(self.created_at),
            'updated_at': ensure_utc_isoformat(self.updated_at),
            'created_by': self.created_by,
            'usage_count': self.usage_count,
            'last_used_at': ensure_utc_isoformat(self.last_used_at),
        }


class AppSettingDB(Base):
    """Key-value application settings stored in the database."""
    __tablename__ = 'app_settings'

    key = Column(String(255), primary_key=True)
    value = Column(JSON, nullable=False)
    value_type = Column(String(50), nullable=False, default="string")
    label = Column(String(255))
    description = Column(Text)
    category = Column(String(100))
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        Index('idx_app_settings_category', 'category'),
        Index('idx_app_settings_updated_at', 'updated_at'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'key': self.key,
            'value': self.value,
            'value_type': self.value_type,
            'label': self.label,
            'description': self.description,
            'category': self.category,
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
