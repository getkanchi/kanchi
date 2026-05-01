import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'
import { useApiService, type TaskEventResponse, type TriageRecommendationResponse } from '../services/apiClient'

export interface TriageRecommendationListItem extends TriageRecommendationResponse {
  task_id: string
  task_name: string
  event_type: TaskEventResponse['event_type']
  timestamp: string
}

function toEventType(severity: TriageRecommendationResponse['severity']): TaskEventResponse['event_type'] {
  if (severity === 'critical') return 'task-failed'
  if (severity === 'warning') return 'task-received'
  return 'task-started'
}

function toListItem(item: TriageRecommendationResponse): TriageRecommendationListItem {
  return {
    ...item,
    task_id: item.task_id || item.recommendation_id,
    task_name: item.task_name || item.title,
    event_type: toEventType(item.severity),
    timestamp: new Date().toISOString(),
    hostname: item.hostname ?? null,
    supporting_task_ids: item.supporting_task_ids ?? [],
  }
}

export const useTriageRecommendationsStore = defineStore('triageRecommendations', () => {
  const apiService = useApiService()

  const recommendations = ref<TriageRecommendationListItem[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const lastFetchedAt = ref<Date | null>(null)

  const criticalCount = computed(() => recommendations.value.filter(item => item.severity === 'critical').length)

  async function fetchTriageRecommendations() {
    try {
      isLoading.value = true
      error.value = null
      const response = await apiService.getTriageRecommendations()
      recommendations.value = response.map(toListItem)
      lastFetchedAt.value = new Date()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch triage recommendations'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  function clearResolvedTask(taskId: string) {
    recommendations.value = recommendations.value.filter(item => item.task_id !== taskId && !item.supporting_task_ids.includes(taskId))
  }

  function updateFromLiveEvent(event: TaskEventResponse) {
    if (['task-succeeded', 'task-failed', 'task-retried', 'task-revoked', 'task-rejected'].includes(event.event_type)) {
      clearResolvedTask(event.task_id)
    }
  }

  return {
    recommendations: readonly(recommendations),
    isLoading: readonly(isLoading),
    error: readonly(error),
    lastFetchedAt: readonly(lastFetchedAt),
    criticalCount,
    fetchTriageRecommendations,
    clearResolvedTask,
    updateFromLiveEvent,
  }
})
