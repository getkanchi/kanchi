<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ChevronRight, Search, X } from 'lucide-vue-next'
import TaskName from '~/components/TaskName.vue'
import UuidDisplay from '~/components/UuidDisplay.vue'
import { Badge } from '~/components/ui/badge'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '~/components/ui/sheet'
import { useLogger } from '~/services/logger'
import TaskActionOutcomeBadge from './TaskActionOutcomeBadge.vue'
import type { TaskEventResponse } from '~/services/apiClient'

const taskActionsStore = useTaskActionsStore()
const logger = useLogger()
const { eventTypeToStatus, getStatusVariant, formatStatus } = useTaskStatus()
const query = ref('')
const outcomeFilter = ref<'all' | 'failed' | 'skipped' | 'running'>('all')

const focused = computed(() => taskActionsStore.focusedAction)

const filteredItems = computed(() => {
  const items = focused.value?.items || []
  const normalized = query.value.trim().toLowerCase()
  return items.filter(item => {
    if (outcomeFilter.value === 'failed' && item.outcome !== 'failed') return false
    if (outcomeFilter.value === 'skipped' && item.outcome !== 'skipped_unavailable') return false
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
  if (!focused.value) return 'Task action activity'
  if (focused.value.action_type === 'rerun') return 'Rerun activity'
  if (focused.value.action_type === 'unresolve') return 'Unresolve activity'
  return 'Resolve activity'
})

const lifecycleCounts = computed(() =>
  Object.entries(focused.value?.rerun_lifecycle_counts || {})
)

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

watch(() => taskActionsStore.isDrawerOpen, async (open) => {
  if (open && taskActionsStore.actions.length === 0) {
    try {
      await taskActionsStore.fetchActions()
    } catch (error) {
      logger.error('Failed to fetch task actions when opening activity drawer', { error })
    }
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
                <span class="text-sm font-medium capitalize text-text-primary">{{ action.action_type }}</span>
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
            <div class="grid gap-2 sm:grid-cols-4">
              <div class="rounded-md border border-border-subtle p-3">
                <div class="text-xl font-semibold text-text-primary">{{ focused.item_total }}</div>
                <div class="text-xs text-text-muted">items</div>
              </div>
              <div class="rounded-md border border-border-subtle p-3">
                <div class="text-xl font-semibold text-status-success">{{ focused.item_created + focused.item_changed }}</div>
                <div class="text-xs text-text-muted">changed</div>
              </div>
              <div class="rounded-md border border-border-subtle p-3">
                <div class="text-xl font-semibold text-status-warning">{{ focused.item_skipped }}</div>
                <div class="text-xs text-text-muted">skipped</div>
              </div>
              <div class="rounded-md border border-border-subtle p-3">
                <div class="text-xl font-semibold text-status-error">{{ focused.item_failed }}</div>
                <div class="text-xs text-text-muted">failed</div>
              </div>
            </div>

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
                <Input v-model="query" class="pl-8" placeholder="Search activity..." />
              </div>
              <Button variant="outline" size="sm" :class="outcomeFilter === 'all' ? 'bg-background-selected' : ''" @click="outcomeFilter = 'all'">All</Button>
              <Button variant="outline" size="sm" :class="outcomeFilter === 'failed' ? 'bg-background-selected' : ''" @click="outcomeFilter = 'failed'">Failed</Button>
              <Button variant="outline" size="sm" :class="outcomeFilter === 'skipped' ? 'bg-background-selected' : ''" @click="outcomeFilter = 'skipped'">Skipped</Button>
              <Button v-if="focused.action_type === 'rerun'" variant="outline" size="sm" :class="outcomeFilter === 'running' ? 'bg-background-selected' : ''" @click="outcomeFilter = 'running'">Running</Button>
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
                  </div>
                  <div class="flex items-center gap-2">
                    <NuxtLink
                      :to="`/tasks/${item.original_task_id}`"
                      @click="taskActionsStore.closeDrawer()"
                    >
                      <Button variant="outline" size="xs">Original</Button>
                    </NuxtLink>
                    <NuxtLink
                      v-if="item.rerun_task_id"
                      :to="`/tasks/${item.rerun_task_id}`"
                      @click="taskActionsStore.closeDrawer()"
                    >
                      <Button variant="outline" size="xs">Rerun</Button>
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
