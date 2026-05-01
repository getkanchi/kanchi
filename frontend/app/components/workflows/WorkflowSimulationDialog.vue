<template>
  <Dialog :open="open" @update:open="$emit('close')">
    <DialogContent class="max-w-3xl max-h-[85vh] overflow-hidden flex flex-col">
      <DialogHeader>
        <DialogTitle>Simulate Workflow</DialogTitle>
        <DialogDescription>Dry-run this workflow against a sample event without firing real actions.</DialogDescription>
      </DialogHeader>

      <div class="space-y-4 overflow-y-auto pr-1">
        <div>
          <label class="text-xs font-medium text-text-secondary mb-1.5 block">Sample event context (JSON)</label>
          <Textarea v-model="localContext" rows="10" class="font-mono text-xs w-full" />
        </div>

        <div v-if="simulationError" class="text-sm text-status-error bg-status-error-bg border border-status-error-border rounded px-3 py-2">
          {{ simulationError }}
        </div>

        <div v-if="result" class="space-y-4">
          <div class="rounded-lg border border-border-subtle p-4 bg-background-raised">
            <div class="flex flex-wrap items-center gap-2 mb-3">
              <Badge :variant="result.conditions_met ? 'default' : 'secondary'">
                {{ result.conditions_met ? 'Conditions match' : 'Conditions do not match' }}
              </Badge>
              <Badge :variant="result.would_execute ? 'default' : 'secondary'">
                {{ result.would_execute ? 'Would execute' : 'Would not execute' }}
              </Badge>
            </div>
            <div v-if="result.warnings.length" class="space-y-2">
              <div v-for="warning in result.warnings" :key="warning" class="text-xs rounded border border-amber-300/40 bg-amber-500/10 px-3 py-2 text-amber-200">
                {{ warning }}
              </div>
            </div>
          </div>

          <div class="rounded-lg border border-border-subtle p-4 space-y-3">
            <h3 class="text-sm font-medium text-text-primary">Action preview</h3>
            <div v-for="(action, index) in result.action_previews" :key="`${action.action_type}-${index}`" class="rounded border border-border-subtle bg-background-base p-3 space-y-2">
              <div class="flex items-center gap-2">
                <Badge :variant="action.status === 'would_execute' ? 'default' : 'destructive'">{{ action.status === 'would_execute' ? 'Would run' : 'Blocked' }}</Badge>
                <span class="text-sm text-text-primary font-medium">{{ action.action_type }}</span>
              </div>
              <p class="text-sm text-text-secondary">{{ action.summary }}</p>
              <div v-if="Object.keys(action.details || {}).length" class="text-xs text-text-muted font-mono whitespace-pre-wrap break-all">{{ formatDetails(action.details) }}</div>
              <div v-for="warning in action.warnings || []" :key="warning" class="text-xs rounded border border-amber-300/40 bg-amber-500/10 px-3 py-2 text-amber-200">
                {{ warning }}
              </div>
            </div>
          </div>

          <div v-if="result.simulation_history.length" class="rounded-lg border border-border-subtle p-4 space-y-3">
            <h3 class="text-sm font-medium text-text-primary">Recent simulations</h3>
            <div v-for="(entry, index) in result.simulation_history.slice(0, 5)" :key="`${entry.simulated_at}-${index}`" class="text-xs text-text-muted border-b border-border-subtle last:border-b-0 pb-2 last:pb-0">
              <div class="flex items-center gap-2 mb-1">
                <Badge variant="outline">{{ entry.would_execute ? 'Would execute' : 'No execution' }}</Badge>
                <span>{{ formatTime(entry.simulated_at) }}</span>
              </div>
              <div>{{ entry.warnings[0] || 'No major warnings.' }}</div>
            </div>
          </div>
        </div>
      </div>

      <DialogFooter>
        <Button variant="ghost" @click="$emit('close')">Close</Button>
        <Button @click="runSimulation" :disabled="running">
          {{ running ? 'Simulating...' : 'Run Simulation' }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { Button } from '~/components/ui/button'
import { Textarea } from '~/components/ui/textarea'
import { Badge } from '~/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from '~/components/ui/dialog'
import type { WorkflowCreateRequest, WorkflowSimulationResponse } from '~/types/workflow'

const props = defineProps<{
  open: boolean
  workflow: WorkflowCreateRequest
  defaultContext: string
}>()

const emit = defineEmits<{ close: [] }>()

const workflowStore = useWorkflowsStore()
const localContext = ref(props.defaultContext)
const running = ref(false)
const simulationError = ref<string | null>(null)
const result = ref<WorkflowSimulationResponse | null>(null)

watch(() => props.defaultContext, (value) => {
  localContext.value = value
})

watch(() => props.open, (open) => {
  if (open) {
    simulationError.value = null
  }
})

async function runSimulation() {
  try {
    simulationError.value = null
    result.value = null
    running.value = true
    const context = localContext.value ? JSON.parse(localContext.value) : {}
    result.value = await workflowStore.simulateWorkflow(props.workflow, context)
  } catch (err) {
    if (err instanceof SyntaxError) {
      simulationError.value = 'Context must be valid JSON.'
    } else if (err instanceof Error) {
      simulationError.value = err.message
    } else {
      simulationError.value = 'Unable to run workflow simulation.'
    }
  } finally {
    running.value = false
  }
}

function formatDetails(details: Record<string, any>) {
  return JSON.stringify(details, null, 2)
}

function formatTime(value: string) {
  return new Date(value).toLocaleString()
}
</script>
