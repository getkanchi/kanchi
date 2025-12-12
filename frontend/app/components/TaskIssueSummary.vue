<template>
  <div
    v-if="!shouldHideCard"
    class="border border-border-subtle rounded-md bg-background-surface glow-border"
  >
    <button
      type="button"
      class="flex w-full items-center border-border-subtle justify-between p-2 border-b gap-4 text-left hover:bg-background-hover-subtle transition-colors"
      @click="toggleCollapsed"
    >
      <div class="flex items-center gap-3">
        <ChevronRight
          class="h-4 w-4 transition-transform duration-200 text-text-muted group-hover:text-text-primary"
          :class="{ 'rotate-90': !isCollapsed }"
        />
        <StatusDot
          :status="effectiveStatus"
          :pulse="statusDotPulse"
          class="scale-110"
        />
        <div class="flex items-center gap-2 text-left">
          <span class="font-medium text-sm text-text-primary truncate">{{ title }}</span>
          <div class="flex items-center gap-2 text-xs text-text-secondary">
            <span class="flex items-center gap-1">
              <span class="font-mono">{{ unresolvedCount }}</span>
              <span>{{ primaryLabel }}</span>
            </span>
            <span
              v-if="recentCount > 0 && secondaryLabel"
              class="flex items-center gap-1"
            >
              <span class="font-mono">{{ recentCount }}</span>
              <span>{{ secondaryLabel }}</span>
            </span>
          </div>
        </div>
      </div>
    </button>

    <div v-if="!isCollapsed" class="border-b border-border-subtle px-4 py-3 space-y-2">
      <div class="flex flex-wrap items-center gap-4 justify-between">
        <div class="flex-1 min-w-[240px]">
          <SearchInput
            :model-value="searchQuery"
            :filters="activeFilters"
            @update:model-value="handleSearchUpdate"
            @update:filters="handleFiltersUpdate"
          />
        </div>
        <div class="flex flex-wrap items-center justify-end gap-3">
            <Tabs
              :model-value="activeLookbackString"
              :disabled="isUpdatingLookback"
              @update:model-value="handleLookbackSelectString"
              class="flex items-center"
            >
              <TabsList class="bg-background-surface border-border-subtle p-0.5">
                <TabsTrigger
                  v-for="option in lookbackOptionsNormalized"
                  :key="option"
                  :value="String(option)"
                  class="min-w-[44px] px-2.5 py-1 text-xs"
                >
                  {{ formatLookbackLabel(option) }}
                </TabsTrigger>
              </TabsList>
            </Tabs>
          <div class="text-sm text-gray-500 text-right">
            <template v-if="totalFiltered > 0">
              Showing {{ pageStart }} to {{ pageEnd }} of {{ totalFiltered }} tasks
              <span v-if="showFilteredHint" class="text-text-muted"> (filtered from {{ totalCount }})</span>
            </template>
            <template v-else>
              No matching tasks
              <span v-if="showFilteredHint" class="text-text-muted"> (from {{ totalCount }})</span>
            </template>
          </div>
        </div>
      </div>
      <p v-if="lookbackError" class="text-xs text-status-danger text-right">{{ lookbackError }}</p>
    </div>

    <div v-if="!isCollapsed">
      <Table>
        <TableHeader>
          <TableRow class="border-border-subtle">
            <TableHead class="w-12" />
            <TableHead>Task Name</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Time</TableHead>
            <TableHead>Runtime</TableHead>
            <TableHead>Worker</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <template v-if="displayedTasks.length">
            <template v-for="task in displayedTasks" :key="task.task_id">
              <TableRow
                class="border-border-subtle cursor-pointer hover:bg-background-hover-subtle transition-colors duration-150"
                @click="toggleTaskExpansion(task.task_id)"
              >
                <TableCell class="w-12">
                  <ChevronRight
                    v-if="!expandedTaskIds.has(task.task_id)"
                    class="h-4 w-4 text-gray-400"
                  />
                  <ChevronDown v-else class="h-4 w-4 text-gray-400" />
                </TableCell>
                <TableCell>
                  <div class="flex items-center gap-3">
                    <TaskName
                      :name="task.task_name"
                      size="sm"
                      :max-length="30"
                      :expandable="true"
                    />
                    <slot name="meta-badges" :task="task" />
                    <Badge
                      v-if="resolutionState(task).resolved"
                      variant="outline"
                      class="text-[11px] px-2 py-0.5 border-status-success text-status-success bg-status-success-bg/50"
                    >
                      Resolved
                    </Badge>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge :variant="statusVariant(task)" class="text-xs">
                    {{ statusLabel(task) }}
                  </Badge>
                </TableCell>
                <TableCell>
                  <TimeDisplay
                    v-if="taskTimestamp(task)"
                    :timestamp="taskTimestamp(task)"
                    layout="inline"
                    :auto-refresh="true"
                    :refresh-interval="1000"
                  />
                  <span v-else class="text-gray-400">-</span>
                </TableCell>
                <TableCell>
                  <span
                    v-if="hasRuntime(task)"
                    class="text-sm font-mono"
                  >
                    {{ runtimeDisplay(task) }}
                  </span>
                  <span v-else class="text-gray-400">-</span>
                </TableCell>
                <TableCell>
                  <span v-if="task.hostname" class="text-xs font-mono">
                    {{ task.hostname }}
                  </span>
                  <span v-else class="text-xs text-gray-400">-</span>
                </TableCell>
              </TableRow>
              <TableRow
                v-if="expandedTaskIds.has(task.task_id)"
                class="bg-background-raised border-border-subtle cursor-default"
              >
                <TableCell :colspan="summaryColumnCount + 1" class="p-0">
                  <TaskDetailsSection
                    :task-name="task.task_name || 'Task'"
                    :status-label="statusLabel(task)"
                    :status-variant="statusVariant(task)"
                    :started-timestamp="taskTimestamp(task)"
                    :runtime-label="hasRuntime(task) ? runtimeDisplay(task) : null"
                    :task-id="task.task_id"
                    :routing-key="task.routing_key"
                    :hostname="task.hostname"
                    :args="task.args"
                    :kwargs="task.kwargs"
                    :result="task.result"
                    :traceback="task.exception"
                    :show-exception="showException"
                  >
                    <template #actions>
                      <slot name="actions" :task="task">
                        <Button
                          v-if="itemActionLabel"
                          variant="outline"
                          size="xs"
                          class="gap-1"
                          :disabled="isActionDisabled(task)"
                          @click.stop="handleItemAction(task)"
                        >
                          <Loader2
                            v-if="isActionLoading(task)"
                            class="h-3.5 w-3.5 animate-spin"
                          />
                          <span>{{ itemActionLabel }}</span>
                        </Button>
                      </slot>
                    </template>

                    <template #meta-extra>
                      <div
                        v-if="resolutionState(task).resolved"
                        class="flex items-center gap-1.5 text-xs text-status-success"
                      >
                        <CheckCircle2 class="h-3.5 w-3.5" />
                        <span class="font-medium">Manually resolved</span>
                        <span v-if="resolutionState(task).resolved_by" class="text-text-secondary">
                          by {{ resolutionState(task).resolved_by }}
                        </span>
                        <span v-if="resolutionState(task).resolved_at" class="text-text-muted flex items-center gap-1">
                          •
                          <TimeDisplay
                            :timestamp="resolutionState(task).resolved_at || ''"
                            layout="inline"
                            :auto-refresh="true"
                            :refresh-interval="60000"
                          />
                        </span>
                      </div>
                    </template>

                  </TaskDetailsSection>
                </TableCell>
              </TableRow>
            </template>
          </template>
          <template v-else>
            <TableRow class="border-border-subtle">
              <TableCell :colspan="summaryColumnCount + 1" class="p-8">
                <div class="flex flex-col items-center gap-2 rounded-lg border border-dashed border-border-subtle px-6 py-8 text-center">
                  <svg class="h-10 w-10 text-text-muted/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M12 3a9 9 0 100 18 9 9 0 000-18z" />
                  </svg>
                  <p class="text-sm font-medium text-text-secondary">{{ emptyStateTitle }}</p>
                  <p
                    v-if="emptyStateDescription"
                    class="max-w-md text-xs text-text-muted"
                  >
                    {{ emptyStateDescription }}
                  </p>
                </div>
              </TableCell>
            </TableRow>
          </template>
        </TableBody>
      </Table>

      <div class="flex items-center justify-between p-4 border-t border-border-subtle">
        <div class="flex items-center space-x-2">
          <span v-if="isLoading" class="text-sm text-gray-500">
            Loading...
          </span>
          <span v-else class="text-sm text-gray-500">
            <span v-if="totalFiltered > 0">
              Showing {{ pageStart }} to {{ pageEnd }} of {{ totalFiltered }} entries
            </span>
            <span v-else>No tasks to display.</span>
          </span>
        </div>
        <div class="flex items-center space-x-2">
          <div class="flex items-center space-x-2">
            <span class="text-sm text-gray-500">Show</span>
            <Select
              :model-value="String(pageSize)"
              @update:model-value="handlePageSizeChange"
              size="sm"
            >
              <option
                v-for="option in pageSizeOptions"
                :key="option"
                :value="String(option)"
              >
                {{ option }}
              </option>
            </Select>
            <span class="text-sm text-gray-500">per page</span>
          </div>
          
          <div class="flex items-center space-x-1">
            <IconButton
              :icon="ChevronsLeft"
              variant="ghost"
              size="md"
              @click="goToFirstPage"
              :disabled="!hasPrevPage"
            />
            <IconButton
              :icon="ChevronLeft"
              variant="ghost"
              size="md"
              @click="goToPreviousPage"
              :disabled="!hasPrevPage"
            />
            <span class="px-2 text-sm text-gray-500">
              Page {{ totalPages > 0 ? currentPage + 1 : 0 }} of {{ totalPages }}
            </span>
            <IconButton
              :icon="ChevronRight"
              variant="ghost"
              size="md"
              @click="goToNextPage"
              :disabled="!hasNextPage"
            />
            <IconButton
              :icon="ChevronsRight"
              variant="ghost"
              size="md"
              @click="goToLastPage"
              :disabled="!hasNextPage"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import TaskName from '~/components/TaskName.vue'
