<template>
  <div 
    class="border border-border rounded-lg overflow-hidden glow-border transition-all duration-300"
    :class="summaryClasses">
      
      <!-- Collapsed Summary View -->
      <div 
        class="py-2 px-4 cursor-pointer hover:bg-background-surface/5 transition-all duration-200"
        @click="toggleExpanded"
      >
      <div class="flex items-center justify-between">
        
        <!-- Left: Status Overview -->
        <div class="flex items-center gap-3">
          <div class="flex items-center gap-2">
              <StatusDot status="warning"/>
            <span class="font-medium text-sm">Orphans detected</span>
          </div>
          
          <!-- Quick Stats -->
          <div class="hidden sm:flex items-center gap-2 text-xs text-text-secondary">
            <span class="flex items-center gap-1">
              <span class="font-mono">{{ uniqueOrphanedTasksCount }}</span>
              <span>detected</span>
            </span>
            <span v-if="recentOrphansCount > 0" class="flex items-center gap-1 text-status-warning">
              <span class="font-mono">{{ recentOrphansCount }}</span>
              <span>recent</span>
            </span>
          </div>
        </div>

        <!-- Right: Expand Button -->
        <div class="flex items-center gap-2">
          <span class="text-xs text-text-muted hidden sm:inline">
            {{ isExpanded ? 'Hide details' : 'View details' }}
          </span>
          <svg 
            class="w-4 h-4 text-text-muted transition-transform duration-200"
            :class="{ 'rotate-180': isExpanded }"
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>

      <!-- Mobile Quick Stats (when collapsed) -->
      <div v-if="!isExpanded" class="sm:hidden flex items-center gap-4 text-xs text-text-secondary mt-2 pt-2 border-t border-border/50">
        <span class="flex items-center gap-1">
          <span class="font-mono">{{ uniqueOrphanedTasksCount }}</span>
          <span>detected</span>
        </span>
        <span v-if="recentOrphansCount > 0" class="flex items-center gap-1 text-status-warning">
          <span class="font-mono">{{ recentOrphansCount }}</span>
          <span>recent</span>
        </span>
      </div>
    </div>

    <!-- Expanded Orphan Tasks Table -->
    <div 
      v-if="isExpanded" 
      class="border-t border-border bg-background-surface"
    >
      <div v-if="uniqueOrphanedTasks.length > 0">
        <!-- Header with search controls -->
        <div class="flex items-center border-border justify-between p-4 border-b">
          <div class="flex items-center gap-3 flex-1">
            <!-- Search input -->
            <SearchInput
              :model-value="searchInput"
              :filters="[]"
              @update:model-value="handleSearch"
              @update:filters="() => {}"
            />
          </div>
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
                  class="border-border cursor-pointer hover:bg-background-surface/10"
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
                
                <!-- Expanded Row Details -->
                <TableRow v-if="expandedRows.has(row.original.task_id)" class="bg-muted/30 border-border">
                  <TableCell :colspan="orphanColumns.length + 1" class="p-0">
                    <div class="px-8 py-6">
                      <div class="grid grid-cols-2 md:grid-cols-4 gap-6 text-sm mb-2">
                        
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
                        
                        <div v-if="row.original.orphaned_at" class="flex items-center gap-1.5">
                          <Clock class="h-3.5 w-3.5 text-gray-400" />
                          <span class="text-gray-500">Orphaned:</span>
                          <span class="font-medium text-sm">{{ formatTime(row.original.orphaned_at) }}</span>
                        </div>
                      </div>
                    </div>
                  </TableCell>
                </TableRow>
              </template>
            </template>
            <template v-else>
              <TableRow class="border-border">
                <TableCell :colspan="orphanColumns.length + 1" class="h-24 text-center">
                  No results.
                </TableCell>
              </TableRow>
            </template>
          </TableBody>
        </Table>
        
        <!-- Pagination -->
        <div class="flex items-center justify-between p-4 border-t border-border">
          <div class="flex items-center space-x-2">
            <span class="text-sm text-gray-500">
              Showing {{ table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1 }} to 
              {{ Math.min((table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize, filteredTasks.length) }} 
              of {{ filteredTasks.length }} entries
            </span>
          </div>
          
          <div class="flex items-center space-x-2">
            <div class="flex items-center space-x-2">
              <span class="text-sm text-gray-500">Show</span>
              <select 
                :value="table.getState().pagination.pageSize"
                @change="(e) => table.setPageSize(parseInt((e.target as HTMLSelectElement).value))"
                class="px-2 py-1 text-sm border border-border rounded bg-background-surface"
              >
                <option value="5">5</option>
                <option value="10">10</option>
                <option value="20">20</option>
                <option value="50">50</option>
              </select>
              <span class="text-sm text-gray-500">per page</span>
            </div>
            
            <div class="flex items-center space-x-1">
              <Button
                variant="outline"
                size="sm"
                @click="table.setPageIndex(0)"
                :disabled="!table.getCanPreviousPage()"
                class="h-8 w-8 p-0"
              >
                <ChevronsLeft class="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                @click="table.previousPage()"
                :disabled="!table.getCanPreviousPage()"
                class="h-8 w-8 p-0"
              >
                <ChevronLeft class="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                @click="table.nextPage()"
                :disabled="!table.getCanNextPage()"
                class="h-8 w-8 p-0"
              >
                <ChevronRight class="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                @click="table.setPageIndex(table.getPageCount() - 1)"
                :disabled="!table.getCanNextPage()"
                class="h-8 w-8 p-0"
              >
                <ChevronsRight class="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Empty State -->
      <div v-else class="text-center py-8">
        <div class="text-text-muted text-sm">
          <svg class="w-8 h-8 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p>No orphaned tasks</p>
          <p class="text-xs mt-1">Tasks are marked as orphaned when their workers go offline</p>
        </div>
      </div>
    </div>
  </div>

  <!-- Retry Confirmation Dialog -->
  <RetryTaskConfirmDialog
    ref="retryDialogRef"
    :task="currentRetryTaskId ? uniqueOrphanedTasks.find(t => t.task_id === currentRetryTaskId) || null : null"
    :is-loading="isRetrying && !!currentRetryTaskId"
    @confirm="handleRetryConfirm"
    @cancel="handleRetryCancel"
  />
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  FlexRender,
  getCoreRowModel,
  getExpandedRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useVueTable,
} from '@tanstack/vue-table'
import StatusDot from '~/components/StatusDot.vue'
import CopyButton from '~/components/CopyButton.vue'
import SearchInput from '~/components/SearchInput.vue'
import RetryTaskConfirmDialog from '~/components/RetryTaskConfirmDialog.vue'
import { formatTime } from '~/composables/useDateTimeFormatters'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ChevronRight, ChevronDown, Hash, Database, Cpu, Clock, ArrowUpDown, ArrowUp, ArrowDown, ChevronLeft, ChevronsLeft, ChevronsRight, CircleAlert, RefreshCw } from 'lucide-vue-next'
import { getOrphanTaskColumns } from '~/config/tableColumns'
import type { TaskEventResponse } from '../src/types/api'
const props = defineProps<{
  orphanedTasks: TaskEventResponse[]
  isLoading?: boolean
}>()

