<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
  AlertTriangle,
  Check,
  RefreshCw,
  RotateCcw,
  SkipForward,
  Undo2,
  Redo2,
  X,
} from 'lucide-vue-next'
import TaskName from '~/components/TaskName.vue'
import UuidDisplay from '~/components/UuidDisplay.vue'
import { Alert } from '~/components/alert'
import { Badge } from '~/components/ui/badge'
import { Button } from '~/components/ui/button'
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '~/components/ui/sheet'
import CopyButton from '~/components/CopyButton.vue'
import DataMetricStrip from '~/components/common/DataMetricStrip.vue'
import RerunInputEditor from './RerunInputEditor.vue'
import { containsTruncatedValue } from '~/utils/payload'
import type {
  RerunKind,
  RerunPreflightItemDTO,
  RerunPreflightResponseDTO,
  RerunSubmitItemDTO,
  TaskActionDetailDTO,
  TaskEventResponse,
} from '~/services/apiClient'

interface DraftSnapshot {
  args: any[]
  kwargs: Record<string, any>
  skipped: boolean
}

interface ReviewDraft extends DraftSnapshot {
  history: DraftSnapshot[]
  future: DraftSnapshot[]
}

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
  submitted: [detail: TaskActionDetailDTO]
  cancel: []
}>()

const taskActionsStore = useTaskActionsStore()
const { eventTypeToStatus, getStatusVariant, formatStatus } = useTaskStatus()

const focusedTaskId = ref<string | null>(null)
const drafts = ref<Record<string, ReviewDraft>>({})
const submitError = ref<string | null>(null)

const taskMap = computed(() => new Map(props.tasks.map(task => [task.task_id, task])))
const items = computed(() => props.preflight?.items || [])
const focusedItem = computed(() => items.value.find(item => item.task_id === focusedTaskId.value) || items.value[0] || null)
const focusedDraft = computed(() => focusedItem.value ? drafts.value[focusedItem.value.task_id] : null)
const isBusy = computed(() => props.isLoading || props.isPreflighting || taskActionsStore.isCreating)

const summary = computed(() => {
  const counts = {
    replay: 0,
    edited: 0,
    repaired: 0,
    userSkipped: 0,
    blocked: 0,
    failed: 0,
    needsAttention: 0,
    submitCount: 0,
  }

  items.value.forEach(item => {
    const draft = drafts.value[item.task_id]
    if (item.review_state === 'blocked') {
      counts.blocked += 1
      return
    }
    if (draft?.skipped) {
      counts.userSkipped += 1
      return
    }
    if (!draft || !isDraftValid(draft)) {
      counts.needsAttention += 1
      return
    }
    counts.submitCount += 1
    const kind = rerunKind(item, draft)
    if (kind === 'replay') counts.replay += 1
    if (kind === 'edited_override') counts.edited += 1
    if (kind === 'repaired_override') counts.repaired += 1
  })

  return counts
})

const canSubmit = computed(() =>
  Boolean(props.preflight)
  && summary.value.submitCount > 0
  && summary.value.needsAttention === 0
  && !isBusy.value
)
const summaryMetrics = computed(() => [
  { label: 'Ready as-is', value: summary.value.replay, tone: 'success' as const },
  { label: 'Edited', value: summary.value.edited, tone: 'primary' as const },
  { label: 'Fixed', value: summary.value.repaired, tone: 'success' as const },
  { label: 'Skipped by you', value: summary.value.userSkipped, tone: 'muted' as const },
  { label: 'Cannot rerun', value: summary.value.blocked, tone: 'warning' as const },
  { label: 'Send failed', value: summary.value.failed, tone: 'error' as const },
  { label: 'Needs input', value: summary.value.needsAttention, tone: 'warning' as const },
  { label: 'Will rerun', value: summary.value.submitCount, tone: 'primary' as const },
])

const isDirty = computed(() => items.value.some(item => isItemDirty(item)))

watch(() => props.open, (next) => {
  submitError.value = null
  if (next && props.taskIds.length > 0) {
    emit('preflight')
  }
})

