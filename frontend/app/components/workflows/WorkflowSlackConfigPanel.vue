<template>
  <div class="space-y-5">
    <div class="rounded-2xl border border-border bg-background-surface shadow-sm">
      <div class="flex flex-wrap items-start justify-between gap-4 border-b border-border px-6 py-5">
        <div>
          <h2 class="text-sm font-semibold text-text-primary">Slack Webhooks</h2>
          <p class="text-xs text-text-muted">
            Configure reusable Slack webhook destinations for your workflow notifications.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          class="shrink-0"
          @click="startCreate"
        >
          <Plus class="h-3.5 w-3.5 mr-1" />
          New Webhook
        </Button>
      </div>

      <div class="px-6 py-5 space-y-5">
        <div v-if="slackConfigs.length === 0 && mode !== 'form'" class="text-sm text-text-muted">
          No Slack configurations yet. Create one to start sending workflow alerts.
        </div>

        <div
          v-for="config in slackConfigs"
          :key="config.id"
          class="rounded-xl border border-border bg-background-base px-4 py-4 shadow-sm"
        >
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div class="space-y-2">
              <div class="flex items-center gap-2">
                <h3 class="text-sm font-medium text-text-primary">
                  {{ config.name }}
                </h3>
                <Badge
                  v-if="config.usage_count > 0"
                  size="xs"
                  variant="outline"
                >
                  {{ config.usage_count }} use{{ config.usage_count === 1 ? '' : 's' }}
                </Badge>
              </div>
              <p v-if="config.description" class="text-xs text-text-muted max-w-prose">
                {{ config.description }}
              </p>
              <p class="text-[11px] text-text-secondary">
                Webhook destination stored securely.
              </p>
            </div>
            <div class="flex flex-col items-end gap-2 shrink-0">
              <Button
                variant="outline"
                size="xs"
                @click="startEdit(config)"
              >
                <Pencil class="h-3.5 w-3.5 mr-1" />
                Edit
              </Button>
              <Button
                variant="ghost"
                size="xs"
                class="text-status-error hover:text-status-error-hover"
                @click="confirmDelete(config)"
                :disabled="deletingId === config.id"
              >
                <Trash2 class="h-3.5 w-3.5 mr-1" />
                Delete
              </Button>
              <Button
                variant="secondary"
                size="xs"
                v-if="selectionEnabled"
                @click="selectConfig(config)"
              >
                Use
              </Button>
            </div>
          </div>
        </div>

        <div
          v-if="mode === 'form'"
          class="rounded-xl border border-border bg-background-base px-5 py-5 shadow-sm space-y-5"
        >
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-text-primary">
              {{ editingConfig?.id ? 'Edit Slack Webhook' : 'Create Slack Webhook' }}
            </span>
            <Button variant="ghost" size="xs" @click="cancelForm">
              Cancel
            </Button>
          </div>
          <div class="space-y-4">
            <div>
              <label class="text-[11px] font-medium text-text-secondary mb-1 block">
                Name *
              </label>
              <Input
                :value="form.name"
                placeholder="e.g., Pager Alerts"
                @input="form.name = ($event.target as HTMLInputElement).value"
              />
            </div>
            <div>
              <label class="text-[11px] font-medium text-text-secondary mb-1 block">
                Description
              </label>
              <Textarea
                v-model="form.description"
                rows="2"
                placeholder="How will this webhook be used?"
              />
            </div>
            <div>
              <label class="text-[11px] font-medium text-text-secondary mb-1 block">
                Webhook URL *
              </label>
              <Input
                :value="form.webhook_url"
                type="url"
                placeholder="https://hooks.slack.com/services/..."
                @input="form.webhook_url = ($event.target as HTMLInputElement).value"
              />
            </div>
          </div>
          <div class="flex justify-end gap-2">
            <Button
              variant="outline"
              size="sm"
              @click="cancelForm"
              :disabled="saving"
            >
              Cancel
            </Button>
            <Button
              size="sm"
              @click="saveForm"
              :disabled="!isFormValid || saving"
            >
              {{ saving ? 'Saving...' : 'Save' }}
            </Button>
          </div>
        </div>

        <div v-if="error" class="rounded-lg border border-status-error/40 bg-status-error/5 px-4 py-3 text-xs text-status-error">
          {{ error }}
        </div>
        <div v-else class="text-xs text-text-muted">
          Configurations are shared across workflows that send Slack notifications.
        </div>
      </div>
    </div>

    <AlertDialog :open="!!configToDelete" @update:open="val => !val && (configToDelete = null)">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Slack Configuration</AlertDialogTitle>
          <AlertDialogDescription>
            This will remove "{{ configToDelete?.name }}". Workflows using it will fail until updated.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            class="bg-status-error hover:bg-status-error-hover"
            @click="deleteConfig"
          >
            Delete
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { Plus, Pencil, Trash2 } from 'lucide-vue-next'

