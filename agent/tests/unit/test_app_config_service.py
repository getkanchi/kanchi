import unittest

from services.app_config_service import (
    AppConfigService,
    TASK_ISSUE_LOOKBACK_KEY,
)
from models import AppSettingUpdate
from tests.base import DatabaseTestCase
from database import AppSettingDB


class TestAppConfigService(DatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.service = AppConfigService(self.session)
        self.service.ensure_defaults()

    def test_ensure_defaults_persists_task_issue_setting(self):
        setting = (
            self.session.query(AppSettingDB)
            .filter_by(key=TASK_ISSUE_LOOKBACK_KEY)
            .first()
        )
        self.assertIsNotNone(setting)
        self.assertEqual(setting.value, 24)
        self.assertEqual(setting.category, "task_issue_summary")

    def test_get_task_issue_lookback_hours_uses_overrides(self):
        updated = self.service.upsert_setting(
            TASK_ISSUE_LOOKBACK_KEY,
            AppSettingUpdate(value=12, value_type="number"),
        )
        self.assertEqual(updated.value, 12)
        self.assertEqual(self.service.get_task_issue_lookback_hours(), 12)

    def test_upsert_setting_rejects_invalid_number(self):
        with self.assertRaises(ValueError):
            self.service.upsert_setting(
                TASK_ISSUE_LOOKBACK_KEY,
                AppSettingUpdate(value=0, value_type="number"),
            )


if __name__ == "__main__":
    unittest.main()
