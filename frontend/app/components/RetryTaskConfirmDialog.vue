<script setup lang="ts">
import { computed, ref } from 'vue'
import ConfirmationDialog from '~/components/ConfirmationDialog.vue'
import TaskName from '~/components/TaskName.vue'
import CopyButton from '~/components/CopyButton.vue'
import UuidDisplay from '~/components/UuidDisplay.vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import Pill from '~/components/common/Pill.vue'
import { Alert } from '~/components/alert'
import { formatTime } from '~/composables/useDateTimeFormatters'
import type { TaskEventResponse } from '../src/types/api'

interface Props {
  task: TaskEventResponse | null
  isLoading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isLoading: false
})

const emit = defineEmits<{
  confirm: [policy: Record<string, unknown>]
  cancel: []
}>()

const confirmationDialogRef = ref<InstanceType<typeof ConfirmationDialog> | null>(null)
const tasksStore = useTasksStore()
const mode = ref<'immediate' | 'delayed'>('immediate')
const delaySeconds = ref(300)
const maxAttempts = ref(3)
const operatorComment = ref('')
const preview = ref<any>(null)
const isPreviewLoading = ref(false)

const retryPolicy = computed(() => ({
  mode: mode.value,
  delay_seconds: mode.value === 'delayed' ? delaySeconds.value : 0,
  max_attempts: maxAttempts.value,
  operator_comment: operatorComment.value || null,
}))

const loadPreview = async () => {
  if (!props.task?.task_id) return
  isPreviewLoading.value = true
  try {
    preview.value = await tasksStore.getRetryPreview(props.task.task_id, maxAttempts.value)
  } finally {
    isPreviewLoading.value = false
  }
}

const open = async () => {
  await loadPreview()
  confirmationDialogRef.value?.open()
}

const handleConfirm = () => {
  emit('confirm', retryPolicy.value)
}

const handleCancel = () => {
  emit('cancel')
}

const getStatusBadge = (task: TaskEventResponse) => {
  if (task.is_orphan) {
    return { variant: 'revoked' as const, text: 'Orphaned' }
  }
  
  const { eventTypeToStatus, getStatusVariant, formatStatus } = useTaskStatus()
  const status = eventTypeToStatus(task.event_type)
  return {
    variant: getStatusVariant(status),
    text: formatStatus(status)
  }
}

const getTimestamp = (task: TaskEventResponse) => {
  return task.orphaned_at || task.timestamp
}

defineExpose({ open })
</script>

<template>
  <ConfirmationDialog
    ref="confirmationDialogRef"
    title="Retry Task"
    confirm-text="Retry Task"
    cancel-text="Cancel"
    :is-loading="isLoading"
    @confirm="handleConfirm"
    @cancel="handleCancel"
  >
    <template #trigger>
      <Button style="display: none;" />
    </template>
    
    <template #content>
      <div v-if="task" class="space-y-4">
        <!-- Task identification -->
        <div class="text-center">
          <div class="mb-2">
            <TaskName 
              :name="task.task_name || 'Unknown Task'" 
              size="lg" 
              :max-length="50"
              :expandable="true"
            />
          </div>
          <div class="flex items-center justify-center gap-2 text-text-secondary">
            <UuidDisplay
              :uuid="task.task_id"
              :show-copy="true"
              :show-copy-text="false"
              copy-title="Copy full task ID"
              :truncate-length="12"
              size="sm"
            />
          </div>
        </div>
        
        <!-- Task status info -->
        <div class="flex items-center justify-center gap-3">
          <Badge :variant="getStatusBadge(task).variant">
            {{ getStatusBadge(task).text }}
          </Badge>
          <template v-if="getTimestamp(task)">
            <span class="text-text-muted text-xs">at</span>
            <Pill variant="subtle" size="sm" class="font-mono text-xs">
              {{ formatTime(getTimestamp(task)) }}
            </Pill>
          </template>
        </div>
        
        <!-- Warning about what will happen -->
        <Alert variant="warning" title="This will create a new task instance">
          The task will be re-queued and executed again by an available worker.
        </Alert>

        <div class="rounded-lg border border-border bg-background-muted/30 p-4 space-y-3 text-sm">
          <div class="flex items-center justify-between gap-3">
            <label class="text-text-secondary">Retry mode</label>
            <select v-model="mode" class="rounded-md border border-border bg-background-base px-3 py-2 text-text-primary">
              <option value="immediate">Immediate</option>
              <option value="delayed">Delayed</option>
            </select>
          </div>

          <div v-if="mode === 'delayed'" class="flex items-center justify-between gap-3">
            <label class="text-text-secondary">Delay seconds</label>
            <input v-model.number="delaySeconds" type="number" min="1" max="86400" class="w-32 rounded-md border border-border bg-background-base px-3 py-2 text-right text-text-primary" />
          </div>

          <div class="flex items-center justify-between gap-3">
            <label class="text-text-secondary">Cap attempts</label>
            <input v-model.number="maxAttempts" type="number" min="1" max="25" @change="loadPreview" class="w-24 rounded-md border border-border bg-background-base px-3 py-2 text-right text-text-primary" />
          </div>

          <textarea v-model="operatorComment" rows="2" maxlength="500" placeholder="Operator comment (optional)" class="w-full rounded-md border border-border bg-background-base px-3 py-2 text-text-primary placeholder:text-text-muted" />
        </div>

        <div v-if="preview" class="rounded-lg border border-border p-4 space-y-2 text-sm">
          <div class="font-medium text-text-primary">Retry-chain impact</div>
          <p class="text-text-secondary">
            {{ preview.retry_count }} existing retry attempt(s), {{ preview.remaining_attempts }} remaining under cap {{ preview.max_attempts }}.
          </p>
          <Alert
            v-for="warning in preview.warnings"
            :key="warning.code"
            :variant="warning.severity === 'critical' ? 'error' : 'warning'"
            :title="warning.code.replaceAll('_', ' ')"
          >
            {{ warning.message }}
          </Alert>
        </div>

        <p v-else-if="isPreviewLoading" class="text-sm text-text-muted">Loading retry impact preview…</p>
      </div>
    </template>
  </ConfirmationDialog>
</template>
