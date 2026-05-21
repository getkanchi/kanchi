<script setup lang="ts">
import { computed, watch } from 'vue'
import { AlertTriangle, ChevronRight, Info, RefreshCw } from 'lucide-vue-next'
import TaskName from '~/components/TaskName.vue'
import UuidDisplay from '~/components/UuidDisplay.vue'
import { Alert } from '~/components/alert'
import { Badge } from '~/components/ui/badge'
import { Button } from '~/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '~/components/ui/dialog'
import {
  TooltipContent,
  TooltipProvider,
  TooltipRoot,
  TooltipTrigger,
} from '~/components/ui/tooltip'
import type { RerunPreflightResponseDTO, TaskEventResponse } from '~/services/apiClient'

const props = withDefaults(defineProps<{
  open: boolean
  taskIds: string[]
  tasks?: TaskEventResponse[]
  preflight?: RerunPreflightResponseDTO | null
  isLoading?: boolean
  isPreflighting?: boolean
}>(), {
  tasks: () => [],
  preflight: null,
  isLoading: false,
  isPreflighting: false,
})

const emit = defineEmits<{
  'update:open': [open: boolean]
  preflight: []
  confirm: []
  cancel: []
}>()

const { eventTypeToStatus, getStatusVariant, formatStatus } = useTaskStatus()

const taskMap = computed(() => new Map(props.tasks.map(task => [task.task_id, task])))
const items = computed(() => props.preflight?.items || [])
const readyItems = computed(() => items.value.filter(item => item.ready))
const unavailableItems = computed(() => items.value.filter(item => !item.ready))
const canConfirm = computed(() => readyItems.value.length > 0 && !props.isLoading && !props.isPreflighting)

const groupedUnavailable = computed(() => {
  const groups = new Map<string, { reason: string; count: number }>()
  unavailableItems.value.forEach(item => {
    const key = item.reason_code || 'unavailable'
    const existing = groups.get(key) || { reason: item.reason || 'Unavailable', count: 0 }
    existing.count += 1
    groups.set(key, existing)
  })
  return Array.from(groups.entries()).map(([code, value]) => ({ code, ...value }))
})

function taskFor(item: { task_id: string; task?: TaskEventResponse | null }) {
  return item.task || taskMap.value.get(item.task_id) || null
}

function statusMeta(task: TaskEventResponse | null) {
  if (!task) return { label: 'Unknown', variant: 'outline' as const }
  if (task.is_orphan) return { label: 'Orphaned', variant: 'orphaned' as const }
  const status = eventTypeToStatus(task.event_type || 'unknown')
  return {
    label: formatStatus(status),
    variant: getStatusVariant(status),
  }
}

function handleOpenChange(next: boolean) {
  if (props.isLoading) return
  emit('update:open', next)
  if (!next) emit('cancel')
}

watch(() => props.open, (next) => {
  if (next && props.taskIds.length > 0) {
    emit('preflight')
  }
})
</script>

