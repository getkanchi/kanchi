import unittest
from unittest.mock import Mock
from sqlalchemy.orm import Query
from sqlalchemy import or_

from services.utils import parse_filter_string, GenericFilter, EnvironmentFilter
from database import TaskEventDB
from tests.base import DatabaseTestCase


class TestParseFilterString(unittest.TestCase):

    def test_parse_single_filter_with_is_operator(self):
        result = parse_filter_string("state:is:success")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['field'], 'state')
        self.assertEqual(result[0]['operator'], 'is')
        self.assertEqual(result[0]['values'], ['success'])

    def test_parse_single_filter_implicit_is_operator(self):
        result = parse_filter_string("state:success")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['field'], 'state')
        self.assertEqual(result[0]['operator'], 'is')
        self.assertEqual(result[0]['values'], ['success'])

    def test_parse_filter_with_contains_operator(self):
        result = parse_filter_string("worker:contains:celery")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['field'], 'worker')
        self.assertEqual(result[0]['operator'], 'contains')
        self.assertEqual(result[0]['values'], ['celery'])

    def test_parse_filter_with_starts_operator(self):
        result = parse_filter_string("task:starts:tasks.")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['field'], 'task')
        self.assertEqual(result[0]['operator'], 'starts')
        self.assertEqual(result[0]['values'], ['tasks.'])

    def test_parse_filter_with_not_operator(self):
        result = parse_filter_string("state:not:failed")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['field'], 'state')
        self.assertEqual(result[0]['operator'], 'not')
        self.assertEqual(result[0]['values'], ['failed'])

    def test_parse_filter_with_in_operator_single_value(self):
        result = parse_filter_string("state:in:success")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['field'], 'state')
        self.assertEqual(result[0]['operator'], 'in')
        self.assertEqual(result[0]['values'], ['success'])

    def test_parse_filter_with_in_operator_multiple_values(self):
        result = parse_filter_string("state:in:success,failed,pending")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['field'], 'state')
        self.assertEqual(result[0]['operator'], 'in')
        self.assertEqual(result[0]['values'], ['success', 'failed', 'pending'])

    def test_parse_filter_with_not_in_operator(self):
        result = parse_filter_string("state:not_in:success,failed")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['field'], 'state')
        self.assertEqual(result[0]['operator'], 'not_in')
        self.assertEqual(result[0]['values'], ['success', 'failed'])

    def test_parse_multiple_filters_separated_by_semicolon(self):
        result = parse_filter_string("state:is:success;worker:contains:celery")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['field'], 'state')
        self.assertEqual(result[0]['operator'], 'is')
        self.assertEqual(result[1]['field'], 'worker')
        self.assertEqual(result[1]['operator'], 'contains')

    def test_parse_filter_with_whitespace_trimming(self):
        result = parse_filter_string(" state : is : success ")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['field'], 'state')
        self.assertEqual(result[0]['operator'], 'is')
        self.assertEqual(result[0]['values'], ['success'])

    def test_parse_filter_with_comma_separated_values_trimming(self):
        result = parse_filter_string("state:in:success , failed , pending")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['values'], ['success', 'failed', 'pending'])

    def test_parse_empty_string_returns_empty_list(self):
        result = parse_filter_string("")
        self.assertEqual(result, [])

    def test_parse_none_returns_empty_list(self):
        result = parse_filter_string(None)
        self.assertEqual(result, [])

    def test_parse_filter_skips_empty_parts(self):
        result = parse_filter_string("state:is:success;;worker:contains:celery")
        self.assertEqual(len(result), 2)

    def test_parse_filter_skips_malformed_parts(self):
        result = parse_filter_string("state:is:success;incomplete;worker:contains:celery")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['field'], 'state')
        self.assertEqual(result[1]['field'], 'worker')

    def test_parse_filter_handles_colon_in_value(self):
        result = parse_filter_string("message:contains:error:critical")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['field'], 'message')
        self.assertEqual(result[0]['operator'], 'contains')
        self.assertEqual(result[0]['values'], ['error:critical'])

    def test_parse_filter_field_is_lowercase(self):
        result = parse_filter_string("STATE:is:success")
        self.assertEqual(result[0]['field'], 'state')

    def test_parse_filter_operator_is_lowercase(self):
        result = parse_filter_string("state:CONTAINS:success")
        self.assertEqual(result[0]['operator'], 'contains')


