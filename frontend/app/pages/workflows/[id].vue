<template>
  <div v-if="workflowStore.currentWorkflow" class="max-w-6xl mx-auto">
    <!-- Header -->
    <div class="mb-6">
      <Button
        variant="ghost"
        size="sm"
        @click="navigateTo('/workflows')"
        class="mb-3 -ml-2"
      >
        <ChevronLeft class="h-4 w-4 mr-1" />
        Back to Workflows
      </Button>

      <div class="flex items-start justify-between gap-4">
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-3 mb-2">
            <h1 class="text-2xl font-bold text-text-primary">
              {{ workflowStore.currentWorkflow.name }}
            </h1>
            <StatusDot
              :status="workflowStore.currentWorkflow.enabled ? 'online' : 'offline'"
              :pulse="workflowStore.currentWorkflow.enabled"
            />
          </div>
          <p v-if="workflowStore.currentWorkflow.description" class="text-sm text-text-secondary">
            {{ workflowStore.currentWorkflow.description }}
          </p>
        </div>

        <div class="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            @click="toggleEnabled"
            :disabled="toggling"
          >
            <Power class="h-4 w-4 mr-2" />
            {{ workflowStore.currentWorkflow.enabled ? 'Disable' : 'Enable' }}
          </Button>
          <Button
            variant="outline"
            size="sm"
            @click="navigateTo(`/workflows/${route.params.id}/edit`)"
          >
            <Pencil class="h-4 w-4 mr-2" />
            Edit
          </Button>
        </div>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-4 gap-4 mb-6">
      <div class="bg-background-surface border border-border rounded-lg p-4">
        <div class="text-2xl font-bold text-text-primary">
          {{ workflowStore.currentWorkflow.execution_count }}
        </div>
        <div class="text-sm text-text-muted">Total Executions</div>
      </div>
      <div class="bg-background-surface border border-border rounded-lg p-4">
        <div class="text-2xl font-bold text-status-success">
          {{ workflowStore.currentWorkflow.success_count }}
        </div>
        <div class="text-sm text-text-muted">Successful</div>
      </div>
      <div class="bg-background-surface border border-border rounded-lg p-4">
        <div class="text-2xl font-bold text-status-error">
          {{ workflowStore.currentWorkflow.failure_count }}
        </div>
        <div class="text-sm text-text-muted">Failed</div>
      </div>
      <div class="bg-background-surface border border-border rounded-lg p-4">
        <div class="text-2xl font-bold text-text-primary">
          {{ successRate }}%
        </div>
        <div class="text-sm text-text-muted">Success Rate</div>
      </div>
    </div>

    <!-- Tabs -->
    <Tabs default-value="overview" class="w-full">
      <TabsList class="grid w-full grid-cols-3 mb-6">
        <TabsTrigger value="overview">Overview</TabsTrigger>
        <TabsTrigger value="executions">Executions</TabsTrigger>
        <TabsTrigger value="settings">Settings</TabsTrigger>
      </TabsList>

      <!-- Overview Tab -->
      <TabsContent value="overview">
        <div class="space-y-6">
          <!-- Workflow Configuration -->
          <div class="bg-background-surface border border-border rounded-lg p-5">
            <h2 class="text-sm font-semibold text-text-primary mb-4">Workflow Configuration</h2>

            <!-- Trigger -->
            <div class="mb-4">
              <div class="text-xs font-medium text-text-muted mb-2">TRIGGER</div>
              <div class="flex items-center gap-2">
                <Badge variant="outline">
                  {{ workflowStore.currentWorkflow.trigger.type }}
                </Badge>
              </div>
            </div>

            <!-- Conditions -->
            <div v-if="workflowStore.currentWorkflow.conditions" class="mb-4">
              <div class="text-xs font-medium text-text-muted mb-2">CONDITIONS</div>
              <div class="space-y-1">
                <div
                  v-for="(condition, idx) in workflowStore.currentWorkflow.conditions.conditions"
                  :key="idx"
                  class="text-xs font-mono bg-background-base px-2 py-1 rounded"
                >
                  {{ condition.field }} {{ condition.operator }} {{ condition.value }}
                </div>
              </div>
            </div>

            <!-- Actions -->
            <div>
              <div class="text-xs font-medium text-text-muted mb-2">ACTIONS</div>
              <div class="space-y-2">
                <div
                  v-for="(action, idx) in workflowStore.currentWorkflow.actions"
                  :key="idx"
                  class="flex items-center gap-2 text-sm"
                >
                  <span class="text-text-muted">{{ idx + 1 }}.</span>
                  <Badge variant="outline">{{ action.type }}</Badge>
                </div>
              </div>
            </div>
          </div>

          <!-- Last Execution -->
          <div v-if="workflowStore.currentWorkflow.last_executed_at" class="bg-background-surface border border-border rounded-lg p-5">
            <h2 class="text-sm font-semibold text-text-primary mb-2">Last Execution</h2>
            <p class="text-sm text-text-secondary">
              {{ formatDateTime(workflowStore.currentWorkflow.last_executed_at) }}
            </p>
          </div>
        </div>
      </TabsContent>

      <!-- Executions Tab -->
      <TabsContent value="executions">
        <WorkflowExecutionHistory :workflow-id="route.params.id as string" />
      </TabsContent>

      <!-- Settings Tab -->
      <TabsContent value="settings">
        <div class="bg-background-surface border border-border rounded-lg p-5">
          <h2 class="text-sm font-semibold text-text-primary mb-4">Advanced Settings</h2>
          <div class="space-y-4 text-sm">
            <div class="flex justify-between">
              <span class="text-text-secondary">Priority</span>
              <span class="text-text-primary font-medium">
                {{ workflowStore.currentWorkflow.priority }}
              </span>
            </div>
            <div class="flex justify-between">
              <span class="text-text-secondary">Cooldown</span>
              <span class="text-text-primary font-medium">
                {{ workflowStore.currentWorkflow.cooldown_seconds }}s
              </span>
            </div>
            <div class="flex justify-between">
              <span class="text-text-secondary">Max Executions/Hour</span>
              <span class="text-text-primary font-medium">
                {{ workflowStore.currentWorkflow.max_executions_per_hour || 'Unlimited' }}
              </span>
            </div>
            <div class="flex justify-between">
              <span class="text-text-secondary">Created</span>
              <span class="text-text-primary font-medium">
                {{ formatDateTime(workflowStore.currentWorkflow.created_at!) }}
              </span>
            </div>
            <div v-if="workflowStore.currentWorkflow.updated_at !== workflowStore.currentWorkflow.created_at" class="flex justify-between">
              <span class="text-text-secondary">Last Updated</span>
              <span class="text-text-primary font-medium">
                {{ formatDateTime(workflowStore.currentWorkflow.updated_at!) }}
              </span>
            </div>
          </div>
        </div>
      </TabsContent>
    </Tabs>
  </div>

  <!-- Loading State -->
  <div v-else-if="workflowStore.isLoading" class="max-w-6xl mx-auto">
    <div class="h-48 bg-background-surface border border-border rounded-lg animate-pulse" />
  </div>

  <!-- Error State -->
  <div v-else class="max-w-6xl mx-auto text-center py-16">
    <AlertCircle class="h-12 w-12 text-status-error mx-auto mb-4" />
    <h3 class="text-lg font-medium text-text-primary mb-2">Workflow not found</h3>
    <Button @click="navigateTo('/workflows')">
      Back to Workflows
    </Button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ChevronLeft, Power, Pencil, AlertCircle } from 'lucide-vue-next'
import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs'
import StatusDot from '~/components/StatusDot.vue'
import WorkflowExecutionHistory from '~/components/workflows/WorkflowExecutionHistory.vue'

const route = useRoute()
const workflowStore = useWorkflowsStore()
const toggling = ref(false)

const successRate = computed(() => {
  const workflow = workflowStore.currentWorkflow
  if (!workflow || workflow.execution_count === 0) return 0
  return Math.round((workflow.success_count / workflow.execution_count) * 100)
})

async function toggleEnabled() {
  if (!workflowStore.currentWorkflow?.id) return

  toggling.value = true
  try {
    await workflowStore.toggleWorkflow(workflowStore.currentWorkflow.id)
  } finally {
    toggling.value = false
  }
}

function formatDateTime(timestamp: string): string {
  return new Date(timestamp).toLocaleString()
}

onMounted(async () => {
  await workflowStore.fetchWorkflow(route.params.id as string)
})
</script>