<template>
  <Dialog :open="open" @update:open="handleOpenChange">
    <DialogContent class="sm:max-w-2xl">
      <DialogHeader>
        <DialogTitle class="flex items-center gap-2">
          <RefreshCw class="h-4 w-4 text-primary" />
          Rerun task{{ taskIds.length === 1 ? '' : 's' }}
          <TooltipProvider :delay-duration="150">
            <TooltipRoot>
              <TooltipTrigger as-child>
                <button
                  type="button"
                  class="inline-flex h-6 w-6 items-center justify-center rounded border border-border-subtle bg-background-raised text-text-muted transition-colors hover:bg-background-hover-subtle hover:text-text-primary"
                  aria-label="Rerun help"
                >
                  <Info class="h-3.5 w-3.5" />
                </button>
              </TooltipTrigger>
              <TooltipContent class="max-w-xs text-left leading-relaxed">
                Rerun creates new task executions from Kanchi's captured task name and arguments.
                Ready tasks can be re-queued. Unavailable tasks are missing usable captured data or
                cannot be sent, and are recorded as skipped.
              </TooltipContent>
            </TooltipRoot>
          </TooltipProvider>
        </DialogTitle>
        <DialogDescription class="text-left">
          This creates new executions with the captured task name and parameters.
        </DialogDescription>
      </DialogHeader>

      <div class="space-y-4">
        <div
          v-if="isPreflighting"
          class="rounded-md border border-border-subtle bg-background-surface p-4 text-sm text-text-secondary"
        >
          Checking captured data...
        </div>

        <template v-else-if="preflight">
          <div class="grid gap-3 sm:grid-cols-2">
            <div class="rounded-md border border-status-success-border bg-status-success-bg/40 p-3">
              <div class="text-2xl font-semibold text-status-success">{{ preflight.ready_count }}</div>
              <div class="text-xs text-text-secondary">ready to rerun</div>
            </div>
            <div class="rounded-md border border-status-warning-border bg-status-warning-bg/30 p-3">
              <div class="text-2xl font-semibold text-status-warning">{{ preflight.unavailable_count }}</div>
              <div class="text-xs text-text-secondary">unavailable</div>
            </div>
          </div>

          <Alert v-if="preflight.ready_count === 0" variant="warning" title="No tasks can be rerun">
            Kanchi cannot reconstruct the selected task{{ taskIds.length === 1 ? '' : 's' }} from captured data.
          </Alert>
          <Alert v-else-if="preflight.unavailable_count > 0" variant="warning" title="Partial rerun">
            Rerunnable tasks will proceed. Unavailable selected tasks will be recorded as skipped.
          </Alert>

          <div v-if="groupedUnavailable.length" class="space-y-1 text-xs text-text-secondary">
            <div v-for="group in groupedUnavailable" :key="group.code" class="flex justify-between rounded border border-border-subtle px-3 py-2">
              <span>{{ group.reason }}</span>
              <span class="font-mono">{{ group.count }}</span>
            </div>
          </div>

          <div class="max-h-80 space-y-2 overflow-y-auto pr-1">
            <div
              v-for="item in items"
              :key="item.task_id"
              class="flex items-center justify-between gap-3 rounded-md border border-border-subtle bg-background-surface px-3 py-2"
            >
              <div class="min-w-0 flex-1">
                <div class="flex flex-wrap items-center gap-2">
                  <TaskName :name="item.task_name || taskFor(item)?.task_name || 'Unknown task'" size="sm" :max-length="42" />
                  <Badge :variant="statusMeta(taskFor(item)).variant" class="text-[11px]">
                    {{ statusMeta(taskFor(item)).label }}
                  </Badge>
                  <Badge v-if="item.ready" variant="success" class="text-[11px]">Ready</Badge>
                  <Badge v-else variant="pending" class="text-[11px]">Skipped</Badge>
                </div>
                <div class="mt-1 flex items-center gap-2 text-xs text-text-muted">
                  <UuidDisplay :uuid="item.task_id" :truncate-length="12" size="sm" />
                  <span v-if="!item.ready && item.reason">{{ item.reason }}</span>
                </div>
              </div>
              <NuxtLink :to="`/tasks/${item.task_id}`">
                <Button variant="outline" size="xs" class="gap-1">
                  <ChevronRight class="h-3.5 w-3.5" />
                  Open
                </Button>
              </NuxtLink>
            </div>
          </div>
        </template>

        <Alert v-else variant="warning" title="No preflight result">
          <span class="flex items-center gap-2">
            <AlertTriangle class="h-3.5 w-3.5" />
            Rerun availability has not been checked yet.
          </span>
        </Alert>
      </div>

      <DialogFooter class="gap-2">
        <Button variant="outline" :disabled="isLoading" @click="handleOpenChange(false)">
          Cancel
        </Button>
        <Button variant="outline" class="gap-2" :disabled="!canConfirm" @click="emit('confirm')">
          <RefreshCw v-if="isLoading" class="h-4 w-4 animate-spin" />
          Rerun
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
