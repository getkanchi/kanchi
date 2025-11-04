import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { useApiService } from '~/services/apiClient'

// TODO: Isnt this available in the generated types ??
interface HealthData {
  status: string
  monitor_running: boolean
  connections: number
  workers: number
  database_url: string
  database_url_full: string
  broker_url: string
  broker_url_full: string
  uptime_seconds: number
  python_version: string
  platform: string
  system: string
  api_version: string
  development_mode: boolean
  log_level: string
  total_tasks_processed: number
  first_task_at: string | null
}

export const useHealthStore = defineStore('health', () => {
  const apiService = useApiService()

  const health = ref<HealthData | null>(null)

  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function fetchHealth() {
    try {
      isLoading.value = true
      error.value = null
      health.value = await apiService.healthCheck()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch health'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchHealthDetails() {
    try {
      isLoading.value = true
      error.value = null
      health.value = await apiService.healthDetailsCheck()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch health details'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  return {
    health: readonly(health),
    isLoading: readonly(isLoading),
    error: readonly(error),

    fetchHealth,
    fetchHealthDetails,
  }

})
