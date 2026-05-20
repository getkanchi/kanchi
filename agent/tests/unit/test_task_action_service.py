import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock

from database import (
    TaskActionDB,
    TaskActionItemDB,
    TaskRerunRelationshipDB,
    TaskResolutionDB,
)
from models import (
    RerunReviewState,
    RerunSubmitDecision,
    RerunSubmitItem,
    TaskActionItemOutcome,
    TaskActionStatus,
    TaskActionType,
)
from services.task_action_service import TaskActionService, TaskActionValidationError
from services.task_service import TaskService
from tests.base import DatabaseTestCase


class TestTaskActionService(DatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.base_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        self.send_task = Mock()
        self.monitor = SimpleNamespace(app=SimpleNamespace(send_task=self.send_task))
        self.service = TaskActionService(self.session, monitor_instance=self.monitor)

    def test_preflight_rerun_accepts_reconstructable_payload(self):
        self.create_task_event_db(
            task_id="task-1",
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=self.base_time,
            args="[1, 2]",
            kwargs='{"dry_run": true}',
        )

        result = self.service.preflight_rerun(["task-1"])

        self.assertEqual(result.total, 1)
        self.assertEqual(result.ready_count, 1)
        self.assertTrue(result.items[0].ready)

    def test_create_rerun_action_sends_task_and_records_history(self):
        self.create_task_event_db(
            task_id="task-1",
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=self.base_time,
            args="[1, 2]",
            kwargs='{"dry_run": true}',
            queue="critical",
        )

        action = self.service.create_action(
            action_type=TaskActionType.RERUN,
            task_ids=["task-1"],
            initiated_by="tester",
            initiated_session_id="session-1",
        )

        self.assertEqual(action.action_type, TaskActionType.RERUN)
        self.assertEqual(action.status, TaskActionStatus.COMPLETED)
        self.assertEqual(action.item_created, 1)
        self.assertEqual(len(action.items), 1)
        self.assertEqual(action.items[0].outcome, TaskActionItemOutcome.CREATED)
        self.assertIsNotNone(action.items[0].rerun_task_id)

        self.send_task.assert_called_once()
        _, kwargs = self.send_task.call_args
        self.assertEqual(kwargs["args"], [1, 2])
        self.assertEqual(kwargs["kwargs"], {"dry_run": True})
        self.assertEqual(kwargs["queue"], "critical")
        self.assertEqual(kwargs["task_id"], action.items[0].rerun_task_id)
        self.assertEqual(action.items[0].submitted_args, [1, 2])
        self.assertEqual(action.items[0].submitted_kwargs, {"dry_run": True})
        self.assertEqual(action.items[0].rerun_kind.value, "replay")

        relationship = self.session.query(TaskRerunRelationshipDB).one()
        self.assertEqual(relationship.original_task_id, "task-1")
        self.assertEqual(relationship.rerun_task_id, action.items[0].rerun_task_id)
        self.assertEqual(relationship.action_id, action.id)

    def test_preflight_marks_truncated_payload_repairable(self):
        self.create_task_event_db(
            task_id="task-1",
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=self.base_time,
            args=[{"__kanchi_placeholder__": "celery_payload_truncated", "message": "truncated"}],
            kwargs={},
        )

        result = self.service.preflight_rerun(["task-1"])

        self.assertEqual(result.repairable_count, 1)
        self.assertEqual(result.items[0].review_state, RerunReviewState.REPAIRABLE)
        self.assertFalse(result.items[0].ready)
        self.assertEqual(result.items[0].required_replacements[0].path, "$.args[0]")

    def test_submit_rerun_review_sends_edited_inputs_and_records_audit(self):
        self.create_task_event_db(
            task_id="task-1",
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=self.base_time,
            args="[1, 2]",
            kwargs='{"dry_run": true}',
            queue="critical",
        )
        preflight = self.service.preflight_rerun(["task-1"])
        item = preflight.items[0]

        action = self.service.submit_rerun_review(
            items=[
                RerunSubmitItem(
                    task_id="task-1",
                    decision=RerunSubmitDecision.SUBMIT,
                    fingerprint=item.fingerprint,
                    args=[1, 99],
                    kwargs={"dry_run": False},
                )
            ],
            initiated_by="tester",
        )

        self.assertEqual(action.status, TaskActionStatus.COMPLETED)
        self.assertEqual(action.items[0].outcome, TaskActionItemOutcome.CREATED)
        self.assertEqual(action.items[0].submitted_args, [1, 99])
        self.assertEqual(action.items[0].submitted_kwargs, {"dry_run": False})
        self.assertEqual(action.items[0].rerun_kind.value, "edited_override")
        _, kwargs = self.send_task.call_args
        self.assertEqual(kwargs["args"], [1, 99])
        self.assertEqual(kwargs["kwargs"], {"dry_run": False})

    def test_submit_rerun_review_rejects_stale_fingerprint_before_send(self):
        self.create_task_event_db(
            task_id="task-1",
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=self.base_time,
            args="[1]",
            kwargs="{}",
        )

        with self.assertRaises(TaskActionValidationError):
            self.service.submit_rerun_review(
                items=[
                    RerunSubmitItem(
                        task_id="task-1",
                        decision=RerunSubmitDecision.SUBMIT,
                        fingerprint="stale",
                        args=[1],
                        kwargs={},
                    )
                ]
            )

        self.send_task.assert_not_called()
        self.assertEqual(self.session.query(TaskActionDB).count(), 0)

    def test_submit_rerun_review_allows_user_skipped_repairable_in_bulk(self):
        self.create_task_event_db(
            task_id="task-1",
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=self.base_time,
            args=[{"__kanchi_placeholder__": "celery_payload_truncated", "message": "truncated"}],
            kwargs={},
        )
        self.create_task_event_db(
            task_id="task-2",
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=self.base_time,
            args="[2]",
            kwargs="{}",
        )
        preflight = self.service.preflight_rerun(["task-1", "task-2"])
        by_id = {item.task_id: item for item in preflight.items}

        action = self.service.submit_rerun_review(
            items=[
                RerunSubmitItem(
                    task_id="task-1",
                    decision=RerunSubmitDecision.USER_SKIP,
                    fingerprint=by_id["task-1"].fingerprint,
                ),
                RerunSubmitItem(
                    task_id="task-2",
                    decision=RerunSubmitDecision.SUBMIT,
                    fingerprint=by_id["task-2"].fingerprint,
                    args=[2],
                    kwargs={},
                ),
            ]
        )

        self.assertEqual(action.status, TaskActionStatus.COMPLETED)
        self.assertEqual(action.item_created, 1)
        self.assertEqual(action.item_skipped, 1)
        self.assertEqual(action.summary["user_skipped"], 1)

    def test_submit_rerun_review_records_failed_send_without_lineage(self):
        self.send_task.side_effect = RuntimeError("broker down")
        self.create_task_event_db(
            task_id="task-1",
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=self.base_time,
            args="[1]",
            kwargs="{}",
        )
        item = self.service.preflight_rerun(["task-1"]).items[0]

        action = self.service.submit_rerun_review(
            items=[
                RerunSubmitItem(
                    task_id="task-1",
                    decision=RerunSubmitDecision.SUBMIT,
                    fingerprint=item.fingerprint,
                    args=[1],
                    kwargs={},
                )
            ]
        )

        self.assertEqual(action.status, TaskActionStatus.FAILED)
        self.assertEqual(action.items[0].outcome, TaskActionItemOutcome.FAILED)
        self.assertIsNotNone(action.items[0].attempted_task_id)
        self.assertIsNone(action.items[0].rerun_task_id)
        self.assertEqual(self.session.query(TaskRerunRelationshipDB).count(), 0)

    def test_create_rerun_action_requires_at_least_one_ready_task(self):
        self.create_task_event_db(
            task_id="task-1",
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=self.base_time,
            args="[1]",
            kwargs="{}",
        )
        service = TaskActionService(self.session, monitor_instance=None)

        with self.assertRaises(TaskActionValidationError):
            service.create_action(action_type=TaskActionType.RERUN, task_ids=["task-1"])

        self.assertEqual(self.session.query(TaskActionDB).count(), 0)
        self.assertEqual(self.session.query(TaskActionItemDB).count(), 0)

    def test_resolve_and_unresolve_actions_are_persisted(self):
        self.create_task_event_db(
            task_id="task-1",
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=self.base_time,
        )

        resolve = self.service.create_action(
            action_type=TaskActionType.RESOLVE,
            task_ids=["task-1"],
            initiated_by="tester",
        )

        self.assertEqual(resolve.status, TaskActionStatus.COMPLETED)
        self.assertEqual(resolve.item_changed, 1)
        resolution = self.session.query(TaskResolutionDB).filter_by(task_id="task-1").one()
        self.assertTrue(resolution.resolved)
        self.assertEqual(resolution.resolved_by, "tester")

        unresolve = self.service.create_action(
            action_type=TaskActionType.UNRESOLVE,
            task_ids=["task-1"],
            initiated_by="tester",
        )

        self.assertEqual(unresolve.status, TaskActionStatus.COMPLETED)
        self.assertEqual(unresolve.item_changed, 1)
        remaining = self.session.query(TaskResolutionDB).filter_by(task_id="task-1").count()
        self.assertEqual(remaining, 0)

    def test_manual_rerun_lineage_enrichment_is_separate_from_retry_chain(self):
        original_db = self.create_task_event_db(
            task_id="original-1",
            task_name="tasks.example",
            event_type="task-failed",
            timestamp=self.base_time,
        )
        rerun_db = self.create_task_event_db(
            task_id="rerun-1",
            task_name="tasks.example",
            event_type="task-succeeded",
            timestamp=self.base_time + timedelta(seconds=5),
        )
        self.session.add(TaskRerunRelationshipDB(
            original_task_id="original-1",
            rerun_task_id="rerun-1",
            created_by="tester",
        ))
        self.session.commit()

        task_service = TaskService(self.session)
        original = task_service._db_to_task_event(original_db)
        rerun = task_service._db_to_task_event(rerun_db)
        task_service._bulk_enrich_with_rerun_info([original, rerun])

        self.assertFalse(original.is_retry)
        self.assertFalse(rerun.is_retry)
        self.assertFalse(original.is_rerun)
        self.assertTrue(original.has_reruns)
        self.assertEqual(original.rerun_count, 1)
        self.assertEqual(original.rerun_by[0].task_id, "rerun-1")
        self.assertTrue(rerun.is_rerun)
        self.assertEqual(rerun.rerun_of.task_id, "original-1")


if __name__ == "__main__":
    unittest.main()