const emit = defineEmits<{
  'retry-task': [taskId: string]
}>()

const isExpanded = ref(false)
const expandedRows = ref(new Set<string>())
const sorting = ref<{ id: string; desc: boolean }[]>([
  { id: 'orphaned_at', desc: true }
])
const searchInput = ref('')
let searchTimeout: ReturnType<typeof setTimeout> | null = null

// Retry functionality
const orphanTasksStore = useOrphanTasksStore()
const currentRetryTaskId = ref<string | null>(null)
const isRetrying = computed(() => orphanTasksStore.isLoading)
const retryDialogRef = ref<InstanceType<typeof RetryTaskConfirmDialog> | null>(null)

// Table columns with retry functionality
const orphanColumns = getOrphanTaskColumns({
  onRetryClick: (taskId: string) => {
    currentRetryTaskId.value = taskId
    retryDialogRef.value?.open()
  },
  isRetrying: (taskId: string) => isRetrying.value && currentRetryTaskId.value === taskId
})

const toggleExpanded = () => {
  isExpanded.value = !isExpanded.value
}

const toggleRowExpansion = (taskId: string) => {
  if (expandedRows.value.has(taskId)) {
    expandedRows.value.delete(taskId)
  } else {
    expandedRows.value.add(taskId)
  }
}

