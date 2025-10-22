<template>
      <!-- Command Palette -->
      <CommandPalette 
        :is-live-mode="tasksStore.isLiveMode"
        @toggle-live-mode="handleToggleLiveMode"
        @rerun-task="handleRerunTask"
      />

      <!-- Workers Overview -->
      <div class="mb-6 workers-section">
        <WorkerStatusSummary
          :workers="workersStore.workers"
          @update="workersStore.updateWorker"
        />
      </div>

      <!-- Failure & Orphaned Tasks Overview -->
      <div class="mb-6 grid gap-4 xl:grid-cols-2 failure-insights-section">
        <FailedTasksSummary
          :failed-tasks="failedTasksStore.failedTasks"
          :is-loading="failedTasksStore.isLoading"
        />
        <OrphanTasksSummary
          :orphaned-tasks="orphanTasksStore.orphanedTasks"
          :is-loading="orphanTasksStore.isLoading"
          @retry-task="handleRerunTask"
        />
      </div>

      <div class="mb-6">
        <DataTable
          :columns="columns"
          :data="tasksStore.paginatedEvents"
          :is-live-mode="tasksStore.isLiveMode"
          :seconds-since-update="secondsSinceUpdate"
          :page-index="tasksStore.currentPage"
          :page-size="tasksStore.paginationParams.limit"
          :pagination="tasksStore.pagination"
          :is-loading="tasksStore.isLoading"
          :sorting="currentSorting"
          :search-query="tasksStore.filters.search || ''"
          :filters="currentFilters"
          :time-range="timeRange"
          class="relative backdrop-blur-sm bg-background-surface border-border glow-border"
          @toggle-live-mode="handleToggleLiveMode"
          @set-page-index="tasksStore.setPage"
          @set-page-size="tasksStore.setPageSize"
          @set-sorting="handleSetSorting"
          @set-search-query="tasksStore.setSearchQuery"
          @set-filters="handleSetFilters"
          @set-time-range="handleSetTimeRange"
          @clear-time-range="handleClearTimeRange"
        />
      </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { getTaskColumns } from "~/config/tableColumns"
import DataTable from "~/components/data-table.vue"
import WorkerStatusSummary from "~/components/WorkerStatusSummary.vue"
import OrphanTasksSummary from "~/components/OrphanTasksSummary.vue"
import CommandPalette from "~/components/CommandPalette.vue"
import FailedTasksSummary from "~/components/FailedTasksSummary.vue"
import type { ParsedFilter } from '~/composables/useFilterParser'
import type { TimeRange } from '~/components/TimeRangeFilter.vue'
import type { UrlQueryState } from '~/composables/useUrlQuerySync'

const tasksStore = useTasksStore()
const workersStore = useWorkersStore()
const orphanTasksStore = useOrphanTasksStore()
const failedTasksStore = useFailedTasksStore()
const wsStore = useWebSocketStore()
const environmentStore = useEnvironmentStore()

// Time range state
const timeRange = ref<TimeRange>({ start: null, end: null })

const { queryStringToFilters, filtersToQueryString } = useFilterParser()

// URL query sync
const urlQuerySync = useUrlQuerySync()

// Track if we're initializing from URL to avoid duplicate fetches
const isInitializing = ref(true)

const secondsSinceUpdate = computed(() => {
  if (!tasksStore.lastRefreshTime) return 0
  return Math.floor((Date.now() - tasksStore.lastRefreshTime.getTime()) / 1000)
})

const currentSorting = computed(() => {
  const { sort_by, sort_order } = tasksStore.paginationParams
  if (!sort_by) return []
  return [{ id: sort_by, desc: sort_order === 'desc' }]
})

const currentFilters = computed((): ParsedFilter[] => {
  const filters = tasksStore.filters

  if (filters.filters) {
    return queryStringToFilters(filters.filters)
  }

  // Otherwise return empty array (legacy filters handled by backend)
  return []
})

// Table columns
const columns = getTaskColumns()

function handleToggleLiveMode() {
  const newMode = !tasksStore.isLiveMode
  wsStore.setMode(newMode ? 'live' : 'static')
  tasksStore.setLiveMode(newMode)
  
  if (newMode) {
    // Reset to first page for live mode to see newest events
    tasksStore.setPage(0)
  } else {
    tasksStore.fetchRecentEvents()
  }
}

function handleSetSorting(sorting: { id: string; desc: boolean }[]) {
  if (sorting.length > 0) {
    const sort = sorting[0]
    if (sort) {
      tasksStore.setSorting(sort.id, sort.desc ? 'desc' : 'asc')
    }
  } else {
    tasksStore.setSorting(null)
  }
}

function handleSetFilters(filters: ParsedFilter[]) {
  // Convert ParsedFilter[] to query string format
  const filterQueryString = filtersToQueryString(filters)

  tasksStore.setFilters({
    filters: filterQueryString || null
  })
}

