<template>
  <Sheet :open="open" @update:open="onOpenChange">
    <SheetContent
      side="right"
      class="w-[640px] max-w-[95vw] border-l border-border-subtle bg-background-base p-0"
    >
      <div class="flex h-full flex-col">
        <SheetHeader class="border-b border-border-subtle px-6 py-5 bg-background-surface">
          <div class="flex items-start justify-between gap-3">
            <div class="space-y-1">
              <SheetTitle>Slack Webhooks</SheetTitle>
              <SheetDescription>
                Manage reusable Slack webhook destinations for your workflows.
              </SheetDescription>
            </div>
            <SheetClose as-child>
              <Button variant="ghost" size="icon">
                <X class="h-4 w-4" />
                <span class="sr-only">Close</span>
              </Button>
            </SheetClose>
          </div>
        </SheetHeader>

        <div class="flex-1 overflow-y-auto px-6 py-6">
          <WorkflowSlackConfigPanel
            :active="open"
            :enable-selection="enableSelection"
            @select="handleSelect"
            @request-close="emit('close')"
          />
        </div>
      </div>
    </SheetContent>
  </Sheet>
</template>

<script setup lang="ts">
import { Sheet, SheetClose, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '~/components/ui/sheet'
import { Button } from '~/components/ui/button'
import { X } from 'lucide-vue-next'
import WorkflowSlackConfigPanel from '~/components/workflows/WorkflowSlackConfigPanel.vue'

const props = withDefaults(defineProps<{
  open: boolean
  enableSelection?: boolean
}>(), {
  enableSelection: true
})

const emit = defineEmits<{
  close: []
  select: [configId: string]
}>()

function onOpenChange(value: boolean) {
  if (!value) {
    emit('close')
  }
}

function handleSelect(configId: string) {
  emit('select', configId)
}
</script>
