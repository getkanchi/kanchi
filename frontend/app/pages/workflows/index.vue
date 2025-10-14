<template>
  <div>
    <!-- Header -->
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-text-primary mb-2 flex items-center gap-2">
          <Zap class="h-6 w-6 text-primary" />
          Workflows
        </h1>
        <p class="text-text-secondary text-sm">
          Automate your Celery monitoring with smart rules
        </p>
      </div>
      <Button @click="navigateTo('/workflows/new')">
        <Plus class="h-4 w-4 mr-2" />
        New Workflow
      </Button>
    </div>

    <!-- Stats Cards -->
    <div v-if="!workflowStore.isLoading" class="grid grid-cols-4 gap-4 mb-6">
      <div class="bg-background-surface border border-border rounded-lg p-4">
        <div class="text-2xl font-bold text-text-primary">
          {{ workflowStore.activeWorkflowsCount }}
        </div>
        <div class="text-sm text-text-muted">Active</div>
      </div>
      <div class="bg-background-surface border border-border rounded-lg p-4">
        <div class="text-2xl font-bold text-text-primary">
          {{ workflowStore.workflows.length }}
        </div>
        <div class="text-sm text-text-muted">Total</div>
      </div>
      <div class="bg-background-surface border border-border rounded-lg p-4">
        <div class="text-2xl font-bold text-text-primary">
          {{ totalExecutionsToday }}
        </div>
        <div class="text-sm text-text-muted">Today</div>
      </div>
      <div class="bg-background-surface border border-border rounded-lg p-4">
        <div class="text-2xl font-bold text-status-success">
          {{ averageSuccessRate }}%
        </div>
        <div class="text-sm text-text-muted">Success Rate</div>
      </div>
    </div>

    <!-- Filters -->
    <div class="mb-4 flex items-center gap-3">
      <div class="flex-1">
        <Input
          v-model="searchQuery"
          type="text"
          placeholder="Search workflows..."
          class="w-full"
        />
      </div>
      <Select v-model="filterEnabled" class="w-40">
        <option value="all">All Workflows</option>
        <option value="enabled">Enabled Only</option>
        <option value="disabled">Disabled Only</option>
      </Select>
    </div>

    <!-- Loading State -->
    <div v-if="workflowStore.isLoading" class="space-y-3">
      <div v-for="i in 3" :key="i" class="h-24 bg-background-surface border border-border rounded-lg animate-pulse" />
    </div>

    <!-- Empty State -->
    <div
      v-else-if="filteredWorkflows.length === 0"
      class="text-center py-16 bg-background-surface border border-border rounded-lg"
    >
      <Zap class="h-12 w-12 text-text-muted mx-auto mb-4 opacity-50" />
      <h3 class="text-lg font-medium text-text-primary mb-2">No workflows yet</h3>
      <p class="text-sm text-text-muted mb-6">Create your first workflow to automate task monitoring</p>
      <Button @click="navigateTo('/workflows/new')">
        <Plus class="h-4 w-4 mr-2" />
        Create Workflow
      </Button>
    </div>

    <!-- Workflows List -->
    <div v-else class="space-y-3">
      <div
        v-for="workflow in filteredWorkflows"
        :key="workflow.id"
        class="bg-background-surface border border-border rounded-lg p-4 hover:border-border-highlight transition-colors cursor-pointer group"
        @click="navigateTo(`/workflows/${workflow.id}`)"
      >
        <div class="flex items-start justify-between gap-4">
          <!-- Left: Status + Info -->
          <div class="flex items-start gap-3 flex-1 min-w-0">
            <!-- Status Indicator -->
            <div class="mt-1">
              <StatusDot
                :status="workflow.enabled ? 'online' : 'offline'"
                :pulse="workflow.enabled"
              />
            </div>

            <!-- Workflow Info -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <h3 class="text-sm font-semibold text-text-primary truncate">
                  {{ workflow.name }}
                </h3>
              </div>

              <!-- Description -->
              <p v-if="workflow.description" class="text-xs text-text-muted mb-2 line-clamp-1">
                {{ workflow.description }}
              </p>

              <!-- Workflow Formula -->
              <div class="flex items-center gap-2 text-xs text-text-secondary flex-wrap">
                <span class="text-text-muted">When</span>
                <Badge variant="outline" size="sm" class="font-mono">
                  {{ formatTrigger(workflow.trigger.type) }}
                </Badge>
                <span v-if="workflow.conditions" class="text-text-muted">and</span>
                <Badge v-if="workflow.conditions" variant="outline" size="sm">
                  {{ workflow.conditions.conditions.length }} condition{{  workflow.conditions.conditions.length !== 1 ? 's' : '' }}
                </Badge>
                <span class="text-text-muted">→</span>
                <Badge
                  v-for="(action, idx) in workflow.actions.slice(0, 2)"
                  :key="idx"
                  variant="outline"
                  size="sm"
                >
                  {{ formatActionType(action.type) }}
                </Badge>
                <span v-if="workflow.actions.length > 2" class="text-text-muted">
                  +{{ workflow.actions.length - 2 }} more
                </span>
              </div>

              <!-- Stats -->
              <div class="flex items-center gap-4 mt-2 text-xs text-text-muted">
                <span v-if="workflow.execution_count > 0">
                  ✓ {{ workflow.execution_count }} execution{{ workflow.execution_count !== 1 ? 's' : '' }}
                </span>
                <span v-if="workflow.execution_count > 0 && workflow.success_count">
                  {{ Math.round((workflow.success_count / workflow.execution_count) * 100) }}% success
                </span>
                <span v-if="workflow.last_executed_at">
                  Last: {{ formatRelativeTime(workflow.last_executed_at) }}
                </span>
                <span v-else class="text-text-disabled">Never executed</span>
              </div>
            </div>
          </div>

          <!-- Right: Actions -->
          <div class="flex items-center gap-2">
            <!-- Toggle -->
            <Button
              variant="ghost"
              size="sm"
              @click.stop="toggleWorkflow(workflow)"
              :disabled="toggling.has(workflow.id!)"
            >
              <Power
                :class="[
                  'h-4 w-4',
                  workflow.enabled ? 'text-status-success' : 'text-text-muted'
                ]"
              />
            </Button>

            <!-- Edit -->
            <Button
              variant="ghost"
              size="sm"
              @click.stop="navigateTo(`/workflows/${workflow.id}/edit`)"
            >
              <Pencil class="h-4 w-4" />
            </Button>

            <!-- Delete -->
            <Button
              variant="ghost"
              size="sm"
              @click.stop="confirmDelete(workflow)"
              :disabled="deleting.has(workflow.id!)"
            >
              <Trash2 class="h-4 w-4 text-status-error" />
            </Button>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Dialog -->
    <AlertDialog :open="!!workflowToDelete" @update:open="(open) => !open && (workflowToDelete = null)">
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
  </div>
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

// State
const searchQuery = ref('')
const filterEnabled = ref('all')
const toggling = ref(new Set<string>())
const deleting = ref(new Set<string>())
const workflowToDelete = ref<WorkflowDefinition | null>(null)

// Computed
const filteredWorkflows = computed(() => {
  let result = workflowStore.workflows

  // Filter by enabled status
  if (filterEnabled.value === 'enabled') {
    result = result.filter(w => w.enabled)
  } else if (filterEnabled.value === 'disabled') {
    result = result.filter(w => !w.enabled)
  }

  // Filter by search query
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

// Actions
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
