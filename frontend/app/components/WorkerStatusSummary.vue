<template>
  <div 
    class="border border-border rounded-lg overflow-hidden glow-border transition-all duration-300"
    :class="summaryClasses">
    
    <!-- Collapsed Summary View -->
    <div 
      class="py-2 px-4 cursor-pointer hover:bg-background-surface/5 transition-all duration-200"
      @click="toggleExpanded"
    >
      <div class="flex items-center justify-between">
        
        <!-- Left: Status Overview -->
        <div class="flex items-center gap-3">
          <div class="flex items-center gap-2">
            <StatusDot 
              :status="overallStatus" 
              :pulse="overallStatus === 'online'"
              class="scale-125"
            />
            <span class="font-medium text-sm">{{ statusText }}</span>
          </div>
          
          <!-- Quick Stats -->
          <div class="hidden sm:flex items-center gap-2 text-xs text-text-secondary">
            <span class="flex items-center gap-1">
              <span class="font-mono">{{ activeWorkersCount }}</span>
              <span>online</span>
            </span>
            <span class="flex items-center gap-1">
              <span class="font-mono">{{ totalActiveTasks }}</span>
              <span>active tasks</span>
            </span>
            <span v-if="totalErrors > 0" class="flex items-center gap-1 text-status-error">
              <span class="font-mono">{{ totalErrors }}</span>
              <span>errors</span>
            </span>
          </div>
        </div>

        <!-- Right: Expand Button -->
        <div class="flex items-center gap-2">
          <span class="text-xs text-text-muted hidden sm:inline">
            {{ isExpanded ? 'Hide details' : 'View details' }}
          </span>
          <svg 
            class="w-4 h-4 text-text-muted transition-transform duration-200"
            :class="{ 'rotate-180': isExpanded }"
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>

      <!-- Mobile Quick Stats (when collapsed) -->
      <div v-if="!isExpanded" class="sm:hidden flex items-center gap-4 text-xs text-text-secondary mt-2 pt-2 border-t border-border/50">
        <span class="flex items-center gap-1">
          <span class="font-mono">{{ activeWorkersCount }}</span>
          <span>online</span>
        </span>
        <span class="flex items-center gap-1">
          <span class="font-mono">{{ totalActiveTasks }}</span>
          <span>tasks</span>
        </span>
        <span v-if="totalErrors > 0" class="flex items-center gap-1 text-status-error">
          <span class="font-mono">{{ totalErrors }}</span>
          <span>errors</span>
        </span>
      </div>
    </div>

    <!-- Expanded Worker Grid -->
    <div 
      v-if="isExpanded" 
      class="border-t border-border bg-background-surface/30"
    >
      <div class="p-4 space-y-4">
        <!-- Active Workers Section -->
        <div v-if="activeWorkers.length > 0">
          <h3 class="text-sm font-medium text-text-secondary mb-3 flex items-center gap-2">
            <StatusDot status="online" class="scale-90" />
            Active Workers ({{ activeWorkers.length }})
          </h3>
          <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-2">
            <WorkerCard
              v-for="worker in activeWorkers"
              :key="worker.hostname"
              :worker="worker"
              @update="$emit('update', $event)"
            />
          </div>
        </div>

        <!-- Offline Workers Section (Collapsible) -->
        <div v-if="offlineWorkers.length > 0" class="pt-2">
          <div 
            class="flex items-center justify-between cursor-pointer py-2 px-3 rounded-lg hover:bg-background-surface/20 transition-all duration-200"
            @click="toggleOfflineExpanded"
          >
            <h3 class="text-sm font-medium text-text-secondary flex items-center gap-2">
              <StatusDot status="error" class="scale-90" />
              Offline Workers ({{ offlineWorkers.length }})
            </h3>
            <div class="flex items-center gap-2">
              <span class="text-xs text-text-muted">
                {{ isOfflineExpanded ? 'Hide offline' : 'Show offline' }}
              </span>
              <svg 
                class="w-4 h-4 text-text-muted transition-transform duration-200"
                :class="{ 'rotate-180': isOfflineExpanded }"
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>
          
          <!-- Offline Workers Grid -->
          <div 
            v-if="isOfflineExpanded"
            class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-2 mt-3"
          >
            <WorkerCard
              v-for="worker in offlineWorkers"
              :key="worker.hostname"
              :worker="worker"
              @update="$emit('update', $event)"
            />
          </div>
        </div>
        
        <!-- Empty State -->
        <div v-if="workers.length === 0" class="col-span-full text-center py-8">
          <div class="text-text-muted text-sm">
            <svg class="w-8 h-8 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <p>No workers detected</p>
            <p class="text-xs mt-1">Workers will appear here when they come online</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import StatusDot from '~/components/StatusDot.vue'
import WorkerCard from '~/components/WorkerCard.vue'

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
}

const props = defineProps<{
  workers: WorkerInfo[]
}>()

const emit = defineEmits<{
  update: [hostname: string, updates: Partial<WorkerInfo>]
}>()

const isExpanded = ref(false)
const isOfflineExpanded = ref(false)

const toggleExpanded = () => {
  isExpanded.value = !isExpanded.value
}

const toggleOfflineExpanded = () => {
  isOfflineExpanded.value = !isOfflineExpanded.value
}

// Computed properties for status analysis
const activeWorkers = computed(() => {
  return props.workers.filter(w => w.status === 'online')
})

const offlineWorkers = computed(() => {
  return props.workers.filter(w => w.status === 'offline')
})

const activeWorkersCount = computed(() => {
  return activeWorkers.value.length
})

const offlineWorkersCount = computed(() => {
  return offlineWorkers.value.length
})

const totalActiveTasks = computed(() => {
  return props.workers.reduce((sum, w) => sum + (w.active_tasks || 0), 0)
})

const totalErrors = computed(() => {
  return props.workers.reduce((sum, w) => sum + (w.error_count || 0), 0)
})

const overallStatus = computed((): 'online' | 'warning' | 'error' | 'muted' => {
  if (props.workers.length === 0) return 'muted'
  
  // Critical: Any workers offline
  if (offlineWorkersCount.value > 0) return 'error'
  
  // Warning: High error rate
  if (totalErrors.value > 0) return 'warning'
  
  // All good
  if (activeWorkersCount.value > 0) return 'online'
  
  return 'muted'
})

const statusText = computed(() => {
  const total = props.workers.length
  
  if (total === 0) {
    return 'No workers detected'
  }
  
  if (offlineWorkersCount.value > 0) {
    const online = activeWorkersCount.value
    return `${offlineWorkersCount.value} worker${offlineWorkersCount.value === 1 ? '' : 's'} offline${online > 0 ? `, ${online} online` : ''}`
  }
  
  if (totalErrors.value > 0) {
    return `All workers online, ${totalErrors.value} recent error${totalErrors.value === 1 ? '' : 's'}`
  }
  
  if (activeWorkersCount.value === total) {
    return `All ${total} worker${total === 1 ? '' : 's'} operational`
  }
  
  return `${activeWorkersCount.value} of ${total} workers online`
})

const summaryClasses = computed(() => {
  const classes = ['bg-background-surface']
  
  // Critical: Any workers offline
  if (offlineWorkersCount.value > 0) {
    classes.push('bg-gradient-to-r from-card-base to-status-error/5')
  }
  // Warning: High error rate
  else if (totalErrors.value > 0) {
    classes.push('bg-gradient-to-r from-card-base to-status-warning/5')
  }
  
  return classes.join(' ')
})
</script>

<style scoped>
/* Glow effects are now handled by global CSS utilities */
</style>