import TimeDisplay from '~/components/TimeDisplay.vue'
import CopyButton from '~/components/CopyButton.vue'
import StatusDot from '~/components/StatusDot.vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import SearchInput from '~/components/SearchInput.vue'
import PythonValueViewer from '~/components/PythonValueViewer.vue'
import { IconButton, Select } from '~/components/common'
import TaskDetailsSection from '~/components/common/TaskDetailsSection.vue'
import { ChevronDown, ChevronRight, Loader2, AlertTriangle, ChevronsLeft, ChevronLeft, ChevronsRight, CheckCircle2 } from 'lucide-vue-next'
import type { TaskEventResponse } from '~/services/apiClient'
import { useTaskStatus } from '~/composables/useTaskStatus'
import type { ParsedFilter } from '~/composables/useFilterParser'

const props = withDefaults(defineProps<{
  title: string
  tasks: TaskEventResponse[]
  status?: 'success' | 'warning' | 'error' | 'info'
  isLoading?: boolean
  showLookbackSelector?: boolean
  lookbackHours?: number | null
  primaryLabel: string
  secondaryLabel?: string
  recentField?: keyof TaskEventResponse
  recentWindowMinutes?: number
  timeField?: keyof TaskEventResponse
  limit?: number
  showException?: boolean
  emptyStateTitle: string
  emptyStateDescription?: string
  pulse?: boolean | null
  itemActionLabel?: string
  itemActionLoadingIds?: string[]
  itemActionDisabledIds?: string[]
  hideWhenEmpty?: boolean
  ignoreResolved?: boolean
}>(), {
  status: 'info',
  isLoading: false,
  secondaryLabel: undefined,
  recentField: 'timestamp',
  recentWindowMinutes: 60,
  timeField: 'timestamp',
  limit: 10,
  showException: false,
  emptyStateDescription: undefined,
  pulse: null,
  itemActionLabel: undefined,
  itemActionLoadingIds: () => [],
  itemActionDisabledIds: () => [],
  hideWhenEmpty: false,
  ignoreResolved: false,
  showLookbackSelector: false,
  lookbackHours: null,
})

