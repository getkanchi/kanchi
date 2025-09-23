<template>
  <NuxtLayout>
    <div class="p-6">

      <!-- Workers Overview -->
      <div class="mb-6">
        <WorkerStatusSummary
          :workers="workers"
          @update="updateWorkerData"
        />
      </div>

      <div class="mb-6">
        <DataTable
          :columns="columns" 
          :data="liveTable.data" 
          :is-live-mode="liveTable.isLiveMode"
          :seconds-since-update="liveTable.secondsSinceUpdate"
          :page-index="liveTable.pageIndex"
          :page-size="liveTable.pageSize"
          :pagination="liveTable.pagination"
          :is-loading="liveTable.isLoading"
          :sorting="liveTable.sorting"
          :search-query="liveTable.searchQuery"
          :filters="liveTable.filters"
          class="relative backdrop-blur-sm bg-card-base border-card-border glow-border"
          @toggle-live-mode="liveTable.toggleLiveMode"
          @set-page-index="liveTable.setPageIndex"
          @set-page-size="liveTable.setPageSize"
          @set-sorting="liveTable.setSorting"
          @set-search-query="liveTable.setSearchQuery"
          @set-filters="liveTable.setFilters"
        />
      </div>
    </div>
  </NuxtLayout>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, h } from 'vue'
import { useWebSocketSingleton } from "~/composables/useWebsocketSingleton"
import { useLiveTable } from "~/composables/useLiveTable"
import DataTable from "~/components/data-table.vue"
import { Badge } from "~/components/ui/badge"
import WorkerStatusSummary from "~/components/WorkerStatusSummary.vue"
import type { ColumnDef } from '@tanstack/vue-table'

interface Task {
  task_id: string
  task_name: string
  event_type: string
  timestamp: string
  args?: string
  kwargs?: string
  retries: number
  eta?: string
  expires?: string
  hostname?: string
  exchange: string
  routing_key: string
  root_id?: string
  parent_id?: string
  result?: any
  runtime?: number
  exception?: string
  traceback?: string
}

interface WorkerInfo {
  hostname: string
  status: string
  timestamp: string
  active_tasks: number
  processed_tasks: number
  sw_ident?: string
  sw_ver?: string
  sw_sys?: string
  loadavg?: number[]
  freq?: number
  error_count?: number
  tasks_per_minute?: number
  queue_depth?: number
  recent_errors?: Array<{time: string, task: string, error?: string}>
  active_task_details?: Array<{
    name: string
    progress: number
    duration: number
    task_id?: string
  }>
  metrics_history?: {
    tasks_per_minute: number[]
    errors: number[]
    latency: number[]
  }
}

interface WorkerEvent {
  hostname: string
  event_type: string
  timestamp: string
  active?: number
  processed?: number
  pool?: any
  loadavg?: number[]
  freq?: number
}

const { isConnected, messages } = useWebSocketSingleton("ws://localhost:8765/ws")

const liveTable = useLiveTable([], "http://localhost:8765/api/events/recent")

const workers = ref<WorkerInfo[]>([])
const workerMap = ref<Map<string, WorkerInfo>>(new Map())

const fetchWorkers = async () => {
  try {
    const response = await fetch('http://localhost:8765/api/workers')
    if (response.ok) {
      const data = await response.json()
      data.forEach((worker: WorkerInfo) => {
        workerMap.value.set(worker.hostname, worker)
      })
      workers.value = Array.from(workerMap.value.values())
    }
  } catch (error) {
    console.error('Failed to fetch workers:', error)
  }
}

const eventTypeToStatus = (eventType: string): string => {
  switch (eventType) {
    case 'task-sent':
      return 'PENDING'
    case 'task-received':
      return 'RECEIVED'
    case 'task-started':
      return 'RUNNING'
    case 'task-succeeded':
      return 'SUCCESS'
    case 'task-failed':
      return 'FAILED'
    case 'task-retried':
      return 'RETRY'
    case 'task-revoked':
      return 'REVOKED'
    default:
      return 'UNKNOWN'
  }
}

watch(messages, (newMessages) => {
  if (liveTable.isLiveMode.value && newMessages.length > 0) {
    const latestMessage = newMessages[newMessages.length - 1]
    
    if (typeof latestMessage === 'object' && 'task_id' in latestMessage && 'event_type' in latestMessage) {
      if (liveTable.pageIndex.value === 0) {
        liveTable.fetchData()
      }
    }
    
    if (typeof latestMessage === 'object' && 'event_type' in latestMessage && 
        latestMessage.event_type?.startsWith('worker-')) {
      const workerEvent = latestMessage as WorkerEvent
      
      const hostname = workerEvent.hostname
      let workerInfo = workerMap.value.get(hostname)
      
      if (!workerInfo) {
        workerInfo = {
          hostname,
          status: 'unknown',
          timestamp: workerEvent.timestamp,
          active_tasks: 0,
          processed_tasks: 0
        }
        workerMap.value.set(hostname, workerInfo)
      }
      
      if (workerEvent.event_type === 'worker-online') {
        workerInfo.status = 'online'
      } else if (workerEvent.event_type === 'worker-offline') {
        workerInfo.status = 'offline'
      } else if (workerEvent.event_type === 'worker-heartbeat') {
        workerInfo.status = 'online'
        if (workerEvent.active !== undefined) {
          workerInfo.active_tasks = workerEvent.active
        }
        if (workerEvent.processed !== undefined) {
          workerInfo.processed_tasks = workerEvent.processed
        }
        if (workerEvent.loadavg) {
          workerInfo.loadavg = workerEvent.loadavg
        }
      }
      
      workerInfo.timestamp = workerEvent.timestamp
      
      workers.value = Array.from(workerMap.value.values())
    }
  }
}, { deep: true })

