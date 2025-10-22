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
        <Button variant="ghost" @click="cancel">Cancel</Button>
        <Button variant="outline" @click="showTestDialog = true">
          <FlaskConical class="h-4 w-4 mr-2" />
          Test
        </Button>
        <Button @click="saveWorkflow" :disabled="!canSave || saving">
          <Save class="h-4 w-4 mr-2" />
          {{ saving ? 'Saving...' : 'Save Changes' }}
        </Button>
      </div>
    </div>

    <!-- Main Form (same as new.vue) -->
    <div class="space-y-6">
      <!-- Basic Info -->
      <Card>
        <CardHeader class="pb-4">
          <CardTitle class="text-sm text-text-primary">Basic Information</CardTitle>
          <CardDescription>Edit the workflow name and high-level description.</CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
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
        </CardContent>
      </Card>

      <Dialog :open="showTestDialog" @update:open="(open) => { showTestDialog = open; testError = null }">
        <DialogContent class="max-w-xl">
          <DialogHeader>
            <DialogTitle>Test Workflow</DialogTitle>
            <DialogDescription>Provide a sample event payload to evaluate workflow conditions.</DialogDescription>
          </DialogHeader>
          <div class="space-y-4">
            <div>
              <label class="text-xs font-medium text-text-secondary mb-1.5 block">
                Test Context (JSON)
              </label>
              <Textarea
                v-model="testContext"
                rows="8"
                class="font-mono text-xs"
              />
            </div>
            <div v-if="testError" class="text-sm text-status-error bg-status-error-bg border border-status-error-border rounded px-3 py-2">
              {{ testError }}
            </div>
            <div v-if="testResult" class="rounded border border-border bg-background-base p-3 space-y-2">
              <div class="flex items-center gap-2 text-sm">
                <span class="text-text-secondary">Conditions met:</span>
                <Badge :variant="testResult.conditions_met ? 'default' : 'destructive'">
                  {{ testResult.conditions_met ? 'Yes' : 'No' }}
                </Badge>
              </div>
              <div class="text-xs text-text-muted">
                Actions: {{ testResult.actions.join(', ') || 'None' }}
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" @click="showTestDialog = false">Close</Button>
            <Button @click="runTest" :disabled="testing">
              {{ testing ? 'Testing...' : 'Run Test' }}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <!-- Workflow Builder -->
      <Card>
        <CardHeader class="pb-4 flex flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle class="text-sm text-text-primary">Workflow Builder</CardTitle>
            <CardDescription>Adjust trigger, filters, and actions in sequence.</CardDescription>
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
          <CardDescription>Fine-tune execution priority, limits, and status.</CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
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
              Max executions per hour
            </label>
            <Input
              v-model.number="workflow.max_executions_per_hour"
              type="number"
              min="0"
              class="w-full"
              placeholder="Unlimited"
            />
          </div>
          <div class="flex items-center justify-between rounded-lg border border-border px-4 py-3">
            <div>
              <label class="text-sm font-medium text-text-primary">Enabled</label>
              <p class="text-xs text-text-muted">Toggle workflow availability.</p>
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

  <!-- Loading State -->
  <div v-else-if="workflowStore.isLoading" class="max-w-5xl mx-auto">
    <div class="h-96 bg-background-surface border border-border rounded-lg animate-pulse" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ChevronLeft, Save, FlaskConical } from 'lucide-vue-next'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Badge } from '~/components/ui/badge'
import { Switch } from '~/components/ui/switch'
import { Textarea } from '~/components/ui/textarea'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '~/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from '~/components/ui/dialog'
import WorkflowTriggerSelector from '~/components/workflows/WorkflowTriggerSelector.vue'
import WorkflowConditionBuilder from '~/components/workflows/WorkflowConditionBuilder.vue'
import WorkflowActionsList from '~/components/workflows/WorkflowActionsList.vue'
import type { WorkflowUpdateRequest } from '~/types/workflow'

const route = useRoute()
const workflowStore = useWorkflowsStore()
const saving = ref(false)
const showTestDialog = ref(false)
const testing = ref(false)
const testContext = ref('{\n  "task_id": "example-task",\n  "task_name": "process_payment",\n  "event_type": "task.failed",\n  "retry_count": 0,\n  "queue": "default"\n}')
const testResult = ref<any | null>(null)
const testError = ref<string | null>(null)

// Local workflow state (editable)
const workflow = ref<WorkflowUpdateRequest | null>(null)

const canSave = computed(() => {
  return workflow.value &&
         workflow.value.name &&
         workflow.value.name.trim().length > 0 &&
         workflow.value.trigger &&
         workflow.value.trigger.type.length > 0 &&
         workflow.value.actions &&
         workflow.value.actions.length > 0
})

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

async function runTest() {
  try {
    testResult.value = null
    const context = testContext.value ? JSON.parse(testContext.value) : {}
    testing.value = true
    testError.value = null
    testResult.value = await workflowStore.testWorkflow(route.params.id as string, context)
  } catch (err) {
    if (err instanceof SyntaxError) {
      testError.value = 'Context must be valid JSON.'
    } else if (err instanceof Error) {
      testError.value = err.message
    } else {
      testError.value = 'Unable to run workflow test.'
    }
  } finally {
    testing.value = false
  }
}

// Lifecycle
onMounted(async () => {
  try {
    await workflowStore.fetchWorkflowMetadata()
  } catch (err) {
    console.error('Failed to load workflow metadata:', err)
  }
  const loaded = await workflowStore.fetchWorkflow(route.params.id as string)
  if (loaded) {
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
