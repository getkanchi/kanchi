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
      <div class="mb-6 flex flex-col gap-4 failure-insights-section">
        <TaskIssueSummary
          :tasks="failedTasksStore.failedTasks"
          :is-loading="failedTasksStore.isLoading"
          :status="failedCardStatus"
          :summary-variant="failedSummaryVariant"
          :hide-when-empty="true"
          title="Failed tasks (24h)"
          primary-label="unresolved"
          secondary-label="last hour"
          recent-field="timestamp"
          :recent-window-minutes="60"
          latest-label="Last failure"
          time-field="timestamp"
          badge-label="Failed"
          badge-variant="destructive"
          :show-retry-badge="true"
          :show-exception="true"
          empty-state-title="No failed tasks detected in the last 24 hours"
          empty-state-description="New failures will appear here instantly."
          :item-action-loading-ids="retryLoadingIds"
          @item-action="handleFailedRetryAction"
        >
          <template #actions="{ task }">

            <NuxtLink :to="`/tasks/${task.task_id}`">
              <Button
                variant="ghost"
                size="sm"
                class="gap-1.5"
              >
                <ChevronRight class="h-3.5 w-3.5" />
                Open
              </Button>
            </NuxtLink>
            <IconButton :icon="RefreshCw"
              size="xs"
              variant="ghost"
              :disabled="retryLoadingIds.includes(task.task_id)"
              @click.stop="handleFailedRetryAction(task)"
            />
          </template>
        </TaskIssueSummary>

        <TaskIssueSummary
          :tasks="uniqueOrphanedTasks"
          :is-loading="orphanTasksStore.isLoading"
          :status="orphanCardStatus"
          :summary-variant="orphanSummaryVariant"
          :hide-when-empty="true"
          title="Orphaned tasks"
          primary-label="detected"
          secondary-label="recent"
          recent-field="orphaned_at"
          :recent-window-minutes="60"
          latest-label="Last orphan detected"
          time-field="orphaned_at"
          badge-label="Orphaned"
          badge-variant="orphaned"
          empty-state-title="No orphaned tasks detected"
          empty-state-description="Tasks are marked as orphaned when their workers go offline."
          :item-action-loading-ids="retryLoadingIds"
          @item-action="handleOrphanRetryAction"
        >
          <template #actions="{ task }">
            <Button
              variant="ghost"
              size="xs"
              class="gap-1 border border-border/70 text-text-secondary hover:border-border-highlight hover:text-text-primary"
              :disabled="retryLoadingIds.includes(task.task_id)"
              @click.stop="handleOrphanRetryAction(task)"
            >
              <RefreshCw
                v-if="retryLoadingIds.includes(task.task_id)"
                class="h-3.5 w-3.5 animate-spin"
              />
              <RefreshCw v-else class="h-3.5 w-3.5" />
              Retry
            </Button>
          </template>
          <template #details="{ task }">
            <div class="mt-3 flex flex-wrap items-center gap-2 text-xs text-text-secondary">
              <Badge
                variant="outline"
                class="gap-2 border-border text-text-secondary"
              >
                <span class="uppercase tracking-wide text-[9px] text-text-muted">Detected</span>
                <TimeDisplay
                  :timestamp="task.orphaned_at || task.timestamp"
                  layout="inline"
                  :auto-refresh="true"
                  :refresh-interval="60000"
                />
              </Badge>
              <span class="text-text-muted">
                Waiting for worker "{{ task.hostname || 'unknown' }}" to acknowledge this task.
              </span>
            </div>
          </template>
        </TaskIssueSummary>
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

      <RetryTaskConfirmDialog
        ref="retryDialogRef"
        :task="retryDialogTask"
        :is-loading="isRetryingTask"
        @confirm="confirmRetry"
        @cancel="cancelRetry"
      />
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { getTaskColumns } from "~/config/tableColumns"
import DataTable from "~/components/data-table.vue"
import WorkerStatusSummary from "~/components/WorkerStatusSummary.vue"
import CommandPalette from "~/components/CommandPalette.vue"
import TaskIssueSummary from "~/components/TaskIssueSummary.vue"
import RetryTaskConfirmDialog from "~/components/RetryTaskConfirmDialog.vue"
import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import TimeDisplay from '~/components/TimeDisplay.vue'
import { useFilterParser } from '~/composables/useFilterParser'
import type { ParsedFilter } from '~/composables/useFilterParser'
import type { TimeRange } from '~/components/TimeRangeFilter.vue'
import { useUrlQuerySync } from '~/composables/useUrlQuerySync'
import type { UrlQueryState } from '~/composables/useUrlQuerySync'
import type { TaskEventResponse } from '~/services/apiClient'
import {ChevronRight, RefreshCw} from 'lucide-vue-next'
import {IconButton} from "~/components/common";

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

