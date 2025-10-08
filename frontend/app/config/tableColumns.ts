import { h } from 'vue'
import type { ColumnDef } from '@tanstack/vue-table'
import { formatTime, calculateDuration } from '~/composables/useDateTimeFormatters'
import { Badge } from '~/components/ui/badge'
import { Button } from '~/components/ui/button'
import TaskName from '~/components/TaskName.vue'
import TimeDisplay from '~/components/TimeDisplay.vue'
import { RefreshCw } from 'lucide-vue-next'
import type { TaskEventResponse } from '~/services/apiClient'

export function getTaskColumns(): ColumnDef<TaskEventResponse>[] {
  return [
    {
      accessorKey: 'task_name',
      header: 'Task Name',
      cell: ({ row }) => {
        const taskName = row.getValue("task_name") as string

        return h(TaskName, {
          name: taskName,
          size: "sm",
          maxLength: 35,
          expandable: true
        })
      },
      enableSorting: true
    },
    {
      accessorKey: 'event_type',
      header: 'Status',
      cell: ({ row }) => {
        const { eventTypeToStatus, getStatusVariant, formatStatus } = useTaskStatus()
        const isOrphan = row.original.is_orphan
        const eventType = row.getValue('event_type') as string

        // If task is orphaned, always show ORPHANED status
        // (even if it has been retried - it WAS orphaned)
        const status = isOrphan ? 'ORPHANED' : eventTypeToStatus(eventType)
        const variant = getStatusVariant(status)

        return h(Badge, {
          variant,
          class: 'text-xs'
        }, () => formatStatus(status))
      },
      enableSorting: true
    },
    {
      accessorKey: 'timestamp',
      header: 'Time',
      cell: ({ row }) => h(TimeDisplay, {
        timestamp: row.getValue("timestamp"),
        autoRefresh: true,
        refreshInterval: 1000
      }),
      enableSorting: true,
      sortDescFirst: true
    },
    {
      accessorKey: 'runtime',
      header: 'Runtime',
      cell: ({ row }) => {
        const runtime = row.original.runtime
        if (!runtime) return h("div", { class: "text-gray-400" }, "-")
        return h("div", { class: "text-sm font-mono" }, `${runtime.toFixed(2)}s`)
      },
      enableSorting: true
    },
    {
      accessorKey: 'retries',
      header: 'Retries',
      cell: ({ row }) => {
        const retries = row.original.retries || 0
        return h("div", { 
          class: retries > 0 ? "text-orange-500 font-medium" : "text-gray-400" 
        }, retries.toString())
      },
      enableSorting: true
    },
    {
      accessorKey: 'hostname',
      header: 'Worker',
      cell: ({ row }) => {
        const hostname = row.original.hostname
        if (!hostname) return h("div", { class: "text-gray-400" }, "-")
        return h("div", { class: "text-xs font-mono" }, hostname)
      },
      enableSorting: true
    }
  ]
}

export function getOrphanTaskColumns(options?: {
  onRetryClick?: (taskId: string) => void
  isRetrying?: (taskId: string) => boolean
}): ColumnDef<TaskEventResponse>[] {
  return [
    {
      accessorKey: 'task_name', 
      header: 'Task Name',
      cell: ({ row }) => {
        const taskName = row.getValue("task_name") as string
        
        return h(TaskName, { 
          name: taskName,
          size: "sm",
          maxLength: 30,
          expandable: true
        })
      },
      enableSorting: true
    },
    {
      accessorKey: 'task_id',
      header: 'Task ID',
      cell: ({ row }) => {
        const taskId = row.getValue("task_id") as string
        return h("div", { class: "text-xs font-mono text-gray-400" }, taskId.slice(0, 8) + '...')
      },
      enableSorting: false
    },
    {
      accessorKey: 'orphaned_at',
      header: 'Orphaned At',
      cell: ({ row }) => {
        const orphanedAt = row.original.orphaned_at
        if (!orphanedAt) return h("div", { class: "text-gray-400" }, "-")
        return h(TimeDisplay, {
          timestamp: orphanedAt,
          autoRefresh: true,
          refreshInterval: 1000
        })
      },
      enableSorting: true,
      sortDescFirst: true
    },
    {
      accessorKey: 'hostname',
      header: 'Worker',
      cell: ({ row }) => {
        const hostname = row.original.hostname
        if (!hostname) return h("div", { class: "text-gray-400" }, "-")
        return h("div", { class: "text-xs font-mono" }, hostname)
      },
      enableSorting: true
    },
    {
      accessorKey: 'routing_key',
      header: 'Queue',
      cell: ({ row }) => {
        const routingKey = row.original.routing_key
        return h("div", { class: "text-xs" }, routingKey || 'default')
      },
      enableSorting: true
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => {
        const taskId = row.original.task_id
        if (!taskId || !options?.onRetryClick) return null
        
        const isTaskRetrying = options.isRetrying?.(taskId) || false
        
        return h(Button, {
          variant: 'ghost',
          class: 'h-4 w-4 p-0 min-h-0 min-w-0 transition-colors',
          disabled: isTaskRetrying,
          onClick: (e: Event) => {
            e.stopPropagation() // Prevent row expansion
            options.onRetryClick?.(taskId)
          },
          title: 'Retry Task'
        }, () => [
          h(RefreshCw, {
            class: [
              'h-2.5 w-2.5',
              isTaskRetrying ? 'animate-spin text-blue-400' : 'text-gray-400 hover:text-blue-400'
            ]
          })
        ])
      },
      enableSorting: false
    }
  ]
}
