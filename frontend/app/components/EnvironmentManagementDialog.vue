<template>
  <Dialog v-model:open="isOpen">
    <DialogContent class="max-w-3xl max-h-[85vh] overflow-hidden flex flex-col bg-background-surface border-border p-0">
      <DialogHeader class="px-6 pt-6 pb-4 border-b border-border">
        <div class="flex items-center justify-between">
          <div>
            <DialogTitle class="text-lg font-semibold text-text-primary">Environments</DialogTitle>
            <DialogDescription class="text-xs text-text-secondary mt-0.5">
              Filter tasks by queue and worker patterns
            </DialogDescription>
          </div>
          <Button @click="openCreateForm" size="sm" class="h-8 text-xs">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-1.5">
              <line x1="12" y1="5" x2="12" y2="19"/>
              <line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            New
          </Button>
        </div>
      </DialogHeader>

      <div class="flex-1 overflow-y-auto px-6 py-4">
        <div v-if="environmentStore.environments.length === 0" class="text-center py-16">
          <svg xmlns="http://www.w3.org/2000/svg" width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="mx-auto mb-4 text-text-muted opacity-30">
            <path d="M3 3v18h18"/>
            <path d="M18 17V9"/>
            <path d="M13 17V5"/>
            <path d="M8 17v-3"/>
          </svg>
          <p class="text-sm text-text-secondary">No environments configured</p>
          <p class="text-xs text-text-muted mt-1">Create your first environment to start filtering</p>
        </div>

        <div class="space-y-2">
          <div
            v-for="env in environmentStore.environments"
            :key="env.id"
            class="group relative bg-background-surface border border-border rounded-lg p-4 transition-all duration-200 cursor-pointer"
            :class="{
              'bg-background-raised border-primary/30 shadow-glow-sm': env.is_active,
              'hover:bg-background-raised hover:border-border-highlight': !env.is_active
            }"
            @click="!env.is_active && activateEnv(env.id)"
          >
            <!-- Header Row -->
            <div class="flex items-start justify-between gap-3 mb-3">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1">
                  <!-- Status Indicator -->
                  <div v-if="env.is_active" class="w-2 h-2 rounded-full bg-primary shadow-glow-sm animate-pulse-subtle"></div>

                  <h3 class="text-sm font-mono font-medium text-text-primary truncate">
                    {{ env.name }}
                  </h3>

                  <Badge v-if="env.is_active" variant="online" class="text-[10px] font-mono uppercase tracking-wide">
                    Active
                  </Badge>
                  <Badge v-if="env.is_default" variant="default" class="text-[10px] font-mono uppercase tracking-wide">
                    Default
                  </Badge>
                </div>

                <p v-if="env.description" class="text-xs text-text-muted line-clamp-1 font-mono">
                  {{ env.description }}
                </p>
              </div>

              <DropdownMenu>
                <DropdownMenuTrigger as-child @click.stop>
                  <button class="flex-shrink-0 w-7 h-7 flex items-center justify-center rounded-md hover:bg-background-hover text-text-muted hover:text-text-primary transition-all duration-200 opacity-0 group-hover:opacity-100">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <circle cx="12" cy="12" r="1"/>
                      <circle cx="12" cy="5" r="1"/>
                      <circle cx="12" cy="19" r="1"/>
                    </svg>
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" class="bg-background-surface border-border w-40">
                  <DropdownMenuItem @click="editEnvironment(env)" class="text-text-primary hover:bg-background-hover cursor-pointer text-sm font-mono">
                    Edit
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    v-if="!env.is_active"
                    @click="activateEnv(env.id)"
                    class="text-text-primary hover:bg-background-hover cursor-pointer text-sm font-mono"
                  >
                    Activate
                  </DropdownMenuItem>
                  <DropdownMenuSeparator class="bg-border" />
                  <DropdownMenuItem
                    @click="confirmDelete(env)"
                    :disabled="env.is_active"
                    class="text-status-error hover:bg-status-error/10 cursor-pointer text-sm font-mono"
                    :class="{ 'opacity-50 cursor-not-allowed': env.is_active }"
                  >
                    Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>

            <!-- Patterns Grid -->
            <div class="grid grid-cols-1 gap-2 text-xs">
              <div v-if="env.queue_patterns.length > 0" class="flex items-start gap-2">
                <span class="text-text-muted font-mono text-[10px] uppercase tracking-wider mt-1 flex-shrink-0">Queues</span>
                <div class="flex flex-wrap gap-1 flex-1">
                  <Badge
                    v-for="pattern in env.queue_patterns"
                    :key="pattern"
                    variant="secondary"
                    class="text-[10px] font-mono bg-background-base border border-border hover:border-border-highlight transition-colors"
                  >
                    {{ pattern }}
                  </Badge>
                </div>
              </div>

              <div v-if="env.worker_patterns.length > 0" class="flex items-start gap-2">
                <span class="text-text-muted font-mono text-[10px] uppercase tracking-wider mt-1 flex-shrink-0">Workers</span>
                <div class="flex flex-wrap gap-1 flex-1">
                  <Badge
                    v-for="pattern in env.worker_patterns"
                    :key="pattern"
                    variant="secondary"
                    class="text-[10px] font-mono bg-background-base border border-border hover:border-border-highlight transition-colors"
                  >
                    {{ pattern }}
                  </Badge>
                </div>
              </div>

              <div v-if="env.queue_patterns.length === 0 && env.worker_patterns.length === 0" class="text-text-muted text-xs font-mono italic">
                No filters — matches all tasks
              </div>
            </div>
          </div>
        </div>
      </div>
    </DialogContent>
  </Dialog>

  <!-- Create/Edit Form Dialog -->
  <Dialog v-model:open="isFormOpen">
    <DialogContent class="max-w-2xl bg-background-surface border-border p-0">
      <DialogHeader class="px-6 pt-6 pb-4 border-b border-border">
        <DialogTitle class="text-lg font-semibold text-text-primary">{{ isEditing ? 'Edit' : 'New' }} Environment</DialogTitle>
        <DialogDescription class="text-xs text-text-secondary mt-0.5">
          Wildcards: * (any chars), ? (single char)
        </DialogDescription>
      </DialogHeader>

      <div class="px-6 py-4 space-y-3">
        <div class="space-y-1.5">
          <Label for="name" class="text-xs font-medium text-text-primary">Name *</Label>
          <Input
            id="name"
            :value="formName"
            @input="formName = ($event.target as HTMLInputElement).value"
            placeholder="Production"
            class="h-9 bg-background-base border-border text-text-primary text-sm"
          />
        </div>

        <div class="space-y-1.5">
          <Label for="description" class="text-xs font-medium text-text-primary">Description</Label>
          <Textarea
            id="description"
            v-model="formDescription"
            placeholder="Optional description"
            class="bg-background-base border-border text-text-primary text-sm resize-none"
            rows="2"
          />
        </div>

        <div class="space-y-1.5">
          <Label class="text-xs font-medium text-text-primary">Queue Patterns</Label>
          <TagsInput v-model="formQueuePatterns" class="min-h-[36px] bg-background-base border-border">
            <TagsInputItem v-for="pattern in formQueuePatterns" :key="pattern" :value="pattern">
              <TagsInputItemText class="text-xs" />
              <TagsInputItemDelete />
            </TagsInputItem>
            <TagsInputInput placeholder="prod-*, staging-*" class="text-sm text-text-primary placeholder:text-text-muted" />
          </TagsInput>
          <p class="text-[10px] text-text-muted">Press Enter to add. Ex: prod-*, staging-queue-?</p>
        </div>

        <div class="space-y-1.5">
          <Label class="text-xs font-medium text-text-primary">Worker Patterns</Label>
          <TagsInput v-model="formWorkerPatterns" class="min-h-[36px] bg-background-base border-border">
            <TagsInputItem v-for="pattern in formWorkerPatterns" :key="pattern" :value="pattern">
              <TagsInputItemText class="text-xs" />
              <TagsInputItemDelete />
            </TagsInputItem>
            <TagsInputInput placeholder="worker-*.prod.com" class="text-sm text-text-primary placeholder:text-text-muted" />
          </TagsInput>
          <p class="text-[10px] text-text-muted">Press Enter to add. Ex: worker-*.prod.com, celery@prod-*</p>
        </div>

        <div class="flex items-center gap-2 pt-1">
          <Switch id="is_default" v-model:checked="formIsDefault" class="data-[state=checked]:bg-primary data-[state=unchecked]:bg-border" />
          <Label for="is_default" class="text-xs text-text-primary cursor-pointer">Set as default</Label>
        </div>
      </div>

      <div class="px-6 py-4 border-t border-border flex justify-end gap-2">
        <Button @click="isFormOpen = false" variant="outline" size="sm" class="h-8 text-xs">Cancel</Button>
        <Button @click="saveEnvironment" :disabled="!isFormValid || environmentStore.loading" size="sm" class="h-8 text-xs">
          {{ environmentStore.loading ? 'Saving...' : 'Save' }}
        </Button>
      </div>
    </DialogContent>
  </Dialog>

  <!-- Delete Confirmation Dialog -->
  <AlertDialog v-model:open="isDeleteDialogOpen">
    <AlertDialogContent class="bg-background-surface border-border max-w-md">
      <AlertDialogHeader>
        <AlertDialogTitle class="text-base font-semibold text-text-primary">Delete Environment</AlertDialogTitle>
        <AlertDialogDescription class="text-xs text-text-secondary">
          Delete "{{ environmentToDelete?.name }}"? This cannot be undone.
        </AlertDialogDescription>
      </AlertDialogHeader>
      <AlertDialogFooter class="gap-2">
        <AlertDialogCancel class="h-8 text-xs bg-background-base text-text-primary border-border hover:bg-background-hover">
          Cancel
        </AlertDialogCancel>
        <AlertDialogAction
          @click="deleteEnv"
          class="h-8 text-xs bg-red-600 text-white hover:bg-red-700"
        >
          Delete
        </AlertDialogAction>
      </AlertDialogFooter>
    </AlertDialogContent>
  </AlertDialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useEnvironmentStore } from '~/stores/environment'
