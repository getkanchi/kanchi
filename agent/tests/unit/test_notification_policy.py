import asyncio
from datetime import datetime, timedelta, timezone

from database import ActionConfigDB, WorkflowDB, WorkflowExecutionDB
from models import WorkflowCreateRequest
from services.action_executor import ActionExecutor
from services.workflow_service import WorkflowService
from tests.base import ServiceTestCase


class NotificationPolicyTestCase(ServiceTestCase):
    def setUp(self):
        super().setUp()
        self.primary_config = ActionConfigDB(
            id='cfg-primary',
            name='Primary Slack',
            action_type='slack.notify',
            config={'webhook_url': 'https://hooks.slack.test/primary'}
        )
        self.escalation_config = ActionConfigDB(
            id='cfg-escalation',
            name='Escalation Slack',
            action_type='slack.notify',
            config={'webhook_url': 'https://hooks.slack.test/escalation'}
        )
        self.session.add_all([self.primary_config, self.escalation_config])
        self.session.commit()

    def test_preview_applies_escalation_step(self):
        preview = ActionExecutor(self.session, db_manager=None).preview(
            'slack.notify',
            {
                'task_name': 'tasks.payment.capture',
                'event_type': 'task-failed',
                'severity': 'critical',
                'duration_seconds': 600,
            },
            {
                'config_id': 'cfg-primary',
                'template': 'Task {{task_name}} failed',
                'channel': '#ops',
                'notification_policy': {
                    'minimum_severity': 'medium',
                    'dedupe_window_seconds': 300,
                    'escalation_steps': [
                        {
                            'name': 'pager',
                            'after_seconds': 300,
                            'config_id': 'cfg-escalation',
                            'channel': '#sev1',
                            'template': 'Escalation for {{task_name}} after {{duration_seconds}}s',
                        }
                    ]
                }
            }
        )

        self.assertTrue(preview['supported'])
        self.assertTrue(preview['would_send'])
        self.assertEqual(preview['stage'], 'pager')
        self.assertEqual(preview['channel'], '#sev1')
        self.assertIn('after 600s', preview['message'])

    def test_execute_skips_when_deduped_recently(self):
        workflow = WorkflowDB(
            id='wf-1',
            name='Escalation workflow',
            enabled=True,
            trigger_type='task-failed',
            trigger_config={},
            actions=[],
            priority=100,
            cooldown_seconds=0,
        )
        self.session.add(workflow)
        self.session.commit()

        self.session.add(WorkflowExecutionDB(
            workflow_id='wf-1',
            trigger_type='task-failed',
            trigger_event={'task_name': 'tasks.payment.capture'},
            status='completed',
            triggered_at=datetime.now(timezone.utc) - timedelta(seconds=30),
            actions_executed=[{
                'action_type': 'slack.notify',
                'status': 'success',
                'result': {'notification_key': 'slack.notify:initial:tasks.payment.capture:task-failed:task-1'}
            }],
            workflow_snapshot={}
        ))
        self.session.commit()

        result = asyncio.run(ActionExecutor(self.session, db_manager=None).execute(
            'slack.notify',
            {
                'task_id': 'task-1',
                'task_name': 'tasks.payment.capture',
                'event_type': 'task-failed',
                '_workflow': {'id': 'wf-1', 'name': 'Escalation workflow'}
            },
            {
                'config_id': 'cfg-primary',
                'template': 'Task {{task_name}} failed',
                'notification_policy': {'dedupe_window_seconds': 300}
            }
        ))

        self.assertEqual(result.status, 'skipped')
        self.assertIn('dedupe window', result.result['skip_reason'])

    def test_workflow_validation_checks_escalation_config(self):
        service = WorkflowService(self.session)
        with self.assertRaises(ValueError) as ctx:
            service.create_workflow(WorkflowCreateRequest(**{
                'name': 'Broken workflow',
                'trigger': {'type': 'task.failed', 'config': {}},
                'actions': [{
                    'type': 'slack.notify',
                    'params': {
                        'config_id': 'cfg-primary',
                        'template': 'Task {{task_name}} failed',
                        'notification_policy': {
                            'escalation_steps': [
                                {'after_seconds': 60, 'config_id': 'missing-config'}
                            ]
                        }
                    }
                }],
                'enabled': True,
                'priority': 100,
                'cooldown_seconds': 0,
            }))
        self.assertIn('missing-config', str(ctx.exception))
