<template>
  <div class="space-y-2">
    <!-- Timeline label -->
    <div class="flex items-center justify-between text-xs font-mono text-text-muted">
      <span>24H ACTIVITY</span>
      <span v-if="maxExecutions > 0">{{ maxExecutions }} peak</span>
    </div>

    <!-- Timeline bars -->
    <TooltipProvider :delay-duration="200">
      <div class="relative h-12 flex items-end gap-[2px] bg-background-base rounded-md px-2 pt-2">
        <TooltipRoot
          v-for="(bucket, index) in buckets"
          :key="index"
          :disabled="bucket.total_executions === 0"
        >
          <TooltipTrigger as-child>
            <div class="flex-1 h-full flex flex-col justify-end">
              <!-- Stacked Bar -->
              <div
                class="w-full flex flex-col-reverse rounded-t-sm overflow-hidden transition-all duration-200"
                :style="{ height: getTotalBarHeight(bucket) }"
              >
                <!-- Success segment (bottom) -->
                <div
                  v-if="bucket.succeeded > 0"
                  class="w-full bg-status-success opacity-80 hover:opacity-100 transition-opacity"
                  :style="{ height: getSegmentHeight(bucket, bucket.succeeded) }"
                />
                <!-- Retry segment (middle) -->
                <div
                  v-if="bucket.retried > 0"
                  class="w-full bg-status-warning opacity-80 hover:opacity-100 transition-opacity"
                  :style="{ height: getSegmentHeight(bucket, bucket.retried) }"
                />
                <!-- Failed segment (top) -->
                <div
                  v-if="bucket.failed > 0"
                  class="w-full bg-status-error opacity-80 hover:opacity-100 transition-opacity"
                  :style="{ height: getSegmentHeight(bucket, bucket.failed) }"
                />
                <!-- Empty state -->
                <div
                  v-if="bucket.total_executions === 0"
                  class="w-full bg-background-raised opacity-50 h-[4%]"
                />
              </div>
            </div>
          </TooltipTrigger>
          <TooltipContent
            v-if="bucket.total_executions > 0"
            side="top"
            class="bg-background-surface border border-border text-text-primary"
          >
            <div class="space-y-2">
              <div class="font-mono text-xs font-medium">
                {{ formatTime(bucket.timestamp) }}
              </div>
              <div class="space-y-1 text-xs">
                <div class="flex items-center gap-2">
                  <StatusDot status="success" />
                  <span class="text-text-secondary">{{ bucket.succeeded }} succeeded</span>
                </div>
                <div v-if="bucket.failed > 0" class="flex items-center gap-2">
                  <StatusDot status="error" />
                  <span class="text-text-secondary">{{ bucket.failed }} failed</span>
                </div>
                <div v-if="bucket.retried > 0" class="flex items-center gap-2">
                  <StatusDot status="warning" />
                  <span class="text-text-secondary">{{ bucket.retried }} retried</span>
                </div>
              </div>
              <div class="pt-1 border-t border-border font-mono text-xs font-bold">
                {{ bucket.total_executions }} total
              </div>
            </div>
          </TooltipContent>
        </TooltipRoot>
      </div>
    </TooltipProvider>

    <!-- Time labels -->
    <div class="flex justify-between text-[10px] font-mono text-text-muted">
      <span>24h ago</span>
      <span>12h</span>
      <span>now</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { TooltipRoot, TooltipContent, TooltipProvider, TooltipTrigger } from '~/components/ui/tooltip'
import StatusDot from '~/components/StatusDot.vue'
import type { TimelineBucket } from '~/services/apiClient'

interface Props {
  buckets: TimelineBucket[]
}

const props = defineProps<Props>()

// Calculate max executions for scaling
const maxExecutions = computed(() => {
  if (!props.buckets || props.buckets.length === 0) return 0
  return Math.max(...props.buckets.map(b => b.total_executions))
})

function getTotalBarHeight(bucket: TimelineBucket) {
  if (maxExecutions.value === 0 || bucket.total_executions === 0) {
    return '4%' // Minimum for empty state visibility
  }
  const percentage = (bucket.total_executions / maxExecutions.value) * 100
  return `${Math.max(percentage, 4)}%` // Minimum 4% for visibility
}

function getSegmentHeight(bucket: TimelineBucket, count: number) {
  if (bucket.total_executions === 0) return '0%'
  const percentage = (count / bucket.total_executions) * 100
  return `${percentage}%`
}

// Format timestamp for tooltip
function formatTime(timestamp: string) {
  const date = new Date(timestamp)
  const now = new Date()
  const diffHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60))

  if (diffHours === 0) {
    return 'Now'
  } else if (diffHours === 1) {
    return '1h ago'
  } else {
    return `${diffHours}h ago`
  }
}
</script>
