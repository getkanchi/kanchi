<template>
  <Sheet :open="isOpen" @update:open="handleClose">
    <SheetContent
      side="right"
      class="w-[800px] max-w-[95vw] p-0 border-l border-border bg-background-base"
    >
      <div v-if="task" class="h-full flex flex-col">
        <!-- Header -->
        <div class="flex items-start justify-between p-5 border-b border-border bg-background-surface">
          <div class="flex-1 min-w-0 pr-4">
            <!-- Edit mode: human readable name -->
            <div v-if="isEditing" class="mb-2">
              <label class="text-[10px] font-mono text-text-muted uppercase tracking-wider mb-1 block">Display Name</label>
              <input
                v-model="editForm.human_readable_name"
                type="text"
                class="w-full px-2 py-1 text-sm font-mono bg-background-base border border-border rounded text-text-primary focus:outline-none focus:border-primary"
                placeholder="Task display name"
              />
            </div>
            <h2 v-else class="text-base font-mono font-semibold text-text-primary mb-1 truncate">
              {{ task.human_readable_name || task.name }}
            </h2>

            <!-- Edit mode: description -->
            <div v-if="isEditing" class="mb-2">
              <label class="text-[10px] font-mono text-text-muted uppercase tracking-wider mb-1 block">Description</label>
              <textarea
                v-model="editForm.description"
                rows="2"
                class="w-full px-2 py-1 text-xs bg-background-base border border-border rounded text-text-secondary leading-relaxed focus:outline-none focus:border-primary resize-none"
                placeholder="Task description"
              />
            </div>
            <p v-else-if="task.description" class="text-xs text-text-secondary leading-relaxed mb-2">
              {{ task.description }}
            </p>

            <!-- Edit mode: tags -->
            <div v-if="isEditing" class="mb-2">
              <label class="text-[10px] font-mono text-text-muted uppercase tracking-wider mb-1 block">Tags</label>
              <div class="flex flex-wrap gap-1.5 mb-2">
                <BaseTag
                  v-for="(tag, index) in editForm.tags"
                  :key="index"
                  size="xs"
                  colored
                  :text="tag"
                  removable
                  @remove="removeTag(index)"
                >
                  {{ tag }}
                </BaseTag>
              </div>
              <div class="flex gap-2">
                <input
                  v-model="newTag"
                  type="text"
                  class="flex-1 px-2 py-1 text-xs font-mono bg-background-base border border-border rounded text-text-primary focus:outline-none focus:border-primary"
                  placeholder="Add tag..."
                  @keyup.enter="addTag"
                />
                <button
                  @click="addTag"
                  class="px-3 py-1 text-xs font-mono bg-background-raised border border-border rounded text-text-primary hover:bg-background-hover transition-colors"
                >
                  Add
                </button>
              </div>
            </div>
            <div v-else-if="task.tags && task.tags.length > 0" class="flex flex-wrap gap-1.5">
              <BaseTag
                v-for="tag in task.tags"
                :key="tag"
                size="xs"
                colored
                :text="tag"
              >
                {{ tag }}
              </BaseTag>
            </div>

            <!-- Edit mode: action buttons -->
            <div v-if="isEditing" class="flex gap-2 mt-3">
              <button
                @click="saveChanges"
                :disabled="isSaving"
                class="px-3 py-1.5 text-xs font-medium bg-primary text-white rounded hover:bg-primary-hover transition-colors disabled:opacity-50"
              >
                {{ isSaving ? 'Saving...' : 'Save' }}
              </button>
              <button
                @click="cancelEdit"
                :disabled="isSaving"
                class="px-3 py-1.5 text-xs font-medium bg-background-raised border border-border text-text-primary rounded hover:bg-background-hover transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
          <div class="flex gap-1">
            <BaseIconButton
              v-if="!isEditing"
              :icon="Pencil"
              size="sm"
              @click="startEdit"
            />
            <button
              @click="handleClose"
              class="flex-shrink-0 w-7 h-7 flex items-center justify-center rounded-md text-text-muted hover:text-text-primary hover:bg-background-hover transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
        </div>

        <!-- Content -->
        <div class="flex-1 overflow-y-auto p-5 space-y-4">
          <!-- Stats Grid -->
          <div class="grid grid-cols-2 gap-3">
            <!-- 24H Stats -->
            <div class="bg-background-surface border border-border rounded-lg p-3">
              <div class="text-[10px] font-mono font-bold text-text-muted uppercase tracking-wider mb-3">
                24H Activity
              </div>
              <div v-if="stats" class="grid grid-cols-2 gap-3">
                <div>
                  <div class="text-[10px] text-text-muted uppercase tracking-wide mb-0.5">Exec</div>
                  <div class="text-xl font-mono font-bold text-text-primary">
                    {{ stats.total_executions }}
                  </div>
                </div>
                <div>
                  <div class="text-[10px] text-text-muted uppercase tracking-wide mb-0.5">Success</div>
                  <div class="text-xl font-mono font-bold text-status-success">
                    {{ calculateSuccessRate(stats) }}%
                  </div>
                </div>
                <div>
                  <div class="text-[10px] text-text-muted uppercase tracking-wide mb-0.5">Failed</div>
                  <div class="text-xl font-mono font-bold text-status-error">
                    {{ stats.failed }}
                  </div>
                </div>
                <div>
                  <div class="text-[10px] text-text-muted uppercase tracking-wide mb-0.5">Avg Time</div>
                  <div class="text-xl font-mono font-bold text-text-primary">
                    {{ formatRuntime(stats.avg_runtime) }}
                  </div>
                </div>
              </div>
              <div v-else class="h-24 bg-background-base animate-pulse rounded"></div>
            </div>

            <!-- 7D Trend -->
            <div class="bg-background-surface border border-border rounded-lg p-3">
              <div class="text-[10px] font-mono font-bold text-text-muted uppercase tracking-wider mb-3">
                7-Day Trend
              </div>
              <div v-if="trend" class="space-y-2">
                <div>
                  <div class="text-[10px] text-text-muted uppercase tracking-wide mb-0.5">Total Exec</div>
                  <div class="text-xl font-mono font-bold text-text-primary">{{ trend.total_executions }}</div>
                </div>
                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <div class="text-[10px] text-text-muted uppercase tracking-wide mb-0.5">Avg Success</div>
                    <div class="text-lg font-mono font-bold text-status-success">{{ trend.avg_success_rate }}%</div>
                  </div>
                  <div>
                    <div class="text-[10px] text-text-muted uppercase tracking-wide mb-0.5">Avg Time</div>
                    <div class="text-lg font-mono font-bold text-text-primary">{{ formatRuntime(trend.avg_runtime) }}</div>
                  </div>
                </div>
              </div>
              <div v-else class="h-24 bg-background-base animate-pulse rounded"></div>
            </div>
          </div>

          <!-- Failures Section (Compact) -->
          <div v-if="failures && failures.length > 0"
               class="bg-red-950/10 border border-red-900/30 rounded-lg p-2.5">
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center gap-1.5">
                <AlertTriangle class="h-3.5 w-3.5 text-red-400" />
                <h3 class="text-[10px] font-mono font-bold text-red-400 uppercase tracking-wider">
                  Failures (24H)
                </h3>
                <Badge variant="destructive" class="text-[10px] px-1 py-0">{{ failures.length }}</Badge>
              </div>
              <button
                @click="failuresExpanded = !failuresExpanded"
                class="text-[10px] text-red-400 hover:text-red-300 transition-colors font-mono"
              >
                {{ failuresExpanded ? 'Hide' : 'Show' }}
              </button>
            </div>

            <!-- Collapsed: Show only count and last error -->
            <div v-if="!failuresExpanded" class="text-[11px] text-red-400/80 font-mono">
              Last: {{ new Date(failures[0].timestamp).toLocaleTimeString() }}
            </div>

            <!-- Expanded: Show failure cards -->
            <div v-else class="space-y-1.5">
              <FailureCard
                v-for="(failure, idx) in (showAllFailures ? failures : failures.slice(0, 3))"
                :key="failure.task_id"
                :failure="failure"
                @retry="handleRetryFailure"
              />

              <button
                v-if="failures.length > 3 && !showAllFailures"
                @click="showAllFailures = true"
                class="w-full py-1.5 text-[10px] text-red-400 hover:text-red-300 border border-red-900/30 rounded hover:bg-red-950/20 transition-colors font-mono"
              >
                Show {{ failures.length - 3 }} more →
              </button>
            </div>
          </div>

          <!-- Frequency Timeline -->
          <div class="bg-background-surface border border-border rounded-lg p-3">
            <div class="text-[10px] font-mono font-bold text-text-muted uppercase tracking-wider mb-3">
              24H Frequency
            </div>
            <TaskFrequencyTimeline
              v-if="timeline && timeline.buckets"
              :buckets="timeline.buckets"
            />
            <div v-else class="h-16 bg-background-base animate-pulse rounded"></div>
          </div>

          <!-- Metadata -->
          <div class="bg-background-surface border border-border rounded-lg p-3">
            <div class="text-[10px] font-mono font-bold text-text-muted uppercase tracking-wider mb-2">
              Metadata
            </div>
            <div class="space-y-1.5 text-xs font-mono">
              <div class="flex justify-between items-center py-1">
                <span class="text-text-muted">Task Name</span>
                <span class="text-text-primary font-medium">{{ task.name }}</span>
              </div>
              <div class="flex justify-between items-center py-1 border-t border-border-subtle">
                <span class="text-text-muted">First Seen</span>
                <span class="text-text-secondary">{{ formatDate(task.first_seen) }}</span>
              </div>
              <div class="flex justify-between items-center py-1 border-t border-border-subtle">
                <span class="text-text-muted">Last Seen</span>
                <span class="text-text-secondary">{{ formatDate(task.last_seen) }}</span>
              </div>
              <div class="flex justify-between items-center py-1 border-t border-border-subtle">
                <span class="text-text-muted">Updated</span>
                <span class="text-text-secondary">{{ formatDate(task.updated_at) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </SheetContent>
  </Sheet>

  <!-- Retry Confirmation Dialog -->
  <RetryTaskConfirmDialog
    ref="retryDialogRef"
    :task="currentRetryTaskId ? failures.find(f => f.task_id === currentRetryTaskId) || null : null"
    :is-loading="isRetrying && !!currentRetryTaskId"
    @confirm="handleRetryConfirm"
    @cancel="handleRetryCancel"
  />
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { Pencil, AlertTriangle } from 'lucide-vue-next'
import { Sheet, SheetContent } from '~/components/ui/sheet'
import TaskFrequencyTimeline from './TaskFrequencyTimeline.vue'
import { BaseTag } from '~/components/ui/tag'
import { Badge } from '~/components/ui/badge'
import BaseIconButton from '~/components/BaseIconButton.vue'
import FailureCard from '~/components/FailureCard.vue'
import RetryTaskConfirmDialog from '~/components/RetryTaskConfirmDialog.vue'
import type { TaskRegistryResponse, TaskRegistryStats, TaskTimelineResponse, TaskRegistryUpdate, TaskEventResponse } from '~/services/apiClient'

interface Props {
  isOpen: boolean
  task: TaskRegistryResponse | null
}

const props = defineProps<Props>()
const emit = defineEmits(['close', 'update'])

const taskRegistryStore = useTaskRegistryStore()
const tasksStore = useTasksStore()
const { useApiService } = await import('~/services/apiClient')
const apiService = useApiService()

const stats = ref<TaskRegistryStats | null>(null)
const timeline = ref<TaskTimelineResponse | null>(null)
const trend = ref<any | null>(null)
const failures = ref<TaskEventResponse[]>([])
const failuresExpanded = ref(true)
const showAllFailures = ref(false)

// Retry dialog state
const currentRetryTaskId = ref<string | null>(null)
const retryDialogRef = ref<InstanceType<typeof RetryTaskConfirmDialog> | null>(null)
const isRetrying = computed(() => tasksStore.isLoading)

// Edit mode state
const isEditing = ref(false)
const isSaving = ref(false)
const newTag = ref('')
const editForm = ref<TaskRegistryUpdate>({
  human_readable_name: null,
  description: null,
  tags: null
})

// Load data when task changes
watch(() => props.task, async (newTask) => {
  if (newTask) {
    await loadTaskData(newTask)
  }
}, { immediate: true })

// Reload data when environment changes
const environmentStore = useEnvironmentStore()
watch(() => environmentStore.activeEnvironment, async () => {
  if (props.task) {
    await loadTaskData(props.task)
  }
})

async function loadTaskData(task: TaskRegistryResponse) {
  stats.value = null
  timeline.value = null
  trend.value = null
  failures.value = []
  isEditing.value = false
  failuresExpanded.value = true
  showAllFailures.value = false

  const [statsData, timelineData, trendData, failuresData] = await Promise.all([
    taskRegistryStore.fetchTaskStats(task.name, 24),
    taskRegistryStore.fetchTaskTimeline(task.name, 24, 60),
    taskRegistryStore.fetchTrend(task.name, 7),
    apiService.getTaskFailures(task.name, 24, 10)
  ])

  stats.value = statsData
  timeline.value = timelineData
  trend.value = trendData
  failures.value = failuresData
}

function handleClose() {
  isEditing.value = false
  emit('close')
}

function startEdit() {
  if (!props.task) return

  isEditing.value = true
  editForm.value = {
    human_readable_name: props.task.human_readable_name || '',
    description: props.task.description || '',
    tags: [...(props.task.tags || [])]
  }
}

function cancelEdit() {
  isEditing.value = false
  newTag.value = ''
}

function addTag() {
  const tag = newTag.value.trim()
  if (tag && editForm.value.tags && !editForm.value.tags.includes(tag)) {
    editForm.value.tags.push(tag)
    newTag.value = ''
  }
}

function removeTag(index: number) {
  if (editForm.value.tags) {
    editForm.value.tags.splice(index, 1)
  }
}

async function saveChanges() {
  if (!props.task || isSaving.value) return

  isSaving.value = true
  try {
    const updated = await taskRegistryStore.updateTask(props.task.name, editForm.value)
    if (updated) {
      // Emit event to parent to update the task prop
      emit('update', updated)
      isEditing.value = false
      newTag.value = ''
    }
  } catch (error) {
    console.error('Failed to save changes:', error)
  } finally {
    isSaving.value = false
  }
}

function calculateSuccessRate(stats: TaskRegistryStats) {
  if (!stats || stats.total_executions === 0) return 0
  return Math.round((stats.succeeded / stats.total_executions) * 100)
}

function formatRuntime(runtime: number | null | undefined) {
  if (!runtime) return '-'
  if (runtime < 1) return `${Math.round(runtime * 1000)}ms`
  return `${runtime.toFixed(2)}s`
}

function formatDate(dateStr: string) {
  const date = new Date(dateStr)
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function handleRetryFailure(taskId: string) {
  currentRetryTaskId.value = taskId
  retryDialogRef.value?.open()
}

async function handleRetryConfirm() {
  if (!currentRetryTaskId.value) return

  try {
    await tasksStore.retryTask(currentRetryTaskId.value)
    currentRetryTaskId.value = null
  } catch (error) {
    console.error('Failed to retry task:', error)
    currentRetryTaskId.value = null
  }
}

function handleRetryCancel() {
  currentRetryTaskId.value = null
}
</script>
