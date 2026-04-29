import unittest
from datetime import datetime, timezone, timedelta

from services.task_service import TaskService
from tests.base import DatabaseTestCase


class TestTaskServiceIncidentSummaries(DatabaseTestCase):

    def setUp(self):
        super().setUp()
        self.service = TaskService(self.session)
        self.now = datetime.now(timezone.utc)

    def test_groups_failures_by_task_name_and_collects_retry_metadata(self):
        self.create_task_event_db(
            task_id='alpha-1',
            task_name='tasks.alpha',
            event_type='task-failed',
            timestamp=self.now - timedelta(minutes=20),
            hostname='worker-a',
            has_retries=True,
            retry_count=2,
            retried_by='["alpha-r1", "alpha-r2"]',
            exception='boom',
        )
        self.create_task_event_db(
            task_id='alpha-2',
            task_name='tasks.alpha',
            event_type='task-failed',
            timestamp=self.now - timedelta(minutes=5),
            hostname='worker-b',
            has_retries=False,
            retry_count=0,
            exception='still broken',
        )

        summaries = self.service.get_incident_summaries(hours=24)

        self.assertEqual(len(summaries), 1)
        summary = summaries[0]
        self.assertEqual(summary.task_name, 'tasks.alpha')
        self.assertEqual(summary.failure_count, 2)
        self.assertEqual(summary.retried_task_count, 1)
        self.assertEqual(summary.retry_attempt_count, 2)
        self.assertEqual(summary.worker_count, 2)
        self.assertEqual(summary.affected_workers, ['worker-a', 'worker-b'])
        self.assertEqual(summary.latest_task_id, 'alpha-2')
        self.assertEqual(summary.latest_exception, 'still broken')
        self.assertEqual(summary.latest_status, 'recovering')
        self.assertEqual(summary.recent_failure_count, 2)

    def test_ranks_busier_incidents_ahead_of_smaller_clusters(self):
        for index in range(4):
            self.create_task_event_db(
                task_id=f'critical-{index}',
                task_name='tasks.critical',
                event_type='task-failed',
                timestamp=self.now - timedelta(minutes=10 + index),
                hostname=f'worker-{index}',
                exception='critical path failed',
            )

        self.create_task_event_db(
            task_id='minor-1',
            task_name='tasks.minor',
            event_type='task-failed',
            timestamp=self.now - timedelta(hours=2),
            hostname='worker-z',
            exception='minor issue',
        )

        summaries = self.service.get_incident_summaries(hours=24)

        self.assertEqual([summary.task_name for summary in summaries], ['tasks.critical', 'tasks.minor'])
        self.assertIn(summaries[0].severity, {'high', 'critical'})
        self.assertIn(summaries[1].severity, {'low', 'medium'})
        self.assertGreater(summaries[0].urgency_score, summaries[1].urgency_score)


if __name__ == '__main__':
    unittest.main()
