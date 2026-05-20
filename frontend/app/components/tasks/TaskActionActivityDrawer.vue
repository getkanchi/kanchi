<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Check, ChevronRight, ChevronsUpDown, Search, X } from 'lucide-vue-next'
import TaskName from '~/components/TaskName.vue'
import UuidDisplay from '~/components/UuidDisplay.vue'
import CopyButton from '~/components/CopyButton.vue'
import DataMetricStrip from '~/components/common/DataMetricStrip.vue'
import { Badge } from '~/components/ui/badge'
import { Button } from '~/components/ui/button'
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandList,
} from '~/components/ui/command'
import { Input } from '~/components/ui/input'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '~/components/ui/popover'
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '~/components/ui/sheet'
import { useLogger } from '~/services/logger'
import { cn } from '~/lib/utils'
import TaskActionOutcomeBadge from './TaskActionOutcomeBadge.vue'
import type { TaskEventResponse } from '~/services/apiClient'

const taskActionsStore = useTaskActionsStore()
const logger = useLogger()
const { eventTypeToStatus, getStatusVariant, formatStatus } = useTaskStatus()
const query = ref('')
const outcomeFilter = ref<'all' | 'failed' | 'skipped' | 'running'>('all')
const outcomeFilterOpen = ref(false)

const focused = computed(() => taskActionsStore.focusedAction)
const outcomeFilterOptions = computed(() => {
  const options: Array<{ value: 'all' | 'failed' | 'skipped' | 'running'; label: string }> = [
    { value: 'all', label: 'All outcomes' },
    { value: 'failed', label: 'Failed only' },
    { value: 'skipped', label: 'Skipped only' },
  ]
  if (focused.value?.action_type === 'rerun') {
    options.push({ value: 'running', label: 'Still running' })
  }
  return options
})
const selectedOutcomeFilter = computed(() =>
  outcomeFilterOptions.value.find(option => option.value === outcomeFilter.value) ?? outcomeFilterOptions.value[0]
)

const filteredItems = computed(() => {
  const items = focused.value?.items || []
  const normalized = query.value.trim().toLowerCase()
  return items.filter(item => {
    if (outcomeFilter.value === 'failed' && item.outcome !== 'failed') return false
    if (
      outcomeFilter.value === 'skipped'
      && !['skipped_unavailable', 'user_skipped', 'blocked_skipped'].includes(item.outcome)
    ) return false
    if (outcomeFilter.value === 'running') {
      const eventType = item.rerun_task?.event_type || ''
      if (!item.rerun_task_id || ['task-succeeded', 'task-failed', 'task-revoked', 'task-retried'].includes(eventType)) {
        return false
      }
    }
    if (!normalized) return true
    return [
      item.original_task_name,
      item.original_task_id,
      item.rerun_task_id,
      item.reason,
    ].some(value => value && String(value).toLowerCase().includes(normalized))
  })
})

const title = computed(() => {
  if (!focused.value) return 'Recent actions'
  if (focused.value.action_type === 'rerun') return 'Rerun history'
  if (focused.value.action_type === 'unresolve') return 'Unresolve activity'
  return 'Resolve activity'
})

const lifecycleCounts = computed(() =>
  Object.entries(focused.value?.rerun_lifecycle_counts || {})
)
const activityMetrics = computed(() => {
  if (!focused.value) return []
  return [
    { label: 'Items', value: focused.value.item_total },
    {
      label: focused.value.action_type === 'rerun' ? 'Sent' : 'Changed',
      value: focused.value.item_created + focused.value.item_changed,
      tone: 'success' as const,
    },
    { label: 'Skipped', value: focused.value.item_skipped, tone: 'warning' as const },
    { label: 'Failed', value: focused.value.item_failed, tone: 'error' as const },
  ]
})

function taskStatusMeta(task: TaskEventResponse | null | undefined) {
  if (!task) {
    return { label: 'Pending', variant: 'pending' as const }
  }
  const status = task.is_orphan ? 'ORPHANED' : eventTypeToStatus(task.event_type || 'unknown')
  return {
    label: formatStatus(status),
    variant: getStatusVariant(status),
  }
}

function eventTypeStatusMeta(eventType: string) {
  const status = eventTypeToStatus(eventType || 'unknown')
  return {
    label: formatStatus(status),
    variant: getStatusVariant(status),
  }
}

function actionTypeLabel(type: string) {
  if (type === 'rerun') return 'Rerun'
  if (type === 'unresolve') return 'Unresolve'
  return 'Resolve'
}