import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import { Input } from '~/components/ui/input'
import { Textarea } from '~/components/ui/textarea'
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
import type {
  ActionConfigDefinition,
  ActionConfigCreateRequest,
  ActionConfigUpdateRequest
} from '~/types/workflow'
import { useWorkflowsStore } from '~/stores/workflows'

const props = defineProps<{
  active?: boolean
  enableSelection?: boolean
}>()

const emit = defineEmits<{
  select: [configId: string]
  requestClose: []
}>()

const workflowStore = useWorkflowsStore()
const slackConfigs = computed(() =>
  workflowStore.actionConfigs.filter(config => config.action_type === 'slack.notify')
)
const selectionEnabled = computed(() => props.enableSelection !== false)

const mode = ref<'list' | 'form'>('list')
const editingConfig = ref<ActionConfigDefinition | null>(null)
const configToDelete = ref<ActionConfigDefinition | null>(null)
const deletingId = ref<string | null>(null)
const saving = ref(false)

const form = reactive({
  name: '',
  description: '',
  webhook_url: ''
})

const error = computed(() => workflowStore.error)

const isFormValid = computed(() => {
  return form.name.trim().length > 0 && form.webhook_url.trim().length > 0
})

async function ensureLoaded() {
  if (!slackConfigs.value.length) {
    try {
      await workflowStore.fetchActionConfigs({ action_type: 'slack.notify' })
    } catch (err) {
      console.error('Failed to load Slack configs:', err)
    }
  }
}

const isActive = computed(() => props.active !== false)

watch(
  () => isActive.value,
  async (active) => {
    if (active) {
      await ensureLoaded()
    } else {
      resetState()
    }
  },
  { immediate: true }
)

function startCreate() {
  editingConfig.value = null
  mode.value = 'form'
  resetForm()
}

function startEdit(config: ActionConfigDefinition) {
  editingConfig.value = config
  mode.value = 'form'
  form.name = config.name
  form.description = config.description || ''
  form.webhook_url = config.config.webhook_url || ''
}

function cancelForm() {
  mode.value = 'list'
  editingConfig.value = null
  resetForm()
  workflowStore.clearError()
}

function resetForm() {
  form.name = ''
  form.description = ''
  form.webhook_url = ''
}

async function saveForm() {
  if (!isFormValid.value) return

  saving.value = true
  try {
    const payload = {
      name: form.name.trim(),
      description: form.description.trim() || undefined,
      config: {
        webhook_url: form.webhook_url.trim()
      }
    }

    let result: ActionConfigDefinition
    if (editingConfig.value && editingConfig.value.id) {
      const updatePayload: ActionConfigUpdateRequest = payload
      result = await workflowStore.updateActionConfig(editingConfig.value.id, updatePayload)
    } else {
      const createPayload: ActionConfigCreateRequest = {
        ...payload,
        action_type: 'slack.notify'
      }
      result = await workflowStore.createActionConfig(createPayload)
    }

    mode.value = 'list'
    editingConfig.value = null
    resetForm()
    if (selectionEnabled.value) {
      emit('select', result.id!)
    }
    workflowStore.clearError()
  } catch (err) {
    console.error('Failed to save Slack config:', err)
  } finally {
    saving.value = false
  }
}

function confirmDelete(config: ActionConfigDefinition) {
  configToDelete.value = config
}

async function deleteConfig() {
  if (!configToDelete.value?.id) return

  const id = configToDelete.value.id
  deletingId.value = id
  try {
    await workflowStore.deleteActionConfig(id)
    if (editingConfig.value?.id === id) {
      cancelForm()
    }
    configToDelete.value = null
    if (selectionEnabled.value) {
      emit('select', '')
    }
    workflowStore.clearError()
  } catch (err) {
    console.error('Failed to delete Slack config:', err)
  } finally {
    deletingId.value = null
  }
}

function selectConfig(config: ActionConfigDefinition) {
  if (!selectionEnabled.value) {
    return
  }
  if (config.id) {
    emit('select', config.id)
    emit('request-close')
  }
}

function resetState() {
  mode.value = 'list'
  editingConfig.value = null
  configToDelete.value = null
  deletingId.value = null
  saving.value = false
  resetForm()
  workflowStore.clearError()
}
</script>
