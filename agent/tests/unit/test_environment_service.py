import unittest
from datetime import datetime, timezone

from services.environment_service import EnvironmentService
from models import EnvironmentCreate, EnvironmentUpdate
from tests.base import DatabaseTestCase


class TestEnvironmentService(DatabaseTestCase):

    def setUp(self):
        super().setUp()
        self.service = EnvironmentService(self.session)

    def test_create_environment_basic(self):
        env_create = EnvironmentCreate(
            name="Production",
            description="Production environment",
            queue_patterns=["prod-*"],
            worker_patterns=["prod-worker-*"],
            is_default=False
        )

        result = self.service.create_environment(env_create)

        self.assertIsNotNone(result.id)
        self.assertEqual(result.name, "Production")
        self.assertEqual(result.description, "Production environment")
        self.assertEqual(result.queue_patterns, ["prod-*"])
        self.assertEqual(result.worker_patterns, ["prod-worker-*"])
        self.assertFalse(result.is_default)

    def test_create_environment_as_default_unsets_other_defaults(self):
        env1 = EnvironmentCreate(
            name="Environment 1",
            queue_patterns=["env1-*"],
            is_default=True
        )
        self.service.create_environment(env1)

        env2 = EnvironmentCreate(
            name="Environment 2",
            queue_patterns=["env2-*"],
            is_default=True
        )
        result2 = self.service.create_environment(env2)

        environments = self.service.list_environments()
        default_envs = [e for e in environments if e.is_default]

        self.assertEqual(len(default_envs), 1)
        self.assertEqual(default_envs[0].name, "Environment 2")
        self.assertTrue(result2.is_default)

    def test_create_environment_with_minimal_fields(self):
        env_create = EnvironmentCreate(
            name="Minimal",
            is_default=False
        )

        result = self.service.create_environment(env_create)

        self.assertEqual(result.name, "Minimal")
        self.assertIsNone(result.description)
        self.assertEqual(result.queue_patterns, [])
        self.assertEqual(result.worker_patterns, [])

    def test_list_environments_empty(self):
        result = self.service.list_environments()
        self.assertEqual(len(result), 0)

    def test_list_environments_orders_by_default_then_name(self):
        self.service.create_environment(EnvironmentCreate(
            name="Zebra",
            is_default=False
        ))
        self.service.create_environment(EnvironmentCreate(
            name="Alpha",
            is_default=True
        ))
        self.service.create_environment(EnvironmentCreate(
            name="Beta",
            is_default=False
        ))

        result = self.service.list_environments()

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].name, "Alpha")
        self.assertTrue(result[0].is_default)
        self.assertEqual(result[1].name, "Beta")
        self.assertEqual(result[2].name, "Zebra")

    def test_get_environment_exists(self):
        created = self.service.create_environment(EnvironmentCreate(
            name="Test Env",
            is_default=False
        ))

        result = self.service.get_environment(created.id)

        self.assertIsNotNone(result)
        self.assertEqual(result.id, created.id)
        self.assertEqual(result.name, "Test Env")

    def test_get_environment_not_found(self):
        result = self.service.get_environment("nonexistent-id")
        self.assertIsNone(result)

    def test_update_environment_name(self):
        created = self.service.create_environment(EnvironmentCreate(
            name="Original Name",
            is_default=False
        ))

        update = EnvironmentUpdate(name="Updated Name")
        result = self.service.update_environment(created.id, update)

        self.assertIsNotNone(result)
        self.assertEqual(result.name, "Updated Name")

    def test_update_environment_description(self):
        created = self.service.create_environment(EnvironmentCreate(
            name="Test",
            description="Original",
            is_default=False
        ))

        update = EnvironmentUpdate(description="Updated description")
        result = self.service.update_environment(created.id, update)

        self.assertEqual(result.description, "Updated description")

    def test_update_environment_queue_patterns(self):
        created = self.service.create_environment(EnvironmentCreate(
            name="Test",
            queue_patterns=["old-*"],
            is_default=False
        ))

        update = EnvironmentUpdate(queue_patterns=["new-*", "other-*"])
        result = self.service.update_environment(created.id, update)

        self.assertEqual(result.queue_patterns, ["new-*", "other-*"])

    def test_update_environment_worker_patterns(self):
        created = self.service.create_environment(EnvironmentCreate(
            name="Test",
            worker_patterns=["old-worker-*"],
            is_default=False
        ))

        update = EnvironmentUpdate(worker_patterns=["new-worker-*"])
        result = self.service.update_environment(created.id, update)

        self.assertEqual(result.worker_patterns, ["new-worker-*"])

    def test_update_environment_set_as_default_unsets_others(self):
        env1 = self.service.create_environment(EnvironmentCreate(
            name="Env 1",
            is_default=True
        ))
        env2 = self.service.create_environment(EnvironmentCreate(
            name="Env 2",
            is_default=False
        ))

        update = EnvironmentUpdate(is_default=True)
        self.service.update_environment(env2.id, update)

        result1 = self.service.get_environment(env1.id)
        result2 = self.service.get_environment(env2.id)

        self.assertFalse(result1.is_default)
        self.assertTrue(result2.is_default)

    def test_update_environment_updates_timestamp(self):
        created = self.service.create_environment(EnvironmentCreate(
            name="Test",
            is_default=False
        ))

        original_updated_at = created.updated_at

        update = EnvironmentUpdate(name="Updated")
        result = self.service.update_environment(created.id, update)

        self.assertGreater(result.updated_at, original_updated_at)

    def test_update_environment_not_found(self):
        update = EnvironmentUpdate(name="Updated")
        result = self.service.update_environment("nonexistent-id", update)

        self.assertIsNone(result)

    def test_update_environment_with_no_changes(self):
        created = self.service.create_environment(EnvironmentCreate(
            name="Test",
            is_default=False
        ))

        update = EnvironmentUpdate()
        result = self.service.update_environment(created.id, update)

        self.assertIsNotNone(result)
        self.assertEqual(result.name, "Test")

    def test_delete_environment_exists(self):
        created = self.service.create_environment(EnvironmentCreate(
            name="To Delete",
            is_default=False
        ))

        result = self.service.delete_environment(created.id)

        self.assertTrue(result)
        self.assertIsNone(self.service.get_environment(created.id))

    def test_delete_environment_not_found(self):
        result = self.service.delete_environment("nonexistent-id")
        self.assertFalse(result)

    def test_matches_patterns_with_wildcard_star(self):
        self.assertTrue(EnvironmentService.matches_patterns(
            "prod-queue-1", ["prod-*"]
        ))
        self.assertTrue(EnvironmentService.matches_patterns(
            "prod-queue-123", ["prod-*"]
        ))
        self.assertFalse(EnvironmentService.matches_patterns(
            "dev-queue-1", ["prod-*"]
        ))

    def test_matches_patterns_with_wildcard_question_mark(self):
        self.assertTrue(EnvironmentService.matches_patterns(
            "q1", ["q?"]
        ))
        self.assertTrue(EnvironmentService.matches_patterns(
            "q2", ["q?"]
        ))
        self.assertFalse(EnvironmentService.matches_patterns(
            "q12", ["q?"]
        ))

    def test_matches_patterns_with_multiple_patterns(self):
        patterns = ["prod-*", "staging-*"]
        self.assertTrue(EnvironmentService.matches_patterns("prod-queue", patterns))
        self.assertTrue(EnvironmentService.matches_patterns("staging-queue", patterns))
        self.assertFalse(EnvironmentService.matches_patterns("dev-queue", patterns))

    def test_matches_patterns_exact_match(self):
        self.assertTrue(EnvironmentService.matches_patterns(
            "exact-match", ["exact-match"]
        ))
        self.assertFalse(EnvironmentService.matches_patterns(
            "exact-match-not", ["exact-match"]
        ))

    def test_matches_patterns_empty_patterns_returns_true(self):
        self.assertTrue(EnvironmentService.matches_patterns("anything", []))

    def test_matches_patterns_with_complex_wildcards(self):
        self.assertTrue(EnvironmentService.matches_patterns(
            "prod-worker-1-eu", ["prod-worker-?-*"]
        ))
        self.assertFalse(EnvironmentService.matches_patterns(
            "prod-worker-12-eu", ["prod-worker-?-*"]
        ))

    def test_should_include_event_no_environment_returns_true(self):
        result = self.service.should_include_event(
            queue_name="any-queue",
            worker_hostname="any-worker",
            env=None
        )
        self.assertTrue(result)

    def test_should_include_event_matches_queue_pattern(self):
        env = self.service.create_environment(EnvironmentCreate(
            name="Test",
            queue_patterns=["prod-*"],
            is_default=False
        ))

        self.assertTrue(self.service.should_include_event(
            queue_name="prod-queue",
            env=env
        ))
        self.assertFalse(self.service.should_include_event(
            queue_name="dev-queue",
            env=env
        ))

    def test_should_include_event_matches_worker_pattern(self):
        env = self.service.create_environment(EnvironmentCreate(
            name="Test",
            worker_patterns=["celery-*"],
            is_default=False
        ))

        self.assertTrue(self.service.should_include_event(
            worker_hostname="celery-worker-1",
            env=env
        ))
        self.assertFalse(self.service.should_include_event(
            worker_hostname="other-worker-1",
            env=env
        ))

    def test_should_include_event_matches_both_queue_and_worker(self):
        env = self.service.create_environment(EnvironmentCreate(
            name="Test",
            queue_patterns=["prod-*"],
            worker_patterns=["celery-*"],
            is_default=False
        ))

        self.assertTrue(self.service.should_include_event(
            queue_name="prod-queue",
            worker_hostname="celery-worker-1",
            env=env
        ))

    def test_should_include_event_fails_if_queue_does_not_match(self):
        env = self.service.create_environment(EnvironmentCreate(
            name="Test",
            queue_patterns=["prod-*"],
            worker_patterns=["celery-*"],
            is_default=False
        ))

        self.assertFalse(self.service.should_include_event(
            queue_name="dev-queue",
            worker_hostname="celery-worker-1",
            env=env
        ))

    def test_should_include_event_fails_if_worker_does_not_match(self):
        env = self.service.create_environment(EnvironmentCreate(
            name="Test",
            queue_patterns=["prod-*"],
            worker_patterns=["celery-*"],
            is_default=False
        ))

        self.assertFalse(self.service.should_include_event(
            queue_name="prod-queue",
            worker_hostname="other-worker-1",
            env=env
        ))

    def test_should_include_event_with_empty_patterns_matches_all(self):
        env = self.service.create_environment(EnvironmentCreate(
            name="Test",
            queue_patterns=[],
            worker_patterns=[],
            is_default=False
        ))

        self.assertTrue(self.service.should_include_event(
            queue_name="any-queue",
            worker_hostname="any-worker",
            env=env
        ))

    def test_should_include_event_with_none_values(self):
        env = self.service.create_environment(EnvironmentCreate(
            name="Test",
            queue_patterns=["prod-*"],
            is_default=False
        ))

        self.assertTrue(self.service.should_include_event(
            queue_name=None,
            worker_hostname="some-worker",
            env=env
        ))


if __name__ == '__main__':
    unittest.main()
