import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useApiService } from '~/services/apiClient'
import type {
  TaskRegistryResponse,
  TaskRegistryUpdate,
  TaskRegistryStats,
  TaskDailyStatsResponse,
  TaskTimelineResponse,
  TaskTrendSummary
} from '~/services/apiClient'

export const useTaskRegistryStore = defineStore('taskRegistry', () => {
  const tasks = ref<TaskRegistryResponse[]>([])
  const selectedTask = ref<TaskRegistryResponse | null>(null)
  const taskStats = ref<TaskRegistryStats | null>(null)
  const taskTimeline = ref<TaskTimelineResponse | null>(null)
  const dailyStats = ref<TaskDailyStatsResponse[]>([])
  const trend = ref<TaskTrendSummary | null>(null)
  const tags = ref<string[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const apiClient = useApiService()

  async function fetchTasks(tag?: string, name?: string) {
    isLoading.value = true
    error.value = null
    try {
      tasks.value = await apiClient.getRegistryTasks({ tag, name })
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch tasks'
      console.error('Error fetching tasks:', err)
    } finally {
      isLoading.value = false
    }
  }

  async function fetchTaskDetails(taskName: string) {
    isLoading.value = true
    error.value = null
    try {
      const data = await apiClient.getRegistryTask(taskName)
      selectedTask.value = data
      return data
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch task details'
      console.error('Error fetching task details:', err)
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function fetchTaskStats(taskName: string, hours: number = 24) {
    try {
      const data = await apiClient.getRegistryTaskStats(taskName, hours)
      taskStats.value = data
      return data
    } catch (err: any) {
      console.error('Error fetching task stats:', err)
      return null
    }
  }

  async function fetchTaskTimeline(taskName: string, hours: number = 24, bucketSizeMinutes: number = 60) {
    try {
      const data = await apiClient.getRegistryTaskTimeline(taskName, hours, bucketSizeMinutes)
      taskTimeline.value = data
      return data
    } catch (err: any) {
      console.error('Error fetching task timeline:', err)
      return null
    }
  }

  async function fetchDailyStats(taskName: string, days: number = 30) {
    try {
      const data = await apiClient.getRegistryTaskDailyStats(taskName, { days })
      dailyStats.value = data
      return data
    } catch (err: any) {
      console.error('Error fetching daily stats:', err)
      return null
    }
  }

  async function fetchTrend(taskName: string, days: number = 7) {
    try {
      const data = await apiClient.getRegistryTaskTrend(taskName, days)
      trend.value = data
      return data
    } catch (err: any) {
      console.error('Error fetching trend:', err)
      return null
    }
  }

  async function fetchAllTags() {
    try {
      const data = await apiClient.getRegistryTags()
      tags.value = data
      return data
    } catch (err: any) {
      console.error('Error fetching tags:', err)
      return []
    }
  }

  async function updateTask(taskName: string, update: TaskRegistryUpdate) {
    try {
      const data = await apiClient.updateRegistryTask(taskName, update)
      const index = tasks.value.findIndex(t => t.name === taskName)
      if (index !== -1) {
        tasks.value[index] = data
      }
      if (selectedTask.value?.name === taskName) {
        selectedTask.value = data
      }
      return data
    } catch (err: any) {
      error.value = err.message || 'Failed to update task'
      console.error('Error updating task:', err)
      return null
    }
  }

  function setSelectedTask(task: TaskRegistryResponse | null) {
    selectedTask.value = task
  }

  function clearError() {
    error.value = null
  }

  return {
    tasks,
    selectedTask,
    taskStats,
    taskTimeline,
    dailyStats,
    trend,
    tags,
    isLoading,
    error,
    fetchTasks,
    fetchTaskDetails,
    fetchTaskStats,
    fetchTaskTimeline,
    fetchDailyStats,
    fetchTrend,
    fetchAllTags,
    updateTask,
    setSelectedTask,
    clearError
  }
})
