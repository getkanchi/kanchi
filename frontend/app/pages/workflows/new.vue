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
        <Button variant="outline" disabled title="Save the workflow to run a test">
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
      <Card>
        <CardHeader class="pb-4">
          <CardTitle class="text-sm text-text-primary">Basic Information</CardTitle>
          <CardDescription>Give the workflow a clear title and optional description.</CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
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
        </CardContent>
      </Card>

      <!-- Workflow Builder -->
      <Card>
        <CardHeader class="pb-4 flex flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle class="text-sm text-text-primary">Workflow Builder</CardTitle>
            <CardDescription>Define trigger, optional filters, and follow-up actions.</CardDescription>
          </div>
          <Badge variant="outline" size="sm" class="font-mono">
            {{ workflow.trigger?.type || 'no trigger' }} → {{ workflow.actions.length }} actions
          </Badge>
        </CardHeader>
        <CardContent class="space-y-6">
          <!-- Step 1: Trigger -->
          <div>
            <div class="flex items-center gap-2 mb-3">
              <span class="flex items-center justify-center w-7 h-7 rounded-full bg-primary/10 text-xs font-semibold text-primary">
                1
              </span>
              <span class="text-sm font-medium text-text-primary uppercase tracking-wide">When</span>
            </div>
            <div class="ml-9">
              <WorkflowTriggerSelector
                :trigger="workflow.trigger"
                @update:trigger="workflow.trigger = $event"
              />
            </div>
          </div>

          <!-- Step 2: Conditions -->
          <div>
            <div class="flex items-center gap-2 mb-3">
              <span class="flex items-center justify-center w-7 h-7 rounded-full bg-primary/10 text-xs font-semibold text-primary">
                2
              </span>
              <span class="text-sm font-medium text-text-primary uppercase tracking-wide">If (optional)</span>
            </div>
            <div class="ml-9">
              <WorkflowConditionBuilder
                :conditions="workflow.conditions"
                @update:conditions="workflow.conditions = $event"
              />
            </div>
          </div>

          <!-- Step 3: Actions -->
          <div>
            <div class="flex items-center gap-2 mb-3">
              <span class="flex items-center justify-center w-7 h-7 rounded-full bg-primary/10 text-xs font-semibold text-primary">
                3
              </span>
              <span class="text-sm font-medium text-text-primary uppercase tracking-wide">Then</span>
            </div>
            <div class="ml-9">
              <WorkflowActionsList
                :actions="workflow.actions"
                @update:actions="workflow.actions = $event"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- Advanced Settings -->
      <Card>
        <CardHeader class="pb-4">
          <CardTitle class="text-sm text-text-primary">Advanced Controls</CardTitle>
          <CardDescription>Tune execution priority, throttling, and status.</CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
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
              <p class="text-xs text-text-muted mt-1">Higher values run before others.</p>
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
              <p class="text-xs text-text-muted mt-1">Minimum gap between executions.</p>
            </div>
          </div>
          <div>
            <label class="text-xs font-medium text-text-secondary mb-1.5 block">
              Max executions per hour
            </label>
            <Input
              :value="workflow.max_executions_per_hour"
              @input="workflow.max_executions_per_hour = ($event.target as HTMLInputElement).value ? Number(($event.target as HTMLInputElement).value) : undefined"
              type="number"
              min="0"
              class="w-full"
              placeholder="Unlimited"
            />
            <p class="text-xs text-text-muted mt-1">Leave blank for no hourly cap.</p>
          </div>
          <div class="flex items-center justify-between rounded-lg border border-border px-4 py-3">
            <div>
              <label class="text-sm font-medium text-text-primary">Enabled</label>
              <p class="text-xs text-text-muted">Toggle workflow activation.</p>
            </div>
            <Switch
              :checked="workflow.enabled"
              @update:checked="workflow.enabled = $event"
            />
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Error Display -->
    <div v-if="workflowStore.error" class="mt-4 p-4 bg-status-error-bg border border-status-error-border rounded-lg">
      <p class="text-sm text-status-error">{{ workflowStore.error }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ChevronLeft, Save, FlaskConical } from 'lucide-vue-next'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Badge } from '~/components/ui/badge'
import { Switch } from '~/components/ui/switch'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '~/components/ui/card'
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

const canSave = computed(() => {
  return workflow.value.name.trim().length > 0 &&
         workflow.value.trigger?.type.length > 0 &&
         workflow.value.actions.length > 0
})

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

onMounted(async () => {
  try {
    await workflowStore.fetchWorkflowMetadata()
  } catch (err) {
    console.error('Failed to load workflow metadata:', err)
  }
})
</script>
