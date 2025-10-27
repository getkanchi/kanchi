<template>
  <div v-if="workflowStore.currentWorkflow" class="max-w-7xl mx-auto">
    <!-- Header -->
    <div class="mb-10">
      <NuxtLink to="/workflows">
        <Button
          variant="ghost"
          size="sm"
          class="mb-4 -ml-2"
        >
          <ChevronLeft class="h-4 w-4 mr-1" />
          Back to Workflows
        </Button>
      </NuxtLink>

      <div class="flex items-start justify-between gap-4">
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-3 mb-1">
            <h1 class="text-xl font-semibold text-text-primary">
              {{ workflowStore.currentWorkflow.name }}
            </h1>
            <StatusDot
              :status="workflowStore.currentWorkflow.enabled ? 'online' : 'offline'"
              :pulse="workflowStore.currentWorkflow.enabled"
            />
          </div>
          <p v-if="workflowStore.currentWorkflow.description" class="text-xs text-text-muted">
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
            <Power class="h-3.5 w-3.5 mr-1.5" />
            {{ workflowStore.currentWorkflow.enabled ? 'Disable' : 'Enable' }}
          </Button>
          <NuxtLink :to="`/workflows/${route.params.id}/edit`">
            <Button
              variant="outline"
              size="sm"
            >
              <Pencil class="h-3.5 w-3.5 mr-1.5" />
              Edit
            </Button>
          </NuxtLink>
        </div>
      </div>
    </div>

    <!-- Main Layout: Content + Stats Rail -->
    <div class="flex flex-col lg:flex-row gap-6">

      <!-- Main Content Area -->
      <main class="flex-1 min-w-0">
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
          <div class="border border-border rounded-md p-5">
            <h2 class="text-sm font-medium text-text-primary mb-4">Workflow Configuration</h2>

            <!-- Trigger -->
            <div class="mb-4">
              <div class="text-[10px] uppercase tracking-wider font-medium text-text-muted mb-2">Trigger</div>
              <div class="flex items-center gap-2">
                <Badge variant="outline" class="font-mono text-xs">
                  {{ workflowStore.currentWorkflow.trigger.type }}
                </Badge>
              </div>
            </div>

            <!-- Conditions -->
            <div v-if="workflowStore.currentWorkflow.conditions" class="mb-4">
              <div class="text-[10px] uppercase tracking-wider font-medium text-text-muted mb-2">Conditions</div>
              <div class="space-y-1.5">
                <div
                  v-for="(condition, idx) in workflowStore.currentWorkflow.conditions.conditions"
                  :key="idx"
                  class="text-xs font-mono border border-border px-2 py-1.5 rounded"
                >
                  {{ condition.field }} {{ condition.operator }} {{ condition.value }}
                </div>
              </div>
            </div>

            <!-- Actions -->
            <div>
              <div class="text-[10px] uppercase tracking-wider font-medium text-text-muted mb-2">Actions</div>
              <div class="space-y-2">
                <div
                  v-for="(action, idx) in workflowStore.currentWorkflow.actions"
                  :key="idx"
                  class="flex items-center gap-2 text-sm"
                >
                  <span class="text-text-muted text-xs">{{ idx + 1 }}.</span>
                  <Badge variant="outline" class="text-xs">{{ action.type }}</Badge>
                </div>
              </div>
            </div>
          </div>

          <!-- Last Execution -->
          <div v-if="workflowStore.currentWorkflow.last_executed_at" class="border border-border rounded-md p-5">
            <h2 class="text-sm font-medium text-text-primary mb-2">Last Execution</h2>
            <p class="text-xs text-text-muted">
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
        <div class="border border-border rounded-md p-5">
          <h2 class="text-sm font-medium text-text-primary mb-4">Advanced Settings</h2>
          <div class="space-y-3 text-xs">
            <div class="flex justify-between py-2 border-b border-border">
              <span class="text-text-muted">Priority</span>
              <span class="text-text-primary font-medium tabular-nums">
                {{ workflowStore.currentWorkflow.priority }}
              </span>
            </div>
            <div class="flex justify-between py-2 border-b border-border">
              <span class="text-text-muted">Cooldown</span>
              <span class="text-text-primary font-medium tabular-nums">
                {{ workflowStore.currentWorkflow.cooldown_seconds }}s
              </span>
            </div>
            <div class="flex justify-between py-2 border-b border-border">
              <span class="text-text-muted">Max Executions/Hour</span>
              <span class="text-text-primary font-medium tabular-nums">
                {{ workflowStore.currentWorkflow.max_executions_per_hour || 'Unlimited' }}
              </span>
            </div>
            <div v-if="workflowStore.currentWorkflow.circuit_breaker?.enabled" class="py-2 border-b border-border">
              <div class="flex items-center gap-2 mb-1.5">
                <ShieldCheck class="h-3.5 w-3.5 text-status-info" />
                <span class="text-text-muted">Circuit Breaker</span>
              </div>
              <div class="ml-5 space-y-1">
                <div class="text-text-primary text-xs">
                  Max {{ workflowStore.currentWorkflow.circuit_breaker.max_executions }}
                  execution{{ workflowStore.currentWorkflow.circuit_breaker.max_executions > 1 ? 's' : '' }}
                  per {{ workflowStore.currentWorkflow.circuit_breaker.window_seconds }}s
                </div>
                <div v-if="workflowStore.currentWorkflow.circuit_breaker.context_field" class="text-text-muted text-xs">
                  Group by: <code class="px-1 py-0.5 rounded bg-background-base text-primary font-mono text-[10px]">{{ workflowStore.currentWorkflow.circuit_breaker.context_field }}</code>
                </div>
                <div v-else class="text-text-muted text-xs">
                  Auto grouping (root_id)
                </div>
              </div>
            </div>
            <div class="flex justify-between py-2 border-b border-border">
              <span class="text-text-muted">Created</span>
              <span class="text-text-primary font-medium">
                {{ formatDateTime(workflowStore.currentWorkflow.created_at!) }}
              </span>
            </div>
            <div v-if="workflowStore.currentWorkflow.updated_at !== workflowStore.currentWorkflow.created_at" class="flex justify-between py-2">
              <span class="text-text-muted">Last Updated</span>
              <span class="text-text-primary font-medium">
                {{ formatDateTime(workflowStore.currentWorkflow.updated_at!) }}
              </span>
            </div>
          </div>
        </div>
      </TabsContent>
    </Tabs>
      </main>

      <!-- Stats Rail (Right Sidebar) -->
      <aside class="w-full lg:w-64 lg:sticky lg:top-6 lg:self-start">
        <div class="space-y-3">
          <div class="border border-border rounded-md px-4 py-3.5 hover:border-border-highlight transition-colors">
            <p class="text-[10px] uppercase tracking-wider text-text-muted mb-1.5 font-medium">Total Executions</p>
            <p class="text-2xl font-semibold text-text-primary tabular-nums">
              {{ workflowStore.currentWorkflow.execution_count }}
            </p>
          </div>
          <div class="border border-border rounded-md px-4 py-3.5 hover:border-border-highlight transition-colors">
            <p class="text-[10px] uppercase tracking-wider text-text-muted mb-1.5 font-medium">Successful</p>
            <p class="text-2xl font-semibold text-status-success tabular-nums">
              {{ workflowStore.currentWorkflow.success_count }}
            </p>
          </div>
          <div class="border border-border rounded-md px-4 py-3.5 hover:border-border-highlight transition-colors">
            <p class="text-[10px] uppercase tracking-wider text-text-muted mb-1.5 font-medium">Failed</p>
            <p class="text-2xl font-semibold text-status-error tabular-nums">
              {{ workflowStore.currentWorkflow.failure_count }}
            </p>
          </div>
          <div class="border border-border rounded-md px-4 py-3.5 hover:border-border-highlight transition-colors">
            <p class="text-[10px] uppercase tracking-wider text-text-muted mb-1.5 font-medium">Success Rate</p>
            <p class="text-2xl font-semibold text-text-primary tabular-nums">
              {{ successRate }}%
            </p>
          </div>
        </div>
      </aside>

    </div>
  </div>

  <!-- Loading State -->
  <div v-else-if="workflowStore.isLoading" class="max-w-7xl mx-auto">
    <div class="h-48 border border-border rounded-md animate-pulse" />
  </div>

  <!-- Error State -->
  <div v-else-if="!workflowStore.isLoading" class="max-w-7xl mx-auto text-center py-24">
    <AlertCircle class="h-10 w-10 text-status-error mx-auto mb-3 opacity-40" />
    <h3 class="text-sm font-medium text-text-primary mb-1">Workflow not found</h3>
    <p class="text-xs text-text-muted mb-6">This workflow may have been deleted or you don't have access to it.</p>
    <NuxtLink to="/workflows">
      <Button size="sm">
        Back to Workflows
      </Button>
    </NuxtLink>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ChevronLeft, Power, Pencil, AlertCircle, ShieldCheck } from 'lucide-vue-next'
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
