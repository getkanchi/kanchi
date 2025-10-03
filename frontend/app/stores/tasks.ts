/**
 * Pinia store for task management
 * Live mode: Real-time updates via WebSocket
 * Static mode: Manual refresh with server-side pagination
 */
import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'
import { useApiService } from '../services/apiClient'
import type { TaskStats, TaskEventResponse } from '../services/apiClient'

export interface TaskFilters {
  search?: string | null
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

  // State - Single source of truth
  const stats = ref<TaskStats | null>(null)
  const events = ref<TaskEventResponse[]>([])  // Current page data
  const activeTasks = ref<TaskEventResponse[]>([])
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
  
  // Live mode specific state
  const lastRefreshTime = ref<Date | null>(null)

  // Current filter and pagination state
  const filters = ref<TaskFilters>({})
  const paginationParams = ref<PaginationParams>({
    page: 0,
    limit: 10,
    sort_order: 'desc'
  })

  // Computed - Simplified pagination
  const hasNextPage = computed(() => pagination.value.has_next)
  const hasPrevPage = computed(() => pagination.value.has_prev)
  const totalPages = computed(() => pagination.value.total_pages)
  const currentPage = computed(() => pagination.value.page)
  
  // Single computed property for paginated events
  const paginatedEvents = computed(() => events.value)

  // Actions
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
      
      const response = await apiService.getRecentEvents({
        ...paginationParams.value,
        ...filters.value,
        aggregate: true
      })

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
      // Refresh events after retry
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

  // Pagination actions
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

  // Filter actions
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

  // Live mode management
  function setLiveMode(enabled: boolean) {
    isLiveMode.value = enabled
    
    if (enabled) {
      // In live mode, we'll receive updates via WebSocket
      // Reset to first page to see newest events
      if (paginationParams.value.page !== 0) {
        paginationParams.value.page = 0
        fetchRecentEvents()
      }
    }
  }

  // Handle live events from WebSocket - SIMPLE SOLUTION
  function handleLiveEvent(event: TaskEventResponse) {
    if (!isLiveMode.value) return
    
    // Find if we have any event for this task_id
    const existingTaskIndex = events.value.findIndex(e => e.task_id === event.task_id)
    
    if (existingTaskIndex !== -1) {
      // Create a completely new array with the updated task
      // This guarantees Vue detects the change
      const newEvents = [...events.value]
      newEvents[existingTaskIndex] = event
      events.value = newEvents
    } else if (paginationParams.value.page === 0) {
      // Add new task at the beginning
      // Create completely new array to ensure reactivity
      const newEvents = [event, ...events.value.slice(0, paginationParams.value.limit - 1)]
      events.value = newEvents
      
      // Update pagination total
      pagination.value = {
        ...pagination.value,
        total: (pagination.value.total || 0) + 1,
        total_pages: Math.ceil(((pagination.value.total || 0) + 1) / paginationParams.value.limit)
      }
    }
    
    lastRefreshTime.value = new Date()
  }

  return {
    // State
    stats: readonly(stats),
    events: readonly(events),
    activeTasks: readonly(activeTasks),
    pagination: readonly(pagination),
    isLoading: readonly(isLoading),
    error: readonly(error),
    filters: readonly(filters),
    paginationParams: readonly(paginationParams),
    isLiveMode: readonly(isLiveMode),
    lastRefreshTime: readonly(lastRefreshTime),

    // Computed
    hasNextPage,
    hasPrevPage,
    totalPages,
    currentPage,
    paginatedEvents,

    // Actions
    fetchStats,
    fetchRecentEvents,
    fetchActiveTasks,
    retryTask,
    getTaskEvents,
    setPage,
    setPageSize,
    nextPage,
    prevPage,
    setFilters,
    setSorting,
    setSearchQuery,
    setLiveMode,
    handleLiveEvent,
  }
})