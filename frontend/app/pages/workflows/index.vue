<template>
    <!-- Header -->
    <div class="mb-10 flex items-center justify-between">
      <div>
        <h1 class="text-xl font-semibold text-text-primary mb-1 flex items-center gap-2">
          Workflows
        </h1>
        <p class="text-text-muted text-xs">
          Automate your Celery monitoring with smart rules
        </p>
      </div>
      <NuxtLink to="/workflows/new">
        <Button size="sm" variant="outline">
          <Plus class="h-4 w-4 mr-1.5" />
          New Workflow
        </Button>
      </NuxtLink>
    </div>

    <!-- Main Layout: Workflows + Stats Rail -->
    <div class="flex flex-col lg:flex-row gap-6">

      <!-- Main Content Area -->
      <main class="flex-1 min-w-0">

        <!-- Filters -->
        <div class="flex flex-col gap-3 mb-6 sm:flex-row sm:items-center">
          <div class="flex-1">
            <Input
              v-model="searchQuery"
              type="text"
              placeholder="Search workflows..."
              class="w-full"
            />
          </div>
          <Select v-model="filterEnabled" class="w-full sm:w-44">
            <option value="all">All Workflows</option>
            <option value="enabled">Enabled Only</option>
            <option value="disabled">Disabled Only</option>
          </Select>
        </div>

        <!-- Loading State -->
        <div v-if="workflowStore.isLoading" class="space-y-2">
          <div v-for="i in 3" :key="i" class="h-16 border border-border rounded-md animate-pulse" />
        </div>

        <!-- Empty State -->
        <div
          v-else-if="filteredWorkflows.length === 0"
          class="text-center py-24"
        >
          <Zap class="h-10 w-10 text-text-muted mx-auto mb-3 opacity-40" />
          <h3 class="text-sm font-medium text-text-primary mb-1">No workflows yet</h3>
          <p class="text-xs text-text-muted mb-6">Create your first workflow to automate task monitoring</p>
          <NuxtLink to="/workflows/new">
            <Button size="sm">
              <Plus class="h-4 w-4 mr-1.5" />
              Create Workflow
            </Button>
          </NuxtLink>
        </div>

        <!-- Workflows List -->
        <div v-else class="border border-border rounded-md divide-y divide-border">
      <div
        v-for="workflow in filteredWorkflows"
        :key="workflow.id"
        class="flex items-start justify-between gap-4 px-4 py-4 transition-colors hover:bg-background-hover-subtle group"
      >
        <NuxtLink
          :to="`/workflows/${workflow.id}`"
          class="flex items-center gap-3 flex-1 min-w-0 cursor-pointer"
        >
          <div class="mt-0.5">
            <StatusDot
              :status="workflow.enabled ? 'online' : 'offline'"
              :pulse="workflow.enabled"
            />
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-0.5">
              <h3 class="text-sm font-medium text-text-primary truncate">
                {{ workflow.name }}
              </h3>
            </div>
            <p v-if="workflow.description" class="text-xs text-text-muted mb-2 line-clamp-1">
              {{ workflow.description }}
            </p>
            <div class="flex items-center gap-1.5 text-[11px] text-text-secondary flex-wrap">
              <span class="text-text-muted">When</span>
              <Badge variant="outline" size="sm" class="font-mono text-[10px] px-1.5 py-0">
                {{ formatTrigger(workflow.trigger.type) }}
              </Badge>
              <span v-if="workflow.conditions" class="text-text-muted">and</span>
              <Badge v-if="workflow.conditions" variant="outline" size="sm" class="text-[10px] px-1.5 py-0">
                {{ workflow.conditions.conditions.length }} condition{{  workflow.conditions.conditions.length !== 1 ? 's' : '' }}
              </Badge>
              <span class="text-text-muted">→</span>
              <Badge
                v-for="(action, idx) in workflow.actions.slice(0, 2)"
                :key="idx"
                variant="outline"
                size="sm"
                class="text-[10px] px-1.5 py-0"
              >
                {{ formatActionType(action.type) }}
              </Badge>
              <span v-if="workflow.actions.length > 2" class="text-text-muted">
                +{{ workflow.actions.length - 2 }} more
              </span>
            </div>
            <div class="flex items-center gap-3 mt-1.5 text-[11px] text-text-muted">
              <span v-if="workflow.execution_count > 0" class="tabular-nums">
                {{ workflow.execution_count }} execution{{ workflow.execution_count !== 1 ? 's' : '' }}
              </span>
              <span v-if="workflow.execution_count > 0 && workflow.success_count" class="tabular-nums">
                {{ Math.round((workflow.success_count / workflow.execution_count) * 100) }}% success
              </span>
              <span v-if="workflow.last_executed_at">
                Last: {{ formatRelativeTime(workflow.last_executed_at) }}
              </span>
              <span v-else class="text-text-disabled">Never executed</span>
            </div>
          </div>
        </NuxtLink>
        <div class="flex items-center gap-1 opacity-60 group-hover:opacity-100 transition-opacity">
          <Button
            variant="ghost"
            size="sm"
            @click="toggleWorkflow(workflow)"
            :disabled="toggling.has(workflow.id!)"
          >
            <Power
              :class="[
                'h-3.5 w-3.5',
                workflow.enabled ? 'text-status-success' : 'text-text-muted'
              ]"
            />
          </Button>
          <NuxtLink :to="`/workflows/${workflow.id}/edit`">
            <Button
              variant="ghost"
              size="sm"
            >
              <Pencil class="h-3.5 w-3.5" />
            </Button>
          </NuxtLink>
          <Button
            variant="ghost"
            size="sm"
            @click="confirmDelete(workflow)"
            :disabled="deleting.has(workflow.id!)"
          >
            <Trash2 class="h-3.5 w-3.5 text-status-error" />
          </Button>
        </div>
      </div>
        </div>
      </main>

      <!-- Stats Rail (Right Sidebar) -->
      <aside class="w-full lg:w-64 lg:sticky lg:top-6 lg:self-start">
        <div v-if="!workflowStore.isLoading" class="space-y-3">
          <div class="border border-border rounded-md px-4 py-3.5 hover:border-border-highlight transition-colors">
            <p class="text-[10px] uppercase tracking-wider text-text-muted mb-1.5 font-medium">Active</p>
            <p class="text-2xl font-semibold text-text-primary tabular-nums">{{ workflowStore.activeWorkflowsCount }}</p>
          </div>
          <div class="border border-border rounded-md px-4 py-3.5 hover:border-border-highlight transition-colors">
            <p class="text-[10px] uppercase tracking-wider text-text-muted mb-1.5 font-medium">Total Workflows</p>
            <p class="text-2xl font-semibold text-text-primary tabular-nums">{{ workflowStore.workflows.length }}</p>
          </div>
          <div class="border border-border rounded-md px-4 py-3.5 hover:border-border-highlight transition-colors">
            <p class="text-[10px] uppercase tracking-wider text-text-muted mb-1.5 font-medium">Executions Today</p>
            <p class="text-2xl font-semibold text-text-primary tabular-nums">{{ totalExecutionsToday }}</p>
          </div>
          <div class="border border-border rounded-md px-4 py-3.5 hover:border-border-highlight transition-colors">
            <p class="text-[10px] uppercase tracking-wider text-text-muted mb-1.5 font-medium">Success Rate</p>
            <p class="text-2xl font-semibold text-status-success tabular-nums">{{ averageSuccessRate }}%</p>
          </div>
        </div>
      </aside>

    </div>

    <!-- Delete Confirmation Dialog -->
    <AlertDialog :open="!!workflowToDelete" @update:open="(open) => !open">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Workflow</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to delete "{{ workflowToDelete?.name }}"? This action cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            class="bg-status-error hover:bg-status-error-hover"
            @click="deleteWorkflow(workflowToDelete!)"
          >
            Delete
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>

