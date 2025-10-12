<template>
  <div
    class="group relative bg-background-surface border border-border rounded-lg p-4 transition-all duration-200 hover:bg-background-raised cursor-pointer flex flex-col"
    @click="$emit('click')"
  >
    <!-- Task Name & Last Seen -->
    <div class="flex items-start justify-between mb-3">
      <div class="flex-1 min-w-0">
        <h3 class="text-sm font-mono font-medium text-text-primary truncate mb-1">
          {{ task.human_readable_name || task.name }}
        </h3>
        <p v-if="task.description" class="text-xs text-text-muted line-clamp-2">
          {{ task.description }}
        </p>
      </div>
      <div class="ml-2 text-xs font-mono text-text-muted whitespace-nowrap flex items-center gap-1">
        <Clock class="h-3 w-3" />
        {{ formatLastSeen(task.last_seen) }}
      </div>
    </div>

    <!-- Frequency Timeline -->
    <div class="mb-4">
      <TaskFrequencyTimeline
        v-if="timeline && timeline.buckets"
        :buckets="timeline.buckets"
      />
      <div v-else class="h-12 bg-background-base rounded-md animate-pulse"></div>
    </div>

    <!-- Stats Grid -->
    <div class="grid grid-cols-5 gap-2 mb-3 font-mono text-xs">
      <div class="text-center">
        <div class="text-text-muted uppercase mb-1">Exec</div>
        <div class="text-text-primary font-bold">
          {{ formatNumber(stats?.total_executions || 0) }}
        </div>
      </div>
      <div class="text-center">
        <div class="text-text-muted uppercase mb-1">OK</div>
        <div class="text-status-success font-bold">
          {{ formatNumber(stats?.succeeded || 0) }}
        </div>
      </div>
      <div class="text-center">
        <div class="text-text-muted uppercase mb-1">Fail</div>
        <div class="text-status-error font-bold">
          {{ formatNumber(stats?.failed || 0) }}
        </div>
      </div>
      <div class="text-center">
        <div class="text-text-muted uppercase mb-1">Retry</div>
        <div class="text-status-warning font-bold">
          {{ formatNumber(stats?.retried || 0) }}
        </div>
      </div>
      <div class="text-center">
        <div class="text-text-muted uppercase mb-1">Avg</div>
        <div class="text-text-primary font-bold">
          {{ formatRuntime(stats?.avg_runtime) }}
        </div>
      </div>
    </div>

    <!-- Critical Failures Alert -->
    <Alert
      v-if="criticalFailures > 0"
      variant="error"
      size="sm"
      class="mb-3"
    >
      {{ criticalFailures }} unretried failure{{ criticalFailures > 1 ? 's' : '' }}
    </Alert>

    <!-- Spacer to push tags to bottom -->
    <div class="flex-1"></div>

    <!-- Tags & View Details -->
    <div class="flex items-center justify-between">
      <div class="flex flex-wrap gap-1">
        <BaseTag
          v-for="tag in task.tags"
          :key="tag"
          size="xs"
          colored
          :text="tag"
        >
          {{ tag }}
        </BaseTag>
      </div>
      <button
        class="text-xs text-text-secondary group-hover:text-text-primary transition-colors font-medium"
      >
        → Details
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Clock } from 'lucide-vue-next'
import TaskFrequencyTimeline from './TaskFrequencyTimeline.vue'
import { BaseTag } from '~/components/ui/tag'
import { Alert } from '~/components/alert'
import type { TaskRegistryResponse, TaskRegistryStats, TaskTimelineResponse } from '~/services/apiClient'

interface Props {
  task: TaskRegistryResponse
}

const props = defineProps<Props>()
defineEmits(['click'])

const taskRegistryStore = useTaskRegistryStore()
const stats = ref<TaskRegistryStats | null>(null)
const timeline = ref<TaskTimelineResponse | null>(null)

// Critical failures: tasks that failed with no successful retry in the chain
// The 'failed' stat already represents terminal failures (max retries exceeded or no retry configured)
// If a retry succeeded, the original task wouldn't be counted in 'failed'
const criticalFailures = computed(() => {
  if (!stats.value) return 0
  return stats.value.failed || 0
})

// Format helpers
function formatLastSeen(dateStr: string) {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))

  if (diffMinutes < 1) return 'now'
  if (diffMinutes < 60) return `${diffMinutes}m`
  if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}h`
  return `${Math.floor(diffMinutes / 1440)}d`
}

function formatNumber(num: number) {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
  return num.toString()
}

function formatRuntime(runtime: number | null | undefined) {
  if (!runtime) return '-'
  if (runtime < 1) return `${Math.round(runtime * 1000)}ms`
  return `${runtime.toFixed(1)}s`
}

// Load stats and timeline on mount
onMounted(async () => {
  const [statsData, timelineData] = await Promise.all([
    taskRegistryStore.fetchTaskStats(props.task.name, 24),
    taskRegistryStore.fetchTaskTimeline(props.task.name, 24, 60) // 24 hours, 1-hour buckets
  ])

  stats.value = statsData
  timeline.value = timelineData
})
</script>