class TestGenericFilter(DatabaseTestCase):

    def test_apply_is_operator(self):
        self.create_task_event_db(task_id="task-1", task_name="tasks.success")
        self.create_task_event_db(task_id="task-2", task_name="tasks.failed")

        query = self.session.query(TaskEventDB)
        filtered = GenericFilter.apply(query, TaskEventDB.task_name, 'is', ['tasks.success'])
        results = filtered.all()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].task_name, 'tasks.success')

    def test_apply_is_operator_with_empty_string(self):
        self.create_task_event_db(task_id="task-1", task_name="tasks.success")

        query = self.session.query(TaskEventDB)
        filtered = GenericFilter.apply(query, TaskEventDB.task_name, '', ['tasks.success'])
        results = filtered.all()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].task_name, 'tasks.success')

    def test_apply_not_operator(self):
        self.create_task_event_db(task_id="task-1", task_name="tasks.success")
        self.create_task_event_db(task_id="task-2", task_name="tasks.failed")

        query = self.session.query(TaskEventDB)
        filtered = GenericFilter.apply(query, TaskEventDB.task_name, 'not', ['tasks.success'])
        results = filtered.all()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].task_name, 'tasks.failed')

    def test_apply_contains_operator_case_insensitive(self):
        self.create_task_event_db(task_id="task-1", task_name="tasks.user_login")
        self.create_task_event_db(task_id="task-2", task_name="tasks.admin_action")

        query = self.session.query(TaskEventDB)
        filtered = GenericFilter.apply(query, TaskEventDB.task_name, 'contains', ['USER'])
        results = filtered.all()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].task_name, 'tasks.user_login')

    def test_apply_starts_operator_case_insensitive(self):
        self.create_task_event_db(task_id="task-1", task_name="tasks.user_login")
        self.create_task_event_db(task_id="task-2", task_name="admin.action")

        query = self.session.query(TaskEventDB)
        filtered = GenericFilter.apply(query, TaskEventDB.task_name, 'starts', ['TASKS'])
        results = filtered.all()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].task_name, 'tasks.user_login')

    def test_apply_in_operator_with_single_value(self):
        self.create_task_event_db(task_id="task-1", task_name="tasks.success")
        self.create_task_event_db(task_id="task-2", task_name="tasks.failed")

        query = self.session.query(TaskEventDB)
        filtered = GenericFilter.apply(query, TaskEventDB.task_name, 'in', ['tasks.success'])
        results = filtered.all()

        self.assertEqual(len(results), 1)

    def test_apply_in_operator_with_multiple_values(self):
        self.create_task_event_db(task_id="task-1", task_name="tasks.success")
        self.create_task_event_db(task_id="task-2", task_name="tasks.failed")
        self.create_task_event_db(task_id="task-3", task_name="tasks.pending")

        query = self.session.query(TaskEventDB)
        filtered = GenericFilter.apply(
            query, TaskEventDB.task_name, 'in', ['tasks.success', 'tasks.failed']
        )
        results = filtered.all()

        self.assertEqual(len(results), 2)
        task_names = {r.task_name for r in results}
        self.assertEqual(task_names, {'tasks.success', 'tasks.failed'})

    def test_apply_not_in_operator(self):
        self.create_task_event_db(task_id="task-1", task_name="tasks.success")
        self.create_task_event_db(task_id="task-2", task_name="tasks.failed")
        self.create_task_event_db(task_id="task-3", task_name="tasks.pending")

        query = self.session.query(TaskEventDB)
        filtered = GenericFilter.apply(
            query, TaskEventDB.task_name, 'not_in', ['tasks.success', 'tasks.failed']
        )
        results = filtered.all()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].task_name, 'tasks.pending')

    def test_apply_returns_unmodified_query_for_empty_values(self):
        self.create_task_event_db(task_id="task-1", task_name="tasks.success")
        self.create_task_event_db(task_id="task-2", task_name="tasks.failed")

        query = self.session.query(TaskEventDB)
        filtered = GenericFilter.apply(query, TaskEventDB.task_name, 'is', [])
        results = filtered.all()

        self.assertEqual(len(results), 2)

    def test_apply_with_value_mapper_that_filters_out_values(self):
        self.create_task_event_db(task_id="task-1", task_name="tasks.success")

        query = self.session.query(TaskEventDB)
        filtered = GenericFilter.apply(
            query,
            TaskEventDB.task_name,
            'is',
            ['invalid'],
            value_mapper=lambda x: None
        )
        results = filtered.all()

        self.assertEqual(len(results), 1)

    def test_apply_with_value_mapper_that_transforms_values(self):
        self.create_task_event_db(task_id="task-1", task_name="TASKS.SUCCESS")

        query = self.session.query(TaskEventDB)
        filtered = GenericFilter.apply(
            query,
            TaskEventDB.task_name,
            'is',
            ['tasks.success'],
            value_mapper=lambda x: x.upper()
        )
        results = filtered.all()

        self.assertEqual(len(results), 1)

    def test_apply_unknown_operator_returns_unmodified_query(self):
        self.create_task_event_db(task_id="task-1", task_name="tasks.success")
        self.create_task_event_db(task_id="task-2", task_name="tasks.failed")

        query = self.session.query(TaskEventDB)
        filtered = GenericFilter.apply(query, TaskEventDB.task_name, 'unknown_op', ['tasks.success'])
        results = filtered.all()

        self.assertEqual(len(results), 2)


