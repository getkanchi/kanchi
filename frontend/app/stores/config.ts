import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'
import {
  useApiService,
  type AppConfigSnapshotDTO,
  type AppSettingDTO,
  type AppSettingInput
} from '~/services/apiClient'

const TASK_ISSUE_LOOKBACK_DEFAULT = 24
const TASK_ISSUE_LOOKBACK_KEY = 'task_issue_summary.lookback_hours'

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
          ...(config.value ?? { task_issue_summary: { lookback_hours: TASK_ISSUE_LOOKBACK_DEFAULT } }),
          task_issue_summary: { lookback_hours: Number(updated.value) }
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

  return {
    config: readonly(config),
    settings: readonly(settings),
    isLoading: readonly(isLoading),
    error: readonly(error),
    taskIssueLookbackHours,
    settingsMap,
    fetchConfig,
    upsertSetting,
    deleteSetting,
    updateTaskIssueLookback,
  }
})
