<template>
  <NuxtLayout>
    <div class="p-6">

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

      <!-- Orphaned Tasks Overview -->
      <div class="mb-6 orphan-tasks-section">
        <OrphanTasksSummary
          v-if="orphanTasksStore.orphanedTasks.length > 0"
          :orphaned-tasks="orphanTasksStore.orphanedTasks"
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
          class="relative backdrop-blur-sm bg-background-surface border-border glow-border"
          @toggle-live-mode="handleToggleLiveMode"
          @set-page-index="tasksStore.setPage"
          @set-page-size="tasksStore.setPageSize"
          @set-sorting="handleSetSorting"
          @set-search-query="tasksStore.setSearchQuery"
          @set-filters="handleSetFilters"
        />
      </div>
    </div>
  </NuxtLayout>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { getTaskColumns } from "~/config/tableColumns"
import DataTable from "~/components/data-table.vue"
import WorkerStatusSummary from "~/components/WorkerStatusSummary.vue"
import OrphanTasksSummary from "~/components/OrphanTasksSummary.vue"
import CommandPalette from "~/components/CommandPalette.vue"

// Stores
const tasksStore = useTasksStore()
const workersStore = useWorkersStore()
const orphanTasksStore = useOrphanTasksStore()
const wsStore = useWebSocketStore()

// Computed
const secondsSinceUpdate = computed(() => {
  if (!tasksStore.lastRefreshTime) return 0
  return Math.floor((Date.now() - tasksStore.lastRefreshTime.getTime()) / 1000)
})

const currentSorting = computed(() => {
  const { sort_by, sort_order } = tasksStore.paginationParams
  if (!sort_by) return []
  return [{ id: sort_by, desc: sort_order === 'desc' }]
})

const currentFilters = computed(() => {
  const filters = tasksStore.filters
  const result: { key: string; value: string }[] = []
  
  Object.entries(filters).forEach(([key, value]) => {
    if (value && key !== 'search') {
      // Remove 'filter_' prefix if present
      const cleanKey = key.startsWith('filter_') ? key.slice(7) : key
      result.push({ key: cleanKey, value })
    }
  })
  
  return result
})

// Table columns
const columns = getTaskColumns()

// Actions
function handleToggleLiveMode() {
  const newMode = !tasksStore.isLiveMode
  wsStore.setMode(newMode ? 'live' : 'static')
  tasksStore.setLiveMode(newMode)
  
  if (newMode) {
    // Reset to first page for live mode to see newest events
    tasksStore.setPage(0)
  } else {
    // Refresh data when switching to static mode
    tasksStore.fetchRecentEvents()
  }
}

function handleSetSorting(sorting: { id: string; desc: boolean }[]) {
  if (sorting.length > 0) {
    const sort = sorting[0]
    tasksStore.setSorting(sort.id, sort.desc ? 'desc' : 'asc')
  } else {
    tasksStore.setSorting(null)
  }
}

function handleSetFilters(filters: { key: string; value: string }[]) {
  const filterObj: Record<string, string | null> = {}
  
  filters.forEach(filter => {
    // Add 'filter_' prefix for API compatibility
    filterObj[`filter_${filter.key}`] = filter.value
  })
  
  tasksStore.setFilters(filterObj)
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

// Lifecycle
onMounted(async () => {
  document.addEventListener('mousemove', handleMouseMove)
  
  // Initial data fetch
  await Promise.all([
    tasksStore.fetchRecentEvents(),
    tasksStore.fetchStats(),
    workersStore.fetchWorkers(),
    orphanTasksStore.fetchOrphanedTasks()
  ])
  
  // Set initial mode based on WebSocket client preference
  tasksStore.setLiveMode(wsStore.clientMode === 'live')
  
  // Set up periodic refresh for workers and orphaned tasks
  const orphanTasksInterval = setInterval(() => {
    orphanTasksStore.fetchOrphanedTasks()
  }, 60000) // Poll every 60 seconds for orphaned tasks
  
  const workerInterval = setInterval(() => {
    // Only fetch if WebSocket is not connected
    if (!wsStore.isConnected) {
      workersStore.fetchWorkers()
    }
  }, 30000)
  
  onUnmounted(() => {
    clearInterval(orphanTasksInterval)
    clearInterval(workerInterval)
  })
})

onUnmounted(() => {
  document.removeEventListener('mousemove', handleMouseMove)
})
</script>

<style scoped>
/* Glow effects are now handled by global CSS utilities */
</style>
