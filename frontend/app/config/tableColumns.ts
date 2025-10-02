import { h } from 'vue'
import type { ColumnDef } from '@tanstack/vue-table'
import { formatTime, calculateDuration } from '~/composables/useDateTimeFormatters'
import { Badge } from '~/components/ui/badge'
import type { TaskEventResponse } from '~/services/apiClient'

export function getTaskColumns(): ColumnDef<TaskEventResponse>[] {
  return [
    {
      accessorKey: 'task_name', 
      header: 'Task Name',
      cell: ({ row }) => h("div", { class: "font-medium" }, row.getValue("task_name")),
      enableSorting: true
    },
    {
      accessorKey: 'event_type',
      header: 'Status',
      cell: ({ row }) => {
        const { eventTypeToStatus, getStatusVariant, formatStatus } = useTaskStatus()
        const eventType = row.getValue('event_type') as string
        const status = eventTypeToStatus(eventType)
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
      cell: ({ row }) => h("div", { class: "text-sm" }, formatTime(row.getValue("timestamp"))),
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