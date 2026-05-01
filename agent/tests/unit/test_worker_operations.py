from datetime import datetime, timedelta, timezone

from database import TaskLatestDB, AppSettingDB
from services.worker_service import WorkerService
from tests.base import DatabaseTestCase


class TestWorkerOperations(DatabaseTestCase):
    def test_builds_queue_and_worker_surface_with_notes(self):
        now = datetime.now(timezone.utc)
        self.session.add_all([
            TaskLatestDB(task_id='active-1', event_id=1, task_name='tasks.alpha', event_type='task-started', timestamp=now, hostname='worker-a', queue='priority'),
            TaskLatestDB(task_id='active-2', event_id=2, task_name='tasks.alpha', event_type='task-received', timestamp=now, hostname='worker-a', queue='priority'),
            TaskLatestDB(task_id='fail-1', event_id=3, task_name='tasks.alpha', event_type='task-failed', timestamp=now, hostname='worker-a', queue='priority'),
            TaskLatestDB(task_id='done-1', event_id=4, task_name='tasks.alpha', event_type='task-succeeded', timestamp=now - timedelta(minutes=5), hostname='worker-a', queue='priority'),
            AppSettingDB(key='operator_notes.worker.worker-a', value={'entity_type': 'worker', 'entity_key': 'worker-a', 'note': 'Investigating memory pressure', 'author': 'ops'}, value_type='json', category='operator_notes'),
        ])
        self.session.commit()

        service = WorkerService(self.session)
        surface = service.get_queue_worker_surface({
            'worker-a': {'status': 'online', 'active': 2, 'processed': 11},
        })

        self.assertEqual(len(surface.queues), 1)
        self.assertEqual(surface.queues[0].queue_name, 'priority')
        self.assertEqual(surface.queues[0].active_tasks, 2)
        self.assertEqual(surface.queues[0].recent_failures, 1)
        self.assertEqual(surface.queues[0].throughput_last_hour, 1)

        self.assertEqual(len(surface.workers), 1)
        self.assertEqual(surface.workers[0].hostname, 'worker-a')
        self.assertEqual(surface.workers[0].active_queues, ['priority'])
        self.assertEqual(surface.workers[0].recent_failures, 1)

        self.assertEqual(len(surface.notes), 1)
        self.assertEqual(surface.notes[0].entity_key, 'worker-a')

    def test_save_operator_note_upserts(self):
        service = WorkerService(self.session)
        note = service.save_operator_note('queue', 'priority', 'Drain after deploy', 'bernhard')
        self.assertEqual(note.entity_type, 'queue')
        self.assertEqual(note.entity_key, 'priority')
        self.assertEqual(note.note, 'Drain after deploy')

        updated = service.save_operator_note('queue', 'priority', 'Drain completed', 'bernhard')
        self.assertEqual(updated.note, 'Drain completed')
        rows = self.session.query(AppSettingDB).filter_by(key='operator_notes.queue.priority').all()
        self.assertEqual(len(rows), 1)
