"""Suppression rules for noisy task failures."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from database import AppSettingDB
from models import TaskEvent, TaskSuppressionMetrics, TaskSuppressionRule, TaskSuppressionRuleCreate

SUPPRESSION_RULES_KEY = "task_issue_summary.suppression_rules"


def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class SuppressionService:
    def __init__(self, session: Session):
        self.session = session

    def list_rules(self, include_expired: bool = False) -> List[TaskSuppressionRule]:
        rules = [self._normalize_rule(item) for item in self._raw_rules()]
        if include_expired:
            return rules
        now = datetime.now(timezone.utc)
        return [rule for rule in rules if not rule.expires_at or rule.expires_at > now]

    @staticmethod
    def _match_rule_from_rules(rules: List[TaskSuppressionRule], event: TaskEvent) -> Optional[TaskSuppressionRule]:
        for rule in rules:
            if rule.task_name != event.task_name:
                continue
            if rule.exception_contains and rule.exception_contains not in (event.exception or ""):
                continue
            return rule
        return None

    def create_rule(self, payload: TaskSuppressionRuleCreate) -> TaskSuppressionRule:
        rules = self._raw_rules()
        rule = TaskSuppressionRule(
            id=str(uuid4()),
            task_name=payload.task_name,
            exception_contains=payload.exception_contains,
            reason=payload.reason,
            created_at=datetime.now(timezone.utc),
            expires_at=_ensure_utc(payload.expires_at),
        )
        rules.append(rule.model_dump(mode="json"))
        self._save_rules(rules)
        return rule

    def delete_rule(self, rule_id: str) -> bool:
        rules = self._raw_rules()
        filtered = [rule for rule in rules if rule.get("id") != rule_id]
        if len(filtered) == len(rules):
            return False
        self._save_rules(filtered)
        return True

    def match_rule(self, event: TaskEvent, rules: Optional[List[TaskSuppressionRule]] = None) -> Optional[TaskSuppressionRule]:
        return self._match_rule_from_rules(rules or self.list_rules(), event)

    def annotate_events(self, events: List[TaskEvent]) -> TaskSuppressionMetrics:
        active = 0
        suppressed = 0
        rules = self.list_rules()
        for event in events:
            rule = self.match_rule(event, rules=rules)
            if rule:
                event.suppressed = True
                event.suppression_rule_id = rule.id
                event.suppression_reason = rule.reason
                event.suppression_expires_at = rule.expires_at
                suppressed += 1
            else:
                event.suppressed = False
                active += 1
        return TaskSuppressionMetrics(active_count=active, suppressed_count=suppressed)

    def _raw_rules(self) -> List[Dict[str, Any]]:
        setting = self.session.query(AppSettingDB).filter_by(key=SUPPRESSION_RULES_KEY).first()
        if not setting or not isinstance(setting.value, list):
            return []
        return setting.value

    def _save_rules(self, rules: List[Dict[str, Any]]) -> None:
        setting = self.session.query(AppSettingDB).filter_by(key=SUPPRESSION_RULES_KEY).first()
        if setting:
            setting.value = rules
            setting.value_type = "json"
            setting.label = setting.label or "Task issue suppression rules"
            setting.description = setting.description or "Rules for muting noisy failed-task patterns."
            setting.category = setting.category or "task_issue_summary"
        else:
            self.session.add(AppSettingDB(
                key=SUPPRESSION_RULES_KEY,
                value=rules,
                value_type="json",
                label="Task issue suppression rules",
                description="Rules for muting noisy failed-task patterns.",
                category="task_issue_summary",
            ))
        self.session.commit()

    def _normalize_rule(self, payload: Dict[str, Any]) -> TaskSuppressionRule:
        return TaskSuppressionRule(**payload)
