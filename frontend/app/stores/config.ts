import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  useApiService,
  type AppConfigSnapshotDTO,
  type AppSettingDTO,
  type AppSettingInput,
  type DataRetentionConfigDTO,
  type RetentionCleanupResponseDTO,
  type RetentionLastRunDTO,
  type RetentionScheduleConfigDTO,
} from '~/services/apiClient'

const TASK_ISSUE_LOOKBACK_DEFAULT = 24
const TASK_ISSUE_LOOKBACK_KEY = 'task_issue_summary.lookback_hours'
const RETENTION_DEFAULTS: DataRetentionConfigDTO = {
  task_successful_days: 14,
  task_unsuccessful_days: 30,
  worker_events_days: 30,
  workflow_executions_days: 30,
  task_daily_stats_days: 365,
  inactive_sessions_days: 30,
}
const RETENTION_KEYS = {
  task_successful_days: 'data_retention.task_successful_days',
  task_unsuccessful_days: 'data_retention.task_unsuccessful_days',
  worker_events_days: 'data_retention.worker_events_days',
  workflow_executions_days: 'data_retention.workflow_executions_days',
  task_daily_stats_days: 'data_retention.task_daily_stats_days',
  inactive_sessions_days: 'data_retention.inactive_sessions_days',
} as const
const RETENTION_SCHEDULE_KEYS = {
  enabled: 'data_retention.schedule.enabled',
  preset: 'data_retention.schedule.preset',
  hour: 'data_retention.schedule.hour',
  minute: 'data_retention.schedule.minute',
  weekday: 'data_retention.schedule.weekday',
  month_day: 'data_retention.schedule.month_day',
  timezone: 'data_retention.schedule.timezone',
} as const
const RETENTION_SCHEDULE_DEFAULTS: RetentionScheduleConfigDTO = {
  enabled: false,
  preset: 'daily',
  hour: 3,
  minute: 0,
  weekday: 0,
  month_day: 1,
  timezone: 'UTC',
}
const RETENTION_LAST_RUN_DEFAULTS: RetentionLastRunDTO = {
  status: 'never',
  total_deleted: 0,
  dry_run: false,
  results: [],
}

