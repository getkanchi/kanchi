from tests.base import DatabaseTestCase
from services.workflow_templates import WORKFLOW_TEMPLATES
from services.workflow_service import WorkflowService
from models import WorkflowCreateRequest


class TestWorkflowTemplates(DatabaseTestCase):
    def test_templates_cover_expected_scenarios(self):
        ids = {template['id'] for template in WORKFLOW_TEMPLATES}
        self.assertEqual(ids, {
            'repeated-task-failure',
            'orphaned-task-recovery',
            'worker-offline-alert',
            'long-running-task-followup',
            'error-rate-spike-escalation',
        })

    def test_templates_can_be_loaded_into_workflow_models(self):
        service = WorkflowService(self.session)
        for template in WORKFLOW_TEMPLATES:
            payload = WorkflowCreateRequest(**template['workflow'])
            actions = service._coerce_actions(payload.actions)
            self.assertGreater(len(actions), 0)
            self.assertTrue(payload.trigger.type)
