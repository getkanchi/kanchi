import unittest

from services.app_config_service import (
    AppConfigService,
    TASK_ISSUE_LOOKBACK_KEY,
    RETENTION_TASK_SUCCESSFUL_DAYS_KEY,
    RETENTION_TASK_UNSUCCESSFUL_DAYS_KEY,
    RETENTION_SCHEDULE_ENABLED_KEY,
    RETENTION_SCHEDULE_FREQUENCY_KEY,
    RETENTION_SCHEDULE_RUN_AT_KEY,
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
        self.assertEqual(defaults.frequency, "daily")
        self.assertEqual(defaults.run_at, "03:00")

        self.service.upsert_setting(
            RETENTION_SCHEDULE_ENABLED_KEY,
            AppSettingUpdate(value=True, value_type="boolean"),
        )
        self.service.upsert_setting(
            RETENTION_SCHEDULE_FREQUENCY_KEY,
            AppSettingUpdate(value="weekly", value_type="string"),
        )
        self.service.upsert_setting(
            RETENTION_SCHEDULE_RUN_AT_KEY,
            AppSettingUpdate(value="04:30", value_type="string"),
        )

        updated = self.service.get_retention_schedule_config()
        self.assertTrue(updated.enabled)
        self.assertEqual(updated.frequency, "weekly")
        self.assertEqual(updated.run_at, "04:30")

    def test_retention_schedule_rejects_invalid_values(self):
        with self.assertRaises(ValueError):
            self.service.upsert_setting(
                RETENTION_SCHEDULE_FREQUENCY_KEY,
                AppSettingUpdate(value="hourly", value_type="string"),
            )
        with self.assertRaises(ValueError):
            self.service.upsert_setting(
                RETENTION_SCHEDULE_RUN_AT_KEY,
                AppSettingUpdate(value="25:00", value_type="string"),
            )

    def test_retention_last_run_round_trips(self):
        self.service.set_retention_last_run(RetentionLastRun(status="success", total_deleted=3))
        last_run = self.service.get_retention_last_run()
        self.assertEqual(last_run.status, "success")
        self.assertEqual(last_run.total_deleted, 3)

if __name__ == "__main__":
    unittest.main()
