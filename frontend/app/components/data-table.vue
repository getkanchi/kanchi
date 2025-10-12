<script setup lang="ts" generic="TData, TValue">
import type { ColumnDef } from '@tanstack/vue-table'
import { ref } from 'vue'
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

import {Badge} from "~/components/ui/badge";
import StatusDot from "~/components/StatusDot.vue";
import CopyButton from "~/components/CopyButton.vue";
import SearchInput from "~/components/SearchInput.vue";
import TimeRangeFilter from "~/components/TimeRangeFilter.vue";
import RetryChain from "~/components/RetryChain.vue";
import RetryTaskConfirmDialog from "~/components/RetryTaskConfirmDialog.vue";
import BaseIconButton from "~/components/BaseIconButton.vue";
import PythonValueViewer from "~/components/PythonValueViewer.vue";
import type { ParsedFilter } from '~/composables/useFilterParser'
import type { TimeRange } from '~/components/TimeRangeFilter.vue'

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

// Use tasks store for retry functionality
const tasksStore = useTasksStore()
const isRetrying = computed(() => tasksStore.isLoading)
const currentRetryTaskId = ref<string | null>(null)
const retryDialogRef = ref<InstanceType<typeof RetryTaskConfirmDialog> | null>(null)

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

const toggleRowExpansion = (taskId: string | undefined) => {
  if (!taskId) return
  if (expandedRows.value.has(taskId)) {
    expandedRows.value.delete(taskId)
  } else {
    expandedRows.value.add(taskId)
  }
}

const handleRetryConfirm = async () => {
  if (!currentRetryTaskId.value) return
  
  try {
    const result = await tasksStore.retryTask(currentRetryTaskId.value)
    // Reset current retry task ID
    currentRetryTaskId.value = null
  } catch (error) {
    console.error('Failed to retry task:', error)
    // Reset current retry task ID on error too
    currentRetryTaskId.value = null
  }
}

const handleRetryCancel = () => {
  currentRetryTaskId.value = null
}

// Helper to map TaskEventResponse to RetryChain format with status
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

</script>

