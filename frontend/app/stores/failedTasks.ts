import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'
import { useApiService } from '../services/apiClient'
import type { FailureNoveltyStatus, TaskFailureNoveltyResponse } from '../services/apiClient'

const DEFAULT_LOOKBACK_HOURS = 24
const MIN_LOOKBACK_HOURS = 1
const LOOKBACK_HOURS_FALLBACK = DEFAULT_LOOKBACK_HOURS

function parseTimestamp(timestamp?: string | null): number | null {
  if (!timestamp) {
    return null
  }
  const value = Date.parse(timestamp)
  return Number.isNaN(value) ? null : value
}

export const useFailedTasksStore = defineStore('failedTasks', () => {
  const apiService = useApiService()

  const failedTasks = ref<TaskFailureNoveltyResponse[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const lastFetchedAt = ref<Date | null>(null)
  const lookbackHours = ref(DEFAULT_LOOKBACK_HOURS)
  const lookbackWindowMs = computed(() => lookbackHours.value * 60 * 60 * 1000)

  const totalFailedTasks = computed(() => failedTasks.value.length)
  const latestFailedTask = computed(() => failedTasks.value[0] || null)

  function noveltyPriority(task: TaskFailureNoveltyResponse): number {
    switch (task.failure_novelty_status) {
      case 'new':
        return 0
      case 'regressed':
        return 1
      case 'recurring':
        return 2
      default:
        return 3
    }
  }

  function sortTasks(tasks: TaskFailureNoveltyResponse[]): TaskFailureNoveltyResponse[] {
    return [...tasks].sort((a, b) => {
      const noveltyDiff = noveltyPriority(a) - noveltyPriority(b)
      if (noveltyDiff !== 0) {
        return noveltyDiff
      }
      const aTime = parseTimestamp(a.timestamp) ?? 0
      const bTime = parseTimestamp(b.timestamp) ?? 0
      return bTime - aTime
    })
  }

  function setTasks(tasks: TaskFailureNoveltyResponse[]) {
    failedTasks.value = sortTasks(tasks)
  }

  function pruneExpired(referenceTime = Date.now()) {
    const cutoff = referenceTime - lookbackWindowMs.value
    failedTasks.value = failedTasks.value.filter(task => {
      const timestamp = parseTimestamp(task.timestamp)
      return timestamp !== null && timestamp >= cutoff
    })
  }

  function upsertFailedTask(task: TaskFailureNoveltyResponse) {
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
      } as TaskFailureNoveltyResponse
    })
  }

  function shouldExclude(task: TaskFailureNoveltyResponse): boolean {
    if (task.has_retries) {
      return true
    }
    if (task.retried_by && Array.isArray(task.retried_by) && task.retried_by.length > 0) {
      return true
    }
    return false
  }

  function setLookbackHours(hours: number | undefined) {
    if (typeof hours !== 'number' || Number.isNaN(hours)) {
      lookbackHours.value = LOOKBACK_HOURS_FALLBACK
      return
    }
    lookbackHours.value = Math.max(MIN_LOOKBACK_HOURS, hours)
  }

  async function fetchFailedTasks(options?: {
    hours?: number
    limit?: number
    includeRetried?: boolean
    noveltyStatus?: FailureNoveltyStatus
    noveltyLookbackHours?: number
  }) {
    try {
      isLoading.value = true
      error.value = null

      const effectiveHours = options?.hours ?? lookbackHours.value
      setLookbackHours(effectiveHours)

      const response = await apiService.getRecentFailedTasks({
        hours: effectiveHours,
        limit: options?.limit,
        include_retried: options?.includeRetried ?? false,
        novelty_status: options?.noveltyStatus,
        novelty_lookback_hours: options?.noveltyLookbackHours,
        sort_by: 'novelty',
        sort_order: 'desc',
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

  function updateFromLiveEvent(event: TaskFailureNoveltyResponse) {
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

      const cutoff = Date.now() - lookbackWindowMs.value
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
    lookbackHours: readonly(lookbackHours),

    totalFailedTasks,
    latestFailedTask,

    fetchFailedTasks,
    setLookbackHours,
    updateFromLiveEvent,
    pruneExpired,
    removeFailedTask,
    applyResolutionState,
    resolveTask,
    clearTaskResolution,
  }
})
