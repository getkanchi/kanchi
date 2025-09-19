<template>
  <div class="p-6 bg-background-base text-text-primary min-h-full">
    <h1 class="text-2xl font-bold mb-4">Task Monitor</h1>
    <p class="mb-4">Status: {{ isConnected ? "Connected" : "Disconnected" }}</p>

    <!-- Dotted grid background -->
    <div
      class="absolute inset-0 opacity-20 pointer-events-none"
      style="
        background-image: radial-gradient(circle, rgb(255,255,255) 1px, transparent 1px);
        background-size: 25px 25px;
      "
    ></div>
    
    <div class="mb-6">
      <h2 class="text-lg font-semibold mb-3">Tasks Table</h2>
      <DataTable 
        :columns="columns" 
        :data="liveTable.data" 
        :is-live-mode="liveTable.isLiveMode"
        :seconds-since-update="liveTable.secondsSinceUpdate"
        :page-index="liveTable.pageIndex"
        :page-size="liveTable.pageSize"
        class="relative backdrop-blur-sm bg-card-base border-card-border glow-border"
        @toggle-live-mode="liveTable.toggleLiveMode"
        @set-page-index="liveTable.setPageIndex"
        @set-page-size="liveTable.setPageSize"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, h } from 'vue'
import { useWebSocket } from "~/composables/useWebsocket"
import { useLiveTable } from "~/composables/useLiveTable"
import DataTable from "~/components/data-table.vue"
import { Badge } from "~/components/ui/badge"
import type { ColumnDef } from '@tanstack/vue-table'

interface Task {
  id: string
  name: string
  status: string
  queue: string
  started_at: string
  completed_at: string
  args?: any[]
  kwargs?: Record<string, any>
  result?: any
  traceback?: string
  worker?: string
  runtime?: number
  eta?: string
  retries?: number
}

const { isConnected, messages } = useWebSocket("ws://localhost:8765/ws")

// Initial task data
const initialData: Task[] = [
  {
    id: 'task-1',
    name: 'process_data',
    status: 'SUCCESS',
    queue: 'default',
    started_at: '2024-01-01 10:00:00',
    completed_at: '2024-01-01 10:05:00',
    args: ['data_file.csv', 1000],
    kwargs: { 'batch_size': 50, 'validate': true },
    result: { 'processed': 1000, 'failed': 0 },
    worker: 'worker-01'
  },
  {
    id: 'task-2', 
    name: 'send_email',
    status: 'FAILED',
    queue: 'email',
    started_at: '2024-01-01 10:03:00',
    completed_at: '2024-01-01 10:03:15',
    args: ['user@example.com'],
    kwargs: { 'template': 'welcome', 'retry': true },
    traceback: 'ConnectionError: Failed to connect to SMTP server\n  at send_email (tasks.py:45)\n  at execute (celery/task.py:123)',
    worker: 'worker-02',
    retries: 2
  },
  {
    id: 'task-3',
    name: 'backup_database',
    status: 'RUNNING',
    queue: 'high_priority',
    started_at: '2024-01-01 10:01:00',
    completed_at: '',
    args: [],
    kwargs: { 'database': 'production', 'compression': 'gzip' },
    worker: 'worker-01',
    eta: '2024-01-01 10:15:00'
  }
]

// Setup live table with WebSocket integration
const liveTable = useLiveTable(initialData)

// Track tasks by ID for updates
const taskMap = ref<Map<string, Task>>(new Map())

// Initialize task map
initialData.forEach(task => {
  taskMap.value.set(task.id, task)
})

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
      const taskEvent = latestMessage as any
      const taskId = taskEvent.task_id
      const status = eventTypeToStatus(taskEvent.event_type)
      
      // Update existing task or create new one
      const existingTask = taskMap.value.get(taskId)
      const updatedTask: Task = {
        id: taskId,
        name: taskEvent.task_name || 'unknown_task',
        status: status,
        queue: taskEvent.routing_key || 'default',
        started_at: taskEvent.event_type === 'task-started' ? taskEvent.timestamp : (existingTask?.started_at || ''),
        completed_at: ['task-succeeded', 'task-failed'].includes(taskEvent.event_type) ? taskEvent.timestamp : (existingTask?.completed_at || ''),
        worker: taskEvent.hostname || existingTask?.worker,
        runtime: taskEvent.runtime || existingTask?.runtime,
        result: taskEvent.result || existingTask?.result,
        traceback: taskEvent.traceback || existingTask?.traceback,
        retries: taskEvent.retries || existingTask?.retries || 0
      }
      
      // Update task map
      taskMap.value.set(taskId, updatedTask)
      
      // Update live table data only if task was new or actually changed
      const currentData = liveTable.data.value
      const existingIndex = currentData.findIndex(task => task.id === taskId)
      
      if (existingIndex === -1) {
        // New task - add to the beginning of the array
        const updatedData = [updatedTask, ...currentData]
        liveTable.updateData(updatedData)
      } else {
        // Existing task - update in place to avoid re-rendering entire table
        const updatedData = [...currentData]
        updatedData[existingIndex] = updatedTask
        liveTable.updateData(updatedData)
      }
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

// Column definitions - focused on troubleshooting
const columns: ColumnDef<Task>[] = [
  {
    accessorKey: 'name', 
    header: 'Task Name',
    cell: ({ row }) => h("div", { class: "font-medium" }, row.getValue("name")),
  },
  {
    accessorKey: 'status',
    header: 'Status',
    cell: ({ row }) => {
      const status = row.getValue('status') as string
      const statusLower = status.toLowerCase()
      
      // Custom status badge styling
      const statusStyles: Record<string, string> = {
        'success': 'bg-green-950/20 text-green-400 border-green-900/20',
        'failed': 'bg-red-950/20 text-red-400 border-red-900/20',
        'pending': 'bg-yellow-950/20 text-yellow-400 border-yellow-900/20',
        'running': 'bg-blue-950/20 text-blue-400 border-blue-900/20',
        'retry': 'bg-orange-950/20 text-orange-400 border-orange-900/20',
        'revoked': 'bg-gray-950/20 text-gray-400 border-gray-900/20',
        'received': 'bg-purple-950/20 text-purple-400 border-purple-900/20'
      }
      
      const className = statusStyles[statusLower] || 'bg-gray-950/20 text-gray-400 border-gray-900/20'
      
      return h('div', { 
        class: `inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-full border ${className}`
      }, status)
    }
  },
  {
    accessorKey: 'started_at',
    header: 'Started',
    cell: ({ row }) => h("div", { class: "text-sm" }, formatTime(row.getValue("started_at"))),
    enableSorting: true,
    sortDescFirst: true
  },
  {
    accessorKey: 'duration',
    header: 'Duration',
    cell: ({ row }) => {
      const task = row.original
      return h("div", { class: "text-sm font-mono" }, calculateDuration(task.started_at, task.completed_at))
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
    accessorKey: 'worker',
    header: 'Worker',
    cell: ({ row }) => {
      const worker = row.original.worker
      if (!worker) return h("div", { class: "text-gray-400" }, "-")
      return h("div", { class: "text-xs font-mono" }, worker)
    }
  },
  {
    accessorKey: 'queue',
    header: 'Queue',
    cell: ({ row }) => {
      const queue = row.original.queue
      if (!queue) return h("div", { class: "text-gray-400" }, "default")
      return h("div", { class: "text-xs" }, queue)
    }
  }
]

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