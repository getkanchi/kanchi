/**
 * Pinia store for orphan task management
 */
import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'
import { useApiService } from '../services/apiClient'
import type { TaskEventResponse } from '../services/apiClient'

export const useOrphanTasksStore = defineStore('orphanTasks', () => {
  const apiService = useApiService()

  // State
  const orphanedTasks = ref<TaskEventResponse[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Computed
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

  // Actions
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
      // Remove the task from orphaned list after successful retry
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
    // Check if task is already in the list
    if (!orphanedTasks.value.find(t => t.task_id === task.task_id)) {
      orphanedTasks.value.push(task)
    }
  }

  function removeOrphanedTask(taskId: string) {
    orphanedTasks.value = orphanedTasks.value.filter(task => task.task_id !== taskId)
  }

  // Update orphaned tasks from live WebSocket event
  function updateFromLiveEvent(event: any) {
    if (event.event_type === 'task-orphaned' && event.task_id) {
      addOrphanedTask(event as TaskEventResponse)
    } else if (event.event_type === 'task-succeeded' || event.event_type === 'task-failed') {
      // Remove from orphaned list if task completes
      removeOrphanedTask(event.task_id)
    }
  }

  return {
    // State
    orphanedTasks: readonly(orphanedTasks),
    isLoading: readonly(isLoading),
    error: readonly(error),

    // Computed
    orphanedTasksCount,
    recentOrphanedTasks,
    recentOrphanedTasksCount,
    orphanedTasksByHostname,

    // Actions
    fetchOrphanedTasks,
    retryOrphanedTask,
    updateOrphanedTasks,
    addOrphanedTask,
    removeOrphanedTask,
    updateFromLiveEvent,
  }
})