watch(() => props.preflight, (preflight) => {
  if (!preflight) {
    drafts.value = {}
    focusedTaskId.value = null
    return
  }

  const nextDrafts: Record<string, ReviewDraft> = {}
  preflight.items.forEach(item => {
    nextDrafts[item.task_id] = makeDraft(item)
  })
  drafts.value = nextDrafts
  focusedTaskId.value =
    preflight.items.find(item => item.review_state === 'repairable')?.task_id
    || preflight.items[0]?.task_id
    || null
}, { deep: true })

function makeDraft(item: RerunPreflightItemDTO): ReviewDraft {
  return {
    args: clone(item.baseline?.args || []),
    kwargs: clone(item.baseline?.kwargs || {}),
    skipped: false,
    history: [],
    future: [],
  }
}

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value))
}

function stable(value: any) {
  return JSON.stringify(value)
}

function taskFor(item: RerunPreflightItemDTO | null) {
  if (!item) return null
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

function snapshot(draft: ReviewDraft): DraftSnapshot {
  return {
    args: clone(draft.args),
    kwargs: clone(draft.kwargs),
    skipped: draft.skipped,
  }
}

function applySnapshot(taskId: string, next: DraftSnapshot, recordHistory = true) {
  const draft = drafts.value[taskId]
  if (!draft) return
  if (recordHistory) {
    draft.history.push(snapshot(draft))
    draft.future = []
  }
  draft.args = clone(next.args)
  draft.kwargs = clone(next.kwargs)
  draft.skipped = next.skipped
}

function updateInputs(taskId: string, args: any[], kwargs: Record<string, any>) {
  const draft = drafts.value[taskId]
  if (!draft) return
  applySnapshot(taskId, { args, kwargs, skipped: draft.skipped })
}

function toggleSkip(item: RerunPreflightItemDTO) {
  const draft = drafts.value[item.task_id]
  if (!draft || item.review_state !== 'repairable' || items.value.length === 1) return
  applySnapshot(item.task_id, { args: draft.args, kwargs: draft.kwargs, skipped: !draft.skipped })
}

function resetTask(item: RerunPreflightItemDTO) {
  const draft = drafts.value[item.task_id]
  if (!draft) return
  applySnapshot(item.task_id, {
    args: clone(item.baseline.args),
    kwargs: clone(item.baseline.kwargs),
    skipped: false,
  })
}

function undo(taskId: string) {
  const draft = drafts.value[taskId]
  if (!draft || draft.history.length === 0) return
  draft.future.push(snapshot(draft))
  const previous = draft.history.pop()
  if (previous) applySnapshot(taskId, previous, false)
}

function redo(taskId: string) {
  const draft = drafts.value[taskId]
  if (!draft || draft.future.length === 0) return
  draft.history.push(snapshot(draft))
  const next = draft.future.pop()
  if (next) applySnapshot(taskId, next, false)
}

function isDraftValid(draft: ReviewDraft) {
  return Array.isArray(draft.args)
    && draft.kwargs
    && typeof draft.kwargs === 'object'
    && !Array.isArray(draft.kwargs)
    && !containsTruncatedValue(draft.args)
    && !containsTruncatedValue(draft.kwargs)
}

function hasInputChanges(item: RerunPreflightItemDTO, draft: ReviewDraft) {
  return stable(item.baseline.args) !== stable(draft.args)
    || stable(item.baseline.kwargs) !== stable(draft.kwargs)
}

function isItemDirty(item: RerunPreflightItemDTO) {
  const draft = drafts.value[item.task_id]
  if (!draft) return false
  return draft.skipped || hasInputChanges(item, draft)
}

function rerunKind(item: RerunPreflightItemDTO, draft: ReviewDraft): RerunKind {
  if (item.review_state === 'repairable') return 'repaired_override'
  return hasInputChanges(item, draft) ? 'edited_override' : 'replay'
}

function itemBadge(item: RerunPreflightItemDTO) {
  const draft = drafts.value[item.task_id]
  if (item.review_state === 'blocked') return { label: 'Cannot rerun', variant: 'destructive' as const }
  if (draft?.skipped) return { label: 'Skipped by you', variant: 'pending' as const }
  if (!draft || !isDraftValid(draft)) return { label: 'Needs input', variant: 'pending' as const }
  const kind = rerunKind(item, draft)
  if (kind === 'replay') return { label: 'Ready as-is', variant: 'success' as const }
  if (kind === 'edited_override') return { label: 'Edited', variant: 'default' as const }
  return { label: 'Fixed', variant: 'success' as const }
}

function baselineSourceLabel(source: string | null | undefined) {
  switch (source) {
    case 'submitted_rerun_inputs':
      return 'Inputs from previous rerun'
    case 'unparseable_observed_task_inputs':
      return 'Needs fresh inputs'
    case 'observed_task_inputs':
    default:
      return 'Observed from Celery'
  }
}

function requestClose() {
  if (isBusy.value) return
  if (isDirty.value && typeof window !== 'undefined') {
    const discard = window.confirm('Discard rerun review draft?')
    if (!discard) {
      emit('update:open', true)
      return
    }
  }
  emit('update:open', false)
  emit('cancel')
}

function effectiveInputsText(item: RerunPreflightItemDTO) {
  const draft = drafts.value[item.task_id]
  return JSON.stringify({ args: draft?.args || [], kwargs: draft?.kwargs || {} }, null, 2)
}

function inputDiffText(item: RerunPreflightItemDTO) {
  const draft = drafts.value[item.task_id]
  const diff = {
    args: !draft || stable(item.baseline.args) === stable(draft.args)
      ? null
      : { before: item.baseline.args, after: draft.args },
    kwargs: !draft || stable(item.baseline.kwargs) === stable(draft.kwargs)
      ? null
      : { before: item.baseline.kwargs, after: draft.kwargs },
  }
  return JSON.stringify(diff, null, 2)
}

function celerySnippetText(item: RerunPreflightItemDTO) {
  const draft = drafts.value[item.task_id]
  if (!draft || !item.target.task_name) return ''
  const queue = item.target.queue || item.target.routing_key || 'default'
  return `app.send_task(${pythonLiteral(item.target.task_name)}, args=${pythonLiteral(draft.args)}, kwargs=${pythonLiteral(draft.kwargs)}, queue=${pythonLiteral(queue)})`
}

function pythonLiteral(value: any): string {
  if (value === null) return 'None'
  if (typeof value === 'boolean') return value ? 'True' : 'False'
  if (typeof value === 'string') return JSON.stringify(value)
  if (typeof value === 'number') return String(value)
  if (Array.isArray(value)) return `[${value.map(pythonLiteral).join(', ')}]`
  if (value && typeof value === 'object') {
    return `{${Object.entries(value).map(([key, val]) => `${JSON.stringify(key)}: ${pythonLiteral(val)}`).join(', ')}}`
  }
  return JSON.stringify(value)
}

async function submitReview() {
  if (!canSubmit.value) return
  submitError.value = null
  const payload: RerunSubmitItemDTO[] = items.value.map(item => {
    const draft = drafts.value[item.task_id]
    if (item.review_state === 'blocked') {
      return {
        task_id: item.task_id,
        decision: 'blocked_skip',
        fingerprint: item.fingerprint || '',
      }
    }
    if (draft?.skipped) {
      return {
        task_id: item.task_id,
        decision: 'user_skip',
        fingerprint: item.fingerprint || '',
      }
    }
    return {
      task_id: item.task_id,
      decision: 'submit',
      fingerprint: item.fingerprint || '',
      args: draft?.args || [],
      kwargs: draft?.kwargs || {},
    }
  })

  try {
    const detail = await taskActionsStore.submitRerunReview(payload)
    emit('submitted', detail)
    emit('update:open', false)
  } catch (error) {
    submitError.value = error instanceof Error ? error.message : 'Kanchi could not submit this rerun.'
  }
}
</script>

<template>
  <Sheet :open="open" @update:open="(next) => next ? emit('update:open', true) : requestClose()">
    <SheetContent
      side="right"
      class="flex h-screen w-full max-w-full flex-col border-l border-border-subtle bg-background-base p-0 md:w-[1180px] md:max-w-[96vw]"
    >
      <SheetHeader class="border-b border-border-subtle bg-background-surface px-5 py-4">
        <div class="flex items-center justify-between gap-3">
          <SheetTitle class="flex min-w-0 items-center gap-2">
            <RefreshCw class="h-4 w-4 text-primary" />
            Review rerun inputs
          </SheetTitle>
          <Button type="button" variant="ghost" size="icon" :disabled="isBusy" @click="requestClose">
            <X class="h-4 w-4" />
          </Button>
        </div>
      </SheetHeader>

      <div class="border-b border-border-subtle bg-background-base px-4 py-3">
        <DataMetricStrip :metrics="summaryMetrics" />
      </div>

      <div v-if="isPreflighting" class="flex flex-1 items-center justify-center text-sm text-text-secondary">
        Checking what Kanchi can safely rerun...
      </div>

      <div v-else-if="preflight && focusedItem && focusedDraft" class="grid min-h-0 flex-1 grid-cols-1 md:grid-cols-[280px_1fr]">
        <aside class="min-h-0 overflow-y-auto border-b border-border-subtle bg-background-surface/60 p-3 md:border-b-0 md:border-r">
          <div class="space-y-2">
            <button
              v-for="item in items"
              :key="item.task_id"
              type="button"
              class="w-full rounded-md border px-3 py-2 text-left transition-colors"
              :class="item.task_id === focusedTaskId ? 'border-primary-border bg-primary-bg/30' : 'border-border-subtle hover:bg-background-hover-subtle'"
              @click="focusedTaskId = item.task_id"
            >
              <div class="flex min-w-0 items-center justify-between gap-2">
                <TaskName :name="item.task_name || taskFor(item)?.task_name || 'Unknown task'" size="sm" :max-length="28" />
                <Badge :variant="itemBadge(item).variant" class="shrink-0 text-[10px]">
                  {{ itemBadge(item).label }}
                </Badge>
              </div>
              <div class="mt-1 flex items-center gap-2 text-xs text-text-muted">
                <UuidDisplay :uuid="item.task_id" :truncate-length="12" size="sm" />
              </div>
            </button>
          </div>
        </aside>

        <main class="flex min-h-0 flex-col overflow-hidden">
          <div class="border-b border-border-subtle bg-background-surface px-4 py-3">
            <div class="flex flex-wrap items-start justify-between gap-3">
              <div class="min-w-0">
                <div class="flex flex-wrap items-center gap-2">
                  <TaskName :name="focusedItem.task_name || taskFor(focusedItem)?.task_name || 'Unknown task'" size="md" :max-length="56" />
                  <Badge :variant="statusMeta(taskFor(focusedItem)).variant" class="text-[11px]">
                    {{ statusMeta(taskFor(focusedItem)).label }}
                  </Badge>
                  <Badge :variant="itemBadge(focusedItem).variant" class="text-[11px]">
                    {{ itemBadge(focusedItem).label }}
                  </Badge>
                </div>
                <div class="mt-2 grid gap-x-4 gap-y-1 text-xs text-text-muted sm:grid-cols-2 lg:grid-cols-4">
                  <span>task <UuidDisplay :uuid="focusedItem.task_id" :truncate-length="12" size="sm" /></span>
                  <span>queue <code class="text-text-primary">{{ focusedItem.target.queue || focusedItem.target.routing_key || 'default' }}</code></span>
                  <span>source <span class="text-text-primary">{{ baselineSourceLabel(focusedItem.baseline.source) }}</span></span>
                  <span v-if="taskFor(focusedItem)?.exception" class="truncate">error {{ taskFor(focusedItem)?.exception }}</span>
                </div>
              </div>

              <div class="flex flex-wrap items-center gap-2">
                <CopyButton
                  v-if="isDraftValid(focusedDraft)"
                  :text="effectiveInputsText(focusedItem)"
                  :copy-key="`rerun-inputs-${focusedItem.task_id}`"
                  label="Inputs"
                  size="xs"
                  title="Copy inputs"
                />
                <CopyButton
                  :text="inputDiffText(focusedItem)"
                  :copy-key="`rerun-diff-${focusedItem.task_id}`"
                  label="Diff"
                  size="xs"
                  title="Copy diff"
                />
                <CopyButton
                  v-if="isDraftValid(focusedDraft) && focusedItem.target.task_name"
                  :text="celerySnippetText(focusedItem)"
                  :copy-key="`rerun-snippet-${focusedItem.task_id}`"
                  label="Snippet"
                  size="xs"
                  title="Copy Celery snippet"
                />
                <Button type="button" variant="ghost" size="icon" :disabled="focusedDraft.history.length === 0" title="Undo" @click="undo(focusedItem.task_id)">
                  <Undo2 class="h-4 w-4" />
                </Button>
                <Button type="button" variant="ghost" size="icon" :disabled="focusedDraft.future.length === 0" title="Redo" @click="redo(focusedItem.task_id)">
                  <Redo2 class="h-4 w-4" />
                </Button>
                <Button type="button" variant="ghost" size="icon" title="Reset" @click="resetTask(focusedItem)">
                  <RotateCcw class="h-4 w-4" />
                </Button>
                <Button
                  v-if="focusedItem.review_state === 'repairable' && items.length > 1"
                  type="button"
                  variant="outline"
                  size="xs"
                  @click="toggleSkip(focusedItem)"
                >
                  <SkipForward class="h-3.5 w-3.5" />
                  {{ focusedDraft.skipped ? 'Unskip' : 'Skip' }}
                </Button>
              </div>
            </div>

            <Alert
              v-if="focusedItem.review_state === 'blocked'"
              variant="warning"
              title="Cannot rerun this task"
              class="mt-3"
            >
              {{ focusedItem.reason || 'Kanchi does not have enough task information to send a new run.' }}
            </Alert>
            <Alert
              v-else-if="focusedItem.review_state === 'repairable' && !isDraftValid(focusedDraft)"
              variant="warning"
              title="Inputs needed"
              class="mt-3"
            >
              Some captured values were truncated. Replace them, or set them to JSON null if that is intentional.
            </Alert>
          </div>

          <div class="min-h-0 flex-1 overflow-y-auto p-4">
            <RerunInputEditor
              :args="focusedDraft.args"
              :kwargs="focusedDraft.kwargs"
              :baseline-args="focusedItem.baseline.args"
              :baseline-kwargs="focusedItem.baseline.kwargs"
              :issues="focusedItem.required_replacements"
              :disabled="focusedItem.review_state === 'blocked' || focusedDraft.skipped"
              @update="(args, kwargs) => updateInputs(focusedItem.task_id, args, kwargs)"
            />
          </div>
        </main>
      </div>

      <div v-else class="flex flex-1 items-center justify-center p-6">
        <Alert variant="warning" title="No review loaded">
          <span class="flex items-center gap-2">
            <AlertTriangle class="h-3.5 w-3.5" />
            Kanchi has not checked these tasks yet.
          </span>
        </Alert>
      </div>

      <div class="border-t border-border-subtle bg-background-surface px-5 py-4">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <p class="min-h-5 text-xs" :class="submitError ? 'text-status-error' : 'text-text-muted'">
            {{ submitError || `Kanchi will rerun ${summary.submitCount} task${summary.submitCount === 1 ? '' : 's'}.` }}
          </p>
          <div class="flex items-center gap-2">
            <Button type="button" variant="outline" :disabled="isBusy" @click="requestClose">
              Cancel
            </Button>
            <Button type="button" variant="primary" :disabled="!canSubmit" @click="submitReview">
              <RefreshCw v-if="taskActionsStore.isCreating" class="h-4 w-4 animate-spin" />
              <Check v-else class="h-4 w-4" />
              Rerun {{ summary.submitCount }}
            </Button>
          </div>
        </div>
      </div>
    </SheetContent>
  </Sheet>
</template>
