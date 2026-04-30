import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'
import {
  useApiService,
  type AppConfigSnapshotDTO,
  type AppSettingDTO,
  type AppSettingInput,
  type DataRetentionConfigDTO,
  type RetentionCleanupResponseDTO,
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
          }),
          data_retention: {
            ...dataRetention.value,
            [retentionField]: Number(updated.value),
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
  }

  async function runRetentionCleanup(dryRun = true): Promise<RetentionCleanupResponseDTO> {
    return apiService.runRetentionCleanup(dryRun)
  }

  return {
    config: readonly(config),
    settings: readonly(settings),
    isLoading: readonly(isLoading),
    error: readonly(error),
    taskIssueLookbackHours,
    dataRetention,
    settingsMap,
    fetchConfig,
    upsertSetting,
    deleteSetting,
    updateTaskIssueLookback,
    updateDataRetention,
    runRetentionCleanup,
  }
})
