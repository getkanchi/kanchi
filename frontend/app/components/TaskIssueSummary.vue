<template>
  <TaskTable
    v-if="!shouldHideCard"
    collapsible
    :default-expanded="false"
    :glow="true"
    container-class="relative overflow-hidden shadow-sm"
    header-class="py-2 px-4 transition-all duration-200 hover:bg-background-surface/5"
    body-class="border-t border-border bg-background-surface/30"
  >
    <template #header="{ isExpanded }">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="flex items-center gap-2">
            <StatusDot
              :status="effectiveStatus"
              :pulse="statusDotPulse"
              class="scale-125"
            />
            <span class="font-medium text-sm">{{ title }}</span>
          </div>
          <div class="hidden sm:flex items-center gap-2 text-xs text-text-secondary">
            <span class="flex items-center gap-1">
              <span class="font-mono">{{ totalCount }}</span>
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
        <div class="flex items-center gap-2">
          <span
            v-if="isLoading"
            class="flex items-center gap-1 text-xs text-text-muted"
          >
            <Loader2 class="h-3.5 w-3.5 animate-spin" />
            Updating…
          </span>
          <span class="text-xs text-text-muted hidden sm:inline">
            {{ isExpanded ? 'Hide details' : 'View details' }}
          </span>
          <ChevronDown
            class="w-4 h-4 text-text-muted transition-transform duration-200"
            :class="{ 'rotate-180': isExpanded }"
          />
        </div>
      </div>
      <div
        v-if="!isExpanded"
        class="sm:hidden flex items-center gap-4 text-xs text-text-secondary mt-2 pt-2 border-t border-border/50"
      >
        <span class="flex items-center gap-1">
          <span class="font-mono">{{ totalCount }}</span>
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
    </template>

    <template #default>
      <div class="flex flex-col">
        <div class="flex flex-wrap items-center justify-between gap-3 px-4 py-3 border-b border-border">
          <SearchInput
            :model-value="searchQuery"
            :filters="activeFilters"
            @update:model-value="handleSearchUpdate"
            @update:filters="handleFiltersUpdate"
          />
          <div class="text-xs text-text-muted">
            <template v-if="totalFiltered > 0">
              Showing {{ pageStart }} to {{ pageEnd }} of {{ totalFiltered }} tasks
              <span v-if="showFilteredHint" class="text-text-muted/80"> (filtered from {{ totalCount }})</span>
            </template>
            <template v-else>
              No matching tasks
              <span v-if="showFilteredHint" class="text-text-muted/80"> (from {{ totalCount }})</span>
            </template>
          </div>
        </div>

        <Table>
          <TableHeader>
            <TableRow class="border-border">
              <TableHead class="w-12" />
              <TableHead>Task Name</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Time</TableHead>
              <TableHead>Runtime</TableHead>
              <TableHead>Retries</TableHead>
              <TableHead>Worker</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <template v-if="displayedTasks.length">
              <template v-for="task in displayedTasks" :key="task.task_id">
                <TableRow
                  class="border-border cursor-pointer hover:bg-background-hover-subtle transition-colors duration-150"
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
                  <span :class="['text-sm', retryClass(task)]">
                    {{ task.retries ?? 0 }}
                  </span>
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
                  class="bg-background-raised border-border"
                >
                  <TableCell :colspan="summaryColumnCount + 1" class="p-0">
                    <div class="px-8 py-6">
                      <div class="flex items-center justify-between gap-6 text-sm mb-6">
                        <div class="flex items-center gap-6 flex-wrap">
                          <div class="flex items-center gap-1.5">
                            <Hash class="h-3.5 w-3.5 text-gray-400" />
                            <span class="text-gray-500">ID:</span>
                            <code class="text-xs bg-background-surface px-1 py-0.5 rounded">{{ task.task_id }}</code>
                            <CopyButton
                              :text="task.task_id"
                              :copy-key="`task-id-${task.task_id}`"
                              title="Copy task ID"
                              :show-text="true"
                            />
                          </div>
                          <div class="flex items-center gap-1.5">
                            <Database class="h-3.5 w-3.5 text-gray-400" />
                            <span class="text-gray-500">Queue:</span>
                            <span class="font-medium text-sm">{{ task.routing_key || 'default' }}</span>
                          </div>
                          <div v-if="task.hostname" class="flex items-center gap-1.5">
                            <Cpu class="h-3.5 w-3.5 text-gray-400" />
                            <span class="text-gray-500">Worker:</span>
                            <span class="font-medium text-sm">{{ task.hostname }}</span>
                          </div>
                        </div>
                        <slot name="actions" :task="task">
                          <Button
                            v-if="itemActionLabel"
                            variant="ghost"
                            size="sm"
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
                      </div>
                      <slot name="details" :task="task">
                        <div class="space-y-4">
                          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            <PythonValueViewer
                              v-if="task.args"
                              :value="task.args"
                              title="Arguments"
                              :copy-key="`args-${task.task_id}`"
                              empty-message="No arguments"
                            />
                            <PythonValueViewer
                              v-if="task.kwargs"
                              :value="task.kwargs"
                              title="Keyword Arguments"
                              :copy-key="`kwargs-${task.task_id}`"
                              empty-message="No keyword arguments"
                            />
                          </div>
                          <div
                            v-if="task.result"
                            class="p-4 border border-border rounded-md bg-background-surface"
                          >
                            <div class="flex items-center justify-between mb-3">
                              <h4 class="text-sm font-medium text-status-success">Result:</h4>
                              <CopyButton
                                :text="formatResult(task.result)"
                                :copy-key="`result-${task.task_id}`"
                                title="Copy result"
                                :show-text="true"
                              />
                            </div>
                            <pre class="bg-status-success-bg border border-status-success-border p-3 rounded text-xs overflow-x-auto text-status-success font-mono">{{ formatResult(task.result) }}</pre>
                          </div>
                          <div
                            v-if="showException && task.exception"
                            class="p-4 border border-border rounded-md bg-background-surface"
                          >
                            <div class="flex items-center justify-between mb-3">
                              <div class="flex items-center gap-1.5">
                                <AlertTriangle class="h-3.5 w-3.5 text-red-400" />
                                <h4 class="text-sm font-medium text-red-400">Error Traceback:</h4>
                              </div>
                              <CopyButton
                                :text="task.exception"
                                :copy-key="`exception-${task.task_id}`"
                                title="Copy exception"
                                :show-text="true"
                              />
                            </div>
                            <pre class="bg-red-950/20 border border-red-900/20 p-3 rounded text-xs overflow-x-auto text-red-400 font-mono">{{ task.exception }}</pre>
                          </div>
                        </div>
                      </slot>
                    </div>
                  </TableCell>
                </TableRow>
              </template>
            </template>
            <template v-else>
              <TableRow>
                <TableCell :colspan="summaryColumnCount + 1" class="p-8">
                  <div class="flex flex-col items-center gap-2 rounded-lg border border-dashed border-border px-6 py-8 text-center">
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

        <div class="flex flex-wrap items-center justify-between gap-3 px-4 py-3 border-t border-border">
          <div class="text-sm text-gray-500">
            <span v-if="totalFiltered > 0">
              Showing {{ pageStart }} to {{ pageEnd }} of {{ totalFiltered }} entries
            </span>
            <span v-else>No tasks to display.</span>
          </div>
          <div class="flex items-center gap-3">
            <div class="flex items-center gap-2">
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
    </template>
  </TaskTable>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import StatusDot from '~/components/StatusDot.vue'
