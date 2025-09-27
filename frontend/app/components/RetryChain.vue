<template>
  <div class="space-y-3">
    <h4 class="text-sm font-medium text-gray-300 mb-1">Retry Chain</h4>
    
    <!-- Compact Status Pills Chain -->
    <div class="flex items-center gap-1 flex-wrap text-xs font-mono">
      <!-- Parent Task -->
      <div 
        v-if="parentTask"
        class="flex items-center gap-1 group"
      >
        <StatusPill 
          :status="parentTask.status"
          :task-id="parentTask.task_id"
          :timestamp="parentTask.timestamp"
          label="Parent"
          :is-current="false"
        />
        <ArrowRight class="h-3 w-3 text-gray-600" />
      </div>
      
      <!-- Current Task (if it's a retry) -->
      <div 
        v-if="currentTask && currentTask.is_retry"
        class="flex items-center gap-1"
      >
        <StatusPill 
          :status="currentTask.status"
          :task-id="currentTask.task_id"
          :timestamp="currentTask.timestamp"
          :label="`Retry ${currentTask.retry_number || 1}`"
          :is-current="true"
        />
        <ArrowRight v-if="retries.length > 0" class="h-3 w-3 text-gray-600" />
      </div>
      
      <!-- Subsequent Retries -->
      <template v-for="(retry, index) in retries" :key="retry.task_id">
        <StatusPill 
          :status="retry.status"
          :task-id="retry.task_id"
          :timestamp="retry.timestamp"
          :label="`Retry ${retry.retry_number || index + 2}`"
          :is-current="false"
        />
        <ArrowRight v-if="index < retries.length - 1" class="h-3 w-3 text-gray-600" />
      </template>
    </div>
    
    <!-- Legacy details (optional, can be removed later) -->
    <div v-if="showDetails" class="space-y-2 text-sm mt-3 pt-3 border-t border-card-border">
      <div v-if="parentTask" class="flex items-center gap-2 text-gray-400">
        <ArrowUp class="h-3 w-3" />
        <span>Parent:</span>
        <code class="text-xs bg-background-primary px-1 py-0.5 rounded">
          {{ parentTask.task_id.substring(0, 12) }}...
        </code>
        <CopyButton :text="parentTask.task_id" :show-text="false" />
      </div>
      
      <div v-if="retries.length > 0" class="space-y-1">
        <div class="flex items-center gap-2 text-gray-400 mb-1">
          <ArrowDown class="h-3 w-3" />
          <span>{{ retries.length }} Retries</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { RefreshCw, ArrowRight, ArrowUp, ArrowDown } from 'lucide-vue-next'
import StatusPill from './StatusPill.vue'
import CopyButton from './CopyButton.vue'

interface Task {
  task_id: string
  status: string
  timestamp?: string
  is_retry?: boolean
  retry_of?: string
  retry_number?: number
  retried_by?: string[]
  has_retries?: boolean
  retry_count?: number
}

const props = defineProps<{
  currentTask: Task
  parentTask?: Task | null
  retries?: Task[] | null
  showDetails?: boolean
}>()

const retries = computed(() => props.retries || [])
</script>