class TestEnvironmentFilter(DatabaseTestCase):

    def test_apply_returns_unmodified_query_when_no_environment(self):
        self.create_task_event_db(task_id="task-1", queue="queue1", hostname="worker1")
        self.create_task_event_db(task_id="task-2", queue="queue2", hostname="worker2")

        query = self.session.query(TaskEventDB)
        filtered = EnvironmentFilter.apply(query, None)
        results = filtered.all()

        self.assertEqual(len(results), 2)

    def test_apply_filters_by_single_queue_pattern(self):
        self.create_task_event_db(task_id="task-1", queue="prod-queue", hostname="worker1")
        self.create_task_event_db(task_id="task-2", queue="dev-queue", hostname="worker1")

        env = Mock()
        env.queue_patterns = ['prod-*']
        env.worker_patterns = None

        query = self.session.query(TaskEventDB)
        filtered = EnvironmentFilter.apply(query, env)
        results = filtered.all()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].queue, 'prod-queue')

    def test_apply_filters_by_multiple_queue_patterns(self):
        self.create_task_event_db(task_id="task-1", queue="prod-queue", hostname="worker1")
        self.create_task_event_db(task_id="task-2", queue="staging-queue", hostname="worker1")
        self.create_task_event_db(task_id="task-3", queue="dev-queue", hostname="worker1")

        env = Mock()
        env.queue_patterns = ['prod-*', 'staging-*']
        env.worker_patterns = None

        query = self.session.query(TaskEventDB)
        filtered = EnvironmentFilter.apply(query, env)
        results = filtered.all()

        self.assertEqual(len(results), 2)
        queues = {r.queue for r in results}
        self.assertEqual(queues, {'prod-queue', 'staging-queue'})

    def test_apply_filters_by_single_worker_pattern(self):
        self.create_task_event_db(task_id="task-1", queue="queue1", hostname="celery-worker-1")
        self.create_task_event_db(task_id="task-2", queue="queue1", hostname="other-worker-1")

        env = Mock()
        env.queue_patterns = None
        env.worker_patterns = ['celery-*']

        query = self.session.query(TaskEventDB)
        filtered = EnvironmentFilter.apply(query, env)
        results = filtered.all()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].hostname, 'celery-worker-1')

    def test_apply_filters_by_multiple_worker_patterns(self):
        self.create_task_event_db(task_id="task-1", queue="queue1", hostname="celery-1")
        self.create_task_event_db(task_id="task-2", queue="queue1", hostname="worker-1")
        self.create_task_event_db(task_id="task-3", queue="queue1", hostname="other-1")

        env = Mock()
        env.queue_patterns = None
        env.worker_patterns = ['celery-*', 'worker-*']

        query = self.session.query(TaskEventDB)
        filtered = EnvironmentFilter.apply(query, env)
        results = filtered.all()

        self.assertEqual(len(results), 2)
        hostnames = {r.hostname for r in results}
        self.assertEqual(hostnames, {'celery-1', 'worker-1'})

    def test_apply_filters_by_queue_and_worker_patterns_combined(self):
        self.create_task_event_db(task_id="task-1", queue="prod-queue", hostname="celery-1")
        self.create_task_event_db(task_id="task-2", queue="dev-queue", hostname="celery-1")
        self.create_task_event_db(task_id="task-3", queue="prod-queue", hostname="other-1")

        env = Mock()
        env.queue_patterns = ['prod-*']
        env.worker_patterns = ['celery-*']

        query = self.session.query(TaskEventDB)
        filtered = EnvironmentFilter.apply(query, env)
        results = filtered.all()

        self.assertEqual(len(results), 3)
        queues = {r.queue for r in results}
        hostnames = {r.hostname for r in results}
        self.assertIn('prod-queue', queues)
        self.assertIn('celery-1', hostnames)

    def test_apply_with_wildcard_question_mark_pattern(self):
        self.create_task_event_db(task_id="task-1", queue="q1", hostname="worker1")
        self.create_task_event_db(task_id="task-2", queue="q2", hostname="worker1")
        self.create_task_event_db(task_id="task-3", queue="queue1", hostname="worker1")

        env = Mock()
        env.queue_patterns = ['q?']
        env.worker_patterns = None

        query = self.session.query(TaskEventDB)
        filtered = EnvironmentFilter.apply(query, env)
        results = filtered.all()

        self.assertEqual(len(results), 2)
        queues = {r.queue for r in results}
        self.assertEqual(queues, {'q1', 'q2'})

    def test_apply_with_empty_queue_patterns(self):
        self.create_task_event_db(task_id="task-1", queue="queue1", hostname="worker1")
        self.create_task_event_db(task_id="task-2", queue="queue2", hostname="worker1")

        env = Mock()
        env.queue_patterns = []
        env.worker_patterns = None

        query = self.session.query(TaskEventDB)
        filtered = EnvironmentFilter.apply(query, env)
        results = filtered.all()

        self.assertEqual(len(results), 2)

    def test_apply_with_empty_worker_patterns(self):
        self.create_task_event_db(task_id="task-1", queue="queue1", hostname="worker1")
        self.create_task_event_db(task_id="task-2", queue="queue1", hostname="worker2")

        env = Mock()
        env.queue_patterns = None
        env.worker_patterns = []

        query = self.session.query(TaskEventDB)
        filtered = EnvironmentFilter.apply(query, env)
        results = filtered.all()

        self.assertEqual(len(results), 2)


if __name__ == '__main__':
    unittest.main()
