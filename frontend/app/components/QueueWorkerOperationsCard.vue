<template>
  <div class="rounded-lg border border-border-subtle bg-background-surface p-4 space-y-4 glow-border">
    <div class="flex items-start justify-between gap-4">
      <div>
        <h3 class="text-sm font-medium text-text-primary">Queue & worker operations</h3>
        <p class="text-xs text-text-secondary">Operational context only — direct revoke/pause controls stay guarded for now.</p>
      </div>
      <span class="text-xs text-text-muted">{{ criticalQueues.length }} critical queues</span>
    </div>

    <div class="grid gap-3 lg:grid-cols-2">
      <div class="space-y-2">
        <div class="text-xs font-medium text-text-secondary uppercase tracking-wide">Queues</div>
        <div v-if="surface.queues.length === 0" class="text-xs text-text-muted">No queue activity yet.</div>
        <div v-for="queue in surface.queues.slice(0, 4)" :key="queue.queue_name" class="rounded-md border border-border-subtle p-3 space-y-1">
          <div class="flex items-center justify-between gap-2">
            <span class="font-mono text-xs">{{ queue.queue_name }}</span>
            <Badge :variant="queue.status === 'critical' ? 'destructive' : queue.status === 'warning' ? 'secondary' : 'success'">{{ queue.status }}</Badge>
          </div>
          <div class="text-xs text-text-secondary">{{ queue.summary }}</div>
          <div class="text-[11px] text-text-muted">{{ queue.active_tasks }} active · {{ queue.recent_failures }} failed · {{ queue.throughput_last_hour }} completed/hr</div>
        </div>
      </div>

      <div class="space-y-2">
        <div class="text-xs font-medium text-text-secondary uppercase tracking-wide">Workers</div>
        <div v-if="surface.workers.length === 0" class="text-xs text-text-muted">No workers detected.</div>
        <div v-for="worker in surface.workers.slice(0, 4)" :key="worker.hostname" class="rounded-md border border-border-subtle p-3 space-y-1">
          <div class="flex items-center justify-between gap-2">
            <span class="font-mono text-xs">{{ worker.hostname }}</span>
            <Badge variant="outline">{{ worker.status }}</Badge>
          </div>
          <div class="text-xs text-text-secondary">{{ worker.summary }}</div>
          <div class="text-[11px] text-text-muted">{{ worker.active_tasks }} active · {{ worker.recent_failures }} failures · queues: {{ worker.active_queues.join(', ') || '—' }}</div>
        </div>
      </div>
    </div>

    <div class="space-y-2">
      <div class="text-xs font-medium text-text-secondary uppercase tracking-wide">Operator note</div>
      <div class="flex flex-col gap-2 md:flex-row">
        <select v-model="entityType" class="rounded-md border border-border-subtle bg-background px-3 py-2 text-xs">
          <option value="queue">Queue</option>
          <option value="worker">Worker</option>
        </select>
        <input v-model="entityKey" placeholder="priority or worker-a" class="rounded-md border border-border-subtle bg-background px-3 py-2 text-xs flex-1" />
      </div>
      <textarea v-model="note" rows="2" placeholder="Record maintenance, drain, deploy, or investigation context." class="w-full rounded-md border border-border-subtle bg-background px-3 py-2 text-xs" />
      <div class="flex items-center justify-between gap-3">
        <div class="text-[11px] text-text-muted">Saved notes appear below and help future incident triage.</div>
        <Button size="sm" variant="outline" :disabled="!entityKey || !note || isSaving" @click="submit">{{ isSaving ? 'Saving…' : 'Save note' }}</Button>
      </div>
      <div class="space-y-2">
        <div v-for="saved in surface.notes.slice(0, 5)" :key="`${saved.entity_type}:${saved.entity_key}`" class="rounded-md border border-border-subtle p-2 text-xs">
          <div class="flex items-center justify-between gap-2">
            <span class="font-mono">{{ saved.entity_type }}:{{ saved.entity_key }}</span>
            <span class="text-text-muted">{{ saved.author || 'operator' }}</span>
          </div>
          <div class="mt-1 text-text-secondary">{{ saved.note }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Badge } from '~/components/ui/badge'
import { Button } from '~/components/ui/button'
import type { QueueWorkerSurfaceResponse } from '~/services/apiClient'

const props = defineProps<{
  surface: QueueWorkerSurfaceResponse
  criticalQueues: Array<{ queue_name: string }>
}>()

const emit = defineEmits<{
  save: [payload: { entity_type: 'queue' | 'worker'; entity_key: string; note: string }]
}>()

const entityType = ref<'queue' | 'worker'>('queue')
const entityKey = ref('')
const note = ref('')
const isSaving = ref(false)

async function submit() {
  if (!entityKey.value || !note.value) return
  isSaving.value = true
  try {
    emit('save', { entity_type: entityType.value, entity_key: entityKey.value.trim(), note: note.value.trim() })
    note.value = ''
  } finally {
    isSaving.value = false
  }
}
</script>
