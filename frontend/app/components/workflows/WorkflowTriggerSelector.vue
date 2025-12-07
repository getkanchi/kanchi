<template>
  <div>
    <div
      v-if="!trigger?.type"
      class="border-2 border-dashed border-border-subtle rounded-lg p-6 text-center hover:border-border-highlight transition-colors cursor-pointer"
      @click="showSelector = true"
    >
      <Target class="h-8 w-8 text-text-muted mx-auto mb-2" />
      <p class="text-sm text-text-secondary mb-1">Select a trigger event</p>
      <p class="text-xs text-text-muted">Choose what will start this workflow</p>
    </div>

    <div v-else class="border border-border-subtle rounded-lg p-4 bg-background-raised">
      <div class="flex items-start justify-between gap-3">
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-1">
            <Target class="h-4 w-4 text-primary flex-shrink-0" />
            <span class="text-sm font-medium text-text-primary">
              {{ getTriggerLabel(trigger.type) }}
            </span>
            <Badge :variant="getTriggerCategory(trigger.type) === 'task' ? 'default' : 'secondary'" size="sm">
              {{ getTriggerCategory(trigger.type) }}
            </Badge>
          </div>
          <p class="text-xs text-text-muted">
            {{ getTriggerDescription(trigger.type) }}
          </p>
        </div>
        <Button variant="ghost" size="sm" @click="showSelector = true">
          <Pencil class="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>

    <!-- Trigger Selector Dialog -->
    <Dialog :open="showSelector" @update:open="showSelector = $event">
      <DialogContent class="max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>Select Trigger Event</DialogTitle>
          <DialogDescription>
            Choose the event that will start this workflow
          </DialogDescription>
        </DialogHeader>

        <div class="flex-1 overflow-y-auto">
          <!-- Search -->
          <div class="mb-4">
            <Input
              v-model="searchQuery"
              placeholder="Search triggers..."
              class="w-full"
            />
          </div>

          <!-- Trigger Groups -->
          <div class="space-y-6">
            <div v-for="category in filteredCategories" :key="category.name">
              <h3 class="text-xs font-semibold text-text-muted uppercase tracking-wide mb-3">
                {{ category.name }}
              </h3>
              <div class="space-y-2">
                <button
                  v-for="triggerOpt in category.triggers"
                  :key="triggerOpt.type"
                  class="w-full text-left p-3 rounded-lg border border-border-subtle hover:border-primary hover:bg-background-hover transition-colors"
                  :class="trigger?.type === triggerOpt.type ? 'border-primary bg-background-selected' : ''"
                  @click="selectTrigger(triggerOpt.type)"
                >
                  <div class="flex items-start justify-between gap-3">
                    <div class="flex-1 min-w-0">
                      <div class="text-sm font-medium text-text-primary mb-0.5">
                        {{ triggerOpt.label }}
                      </div>
                      <div class="text-xs text-text-muted line-clamp-2">
                        {{ triggerOpt.description }}
                      </div>
                    </div>
                    <Check v-if="trigger?.type === triggerOpt.type" class="h-4 w-4 text-primary flex-shrink-0 mt-0.5" />
                  </div>
                </button>
              </div>
            </div>
          </div>
        </div>

        <DialogFooter class="border-t border-border-subtle pt-4 mt-4">
          <Button variant="outline" @click="showSelector = false">Cancel</Button>
          <Button @click="confirmSelection" :disabled="!trigger?.type">Select</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Target, Pencil, Check } from 'lucide-vue-next'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Badge } from '~/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from '~/components/ui/dialog'
import type { TriggerConfig } from '~/types/workflow'
import { useWorkflowsStore } from '~/stores/workflows'

const props = defineProps<{
  trigger?: TriggerConfig
}>()

const emit = defineEmits<{
  'update:trigger': [trigger: TriggerConfig]
}>()

const showSelector = ref(false)
const searchQuery = ref('')
const workflowStore = useWorkflowsStore()

const triggers = computed(() => workflowStore.triggerCatalog)

const filteredCategories = computed(() => {
  const query = searchQuery.value.toLowerCase()
  const filtered = query
    ? triggers.value.filter(t =>
        t.label.toLowerCase().includes(query) ||
        t.description.toLowerCase().includes(query) ||
        t.type.toLowerCase().includes(query)
      )
    : triggers.value

  // Group by category
  const taskTriggers = filtered.filter(t => t.category === 'task')
  const workerTriggers = filtered.filter(t => t.category === 'worker')

  return [
    { name: 'Task Events', triggers: taskTriggers },
    { name: 'Worker Events', triggers: workerTriggers }
  ].filter(cat => cat.triggers.length > 0)
})

function selectTrigger(type: string) {
  emit('update:trigger', { type, config: {} })
  showSelector.value = false
}

function confirmSelection() {
  showSelector.value = false
}

function getTriggerLabel(type: string): string {
  return triggers.value.find(t => t.type === type)?.label || type
}

function getTriggerDescription(type: string): string {
  return triggers.value.find(t => t.type === type)?.description || ''
}

function getTriggerCategory(type: string): string {
  return triggers.value.find(t => t.type === type)?.category || 'task'
}

onMounted(async () => {
  if (!workflowStore.triggerCatalog.length) {
    try {
      await workflowStore.fetchWorkflowMetadata()
    } catch (e) {
      console.error('Failed to load workflow metadata:', e)
    }
  }
})
</script>
