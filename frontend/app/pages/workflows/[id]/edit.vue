<template>
  <div v-if="workflow" class="max-w-5xl mx-auto">
    <!-- Header -->
    <div class="mb-6 flex items-center justify-between">
      <div>
        <Button
          variant="ghost"
          size="sm"
          @click="navigateTo(`/workflows/${route.params.id}`)"
          class="mb-3 -ml-2"
        >
          <ChevronLeft class="h-4 w-4 mr-1" />
          Back to Workflow
        </Button>
        <h1 class="text-2xl font-bold text-text-primary">Edit Workflow</h1>
      </div>
      <div class="flex items-center gap-2">
        <Button variant="outline" @click="cancel">Cancel</Button>
        <Button @click="saveWorkflow" :disabled="!canSave || saving">
          <Save class="h-4 w-4 mr-2" />
          {{ saving ? 'Saving...' : 'Save Changes' }}
        </Button>
      </div>
    </div>

    <!-- Main Form (same as new.vue) -->
    <div class="space-y-6">
      <!-- Basic Info -->
      <div class="bg-background-surface border border-border rounded-lg p-5">
        <h2 class="text-sm font-semibold text-text-primary mb-4">Basic Information</h2>
        <div class="space-y-4">
          <div>
            <label class="text-xs font-medium text-text-secondary mb-1.5 block">
              Name *
            </label>
            <Input
              v-model="workflow.name"
              placeholder="e.g., Alert on Critical Failures"
              class="w-full"
            />
          </div>
          <div>
            <label class="text-xs font-medium text-text-secondary mb-1.5 block">
              Description
            </label>
            <Input
              v-model="workflow.description"
              placeholder="What does this workflow do?"
              class="w-full"
            />
          </div>
        </div>
      </div>

      <!-- Workflow Builder -->
      <div class="bg-background-surface border border-border rounded-lg p-5">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-sm font-semibold text-text-primary">Workflow Flow</h2>
          <Badge variant="outline" size="sm" class="font-mono">
            {{ workflow.trigger?.type || 'no trigger' }} → {{ workflow.actions.length }} actions
          </Badge>
        </div>

        <div class="space-y-6">
          <!-- Step 1: Trigger -->
          <div>
            <div class="flex items-center gap-2 mb-3">
              <div class="flex items-center justify-center w-6 h-6 rounded-full bg-primary text-xs font-bold text-white">
                1
              </div>
              <span class="text-sm font-medium text-text-primary">WHEN</span>
            </div>
            <div class="ml-8">
              <WorkflowTriggerSelector
                :trigger="workflow.trigger"
                @update:trigger="workflow.trigger = $event"
              />
            </div>
          </div>

          <!-- Step 2: Conditions -->
          <div>
            <div class="flex items-center gap-2 mb-3">
              <div class="flex items-center justify-center w-6 h-6 rounded-full bg-primary text-xs font-bold text-white">
                2
              </div>
              <span class="text-sm font-medium text-text-primary">IF (Optional)</span>
            </div>
            <div class="ml-8">
              <WorkflowConditionBuilder
                :conditions="workflow.conditions"
                @update:conditions="workflow.conditions = $event"
              />
            </div>
          </div>

          <!-- Step 3: Actions -->
          <div>
            <div class="flex items-center gap-2 mb-3">
              <div class="flex items-center justify-center w-6 h-6 rounded-full bg-primary text-xs font-bold text-white">
                3
              </div>
              <span class="text-sm font-medium text-text-primary">THEN</span>
            </div>
            <div class="ml-8">
              <WorkflowActionsList
                :actions="workflow.actions"
                @update:actions="workflow.actions = $event"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Advanced Settings -->
      <details class="bg-background-surface border border-border rounded-lg">
        <summary class="p-5 cursor-pointer text-sm font-semibold text-text-primary hover:bg-background-hover-subtle transition-colors">
          Advanced Settings
        </summary>
        <div class="px-5 pb-5 space-y-4 border-t border-border pt-5">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="text-xs font-medium text-text-secondary mb-1.5 block">
                Priority
              </label>
              <Input
                v-model.number="workflow.priority"
                type="number"
                min="0"
                max="999"
                class="w-full"
              />
            </div>
            <div>
              <label class="text-xs font-medium text-text-secondary mb-1.5 block">
                Cooldown (seconds)
              </label>
              <Input
                v-model.number="workflow.cooldown_seconds"
                type="number"
                min="0"
                class="w-full"
              />
            </div>
          </div>
          <div>
            <label class="text-xs font-medium text-text-secondary mb-1.5 block">
              Max Executions per Hour
            </label>
            <Input
              v-model.number="workflow.max_executions_per_hour"
              type="number"
              min="0"
              class="w-full"
              placeholder="Unlimited"
            />
          </div>
          <div class="flex items-center justify-between">
            <div>
              <label class="text-sm font-medium text-text-primary">Enabled</label>
              <p class="text-xs text-text-muted">Workflow will execute when triggered</p>
            </div>
            <Switch
              :checked="workflow.enabled"
              @update:checked="workflow.enabled = $event"
            />
          </div>
        </div>
      </details>
    </div>

    <!-- Error Display -->
    <div v-if="workflowStore.error" class="mt-4 p-4 bg-status-error-bg border border-status-error-border rounded-lg">
      <p class="text-sm text-status-error">{{ workflowStore.error }}</p>
    </div>
  </div>

  <!-- Loading State -->
  <div v-else-if="workflowStore.isLoading" class="max-w-5xl mx-auto">
    <div class="h-96 bg-background-surface border border-border rounded-lg animate-pulse" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ChevronLeft, Save } from 'lucide-vue-next'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Badge } from '~/components/ui/badge'
import { Switch } from '~/components/ui/switch'
import WorkflowTriggerSelector from '~/components/workflows/WorkflowTriggerSelector.vue'
import WorkflowConditionBuilder from '~/components/workflows/WorkflowConditionBuilder.vue'
import WorkflowActionsList from '~/components/workflows/WorkflowActionsList.vue'
import type { WorkflowUpdateRequest } from '~/types/workflow'

const route = useRoute()
const workflowStore = useWorkflowsStore()
const saving = ref(false)

// Local workflow state (editable)
const workflow = ref<WorkflowUpdateRequest | null>(null)

// Computed
const canSave = computed(() => {
  return workflow.value &&
         workflow.value.name &&
         workflow.value.name.trim().length > 0 &&
         workflow.value.trigger &&
         workflow.value.trigger.type.length > 0 &&
         workflow.value.actions &&
         workflow.value.actions.length > 0
})

// Actions
async function saveWorkflow() {
  if (!canSave.value || !workflow.value) return

  saving.value = true
  try {
    await workflowStore.updateWorkflow(route.params.id as string, workflow.value)
    navigateTo(`/workflows/${route.params.id}`)
  } catch (err) {
    console.error('Failed to save workflow:', err)
  } finally {
    saving.value = false
  }
}

function cancel() {
  navigateTo(`/workflows/${route.params.id}`)
}

// Lifecycle
onMounted(async () => {
  const loaded = await workflowStore.fetchWorkflow(route.params.id as string)
  if (loaded) {
    // Create editable copy
    workflow.value = {
      name: loaded.name,
      description: loaded.description,
      enabled: loaded.enabled,
      trigger: loaded.trigger,
      conditions: loaded.conditions,
      actions: loaded.actions,
      priority: loaded.priority,
      max_executions_per_hour: loaded.max_executions_per_hour,
      cooldown_seconds: loaded.cooldown_seconds
    }
  }
})
</script>
