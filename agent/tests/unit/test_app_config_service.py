import unittest

from services.app_config_service import (
    AppConfigService,
    TASK_ISSUE_LOOKBACK_KEY,
    RETENTION_TASK_SUCCESSFUL_DAYS_KEY,
    RETENTION_TASK_UNSUCCESSFUL_DAYS_KEY,
    RETENTION_SCHEDULE_ENABLED_KEY,
    RETENTION_SCHEDULE_HOUR_KEY,
    RETENTION_SCHEDULE_MINUTE_KEY,
    RETENTION_SCHEDULE_MONTH_DAY_KEY,
    RETENTION_SCHEDULE_PRESET_KEY,
    RETENTION_SCHEDULE_WEEKDAY_KEY,
)
from models import AppSettingUpdate, RetentionLastRun
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

    def test_get_data_retention_config_uses_defaults_and_overrides(self):
        defaults = self.service.get_data_retention_config()
        self.assertEqual(defaults.task_successful_days, 14)
        self.assertEqual(defaults.task_unsuccessful_days, 30)
        self.assertEqual(defaults.inactive_sessions_days, 30)

        self.service.upsert_setting(
            RETENTION_TASK_SUCCESSFUL_DAYS_KEY,
            AppSettingUpdate(value=7, value_type="number"),
        )
        self.service.upsert_setting(
            RETENTION_TASK_UNSUCCESSFUL_DAYS_KEY,
            AppSettingUpdate(value=45, value_type="number"),
        )
        updated = self.service.get_data_retention_config()
        self.assertEqual(updated.task_successful_days, 7)
        self.assertEqual(updated.task_unsuccessful_days, 45)

    def test_get_retention_schedule_uses_defaults_and_overrides(self):
        defaults = self.service.get_retention_schedule_config()
        self.assertFalse(defaults.enabled)
        self.assertEqual(defaults.preset, "daily")
        self.assertEqual(defaults.hour, 3)
        self.assertEqual(defaults.minute, 0)
        self.assertEqual(defaults.weekday, 0)
        self.assertEqual(defaults.month_day, 1)
        self.assertEqual(defaults.timezone, "UTC")

        self.service.upsert_setting(
            RETENTION_SCHEDULE_ENABLED_KEY,
            AppSettingUpdate(value=True, value_type="boolean"),
        )
        self.service.upsert_setting(
            RETENTION_SCHEDULE_PRESET_KEY,
            AppSettingUpdate(value="weekly", value_type="string"),
        )
        self.service.upsert_setting(
            RETENTION_SCHEDULE_HOUR_KEY,
            AppSettingUpdate(value=4, value_type="number"),
        )
        self.service.upsert_setting(
            RETENTION_SCHEDULE_MINUTE_KEY,
            AppSettingUpdate(value=30, value_type="number"),
        )
        self.service.upsert_setting(
            RETENTION_SCHEDULE_WEEKDAY_KEY,
            AppSettingUpdate(value=2, value_type="number"),
        )
        self.service.upsert_setting(
            RETENTION_SCHEDULE_MONTH_DAY_KEY,
            AppSettingUpdate(value=16, value_type="number"),
        )

        updated = self.service.get_retention_schedule_config()
        self.assertTrue(updated.enabled)
        self.assertEqual(updated.preset, "weekly")
        self.assertEqual(updated.hour, 4)
        self.assertEqual(updated.minute, 30)
        self.assertEqual(updated.weekday, 2)
        self.assertEqual(updated.month_day, 16)

    def test_automatic_retention_cleanup_defaults_to_disabled_for_new_users(self):
        setting = (
            self.session.query(AppSettingDB)
            .filter_by(key=RETENTION_SCHEDULE_ENABLED_KEY)
            .first()
        )
        self.assertIsNotNone(setting)
        self.assertIs(setting.value, False)
        self.assertEqual(setting.value_type, "boolean")
        self.assertFalse(self.service.get_retention_schedule_config().enabled)

    def test_retention_schedule_rejects_invalid_values(self):
        with self.assertRaises(ValueError):
            self.service.upsert_setting(
                RETENTION_SCHEDULE_PRESET_KEY,
                AppSettingUpdate(value="yearly", value_type="string"),
            )
        with self.assertRaises(ValueError):
            self.service.upsert_setting(
                RETENTION_SCHEDULE_HOUR_KEY,
                AppSettingUpdate(value=24, value_type="number"),
            )

    def test_retention_last_run_round_trips(self):
        self.service.set_retention_last_run(RetentionLastRun(status="success", total_deleted=3))
        last_run = self.service.get_retention_last_run()
        self.assertEqual(last_run.status, "success")
        self.assertEqual(last_run.total_deleted, 3)

if __name__ == "__main__":
    unittest.main()
