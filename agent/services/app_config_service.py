"""Service for managing application configuration stored in the database."""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from database import AppSettingDB
from models import (
    AppSetting,
    AppSettingUpdate,
    AppConfigSnapshot,
    TaskIssueConfig,
    DataRetentionConfig,
    RetentionLastRun,
    RetentionScheduleConfig,
)

logger = logging.getLogger(__name__)

TASK_ISSUE_LOOKBACK_KEY = "task_issue_summary.lookback_hours"
RETENTION_TASK_SUCCESSFUL_DAYS_KEY = "data_retention.task_successful_days"
RETENTION_TASK_UNSUCCESSFUL_DAYS_KEY = "data_retention.task_unsuccessful_days"
RETENTION_WORKER_EVENTS_DAYS_KEY = "data_retention.worker_events_days"
RETENTION_WORKFLOW_EXECUTIONS_DAYS_KEY = "data_retention.workflow_executions_days"
RETENTION_TASK_DAILY_STATS_DAYS_KEY = "data_retention.task_daily_stats_days"
RETENTION_INACTIVE_SESSIONS_DAYS_KEY = "data_retention.inactive_sessions_days"
RETENTION_SCHEDULE_ENABLED_KEY = "data_retention.schedule.enabled"
RETENTION_SCHEDULE_PRESET_KEY = "data_retention.schedule.preset"
RETENTION_SCHEDULE_HOUR_KEY = "data_retention.schedule.hour"
RETENTION_SCHEDULE_MINUTE_KEY = "data_retention.schedule.minute"
RETENTION_SCHEDULE_WEEKDAY_KEY = "data_retention.schedule.weekday"
RETENTION_SCHEDULE_MONTH_DAY_KEY = "data_retention.schedule.month_day"
RETENTION_SCHEDULE_TIMEZONE_KEY = "data_retention.schedule.timezone"
RETENTION_LAST_RUN_KEY = "data_retention.last_run"

DEFAULT_SETTING_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    TASK_ISSUE_LOOKBACK_KEY: {
        "default": 24,
        "value_type": "number",
        "label": "Task issue summary lookback (hours)",
        "description": "Number of hours of failed tasks to surface in the dashboard issue summary.",
        "category": "task_issue_summary",
        "min": 1,
        "max": 168,
    },
    RETENTION_TASK_SUCCESSFUL_DAYS_KEY: {
        "default": 14,
        "value_type": "number",
        "label": "Successful task retention (days)",
        "description": "How long successful task records and related events should be kept before cleanup.",
        "category": "data_retention",
        "min": 1,
        "max": 3650,
    },
    RETENTION_TASK_UNSUCCESSFUL_DAYS_KEY: {
        "default": 30,
        "value_type": "number",
        "label": "Unsuccessful task retention (days)",
        "description": "How long failed, retried, revoked, orphaned, or otherwise non-successful task records and related events should be kept before cleanup.",
        "category": "data_retention",
        "min": 1,
        "max": 3650,
    },
    RETENTION_WORKER_EVENTS_DAYS_KEY: {
        "default": 30,
        "value_type": "number",
        "label": "Worker event retention (days)",
        "description": "How long worker heartbeat and lifecycle events should be kept before cleanup.",
        "category": "data_retention",
        "min": 1,
        "max": 3650,
    },
    RETENTION_WORKFLOW_EXECUTIONS_DAYS_KEY: {
        "default": 30,
        "value_type": "number",
        "label": "Workflow execution retention (days)",
        "description": "How long workflow execution logs should be kept before cleanup.",
        "category": "data_retention",
        "min": 1,
        "max": 3650,
    },
    RETENTION_TASK_DAILY_STATS_DAYS_KEY: {
        "default": 365,
        "value_type": "number",
        "label": "Task daily stats retention (days)",
        "description": "How long aggregated daily task statistics should be kept before cleanup.",
        "category": "data_retention",
        "min": 1,
        "max": 3650,
    },
    RETENTION_INACTIVE_SESSIONS_DAYS_KEY: {
        "default": 30,
        "value_type": "number",
        "label": "Inactive session retention (days)",
        "description": "How long inactive user sessions should be kept before cleanup.",
        "category": "data_retention",
        "min": 1,
        "max": 3650,
    },
    RETENTION_SCHEDULE_ENABLED_KEY: {
        "default": False,
        "value_type": "boolean",
        "label": "Automatic cleanup",
        "description": "Whether retention cleanup should run automatically.",
        "category": "data_retention",
    },
    RETENTION_SCHEDULE_PRESET_KEY: {
        "default": "daily",
        "value_type": "string",
        "label": "Automatic cleanup schedule",
        "description": "How often automatic cleanup should run.",
        "category": "data_retention",
        "allowed": {"hourly", "daily", "weekly", "monthly"},
    },
    RETENTION_SCHEDULE_HOUR_KEY: {
        "default": 3,
        "value_type": "number",
        "label": "Automatic cleanup hour",
        "description": "UTC hour when automatic cleanup should run.",
        "category": "data_retention",
        "min": 0,
        "max": 23,
    },
    RETENTION_SCHEDULE_MINUTE_KEY: {
        "default": 0,
        "value_type": "number",
        "label": "Automatic cleanup minute",
        "description": "UTC minute when automatic cleanup should run.",
        "category": "data_retention",
        "min": 0,
        "max": 59,
    },
    RETENTION_SCHEDULE_WEEKDAY_KEY: {
        "default": 0,
        "value_type": "number",
        "label": "Automatic cleanup weekday",
        "description": "UTC weekday for weekly automatic cleanup. Monday is 0.",
        "category": "data_retention",
        "min": 0,
        "max": 6,
    },
    RETENTION_SCHEDULE_MONTH_DAY_KEY: {
        "default": 1,
        "value_type": "number",
        "label": "Automatic cleanup day of month",
        "description": "UTC day of month for monthly automatic cleanup.",
        "category": "data_retention",
        "min": 1,
        "max": 31,
    },
    RETENTION_SCHEDULE_TIMEZONE_KEY: {
        "default": "UTC",
        "value_type": "string",
        "label": "Automatic cleanup timezone",
        "description": "Timezone used for automatic cleanup schedules.",
        "category": "data_retention",
        "allowed": {"UTC"},
    },
    RETENTION_LAST_RUN_KEY: {
        "default": {"status": "never", "total_deleted": 0, "dry_run": False, "results": []},
        "value_type": "json",
        "label": "Last retention cleanup run",
        "description": "Last automatic cleanup status and result.",
        "category": "data_retention",
    },
}


