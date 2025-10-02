/**
 * Pinia store for task management
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

  // State
  const stats = ref<TaskStats | null>(null)
  const recentEvents = ref<TaskEventResponse[]>([])
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

  // Current filter and pagination state
  const filters = ref<TaskFilters>({})
  const paginationParams = ref<PaginationParams>({
    page: 0,
    limit: 10,
    sort_order: 'desc'
  })

  // Computed
  const hasNextPage = computed(() => pagination.value.has_next)
  const hasPrevPage = computed(() => pagination.value.has_prev)
  const totalPages = computed(() => pagination.value.total_pages)
  const currentPage = computed(() => pagination.value.page)

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

  async function fetchRecentEvents() {
    try {
      isLoading.value = true
      error.value = null
      
      const response = await apiService.getRecentEvents({
        ...paginationParams.value,
        ...filters.value,
        aggregate: true
      })

      // Type assertion since the API returns a complex object structure
      const data = response as any
      if (data.data && Array.isArray(data.data)) {
        recentEvents.value = data.data
      }
      if (data.pagination) {
        pagination.value = data.pagination
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch recent events'
      throw err
    } finally {
      isLoading.value = false
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
    // Ensure page is within valid bounds
    const maxPage = Math.max(0, (pagination.value.total_pages || 1) - 1)
    const validPage = Math.max(0, Math.min(page, maxPage))
    
    paginationParams.value.page = validPage
    fetchRecentEvents()
  }

  function setPageSize(limit: number) {
    paginationParams.value.limit = limit
    paginationParams.value.page = 0 // Reset to first page
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
    paginationParams.value.page = 0 // Reset to first page
    fetchRecentEvents()
  }

  function setSorting(sortBy: string | null, sortOrder: 'asc' | 'desc' = 'desc') {
    paginationParams.value.sort_by = sortBy
    paginationParams.value.sort_order = sortOrder
    paginationParams.value.page = 0 // Reset to first page
    fetchRecentEvents()
  }

  function setSearchQuery(search: string) {
    filters.value.search = search || null
    paginationParams.value.page = 0 // Reset to first page
    fetchRecentEvents()
  }


  function addLiveEvent(event: any) {
    if (paginationParams.value.page === 0) {
      const currentEvents = [...recentEvents.value]
      const existingIndex = currentEvents.findIndex(e => e.task_id === event.task_id)
      
      if (existingIndex !== -1) {
        currentEvents[existingIndex] = event
      } else {
        currentEvents.unshift(event)
      }
      
      recentEvents.value = currentEvents
        .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
        .slice(0, 100)
    }
  }

  return {
    // State
    stats: readonly(stats),
    recentEvents: readonly(recentEvents),
    activeTasks: readonly(activeTasks),
    pagination: readonly(pagination),
    isLoading: readonly(isLoading),
    error: readonly(error),
    filters: readonly(filters),
    paginationParams: readonly(paginationParams),

    // Computed
    hasNextPage,
    hasPrevPage,
    totalPages,
    currentPage,

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
    addLiveEvent,
  }
})