const emit = defineEmits<{
  'item-action': [task: TaskEventResponse]
  'lookback-change': [hours: number]
}>()

const { eventTypeToStatus, getStatusVariant, formatStatus } = useTaskStatus()
const configStore = useConfigStore()

const expandedTaskIds = ref(new Set<string>())
const searchQuery = ref('')
const activeFilters = ref<ParsedFilter[]>([])
const pageSize = ref(props.limit)
const currentPage = ref(0)
const isCollapsed = ref(true)

const summaryColumnCount = 5

const visibleTasks = computed(() => {
  if (!props.ignoreResolved) return props.tasks
  return props.tasks.filter(task => !resolutionState(task).resolved)
})

const unresolvedCount = computed(() => visibleTasks.value.filter(task => !resolutionState(task).resolved).length)
const totalCount = computed(() => visibleTasks.value.length)
const shouldHideCard = computed(() => props.hideWhenEmpty && totalCount.value === 0)

type ResolvableTask = TaskEventResponse & { resolved?: boolean; resolved_by?: string | null; resolved_at?: string | null }
const resolutionState = (task: TaskEventResponse) => {
  const candidate = task as ResolvableTask
  return {
    resolved: Boolean(candidate.resolved),
    resolved_by: candidate.resolved_by ?? null,
    resolved_at: candidate.resolved_at ?? null,
  }
}

