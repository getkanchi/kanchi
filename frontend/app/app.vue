<template>
  <NuxtLayout>
    <div class="p-6">
      <div class="flex items-center">
        <h1 class="text-2xl font-bold mb-4 mr-4">Task Monitor</h1>
        <div class="mb-4">
          <Popover>
            <PopoverTrigger as-child>
              <Badge 
                :variant="isConnected ? 'online' : 'offline'"
                class="cursor-pointer"
              >
                <StatusDot 
                  :status="isConnected ? 'online' : 'offline'" 
                  :pulse="isConnected"
                  class="mr-2"
                />
                {{ isConnected ? "Agent Connected" : "Agent Disconnected" }}
              </Badge>
            </PopoverTrigger>
            <PopoverContent class="w-80 bg-card-base border-card-border text-text-primary">
              <div class="space-y-2">
                <h4 class="font-medium text-text-primary">Agent Connection Details</h4>
                <div class="text-sm text-text-secondary space-y-1.5">
                  <p><strong class="text-text-primary">Status:</strong> <span class="font-bold">{{ isConnected ? "Connected" : "Disconnected" }}</span></p>
                  <p><strong class="text-text-primary">WebSocket URL:</strong> <code class="text-xs bg-background-primary px-1 py-0.5 rounded">ws://localhost:8765/ws</code></p>
                  <p><strong class="text-text-primary">Last Update:</strong> <code class="text-xs bg-background-primary px-1 py-0.5 rounded">{{ new Date().toLocaleTimeString() }}</code></p>
                </div>
              </div>
            </PopoverContent>
          </Popover>
        </div>
      </div>

      <!-- Workers Overview -->
      <div class="mb-6">
        <h2 class="text-lg font-mono mb-3">Workers Status</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-4 mb-4">
          <WorkerCard
            v-for="worker in workers"
            :key="worker.hostname"
            :worker="worker"
            :class="'glow-border'"
            @update="updateWorkerData"
          />
          
          <!-- Empty State -->
          <div v-if="workers.length === 0" class="col-span-full text-center py-8">
            <p class="text-muted-foreground text-sm">No workers detected</p>
          </div>
        </div>
      </div>

      <div class="mb-6">
        <h2 class="text-lg mb-3 font-mono">Tasks Table</h2>
        <DataTable 
          :columns="columns" 
          :data="liveTable.data" 
          :is-live-mode="liveTable.isLiveMode"
          :seconds-since-update="liveTable.secondsSinceUpdate"
          :page-index="liveTable.pageIndex"
          :page-size="liveTable.pageSize"
          :pagination="liveTable.pagination"
          :is-loading="liveTable.isLoading"
          class="relative backdrop-blur-sm bg-card-base border-card-border glow-border"
          @toggle-live-mode="liveTable.toggleLiveMode"
          @set-page-index="liveTable.setPageIndex"
          @set-page-size="liveTable.setPageSize"
        />
      </div>

<!--    <div class="mt-6">-->
<!--      <h2 class="text-lg font-semibold mb-3">WebSocket Messages</h2>-->
<!--      <ul class="space-y-1">-->
<!--        <li v-for="(msg, index) in messages" :key="index" class="text-sm bg-gray-100 p-2 rounded">-->
<!--          {{ msg }}-->
<!--        </li>-->
<!--      </ul>-->
<!--    </div>-->
    </div>
  </NuxtLayout>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, h } from 'vue'
import { useWebSocket } from "~/composables/useWebsocket"
import { useLiveTable } from "~/composables/useLiveTable"
import DataTable from "~/components/data-table.vue"
import { Badge } from "~/components/ui/badge"
import { Popover, PopoverContent, PopoverTrigger } from "~/components/ui/popover"
import WorkerCard from "~/components/WorkerCard.vue"
import StatusDot from "~/components/StatusDot.vue"
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

const { isConnected, messages } = useWebSocket("ws://localhost:8765/ws")

