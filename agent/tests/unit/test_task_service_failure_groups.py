import unittest
from datetime import datetime, timezone, timedelta

from models import TaskEvent
from services.task_service import TaskService
from tests.base import DatabaseTestCase


class TestTaskServiceFailureGroups(DatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.service = TaskService(self.session)
        self.now = datetime.now(timezone.utc)

    def _save_failed_event(self, task_id: str, when: datetime, exception: str, queue: str = 'critical', hostname: str = 'worker-a'):
        event = TaskEvent(
            task_id=task_id,
            task_name='tasks.example',
            event_type='task-failed',
            timestamp=when,
            exception=exception,
            traceback=f'Traceback\nValueError: {exception}',
            queue=queue,
            hostname=hostname,
        )
        return self.service.save_task_event(event)

    def test_groups_related_failures_with_stable_fingerprint(self):
        self._save_failed_event('task-1', self.now - timedelta(minutes=10), 'customer 123 missing')
        self._save_failed_event('task-2', self.now - timedelta(minutes=5), 'customer 456 missing')

        groups = self.service.get_recent_failure_groups(hours=24)

        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].failure_count, 2)
        self.assertEqual(groups[0].last_task_id, 'task-2')
        self.assertEqual(groups[0].latest_failure.failure_group_id, groups[0].id)

    def test_separates_distinct_workers_or_queues(self):
        self._save_failed_event('task-1', self.now - timedelta(minutes=10), 'boom', queue='critical', hostname='worker-a')
        self._save_failed_event('task-2', self.now - timedelta(minutes=5), 'boom', queue='bulk', hostname='worker-a')

        groups = self.service.get_recent_failure_groups(hours=24)
        self.assertEqual(len(groups), 2)

    def test_group_drilldown_returns_all_failed_events(self):
        self._save_failed_event('task-1', self.now - timedelta(minutes=10), 'customer 123 missing')
        self._save_failed_event('task-2', self.now - timedelta(minutes=5), 'customer 456 missing')

        group = self.service.get_recent_failure_groups(hours=24)[0]
        events = self.service.get_failure_group_events(group.id)

        self.assertEqual([event.task_id for event in events], ['task-2', 'task-1'])


if __name__ == '__main__':
    unittest.main()