const sortedTasks = computed(() => {
  const field = props.timeField ?? 'timestamp'
  return [...visibleTasks.value].sort((a, b) => {
    const aTime = Date.parse(String((a[field] as string | undefined) ?? a.timestamp ?? 0))
    const bTime = Date.parse(String((b[field] as string | undefined) ?? b.timestamp ?? 0))
    return bTime - aTime
  })
})

// Filter helper functions - must be defined before filteredTasks computed
const getTaskStatusValue = (task: TaskEventResponse) => {
  return task.is_orphan ? 'ORPHANED' : eventTypeToStatus(task.event_type || 'unknown')
}

const matchesSearch = (task: TaskEventResponse) => {
  const query = searchQuery.value.trim().toLowerCase()
  if (!query) return true

  const resultText = (() => {
    try {
      return task.result ? JSON.stringify(task.result) : ''
    } catch {
      return String(task.result ?? '')
    }
  })()

  const candidates = [
    task.task_name,
    task.task_id,
    task.hostname,
    task.routing_key,
    resultText,
    task.exception ?? ''
  ]

  return candidates.some(value =>
    value && String(value).toLowerCase().includes(query)
  )
}

const getFieldCandidates = (task: TaskEventResponse, field: string): string[] => {
  switch (field) {
    case 'state': {
      const status = getTaskStatusValue(task)
      return [status, formatStatus(status)]
    }
    case 'worker':
      return [task.hostname ?? '']
    case 'task':
      return [task.task_name ?? '']
    case 'queue':
      return [task.routing_key ?? 'default']
    case 'id':
      return [task.task_id ?? '']
    default:
      return ['']
  }
}

