<script setup lang="ts">
import { ref } from 'vue'
import ConfirmationDialog from '~/components/ConfirmationDialog.vue'
import TaskName from '~/components/TaskName.vue'
import CopyButton from '~/components/CopyButton.vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Pill } from '~/components/ui/pill'
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
  confirm: []
  cancel: []
}>()

const confirmationDialogRef = ref<InstanceType<typeof ConfirmationDialog> | null>(null)

const open = () => {
  confirmationDialogRef.value?.open()
}

const handleConfirm = () => {
  emit('confirm')
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
            <code class="text-sm bg-background-primary px-2 py-1 rounded font-mono">{{ task.task_id.slice(0, 12) }}...</code>
            <CopyButton 
              :text="task.task_id" 
              :copy-key="`retry-dialog-${task.task_id}`"
              title="Copy full task ID"
            />
          </div>
        </div>
        
        <!-- Task status info -->
        <div class="flex items-center justify-center gap-3">
          <Badge :variant="getStatusBadge(task).variant">
            {{ getStatusBadge(task).text }}
          </Badge>
          <template v-if="getTimestamp(task)">
            <span class="text-text-tertiary text-xs">at</span>
            <Pill variant="subtle" size="sm" class="font-mono text-xs">
              {{ formatTime(getTimestamp(task)) }}
            </Pill>
          </template>
        </div>
        
        <!-- Warning about what will happen -->
        <Alert variant="warning" title="This will create a new task instance">
          The task will be re-queued and executed again by an available worker.
        </Alert>
      </div>
    </template>
  </ConfirmationDialog>
</template>
