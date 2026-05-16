<template>
  <div class="border border-border-subtle rounded-md bg-background-surface glow-border">
    <div class="flex items-center justify-between border-b border-border-subtle px-4 py-3">
      <div>
        <div class="text-sm font-medium text-text-primary">Failed task incidents</div>
        <div class="text-xs text-text-secondary">Grouped by fingerprint · {{ groups.length }} active group{{ groups.length === 1 ? '' : 's' }}</div>
      </div>
      <div class="text-xs text-text-muted">{{ lookbackHours }}h window</div>
    </div>

    <div v-if="groups.length === 0" class="p-8 text-sm text-text-secondary text-center">No grouped failures in this window.</div>
    <div v-else class="divide-y divide-border-subtle">
      <div v-for="group in groups" :key="group.id" class="p-4">
        <button class="flex w-full items-start justify-between gap-4 text-left" @click="toggle(group.id)">
          <div>
            <div class="flex items-center gap-2">
              <span class="font-medium text-sm text-text-primary">{{ group.task_name }}</span>
              <span class="text-[11px] rounded border border-red-500/40 bg-red-500/10 px-2 py-0.5 text-red-300">{{ group.failure_count }} failures</span>
              <span v-if="group.environment" class="text-[11px] text-text-muted">{{ group.environment }}</span>
            </div>
            <div class="mt-1 text-xs text-text-secondary">{{ group.exception_fingerprint || 'Unknown error' }}</div>
            <div class="mt-2 flex flex-wrap gap-3 text-[11px] text-text-muted">
              <span>First: {{ formatRelative(group.first_seen) }}</span>
              <span>Last: {{ formatRelative(group.last_seen) }}</span>
              <span>{{ group.recurrence_rate_per_hour }}/hr</span>
              <span v-if="group.queue">Queue {{ group.queue }}</span>
              <span v-if="group.hostname">Worker {{ group.hostname }}</span>
            </div>
          </div>
          <span class="text-xs text-text-muted">{{ expanded[group.id] ? 'Hide' : 'Show' }}</span>
        </button>

        <div v-if="expanded[group.id]" class="mt-4 space-y-2">
          <div v-if="loading[group.id]" class="text-xs text-text-muted">Loading failures…</div>
          <div v-else-if="groupEvents[group.id]?.length">
            <div v-for="event in groupEvents[group.id]" :key="event.task_id" class="rounded border border-border-subtle p-3">
              <div class="flex items-center justify-between gap-3">
                <div class="text-xs font-mono text-text-primary">{{ event.task_id }}</div>
                <NuxtLink :to="`/tasks/${event.task_id}`" class="text-xs text-primary">Open</NuxtLink>
              </div>
              <div class="mt-1 text-xs text-text-secondary">{{ event.exception || event.traceback || 'Unknown error' }}</div>
            </div>
          </div>
          <div v-else class="text-xs text-text-muted">No failure executions found.</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import type { FailureGroupSummaryResponse, TaskEventResponse } from '~/services/apiClient'

const props = defineProps<{
  groups: FailureGroupSummaryResponse[]
  lookbackHours: number
  fetchGroupEvents: (groupId: string) => Promise<TaskEventResponse[]>
}>()

const expanded = reactive<Record<string, boolean>>({})
const loading = reactive<Record<string, boolean>>({})
const groupEvents = reactive<Record<string, TaskEventResponse[]>>({})

function formatRelative(value?: string | null) {
  if (!value) return '—'
  return new Date(value).toLocaleString()
}

async function toggle(groupId: string) {
  expanded[groupId] = !expanded[groupId]
  if (!expanded[groupId] || groupEvents[groupId]) return
  loading[groupId] = true
  try {
    groupEvents[groupId] = await props.fetchGroupEvents(groupId)
  } finally {
    loading[groupId] = false
  }
}
</script>