import type { Environment, EnvironmentCreate, EnvironmentUpdate } from '~/stores/environment'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '~/components/ui/dialog'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '~/components/ui/alert-dialog'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '~/components/ui/dropdown-menu'
import { TagsInput, TagsInputInput, TagsInputItem, TagsInputItemDelete, TagsInputItemText } from '~/components/ui/tags-input'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Textarea } from '~/components/ui/textarea'
import { Label } from '~/components/ui/label'
import { Badge } from '~/components/ui/badge'
import { Switch } from '~/components/ui/switch'

const props = defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
}>()

const environmentStore = useEnvironmentStore()

const isOpen = computed({
  get: () => props.open,
  set: (value) => emit('update:open', value)
})

const isFormOpen = ref(false)
const isEditing = ref(false)
const editingId = ref<string | null>(null)

const formName = ref('')
const formDescription = ref('')
const formQueuePatterns = ref<string[]>([])
const formWorkerPatterns = ref<string[]>([])
const formIsDefault = ref(false)

const isFormValid = computed(() => {
  return formName.value && formName.value.trim().length > 0
})

const isDeleteDialogOpen = ref(false)
const environmentToDelete = ref<Environment | null>(null)

function openCreateForm() {
  isEditing.value = false
  editingId.value = null
  formName.value = ''
  formDescription.value = ''
  formQueuePatterns.value = []
  formWorkerPatterns.value = []
  formIsDefault.value = false
  isFormOpen.value = true
}

