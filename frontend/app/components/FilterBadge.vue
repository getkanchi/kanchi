<template>
  <Badge
    variant="secondary"
    class="text-xs px-2 py-1 h-6 bg-background-primary/80 border-gray-600 flex items-center gap-1 whitespace-nowrap"
  >
    <span class="text-gray-400">{{ filter.key }}:</span>
    <Badge
      v-if="filter.key === 'state'"
      :variant="getStateVariant(filter.value)"
      class="text-xs px-1 py-0 h-4 normal-case"
    >
      {{ formatStateValue(filter.value) }}
    </Badge>
    <span v-else class="text-white">
      {{ filter.value }}
    </span>
    <button
      @click.stop="$emit('remove')"
      class="ml-1 hover:text-red-400 transition-colors"
    >
      <X class="h-3 w-3" />
    </button>
  </Badge>
</template>

<script setup lang="ts">
import { Badge } from '@/components/ui/badge'
import type { BadgeVariants } from '@/components/ui/badge'
import { X } from 'lucide-vue-next'

interface Filter {
  key: string
  value: string
}

defineProps<{
  filter: Filter
}>()

defineEmits<{
  remove: []
}>()

const getStateVariant = (state: string): BadgeVariants['variant'] => {
  const variants: Record<string, BadgeVariants['variant']> = {
    'SUCCESS': 'success',
    'RUNNING': 'running', 
    'PENDING': 'pending',
    'RECEIVED': 'received',
    'FAILED': 'failed',
    'RETRY': 'retry',
    'REVOKED': 'revoked'
  }
  return variants[state] || 'outline'
}

const formatStateValue = (state: string): string => {
  return state.charAt(0).toUpperCase() + state.slice(1).toLowerCase()
}
</script>