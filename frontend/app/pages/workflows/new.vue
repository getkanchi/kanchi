<template>
  <div class="max-w-5xl mx-auto">
    <!-- Header -->
    <div class="mb-6 flex items-center justify-between">
      <div>
        <Button
          variant="ghost"
          size="sm"
          @click="navigateTo('/workflows')"
          class="mb-3 -ml-2"
        >
          <ChevronLeft class="h-4 w-4 mr-1" />
          Back to Workflows
        </Button>
        <h1 class="text-2xl font-bold text-text-primary">New Workflow</h1>
      </div>
      <div class="flex items-center gap-2">
        <Button variant="outline" @click="testWorkflow" :disabled="!canSave">
          <FlaskConical class="h-4 w-4 mr-2" />
          Test
        </Button>
        <Button @click="saveWorkflow" :disabled="!canSave || saving">
          <Save class="h-4 w-4 mr-2" />
          {{ saving ? 'Saving...' : 'Save' }}
        </Button>
      </div>
    </div>

    <!-- Main Form -->
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
              :value="workflow.name"
              @input="workflow.name = ($event.target as HTMLInputElement).value"
              placeholder="e.g., Alert on Critical Failures"
              class="w-full"
            />
          </div>
          <div>
            <label class="text-xs font-medium text-text-secondary mb-1.5 block">
              Description
            </label>
            <Input
              :value="workflow.description"
              @input="workflow.description = ($event.target as HTMLInputElement).value"
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

        <!-- Step 1: Trigger -->
        <div class="space-y-6">
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
                :value="workflow.priority"
                @input="workflow.priority = Number(($event.target as HTMLInputElement).value)"
                type="number"
                min="0"
                max="999"
                class="w-full"
              />
              <p class="text-xs text-text-muted mt-1">Higher priority workflows execute first</p>
            </div>
            <div>
              <label class="text-xs font-medium text-text-secondary mb-1.5 block">
                Cooldown (seconds)
              </label>
              <Input
                :value="workflow.cooldown_seconds"
                @input="workflow.cooldown_seconds = Number(($event.target as HTMLInputElement).value)"
                type="number"
                min="0"
                class="w-full"
              />
              <p class="text-xs text-text-muted mt-1">Minimum time between executions</p>
            </div>
          </div>
          <div>
            <label class="text-xs font-medium text-text-secondary mb-1.5 block">
              Max Executions per Hour
            </label>
            <Input
              :value="workflow.max_executions_per_hour"
              @input="workflow.max_executions_per_hour = ($event.target as HTMLInputElement).value ? Number(($event.target as HTMLInputElement).value) : undefined"
              type="number"
              min="0"
              class="w-full"
              placeholder="Unlimited"
            />
            <p class="text-xs text-text-muted mt-1">Leave empty for no limit</p>
          </div>
          <div class="flex items-center justify-between">
            <div>
              <label class="text-sm font-medium text-text-primary">Enabled</label>
              <p class="text-xs text-text-muted">Workflow will start executing immediately</p>
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
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ChevronLeft, Save, FlaskConical } from 'lucide-vue-next'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Badge } from '~/components/ui/badge'
import { Switch } from '~/components/ui/switch'
import WorkflowTriggerSelector from '~/components/workflows/WorkflowTriggerSelector.vue'
import WorkflowConditionBuilder from '~/components/workflows/WorkflowConditionBuilder.vue'
import WorkflowActionsList from '~/components/workflows/WorkflowActionsList.vue'
import type { WorkflowCreateRequest } from '~/types/workflow'

const workflowStore = useWorkflowsStore()
const saving = ref(false)

// Form State
const workflow = ref<WorkflowCreateRequest>({
  name: '',
  description: '',
  enabled: true,
  trigger: {
    type: '',
    config: {}
  },
  conditions: undefined,
  actions: [],
  priority: 100,
  max_executions_per_hour: undefined,
  cooldown_seconds: 0
})

// Computed
const canSave = computed(() => {
  return workflow.value.name.trim().length > 0 &&
         workflow.value.trigger?.type.length > 0 &&
         workflow.value.actions.length > 0
})

// Actions
async function saveWorkflow() {
  if (!canSave.value) return

  saving.value = true
  try {
    const created = await workflowStore.createWorkflow(workflow.value)
    navigateTo(`/workflows/${created.id}`)
  } catch (err) {
    console.error('Failed to save workflow:', err)
  } finally {
    saving.value = false
  }
}

function testWorkflow() {
  // TODO: Implement test workflow dialog
  console.log('Test workflow:', workflow.value)
}
</script>
