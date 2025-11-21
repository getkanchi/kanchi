"""Service for managing workflows."""

import logging
import uuid
from datetime import date, datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set
from enum import Enum

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from database import WorkflowDB, WorkflowExecutionDB, ensure_utc_isoformat, utc_now
from models import (
    WorkflowDefinition,
    WorkflowCreateRequest,
    WorkflowUpdateRequest,
    WorkflowExecutionRecord,
    TriggerConfig,
    ConditionGroup,
    ActionConfig,
    CircuitBreakerConfig,
    CircuitBreakerState
)
from services.action_executor import ActionExecutor
from services.action_config_service import ActionConfigService
from services.workflow_catalog import TRIGGER_METADATA

logger = logging.getLogger(__name__)


class WorkflowService:
    """Service for workflow CRUD operations."""

    def __init__(self, session: Session):
        self.session = session

    @staticmethod
    def _ensure_aware_utc(dt: Optional[datetime]) -> Optional[datetime]:
        """
        Ensure datetime objects are timezone-aware and normalized to UTC.
        SQLite sometimes returns naive datetimes even for timezone-aware columns.
        """
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    @staticmethod
    def _circuit_candidate_fields(
        workflow: WorkflowDefinition,
        config: CircuitBreakerConfig
    ) -> List[str]:
        """Determine which context fields should be inspected for circuit breaker grouping."""
        candidates: List[str] = []

        if config.context_field:
            candidates.append(config.context_field)

        trigger_type = workflow.trigger.type
        if trigger_type.startswith("task."):
            candidates.extend(["root_id", "task_id"])
        elif trigger_type.startswith("worker."):
            candidates.extend(["hostname", "worker_name"])

        # Always consider task identifiers as fallback for safety
        candidates.extend(["root_id", "task_id"])

        # Deduplicate while preserving order
        seen: Set[str] = set()
        ordered = []
        for field in candidates:
            if field and field not in seen:
                seen.add(field)
                ordered.append(field)

        return ordered

    def _json_safe(self, value: Any) -> Any:
        """Convert complex objects (datetimes, UUIDs, Pydantic models) into JSON-safe structures."""
        if value is None:
            return None

        if isinstance(value, datetime):
            return ensure_utc_isoformat(value)

        if isinstance(value, date):
            return value.isoformat()

        if isinstance(value, uuid.UUID):
            return str(value)

        if isinstance(value, Enum):
            return value.value

        if isinstance(value, dict):
            return {key: self._json_safe(val) for key, val in value.items()}

        if isinstance(value, (list, tuple, set)):
            return [self._json_safe(item) for item in value]

        # Support Pydantic v1 (`dict`) and v2 (`model_dump`)
        if hasattr(value, "model_dump"):
            try:
                return self._json_safe(value.model_dump())
            except Exception:
                pass

        if hasattr(value, "dict") and callable(value.dict):
            try:
                return self._json_safe(value.dict())
            except Exception:
                pass

        if hasattr(value, "__dict__"):
            return self._json_safe(vars(value))

        return value

    def resolve_circuit_breaker_key(
        self,
        workflow: WorkflowDefinition,
        context: Dict[str, Any]
    ) -> tuple[Optional[str], Optional[str]]:
        """Resolve the circuit breaker grouping key (value, field)."""
        config = workflow.circuit_breaker
        if not config or not config.enabled:
            return None, None

        candidate_fields = self._circuit_candidate_fields(workflow, config)
        for field in candidate_fields:
            value = context.get(field)
            if value is not None:
                value_str = str(value).strip()
                if value_str:
                    return value_str, field

        return None, None

    def is_circuit_breaker_open(
        self,
        workflow: WorkflowDefinition,
        context: Dict[str, Any]
    ) -> CircuitBreakerState:
        """Check whether the circuit breaker should prevent execution."""
        config = workflow.circuit_breaker
        if not config or not config.enabled:
            return CircuitBreakerState(is_open=False)

        key, field = self.resolve_circuit_breaker_key(workflow, context)

        if not key:
            return CircuitBreakerState(is_open=False)

        window_start = datetime.now(timezone.utc) - timedelta(seconds=config.window_seconds)

        recent_count = self.session.query(WorkflowExecutionDB).filter(
            and_(
                WorkflowExecutionDB.workflow_id == workflow.id,
                WorkflowExecutionDB.circuit_breaker_key == key,
                WorkflowExecutionDB.triggered_at >= window_start
            )
        ).count()

        if recent_count >= config.max_executions:
            reason = (
                f"Circuit breaker open for workflow '{workflow.name}' "
                f"(field={field or 'context'}, key={key}) - "
                f"{recent_count} executions within {config.window_seconds}s "
                f"(limit={config.max_executions})"
            )
            return CircuitBreakerState(is_open=True, reason=reason, key=key, field=field)

        return CircuitBreakerState(is_open=False, key=key, field=field)

    def record_circuit_breaker_skip(
        self,
        workflow: WorkflowDefinition,
        trigger_type: str,
        trigger_event: Dict[str, Any],
        workflow_snapshot: Dict[str, Any],
        circuit_breaker_key: Optional[str],
        reason: str
    ) -> None:
        """Persist a workflow execution record for a circuit breaker skip."""
        execution_db = WorkflowExecutionDB(
            workflow_id=workflow.id,
            trigger_type=trigger_type,
            trigger_event=self._json_safe(trigger_event),
            status="circuit_open",
            error_message=reason,
            actions_executed=[],
            circuit_breaker_key=circuit_breaker_key,
            workflow_snapshot=self._json_safe(workflow_snapshot)
        )

        self.session.add(execution_db)
        self.session.commit()

    def _validate_workflow_definition(
        self,
        trigger: TriggerConfig,
        actions: List[ActionConfig]
    ):
        valid_triggers = {meta["type"] for meta in TRIGGER_METADATA}
        if trigger.type not in valid_triggers:
            raise ValueError(f"Unsupported trigger type: {trigger.type}")

        supported_actions = set(ActionExecutor.get_supported_actions())
        config_service = ActionConfigService(self.session)

        for action in actions:
            action_type = action.type
            if action_type not in supported_actions:
                raise ValueError(f"Unsupported action type: {action_type}")

            params = action.params or {}
            if action_type == "slack.notify":
                config_id = params.get("config_id")
                if not config_id:
                    raise ValueError("Slack action requires config_id")
                if not config_service.get_config(config_id):
                    raise ValueError(f"Action config not found: {config_id}")

    def _coerce_actions(self, actions: List[Any]) -> List[ActionConfig]:
        coerced = []
        for action in actions:
            if isinstance(action, ActionConfig):
                coerced.append(action)
            else:
                coerced.append(ActionConfig(**action))
        return coerced

    # ==================== Workflow CRUD ====================

    def create_workflow(self, workflow_data: WorkflowCreateRequest) -> WorkflowDefinition:
        """Create a new workflow."""
        workflow_id = str(uuid.uuid4())

        actions = self._coerce_actions(workflow_data.actions)
        self._validate_workflow_definition(workflow_data.trigger, actions)

        workflow_db = WorkflowDB(
            id=workflow_id,
            name=workflow_data.name,
            description=workflow_data.description,
            enabled=workflow_data.enabled,
            trigger_type=workflow_data.trigger.type,
            trigger_config=workflow_data.trigger.config,
            conditions=workflow_data.conditions.dict() if workflow_data.conditions else None,
            actions=[action.dict() for action in actions],
            priority=workflow_data.priority,
            max_executions_per_hour=workflow_data.max_executions_per_hour,
            cooldown_seconds=workflow_data.cooldown_seconds,
            circuit_breaker_config=workflow_data.circuit_breaker.dict()
            if workflow_data.circuit_breaker
            else None,
        )

        self.session.add(workflow_db)
        self.session.commit()

        logger.info(f"Created workflow: {workflow_data.name} (id={workflow_id})")

        return self._db_to_workflow(workflow_db)

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Get workflow by ID."""
        workflow_db = self.session.query(WorkflowDB).filter_by(id=workflow_id).first()
        return self._db_to_workflow(workflow_db) if workflow_db else None

    def list_workflows(
        self,
        enabled_only: bool = False,
        trigger_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[WorkflowDefinition]:
        """List workflows with filtering."""
        query = self.session.query(WorkflowDB)

        if enabled_only:
            query = query.filter(WorkflowDB.enabled == True)

        if trigger_type:
            query = query.filter(WorkflowDB.trigger_type == trigger_type)

        query = query.order_by(WorkflowDB.priority.desc(), WorkflowDB.created_at.desc())
        query = query.limit(limit).offset(offset)

        workflows_db = query.all()
        return [self._db_to_workflow(w) for w in workflows_db]

    def update_workflow(
        self,
        workflow_id: str,
        updates: WorkflowUpdateRequest
    ) -> Optional[WorkflowDefinition]:
        """Update an existing workflow."""
        workflow_db = self.session.query(WorkflowDB).filter_by(id=workflow_id).first()

        if not workflow_db:
            return None

        # Apply updates
        update_dict = updates.dict(exclude_unset=True)

        for field, value in update_dict.items():
            if field == "trigger" and value is not None:
                workflow_db.trigger_type = value["type"]
                workflow_db.trigger_config = value.get("config", {})
            elif field == "conditions" and value is not None:
                workflow_db.conditions = value
            elif field == "actions" and value is not None:
                workflow_db.actions = [action.dict() if hasattr(action, 'dict') else action for action in value]
            elif field == "circuit_breaker":
                if value is None:
                    workflow_db.circuit_breaker_config = None
                elif hasattr(value, 'dict'):
                    workflow_db.circuit_breaker_config = value.dict()
                else:
                    workflow_db.circuit_breaker_config = value
            elif hasattr(workflow_db, field):
                setattr(workflow_db, field, value)

        trigger = TriggerConfig(
            type=workflow_db.trigger_type,
            config=workflow_db.trigger_config or {}
        )
        actions_payload = self._coerce_actions(workflow_db.actions or [])
        self._validate_workflow_definition(trigger, actions_payload)

        workflow_db.updated_at = datetime.now(timezone.utc)
        self.session.commit()

        logger.info(f"Updated workflow: {workflow_id}")

        return self._db_to_workflow(workflow_db)

    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow."""
        workflow_db = self.session.query(WorkflowDB).filter_by(id=workflow_id).first()

        if not workflow_db:
            return False

        self.session.delete(workflow_db)
        self.session.commit()

        logger.info(f"Deleted workflow: {workflow_id}")
        return True

    # ==================== Workflow Execution Tracking ====================

    def get_active_workflows_for_trigger(self, trigger_type: str) -> List[WorkflowDefinition]:
        """Get all enabled workflows for a specific trigger type."""
        workflows_db = self.session.query(WorkflowDB).filter(
            and_(
                WorkflowDB.enabled == True,
                WorkflowDB.trigger_type == trigger_type
            )
        ).order_by(WorkflowDB.priority.desc()).all()

        return [self._db_to_workflow(w) for w in workflows_db]

    def can_execute_workflow(self, workflow_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if workflow can execute based on rate limiting and cooldown.

        Returns:
            (can_execute, reason)
        """
        workflow_db = self.session.query(WorkflowDB).filter_by(id=workflow_id).first()

        if not workflow_db:
            return False, "Workflow not found"

        if not workflow_db.enabled:
            return False, "Workflow is disabled"

        now = datetime.now(timezone.utc)

        # Check cooldown
        if workflow_db.cooldown_seconds > 0 and workflow_db.last_executed_at:
            cooldown_until = workflow_db.last_executed_at + timedelta(seconds=workflow_db.cooldown_seconds)
            if now < cooldown_until:
                return False, f"Cooldown active until {cooldown_until.isoformat()}"

        # Check rate limiting
        if workflow_db.max_executions_per_hour:
            one_hour_ago = now - timedelta(hours=1)
            recent_executions = self.session.query(WorkflowExecutionDB).filter(
                and_(
                    WorkflowExecutionDB.workflow_id == workflow_id,
                    WorkflowExecutionDB.triggered_at >= one_hour_ago
                )
            ).count()

            if recent_executions >= workflow_db.max_executions_per_hour:
                return False, f"Rate limit exceeded ({workflow_db.max_executions_per_hour}/hour)"

        return True, None

    def record_workflow_execution_start(
        self,
        workflow_id: str,
        trigger_type: str,
        trigger_event: Dict[str, Any],
        workflow_snapshot: Dict[str, Any],
        circuit_breaker_key: Optional[str] = None
    ) -> int:
        """Create workflow execution record."""
        execution_db = WorkflowExecutionDB(
            workflow_id=workflow_id,
            trigger_type=trigger_type,
            trigger_event=self._json_safe(trigger_event),
            status="running",
            started_at=datetime.now(timezone.utc),
            workflow_snapshot=self._json_safe(workflow_snapshot),
            circuit_breaker_key=circuit_breaker_key
        )

        self.session.add(execution_db)
        self.session.commit()

        return execution_db.id

    def update_workflow_execution(
        self,
        execution_id: int,
        status: str,
        actions_executed: Optional[List[Dict[str, Any]]] = None,
        error_message: Optional[str] = None,
        stack_trace: Optional[str] = None
    ):
        """Update workflow execution record."""
        execution_db = self.session.query(WorkflowExecutionDB).filter_by(id=execution_id).first()

        if not execution_db:
            logger.error(f"Workflow execution not found: {execution_id}")
            return

        execution_db.status = status
        execution_db.completed_at = self._ensure_aware_utc(datetime.now(timezone.utc))

        # Normalize started/completed timestamps to avoid naive vs aware subtraction
        if execution_db.started_at and execution_db.started_at.tzinfo is None:
            execution_db.started_at = execution_db.started_at.replace(tzinfo=timezone.utc)

        started_at = self._ensure_aware_utc(execution_db.started_at)
        completed_at = self._ensure_aware_utc(execution_db.completed_at)

        if started_at and completed_at:
            duration = (completed_at - started_at).total_seconds() * 1000
            execution_db.duration_ms = int(duration)

        if actions_executed is not None:
            execution_db.actions_executed = self._json_safe(actions_executed)

        if error_message:
            execution_db.error_message = error_message

        if stack_trace:
            execution_db.stack_trace = stack_trace

        self.session.commit()

    def update_workflow_stats(self, workflow_id: str, success: bool):
        """Update workflow execution statistics."""
        workflow_db = self.session.query(WorkflowDB).filter_by(id=workflow_id).first()

        if not workflow_db:
            return

        workflow_db.execution_count += 1
        workflow_db.last_executed_at = datetime.now(timezone.utc)

        if success:
            workflow_db.success_count += 1
        else:
            workflow_db.failure_count += 1

        self.session.commit()

    # ==================== Execution History ====================

    def get_workflow_executions(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[WorkflowExecutionRecord]:
        """Get workflow execution history."""
        query = self.session.query(WorkflowExecutionDB)

        if workflow_id:
            query = query.filter(WorkflowExecutionDB.workflow_id == workflow_id)

        if status:
            query = query.filter(WorkflowExecutionDB.status == status)

        query = query.order_by(WorkflowExecutionDB.triggered_at.desc())
        query = query.limit(limit).offset(offset)

        executions_db = query.all()
        return [self._db_to_execution(e) for e in executions_db]

    # ==================== Helper Methods ====================

    def _db_to_workflow(self, workflow_db: WorkflowDB) -> WorkflowDefinition:
        """Convert database model to Pydantic model."""
        trigger = TriggerConfig(
            type=workflow_db.trigger_type,
            config=workflow_db.trigger_config or {}
        )

        conditions = None
        if workflow_db.conditions:
            conditions = ConditionGroup(**workflow_db.conditions)

        actions = [ActionConfig(**action) for action in workflow_db.actions]

        circuit_breaker = None
        if workflow_db.circuit_breaker_config:
            circuit_breaker = CircuitBreakerConfig(**workflow_db.circuit_breaker_config)

        return WorkflowDefinition(
            id=workflow_db.id,
            name=workflow_db.name,
            description=workflow_db.description,
            enabled=workflow_db.enabled,
            trigger=trigger,
            conditions=conditions,
            actions=actions,
            priority=workflow_db.priority,
            max_executions_per_hour=workflow_db.max_executions_per_hour,
            cooldown_seconds=workflow_db.cooldown_seconds,
            circuit_breaker=circuit_breaker,
            created_at=workflow_db.created_at,
            updated_at=workflow_db.updated_at,
            created_by=workflow_db.created_by,
            execution_count=workflow_db.execution_count,
            last_executed_at=workflow_db.last_executed_at,
            success_count=workflow_db.success_count,
            failure_count=workflow_db.failure_count
        )

    def _db_to_execution(self, execution_db: WorkflowExecutionDB) -> WorkflowExecutionRecord:
        """Convert database execution to Pydantic model."""
        return WorkflowExecutionRecord(
            id=execution_db.id,
            workflow_id=execution_db.workflow_id,
            triggered_at=execution_db.triggered_at,
            trigger_type=execution_db.trigger_type,
            trigger_event=execution_db.trigger_event,
            status=execution_db.status,
            actions_executed=execution_db.actions_executed,
            error_message=execution_db.error_message,
            stack_trace=execution_db.stack_trace,
            started_at=execution_db.started_at,
            completed_at=execution_db.completed_at,
            duration_ms=execution_db.duration_ms,
            workflow_snapshot=execution_db.workflow_snapshot,
            circuit_breaker_key=execution_db.circuit_breaker_key
        )
