<script setup lang="ts">
import { computed } from 'vue'
import { CheckCircle2, RefreshCw, X } from 'lucide-vue-next'
import { Button } from '~/components/ui/button'
import BulkActionCombobox from '~/components/common/BulkActionCombobox.vue'
import type { BulkTaskAction } from '~/components/common/BulkActionCombobox.vue'

const props = withDefaults(defineProps<{
  selectedCount: number
  maxSelectionSize: number
  action: BulkTaskAction
  isLoading?: boolean
}>(), {
  isLoading: false,
})

const emit = defineEmits<{
  'update:action': [action: BulkTaskAction]
  execute: []
  clear: []
}>()

const isOverLimit = computed(() => props.selectedCount > props.maxSelectionSize)
const executeLabel = computed(() => {
  if (props.action === 'rerun') return 'Review'
  return 'Apply'
})
</script>

<template>
  <div
    class="sticky top-0 z-20 flex flex-wrap items-center justify-between gap-3 border-b border-border-subtle bg-background-raised/95 px-4 py-3 backdrop-blur"
  >
    <div class="flex min-w-0 items-center gap-3">
      <div class="flex h-8 w-8 items-center justify-center rounded-md border border-primary-border bg-primary-bg text-primary">
        <CheckCircle2 class="h-4 w-4" />
      </div>
      <div class="min-w-0">
        <p class="text-sm font-medium text-text-primary">
          {{ selectedCount }} selected
        </p>
        <p class="text-xs text-text-muted">
          Limit {{ maxSelectionSize }} per action
        </p>
      </div>
    </div>

    <div class="flex flex-wrap items-center gap-2">
      <p v-if="isOverLimit" class="text-xs text-status-error">
        Remove {{ selectedCount - maxSelectionSize }} task{{ selectedCount - maxSelectionSize === 1 ? '' : 's' }}.
      </p>
      <BulkActionCombobox
        :model-value="action"
        :disabled="isLoading"
        @update:model-value="emit('update:action', $event)"
      />
      <Button
        variant="outline"
        size="sm"
        class="gap-1.5"
        :disabled="selectedCount === 0 || isOverLimit || isLoading"
        @click="emit('execute')"
      >
        <RefreshCw v-if="isLoading" class="h-3.5 w-3.5 animate-spin" />
        {{ executeLabel }}
      </Button>
      <Button variant="ghost" size="icon" :disabled="isLoading" @click="emit('clear')">
        <X class="h-4 w-4" />
      </Button>
    </div>
  </div>
</template>
