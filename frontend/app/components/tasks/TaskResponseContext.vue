<script setup lang="ts">
import { computed } from 'vue'
import { BookOpen, ExternalLink, MessageSquareText, Siren } from 'lucide-vue-next'
import { Badge } from '~/components/ui/badge'

const props = defineProps<{
  runbookUrl?: string | null
  severityDefault?: 'info' | 'warning' | 'error' | 'critical' | null
  responseNotes?: string | null
  compact?: boolean
}>()

const hasResponseContext = computed(() =>
  Boolean(props.runbookUrl || props.severityDefault || props.responseNotes)
)

const severityLabel = computed(() => {
  if (!props.severityDefault) return null
  return props.severityDefault.charAt(0).toUpperCase() + props.severityDefault.slice(1)
})

const severityVariant = computed(() => {
  switch (props.severityDefault) {
    case 'critical':
      return 'destructive'
    case 'error':
      return 'failed'
    case 'warning':
      return 'pending'
    case 'info':
      return 'running'
    default:
      return 'outline'
  }
})
</script>

<template>
  <div
    v-if="hasResponseContext"
    class="rounded-lg border border-border-subtle bg-background-surface"
    :class="compact ? 'p-3' : 'p-5'"
  >
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-[10px] font-mono uppercase tracking-[0.18em] text-text-muted">
          Response Context
        </p>
        <h3 class="mt-1 text-sm font-medium text-text-primary">
          Recommended response guidance
        </h3>
      </div>

      <Badge v-if="severityLabel" :variant="severityVariant" class="text-[11px]">
        {{ severityLabel }}
      </Badge>
    </div>

    <div class="mt-4 space-y-3 text-sm">
      <a
        v-if="runbookUrl"
        :href="runbookUrl"
        target="_blank"
        rel="noreferrer"
        class="flex items-start gap-2 rounded-md border border-border-subtle bg-background-base px-3 py-2 text-text-primary transition-colors hover:border-primary/40 hover:text-primary"
      >
        <BookOpen class="mt-0.5 h-4 w-4 shrink-0" />
        <span class="min-w-0 flex-1 break-all">{{ runbookUrl }}</span>
        <ExternalLink class="mt-0.5 h-3.5 w-3.5 shrink-0" />
      </a>

      <div
        v-if="responseNotes"
        class="rounded-md border border-border-subtle bg-background-base px-3 py-2 text-text-secondary"
      >
        <div class="mb-1 flex items-center gap-2 text-text-primary">
          <MessageSquareText class="h-4 w-4" />
          <span class="text-xs font-medium uppercase tracking-wide text-text-muted">Notes</span>
        </div>
        <p class="whitespace-pre-wrap leading-6">
          {{ responseNotes }}
        </p>
      </div>

      <div
        v-if="severityLabel && !compact"
        class="flex items-center gap-2 text-xs text-text-secondary"
      >
        <Siren class="h-3.5 w-3.5" />
        Default severity is marked as <span class="font-medium text-text-primary">{{ severityLabel }}</span>.
      </div>
    </div>
  </div>
</template>