import TaskName from '~/components/TaskName.vue'
import TimeDisplay from '~/components/TimeDisplay.vue'
import CopyButton from '~/components/CopyButton.vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { TaskTable } from '~/components/common'
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
import { ChevronDown, ChevronRight, Loader2, Hash, Database, Cpu, AlertTriangle, ChevronsLeft, ChevronLeft, ChevronsRight } from 'lucide-vue-next'
import type { TaskEventResponse } from '~/services/apiClient'
import { useTaskStatus } from '~/composables/useTaskStatus'
import type { ParsedFilter } from '~/composables/useFilterParser'

const props = withDefaults(defineProps<{
  title: string
  tasks: TaskEventResponse[]
  status?: 'success' | 'warning' | 'error' | 'info'
  isLoading?: boolean
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
})

const emit = defineEmits<{
  'item-action': [task: TaskEventResponse]
}>()

const { eventTypeToStatus, getStatusVariant, formatStatus } = useTaskStatus()

const expandedTaskIds = ref(new Set<string>())
const searchQuery = ref('')
const activeFilters = ref<ParsedFilter[]>([])
const pageSize = ref(props.limit)
const currentPage = ref(0)

const summaryColumnCount = 6

const totalCount = computed(() => props.tasks.length)
const shouldHideCard = computed(() => props.hideWhenEmpty && totalCount.value === 0)

const sortedTasks = computed(() => {
  const field = props.timeField ?? 'timestamp'
  return [...props.tasks].sort((a, b) => {
    const aTime = Date.parse(String((a[field] as string | undefined) ?? a.timestamp ?? 0))
    const bTime = Date.parse(String((b[field] as string | undefined) ?? b.timestamp ?? 0))
    return bTime - aTime
  })
})

// Filter helper functions - must be defined before filteredTasks computed
const getTaskStatusValue = (task: TaskEventResponse) => {
  return task.is_orphan ? 'ORPHANED' : eventTypeToStatus(task.event_type || 'unknown')
}

const formatResult = (result: unknown): string => {
  if (typeof result === 'string') {
    return result
  }
  try {
    return JSON.stringify(result, null, 2)
  } catch {
    return String(result)
  }
}

const matchesSearch = (task: TaskEventResponse) => {
  const query = searchQuery.value.trim().toLowerCase()
  if (!query) return true

  const candidates = [
    task.task_name,
    task.task_id,
    task.hostname,
    task.routing_key,
    task.result ? formatResult(task.result) : '',
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
  return props.tasks.filter(task => {
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

watch(() => props.limit, (next) => {
  if (typeof next === 'number' && next > 0) {
    pageSize.value = next
    currentPage.value = 0
  }
})

watch(() => props.tasks, () => {
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

const retryClass = (task: TaskEventResponse) => {
  const retries = task.retries ?? 0
  return retries > 0 ? 'text-orange-500 font-medium' : 'text-gray-400'
}
</script>
