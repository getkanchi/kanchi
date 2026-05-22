import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from database import WorkflowDB
from models import WorkflowUpdateRequest
from services.workflow_service import WorkflowService
from tests.base import DatabaseTestCase


class TestWorkflowServiceConditions(DatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.workflow_service = WorkflowService(self.session)

    def test_update_workflow_clears_conditions_when_explicitly_null(self):
        workflow_db = WorkflowDB(
            id="workflow-with-conditions",
            name="Workflow With Conditions",
            enabled=True,
            trigger_type="task.failed",
            trigger_config={},
            conditions={
                "operator": "AND",
                "conditions": [
                    {
                        "field": "hostname",
                        "operator": "equals",
                        "value": "worker-1",
                    }
                ],
            },
            actions=[{"type": "task.retry", "params": {}}],
            priority=100,
        )
        self.session.add(workflow_db)
        self.session.commit()

        workflow = self.workflow_service.update_workflow(
            "workflow-with-conditions",
            WorkflowUpdateRequest(conditions=None),
        )

        self.assertIsNotNone(workflow)
        self.assertIsNone(workflow.conditions)

        self.session.refresh(workflow_db)
        self.assertIsNone(workflow_db.conditions)