const applyFilter = (task: TaskEventResponse, filter: ParsedFilter) => {
  const candidates = getFieldCandidates(task, filter.field).map(value => value.toLowerCase())
  if (candidates.length === 0) {
    candidates.push('')
  }

  const values = filter.values.map(v => v.toLowerCase()).filter(Boolean)
  if (values.length === 0) {
    return true
  }

  switch (filter.operator) {
    case 'is':
      return candidates.some(candidate => candidate === values[0])
    case 'not':
      return candidates.every(candidate => candidate !== values[0])
    case 'contains':
      return candidates.some(candidate => candidate.includes(values[0]))
    case 'starts':
      return candidates.some(candidate => candidate.startsWith(values[0]))
    case 'in':
      return candidates.some(candidate => values.includes(candidate))
    case 'not_in':
      return candidates.every(candidate => !values.includes(candidate))
    default:
      return true
  }
}

const matchesFilters = (task: TaskEventResponse) => {
  if (activeFilters.value.length === 0) return true
  return activeFilters.value.every(filter => applyFilter(task, filter))
}

const filteredTasks = computed(() =>
  sortedTasks.value.filter(task => matchesSearch(task) && matchesFilters(task))
)

const totalFiltered = computed(() => filteredTasks.value.length)
const pageSizeSafe = computed(() => Math.max(pageSize.value, 1))

const totalPages = computed(() => Math.max(1, Math.ceil(totalFiltered.value / pageSizeSafe.value)))
const pageStart = computed(() => totalFiltered.value === 0 ? 0 : currentPage.value * pageSizeSafe.value + 1)
const pageEnd = computed(() => totalFiltered.value === 0 ? 0 : Math.min(pageStart.value + pageSizeSafe.value - 1, totalFiltered.value))

const paginatedTasks = computed(() => {
  const start = currentPage.value * pageSizeSafe.value
  return filteredTasks.value.slice(start, start + pageSizeSafe.value)
})

const displayedTasks = computed(() => paginatedTasks.value)

const recentCount = computed(() => {
  if (!props.recentField || props.recentWindowMinutes === undefined) return 0
  const threshold = Date.now() - props.recentWindowMinutes * 60 * 1000
  return visibleTasks.value.filter(task => {
    const raw = task[props.recentField!]
    if (!raw) return false
    const parsed = Date.parse(String(raw))
    return !Number.isNaN(parsed) && parsed >= threshold
  }).length
})

const statusDotPulse = computed(() => {
  if (props.pulse !== null) {
    return props.pulse
  }
  return totalCount.value > 0 && recentCount.value > 0
})

const effectiveStatus = computed(() => {
  if (totalCount.value === 0) {
    return 'success'
  }
  return props.status ?? 'info'
})

const showFilteredHint = computed(() => {
  const hasQuery = searchQuery.value.trim().length > 0
  const hasFilters = activeFilters.value.length > 0
  return (hasQuery || hasFilters) && totalFiltered.value < totalCount.value
})

const pageSizeOptions = computed(() => {
  const options = new Set<number>([5, 10, 20, 50, pageSizeSafe.value])
  if (typeof props.limit === 'number') {
    options.add(props.limit)
  }
  return Array.from(options).sort((a, b) => a - b)
})

const hasPrevPage = computed(() => currentPage.value > 0)
const hasNextPage = computed(() => totalFiltered.value > 0 && currentPage.value < totalPages.value - 1)

const lookbackOptionsNormalized = computed(() => [12, 24, 48, 72])

const activeLookback = computed(() => {
  const options = lookbackOptionsNormalized.value
  const sourceHours = props.lookbackHours ?? configStore.taskIssueLookbackHours
  const candidate = Number.isFinite(sourceHours) ? Math.round(Number(sourceHours)) : NaN
  if (!Number.isFinite(candidate)) {
    return options[0]
  }
  if (options.includes(candidate)) {
    return candidate
  }
  return options.reduce((closest, option) => {
    const currentDiff = Math.abs(option - candidate)
    const bestDiff = Math.abs(closest - candidate)
    return currentDiff < bestDiff ? option : closest
  }, options[0])
})
const activeLookbackString = computed(() => String(activeLookback.value))

const isUpdatingLookback = ref(false)
const lookbackError = ref<string | null>(null)

