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
              Channel Override (optional)
            </label>
            <Input
              :value="localAction.params.channel"
              @input="localAction.params.channel = ($event.target as HTMLInputElement).value"
              placeholder="#channel-name"
              class="w-full"
            />
            <p class="text-xs text-text-muted mt-1">
              Override the default channel from your webhook config
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
          <div v-if="localAction.params.template" class="border border-border rounded-lg p-3 bg-background-base">
            <div class="text-xs font-medium text-text-secondary mb-2">Preview</div>
            <div class="text-sm text-text-primary font-mono whitespace-pre-wrap">
              {{ previewMessage }}
            </div>
          </div>

          <!-- Advanced Options -->
          <details class="border border-border rounded-lg">
            <summary class="p-3 cursor-pointer text-xs font-medium text-text-primary hover:bg-background-hover-subtle">
              Advanced Options
            </summary>
            <div class="p-3 border-t border-border space-y-3">
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

watch(() => props.action, (newAction) => {
  localAction.value = { ...newAction }
}, { deep: true })

const availableVariables = '{{task_id}}, {{task_name}}, {{queue}}, {{exception}}, {{retry_count}}'
const templatePlaceholder = 'e.g., 🚨 Task {{task_name}} failed!'

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

onMounted(async () => {
  if (!slackConfigs.value.length) {
    try {
      await workflowStore.fetchActionConfigs({ action_type: 'slack.notify' })
    } catch (e) {
      console.error('Failed to load Slack configs:', e)
    }
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
