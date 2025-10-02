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
import { Input } from '@/components/ui/input'
import { ChevronRight, ChevronDown, Clock, Hash, Database, Cpu, AlertTriangle, ChevronLeft, ChevronsLeft, ChevronsRight, ArrowUpDown, ArrowUp, ArrowDown, Search, RefreshCw, CornerDownRight } from 'lucide-vue-next'
import {Badge} from "~/components/ui/badge";
import StatusDot from "~/components/StatusDot.vue";
import CopyButton from "~/components/CopyButton.vue";
import SearchInput from "~/components/SearchInput.vue";
import RetryChain from "~/components/RetryChain.vue";
// Task API is now handled via stores (auto-imported)

interface Filter {
  key: string
  value: string
}

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
  filters?: Filter[]
}>()

const emit = defineEmits<{
  toggleLiveMode: []
  setPageIndex: [index: number]
  setPageSize: [size: number]
  setSorting: [sorting: { id: string; desc: boolean }[]]
  setSearchQuery: [query: string]
  setFilters: [filters: Filter[]]
}>()

const expandedRows = ref(new Set<string>())

const searchInput = ref(props.searchQuery || '')
let searchTimeout: ReturnType<typeof setTimeout> | null = null

// Use tasks store for retry functionality
const tasksStore = useTasksStore()
const isRetrying = computed(() => tasksStore.isLoading)

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

const toggleRowExpansion = (taskId: string) => {
  if (expandedRows.value.has(taskId)) {
    expandedRows.value.delete(taskId)
  } else {
    expandedRows.value.add(taskId)
  }
}

const handleRetry = async (taskId: string) => {
  try {
    const result = await tasksStore.retryTask(taskId)
    console.log('Task retried successfully:', result)
    // You can add a toast notification here if you have a notification system
  } catch (error) {
    console.error('Failed to retry task:', error)
    // You can add error notification here
  }
}

</script>