const formatLookbackLabel = (hours: number) => {
  if (hours % 24 === 0 && hours >= 24) {
    const days = hours / 24
    return `${days}d`
  }
  return `${hours}h`
}

watch(() => props.limit, (next) => {
  if (typeof next === 'number' && next > 0) {
    pageSize.value = next
    currentPage.value = 0
  }
})

watch(() => [props.tasks, props.ignoreResolved], () => {
  currentPage.value = 0
})

watch(filteredTasks, () => {
  const maxPage = Math.max(0, Math.ceil(totalFiltered.value / pageSizeSafe.value) - 1)
  if (currentPage.value > maxPage) {
    currentPage.value = maxPage
  }
})

const toggleTaskExpansion = (taskId: string) => {
  if (expandedTaskIds.value.has(taskId)) {
    expandedTaskIds.value.delete(taskId)
  } else {
    expandedTaskIds.value.add(taskId)
  }
}

const handleSearchUpdate = (value: string) => {
  searchQuery.value = value
  currentPage.value = 0
}

const handleFiltersUpdate = (filters: ParsedFilter[]) => {
  activeFilters.value = filters ?? []
  currentPage.value = 0
}

const handlePageSizeChange = (value: string) => {
  const parsed = Number(value)
  pageSize.value = Number.isFinite(parsed) && parsed > 0 ? Math.floor(parsed) : 5
  currentPage.value = 0
}

const goToFirstPage = () => {
  currentPage.value = 0
}

const goToPreviousPage = () => {
  currentPage.value = Math.max(0, currentPage.value - 1)
}

const goToNextPage = () => {
  if (hasNextPage.value) {
    currentPage.value = Math.min(totalPages.value - 1, currentPage.value + 1)
  }
}

const goToLastPage = () => {
  currentPage.value = totalPages.value - 1
}

const toggleCollapsed = () => {
  isCollapsed.value = !isCollapsed.value
}

const handleLookbackSelect = async (hours: number) => {
  if (isUpdatingLookback.value || hours === activeLookback.value) {
    return
  }
  isUpdatingLookback.value = true
  lookbackError.value = null
  try {
    emit('lookback-change', hours)
    await configStore.updateTaskIssueLookback(hours)
  } catch (error) {
    lookbackError.value = error instanceof Error ? error.message : 'Failed to update lookback'
  } finally {
    isUpdatingLookback.value = false
  }
}

const handleLookbackSelectString = (value: string) => {
  const parsed = Number(value)
  if (Number.isFinite(parsed)) {
    handleLookbackSelect(parsed)
  }
}

const isActionLoading = (task: TaskEventResponse) => {
  return props.itemActionLoadingIds?.includes(task.task_id) ?? false
}

const isActionDisabled = (task: TaskEventResponse) => {
  return props.itemActionDisabledIds?.includes(task.task_id) ?? false
}

const handleItemAction = (task: TaskEventResponse) => {
  if (!props.itemActionLabel || isActionDisabled(task)) {
    return
  }
  emit('item-action', task)
}

const taskTimestamp = (task: TaskEventResponse): string | null => {
  const field = props.timeField ?? 'timestamp'
  const raw = task[field] as string | undefined | null
  return raw ?? task.timestamp ?? null
}

const statusVariant = (task: TaskEventResponse) => {
  return getStatusVariant(getTaskStatusValue(task))
}

const statusLabel = (task: TaskEventResponse) => {
  return formatStatus(getTaskStatusValue(task))
}

const hasRuntime = (task: TaskEventResponse) => {
  return task.runtime !== undefined && task.runtime !== null && !Number.isNaN(Number(task.runtime))
}

const runtimeDisplay = (task: TaskEventResponse) => {
  if (task.runtime === undefined || task.runtime === null) {
    return '-'
  }
  const runtime = Number(task.runtime)
  if (Number.isNaN(runtime)) {
    return '-'
  }
  return `${runtime.toFixed(2)}s`
}
</script>
