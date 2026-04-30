<template>
  <div class="space-y-3">
    <div v-if="loading" class="space-y-3">
      <div
        v-for="idx in 3"
        :key="idx"
        class="h-24 rounded-md border border-border-subtle animate-pulse"
      />
    </div>

    <div
      v-else-if="entries.length === 0"
      class="rounded-md border border-dashed border-border-subtle px-4 py-8 text-center"
    >
      <p class="text-sm font-medium text-text-primary">{{ emptyTitle }}</p>
      <p v-if="emptyDescription" class="mt-1 text-xs text-text-muted">{{ emptyDescription }}</p>
    </div>

    <div v-else class="space-y-3">
      <div
        v-for="entry in entries"
        :key="entry.id"
        class="rounded-md border border-border-subtle bg-background-surface p-4"
      >
        <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-2">
              <Badge variant="outline" class="font-mono text-[10px] uppercase tracking-wide">
                {{ entry.source }}
              </Badge>
              <Badge :variant="statusVariant(entry.status)" class="text-[10px] uppercase tracking-wide">
                {{ entry.status }}
              </Badge>
              <span class="text-sm font-medium text-text-primary">
                {{ formatAction(entry.action_type) }}
              </span>
            </div>

            <div class="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-text-secondary">
              <span>{{ entry.actor.name }}</span>
              <span class="text-text-muted">•</span>
              <span>
                {{ entry.target_type }}
                <span class="font-mono text-text-primary">
                  {{ entry.target_label || entry.target_id }}
                </span>
              </span>
              <template v-if="entry.task_id">
                <span class="text-text-muted">•</span>
                <NuxtLink
                  :to="`/tasks/${entry.task_id}`"
                  class="font-mono text-primary hover:text-primary-hover"
                >
                  task {{ entry.task_id }}
                </NuxtLink>
              </template>
              <template v-if="entry.related_task_id">
                <span class="text-text-muted">•</span>
                <NuxtLink
                  :to="`/tasks/${entry.related_task_id}`"
                  class="font-mono text-primary hover:text-primary-hover"
                >
                  related {{ entry.related_task_id }}
                </NuxtLink>
              </template>
              <template v-if="entry.workflow_id">
                <span class="text-text-muted">•</span>
                <NuxtLink
                  :to="`/workflows/${entry.workflow_id}`"
                  class="font-mono text-primary hover:text-primary-hover"
                >
                  workflow {{ entry.workflow_id }}
                </NuxtLink>
              </template>
            </div>

            <p v-if="entry.result_summary" class="mt-3 text-sm text-text-primary">
              {{ entry.result_summary }}
            </p>
            <p v-if="entry.reason" class="mt-1 text-xs text-status-error">
              {{ entry.reason }}
            </p>
          </div>

          <div class="shrink-0 text-xs text-text-muted">
            <TimeDisplay :timestamp="entry.timestamp" layout="inline" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Badge } from '~/components/ui/badge'
import TimeDisplay from '~/components/TimeDisplay.vue'
import type { AuditLogEntryDTO } from '~/services/apiClient'

defineProps<{
  entries: AuditLogEntryDTO[]
  loading?: boolean
  emptyTitle?: string
  emptyDescription?: string
}>()

function formatAction(actionType: string): string {
  return actionType
    .replace(/^workflow\.action\./, '')
    .replace(/\./g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

function statusVariant(status: AuditLogEntryDTO['status']) {
  switch (status) {
    case 'success':
      return 'success'
    case 'failed':
      return 'destructive'
    default:
      return 'secondary'
  }
}
</script>