// Setup live table with WebSocket integration and server-side pagination
const liveTable = useLiveTable([], "http://localhost:8765/api/events/recent")

// Worker state
const workers = ref<WorkerInfo[]>([])
const workerMap = ref<Map<string, WorkerInfo>>(new Map())

// Fetch initial worker data
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

// Helper to convert event_type to status
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

// Watch for new WebSocket messages and update table data
watch(messages, (newMessages) => {
  if (liveTable.isLiveMode.value && newMessages.length > 0) {
    // Process the latest message to update task data
    const latestMessage = newMessages[newMessages.length - 1]
    
    // Check if it's a TaskEvent from the agent
    if (typeof latestMessage === 'object' && 'task_id' in latestMessage && 'event_type' in latestMessage) {
      // In live mode with server-side pagination, just refresh the current page
      // This ensures we get the latest data from the server
      if (liveTable.pageIndex.value === 0) {
        // Only auto-refresh if we're on the first page (to see newest tasks)
        liveTable.fetchData()
      }
    }
    
    // Check if it's a WorkerEvent
    if (typeof latestMessage === 'object' && 'event_type' in latestMessage && 
        latestMessage.event_type?.startsWith('worker-')) {
      const workerEvent = latestMessage as WorkerEvent
      
      // Update worker info
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
      
      // Update based on event type
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
        // Calculate tasks per minute based on processing rate
        // This would need backend support for accurate calculation
        // For now, we'll estimate based on processed tasks changes
      }
      
      workerInfo.timestamp = workerEvent.timestamp
      
      // Update workers array
      workers.value = Array.from(workerMap.value.values())
    }
  }
}, { deep: true })

// Helper to calculate duration
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

// Helper to format timestamp
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

// Helper to get status from event_type
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

// Column definitions - focused on troubleshooting
const columns: ColumnDef<Task>[] = [
  {
    accessorKey: 'task_name', 
    header: 'Task Name',
    cell: ({ row }) => h("div", { class: "font-medium" }, row.getValue("task_name")),
  },
  {
    accessorKey: 'event_type',
    header: 'Status',
    cell: ({ row }) => {
      const eventType = row.getValue('event_type') as string
      const status = getStatusFromEventType(eventType)
      const statusLower = status.toLowerCase()
      
      // Map status to badge variant
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
    }
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
    }
  },
  {
    accessorKey: 'retries',
    header: 'Retries',
    cell: ({ row }) => {
      const retries = row.original.retries || 0
      return h("div", { 
        class: retries > 0 ? "text-orange-500 font-medium" : "text-gray-400" 
      }, retries.toString())
    }
  },
  {
    accessorKey: 'hostname',
    header: 'Worker',
    cell: ({ row }) => {
      const hostname = row.original.hostname
      if (!hostname) return h("div", { class: "text-gray-400" }, "-")
      return h("div", { class: "text-xs font-mono" }, hostname)
    }
  }
]

// Worker helper functions removed - moved to WorkerCard component

// Update worker data from child component
const updateWorkerData = (hostname: string, updates: Partial<WorkerInfo>) => {
  const worker = workerMap.value.get(hostname)
  if (worker) {
    Object.assign(worker, updates)
    workers.value = Array.from(workerMap.value.values())
  }
}

// Mouse tracking for glow effect
const handleMouseMove = (e: MouseEvent) => {
  const glowElements = document.querySelectorAll('.glow-border')
  glowElements.forEach(element => {
    const rect = element.getBoundingClientRect()
    
    // Calculate mouse position relative to the element
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    
    ;(element as HTMLElement).style.setProperty('--mouse-x', `${x}px`)
    ;(element as HTMLElement).style.setProperty('--mouse-y', `${y}px`)
  })
}

onMounted(() => {
  document.addEventListener('mousemove', handleMouseMove)
  
  // Fetch initial workers
  fetchWorkers()
  
  // Refresh workers every 30 seconds
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
