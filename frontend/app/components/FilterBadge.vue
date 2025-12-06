<template>
  <div
    class="inline-flex items-center h-6 rounded-md bg-background-surface/80 border border-border-subtle text-xs font-mono whitespace-nowrap overflow-hidden"
  >
    <!-- Field segment -->
    <div class="px-2.5 py-1 text-text-muted border-r border-[hsl(0,0%,15%)]">
      {{ filter.field }}
    </div>

    <!-- Operator segment -->
    <div class="px-2 py-1 text-text-muted text-[10px] border-r border-[hsl(0,0%,15%)]">
      {{ formattedOperator }}
    </div>

    <!-- Values segment -->
    <div class="px-2.5 py-1 flex items-center gap-1 border-r border-[hsl(0,0%,15%)]">
      <template v-if="filter.field === 'state'">
        <!-- State values with colored badges -->
        <Badge
          v-for="(value, index) in filter.values"
          :key="index"
          :variant="getStatusVariant(value)"
          class="text-xs px-1 py-0 h-4 normal-case"
        >
          {{ formatStatus(value) }}
        </Badge>
      </template>
      <template v-else-if="filter.field === 'id'">
        <!-- UUID values - truncated -->
        <span
          v-for="(value, index) in filter.values"
          :key="index"
          class="font-mono text-[10px] text-text-primary bg-background-raised px-1 py-0.5 rounded"
          :title="value"
        >
          {{ truncateUUID(value) }}
        </span>
      </template>
      <template v-else>
        <!-- Regular text values -->
        <span
          v-for="(value, index) in filter.values"
          :key="index"
          class="text-text-primary"
        >
          {{ value }}<span v-if="index < filter.values.length - 1" class="text-text-muted">,</span>
        </span>
      </template>
    </div>

    <!-- Remove button segment -->
    <IconButton
      :icon="X"
      size="xs"
      variant="ghost"
      @click.stop="$emit('remove')"
      class="hover:bg-status-error/10 hover:text-status-error"
    />
  </div>
</template>

<script setup lang="ts">
import { Badge } from '@/components/ui/badge'
import { IconButton } from '~/components/common'
import { X } from 'lucide-vue-next'
import { computed } from 'vue'
import type { ParsedFilter } from '~/composables/useFilterParser'

const props = defineProps<{
  filter: ParsedFilter
}>()

defineEmits<{
  remove: []
}>()

const { getStatusVariant, formatStatus } = useTaskStatus()
const { formatOperator } = useFilterParser()

const formattedOperator = computed(() => formatOperator(props.filter.operator))

function truncateUUID(uuid: string): string {
  if (uuid.length <= 8) return uuid
  return `${uuid.substring(0, 8)}...`
}
</script>