const handleSearch = (value: string) => {
  searchInput.value = value
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  searchTimeout = setTimeout(() => {
    table.setPageIndex(0) // Reset to first page when searching
  }, 300)
}

// Retry handlers
const handleRetryConfirm = async () => {
  if (!currentRetryTaskId.value) return
  
  try {
    await orphanTasksStore.retryOrphanedTask(currentRetryTaskId.value)
    console.log('Orphaned task retried successfully')
    currentRetryTaskId.value = null
  } catch (error) {
    console.error('Failed to retry orphaned task:', error)
    currentRetryTaskId.value = null
  }
}

const handleRetryCancel = () => {
  currentRetryTaskId.value = null
}

// Deduplicate orphaned tasks by task_id - take the most recent event per task
const uniqueOrphanedTasks = computed(() => {
  const taskMap = new Map<string, TaskEventResponse>()
  
  // Sort by timestamp desc to get most recent events first
  const sortedTasks = [...props.orphanedTasks].sort((a, b) => {
    const aTime = new Date(a.timestamp || 0).getTime()
    const bTime = new Date(b.timestamp || 0).getTime()
    return bTime - aTime
  })
  
  // Keep only the most recent event for each task_id
  for (const task of sortedTasks) {
    if (task.task_id && !taskMap.has(task.task_id)) {
      taskMap.set(task.task_id, task)
    }
  }
  
  return Array.from(taskMap.values())
})

// Filtered data based on search
const filteredTasks = computed(() => {
  let filtered = [...uniqueOrphanedTasks.value]
  
  // Apply search filter
  if (searchInput.value) {
    const query = searchInput.value.toLowerCase()
    filtered = filtered.filter(task => 
      task.task_name?.toLowerCase().includes(query) ||
      task.task_id?.toLowerCase().includes(query) ||
      task.hostname?.toLowerCase().includes(query) ||
      task.routing_key?.toLowerCase().includes(query)
    )
  }
  
  return filtered
})

// Table setup
const table = useVueTable({
  get data() { return filteredTasks.value },
  get columns() { return orphanColumns },
  getCoreRowModel: getCoreRowModel(),
  getExpandedRowModel: getExpandedRowModel(),
  getSortedRowModel: getSortedRowModel(),
  getPaginationRowModel: getPaginationRowModel(),
  state: {
    get sorting() {
      return sorting.value
    },
  },
  initialState: {
    pagination: {
      pageIndex: 0,
      pageSize: 10,
    },
  },
  onSortingChange: (updater) => {
    const newSorting = typeof updater === 'function' 
      ? updater(sorting.value)
      : updater
    sorting.value = newSorting
  },
  manualPagination: false,
  enableSorting: true,
})


// Computed properties for status analysis
const uniqueOrphanedTasksCount = computed(() => {
  return uniqueOrphanedTasks.value.length
})

const recentOrphansCount = computed(() => {
  const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000)
  return uniqueOrphanedTasks.value.filter(task => {
    if (!task.orphaned_at) return false
    return new Date(task.orphaned_at) > oneHourAgo
  }).length
})

const overallStatus = computed((): 'online' | 'warning' | 'error' | 'muted' => {
  if (uniqueOrphanedTasksCount.value === 0) return 'online'
  if (recentOrphansCount.value > 0) return 'error'
  return 'warning'
})

const summaryClasses = computed(() => {
  const classes = ['bg-background-surface']
  
  // Add subtle background gradient
  if (recentOrphansCount.value > 0) {
    classes.push('bg-gradient-to-r from-card-base to-status-error/5')
    classes.push('glow-border-error')
  } else if (uniqueOrphanedTasksCount.value > 0) {
    classes.push('bg-gradient-to-r from-card-base to-status-warning/5')
    classes.push('glow-border-warning')
  }
  
  return classes.join(' ')
})
</script>

<style scoped>
/* Glow effects are now handled by global CSS utilities */
</style>
