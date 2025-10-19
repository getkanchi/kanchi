import unittest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from database import Base, DatabaseManager, TaskEventDB, WorkerEventDB, RetryRelationshipDB
from models import TaskEvent, WorkerEvent


class DatabaseTestCase(unittest.TestCase):

    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(self.engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.session: Session = SessionLocal()

    def tearDown(self):
        self.session.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def create_task_event(
        self,
        task_id: str = "test-task-123",
        task_name: str = "tasks.example",
        event_type: str = "task-started",
        timestamp: datetime = None,
        hostname: str = "worker1",
        routing_key: str = "default",
        queue: str = None,
        runtime: float = None,
        exception: str = None,
        is_orphan: bool = False,
        orphaned_at: datetime = None,
        **kwargs
    ) -> TaskEvent:
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        return TaskEvent(
            task_id=task_id,
            task_name=task_name,
            event_type=event_type,
            timestamp=timestamp,
            hostname=hostname,
            routing_key=routing_key,
            queue=queue,
            runtime=runtime,
            exception=exception,
            is_orphan=is_orphan,
            orphaned_at=orphaned_at,
            **kwargs
        )

    def create_task_event_db(
        self,
        task_id: str = "test-task-123",
        task_name: str = "tasks.example",
        event_type: str = "task-started",
        timestamp: datetime = None,
        hostname: str = "worker1",
        routing_key: str = "default",
        queue: str = None,
        runtime: float = None,
        exception: str = None,
        is_orphan: bool = False,
        orphaned_at: datetime = None,
        **kwargs
    ) -> TaskEventDB:
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        event = TaskEventDB(
            task_id=task_id,
            task_name=task_name,
            event_type=event_type,
            timestamp=timestamp,
            hostname=hostname,
            routing_key=routing_key,
            queue=queue,
            runtime=runtime,
            exception=exception,
            is_orphan=is_orphan,
            orphaned_at=orphaned_at,
            **kwargs
        )
        self.session.add(event)
        self.session.commit()
        return event

    def create_worker_event_db(
        self,
        hostname: str = "worker1",
        event_type: str = "worker-heartbeat",
        timestamp: datetime = None,
        status: str = "online",
        **kwargs
    ) -> WorkerEventDB:
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        event = WorkerEventDB(
            hostname=hostname,
            event_type=event_type,
            timestamp=timestamp,
            status=status,
            **kwargs
        )
        self.session.add(event)
        self.session.commit()
        return event

    def create_retry_relationship(
        self,
        task_id: str,
        original_id: str,
        retry_chain: list = None,
        total_retries: int = 0
    ) -> RetryRelationshipDB:
        if retry_chain is None:
            retry_chain = [original_id, task_id]

        relationship = RetryRelationshipDB(
            task_id=task_id,
            original_id=original_id,
            retry_chain=retry_chain,
            total_retries=total_retries
        )
        self.session.add(relationship)
        self.session.commit()
        return relationship

    def get_all_task_events(self) -> list:
        return self.session.query(TaskEventDB).all()

    def get_task_events_by_id(self, task_id: str) -> list:
        return self.session.query(TaskEventDB).filter_by(task_id=task_id).all()

    def assert_task_event_exists(self, task_id: str, event_type: str = None):
        query = self.session.query(TaskEventDB).filter_by(task_id=task_id)
        if event_type:
            query = query.filter_by(event_type=event_type)

        event = query.first()
        self.assertIsNotNone(event, f"Task event {task_id} ({event_type}) not found in database")
        return event


class ServiceTestCase(DatabaseTestCase):

    def setUp(self):
        super().setUp()
