<template>
  <Dialog :open="open" @update:open="$emit('close')">
    <DialogContent class="max-w-lg">
      <DialogHeader>
        <DialogTitle>Configure Task Retry</DialogTitle>
        <DialogDescription>
          Automatically retry the failed task
        </DialogDescription>
      </DialogHeader>

      <div class="space-y-4 py-4">
        <!-- Delay -->
        <div>
          <label class="text-xs font-medium text-text-secondary mb-1.5 block">
            Delay (seconds)
          </label>
          <Input
            :value="localAction.params.delay_seconds"
            @input="localAction.params.delay_seconds = Number(($event.target as HTMLInputElement).value)"
            type="number"
            min="0"
            placeholder="0"
            class="w-full"
          />
          <p class="text-xs text-text-muted mt-1">
            Wait time before retrying (0 for immediate)
          </p>
        </div>

        <!-- Continue on Failure -->
        <div class="flex items-center justify-between border border-border-subtle rounded-lg p-3">
          <div>
            <label class="text-xs font-medium text-text-primary">Continue on Failure</label>
            <p class="text-xs text-text-muted">Continue to next action if retry fails</p>
          </div>
          <Switch
            :checked="localAction.continue_on_failure"
            @update:checked="localAction.continue_on_failure = $event"
          />
        </div>
      </div>

      <DialogFooter>
        <Button variant="outline" @click="$emit('close')">Cancel</Button>
        <Button @click="save">Save</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Switch } from '~/components/ui/switch'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from '~/components/ui/dialog'
import type { ActionConfig } from '~/types/workflow'

const props = defineProps<{
  action: ActionConfig
  open: boolean
}>()

const emit = defineEmits<{
  'update:action': [action: ActionConfig]
  'close': []
}>()

const localAction = ref<ActionConfig>({ ...props.action })

watch(() => props.action, (newAction) => {
  localAction.value = { ...newAction }
}, { deep: true })

function save() {
  emit('update:action', localAction.value)
}
</script>