class AppConfigService:
    """Provide CRUD access to application-level settings."""

    def __init__(self, session: Session):
        self.session = session

    def ensure_defaults(self) -> None:
        """Persist default settings if they are missing."""
        created = False
        for key, definition in DEFAULT_SETTING_DEFINITIONS.items():
            existing = self.session.query(AppSettingDB).filter_by(key=key).first()
            if existing:
                updated = False
                if not existing.label and definition.get("label"):
                    existing.label = definition["label"]
                    updated = True
                if not existing.description and definition.get("description"):
                    existing.description = definition["description"]
                    updated = True
                if not existing.category and definition.get("category"):
                    existing.category = definition["category"]
                    updated = True
                if updated:
                    created = True
                continue

            self.session.add(
                AppSettingDB(
                    key=key,
                    value=definition.get("default"),
                    value_type=definition.get("value_type", "string"),
                    label=definition.get("label"),
                    description=definition.get("description"),
                    category=definition.get("category"),
                )
            )
            created = True

        if created:
            self.session.commit()

    def _definition_for_key(self, key: str) -> Dict[str, Any]:
        return DEFAULT_SETTING_DEFINITIONS.get(key, {})

    def _normalize_boolean(self, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"true", "1", "yes", "on"}:
                return True
            if lowered in {"false", "0", "no", "off"}:
                return False
        raise ValueError("Boolean setting must be true/false")

    def _normalize_number(self, value: Any) -> Tuple[Any, float]:
        if isinstance(value, (int, float)):
            return value, float(value)
        if isinstance(value, str):
            try:
                parsed = float(value)
                if parsed.is_integer():
                    return int(parsed), parsed
                return parsed, parsed
            except ValueError as exc:
                raise ValueError("Numeric setting must be a number") from exc
        raise ValueError("Numeric setting must be a number")

    def _validate_value(self, key: str, value: Any, explicit_type: Optional[str]) -> Tuple[Any, str]:
        definition = self._definition_for_key(key)
        target_type = explicit_type or definition.get("value_type", "string")

        if target_type == "number":
            normalized, numeric_value = self._normalize_number(value)
            min_value = definition.get("min")
            max_value = definition.get("max")
            if min_value is not None and numeric_value < min_value:
                raise ValueError(f"Value for {key} must be >= {min_value}")
            if max_value is not None and numeric_value > max_value:
                raise ValueError(f"Value for {key} must be <= {max_value}")
            value = normalized
        elif target_type == "boolean":
            value = self._normalize_boolean(value)
        elif target_type == "string":
            value = str(value) if value is not None else ""
            allowed_values = definition.get("allowed")
            if allowed_values and value not in allowed_values:
                allowed_display = ", ".join(sorted(allowed_values))
                raise ValueError(f"Value for {key} must be one of: {allowed_display}")
            pattern = definition.get("pattern")
            if pattern and not re.match(pattern, value):
                raise ValueError(f"Value for {key} must match {pattern}")
        elif target_type == "json":
            value = value if value is not None else {}

        return value, target_type

    def _db_to_model(self, setting: AppSettingDB) -> AppSetting:
        definition = self._definition_for_key(setting.key)
        return AppSetting(
            key=setting.key,
            value=setting.value,
            value_type=setting.value_type or definition.get("value_type", "string"),
            label=setting.label or definition.get("label"),
            description=setting.description or definition.get("description"),
            category=setting.category or definition.get("category"),
            created_at=setting.created_at,
            updated_at=setting.updated_at,
        )

    def list_settings(self) -> List[AppSetting]:
        self.ensure_defaults()
        settings = (
            self.session.query(AppSettingDB)
            .order_by(AppSettingDB.category.nullslast(), AppSettingDB.key)
            .all()
        )
        return [self._db_to_model(setting) for setting in settings]

    def get_setting(self, key: str) -> Optional[AppSetting]:
        self.ensure_defaults()
        setting = self.session.query(AppSettingDB).filter_by(key=key).first()
        if not setting:
            return None
        return self._db_to_model(setting)

    def get_setting_value(self, key: str, default: Any = None) -> Any:
        setting = self.get_setting(key)
        if setting is not None:
            return setting.value
        definition = self._definition_for_key(key)
        if "default" in definition:
            return definition["default"]
        return default

    def upsert_setting(self, key: str, update: AppSettingUpdate) -> AppSetting:
        validated_value, value_type = self._validate_value(key, update.value, update.value_type)

        try:
            setting = self.session.query(AppSettingDB).filter_by(key=key).first()
            if setting:
                setting.value = validated_value
                setting.value_type = value_type
                if update.label is not None:
                    setting.label = update.label
                if update.description is not None:
                    setting.description = update.description
                if update.category is not None:
                    setting.category = update.category
            else:
                definition = self._definition_for_key(key)
                setting = AppSettingDB(
                    key=key,
                    value=validated_value,
                    value_type=value_type,
                    label=update.label or definition.get("label"),
                    description=update.description or definition.get("description"),
                    category=update.category or definition.get("category"),
                )
                self.session.add(setting)

            self.session.commit()
            self.session.refresh(setting)
            return self._db_to_model(setting)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to upsert setting %s: %s", key, exc)
            self.session.rollback()
            raise

    def delete_setting(self, key: str) -> bool:
        try:
            setting = self.session.query(AppSettingDB).filter_by(key=key).first()
            if not setting:
                return False
            self.session.delete(setting)
            self.session.commit()
            return True
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to delete setting %s: %s", key, exc)
            self.session.rollback()
            raise

    def get_task_issue_lookback_hours(self) -> int:
        value = self.get_setting_value(TASK_ISSUE_LOOKBACK_KEY, DEFAULT_SETTING_DEFINITIONS[TASK_ISSUE_LOOKBACK_KEY]["default"])
        try:
            normalized, _ = self._normalize_number(value)
            numeric_value = int(normalized)
        except ValueError:
            numeric_value = DEFAULT_SETTING_DEFINITIONS[TASK_ISSUE_LOOKBACK_KEY]["default"]
        min_value = DEFAULT_SETTING_DEFINITIONS[TASK_ISSUE_LOOKBACK_KEY].get("min", 1)
        max_value = DEFAULT_SETTING_DEFINITIONS[TASK_ISSUE_LOOKBACK_KEY].get("max")
        numeric_value = max(min_value, numeric_value)
        if max_value is not None:
            numeric_value = min(max_value, numeric_value)
        return numeric_value

    def _get_bounded_number_setting(self, key: str) -> int:
        definition = DEFAULT_SETTING_DEFINITIONS[key]
        value = self.get_setting_value(key, definition["default"])
        try:
            normalized, _ = self._normalize_number(value)
            numeric_value = int(normalized)
        except ValueError:
            numeric_value = definition["default"]
        numeric_value = max(definition.get("min", 1), numeric_value)
        max_value = definition.get("max")
        if max_value is not None:
            numeric_value = min(max_value, numeric_value)
        return numeric_value

    def get_data_retention_config(self) -> DataRetentionConfig:
        """Return normalized data retention configuration."""
        self.ensure_defaults()
        policy = DataRetentionConfig(
            task_successful_days=self._get_bounded_number_setting(RETENTION_TASK_SUCCESSFUL_DAYS_KEY),
            task_unsuccessful_days=self._get_bounded_number_setting(RETENTION_TASK_UNSUCCESSFUL_DAYS_KEY),
            worker_events_days=self._get_bounded_number_setting(RETENTION_WORKER_EVENTS_DAYS_KEY),
            workflow_executions_days=self._get_bounded_number_setting(RETENTION_WORKFLOW_EXECUTIONS_DAYS_KEY),
            task_daily_stats_days=self._get_bounded_number_setting(RETENTION_TASK_DAILY_STATS_DAYS_KEY),
            inactive_sessions_days=self._get_bounded_number_setting(RETENTION_INACTIVE_SESSIONS_DAYS_KEY),
        )
        logger.info(
            "Data retention policy loaded: task_successful_days=%s "
            "task_unsuccessful_days=%s worker_events_days=%s workflow_executions_days=%s "
            "task_daily_stats_days=%s inactive_sessions_days=%s",
            policy.task_successful_days,
            policy.task_unsuccessful_days,
            policy.worker_events_days,
            policy.workflow_executions_days,
            policy.task_daily_stats_days,
            policy.inactive_sessions_days,
        )
        return policy

    def get_retention_schedule_config(self) -> RetentionScheduleConfig:
        """Return normalized automatic retention cleanup schedule."""
        self.ensure_defaults()
        enabled_value = self.get_setting_value(RETENTION_SCHEDULE_ENABLED_KEY, False)
        try:
            enabled = self._normalize_boolean(enabled_value)
        except ValueError:
            enabled = False

        preset = str(self.get_setting_value(RETENTION_SCHEDULE_PRESET_KEY, "daily"))
        if preset not in {"hourly", "daily", "weekly", "monthly"}:
            preset = "daily"

        timezone_value = str(self.get_setting_value(RETENTION_SCHEDULE_TIMEZONE_KEY, "UTC"))
        if timezone_value != "UTC":
            timezone_value = "UTC"

        schedule = RetentionScheduleConfig(
            enabled=enabled,
            preset=preset,
            hour=self._get_bounded_number_setting(RETENTION_SCHEDULE_HOUR_KEY),
            minute=self._get_bounded_number_setting(RETENTION_SCHEDULE_MINUTE_KEY),
            weekday=self._get_bounded_number_setting(RETENTION_SCHEDULE_WEEKDAY_KEY),
            month_day=self._get_bounded_number_setting(RETENTION_SCHEDULE_MONTH_DAY_KEY),
            timezone=timezone_value,
        )
        logger.info(
            "Retention schedule loaded: enabled=%s preset=%s hour=%s minute=%s "
            "weekday=%s month_day=%s timezone=%s",
            schedule.enabled,
            schedule.preset,
            schedule.hour,
            schedule.minute,
            schedule.weekday,
            schedule.month_day,
            schedule.timezone,
        )
        return schedule

    def get_retention_last_run(self) -> RetentionLastRun:
        """Return the last automatic retention cleanup status."""
        self.ensure_defaults()
        value = self.get_setting_value(RETENTION_LAST_RUN_KEY, {})
        if not isinstance(value, dict):
            value = {}
        try:
            return RetentionLastRun(**value)
        except Exception:  # pylint: disable=broad-except
            return RetentionLastRun()

    def set_retention_last_run(self, last_run: RetentionLastRun) -> AppSetting:
        """Persist the last automatic retention cleanup status."""
        logger.info(
            "Persisting retention last run: status=%s started_at=%s finished_at=%s "
            "total_deleted=%s dry_run=%s error=%s",
            last_run.status,
            last_run.started_at.isoformat() if last_run.started_at else None,
            last_run.finished_at.isoformat() if last_run.finished_at else None,
            last_run.total_deleted,
            last_run.dry_run,
            last_run.error,
        )
        return self.upsert_setting(
            RETENTION_LAST_RUN_KEY,
            AppSettingUpdate(
                value=last_run.model_dump(mode="json"),
                value_type="json",
                category="data_retention",
            ),
        )

    def get_config_snapshot(self) -> AppConfigSnapshot:
        """Return grouped configuration for clients."""
        self.ensure_defaults()
        lookback_hours = self.get_task_issue_lookback_hours()
        return AppConfigSnapshot(
            task_issue_summary=TaskIssueConfig(lookback_hours=lookback_hours),
            data_retention=self.get_data_retention_config(),
            retention_schedule=self.get_retention_schedule_config(),
            retention_last_run=self.get_retention_last_run(),
        )
