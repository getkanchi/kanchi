<template>
  <div
    class="border border-border rounded-lg overflow-hidden glow-border transition-all duration-300"
    :class="summaryClasses"
  >
    <!-- Collapsed Summary -->
    <div
      class="py-2 px-4 cursor-pointer hover:bg-background-surface/5 transition-all duration-200"
      @click="toggleExpanded"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="flex items-center gap-2">
            <StatusDot
              :status="overallStatus"
              :pulse="recentFailureCount > 0"
            />
            <span class="font-medium text-sm">Failed tasks (24h)</span>
          </div>
          <div class="hidden sm:flex items-center gap-3 text-xs text-text-secondary">
            <span class="flex items-center gap-1">
              <span class="font-mono">{{ failedCount }}</span>
              <span>unresolved</span>
            </span>
            <span v-if="recentFailureCount > 0" class="flex items-center gap-1 text-status-error">
              <span class="font-mono">{{ recentFailureCount }}</span>
              <span>last hour</span>
            </span>
            <span v-if="latestFailure" class="flex items-center gap-1 text-text-muted">
              <span>latest</span>
              <TimeDisplay
                :timestamp="latestFailure.timestamp"
                :auto-refresh="true"
                :refresh-interval="60000"
              />
            </span>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <span v-if="isLoading" class="text-xs text-text-muted flex items-center gap-1">
            <Loader2 class="h-3.5 w-3.5 animate-spin" />
            Updating…
          </span>
          <span class="text-xs text-text-muted hidden sm:inline">
            {{ isExpanded ? 'Hide details' : 'View details' }}
          </span>
          <ChevronDown
            class="w-4 h-4 text-text-muted transition-transform duration-200"
            :class="{ 'rotate-180': isExpanded }"
          />
        </div>
      </div>

      <div v-if="!isExpanded" class="sm:hidden flex items-center gap-4 text-xs text-text-secondary mt-2 pt-2 border-t border-border/50">
        <span class="flex items-center gap-1">
          <span class="font-mono">{{ failedCount }}</span>
          <span>unresolved</span>
        </span>
        <span v-if="recentFailureCount > 0" class="flex items-center gap-1 text-status-error">
          <span class="font-mono">{{ recentFailureCount }}</span>
          <span>last hour</span>
        </span>
      </div>
    </div>

    <!-- Expanded Details -->
    <div
      v-if="isExpanded"
      class="border-t border-border bg-background-surface/40"
    >
      <div v-if="failedCount > 0" class="p-4 space-y-4">
        <div class="flex flex-wrap items-center justify-between gap-2 text-xs text-text-muted">
          <span>Showing {{ displayedFailures.length }} of {{ failedCount }} failed task{{ failedCount === 1 ? '' : 's' }}</span>
          <span v-if="latestFailure">
            Last failure
            <TimeDisplay
              :timestamp="latestFailure.timestamp"
              :auto-refresh="true"
              :refresh-interval="60000"
            />
          </span>
        </div>

        <div class="space-y-3">
          <div
            v-for="task in displayedFailures"
            :key="task.task_id"
            class="rounded-lg border border-border/60 bg-background-surface/60 px-4 py-3 flex flex-col gap-2"
          >
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div class="flex items-center gap-2">
                <Badge variant="destructive" class="text-[10px] tracking-wide font-medium">
                  FAILED
                </Badge>
                <TaskName
                  :name="task.task_name"
                  size="sm"
                  :max-length="32"
                  :expandable="true"
                />
                <Badge v-if="task.is_retry" variant="outline" class="text-[10px]">
                  Retry #{{ (task.retry_count || 0) }}
                </Badge>
              </div>
              <TimeDisplay
                :timestamp="task.timestamp"
                :auto-refresh="true"
                :refresh-interval="60000"
              />
            </div>

            <div class="grid gap-3 text-xs text-text-secondary sm:grid-cols-2 xl:grid-cols-3">
              <div class="flex items-center gap-2 font-mono">
                <UuidDisplay
                  :uuid="task.task_id"
                  :show-copy="true"
                  :show-copy-text="true"
                  copy-title="Copy task ID"
                  :truncate-length="12"
                />
              </div>
              <div class="flex items-center gap-2">
                <span class="text-text-muted">Worker</span>
                <span class="font-mono text-xs">{{ task.hostname || 'unknown' }}</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-text-muted">Queue</span>
                <span class="font-mono text-xs">{{ task.routing_key || 'default' }}</span>
              </div>
            </div>

            <div v-if="task.exception" class="rounded-md bg-status-error/10 border border-status-error/30 px-3 py-2">
              <p class="text-xs font-mono text-status-error line-clamp-3">
                {{ task.exception }}
              </p>
            </div>
            <div v-else class="text-xs text-text-muted">
              No exception payload reported.
            </div>
          </div>
        </div>
      </div>

      <div v-else class="text-center py-8">
        <div class="text-text-muted text-sm flex flex-col items-center gap-2">
          <svg class="w-8 h-8 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <p>No failed tasks detected in the last 24 hours</p>
          <p class="text-xs">New failures will appear here instantly.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import StatusDot from '~/components/StatusDot.vue'
import TaskName from '~/components/TaskName.vue'
import TimeDisplay from '~/components/TimeDisplay.vue'
import UuidDisplay from '~/components/UuidDisplay.vue'
import { Badge } from '@/components/ui/badge'
import type { TaskEventResponse } from '~/services/apiClient'
import { ChevronDown, Loader2 } from 'lucide-vue-next'

const props = defineProps<{
  failedTasks: TaskEventResponse[]
  isLoading?: boolean
}>()

const isExpanded = ref(false)

const toggleExpanded = () => {
  isExpanded.value = !isExpanded.value
}

const failedCount = computed(() => props.failedTasks.length)

const recentFailureCount = computed(() => {
  const oneHourAgo = Date.now() - 60 * 60 * 1000
  return props.failedTasks.filter(task => {
    if (!task.timestamp) return false
    const time = Date.parse(task.timestamp)
    return !Number.isNaN(time) && time >= oneHourAgo
  }).length
})

const latestFailure = computed(() => props.failedTasks[0] ?? null)

const displayedFailures = computed(() => props.failedTasks.slice(0, 15))

const overallStatus = computed((): 'success' | 'error' | 'info' => {
  return failedCount.value === 0 ? 'success' : 'error'
})

const summaryClasses = computed(() => {
  const classes = ['bg-background-surface']

  if (failedCount.value > 0) {
    classes.push('bg-gradient-to-r from-card-base to-status-error/5')
    classes.push('glow-border-error')
  }

  return classes.join(' ')
})
</script>