const calculateDuration = (started: string, completed: string): string => {
  if (!started) return '-'
  
  const start = new Date(started).getTime()
  const end = completed ? new Date(completed).getTime() : Date.now()
  const duration = end - start
  
  if (duration < 1000) return `${duration}ms`
  if (duration < 60000) return `${(duration / 1000).toFixed(1)}s`
  if (duration < 3600000) return `${Math.floor(duration / 60000)}m ${Math.floor((duration % 60000) / 1000)}s`
  return `${Math.floor(duration / 3600000)}h ${Math.floor((duration % 3600000) / 60000)}m`
}

const formatTime = (timestamp: string): string => {
  if (!timestamp) return '-'
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit', 
    second: '2-digit',
    hour12: false 
  })
}

const getStatusFromEventType = (eventType: string): string => {
  switch (eventType) {
    case 'task-sent':
      return 'PENDING'
    case 'task-received':
      return 'RECEIVED'
    case 'task-started':
      return 'RUNNING'
    case 'task-succeeded':
      return 'SUCCESS'
    case 'task-failed':
      return 'FAILED'
    case 'task-retried':
      return 'RETRY'
    case 'task-revoked':
      return 'REVOKED'
    default:
      return 'UNKNOWN'
  }
}

const columns: ColumnDef<Task>[] = [
  {
    accessorKey: 'task_name', 
    header: 'Task Name',
    cell: ({ row }) => h("div", { class: "font-medium" }, row.getValue("task_name")),
    enableSorting: true
  },
  {
    accessorKey: 'event_type',
    header: 'Status',
    cell: ({ row }) => {
      const eventType = row.getValue('event_type') as string
      const status = getStatusFromEventType(eventType)
      const statusLower = status.toLowerCase()
      
      const statusVariants: Record<string, string> = {
        'success': 'success',
        'failed': 'failed',
        'pending': 'pending',
        'running': 'running',
        'retry': 'retry',
        'revoked': 'revoked',
        'received': 'received'
      }
      
      const variant = statusVariants[statusLower] || 'outline'
      
      return h(Badge, { 
        variant,
        class: 'text-xs'
      }, () => status.charAt(0).toUpperCase() + status.slice(1).toLowerCase())
    },
    enableSorting: true
  },
  {
    accessorKey: 'timestamp',
    header: 'Time',
    cell: ({ row }) => h("div", { class: "text-sm" }, formatTime(row.getValue("timestamp"))),
    enableSorting: true,
    sortDescFirst: true
  },
  {
    accessorKey: 'runtime',
    header: 'Runtime',
    cell: ({ row }) => {
      const runtime = row.original.runtime
      if (!runtime) return h("div", { class: "text-gray-400" }, "-")
      return h("div", { class: "text-sm font-mono" }, `${runtime.toFixed(2)}s`)
    },
    enableSorting: true
  },
  {
    accessorKey: 'retries',
    header: 'Retries',
    cell: ({ row }) => {
      const retries = row.original.retries || 0
      return h("div", { 
        class: retries > 0 ? "text-orange-500 font-medium" : "text-gray-400" 
      }, retries.toString())
    },
    enableSorting: true
  },
  {
    accessorKey: 'hostname',
    header: 'Worker',
    cell: ({ row }) => {
      const hostname = row.original.hostname
      if (!hostname) return h("div", { class: "text-gray-400" }, "-")
      return h("div", { class: "text-xs font-mono" }, hostname)
    },
    enableSorting: true
  }
]


const updateWorkerData = (hostname: string, updates: Partial<WorkerInfo>) => {
  const worker = workerMap.value.get(hostname)
  if (worker) {
    Object.assign(worker, updates)
    workers.value = Array.from(workerMap.value.values())
  }
}

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

onMounted(() => {
  document.addEventListener('mousemove', handleMouseMove)
  
  fetchWorkers()
  
  const workerInterval = setInterval(fetchWorkers, 30000)
  
  onUnmounted(() => {
    clearInterval(workerInterval)
  })
})

onUnmounted(() => {
  document.removeEventListener('mousemove', handleMouseMove)
})
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