<template>
  <div class="border rounded-md">
    <!-- Header with search and live mode controls -->
    <div class="flex items-center border-card-border justify-between p-4 border-b">
      <div class="flex items-center gap-3 flex-1">
        <!-- Search input with filters -->
        <SearchInput
          :model-value="searchInput"
          :filters="filters || []"
          @update:model-value="handleSearch"
          @update:filters="emit('setFilters', $event)"
        />
        

      </div>
      
      <!-- Live mode indicator badge -->
      <Badge
        v-if="isLiveMode"
        @click="emit('toggleLiveMode')"
        class="bg-green-950/30 text-green-400 border-green-800/40 px-2 py-0.5
         hover:bg-green-950/50 hover:border-green-700/60 transition-colors cursor-pointer"
      >
        <StatusDot status="success" :pulse="true" class="mr-1.5" />
        Live
      </Badge>
      <Badge
        v-else
        @click="emit('toggleLiveMode')"
        class="bg-gray-800/40 text-gray-300 border-gray-600/60 px-2 py-0.5
         hover:bg-gray-700/30 hover:text-gray-300 hover:border-gray-600/80
         transition-colors cursor-pointer group"
      >
        <StatusDot status="muted" class="mr-1.5" />
        Start Live Mode
      </Badge>
    </div>

    <Table>
      <TableHeader>
        <TableRow class="border-card-border" v-for="headerGroup in table.getHeaderGroups()" :key="headerGroup.id">
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
              class="border-card-border cursor-pointer hover:bg-background-primary/10"
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
            
            
            <TableRow v-if="expandedRows.has(row.original.task_id)" class="bg-muted/30 border-card-border">
              <TableCell :colspan="columns.length + 1" class="p-0">
                <div class="px-8 py-6">
                  
                  <!-- Retry Button Section -->
                  <div class="flex items-center justify-between mb-6 pb-4 border-b border-card-border">
                    <div class="flex items-center gap-2">
                      <h3 class="text-base font-medium text-gray-300">Task Actions</h3>
                    </div>
                    <div class="flex items-center gap-2">
                      <Button 
                        @click="handleRetry(row.original.task_id)"
                        :disabled="isRetrying"
                        size="sm"
                        variant="outline"
                        class="flex items-center gap-2 hover:bg-blue-950/30 hover:border-blue-800/60 transition-colors"
                      >
                        <RefreshCw :class="{'animate-spin': isRetrying}" class="h-4 w-4" />
                        {{ isRetrying ? 'Retrying...' : 'Retry Task' }}
                      </Button>
                    </div>
                  </div>
                  
                  <div class="grid grid-cols-2 md:grid-cols-4 gap-6 text-sm mb-2">
                    
                    <div class="flex items-center gap-1.5">
                      <Hash class="h-3.5 w-3.5 text-gray-400" />
                      <span class="text-gray-500">ID:</span>
                      <code class="text-xs bg-background-primary px-1 py-0.5 rounded">{{ row.original.task_id }}</code>
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
                  
                  <!-- Retry Chain Section -->
                  <div v-if="row.original.is_retry || row.original.has_retries" 
                       class="mb-6 p-4 border border-card-border rounded-md bg-card-base">
                    <RetryChain
                      :current-task="row.original"
                      :parent-task="row.original.retry_of ? { 
                        task_id: row.original.retry_of, 
                        status: row.original.parent_status || 'unknown',
                        timestamp: row.original.parent_timestamp
                      } : undefined"
                      :retries="row.original.retried_by ? row.original.retried_by.map((id, index) => ({
                        task_id: id,
                        status: row.original.retry_statuses?.[index] || 'unknown',
                        timestamp: row.original.retry_timestamps?.[index],
                        retry_number: index + 2
                      })) : []"
                      :show-details="false"
                    />
                  </div>
                  
                  <div class="space-y-2">
                    
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
                      <div v-if="row.original.args" class="p-4 border border-card-border rounded-md bg-card-base">
                        <div class="flex items-center justify-between mb-3">
                          <h4 class="text-sm font-medium text-gray-500">Arguments:</h4>
                          <CopyButton 
                            :text="row.original.args"
                            :copy-key="`args-${row.original.task_id}`"
                            title="Copy arguments"
                            :show-text="true"
                          />
                        </div>
                        <pre class="bg-background-primary p-3 rounded text-xs overflow-x-auto">{{ row.original.args }}</pre>
                      </div>
                      
                      <div v-if="row.original.kwargs" class="p-4 border border-card-border rounded-md bg-card-base">
                        <div class="flex items-center justify-between mb-3">
                          <h4 class="text-sm font-medium text-gray-500">Keyword Arguments:</h4>
                          <CopyButton 
                            :text="row.original.kwargs"
                            :copy-key="`kwargs-${row.original.task_id}`"
                            title="Copy kwargs"
                            :show-text="true"
                          />
                        </div>
                        <pre class="bg-background-primary p-3 rounded text-xs overflow-x-auto">{{ row.original.kwargs }}</pre>
                      </div>
                    </div>
                    
                    
                    <div v-if="row.original.result" class="p-4 border border-card-border rounded-md bg-card-base">
                      <div class="flex items-center justify-between mb-3">
                        <h4 class="text-sm font-medium text-green-400">Result:</h4>
                        <CopyButton 
                          :text="typeof row.original.result === 'string' ? row.original.result : JSON.stringify(row.original.result, null, 2)"
                          :copy-key="`result-${row.original.task_id}`"
                          title="Copy result"
                          :show-text="true"
                        />
                      </div>
                      <pre class="bg-green-950/20 border border-green-900/20 p-3 rounded text-xs overflow-x-auto text-green-400 font-mono">{{ typeof row.original.result === 'string' ? row.original.result : JSON.stringify(row.original.result, null, 2) }}</pre>
                    </div>
                    
                    
                    <div v-if="row.original.traceback" class="p-4 border border-card-border rounded-md bg-card-base">
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
          <TableRow class="border-card-border">
            <TableCell :colspan="columns.length + 1" class="h-24 text-center">
              No results.
            </TableCell>
          </TableRow>
        </template>
      </TableBody>
    </Table>
    
    
    <div class="flex items-center justify-between p-4 border-t border-card-border">
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
            class="px-2 py-1 text-sm border border-card-border rounded bg-background-primary"
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
          <Button
            variant="outline"
            size="sm"
            @click="emit('setPageIndex', 0)"
            :disabled="!tasksStore.hasPrevPage"
            class="h-8 w-8 p-0"
            :class="tasksStore.hasPrevPage ? 'hover:cursor-pointer' : 'cursor-not-allowed opacity-50'"
          >
            <ChevronsLeft class="h-4 w-4" :class="tasksStore.hasPrevPage ? 'text-gray-400' : 'text-gray-600'" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            @click="emit('setPageIndex', pageIndex - 1)"
            :disabled="!tasksStore.hasPrevPage"
            class="h-8 w-8 p-0"
            :class="tasksStore.hasPrevPage ? 'hover:cursor-pointer' : 'cursor-not-allowed opacity-50'"
          >
            <ChevronLeft class="h-4 w-4" :class="tasksStore.hasPrevPage ? 'text-gray-400' : 'text-gray-600'" />
          </Button>
          
          <span class="px-2 text-sm text-gray-500">
            Page {{ pageIndex + 1 }} of {{ pagination?.total_pages || 1 }}
          </span>
          
          <Button
            variant="outline"
            size="sm"
            @click="emit('setPageIndex', pageIndex + 1)"
            :disabled="!tasksStore.hasNextPage"
            class="h-8 w-8 p-0"
            :class="tasksStore.hasNextPage ? 'hover:cursor-pointer' : 'cursor-not-allowed opacity-50'"
          >
            <ChevronRight class="h-4 w-4" :class="tasksStore.hasNextPage ? 'text-gray-400' : 'text-gray-600'" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            @click="emit('setPageIndex', (pagination?.total_pages || 1) - 1)"
            :disabled="!tasksStore.hasNextPage"
            class="h-8 w-8 p-0"
            :class="tasksStore.hasNextPage ? 'hover:cursor-pointer' : 'cursor-not-allowed opacity-50'"
          >
            <ChevronsRight class="h-4 w-4" :class="tasksStore.hasNextPage ? 'text-gray-400' : 'text-gray-600'" />
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>
