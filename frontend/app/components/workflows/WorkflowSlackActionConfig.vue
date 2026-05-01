<template>
  <div>
    <Dialog :open="open" @update:open="$emit('close')">
      <DialogContent class="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Configure Slack Notification</DialogTitle>
          <DialogDescription>
            Send a message to Slack when this workflow triggers
          </DialogDescription>
        </DialogHeader>

        <div class="space-y-4 py-4">
          <!-- Config ID -->
          <div>
            <label class="text-xs font-medium text-text-secondary mb-1.5 block">
              Webhook Config *
            </label>
            <div class="flex items-start gap-2">
              <Select
                :model-value="localAction.params.config_id || ''"
                class="w-full h-9 text-sm"
                @update:model-value="value => localAction.params.config_id = value as string"
              >
                <option disabled value="">Select configuration</option>
                <option
                  v-for="config in slackConfigs"
                  :key="config.id"
                  :value="config.id"
                >
                  {{ config.name }}
                </option>
              </Select>
              <Button
                variant="outline"
                size="xs"
                class="h-9"
                @click="showConfigManager = true"
              >
                Manage
              </Button>
            </div>
            <p class="text-xs text-text-muted mt-1">
              Choose a stored Slack webhook configuration
            </p>
          </div>

          <!-- Channel (optional) -->
          <div>
            <label class="text-xs font-medium text-text-secondary mb-1.5 block">
              Channel (optional)
            </label>
            <Input
              :value="localAction.params.channel"
              @input="localAction.params.channel = ($event.target as HTMLInputElement).value"
              placeholder="#channel-name"
              class="w-full"
            />
            <p class="text-xs text-text-muted mt-1">
              Specify the channel to send this notification to
            </p>
          </div>

          <!-- Message Template -->
          <div>
            <label class="text-xs font-medium text-text-secondary mb-1.5 block">
              Message Template *
            </label>
            <Textarea
              :model-value="localAction.params.template"
              @update:model-value="localAction.params.template = $event"
              :placeholder="templatePlaceholder"
              :rows="4"
              class="w-full font-mono text-xs"
            />
            <p class="text-xs text-text-muted mt-1">
              Available variables: <span v-text="availableVariables"></span>
            </p>
          </div>

          <!-- Preview -->
          <div v-if="localAction.params.template" class="border border-border-subtle rounded-lg p-3 bg-background-base space-y-2">
            <div class="text-xs font-medium text-text-secondary mb-2">Preview</div>
            <div class="flex items-center gap-2 text-xs">
              <Button variant="outline" size="xs" class="h-7" @click="runPreview" :disabled="previewLoading || !isValid">
                {{ previewLoading ? 'Loading…' : 'Refresh preview' }}
              </Button>
              <span v-if="preview?.stage" class="text-text-muted">Stage: {{ preview.stage }}</span>
              <span v-if="preview?.skip_reason" class="text-status-warning">{{ preview.skip_reason }}</span>
            </div>
            <div class="text-sm text-text-primary font-mono whitespace-pre-wrap">
              {{ preview?.message || previewMessage }}
            </div>
          </div>

          <div class="border border-border-subtle rounded-lg p-3 space-y-3">
            <div>
              <div class="text-xs font-medium text-text-secondary mb-1">Notification policy</div>
              <p class="text-xs text-text-muted">Add cooldown dedupe and optional escalation steps for slower or more severe incidents.</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label class="text-xs font-medium text-text-secondary mb-1.5 block">Dedupe window (seconds)</label>
                <Input v-model="dedupeWindowInput" type="number" min="0" class="w-full" />
              </div>
              <div>
                <label class="text-xs font-medium text-text-secondary mb-1.5 block">Minimum severity</label>
                <Select v-model="notificationPolicy.minimum_severity" class="w-full h-9 text-sm">
                  <option value="">Any severity</option>
                  <option v-for="level in severityLevels" :key="level" :value="level">{{ level }}</option>
                </Select>
              </div>
            </div>

            <div>
              <label class="text-xs font-medium text-text-secondary mb-1.5 block">Dedupe key template</label>
              <Input v-model="notificationPolicy.dedupe_key_template" class="w-full" placeholder="{{task_name}}:{{event_type}}:{{task_id}}" />
            </div>

            <div>
              <label class="text-xs font-medium text-text-secondary mb-1.5 block">Escalate after (seconds)</label>
              <Input v-model="escalationAfterInput" type="number" min="0" class="w-full" />
              <p class="text-xs text-text-muted mt-1">When reached, switch to the escalation channel/config and message below.</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label class="text-xs font-medium text-text-secondary mb-1.5 block">Escalation config</label>
                <Select v-model="escalationStep.config_id" class="w-full h-9 text-sm">
                  <option value="">Keep primary config</option>
                  <option v-for="config in slackConfigs" :key="config.id" :value="config.id">{{ config.name }}</option>
                </Select>
              </div>
              <div>
                <label class="text-xs font-medium text-text-secondary mb-1.5 block">Escalation channel</label>
                <Input v-model="escalationStep.channel" class="w-full" placeholder="#incidents-critical" />
              </div>
            </div>

            <div>
              <label class="text-xs font-medium text-text-secondary mb-1.5 block">Escalation template</label>
              <Textarea v-model="escalationStep.template" :rows="3" class="w-full font-mono text-xs" placeholder="Escalation: {{task_name}} is still failing after {{duration_seconds}}s" />
            </div>
          </div>

          <!-- Advanced Options -->
          <details class="border border-border-subtle rounded-lg">
            <summary class="p-3 cursor-pointer text-xs font-medium text-text-primary hover:bg-background-hover-subtle">
              Advanced Options
            </summary>
            <div class="p-3 border-t border-border-subtle space-y-3">
              <div class="flex items-center justify-between">
                <div>
                  <label class="text-xs font-medium text-text-primary">Continue on Failure</label>
                  <p class="text-xs text-text-muted">Continue to next action if this fails</p>
                </div>
                <Switch
                  :checked="localAction.continue_on_failure"
                  @update:checked="localAction.continue_on_failure = $event"
                />
              </div>
              <div>
                <label class="text-xs font-medium text-text-secondary mb-1.5 block">
                  Color
                </label>
                <Select v-model="localAction.params.color" class="w-full h-8 text-xs" size="sm">
                  <option value="">Default</option>
                  <option value="#36a64f">Green (Success)</option>
                  <option value="#ff0000">Red (Error)</option>
                  <option value="#ffa500">Orange (Warning)</option>
                  <option value="#0000ff">Blue (Info)</option>
                </Select>
              </div>
            </div>
          </details>
        </div>

        <DialogFooter>
          <Button variant="outline" @click="$emit('close')">Cancel</Button>
          <Button @click="save" :disabled="!isValid">Save</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <WorkflowSlackConfigManager
      :open="showConfigManager"
      :enable-selection="true"
      @close="showConfigManager = false"
      @select="handleConfigSelected"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Textarea } from '~/components/ui/textarea'