export const useConfigStore = defineStore('config', () => {
  const apiService = useApiService()

  const config = ref<AppConfigSnapshotDTO | null>(null)
  const settings = ref<AppSettingDTO[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const settingsMap = computed<Record<string, AppSettingDTO>>(() => {
    return settings.value.reduce((acc, setting) => {
      acc[setting.key] = setting
      return acc
    }, {} as Record<string, AppSettingDTO>)
  })

  const dataRetention = computed<DataRetentionConfigDTO>(() => {
    return config.value?.data_retention ?? {
      task_successful_days: Number(settingsMap.value[RETENTION_KEYS.task_successful_days]?.value ?? RETENTION_DEFAULTS.task_successful_days),
      task_unsuccessful_days: Number(settingsMap.value[RETENTION_KEYS.task_unsuccessful_days]?.value ?? RETENTION_DEFAULTS.task_unsuccessful_days),
      worker_events_days: Number(settingsMap.value[RETENTION_KEYS.worker_events_days]?.value ?? RETENTION_DEFAULTS.worker_events_days),
      workflow_executions_days: Number(settingsMap.value[RETENTION_KEYS.workflow_executions_days]?.value ?? RETENTION_DEFAULTS.workflow_executions_days),
      task_daily_stats_days: Number(settingsMap.value[RETENTION_KEYS.task_daily_stats_days]?.value ?? RETENTION_DEFAULTS.task_daily_stats_days),
      inactive_sessions_days: Number(settingsMap.value[RETENTION_KEYS.inactive_sessions_days]?.value ?? RETENTION_DEFAULTS.inactive_sessions_days),
    }
  })

  const taskIssueLookbackHours = computed(() => {
    if (config.value?.task_issue_summary?.lookback_hours) {
      return config.value.task_issue_summary.lookback_hours
    }
    const stored = settingsMap.value[TASK_ISSUE_LOOKBACK_KEY]
    if (stored && typeof stored.value === 'number') {
      return stored.value
    }
    return TASK_ISSUE_LOOKBACK_DEFAULT
  })

  const retentionSchedule = computed<RetentionScheduleConfigDTO>(() => {
    return config.value?.retention_schedule ?? {
      enabled: Boolean(settingsMap.value[RETENTION_SCHEDULE_KEYS.enabled]?.value ?? RETENTION_SCHEDULE_DEFAULTS.enabled),
      preset: (settingsMap.value[RETENTION_SCHEDULE_KEYS.preset]?.value as 'hourly' | 'daily' | 'weekly' | 'monthly' | undefined) ?? RETENTION_SCHEDULE_DEFAULTS.preset,
      hour: Number(settingsMap.value[RETENTION_SCHEDULE_KEYS.hour]?.value ?? RETENTION_SCHEDULE_DEFAULTS.hour),
      minute: Number(settingsMap.value[RETENTION_SCHEDULE_KEYS.minute]?.value ?? RETENTION_SCHEDULE_DEFAULTS.minute),
      weekday: Number(settingsMap.value[RETENTION_SCHEDULE_KEYS.weekday]?.value ?? RETENTION_SCHEDULE_DEFAULTS.weekday),
      month_day: Number(settingsMap.value[RETENTION_SCHEDULE_KEYS.month_day]?.value ?? RETENTION_SCHEDULE_DEFAULTS.month_day),
      timezone: String(settingsMap.value[RETENTION_SCHEDULE_KEYS.timezone]?.value ?? RETENTION_SCHEDULE_DEFAULTS.timezone) as 'UTC',
    }
  })

  const retentionLastRun = computed<RetentionLastRunDTO>(() => {
    return config.value?.retention_last_run ?? RETENTION_LAST_RUN_DEFAULTS
  })

  async function fetchConfig() {
    try {
      isLoading.value = true
      error.value = null
      const [configSnapshot, storedSettings] = await Promise.all([
        apiService.getAppConfig(),
        apiService.listSettings()
      ])
      config.value = configSnapshot
      settings.value = storedSettings
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load configuration'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function upsertSetting(key: string, payload: AppSettingInput) {
    try {
      const updated = await apiService.upsertSetting(key, payload)
      const existingIndex = settings.value.findIndex(setting => setting.key === key)
      if (existingIndex >= 0) {
        settings.value.splice(existingIndex, 1, updated)
      } else {
        settings.value.push(updated)
      }

      if (key === TASK_ISSUE_LOOKBACK_KEY) {
        config.value = {
          ...(config.value ?? {
            task_issue_summary: { lookback_hours: TASK_ISSUE_LOOKBACK_DEFAULT },
            data_retention: dataRetention.value,
            retention_schedule: retentionSchedule.value,
            retention_last_run: retentionLastRun.value,
          }),
          task_issue_summary: { lookback_hours: Number(updated.value) }
        }
      }

      const retentionEntry = Object.entries(RETENTION_KEYS).find(([, settingKey]) => settingKey === key)
      if (retentionEntry) {
        const [retentionField] = retentionEntry as [keyof DataRetentionConfigDTO, string]
        config.value = {
          ...(config.value ?? {
            task_issue_summary: { lookback_hours: TASK_ISSUE_LOOKBACK_DEFAULT },
            data_retention: dataRetention.value,
            retention_schedule: retentionSchedule.value,
            retention_last_run: retentionLastRun.value,
          }),
          data_retention: {
            ...dataRetention.value,
            [retentionField]: Number(updated.value),
          },
        }
      }

      const scheduleEntry = Object.entries(RETENTION_SCHEDULE_KEYS).find(([, settingKey]) => settingKey === key)
      if (scheduleEntry) {
        const [scheduleField] = scheduleEntry as [keyof RetentionScheduleConfigDTO, string]
        const value = ['hour', 'minute', 'weekday', 'month_day'].includes(scheduleField)
          ? Number(updated.value)
          : updated.value
        config.value = {
          ...(config.value ?? {
            task_issue_summary: { lookback_hours: TASK_ISSUE_LOOKBACK_DEFAULT },
            data_retention: dataRetention.value,
            retention_schedule: retentionSchedule.value,
            retention_last_run: retentionLastRun.value,
          }),
          retention_schedule: {
            ...retentionSchedule.value,
            [scheduleField]: value,
          },
        }
      }

      return updated
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to save setting'
      throw err
    }
  }

  async function deleteSetting(key: string) {
    try {
      await apiService.deleteSetting(key)
      settings.value = settings.value.filter(setting => setting.key !== key)
      if (key === TASK_ISSUE_LOOKBACK_KEY && config.value) {
        config.value = {
          ...config.value,
          task_issue_summary: { lookback_hours: TASK_ISSUE_LOOKBACK_DEFAULT }
        }
      }

      const retentionEntry = Object.entries(RETENTION_KEYS).find(([, settingKey]) => settingKey === key)
      if (retentionEntry && config.value) {
        const [retentionField] = retentionEntry as [keyof DataRetentionConfigDTO, string]
        config.value = {
          ...config.value,
          data_retention: {
            ...config.value.data_retention,
            [retentionField]: RETENTION_DEFAULTS[retentionField],
          },
        }
      }

      const scheduleEntry = Object.entries(RETENTION_SCHEDULE_KEYS).find(([, settingKey]) => settingKey === key)
      if (scheduleEntry && config.value) {
        const [scheduleField] = scheduleEntry as [keyof RetentionScheduleConfigDTO, string]
        config.value = {
          ...config.value,
          retention_schedule: {
            ...config.value.retention_schedule,
            [scheduleField]: RETENTION_SCHEDULE_DEFAULTS[scheduleField],
          },
        }
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to delete setting'
      throw err
    }
  }

  async function updateTaskIssueLookback(hours: number) {
    return upsertSetting(TASK_ISSUE_LOOKBACK_KEY, {
      value: hours,
      value_type: 'number',
      category: 'task_issue_summary'
    })
  }

  async function updateDataRetention(values: DataRetentionConfigDTO) {
    const entries = Object.entries(RETENTION_KEYS) as Array<[keyof DataRetentionConfigDTO, string]>
    for (const [field, key] of entries) {
      await upsertSetting(key, {
        value: Number(values[field]),
        value_type: 'number',
        category: 'data_retention'
      })
    }
    await fetchConfig()
  }

  async function updateRetentionSchedule(values: RetentionScheduleConfigDTO) {
    await upsertSetting(RETENTION_SCHEDULE_KEYS.enabled, {
      value: values.enabled,
      value_type: 'boolean',
      category: 'data_retention'
    })
    await upsertSetting(RETENTION_SCHEDULE_KEYS.preset, {
      value: values.preset,
      value_type: 'string',
      category: 'data_retention'
    })
    await upsertSetting(RETENTION_SCHEDULE_KEYS.hour, {
      value: Number(values.hour),
      value_type: 'number',
      category: 'data_retention'
    })
    await upsertSetting(RETENTION_SCHEDULE_KEYS.minute, {
      value: Number(values.minute),
      value_type: 'number',
      category: 'data_retention'
    })
    await upsertSetting(RETENTION_SCHEDULE_KEYS.weekday, {
      value: Number(values.weekday),
      value_type: 'number',
      category: 'data_retention'
    })
    await upsertSetting(RETENTION_SCHEDULE_KEYS.month_day, {
      value: Number(values.month_day),
      value_type: 'number',
      category: 'data_retention'
    })
    await upsertSetting(RETENTION_SCHEDULE_KEYS.timezone, {
      value: values.timezone ?? 'UTC',
      value_type: 'string',
      category: 'data_retention'
    })
    await fetchConfig()
  }

  async function runRetentionCleanup(dryRun = true): Promise<RetentionCleanupResponseDTO> {
    return apiService.runRetentionCleanup(dryRun)
  }

  return {
    config,
    settings,
    isLoading,
    error,
    taskIssueLookbackHours,
    dataRetention,
    retentionSchedule,
    retentionLastRun,
    settingsMap,
    fetchConfig,
    upsertSetting,
    deleteSetting,
    updateTaskIssueLookback,
    updateDataRetention,
    updateRetentionSchedule,
    runRetentionCleanup,
  }
})
