import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'
import { useApiService } from '../services/apiClient'
import type { TaskEventResponse } from '../services/apiClient'

const DEFAULT_LOOKBACK_HOURS = 24
const LOOKBACK_WINDOW_MS = DEFAULT_LOOKBACK_HOURS * 60 * 60 * 1000

function parseTimestamp(timestamp?: string | null): number | null {
  if (!timestamp) {
    return null
  }
  const value = Date.parse(timestamp)
  return Number.isNaN(value) ? null : value
}

export const useFailedTasksStore = defineStore('failedTasks', () => {
  const apiService = useApiService()

  const failedTasks = ref<TaskEventResponse[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const lastFetchedAt = ref<Date | null>(null)

  const totalFailedTasks = computed(() => failedTasks.value.length)
  const latestFailedTask = computed(() => failedTasks.value[0] || null)

  function sortTasks(tasks: TaskEventResponse[]): TaskEventResponse[] {
    return [...tasks].sort((a, b) => {
      const aTime = parseTimestamp(a.timestamp) ?? 0
      const bTime = parseTimestamp(b.timestamp) ?? 0
      return bTime - aTime
    })
  }

  function setTasks(tasks: TaskEventResponse[]) {
    failedTasks.value = sortTasks(tasks)
  }

  function pruneExpired(referenceTime = Date.now()) {
    const cutoff = referenceTime - LOOKBACK_WINDOW_MS
    failedTasks.value = failedTasks.value.filter(task => {
      const timestamp = parseTimestamp(task.timestamp)
      return timestamp !== null && timestamp >= cutoff
    })
  }

  function upsertFailedTask(task: TaskEventResponse) {
    if (!task.task_id) {
      return
    }

    const existingIndex = failedTasks.value.findIndex(t => t.task_id === task.task_id)
    const next = existingIndex >= 0
      ? failedTasks.value.map((existing, idx) => (idx === existingIndex ? task : existing))
      : [...failedTasks.value, task]

    failedTasks.value = sortTasks(next)
  }

  function removeFailedTask(taskId?: string | null) {
    if (!taskId) {
      return
    }
    failedTasks.value = failedTasks.value.filter(task => task.task_id !== taskId)
  }

  function applyResolutionState(taskId: string, resolved: boolean, resolved_by?: string | null, resolved_at?: string | null) {
    const normalizedResolvedAt = resolved_at ? new Date(resolved_at).toISOString() : null
    failedTasks.value = failedTasks.value.map(task => {
      if (task.task_id !== taskId) return task
      return {
        ...task,
        resolved,
        resolved_by: resolved_by ?? null,
        resolved_at: normalizedResolvedAt,
      } as TaskEventResponse & { resolved?: boolean; resolved_by?: string | null; resolved_at?: string | null }
    })
  }

  function shouldExclude(task: TaskEventResponse): boolean {
    if (task.has_retries) {
      return true
    }
    if (task.retried_by && Array.isArray(task.retried_by) && task.retried_by.length > 0) {
      return true
    }
    return false
  }

  async function fetchFailedTasks(options?: { hours?: number; limit?: number; includeRetried?: boolean }) {
    try {
      isLoading.value = true
      error.value = null

      const response = await apiService.getRecentFailedTasks({
        hours: options?.hours ?? DEFAULT_LOOKBACK_HOURS,
        limit: options?.limit,
        include_retried: options?.includeRetried ?? false
      })

      const filtered = response.filter(task => !shouldExclude(task))
      setTasks(filtered)
      pruneExpired()
      lastFetchedAt.value = new Date()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch failed tasks'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function resolveTask(taskId: string, resolvedBy?: string | null) {
    try {
      error.value = null
      const response = await apiService.resolveTask(taskId, resolvedBy ?? undefined)
      applyResolutionState(
        taskId,
        true,
        response.resolved_by ?? resolvedBy ?? null,
        response.resolved_at ?? new Date().toISOString()
      )
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to resolve task'
      throw err
    }
  }

  async function clearTaskResolution(taskId: string) {
    try {
      error.value = null
      await apiService.clearTaskResolution(taskId)
      applyResolutionState(taskId, false, null, null)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to clear task resolution'
      throw err
    }
  }

  function updateFromLiveEvent(event: TaskEventResponse) {
    const environmentStore = useEnvironmentStore()
    const { matchesEnvironment } = useEnvironmentMatcher()

    if (!matchesEnvironment(event, environmentStore.activeEnvironment)) {
      return
    }

    const eventType = event.event_type

    if (eventType === 'task-failed') {
      if (shouldExclude(event)) {
        removeFailedTask(event.task_id)
        return
      }

      const timestamp = parseTimestamp(event.timestamp)
      if (timestamp === null) {
        return
      }

      const cutoff = Date.now() - LOOKBACK_WINDOW_MS
      if (timestamp < cutoff) {
        return
      }

      upsertFailedTask(event)
      pruneExpired()
      return
    }

    if (eventType === 'task-retried' || eventType === 'task-succeeded') {
      removeFailedTask(event.task_id)
      return
    }
  }

  return {
    failedTasks: readonly(failedTasks),
    isLoading: readonly(isLoading),
    error: readonly(error),
    lastFetchedAt: readonly(lastFetchedAt),

    totalFailedTasks,
    latestFailedTask,

    fetchFailedTasks,
    updateFromLiveEvent,
    pruneExpired,
    removeFailedTask,
    applyResolutionState,
    resolveTask,
    clearTaskResolution,
  }
})
