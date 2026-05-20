<script setup lang="ts">
import { computed } from 'vue'
import { Badge } from '~/components/ui/badge'
import type { TaskActionItemOutcome, TaskActionStatus } from '~/services/apiClient'

const props = defineProps<{
  value: TaskActionItemOutcome | TaskActionStatus
}>()

const meta = computed(() => {
  switch (props.value) {
    case 'completed':
      return { label: 'Completed', variant: 'success' as const }
    case 'partial_success':
      return { label: 'Partial', variant: 'pending' as const }
    case 'running':
      return { label: 'Running', variant: 'running' as const }
    case 'changed':
      return { label: 'Changed', variant: 'success' as const }
    case 'noop':
      return { label: 'No-op', variant: 'outline' as const }
    case 'created':
      return { label: 'Created', variant: 'success' as const }
    case 'skipped_unavailable':
      return { label: 'Skipped', variant: 'pending' as const }
    case 'user_skipped':
      return { label: 'User skipped', variant: 'pending' as const }
    case 'blocked_skipped':
      return { label: 'Blocked', variant: 'pending' as const }
    case 'failed':
      return { label: 'Failed', variant: 'failed' as const }
    case 'pending':
      return { label: 'Pending', variant: 'pending' as const }
    default:
      return { label: String(props.value), variant: 'outline' as const }
  }
})
</script>

<template>
  <Badge :variant="meta.variant" class="text-[11px]">
    {{ meta.label }}
  </Badge>
</template>
