<template>
  <div 
    class="border border-card-border rounded-lg overflow-hidden transition-all duration-300"
    :class="cardClasses">
    
    <!-- Compact View -->
    <div class="p-4 cursor-pointer hover:bg-background-primary/10 transition-colors" @click="toggleExpand">
      
      <!-- Header Row -->
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center gap-2">
          <StatusDot :status="getStatusType(worker.status)" :pulse="worker.status === 'online'" />
          <span class="font-mono text-xs">{{ worker.hostname }}</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-xs text-text-tertiary">{{ formatTimestamp(worker.timestamp) }}</span>
          <svg class="w-4 h-4 text-text-tertiary transition-transform"
               :class="{ 'rotate-180': isExpanded }"
               fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>

      <!-- Key Metrics Grid -->
      <div class="grid grid-cols-2 gap-4 text-xs">
        <div>
          <div class="text-text-tertiary mb-0.5">Active</div>
          <div class="font-mono font-medium">{{ worker.active_tasks || 0 }}</div>
        </div>
        <div>
          <div class="text-text-tertiary mb-0.5">Rate</div>
          <div class="font-mono">{{ worker.tasks_per_minute || 0 }}/min</div>
        </div>
      </div>

      <!-- Error Indicator (if errors exist) -->
      <div v-if="worker.error_count && worker.error_count > 0" class="mt-2 pt-2 border-t border-card-border">
        <div class="flex items-center gap-2 text-xs text-status-error">
          <span>⚠</span>
          <span>{{ worker.error_count }} {{ worker.error_count === 1 ? 'error' : 'errors' }} in last 5 min</span>
        </div>
      </div>
    </div>

    <!-- Expanded Details -->
    <div v-if="isExpanded" class="border-t border-card-border">
      <div class="p-4 space-y-4">
        
        <!-- System Information -->
        <div>
          <h4 class="text-xs font-medium text-text-secondary mb-2">SYSTEM INFO</h4>
          <div class="grid grid-cols-2 gap-x-8 gap-y-2 text-xs">
            <div class="flex justify-between">
              <span class="text-text-tertiary">Software</span>
              <span class="font-mono">{{ worker.sw_ident || 'N/A' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-text-tertiary">Version</span>
              <span class="font-mono">{{ worker.sw_ver || 'N/A' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-text-tertiary">System</span>
              <span class="font-mono">{{ worker.sw_sys || 'N/A' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-text-tertiary">Load Avg</span>
              <span class="font-mono">{{ formatLoadAvg(worker.loadavg) }}</span>
            </div>
          </div>
        </div>

        <!-- Performance Metrics -->
        <div>
          <h4 class="text-xs font-medium text-text-secondary mb-2">PERFORMANCE</h4>
          <div class="grid grid-cols-2 gap-x-8 gap-y-2 text-xs">
            <div class="flex justify-between">
              <span class="text-text-tertiary">Total Processed</span>
              <span class="font-mono">{{ worker.processed_tasks || 0 }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-text-tertiary">Queue Depth</span>
              <span class="font-mono">{{ worker.queue_depth || 0 }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-text-tertiary">Frequency</span>
              <span class="font-mono">{{ worker.freq ? `${worker.freq} Hz` : 'N/A' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-text-tertiary">Tasks/Min</span>
              <span class="font-mono">{{ worker.tasks_per_minute || 0 }}</span>
            </div>
          </div>
        </div>

        <!-- Recent Errors (if any) -->
        <div v-if="worker.recent_errors && worker.recent_errors.length > 0">
          <h4 class="text-xs font-medium text-text-secondary mb-2">RECENT ERRORS</h4>
          <div class="space-y-2">
            <div v-for="(error, idx) in worker.recent_errors.slice(0, 3)" 
                 :key="idx"
                 class="text-xs p-2 bg-background-primary rounded border border-status-error/20">
              <div class="flex justify-between mb-1">
                <span class="font-mono text-status-error">{{ error.task }}</span>
                <span class="text-text-tertiary">{{ formatErrorTime(error.time) }}</span>
              </div>
              <div v-if="error.error" class="text-text-secondary">
                {{ error.error }}
              </div>
            </div>
          </div>
        </div>

        <!-- Active Tasks (if any) -->
        <div v-if="worker.active_task_details && worker.active_task_details.length > 0">
          <h4 class="text-xs font-medium text-text-secondary mb-2">ACTIVE TASKS</h4>
          <div class="space-y-1">
            <div v-for="(task, idx) in worker.active_task_details.slice(0, 5)"
                 :key="task.task_id || idx"
                 class="flex justify-between text-xs">
              <span class="font-mono truncate flex-1 mr-2">{{ task.name }}</span>
              <span class="text-text-tertiary">{{ formatDuration(task.duration) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import StatusDot from '~/components/StatusDot.vue'

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
  queue?: string
  recent_errors?: Array<{time: string, task: string, error?: string}>
  active_task_details?: Array<{
    name: string
    progress: number
    duration: number
    task_id?: string
  }>
}

const props = defineProps<{
  worker: WorkerInfo
}>()

const isExpanded = ref(false)

const toggleExpand = () => {
  isExpanded.value = !isExpanded.value
}

const cardClasses = computed(() => {
  const classes = ['bg-card-base']
  
  if (props.worker.status === 'offline') {
    classes.push('bg-gradient-to-br from-card-base to-status-error/5', 'border-status-error/20')
  }
  else if (props.worker.error_count && props.worker.error_count > 0) {
    classes.push('bg-gradient-to-br from-card-base to-status-warning/5', 'border-status-warning/20')
  }
  else if (props.worker.loadavg && props.worker.loadavg[0] > 4) {
    classes.push('bg-gradient-to-br from-card-base to-status-warning/3', 'border-status-warning/10')
  }
  
  return classes.join(' ')
})

const getStatusType = (status: string): 'online' | 'offline' | 'warning' | 'error' | 'info' | 'success' => {
  switch (status.toLowerCase()) {
    case 'online':
      return 'online'
    case 'offline':
      return 'offline'
    case 'heartbeat':
      return 'info'
    case 'warning':
      return 'warning'
    case 'error':
      return 'error'
    default:
      return 'offline'
  }
}

const formatTimestamp = (timestamp: string): string => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 60000) return `${Math.floor(diff / 1000)}s ago`
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })
}

const formatErrorTime = (timestamp: string): string => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit',
    second: '2-digit',
    hour12: false 
  })
}

const formatLoadAvg = (loadavg?: number[]): string => {
  if (!loadavg || loadavg.length === 0) return 'N/A'
  return loadavg.map(l => l.toFixed(2)).join(', ')
}

const formatDuration = (seconds: number): string => {
  if (seconds < 60) return `${seconds.toFixed(0)}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${(seconds % 60).toFixed(0)}s`
  return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`
}

const getResourceClass = (percent?: number): string => {
  if (percent === undefined) return 'text-text-tertiary'
  if (percent < 60) return ''
  if (percent < 80) return 'text-yellow-500'
  return 'text-red-500'
}
</script>