function handleSetTimeRange(range: TimeRange) {
  timeRange.value = range
  const startTime = range.start ? range.start.toISOString() : null
  const endTime = range.end ? range.end.toISOString() : null
  tasksStore.setTimeRange(startTime, endTime)
}

function handleClearTimeRange() {
  timeRange.value = { start: null, end: null }
  tasksStore.setTimeRange(null, null)
}

async function handleRerunTask(taskId: string) {
  try {
    await tasksStore.retryTask(taskId)
    // Task list will be refreshed automatically by the store
  } catch (error) {
    console.error('Failed to retry task:', error)
    // You might want to show a toast notification here
  }
}

// Mouse glow effect
const handleMouseMove = (e: MouseEvent) => {
  const glowElements = document.querySelectorAll('.glow-border')
  glowElements.forEach(element => {
    const rect = element.getBoundingClientRect()
    
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    
    ;(element as HTMLElement).style.setProperty('--mouse-x', `${x}px`)
    ;(element as HTMLElement).style.setProperty('--mouse-y', `${y}px`)
  })
}

const getCurrentState = computed((): UrlQueryState => ({
  search: tasksStore.filters.search || null,
  filters: tasksStore.filters.filters || null,
  sortBy: tasksStore.paginationParams.sort_by || null,
  sortOrder: tasksStore.paginationParams.sort_order === 'desc' ? 'desc' : 'asc',
  page: tasksStore.paginationParams.page > 0 ? tasksStore.paginationParams.page : undefined,
  pageSize: tasksStore.paginationParams.limit,
  startTime: tasksStore.filters.start_time || null,
  endTime: tasksStore.filters.end_time || null,
  environment: environmentStore.activeEnvironment?.id || null
}))

// Apply state from URL
function applyStateFromUrl(state: UrlQueryState) {
  // Apply environment first if specified
  if (state.environment && state.environment !== environmentStore.activeEnvironment?.id) {
    environmentStore.activateEnvironment(state.environment)
  }

  // Apply filters
  if (state.filters) {
    tasksStore.setFilters({ filters: state.filters })
  }

  // Apply search
  if (state.search) {
    tasksStore.setSearchQuery(state.search)
  }

  // Apply sorting
  if (state.sortBy) {
    tasksStore.setSorting(state.sortBy, state.sortOrder || 'desc')
  }

  // Apply pagination
  if (state.pageSize) {
    tasksStore.setPageSize(state.pageSize)
  }
  if (state.page !== undefined) {
    tasksStore.setPage(state.page)
  }

  // Apply time range
  if (state.startTime || state.endTime) {
    const start = state.startTime ? new Date(state.startTime) : null
    const end = state.endTime ? new Date(state.endTime) : null
    timeRange.value = { start, end }
    tasksStore.setTimeRange(state.startTime, state.endTime)
  }
}

urlQuerySync.initializeFromUrl((state) => {
  applyStateFromUrl(state)
})

// Watch state changes and sync to URL (debounced to avoid excessive updates)
let syncTimeout: ReturnType<typeof setTimeout> | null = null
watch(getCurrentState, (newState) => {
  if (isInitializing.value) return

  if (syncTimeout) clearTimeout(syncTimeout)
  syncTimeout = setTimeout(() => {
    urlQuerySync.updateQueryParams(newState, true)
  }, 300)
}, { deep: true })

// Watch for environment changes and refresh data
watch(() => environmentStore.activeEnvironment, async () => {
  console.log('[Dashboard] Environment changed, refreshing data...')
  await Promise.all([
    tasksStore.fetchRecentEvents(),
    tasksStore.fetchStats(),
    workersStore.fetchWorkers(),
    orphanTasksStore.fetchOrphanedTasks(),
    failedTasksStore.fetchFailedTasks()
  ])
})

// Lifecycle
onMounted(async () => {
  document.addEventListener('mousemove', handleMouseMove)

  // Initial data fetch
  await Promise.all([
    tasksStore.fetchRecentEvents(),
    tasksStore.fetchStats(),
    workersStore.fetchWorkers(),
    orphanTasksStore.fetchOrphanedTasks(),
    failedTasksStore.fetchFailedTasks()
  ])

  tasksStore.setLiveMode(wsStore.clientMode === 'live')

  // Mark initialization as complete
  isInitializing.value = false

  const orphanTasksInterval = setInterval(() => {
    orphanTasksStore.fetchOrphanedTasks().catch(() => {})
  }, 60000) // Poll every 60 seconds for orphaned tasks

  const failedTasksInterval = setInterval(() => {
    failedTasksStore.fetchFailedTasks().catch(() => {})
  }, 60000) // Poll every 60 seconds for failed tasks

  const workerInterval = setInterval(() => {
    // Only fetch if WebSocket is not connected
    if (!wsStore.isConnected) {
      workersStore.fetchWorkers()
    }
  }, 30000)

  onUnmounted(() => {
    clearInterval(orphanTasksInterval)
    clearInterval(failedTasksInterval)
    clearInterval(workerInterval)
  })
})

onUnmounted(() => {
  document.removeEventListener('mousemove', handleMouseMove)
})
</script>
