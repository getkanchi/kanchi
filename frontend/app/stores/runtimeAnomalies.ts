import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'
import { useApiService } from '../services/apiClient'
import type { TaskEventResponse, RuntimeAnomalyResponse } from '../services/apiClient'

export interface RuntimeAnomalyListItem extends TaskEventResponse {
  anomaly_type: RuntimeAnomalyResponse['anomaly_type']
  runtime_seconds: number
  baseline_runtime_seconds?: number | null
  progress_age_seconds?: number | null
  worker_active_task_count: number
  threshold_seconds: number
  detail: string
}

function toListItem(anomaly: RuntimeAnomalyResponse): RuntimeAnomalyListItem {
  return {
    ...anomaly.task,
    anomaly_type: anomaly.anomaly_type,
    runtime_seconds: anomaly.runtime_seconds,
    baseline_runtime_seconds: anomaly.baseline_runtime_seconds ?? null,
    progress_age_seconds: anomaly.progress_age_seconds ?? null,
    worker_active_task_count: anomaly.worker_active_task_count,
    threshold_seconds: anomaly.threshold_seconds,
    detail: anomaly.detail,
  }
}

export const useRuntimeAnomaliesStore = defineStore('runtimeAnomalies', () => {
  const apiService = useApiService()

  const anomalies = ref<RuntimeAnomalyListItem[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const lastFetchedAt = ref<Date | null>(null)

  const longRunningCount = computed(() => anomalies.value.filter(item => item.anomaly_type === 'long_running').length)
  const stalledProgressCount = computed(() => anomalies.value.filter(item => item.anomaly_type === 'stalled_progress').length)

  async function fetchRuntimeAnomalies() {
    try {
      isLoading.value = true
      error.value = null
      const response = await apiService.getRuntimeAnomalies()
      anomalies.value = response.map(toListItem)
      lastFetchedAt.value = new Date()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch runtime anomalies'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  function clearResolvedTask(taskId: string) {
    anomalies.value = anomalies.value.filter(item => item.task_id !== taskId)
  }

  function updateFromLiveEvent(event: TaskEventResponse) {
    if (['task-succeeded', 'task-failed', 'task-retried', 'task-revoked', 'task-rejected'].includes(event.event_type)) {
      clearResolvedTask(event.task_id)
    }
  }

  return {
    anomalies: readonly(anomalies),
    isLoading: readonly(isLoading),
    error: readonly(error),
    lastFetchedAt: readonly(lastFetchedAt),
    longRunningCount,
    stalledProgressCount,
    fetchRuntimeAnomalies,
    clearResolvedTask,
    updateFromLiveEvent,
  }
})
