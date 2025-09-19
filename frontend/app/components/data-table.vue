<script setup lang="ts" generic="TData, TValue">
import type { ColumnDef } from '@tanstack/vue-table'
import { ref } from 'vue'
import {
  FlexRender,
  getCoreRowModel,
  getSortedRowModel,
  getExpandedRowModel,
  getPaginationRowModel,
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
import { ChevronRight, ChevronDown, Clock, Hash, Database, Cpu, AlertTriangle, ChevronLeft, ChevronsLeft, ChevronsRight } from 'lucide-vue-next'
import {Badge} from "~/components/ui/badge";
import StatusDot from "~/components/StatusDot.vue";
import CopyButton from "~/components/CopyButton.vue";

const props = defineProps<{
  columns: ColumnDef<TData, TValue>[]
  data: TData[]
  isLiveMode: ComputedRef<boolean>
  secondsSinceUpdate?: number
  pageIndex: ComputedRef<number>
  pageSize: ComputedRef<number>
  pagination?: ComputedRef<any>
  isLoading?: ComputedRef<boolean>
}>()

const emit = defineEmits<{
  toggleLiveMode: []
  setPageIndex: [index: number]
  setPageSize: [size: number]
}>()

// Track expanded rows
const expandedRows = ref(new Set<string>())

const table = useVueTable({
  get data() { return props.data },
  get columns() { return props.columns },
  getCoreRowModel: getCoreRowModel(),
  getSortedRowModel: getSortedRowModel(),
  getExpandedRowModel: getExpandedRowModel(),
  getPaginationRowModel: getPaginationRowModel(),
  state: {
    get pagination() {
      return {
        pageIndex: props.pageIndex.value,
        pageSize: props.pageSize.value,
      }
    },
    get sorting() {
      return [
        {
          id: 'started_at',
          desc: true
        }
      ]
    }
  },
  onPaginationChange: (updater) => {
    if (typeof updater === 'function') {
      const newState = updater({
        pageIndex: props.pageIndex.value,
        pageSize: props.pageSize.value,
      })
      emit('setPageIndex', newState.pageIndex)
      emit('setPageSize', newState.pageSize)
    }
  },
  manualPagination: true, // Enable server-side pagination
  pageCount: props.pagination?.value?.total_pages || 1,
})

// Toggle row expansion
const toggleRowExpansion = (rowId: string) => {
  if (expandedRows.value.has(rowId)) {
    expandedRows.value.delete(rowId)
  } else {
    expandedRows.value.add(rowId)
  }
}

</script>

<template>
  <div class="border rounded-md">
    <!-- Header with live mode controls -->
    <div class="flex items-center border-card-border justify-between p-4 border-b">
      <div class="flex items-center gap-3">
        <!-- Live mode indicator badge -->
        <Badge
          v-if="isLiveMode.value"
          class="bg-green-950/20 text-green-400 border-green-900/20 px-2 py-0.5"
        >
          <StatusDot status="success" :pulse="true" class="mr-1.5" />
          LIVE
        </Badge>
        
        <!-- Last updated timestamp -->
        <div
          v-if="isLiveMode"
          class="text-sm text-gray-500"
        >
          Last updated: {{ secondsSinceUpdate }} seconds ago
        </div>
      </div>
      
      <!-- Live mode toggle button -->
      <Button
        @click="emit('toggleLiveMode')"
        :variant="'outline'"
        class="bg-background-primary/80 hover:bg-background-primary hover:cursor-pointer"
        size="sm"
      >
        {{ isLiveMode.value ? 'Stop Live Mode' : 'Start Live Mode' }}
      </Button>
    </div>

    <Table>
      <TableHeader>
        <TableRow class="border-card-border" v-for="headerGroup in table.getHeaderGroups()" :key="headerGroup.id">
          <TableHead class="w-12"></TableHead> <!-- Empty header for expand/collapse column -->
          <TableHead v-for="header in headerGroup.headers" :key="header.id">
            <FlexRender
              v-if="!header.isPlaceholder" :render="header.column.columnDef.header"
              :props="header.getContext()"
            />
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <template v-if="table.getRowModel().rows?.length">
          <template v-for="row in table.getRowModel().rows" :key="row.id">
            <TableRow
              class="border-card-border cursor-pointer hover:bg-background-primary/10"
              @click="toggleRowExpansion(row.id)"
            >
              <TableCell class="w-12">
                <ChevronRight v-if="!expandedRows.has(row.id)" class="h-4 w-4 text-gray-400" />
                <ChevronDown v-else class="h-4 w-4 text-gray-400" />
              </TableCell>
              <TableCell v-for="cell in row.getVisibleCells()" :key="cell.id">
                <FlexRender :render="cell.column.columnDef.cell" :props="cell.getContext()" />
              </TableCell>
            </TableRow>
            
            <!-- Expanded row with detailed information -->
            <TableRow v-if="expandedRows.has(row.id)" class="bg-muted/30 border-card-border">
              <TableCell :colspan="columns.length + 1" class="p-0">
                <div class="px-8 py-6">
                  <!-- Task Details Grid -->
                  <div class="grid grid-cols-2 md:grid-cols-4 gap-6 text-sm mb-2">
                    <!-- Task ID -->
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
                    
                    <!-- Queue -->
                    <div class="flex items-center gap-1.5">
                      <Database class="h-3.5 w-3.5 text-gray-400" />
                      <span class="text-gray-500">Queue:</span>
                      <span class="font-medium text-sm">{{ row.original.routing_key || 'default' }}</span>
                    </div>
                    
                    <!-- Worker -->
                    <div v-if="row.original.hostname" class="flex items-center gap-1.5">
                      <Cpu class="h-3.5 w-3.5 text-gray-400" />
                      <span class="text-gray-500">Worker:</span>
                      <span class="font-medium text-sm">{{ row.original.hostname }}</span>
                    </div>
                    
                    <!-- ETA -->
                    <div v-if="row.original.eta" class="flex items-center gap-1.5">
                      <Clock class="h-3.5 w-3.5 text-gray-400" />
                      <span class="text-gray-500">ETA:</span>
                      <span class="font-medium text-sm">{{ row.original.eta }}</span>
                    </div>
                  </div>
                  
                  <!-- Content Cards -->
                  <div class="space-y-2">
                    <!-- Arguments & Kwargs Cards -->
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
                      <Card v-if="row.original.args" class="p-4">
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
                      </Card>
                      
                      <Card v-if="row.original.kwargs" class="p-4">
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
                      </Card>
                    </div>
                    
                    <!-- Result Card -->
                    <Card v-if="row.original.result" class="p-4">
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
                    </Card>
                    
                    <!-- Error/Traceback Card -->
                    <Card v-if="row.original.traceback" class="p-4">
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
                    </Card>
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
    
    <!-- Pagination Controls -->
    <div class="flex items-center justify-between p-4 border-t border-card-border">
      <div class="flex items-center space-x-2">
        <span v-if="isLoading?.value" class="text-sm text-gray-500">
          Loading...
        </span>
        <span v-else class="text-sm text-gray-500">
          Showing {{ (pagination?.value?.page || 0) * (pagination?.value?.limit || 10) + 1 }} to 
          {{ Math.min(((pagination?.value?.page || 0) + 1) * (pagination?.value?.limit || 10), pagination?.value?.total || 0) }} 
          of {{ pagination?.value?.total || 0 }} entries
        </span>
      </div>
      
      <div class="flex items-center space-x-2">
        <!-- Page size selector -->
        <div class="flex items-center space-x-2">
          <span class="text-sm text-gray-500">Show</span>
          <select 
            :value="table.getState().pagination.pageSize"
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
        
        <!-- Page navigation -->
        <div class="flex items-center space-x-1">
          <Button
            variant="outline"
            size="sm"
            @click="emit('setPageIndex', 0)"
            :disabled="!pagination?.value?.has_prev || isLoading?.value"
            class="h-8 w-8 p-0"
          >
            <ChevronsLeft class="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            @click="emit('setPageIndex', (pagination?.value?.page || 0) - 1)"
            :disabled="!pagination?.value?.has_prev || isLoading?.value"
            class="h-8 w-8 p-0"
          >
            <ChevronLeft class="h-4 w-4" />
          </Button>
          
          <span class="px-2 text-sm text-gray-500">
            Page {{ (pagination?.value?.page || 0) + 1 }} of {{ pagination?.value?.total_pages || 1 }}
          </span>
          
          <Button
            variant="outline"
            size="sm"
            @click="emit('setPageIndex', (pagination?.value?.page || 0) + 1)"
            :disabled="!pagination?.value?.has_next || isLoading?.value"
            class="h-8 w-8 p-0"
          >
            <ChevronRight class="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            @click="emit('setPageIndex', (pagination?.value?.total_pages || 1) - 1)"
            :disabled="!pagination?.value?.has_next || isLoading?.value"
            class="h-8 w-8 p-0"
          >
            <ChevronsRight class="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>
