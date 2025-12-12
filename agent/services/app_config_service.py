"""Service for managing application configuration stored in the database."""

import logging
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from database import AppSettingDB
from models import AppSetting, AppSettingUpdate, AppConfigSnapshot, TaskIssueConfig

logger = logging.getLogger(__name__)

TASK_ISSUE_LOOKBACK_KEY = "task_issue_summary.lookback_hours"

DEFAULT_SETTING_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    TASK_ISSUE_LOOKBACK_KEY: {
        "default": 24,
        "value_type": "number",
        "label": "Task issue summary lookback (hours)",
        "description": "Number of hours of failed tasks to surface in the dashboard issue summary.",
        "category": "task_issue_summary",
        "min": 1,
        "max": 168,  # one week window cap to keep queries bounded
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

    def get_config_snapshot(self) -> AppConfigSnapshot:
        """Return grouped configuration for clients."""
        self.ensure_defaults()
        lookback_hours = self.get_task_issue_lookback_hours()
        return AppConfigSnapshot(
            task_issue_summary=TaskIssueConfig(lookback_hours=lookback_hours)
        )
