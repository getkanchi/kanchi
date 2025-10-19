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
  }
})