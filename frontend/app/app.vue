<template>
  <NuxtLayout>
    <div class="p-6">

      <!-- Command Palette -->
      <CommandPalette 
        :is-live-mode="wsStore.clientMode === 'live'"
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

      <div class="mb-6">
        <DataTable
          :columns="columns" 
          :data="tasksStore.recentEvents" 
          :is-live-mode="wsStore.clientMode === 'live'"
          :seconds-since-update="secondsSinceUpdate"
          :page-index="tasksStore.currentPage"
          :page-size="tasksStore.paginationParams.limit"
          :pagination="tasksStore.pagination"
          :is-loading="tasksStore.isLoading"
          :sorting="currentSorting"
          :search-query="tasksStore.filters.search || ''"
          :filters="currentFilters"
          class="relative backdrop-blur-sm bg-card-base border-card-border glow-border"
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
import CommandPalette from "~/components/CommandPalette.vue"

// Stores
const tasksStore = useTasksStore()
const workersStore = useWorkersStore()
const wsStore = useWebSocketStore()

// State
const lastUpdated = ref<Date | null>(null)

// Computed
const secondsSinceUpdate = computed(() => {
  if (!lastUpdated.value) return 0
  return Math.floor((Date.now() - lastUpdated.value.getTime()) / 1000)
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
  const newMode = wsStore.clientMode === 'live' ? 'static' : 'live'
  wsStore.setMode(newMode)
  
  if (newMode === 'live') {
    // Reset to first page for live mode
    tasksStore.setPage(0)
    lastUpdated.value = new Date()
  } else {
    // Fetch current data for static mode
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
    workersStore.fetchWorkers()
  ])
  
  lastUpdated.value = new Date()
  
  // Set up conditional workers refresh - only poll when WebSocket is not connected
  let workerInterval: ReturnType<typeof setInterval> | null = null
  
  const startPolling = () => {
    if (workerInterval) return
    workerInterval = setInterval(() => {
      // Only fetch if WebSocket is not connected
      if (!wsStore.isConnected) {
        workersStore.fetchWorkers()
      }
    }, 30000)
  }
  
  const stopPolling = () => {
    if (workerInterval) {
      clearInterval(workerInterval)
      workerInterval = null
    }
  }
  
  // Start polling initially and manage based on WebSocket connection
  startPolling()
  
  // Watch WebSocket connection status to optimize polling
  watch(() => wsStore.isConnected, (connected) => {
    if (connected) {
      // WebSocket connected: reduce polling frequency or stop
      stopPolling()
      // Refresh workers once when WebSocket connects to get current state
      workersStore.fetchWorkers()
    } else {
      // WebSocket disconnected: start/resume polling
      startPolling()
    }
  })
  
  onUnmounted(() => {
    stopPolling()
  })
})

onUnmounted(() => {
  document.removeEventListener('mousemove', handleMouseMove)
})

// The WebSocket connection watcher for polling is handled above in onMounted
// This separate watcher is just for updating the lastUpdated timestamp
watch(() => wsStore.isConnected, (connected) => {
  if (connected && wsStore.clientMode === 'live') {
    lastUpdated.value = new Date()
  }
})

// Update last updated time when data changes in live mode
watch(() => tasksStore.recentEvents, () => {
  if (wsStore.clientMode === 'live') {
    lastUpdated.value = new Date()
  }
}, { deep: true })
</script>

<style scoped>
.glow-border {
  --mouse-x: 0px;
  --mouse-y: 0px;
  position: relative;
  background: linear-gradient(#121212, #121212) padding-box,
              radial-gradient(300px at var(--mouse-x) var(--mouse-y),
                rgba(156, 163, 175, 0.4), 
                rgba(156, 163, 175, 0.2) 20%,
                transparent 100%) border-box;
  border: 1px solid rgba(156, 163, 175, 0.1);
  background-origin: border-box;
  background-clip: padding-box, border-box;
}
</style>