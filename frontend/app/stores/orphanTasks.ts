import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'
import { useApiService } from '../services/apiClient'
import type { TaskEventResponse } from '../services/apiClient'

export const useOrphanTasksStore = defineStore('orphanTasks', () => {
  const apiService = useApiService()

  const orphanedTasks = ref<TaskEventResponse[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const orphanedTasksCount = computed(() => orphanedTasks.value.length)
  
  const recentOrphanedTasks = computed(() => {
    const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000)
    return orphanedTasks.value.filter(task => {
      if (!task.orphaned_at) return false
      return new Date(task.orphaned_at) > oneHourAgo
    })
  })

  const recentOrphanedTasksCount = computed(() => recentOrphanedTasks.value.length)

  const orphanedTasksByHostname = computed(() => {
    const map = new Map<string, TaskEventResponse[]>()
    orphanedTasks.value.forEach(task => {
      const hostname = task.hostname || 'unknown'
      if (!map.has(hostname)) {
        map.set(hostname, [])
      }
      map.get(hostname)!.push(task)
    })
    return map
  })

  async function fetchOrphanedTasks() {
    try {
      isLoading.value = true
      error.value = null
      orphanedTasks.value = await apiService.getOrphanedTasks()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch orphaned tasks'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function retryOrphanedTask(taskId: string) {
    try {
      error.value = null
      await apiService.retryTask(taskId)
      orphanedTasks.value = orphanedTasks.value.filter(task => task.task_id !== taskId)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to retry orphaned task'
      throw err
    }
  }

  function updateOrphanedTasks(newTasks: TaskEventResponse[]) {
    orphanedTasks.value = newTasks
  }

  function addOrphanedTask(task: TaskEventResponse) {
    if (!orphanedTasks.value.find(t => t.task_id === task.task_id)) {
      orphanedTasks.value.push(task)
    }
  }

  function applyResolutionState(taskId: string, resolved: boolean, resolved_by?: string | null, resolved_at?: string | null) {
    const normalizedResolvedAt = resolved_at ? new Date(resolved_at).toISOString() : null
    orphanedTasks.value = orphanedTasks.value.map(task => {
      if (task.task_id !== taskId) return task
      return {
        ...task,
        resolved,
        resolved_by: resolved_by ?? null,
        resolved_at: normalizedResolvedAt,
      } as TaskEventResponse & { resolved?: boolean; resolved_by?: string | null; resolved_at?: string | null }
    })
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
      error.value = err instanceof Error ? err.message : 'Failed to resolve orphaned task'
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

  function removeOrphanedTask(taskId: string) {
    orphanedTasks.value = orphanedTasks.value.filter(task => task.task_id !== taskId)
  }

  function updateFromLiveEvent(event: any) {
    const environmentStore = useEnvironmentStore()
    const { matchesEnvironment } = useEnvironmentMatcher()

    if (!matchesEnvironment(event as TaskEventResponse, environmentStore.activeEnvironment)) {
      return
    }

    if (event.event_type === 'task-orphaned' && event.task_id) {
      addOrphanedTask(event as TaskEventResponse)
    } else if (event.event_type === 'task-succeeded' || event.event_type === 'task-failed') {
      removeOrphanedTask(event.task_id)
    }
  }

  return {
    orphanedTasks: readonly(orphanedTasks),
    isLoading: readonly(isLoading),
    error: readonly(error),

    orphanedTasksCount,
    recentOrphanedTasks,
    recentOrphanedTasksCount,
    orphanedTasksByHostname,

    fetchOrphanedTasks,
    retryOrphanedTask,
    updateOrphanedTasks,
    addOrphanedTask,
    removeOrphanedTask,
    updateFromLiveEvent,
    applyResolutionState,
    resolveTask,
    clearTaskResolution,
  }
})
