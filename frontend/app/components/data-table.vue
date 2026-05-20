<script setup lang="ts" generic="TData, TValue">
import type { ColumnDef } from '@tanstack/vue-table'
import { computed, ref } from 'vue'
import {
  FlexRender,
  getCoreRowModel,
  getExpandedRowModel,
  useVueTable,
} from '@tanstack/vue-table'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { ChevronRight, ChevronDown, Clock, Hash, Database, Cpu, AlertTriangle, ChevronLeft, ChevronsLeft, ChevronsRight, ArrowUpDown, ArrowUp, ArrowDown, Search, RefreshCw, CornerDownRight } from 'lucide-vue-next'
import { Card, CardContent } from '@/components/ui/card'

import {Badge} from "~/components/ui/badge";
import StatusDot from "~/components/StatusDot.vue";
import CopyButton from "~/components/CopyButton.vue";
import SearchInput from "~/components/SearchInput.vue";
import TimeRangeFilter from "~/components/TimeRangeFilter.vue";
import RetryChain from "~/components/RetryChain.vue";
import IconButton from "~/components/common/IconButton.vue";
import { Select } from '~/components/common'
import PythonValueViewer from "~/components/PythonValueViewer.vue";
import TimeDisplay from "~/components/TimeDisplay.vue";
import { Checkbox } from '~/components/ui/checkbox'
import { Switch } from '~/components/ui/switch'
import type { ParsedFilter } from '~/composables/useFilterParser'
import type { TimeRange } from '~/components/TimeRangeFilter.vue'
import TaskDetailsSection from '~/components/common/TaskDetailsSection.vue'
import TaskProgressSteps from '~/components/tasks/TaskProgressSteps.vue'
import TaskActionSelectionBar from '~/components/tasks/TaskActionSelectionBar.vue'
import TaskActionActivityButton from '~/components/tasks/TaskActionActivityButton.vue'
import RerunConfirmDialog from '~/components/tasks/RerunConfirmDialog.vue'
import type { BulkTaskAction } from '~/components/common/BulkActionCombobox.vue'
import type { RerunPreflightResponseDTO } from '~/services/apiClient'

const props = defineProps<{
  columns: ColumnDef<TData, TValue>[]
  data: TData[]
  isLiveMode: boolean
  secondsSinceUpdate?: number
  pageIndex: number
  pageSize: number
  pagination?: any
  isLoading?: boolean
  sorting?: { id: string; desc: boolean }[]
  searchQuery?: string
  filters?: ParsedFilter[]
  timeRange?: TimeRange
}>()

const emit = defineEmits<{
  toggleLiveMode: []
  setPageIndex: [index: number]
  setPageSize: [size: number]
  setSorting: [sorting: { id: string; desc: boolean }[]]
  setSearchQuery: [query: string]
  setFilters: [filters: ParsedFilter[]]
  setTimeRange: [range: TimeRange]
  clearTimeRange: []
}>()

const expandedRows = ref(new Set<string>())
const searchInput = ref(props.searchQuery || '')
let searchTimeout: ReturnType<typeof setTimeout> | null = null

// Use task action store for manual rerun functionality
const tasksStore = useTasksStore()
const taskActionsStore = useTaskActionsStore()
const currentRetryTaskId = ref<string | null>(null)
const singleRerunDialogOpen = ref(false)
const singleRerunPreflight = ref<RerunPreflightResponseDTO | null>(null)
const bulkMode = ref(false)
const selectedTaskIds = ref(new Set<string>())
const bulkAction = ref<BulkTaskAction>('resolve')
const rerunDialogOpen = ref(false)
const rerunPreflight = ref<RerunPreflightResponseDTO | null>(null)

const handleSearch = (value: string) => {
  searchInput.value = value
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  searchTimeout = setTimeout(() => {
    emit('setSearchQuery', value)
  }, 300)
}

const table = useVueTable({
  get data() { return props.data },
  get columns() { return props.columns },
  getRowId: (row: any) => row?.task_id ?? row?.id,
  getCoreRowModel: getCoreRowModel(),
  getExpandedRowModel: getExpandedRowModel(),
  state: {
    get sorting() {
      return props.sorting || []
    }
  },
  onSortingChange: (updater) => {
    const newSorting = typeof updater === 'function' 
      ? updater(props.sorting || [])
      : updater
    emit('setSorting', newSorting)
  },
  manualSorting: true,
})

const visibleTaskIds = computed(() =>
  table.getRowModel().rows
    .map(row => (row.original as any)?.task_id)
    .filter(Boolean)
)