import { Switch } from '~/components/ui/switch'
import Select from '~/components/common/Select.vue'
import WorkflowSlackConfigManager from '~/components/workflows/WorkflowSlackConfigManager.vue'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from '~/components/ui/dialog'
import type { ActionConfig } from '~/types/workflow'
import { useWorkflowsStore } from '~/stores/workflows'
import type { WorkflowActionPreviewResponse } from '~/types/workflow'

const props = defineProps<{
  action: ActionConfig
  open: boolean
}>()

const emit = defineEmits<{
  'update:action': [action: ActionConfig]
  'close': []
}>()

const localAction = ref<ActionConfig>({ ...props.action })
const workflowStore = useWorkflowsStore()
const slackConfigs = computed(() =>
  workflowStore.actionConfigs.filter(config => config.action_type === 'slack.notify')
)
const showConfigManager = ref(false)
const preview = ref<WorkflowActionPreviewResponse | null>(null)
const previewLoading = ref(false)

watch(() => props.action, (newAction) => {
  localAction.value = { ...newAction }
}, { deep: true })

const availableVariables = '{{task_id}}, {{task_name}}, {{queue}}, {{exception}}, {{retry_count}}'
const templatePlaceholder = 'e.g., 🚨 Task {{task_name}} failed!'
const severityLevels = ['low', 'medium', 'high', 'critical']

const notificationPolicy = computed(() => {
  if (!localAction.value.params.notification_policy) {
    localAction.value.params.notification_policy = {}
  }
  return localAction.value.params.notification_policy
})

const escalationStep = computed(() => {
  if (!notificationPolicy.value.escalation_steps?.length) {
    notificationPolicy.value.escalation_steps = [{}]
  }
  return notificationPolicy.value.escalation_steps[0]
})

const dedupeWindowInput = computed({
  get: () => notificationPolicy.value.dedupe_window_seconds ?? '',
  set: (value: string | number) => {
    const parsed = Number(value)
    if (!value || Number.isNaN(parsed) || parsed <= 0) delete notificationPolicy.value.dedupe_window_seconds
    else notificationPolicy.value.dedupe_window_seconds = parsed
  }
})

const escalationAfterInput = computed({
  get: () => escalationStep.value.after_seconds ?? '',
  set: (value: string | number) => {
    const parsed = Number(value)
    if (!value || Number.isNaN(parsed) || parsed <= 0) {
      delete escalationStep.value.after_seconds
    } else {
      escalationStep.value.after_seconds = parsed
      escalationStep.value.name = 'escalated'
    }
  }
})

const isValid = computed(() => {
  return localAction.value.params.config_id?.toString().trim().length > 0 &&
         localAction.value.params.template?.trim().length > 0
})

const previewMessage = computed(() => {
  if (!localAction.value.params.template) return ''

  return localAction.value.params.template
    .replace(/\{\{task_id\}\}/g, 'abc-123-def')
    .replace(/\{\{task_name\}\}/g, 'process_payment')
    .replace(/\{\{queue\}\}/g, 'high-priority')
    .replace(/\{\{exception\}\}/g, 'PaymentGatewayTimeout')
    .replace(/\{\{retry_count\}\}/g, '3')
})

function save() {
  emit('update:action', localAction.value)
}

async function runPreview() {
  previewLoading.value = true
  try {
    preview.value = await workflowStore.previewWorkflowAction(localAction.value.type, localAction.value.params, {
      task_id: 'preview-task-123',
      task_name: 'tasks.payment.capture',
      event_type: 'task-failed',
      queue: 'payments',
      exception: 'PaymentGatewayTimeout',
      retry_count: 3,
      severity: 'high',
      duration_seconds: Number(escalationStep.value.after_seconds || 0) || 120
    })
  } catch (e) {
    console.error('Failed to preview notification action:', e)
  } finally {
    previewLoading.value = false
  }
}

onMounted(async () => {
  if (!slackConfigs.value.length) {
    try {
      await workflowStore.fetchActionConfigs({ action_type: 'slack.notify' })
    } catch (e) {
      console.error('Failed to load Slack configs:', e)
    }
  }
  if (localAction.value.params.template) {
    await runPreview()
  }
})

function handleConfigSelected(configId: string) {
  showConfigManager.value = false

  if (!configId) {
    if (
      localAction.value.params.config_id &&
      !slackConfigs.value.some(cfg => cfg.id === localAction.value.params.config_id)
    ) {
      localAction.value.params.config_id = ''
    }
    return
  }

  localAction.value.params.config_id = configId
}
</script>