function editEnvironment(env: Environment) {
  isEditing.value = true
  editingId.value = env.id
  formName.value = env.name
  formDescription.value = env.description || ''
  formQueuePatterns.value = [...env.queue_patterns]
  formWorkerPatterns.value = [...env.worker_patterns]
  formIsDefault.value = env.is_default
  isFormOpen.value = true
}

async function saveEnvironment() {
  if (!isFormValid.value || environmentStore.loading) {
    return
  }

  try {
    if (isEditing.value && editingId.value) {
      const update: EnvironmentUpdate = {
        name: formName.value.trim(),
        description: formDescription.value.trim() || undefined,
        queue_patterns: formQueuePatterns.value,
        worker_patterns: formWorkerPatterns.value,
        is_default: formIsDefault.value
      }
      await environmentStore.updateEnvironment(editingId.value, update)
    } else {
      await environmentStore.createEnvironment({
        name: formName.value.trim(),
        description: formDescription.value.trim() || undefined,
        queue_patterns: formQueuePatterns.value,
        worker_patterns: formWorkerPatterns.value,
        is_default: formIsDefault.value
      })
    }
    isFormOpen.value = false
  } catch (err) {
    console.error('Failed to save environment:', err)
  }
}

function confirmDelete(env: Environment) {
  environmentToDelete.value = env
  isDeleteDialogOpen.value = true
}

async function deleteEnv() {
  if (environmentToDelete.value) {
    try {
      await environmentStore.deleteEnvironment(environmentToDelete.value.id)
      isDeleteDialogOpen.value = false
      environmentToDelete.value = null
    } catch (err) {
      console.error('Failed to delete environment:', err)
    }
  }
}

async function activateEnv(id: string) {
  try {
    await environmentStore.activateEnvironment(id)
  } catch (err) {
    console.error('Failed to activate environment:', err)
  }
}
</script>