const uniqueOrphanedTasks = computed<TaskEventResponse[]>(() => {
  const taskMap = new Map<string, TaskEventResponse>()

  const parseTime = (value?: string | null) => {
    if (!value) return 0
    const parsed = Date.parse(value)
    return Number.isNaN(parsed) ? 0 : parsed
  }

  const sorted = [...orphanTasksStore.orphanedTasks].sort((a, b) => {
    const aTime = parseTime(a.orphaned_at || a.timestamp)
    const bTime = parseTime(b.orphaned_at || b.timestamp)
    return bTime - aTime
  })

  sorted.forEach(task => {
    if (!task.task_id) return
    if (taskMap.has(task.task_id)) return
    const hasRetries = task.retried_by && task.retried_by.length > 0
    if (task.is_orphan && !hasRetries) {
      taskMap.set(task.task_id, task)
    }
  })

  return Array.from(taskMap.values())
})

const failedCardStatus = computed(() => failedTasksStore.failedTasks.length > 0 ? 'error' : 'success')
const failedSummaryVariant = computed(() => failedTasksStore.failedTasks.length > 0 ? 'error' : 'success')
const orphanCardStatus = computed(() => uniqueOrphanedTasks.value.length > 0 ? 'warning' : 'success')
const orphanSummaryVariant = computed(() => uniqueOrphanedTasks.value.length > 0 ? 'warning' : 'success')

const retryDialogRef = ref<InstanceType<typeof RetryTaskConfirmDialog> | null>(null)
const retryDialogState = ref<{ task: TaskEventResponse; type: 'failed' | 'orphan' } | null>(null)
const isRetryingTask = ref(false)

const retryDialogTask = computed(() => retryDialogState.value?.task ?? null)

const retryLoadingIds = computed(() => {
  if (!retryDialogState.value || !isRetryingTask.value) {
    return []
  }
  return [retryDialogState.value.task.task_id]
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

function openRetryDialog(task: TaskEventResponse, type: 'failed' | 'orphan') {
  retryDialogState.value = { task, type }
  retryDialogRef.value?.open()
}

function handleFailedRetryAction(task: TaskEventResponse) {
  openRetryDialog(task, 'failed')
}

function handleOrphanRetryAction(task: TaskEventResponse) {
  openRetryDialog(task, 'orphan')
}

async function confirmRetry() {
  if (!retryDialogState.value) return
  isRetryingTask.value = true
  const { task, type } = retryDialogState.value
  try {
    if (type === 'orphan') {
      await orphanTasksStore.retryOrphanedTask(task.task_id)
    } else {
      await tasksStore.retryTask(task.task_id)
    }
    retryDialogState.value = null
  } catch (error) {
    console.error('Failed to retry task:', error)
  } finally {
    isRetryingTask.value = false
  }
}

function cancelRetry() {
  retryDialogState.value = null
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

// Store interval IDs at component scope
let orphanTasksInterval: ReturnType<typeof setInterval> | null = null
let failedTasksInterval: ReturnType<typeof setInterval> | null = null
let workerInterval: ReturnType<typeof setInterval> | null = null

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

  orphanTasksInterval = setInterval(() => {
    orphanTasksStore.fetchOrphanedTasks().catch(() => {})
  }, 60000) // Poll every 60 seconds for orphaned tasks

  failedTasksInterval = setInterval(() => {
    failedTasksStore.fetchFailedTasks().catch(() => {})
  }, 60000) // Poll every 60 seconds for failed tasks

  workerInterval = setInterval(() => {
    // Only fetch if WebSocket is not connected
    if (!wsStore.isConnected) {
      workersStore.fetchWorkers()
    }
  }, 30000)
})

onUnmounted(() => {
  // Clean up intervals
  if (orphanTasksInterval) clearInterval(orphanTasksInterval)
  if (failedTasksInterval) clearInterval(failedTasksInterval)
  if (workerInterval) clearInterval(workerInterval)

  // Clean up event listeners
  document.removeEventListener('mousemove', handleMouseMove)
})
</script>