<template>
  <div class="border border-border rounded-md bg-background-surface glow-border">
    <!-- Header with search and live mode controls -->
    <div class="flex items-center border-border justify-between p-4 border-b">
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

    <Table>
      <TableHeader>
        <TableRow class="border-border" v-for="headerGroup in table.getHeaderGroups()" :key="headerGroup.id">
          <TableHead class="w-12"></TableHead>
          <TableHead v-for="header in headerGroup.headers" :key="header.id">
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
              class="border-border cursor-default hover:bg-background-hover-subtle transition-colors duration-150"
              @click="toggleRowExpansion(row.original.task_id)"
            >
              <TableCell class="w-12">
                <ChevronRight v-if="!expandedRows.has(row.original.task_id)" class="h-4 w-4 text-gray-400" />
                <ChevronDown v-else class="h-4 w-4 text-gray-400" />
              </TableCell>
              <TableCell v-for="cell in row.getVisibleCells()" :key="cell.id">
                <FlexRender :render="cell.column.columnDef.cell" :props="cell.getContext()" />
              </TableCell>
            </TableRow>
            
            
            <TableRow v-if="expandedRows.has(row.original.task_id)" class="bg-background-raised border-border">
              <TableCell :colspan="columns.length + 1" class="p-0">
                <div class="px-8 py-6">

                  <!-- Task Details and Retry Button in one line -->
                  <div class="flex items-center justify-between gap-6 text-sm mb-6">
                    <div class="flex items-center gap-6 flex-wrap">
                      <div class="flex items-center gap-1.5">
                        <Hash class="h-3.5 w-3.5 text-gray-400" />
                        <span class="text-gray-500">ID:</span>
                        <code class="text-xs bg-background-surface px-1 py-0.5 rounded">{{ row.original.task_id }}</code>
                        <CopyButton
                          :text="row.original.task_id"
                          :copy-key="`task-id-${row.original.task_id}`"
                          title="Copy task ID"
                          :show-text="true"
                        />
                      </div>

                      <div class="flex items-center gap-1.5">
                        <Database class="h-3.5 w-3.5 text-gray-400" />
                        <span class="text-gray-500">Queue:</span>
                        <span class="font-medium text-sm">{{ row.original.routing_key || 'default' }}</span>
                      </div>

                      <div v-if="row.original.hostname" class="flex items-center gap-1.5">
                        <Cpu class="h-3.5 w-3.5 text-gray-400" />
                        <span class="text-gray-500">Worker:</span>
                        <span class="font-medium text-sm">{{ row.original.hostname }}</span>
                      </div>

                      <div v-if="row.original.eta" class="flex items-center gap-1.5">
                        <Clock class="h-3.5 w-3.5 text-gray-400" />
                        <span class="text-gray-500">ETA:</span>
                        <span class="font-medium text-sm">{{ row.original.eta }}</span>
                      </div>
                    </div>

                    <!-- Retry Button -->
                    <BaseIconButton
                      :icon="RefreshCw"
                      @click="() => { currentRetryTaskId = row.original.task_id; retryDialogRef?.open() }"
                      :disabled="isRetrying"
                      :loading="isRetrying && currentRetryTaskId === row.original.task_id"
                      size="sm"
                      variant="ghost"
                    />
                  </div>
                  
                  <!-- Retry Chain Section -->
                  <div v-if="row.original.is_retry || row.original.has_retries"
                       class="mb-6 p-4 border border-border rounded-md bg-background-surface">
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
                  
                  <div class="space-y-4">

                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      <PythonValueViewer
                        v-if="row.original.args"
                        :value="row.original.args"
                        title="Arguments"
                        :copy-key="`args-${row.original.task_id}`"
                        empty-message="No arguments"
                      />

                      <PythonValueViewer
                        v-if="row.original.kwargs"
                        :value="row.original.kwargs"
                        title="Keyword Arguments"
                        :copy-key="`kwargs-${row.original.task_id}`"
                        empty-message="No keyword arguments"
                      />
                    </div>
                    
                    
                    <div v-if="row.original.result" class="p-4 border border-border rounded-md bg-background-surface">
                      <div class="flex items-center justify-between mb-3">
                        <h4 class="text-sm font-medium text-status-success">Result:</h4>
                        <CopyButton
                          :text="typeof row.original.result === 'string' ? row.original.result : JSON.stringify(row.original.result, null, 2)"
                          :copy-key="`result-${row.original.task_id}`"
                          title="Copy result"
                          :show-text="true"
                        />
                      </div>
                      <pre class="bg-status-success-bg border border-status-success-border p-3 rounded text-xs overflow-x-auto text-status-success font-mono">{{ typeof row.original.result === 'string' ? row.original.result : JSON.stringify(row.original.result, null, 2) }}</pre>
                    </div>
                    
                    
                    <div v-if="row.original.traceback" class="p-4 border border-border rounded-md bg-background-surface">
                      <div class="flex items-center justify-between mb-3">
                        <div class="flex items-center gap-1.5">
                          <AlertTriangle class="h-3.5 w-3.5 text-red-400" />
                          <h4 class="text-sm font-medium text-red-400">Error Traceback:</h4>
                        </div>
                        <CopyButton 
                          :text="row.original.traceback"
                          :copy-key="`traceback-${row.original.task_id}`"
                          title="Copy traceback"
                          :show-text="true"
                        />
                      </div>
                      <pre class="bg-red-950/20 border border-red-900/20 p-3 rounded text-xs overflow-x-auto text-red-400 font-mono">{{ row.original.traceback }}</pre>
                    </div>
                  </div>
                </div>
              </TableCell>
            </TableRow>
          </template>
        </template>
        <template v-else>
          <TableRow class="border-border">
            <TableCell :colspan="columns.length + 1" class="h-24 text-center">
              No results.
            </TableCell>
          </TableRow>
        </template>
      </TableBody>
    </Table>
    
    
    <div class="flex items-center justify-between p-4 border-t border-border">
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
          <select 
            :value="pageSize"
            @change="(e) => emit('setPageSize', parseInt((e.target as HTMLSelectElement).value))"
            class="px-2 py-1 text-sm border border-border rounded bg-background-surface"
          >
            <option value="5">5</option>
            <option value="10">10</option>
            <option value="20">20</option>
            <option value="50">50</option>
            <option value="100">100</option>
          </select>
          <span class="text-sm text-gray-500">per page</span>
        </div>
        
        
        <div class="flex items-center space-x-1">
          <BaseIconButton
            :icon="ChevronsLeft"
            variant="ghost"
            size="md"
            @click="emit('setPageIndex', 0)"
            :disabled="!tasksStore.hasPrevPage"
          />
          <BaseIconButton
            :icon="ChevronLeft"
            variant="ghost"
            size="md"
            @click="emit('setPageIndex', pageIndex - 1)"
            :disabled="!tasksStore.hasPrevPage"
          />
          
          <span class="px-2 text-sm text-gray-500">
            Page {{ pageIndex + 1 }} of {{ pagination?.total_pages || 1 }}
          </span>
          
          <BaseIconButton
            :icon="ChevronRight"
            variant="ghost"
            size="md"
            @click="emit('setPageIndex', pageIndex + 1)"
            :disabled="!tasksStore.hasNextPage"
          />
          <BaseIconButton
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

  <!-- Retry Confirmation Dialog -->
  <RetryTaskConfirmDialog
    ref="retryDialogRef"
    :task="currentRetryTaskId ? data.find(task => task.task_id === currentRetryTaskId) || null : null"
    :is-loading="isRetrying && !!currentRetryTaskId"
    @confirm="handleRetryConfirm"
    @cancel="handleRetryCancel"
  />
</template>
