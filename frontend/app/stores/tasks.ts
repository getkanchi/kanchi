import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'
import { useApiService } from '../services/apiClient'
import type {
  TaskStats,
  TaskEventResponse,
  TaskProgressSnapshotResponse,
  TaskProgressEventResponse,
  TaskStepsEventResponse,
} from '../services/apiClient'

export interface TaskFilters {
  search?: string | null
  filters?: string | null
  start_time?: string | null
  end_time?: string | null
  filter_state?: string | null
  filter_worker?: string | null
  filter_task?: string | null
  filter_queue?: string | null
}

export interface PaginationParams {
  page: number
  limit: number
  sort_by?: string | null
  sort_order: string
}

export interface PaginationInfo {
  page: number
  limit: number
  total: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}

export const useTasksStore = defineStore('tasks', () => {
  const apiService = useApiService()

  const stats = ref<TaskStats | null>(null)
  const events = ref<TaskEventResponse[]>([])
  const activeTasks = ref<TaskEventResponse[]>([])
  const progressSnapshots = ref<Record<string, TaskProgressSnapshotResponse>>({})
  const pagination = ref<PaginationInfo>({
    page: 0,
    limit: 10,
    total: 0,
    total_pages: 0,
    has_next: false,
    has_prev: false
  })

  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const isLiveMode = ref(false)

  const lastRefreshTime = ref<Date | null>(null)

  const filters = ref<TaskFilters>({})
  const paginationParams = ref<PaginationParams>({
    page: 0,
    limit: 10,
    sort_order: 'desc'
  })

  const hasNextPage = computed(() => pagination.value.has_next)
  const hasPrevPage = computed(() => pagination.value.has_prev)
  const totalPages = computed(() => pagination.value.total_pages)
  const currentPage = computed(() => pagination.value.page)

  const paginatedEvents = computed(() => events.value)

  async function fetchStats() {
    try {
      isLoading.value = true
      error.value = null
      stats.value = await apiService.getTaskStats()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch stats'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchRecentEvents(silent = false) {
    try {
      if (!silent) {
        isLoading.value = true
      }
      error.value = null

      const params = {
        ...paginationParams.value,
        ...filters.value,
        aggregate: true
      }

      const response = await apiService.getRecentEvents(params)

      const data = response as any
      if (data.data && Array.isArray(data.data)) {
        events.value = data.data
      }
      if (data.pagination) {
        pagination.value = data.pagination
      }
      
      lastRefreshTime.value = new Date()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch recent events'
      if (!silent) throw err
    } finally {
      if (!silent) {
        isLoading.value = false
      }
    }
  }

  async function fetchActiveTasks() {
    try {
      isLoading.value = true
      error.value = null
      activeTasks.value = await apiService.getActiveTasks()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch active tasks'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function retryTask(taskId: string) {
    try {
      error.value = null
      const result = await apiService.retryTask(taskId)
      await fetchRecentEvents()
      return result
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to retry task'
      throw err
    }
  }

  async function getTaskEvents(taskId: string): Promise<TaskEventResponse[]> {
    try {
      error.value = null
      return await apiService.getTaskEvents(taskId)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch task events'
      throw err
    }
  }

  async function getTaskProgress(taskId: string): Promise<TaskProgressSnapshotResponse> {
    try {
      error.value = null
      const snapshot = await apiService.getTaskProgress(taskId)
      progressSnapshots.value = {
        ...progressSnapshots.value,
        [taskId]: snapshot,
      }
      return snapshot
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch task progress'
      throw err
    }
  }

  function getProgressSnapshot(taskId: string): TaskProgressSnapshotResponse | undefined {
    return progressSnapshots.value[taskId]
  }

  function setPage(page: number) {
    const maxPage = Math.max(0, (pagination.value.total_pages || 1) - 1)
    const validPage = Math.max(0, Math.min(page, maxPage))
    
    paginationParams.value.page = validPage
    fetchRecentEvents()
  }

  function setPageSize(limit: number) {
    paginationParams.value.limit = limit
    paginationParams.value.page = 0
    fetchRecentEvents()
  }

  function nextPage() {
    if (hasNextPage.value) {
      setPage(paginationParams.value.page + 1)
    }
  }

  function prevPage() {
    if (hasPrevPage.value) {
      setPage(paginationParams.value.page - 1)
    }
  }

  function setFilters(newFilters: TaskFilters) {
    filters.value = { ...newFilters }
    paginationParams.value.page = 0
    fetchRecentEvents()
  }

  function setSorting(sortBy: string | null, sortOrder: 'asc' | 'desc' = 'desc') {
    paginationParams.value.sort_by = sortBy
    paginationParams.value.sort_order = sortOrder
    paginationParams.value.page = 0
    fetchRecentEvents()
  }

  function setSearchQuery(search: string) {
    filters.value.search = search || null
    paginationParams.value.page = 0
    fetchRecentEvents()
  }

  function setTimeRange(startTime: string | null, endTime: string | null) {
    filters.value.start_time = startTime
    filters.value.end_time = endTime
    paginationParams.value.page = 0
    fetchRecentEvents()
  }

  function setLiveMode(enabled: boolean) {
    isLiveMode.value = enabled

    if (enabled) {
      if (paginationParams.value.page !== 0) {
        paginationParams.value.page = 0
        fetchRecentEvents()
      }
    }
  }

  function handleLiveEvent(event: TaskEventResponse) {
    if (!isLiveMode.value) return

    const environmentStore = useEnvironmentStore()
    const { matchesEnvironment } = useEnvironmentMatcher()

    if (!matchesEnvironment(event, environmentStore.activeEnvironment)) {
      return
    }

    const { matchesFilters } = useEventMatcher()
    const { queryStringToFilters } = useFilterParser()

    const parsedFilters = filters.value.filters
      ? queryStringToFilters(filters.value.filters)
      : []

    if (!matchesFilters(
      event,
      parsedFilters,
      filters.value.search || undefined,
      { start: filters.value.start_time, end: filters.value.end_time }
    )) {
      return
    }

    const existingTaskIndex = events.value.findIndex(e => e.task_id === event.task_id)

    if (existingTaskIndex !== -1) {
      const newEvents = [...events.value]
      newEvents[existingTaskIndex] = event
      events.value = newEvents
    } else if (paginationParams.value.page === 0) {
      const newEvents = [event, ...events.value.slice(0, paginationParams.value.limit - 1)]
      events.value = newEvents

      pagination.value = {
        ...pagination.value,
        total: (pagination.value.total || 0) + 1,
        total_pages: Math.ceil(((pagination.value.total || 0) + 1) / paginationParams.value.limit)
      }
    }

    lastRefreshTime.value = new Date()
  }

  function handleProgressLiveEvent(event: TaskProgressEventResponse | TaskStepsEventResponse) {
    const taskId = (event as any)?.task_id
    if (!taskId) return

    const existing = progressSnapshots.value[taskId] || {
      task_id: taskId,
      steps: [],
      history: [],
      latest: null,
    }

    if ((event as TaskProgressEventResponse).event_type === 'kanchi-task-progress') {
      const progressEvent = event as TaskProgressEventResponse
      const latestTs = existing.latest ? new Date(existing.latest.timestamp).getTime() : -1
      const incomingTs = new Date(progressEvent.timestamp).getTime()
      const history = [progressEvent, ...(existing.history || [])].slice(0, 50)

      const updated = {
        ...existing,
        latest: incomingTs >= latestTs ? progressEvent : existing.latest,
        history,
      }

      progressSnapshots.value = {
        ...progressSnapshots.value,
        [taskId]: updated,
      }
    }

    if ((event as TaskStepsEventResponse).event_type === 'kanchi-task-steps') {
      const stepsEvent = event as TaskStepsEventResponse
      const updated = {
        ...existing,
        steps: stepsEvent.steps || [],
      }
      progressSnapshots.value = {
        ...progressSnapshots.value,
        [taskId]: updated,
      }
    }
  }

  return {
    stats: readonly(stats),
    events: readonly(events),
    activeTasks: readonly(activeTasks),
    progressSnapshots: readonly(progressSnapshots),
    pagination: readonly(pagination),
    isLoading: readonly(isLoading),
    error: readonly(error),
    filters: readonly(filters),
    paginationParams: readonly(paginationParams),
    isLiveMode: readonly(isLiveMode),
    lastRefreshTime: readonly(lastRefreshTime),

    hasNextPage,
    hasPrevPage,
    totalPages,
    currentPage,
    paginatedEvents,

    fetchStats,
    fetchRecentEvents,
    fetchActiveTasks,
    retryTask,
    getTaskEvents,
    getTaskProgress,
    getProgressSnapshot,
    setPage,
    setPageSize,
    nextPage,
    prevPage,
    setFilters,
    setSorting,
    setSearchQuery,
    setTimeRange,
    setLiveMode,
    handleLiveEvent,
    handleProgressLiveEvent,
  }
})