const selectedCount = computed(() => selectedTaskIds.value.size)

const selectedTasks = computed(() => {
  const selected = selectedTaskIds.value
  const rows = props.data as any[]
  return rows.filter(task => selected.has(task.task_id))
})

const currentRerunTask = computed(() => {
  if (!currentRetryTaskId.value) return null
  return (props.data as any[]).find(task => task.task_id === currentRetryTaskId.value) || null
})

const headerChecked = computed(() => {
  if (visibleTaskIds.value.length === 0) return false
  const selectedVisible = visibleTaskIds.value.filter(id => selectedTaskIds.value.has(id)).length
  if (selectedVisible === 0) return false
  if (selectedVisible === visibleTaskIds.value.length) return true
  return 'indeterminate'
})

const clearSelection = () => {
  selectedTaskIds.value = new Set()
}

const setBulkMode = (checked: boolean) => {
  bulkMode.value = checked
  if (!checked) {
    clearSelection()
  }
}

const setTaskSelected = (taskId: string | undefined, checked: boolean | 'indeterminate') => {
  if (!taskId) return
  const next = new Set(selectedTaskIds.value)
  if (checked === true) {
    if (next.size >= taskActionsStore.maxSelectionSize && !next.has(taskId)) return
    next.add(taskId)
  } else {
    next.delete(taskId)
  }
  selectedTaskIds.value = next
}

const toggleVisibleSelection = (checked: boolean | 'indeterminate') => {
  const next = new Set(selectedTaskIds.value)
  if (checked === true) {
    for (const taskId of visibleTaskIds.value) {
      if (next.size >= taskActionsStore.maxSelectionSize && !next.has(taskId)) break
      next.add(taskId)
    }
  } else {
    visibleTaskIds.value.forEach(taskId => next.delete(taskId))
  }
  selectedTaskIds.value = next
}

const toggleRowExpansion = (taskId: string | undefined) => {
  if (!taskId) return
  if (expandedRows.value.has(taskId)) {
    expandedRows.value.delete(taskId)
  } else {
    expandedRows.value.add(taskId)
    // Fetch progress/steps snapshot lazily when expanding
    if (!tasksStore.getProgressSnapshot(taskId)) {
      tasksStore.getTaskProgress(taskId).catch(() => null)
    }
  }
}

const openSingleRerun = (task: any) => {
  currentRetryTaskId.value = task?.task_id || null
  singleRerunPreflight.value = null
  singleRerunDialogOpen.value = Boolean(currentRetryTaskId.value)
}

const preflightSelectedRerun = async () => {
  rerunPreflight.value = await taskActionsStore.preflightRerun(Array.from(selectedTaskIds.value))
}

const executeBulkAction = async () => {
  if (selectedTaskIds.value.size === 0) return

  if (bulkAction.value === 'rerun') {
    rerunDialogOpen.value = true
    return
  }

  await taskActionsStore.createAction(bulkAction.value, Array.from(selectedTaskIds.value))
  clearSelection()
}

const confirmSelectedRerun = async () => {
  await taskActionsStore.createAction('rerun', Array.from(selectedTaskIds.value))
  rerunDialogOpen.value = false
  rerunPreflight.value = null
  clearSelection()
}

const preflightSingleRerun = async () => {
  if (!currentRetryTaskId.value) return
  singleRerunPreflight.value = await taskActionsStore.preflightRerun([currentRetryTaskId.value])
}

const confirmSingleRerun = async () => {
  if (!currentRetryTaskId.value) return
  await taskActionsStore.createAction('rerun', [currentRetryTaskId.value])
  singleRerunDialogOpen.value = false
  singleRerunPreflight.value = null
  currentRetryTaskId.value = null
}

const cancelSingleRerun = () => {
  currentRetryTaskId.value = null
  singleRerunPreflight.value = null
}

const mapTaskToRetryChainFormat = (task: any) => {
  if (!task) return null

  const { eventTypeToStatus } = useTaskStatus()

  return {
    task_id: task.task_id || '',
    status: task.is_orphan ? 'orphaned' : eventTypeToStatus(task.event_type || 'unknown'),
    timestamp: task.timestamp || '',
    is_retry: task.is_retry || false,
    is_orphan: task.is_orphan || false,
    has_retries: task.has_retries || false,
    event_type: task.event_type || 'unknown'
  }
}

const { eventTypeToStatus, getStatusVariant, formatStatus } = useTaskStatus()

const getStatusMeta = (task: any) => {
  const status = task?.is_orphan ? 'ORPHANED' : eventTypeToStatus(task?.event_type || 'unknown')
  return {
    label: formatStatus(status),
    variant: getStatusVariant(status)
  }
}

