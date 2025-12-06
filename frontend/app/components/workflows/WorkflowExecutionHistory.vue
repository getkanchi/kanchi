<template>
  <div>
    <!-- Loading State -->
    <div v-if="workflowStore.isLoading" class="space-y-3">
      <div v-for="i in 3" :key="i" class="h-32 bg-background-surface border border-border-subtle rounded-lg animate-pulse" />
    </div>

    <!-- Empty State -->
    <div v-else-if="workflowStore.executions.length === 0" class="text-center py-16 bg-background-surface border border-border-subtle rounded-lg">
      <History class="h-12 w-12 text-text-muted mx-auto mb-4 opacity-50" />
      <h3 class="text-sm font-medium text-text-primary mb-2">No executions yet</h3>
      <p class="text-xs text-text-muted">This workflow hasn't been triggered</p>
    </div>

    <!-- Executions List -->
    <div v-else class="space-y-3">
      <div
        v-for="execution in workflowStore.executions"
        :key="execution.id"
        class="bg-background-surface border border-border-subtle rounded-lg overflow-hidden"
      >
        <!-- Execution Header -->
        <div
          class="p-4 cursor-pointer hover:bg-background-hover-subtle transition-colors"
          @click="toggleExecution(execution.id)"
        >
          <div class="flex items-start justify-between gap-4">
            <div class="flex items-start gap-3 flex-1 min-w-0">
              <!-- Status Icon -->
              <div class="mt-1">
                <CheckCircle2 v-if="execution.status === 'completed'" class="h-5 w-5 text-status-success" />
                <XCircle v-else-if="execution.status === 'failed'" class="h-5 w-5 text-status-error" />
                <AlertCircle v-else-if="execution.status === 'rate_limited'" class="h-5 w-5 text-status-warning" />
                <Loader2 v-else class="h-5 w-5 text-primary animate-spin" />
              </div>

              <!-- Execution Info -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1">
                  <span class="text-sm font-medium text-text-primary">
                    {{ formatRelativeTime(execution.triggered_at) }}
                  </span>
                  <Badge
                    :variant="getStatusVariant(execution.status)"
                    size="sm"
                  >
                    {{ execution.status }}
                  </Badge>
                  <span v-if="execution.duration_ms" class="text-xs text-text-muted">
                    {{ execution.duration_ms }}ms
                  </span>
                </div>

                <div class="text-xs text-text-secondary">
                  Triggered by: <span class="font-mono">{{ execution.trigger_type }}</span>
                  <span v-if="execution.actions_executed">
                    • {{ execution.actions_executed.length }} action{{ execution.actions_executed.length !== 1 ? 's' : '' }} executed
                  </span>
                </div>
              </div>
            </div>

            <!-- Expand Icon -->
            <ChevronDown
              :class="[
                'h-5 w-5 text-text-muted transition-transform',
                expandedExecutions.has(execution.id) ? 'transform rotate-180' : ''
              ]"
            />
          </div>
        </div>

        <!-- Execution Details (Expanded) -->
        <div
          v-if="expandedExecutions.has(execution.id)"
          class="border-t border-border-subtle p-4 bg-background-base space-y-4"
        >
          <!-- Trigger Event -->
          <div>
            <div class="text-xs font-semibold text-text-muted uppercase tracking-wide mb-2">
              Trigger Event
            </div>
            <div class="bg-background-surface border border-border-subtle rounded p-3 font-mono text-xs overflow-x-auto">
              <pre>{{ JSON.stringify(execution.trigger_event, null, 2) }}</pre>
            </div>
          </div>

          <!-- Actions Executed -->
          <div v-if="execution.actions_executed && execution.actions_executed.length > 0">
            <div class="text-xs font-semibold text-text-muted uppercase tracking-wide mb-2">
              Actions Executed
            </div>
            <div class="space-y-2">
              <div
                v-for="(action, idx) in execution.actions_executed"
                :key="idx"
                class="border border-border-subtle rounded-lg p-3"
              >
                <div class="flex items-start justify-between gap-3 mb-2">
                  <div class="flex items-center gap-2">
                    <span class="text-xs text-text-muted">{{ idx + 1 }}.</span>
                    <Badge variant="outline" size="sm">{{ action.action_type }}</Badge>
                    <Badge
                      :variant="action.status === 'success' ? 'default' : 'destructive'"
                      size="sm"
                    >
                      {{ action.status }}
                    </Badge>
                  </div>
                  <span class="text-xs text-text-muted">{{ action.duration_ms }}ms</span>
                </div>

                <div v-if="action.result" class="text-xs bg-background-base p-2 rounded font-mono">
                  {{ JSON.stringify(action.result) }}
                </div>

                <div v-if="action.error_message" class="text-xs text-status-error mt-2">
                  Error: {{ action.error_message }}
                </div>
              </div>
            </div>
          </div>

          <!-- Error Details -->
          <div v-if="execution.error_message">
            <div class="text-xs font-semibold text-text-muted uppercase tracking-wide mb-2">
              Error
            </div>
            <div class="bg-status-error-bg border border-status-error-border rounded p-3">
              <p class="text-xs text-status-error font-medium mb-2">
                {{ execution.error_message }}
              </p>
              <pre v-if="execution.stack_trace" class="text-xs text-status-error opacity-75 overflow-x-auto">{{ execution.stack_trace }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2,
  ChevronDown,
  History
} from 'lucide-vue-next'
import { Badge } from '~/components/ui/badge'

const props = defineProps<{
  workflowId: string
}>()

const workflowStore = useWorkflowsStore()
const expandedExecutions = ref(new Set<number>())

function toggleExecution(executionId: number) {
  if (expandedExecutions.value.has(executionId)) {
    expandedExecutions.value.delete(executionId)
  } else {
    expandedExecutions.value.add(executionId)
  }
}

function getStatusVariant(status: string): any {
  switch (status) {
    case 'completed':
      return 'default'
    case 'failed':
      return 'destructive'
    case 'rate_limited':
      return 'secondary'
    default:
      return 'outline'
  }
}

function formatRelativeTime(timestamp: string): string {
  const now = new Date()
  const then = new Date(timestamp)
  const diff = now.getTime() - then.getTime()

  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (days > 0) return `${days}d ago`
  if (hours > 0) return `${hours}h ago`
  if (minutes > 0) return `${minutes}m ago`
  if (seconds > 10) return `${seconds}s ago`
  return 'just now'
}

onMounted(async () => {
  await workflowStore.fetchWorkflowExecutions(props.workflowId, { limit: 50 })
})
</script>
