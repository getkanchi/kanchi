<template>
  <div v-if="recommendations.length > 0 || !hideWhenEmpty" class="border border-border-subtle rounded-md bg-background-surface glow-border">
    <div class="flex items-center justify-between border-b border-border-subtle px-4 py-3 gap-4">
      <div class="flex items-center gap-3">
        <StatusDot :status="status" :pulse="recommendations.length > 0" class="scale-110" />
        <div>
          <div class="text-sm font-medium text-text-primary">{{ title }}</div>
          <div class="text-xs text-text-secondary">{{ recommendations.length }} active recommendation<span v-if="recommendations.length !== 1">s</span></div>
        </div>
      </div>
    </div>

    <div v-if="recommendations.length > 0" class="divide-y divide-border-subtle">
      <div v-for="item in recommendations" :key="item.recommendation_id" class="px-4 py-3">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-2">
              <Badge :variant="severityVariant(item.severity)" class="text-[11px] px-2 py-0.5">{{ severityLabel(item.severity) }}</Badge>
              <Badge variant="outline" class="text-[11px] px-2 py-0.5 border-border-subtle text-text-secondary">{{ typeLabel(item.recommendation_type) }}</Badge>
              <span class="text-sm font-medium text-text-primary">{{ item.title }}</span>
            </div>
            <p class="mt-2 text-sm text-text-secondary">{{ item.summary }}</p>
            <p class="mt-1 text-xs text-text-muted">{{ item.detail }}</p>
            <div class="mt-3 flex flex-wrap items-center gap-2 text-xs text-text-secondary">
              <Badge v-if="item.task_name" variant="outline" class="gap-2 border-border-subtle text-text-secondary">
                <span class="uppercase tracking-wide text-[9px] text-text-muted">Task</span>
                <span class="font-mono">{{ item.task_name }}</span>
              </Badge>
              <Badge v-if="item.hostname" variant="outline" class="gap-2 border-border-subtle text-text-secondary">
                <span class="uppercase tracking-wide text-[9px] text-text-muted">Worker</span>
                <span class="font-mono">{{ item.hostname }}</span>
              </Badge>
              <Badge variant="outline" class="gap-2 border-border-subtle text-text-secondary">
                <span class="uppercase tracking-wide text-[9px] text-text-muted">Scope</span>
                <span class="font-mono">{{ item.supporting_task_ids.length }} task<span v-if="item.supporting_task_ids.length !== 1">s</span></span>
              </Badge>
            </div>
          </div>
          <div v-if="item.task_id" class="flex items-center gap-2">
            <NuxtLink :to="`/tasks/${item.task_id}`">
              <Button variant="outline" size="sm" class="gap-1.5">
                <ChevronRight class="h-3.5 w-3.5" />
                Open
              </Button>
            </NuxtLink>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="px-6 py-8 text-center text-sm text-text-secondary">
      No active triage recommendations.
    </div>
  </div>
</template>

<script setup lang="ts">
import StatusDot from '~/components/StatusDot.vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ChevronRight } from 'lucide-vue-next'
import type { TriageRecommendationListItem } from '~/stores/triageRecommendations'

withDefaults(defineProps<{
  title?: string
  recommendations: TriageRecommendationListItem[]
  status?: 'success' | 'warning' | 'error' | 'info'
  hideWhenEmpty?: boolean
}>(), {
  title: 'Triage recommendations',
  status: 'info',
  hideWhenEmpty: true,
})

const severityVariant = (severity: TriageRecommendationListItem['severity']) => {
  if (severity === 'critical') return 'destructive'
  if (severity === 'warning') return 'warning'
  return 'secondary'
}

const severityLabel = (severity: TriageRecommendationListItem['severity']) => {
  if (severity === 'critical') return 'Critical'
  if (severity === 'warning') return 'Warning'
  return 'Info'
}

const typeLabel = (type: TriageRecommendationListItem['recommendation_type']) => {
  switch (type) {
    case 'stalled_progress': return 'Stalled progress'
    case 'orphaned_task': return 'Orphaned task'
    case 'repeating_failures': return 'Repeating failures'
    case 'long_running': return 'Long-running'
  }
}
</script>