const getRuntimeLabel = (runtime?: number | null) => {
  if (runtime === undefined || runtime === null) return '-'
  return `${runtime.toFixed(2)}s`
}

const getRetryCount = (task: any) => {
  const retriedBy = Array.isArray(task?.retried_by) ? task.retried_by.length : 0
  const retryOf = task?.retry_of ? 1 : 0
  return retriedBy + retryOf
}

const getProgressSnapshot = (taskId: string) => {
  return tasksStore.getProgressSnapshot(taskId)
}

const getProgressPercent = (snapshot: any) => snapshot?.latest?.progress ?? null
const getProgressMessage = (snapshot: any) => snapshot?.latest?.message || ''

</script>

<template>
  <div class="border border-border-subtle rounded-md bg-background-surface glow-border">
    <!-- Header with search and live mode controls -->
    <div class="flex items-center border-border-subtle justify-between p-4 border-b">
      <div class="flex items-center gap-3 flex-1">
        <!-- Search input with filters -->
        <SearchInput
          :model-value="searchInput"
          :filters="filters || []"
          @update:model-value="handleSearch"
          @update:filters="emit('setFilters', $event)"
        />

        <!-- Time Range Filter -->
        <TimeRangeFilter
          :model-value="timeRange || { start: null, end: null }"
          :disabled="isLiveMode"
          @update:model-value="emit('setTimeRange', $event)"
          @clear="emit('clearTimeRange')"
          @disable-live-mode="emit('toggleLiveMode')"
        />

      </div>
      
      <div class="ml-4 flex shrink-0 items-center gap-2">
        <TaskActionActivityButton />
        <div class="inline-flex h-9 items-center gap-2 text-sm font-medium text-text-secondary">
          <span class="font-medium">Bulk</span>
          <Switch
            aria-label="Bulk mode"
            :model-value="bulkMode"
            @update:model-value="setBulkMode"
          />
        </div>

        <!-- Live mode indicator badge -->
        <Badge
          v-if="isLiveMode"
          @click="emit('toggleLiveMode')"
          variant="success"

        >
          <StatusDot status="success" :pulse="true" class="mr-1.5" />
          Live
        </Badge>
        <Badge
          v-else
          @click="emit('toggleLiveMode')"
          variant="outline"
          >
          <StatusDot status="muted" class="mr-1.5" />
          Start Live Mode
        </Badge>
      </div>
    </div>

    <TaskActionSelectionBar
      v-if="bulkMode && selectedCount > 0"
      v-model:action="bulkAction"
      :selected-count="selectedCount"
      :max-selection-size="taskActionsStore.maxSelectionSize"
      :is-loading="taskActionsStore.isCreating || taskActionsStore.isPreflighting"
      @execute="executeBulkAction"
      @clear="clearSelection"
    />

    <Table>
      <TableHeader>
        <TableRow class="border-border-subtle" v-for="headerGroup in table.getHeaderGroups()" :key="headerGroup.id">
          <TableHead v-if="bulkMode" class="w-10 pl-4 pr-0">
            <Checkbox
              :checked="headerChecked"
              aria-label="Select visible tasks"
              @update:checked="toggleVisibleSelection"
            />
          </TableHead>
          <TableHead class="w-12"></TableHead>
          <TableHead
            v-for="header in headerGroup.headers"
            :key="header.id"
            :class="header.column.columnDef.meta?.columnClass"
          >
            <div
              v-if="!header.isPlaceholder"
              :class="{
                'cursor-pointer select-none flex items-center gap-2': header.column.getCanSort(),
                'cursor-default': !header.column.getCanSort()
              }"
              @click="header.column.getCanSort() ? header.column.getToggleSortingHandler()?.({}) : undefined"
            >
              <FlexRender
                :render="header.column.columnDef.header"
                :props="header.getContext()"
              />
              <div v-if="header.column.getCanSort()" class="ml-auto">
                <ArrowUpDown v-if="!header.column.getIsSorted()" class="h-4 w-4 text-gray-400" />
                <ArrowUp v-else-if="header.column.getIsSorted() === 'asc'" class="h-4 w-4 text-gray-300" />
                <ArrowDown v-else-if="header.column.getIsSorted() === 'desc'" class="h-4 w-4 text-gray-300" />
              </div>
            </div>
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <template v-if="table.getRowModel().rows?.length">
          <template v-for="row in table.getRowModel().rows" :key="row.id">
            <TableRow
              class="border-border-subtle cursor-pointer hover:bg-background-hover-subtle transition-colors duration-150"
              @click="toggleRowExpansion(row.original.task_id)"
            >
              <TableCell v-if="bulkMode" class="w-10 pl-4 pr-0" @click.stop>
                <Checkbox
                  :checked="selectedTaskIds.has(row.original.task_id)"
                  :aria-label="`Select task ${row.original.task_id}`"
                  @update:checked="setTaskSelected(row.original.task_id, $event)"
                />
              </TableCell>
              <TableCell class="w-12">
                <ChevronRight class="h-4 w-4 text-gray-400 transition-transform duration-200 ease-in-out"
                  :class="expandedRows.has(row.original.task_id) ? 'rotate-90' : 'rotate-0'"/>
              </TableCell>
              <TableCell
                v-for="cell in row.getVisibleCells()"
                :key="cell.id"
                :class="cell.column.columnDef.meta?.columnClass"
              >
                <FlexRender :render="cell.column.columnDef.cell" :props="cell.getContext()" />
              </TableCell>
            </TableRow>
            
            
            <TableRow class="bg-background-raised border-border-subtle cursor-default">
              <TableCell :colspan="columns.length + 1 + (bulkMode ? 1 : 0)" class="p-0">
                <Transition
                  enter-active-class="transition-[opacity,transform,max-height] duration-250 ease-out"
                  enter-from-class="opacity-0 -translate-y-1 max-h-[0px]"
                  enter-to-class="opacity-100 translate-y-0 max-h-[500px]"
                  leave-active-class="transition-[opacity,transform,max-height] duration-150 ease-in"
                  leave-from-class="opacity-100 translate-y-0 max-h-[500px]"
                  leave-to-class="opacity-0 -translate-y-1 max-h-[0px]"
                >
                <div v-if="expandedRows.has(row.original.task_id)" >
                  <TaskDetailsSection
                    :task-name="row.original.human_readable_name || row.original.task_name || 'Task'"
                    :status-label="getStatusMeta(row.original).label"
                    :status-variant="getStatusMeta(row.original).variant"
                    :started-timestamp="row.original.timestamp"
                    :runtime-label="getRuntimeLabel(row.original.runtime)"
                    :retry-label="getRetryCount(row.original)"
                    :task-id="row.original.task_id"
                    :routing-key="row.original.routing_key"
                    :hostname="row.original.hostname"
                    :args="row.original.args"
                    :kwargs="row.original.kwargs"
                    :result="row.original.result"
                    :traceback="row.original.traceback"
                  >
                    <template #meta-extra>
                      <div v-if="getProgressPercent(getProgressSnapshot(row.original.task_id)) !== null" class="flex items-center gap-2">
                        <span class="text-[11px] uppercase text-text-muted tracking-wider">Progress</span>
                        <span class="text-xs font-mono text-text-primary">
                          {{ Math.round(getProgressPercent(getProgressSnapshot(row.original.task_id)) as number) }}%
                        </span>
                      </div>
                    </template>
                    <template #actions>
                      <NuxtLink :to="`/tasks/${row.original.task_id}`">
                        <Button
                          variant="outline"
                          size="xs"
                        >
                          <ChevronRight class="h-4 w-4" />
                          Open
                        </Button>
                      </NuxtLink>
                      <Button
                        variant="outline"
                        size="xs"
                        @click="openSingleRerun(row.original)"
                        :disabled="taskActionsStore.isCreating"
                        :loading="taskActionsStore.isCreating && currentRetryTaskId === row.original.task_id"    
                      >
                        <RefreshCw class="h-4 w-4" />
                        Rerun
                      </Button>
                    </template>

                    <!-- Retry Chain Section -->
                    <div v-if="row.original.is_retry || row.original.has_retries"
                         class="p-4 border border-border-subtle rounded-md bg-background-surface">
                      <RetryChain
                        :current-task="mapTaskToRetryChainFormat(row.original)"
                        :parent-task="row.original.retry_of ? mapTaskToRetryChainFormat(row.original.retry_of) : undefined"
                        :retries="row.original.retried_by ? row.original.retried_by
                          .map((retryTask, index) => {
                            const mapped = mapTaskToRetryChainFormat(retryTask)
                            return mapped ? { ...mapped, retry_number: index + 2 } : null
                          })
                          .filter(task => task !== null) : []"
                        :show-details="false"
                      />
                    </div>

                    <!-- Progress & Steps -->
                    <div
                      v-if="getProgressSnapshot(row.original.task_id)"
                      class="p-4 border border-border-subtle rounded-md bg-background-surface space-y-3"
                    >
                      <div
                        v-if="getProgressPercent(getProgressSnapshot(row.original.task_id)) !== null"
                        class="flex items-center justify-between gap-3"
                      >
                        <h4 class="text-sm font-medium text-text-primary">Progress</h4>
                        <span class="text-xs font-mono text-text-primary">
                          {{ Math.round(getProgressPercent(getProgressSnapshot(row.original.task_id)) as number) }}%
                        </span>
                      </div>
                      <div
                        v-if="getProgressPercent(getProgressSnapshot(row.original.task_id)) !== null"
                        class="h-2 rounded-full bg-border-subtle overflow-hidden"
                      >
                        <div
                          class="h-full bg-primary transition-all duration-300"
                          :style="{ width: `${getProgressPercent(getProgressSnapshot(row.original.task_id)) || 0}%` }"
                        />
                      </div>
                      <p v-if="getProgressMessage(getProgressSnapshot(row.original.task_id))" class="text-xs text-text-muted">
                        {{ getProgressMessage(getProgressSnapshot(row.original.task_id)) }}
                      </p>

                      <div v-if="getProgressSnapshot(row.original.task_id)?.steps?.length" class="pt-2">
                        <TaskProgressSteps :snapshot="getProgressSnapshot(row.original.task_id)" />
                      </div>
                    </div>
                    
                  </TaskDetailsSection>
                </div>
                </Transition>
              </TableCell>
            </TableRow>
          </template>
        </template>
        <template v-else>
          <TableRow class="border-border-subtle">
            <TableCell :colspan="columns.length + 1 + (bulkMode ? 1 : 0)" class="h-24 text-center">
              No results.
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
          Showing {{ pageIndex * pageSize + 1 }} to 
          {{ Math.min((pageIndex + 1) * pageSize, pagination?.total || 0) }} 
          of {{ pagination?.total || 0 }} entries
        </span>
      </div>
      
      <div class="flex items-center space-x-2">
        
        <div class="flex items-center space-x-2">
          <span class="text-sm text-gray-500">Show</span>
          <Select
            :model-value="pageSize"
            @update:model-value="(val) => emit('setPageSize', parseInt(val))"
            size="sm"
          >
            <option value="5">5</option>
            <option value="10">10</option>
            <option value="20">20</option>
            <option value="50">50</option>
            <option value="100">100</option>
          </Select>
          <span class="text-sm text-gray-500">per page</span>
        </div>
        
        
        <div class="flex items-center space-x-1">
          <IconButton
            :icon="ChevronsLeft"
            variant="ghost"
            size="md"
            @click="emit('setPageIndex', 0)"
            :disabled="!tasksStore.hasPrevPage"
          />
          <IconButton
            :icon="ChevronLeft"
            variant="ghost"
            size="md"
            @click="emit('setPageIndex', pageIndex - 1)"
            :disabled="!tasksStore.hasPrevPage"
          />

          <span class="px-2 text-sm text-gray-500">
            Page {{ pageIndex + 1 }} of {{ pagination?.total_pages || 1 }}
          </span>

          <IconButton
            :icon="ChevronRight"
            variant="ghost"
            size="md"
            @click="emit('setPageIndex', pageIndex + 1)"
            :disabled="!tasksStore.hasNextPage"
          />
          <IconButton
            :icon="ChevronsRight"
            variant="ghost"
            size="md"
            @click="emit('setPageIndex', (pagination?.total_pages || 1) - 1)"
            :disabled="!tasksStore.hasNextPage"
          />
        </div>
      </div>
    </div>
  </div>

  <RerunConfirmDialog
    v-model:open="singleRerunDialogOpen"
    :task-ids="currentRetryTaskId ? [currentRetryTaskId] : []"
    :tasks="currentRerunTask ? [currentRerunTask] : []"
    :preflight="singleRerunPreflight"
    :is-loading="taskActionsStore.isCreating"
    :is-preflighting="taskActionsStore.isPreflighting"
    @preflight="preflightSingleRerun"
    @confirm="confirmSingleRerun"
    @cancel="cancelSingleRerun"
  />

  <RerunConfirmDialog
    v-model:open="rerunDialogOpen"
    :task-ids="Array.from(selectedTaskIds)"
    :tasks="selectedTasks"
    :preflight="rerunPreflight"
    :is-loading="taskActionsStore.isCreating"
    :is-preflighting="taskActionsStore.isPreflighting"
    @preflight="preflightSelectedRerun"
    @confirm="confirmSelectedRerun"
    @cancel="rerunPreflight = null"
  />
</template>
