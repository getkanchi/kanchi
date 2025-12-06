<template>
  <div class="bg-background-base border border-red-900/20 rounded p-2 space-y-1.5 text-xs">
    <!-- Compact header -->
    <div class="flex items-center justify-between gap-2">
      <div class="flex items-center gap-2 font-mono min-w-0 flex-1">
        <UuidDisplay :uuid="failure.task_id" :truncate-length="8" :show-copy="false" />
        <span class="text-text-muted truncate">{{ formatRelativeTime(failure.timestamp) }}</span>
        <span v-if="failure.hostname" class="text-text-muted truncate text-[10px]">@ {{ failure.hostname }}</span>
      </div>
      <div class="flex items-center gap-0.5 flex-shrink-0">
        <IconButton
          :icon="RefreshCw"
          size="xs"
          variant="ghost"
          @click.stop="handleRetry"
        />
        <button @click.stop="expanded = !expanded" class="p-1 hover:bg-background-hover rounded transition-colors">
          <ChevronRight v-if="!expanded" class="h-3 w-3 text-text-muted" />
          <ChevronDown v-else class="h-3 w-3 text-text-muted" />
        </button>
      </div>
    </div>

    <!-- Error preview (collapsed) -->
    <div v-if="!expanded" class="text-red-400 font-mono truncate text-[11px] leading-tight">
      {{ getErrorPreview(failure.traceback || failure.exception) }}
    </div>

    <!-- Expanded details -->
    <div v-else class="space-y-2 pt-1 border-t border-red-900/10">
      <!-- Traceback -->
      <div v-if="failure.traceback" class="p-2 border border-red-900/20 rounded bg-red-950/20">
        <div class="flex items-center justify-between mb-1.5">
          <h5 class="text-[10px] font-medium text-red-400 uppercase tracking-wide">Error</h5>
          <CopyButton
            :text="failure.traceback"
            :copy-key="`tb-${failure.task_id}`"
            :show-text="false"
          />
        </div>
        <pre class="text-[10px] text-red-400 font-mono overflow-x-auto max-h-24 leading-tight whitespace-pre-wrap break-all">{{ failure.traceback }}</pre>
      </div>

      <!-- Args/Kwargs - inline compact -->
      <div v-if="failure.args || failure.kwargs" class="grid grid-cols-2 gap-2">
        <div v-if="failure.args" class="p-1.5 border border-border-subtle rounded bg-background-surface">
          <div class="text-[9px] text-text-muted uppercase tracking-wide mb-0.5">Args</div>
          <div class="text-[10px] font-mono text-text-primary truncate">{{ formatValue(failure.args) }}</div>
        </div>
        <div v-if="failure.kwargs" class="p-1.5 border border-border-subtle rounded bg-background-surface">
          <div class="text-[9px] text-text-muted uppercase tracking-wide mb-0.5">Kwargs</div>
          <div class="text-[10px] font-mono text-text-primary truncate">{{ formatValue(failure.kwargs) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { RefreshCw, ChevronRight, ChevronDown } from 'lucide-vue-next'
import UuidDisplay from './UuidDisplay.vue'
import CopyButton from './CopyButton.vue'
import IconButton from '~/components/common/IconButton.vue'
import type { TaskEventResponse } from '~/services/apiClient'

interface Props {
  failure: TaskEventResponse
}

const props = defineProps<Props>()
const emit = defineEmits<{
  retry: [taskId: string]
}>()

const expanded = ref(false)

function formatRelativeTime(timestamp: string) {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 1) return 'now'
  if (diffMins < 60) return `${diffMins}m ago`
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays}d ago`
}

function getErrorPreview(traceback: string | null | undefined): string {
  if (!traceback) return 'No error details available'

  const lines = traceback.split('\n').filter(l => l.trim())
  const lastLine = lines[lines.length - 1] || ''
  return lastLine.substring(0, 120)
}

function formatValue(value: any): string {
  if (!value) return '-'
  if (typeof value === 'string') return value
  if (typeof value === 'object') {
    const str = JSON.stringify(value)
    return str.length > 50 ? str.substring(0, 47) + '...' : str
  }
  return String(value)
}

function handleRetry() {
  emit('retry', props.failure.task_id)
}
</script>
