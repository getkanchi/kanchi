<template>
  <div>
    <div v-if="actions.length === 0" class="border-2 border-dashed border-border rounded-lg p-6 text-center">
      <Zap class="h-8 w-8 text-text-muted mx-auto mb-2" />
      <p class="text-sm text-text-secondary mb-3">No actions configured</p>
      <Button size="sm" variant="outline" @click="showActionSelector = true">
        <Plus class="h-3.5 w-3.5 mr-1.5" />
        Add Action
      </Button>
    </div>

    <div v-else class="space-y-3">
      <!-- Actions List -->
      <div
        v-for="(action, index) in actions"
        :key="index"
        class="border border-border rounded-lg p-4 bg-background-raised"
      >
        <div class="flex items-start justify-between gap-3 mb-3">
          <div class="flex items-start gap-3 flex-1 min-w-0">
            <div class="text-sm font-mono text-text-muted">
              {{ index + 1 }}.
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <component :is="getActionIcon(action.type)" class="h-4 w-4 text-primary flex-shrink-0" />
                <span class="text-sm font-medium text-text-primary">
                  {{ getActionLabel(action.type) }}
                </span>
              </div>
              <p class="text-xs text-text-muted">
                {{ getActionDescription(action.type) }}
              </p>
            </div>
          </div>
          <div class="flex items-center gap-1">
            <Button variant="ghost" size="sm" class="h-7 w-7 p-0" @click="editAction(index)">
              <Settings class="h-3.5 w-3.5" />
            </Button>
            <Button variant="ghost" size="sm" class="h-7 w-7 p-0" @click="removeAction(index)">
              <X class="h-3.5 w-3.5 text-status-error" />
            </Button>
          </div>
        </div>

        <!-- Action Configuration Summary -->
        <div v-if="action.type === 'slack.notify'" class="text-xs text-text-muted pl-7 space-y-1">
          <div v-if="action.params.config_id">Config: {{ action.params.config_id }}</div>
          <div v-if="action.params.channel">Channel: {{ action.params.channel }}</div>
          <div v-if="action.params.template" class="font-mono bg-background-base px-2 py-1 rounded">
            {{ truncate(action.params.template, 60) }}
          </div>
        </div>

        <div v-if="action.type === 'task.retry'" class="text-xs text-text-muted pl-7">
          <div v-if="action.params.delay_seconds">
            Delay: {{ action.params.delay_seconds }}s
          </div>
          <div v-else>Retry immediately</div>
        </div>
      </div>

      <!-- Add Action Button -->
      <Button size="sm" variant="outline" @click="showActionSelector = true" class="w-full">
        <Plus class="h-3.5 w-3.5 mr-1.5" />
        Add Action
      </Button>
    </div>

    <!-- Action Type Selector Dialog -->
    <Dialog :open="showActionSelector" @update:open="showActionSelector = $event">
      <DialogContent class="max-w-lg">
        <DialogHeader>
          <DialogTitle>Add Action</DialogTitle>
          <DialogDescription>
            Choose what to do when this workflow triggers
          </DialogDescription>
        </DialogHeader>

        <div class="grid grid-cols-2 gap-3">
          <button
            v-for="actionType in actionTypes"
            :key="actionType.type"
            class="p-4 rounded-lg border border-border hover:border-primary hover:bg-background-hover transition-colors text-left"
            @click="selectActionType(actionType.type)"
          >
            <component :is="actionType.icon" class="h-6 w-6 text-primary mb-2" />
            <div class="text-sm font-medium text-text-primary mb-1">
              {{ actionType.label }}
            </div>
            <div class="text-xs text-text-muted">
              {{ actionType.description }}
            </div>
          </button>
        </div>
      </DialogContent>
    </Dialog>

    <!-- Action Configuration Dialogs -->
    <WorkflowSlackActionConfig
      v-if="editingAction !== null && actions[editingAction]?.type === 'slack.notify'"
      :action="actions[editingAction]"
      :open="editingAction !== null"
      @update:action="updateAction(editingAction, $event)"
      @close="handleConfigClose"
    />

    <WorkflowRetryActionConfig
      v-if="editingAction !== null && actions[editingAction]?.type === 'task.retry'"
      :action="actions[editingAction]"
      :open="editingAction !== null"
      @update:action="updateAction(editingAction, $event)"
      @close="handleConfigClose"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { Plus, X, Settings, Zap, MessageSquare, RotateCw, Mail, Webhook } from 'lucide-vue-next'
import { Button } from '~/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle
} from '~/components/ui/dialog'
import WorkflowSlackActionConfig from './WorkflowSlackActionConfig.vue'
import WorkflowRetryActionConfig from './WorkflowRetryActionConfig.vue'
import type { ActionConfig } from '~/types/workflow'

const props = defineProps<{
  actions: ActionConfig[]
}>()

const emit = defineEmits<{
  'update:actions': [actions: ActionConfig[]]
}>()

const showActionSelector = ref(false)
const editingAction = ref<number | null>(null)

const actionTypes = [
  {
    type: 'slack.notify',
    label: 'Slack Notification',
    description: 'Send message to Slack',
    icon: MessageSquare
  },
  {
    type: 'task.retry',
    label: 'Retry Task',
    description: 'Retry the failed task',
    icon: RotateCw
  },
  {
    type: 'email.send',
    label: 'Email',
    description: 'Send email notification',
    icon: Mail
  },
  {
    type: 'webhook.call',
    label: 'Webhook',
    description: 'Call HTTP endpoint',
    icon: Webhook
  }
]

async function selectActionType(type: string) {
  const newAction: ActionConfig = {
    type,
    params: {},
    continue_on_failure: true
  }

  emit('update:actions', [...props.actions, newAction])
  showActionSelector.value = false

  // Wait for the action to be added to the array before opening config dialog
  await nextTick()
  editingAction.value = props.actions.length
}

function editAction(index: number) {
  editingAction.value = index
}

function removeAction(index: number) {
  const updated = props.actions.filter((_, i) => i !== index)
  emit('update:actions', updated)
}

function updateAction(index: number, action: ActionConfig) {
  const updated = [...props.actions]
  updated[index] = action
  emit('update:actions', updated)
  editingAction.value = null
}

function handleConfigClose() {
  // If closing without configuring a newly added action, remove it
  if (editingAction.value !== null) {
    const action = props.actions[editingAction.value]
    const isNewAction = Object.keys(action.params).length === 0

    // For Slack actions, require config_id and template
    if (action.type === 'slack.notify' && isNewAction) {
      removeAction(editingAction.value)
    }
  }
  editingAction.value = null
}

function getActionIcon(type: string) {
  const actionType = actionTypes.find(a => a.type === type)
  return actionType?.icon || Zap
}

function getActionLabel(type: string): string {
  const actionType = actionTypes.find(a => a.type === type)
  return actionType?.label || type
}

function getActionDescription(type: string): string {
  const actionType = actionTypes.find(a => a.type === type)
  return actionType?.description || ''
}

function truncate(text: string, length: number): string {
  return text.length > length ? text.substring(0, length) + '...' : text
}
</script>