function rerunKindLabel(kind: string | null | undefined) {
  switch (kind) {
    case 'edited_override':
      return 'Sent with edits'
    case 'repaired_override':
      return 'Sent after repair'
    case 'replay':
      return 'Sent as-is'
    default:
      return null
  }
}

function submittedInputsText(item: any) {
  return JSON.stringify({ args: item.submitted_args || [], kwargs: item.submitted_kwargs || {} }, null, 2)
}

function submittedSnippetText(item: any) {
  const queue = item.target_queue || 'default'
  return `app.send_task(${pythonLiteral(item.rerun_task_name)}, args=${pythonLiteral(item.submitted_args)}, kwargs=${pythonLiteral(item.submitted_kwargs)}, queue=${pythonLiteral(queue)})`
}

function selectOutcomeFilter(value: 'all' | 'failed' | 'skipped' | 'running') {
  outcomeFilter.value = value
  outcomeFilterOpen.value = false
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

watch(() => taskActionsStore.isDrawerOpen, async (open) => {
  if (open && taskActionsStore.actions.length === 0) {
    try {
      await taskActionsStore.fetchActions()
    } catch (error) {
      logger.error('Failed to fetch task actions when opening activity drawer', { error })
    }
  }
})

watch(() => focused.value?.action_type, (actionType) => {
  if (actionType !== 'rerun' && outcomeFilter.value === 'running') {
    outcomeFilter.value = 'all'
  }
})
</script>

<template>
  <Sheet :open="taskActionsStore.isDrawerOpen" @update:open="(open) => open ? taskActionsStore.openDrawer() : taskActionsStore.closeDrawer()">
    <SheetContent
      side="right"
      class="flex h-screen w-full max-w-full flex-col border-l border-border-subtle bg-background-base p-0 sm:w-[720px] sm:max-w-[95vw]"
    >
      <SheetHeader class="border-b border-border-subtle bg-background-surface px-5 py-4">
        <div class="flex items-center justify-between gap-3">
          <SheetTitle>{{ title }}</SheetTitle>
          <Button variant="ghost" size="icon" @click="taskActionsStore.closeDrawer()">
            <X class="h-4 w-4" />
          </Button>
        </div>
      </SheetHeader>

      <div class="grid min-h-0 flex-1 grid-cols-1 md:grid-cols-[220px_1fr]">
        <aside class="border-b border-border-subtle bg-background-surface/60 p-3 md:border-b-0 md:border-r">
          <div class="space-y-2">
            <button
              v-for="action in taskActionsStore.activeActions"
              :key="action.id"
              type="button"
              class="w-full rounded-md border px-3 py-2 text-left transition-colors"
              :class="action.id === taskActionsStore.focusedActionId ? 'border-primary-border bg-primary-bg/40' : 'border-border-subtle hover:bg-background-hover-subtle'"
              @click="taskActionsStore.focusAction(action.id)"
            >
              <div class="flex items-center justify-between gap-2">
                <span class="text-sm font-medium text-text-primary">{{ actionTypeLabel(action.action_type) }}</span>
                <TaskActionOutcomeBadge :value="action.status" />
              </div>
              <div class="mt-1 text-xs text-text-muted">
                {{ action.selection_size }} task{{ action.selection_size === 1 ? '' : 's' }}
              </div>
            </button>
            <p v-if="taskActionsStore.activeActions.length === 0" class="p-3 text-sm text-text-muted">
              No task action activity yet.
            </p>
          </div>
        </aside>

        <main class="min-h-0 overflow-y-auto p-4">
          <div v-if="focused" class="space-y-4">
            <DataMetricStrip :metrics="activityMetrics" />

            <div v-if="lifecycleCounts.length" class="flex flex-wrap gap-2">
              <Badge
                v-for="[eventType, count] in lifecycleCounts"
                :key="eventType"
                :variant="eventTypeStatusMeta(eventType).variant"
              >
                {{ eventTypeStatusMeta(eventType).label }} {{ count }}
              </Badge>
            </div>

            <div class="flex flex-wrap items-center gap-2">
              <div class="relative min-w-[220px] flex-1">
                <Search class="absolute left-2 top-2 h-4 w-4 text-text-muted" />
                <Input v-model="query" class="pl-8" placeholder="Search actions" />
              </div>
              <Popover v-model:open="outcomeFilterOpen">
                <PopoverTrigger as-child>
                  <Button variant="outline" size="sm" class="h-9 min-w-40 justify-between gap-2">
                    {{ selectedOutcomeFilter.label }}
                    <ChevronsUpDown class="h-3.5 w-3.5 text-text-muted" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent
                  class="w-44 border-border-subtle bg-background-surface p-0 text-text-primary"
                  align="end"
                >
                  <Command class="bg-background-surface text-text-primary">
                    <CommandList class="max-h-none">
                      <CommandEmpty class="text-text-muted">No filter found.</CommandEmpty>
                      <CommandGroup class="text-text-primary">
                        <CommandItem
                          v-for="option in outcomeFilterOptions"
                          :key="option.value"
                          :value="option.value"
                          class="cursor-pointer text-text-secondary data-[highlighted]:bg-background-hover-subtle data-[highlighted]:text-text-primary"
                          @select="selectOutcomeFilter(option.value)"
                        >
                          <Check
                            :class="cn(
                              'h-4 w-4 text-primary',
                              outcomeFilter === option.value ? 'visible' : 'invisible',
                            )"
                          />
                          {{ option.label }}
                        </CommandItem>
                      </CommandGroup>
                    </CommandList>
                  </Command>
                </PopoverContent>
              </Popover>
            </div>

            <div class="space-y-2">
              <div
                v-for="item in filteredItems"
                :key="item.id"
                class="rounded-md border border-border-subtle bg-background-surface p-3"
              >
                <div class="flex flex-wrap items-start justify-between gap-3">
                  <div class="min-w-0">
                    <div class="flex flex-wrap items-center gap-2">
                      <TaskName :name="item.original_task_name || item.original_task_id" size="sm" :max-length="44" />
                      <TaskActionOutcomeBadge :value="item.outcome" />
                    </div>
                    <div class="mt-1 flex flex-wrap items-center gap-2 text-xs text-text-muted">
                      <span>Original</span>
                      <UuidDisplay :uuid="item.original_task_id" :truncate-length="12" size="sm" />
                      <template v-if="item.rerun_task_id">
                        <ChevronRight class="h-3 w-3" />
                        <span>Rerun</span>
                        <UuidDisplay :uuid="item.rerun_task_id" :truncate-length="12" size="sm" />
                        <Badge
                          :variant="taskStatusMeta(item.rerun_task).variant"
                          class="text-[10px]"
                        >
                          {{ taskStatusMeta(item.rerun_task).label }}
                        </Badge>
                      </template>
                    </div>
                    <p v-if="item.reason" class="mt-2 text-xs text-text-secondary">{{ item.reason }}</p>
                    <div v-if="item.rerun_kind || item.attempted_task_id" class="mt-2 flex flex-wrap items-center gap-2 text-xs text-text-muted">
                      <Badge v-if="rerunKindLabel(item.rerun_kind)" variant="outline" class="text-[10px]">
                        {{ rerunKindLabel(item.rerun_kind) }}
                      </Badge>
                      <template v-if="item.attempted_task_id && !item.rerun_task_id">
                        <span>Attempted task</span>
                        <UuidDisplay :uuid="item.attempted_task_id" :truncate-length="12" size="sm" />
                      </template>
                    </div>
                  </div>
                  <div class="flex items-center gap-2">
                    <CopyButton
                      v-if="item.submitted_args && item.submitted_kwargs"
                      :text="submittedInputsText(item)"
                      :copy-key="`submitted-rerun-inputs-${item.id}`"
                      label="Inputs"
                      size="xs"
                      title="Copy submitted inputs"
                    />
                    <CopyButton
                      v-if="item.submitted_args && item.submitted_kwargs && item.rerun_task_name"
                      :text="submittedSnippetText(item)"
                      :copy-key="`submitted-rerun-snippet-${item.id}`"
                      label="Snippet"
                      size="xs"
                      title="Copy submitted Celery snippet"
                    />
                    <NuxtLink
                      :to="`/tasks/${item.original_task_id}`"
                      @click="taskActionsStore.closeDrawer()"
                    >
                      <Button variant="outline" size="xs" class="gap-1">
                        <ChevronRight class="h-3.5 w-3.5" />
                        Original
                      </Button>
                    </NuxtLink>
                    <NuxtLink
                      v-if="item.rerun_task_id"
                      :to="`/tasks/${item.rerun_task_id}`"
                      @click="taskActionsStore.closeDrawer()"
                    >
                      <Button variant="outline" size="xs" class="gap-1">
                        <ChevronRight class="h-3.5 w-3.5" />
                        Rerun
                      </Button>
                    </NuxtLink>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="flex h-full items-center justify-center text-sm text-text-muted">
            Select an activity entry.
          </div>
        </main>
      </div>
    </SheetContent>
  </Sheet>
</template>