</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Zap, Plus, Power, Pencil, Trash2 } from 'lucide-vue-next'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Badge } from '~/components/ui/badge'
import Select from '~/components/common/Select.vue'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle
} from '~/components/ui/alert-dialog'
import StatusDot from '~/components/StatusDot.vue'
import type { WorkflowDefinition } from '~/types/workflow'

const workflowStore = useWorkflowsStore()

const searchQuery = ref('')
const filterEnabled = ref('all')
const toggling = ref(new Set<string>())
const deleting = ref(new Set<string>())
const workflowToDelete = ref<WorkflowDefinition | null>(null)

const filteredWorkflows = computed(() => {
  let result = workflowStore.workflows

  if (filterEnabled.value === 'enabled') {
    result = result.filter(w => w.enabled)
  } else if (filterEnabled.value === 'disabled') {
    result = result.filter(w => !w.enabled)
  }

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(w =>
      w.name.toLowerCase().includes(query) ||
      w.description?.toLowerCase().includes(query) ||
      w.trigger.type.toLowerCase().includes(query)
    )
  }

  return result
})

const totalExecutionsToday = computed(() => {
  // This would come from execution stats in a real implementation
  return workflowStore.workflows.reduce((sum, w) => sum + w.execution_count, 0)
})

const averageSuccessRate = computed(() => {
  const workflows = workflowStore.workflows.filter(w => w.execution_count > 0)
  if (workflows.length === 0) return 0

  const totalRate = workflows.reduce((sum, w) => {
    return sum + (w.success_count / w.execution_count)
  }, 0)

  return Math.round((totalRate / workflows.length) * 100)
})

async function toggleWorkflow(workflow: WorkflowDefinition) {
  if (!workflow.id) return

  toggling.value.add(workflow.id)
  try {
    await workflowStore.toggleWorkflow(workflow.id)
  } catch (err) {
    console.error('Failed to toggle workflow:', err)
  } finally {
    toggling.value.delete(workflow.id)
  }
}

function confirmDelete(workflow: WorkflowDefinition) {
  workflowToDelete.value = workflow
}

async function deleteWorkflow(workflow: WorkflowDefinition) {
  if (!workflow.id) return

  deleting.value.add(workflow.id)
  try {
    await workflowStore.deleteWorkflow(workflow.id)
    workflowToDelete.value = null
  } catch (err) {
    console.error('Failed to delete workflow:', err)
  } finally {
    deleting.value.delete(workflow.id)
  }
}

// Formatters
function formatTrigger(trigger: string): string {
  return trigger.replace(/\./g, '.')
}

function formatActionType(type: string): string {
  const map: Record<string, string> = {
    'slack.notify': 'Slack',
    'task.retry': 'Retry',
    'email.send': 'Email',
    'webhook.call': 'Webhook'
  }
  return map[type] || type
}

function formatRelativeTime(timestamp: string): string {
  const now = new Date()
  const then = new Date(timestamp)
  const diff = now.getTime() - then.getTime()

  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (days > 0) return `${days}d ago`
  if (hours > 0) return `${hours}h ago`
  if (minutes > 0) return `${minutes}m ago`
  return 'just now'
}

// Lifecycle
onMounted(async () => {
  await workflowStore.fetchWorkflows()
})
</script>
