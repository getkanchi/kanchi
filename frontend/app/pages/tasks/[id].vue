<template>
  <div v-if="task" class="max-w-7xl mx-auto">
    <!-- Header -->
    <div class="mb-10">
      <NuxtLink to="/">
        <Button
          variant="ghost"
          size="sm"
          class="mb-4 -ml-2"
        >
          <ChevronLeft class="h-4 w-4 mr-1" />
          Back to Dashboard
        </Button>
      </NuxtLink>

      <div class="flex items-start justify-between gap-4">
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-3 mb-2">
            <h1 class="text-xl font-semibold text-text-primary">
              {{ task.task_name }}
            </h1>
            <Badge :variant="statusVariant" class="text-xs">
              {{ statusDisplay }}
            </Badge>
          </div>
          <div class="flex items-center gap-2">
            <UuidDisplay
              :uuid="task.task_id"
              :show-copy="true"
              :truncate-length="36"
              size="sm"
            />
          </div>
        </div>

        <div class="flex items-center gap-2">
          <Button
            @click="handleTaskIdUrlCopy"
            variant="outline"
            size="sm"
          >
            <Transition
              mode="out-in"
              enter-active-class="transition duration-150 ease-out"
              enter-from-class="opacity-0 scale-90"
              enter-to-class="opacity-100 scale-100"
              leave-active-class="transition duration-150 ease-in"
              leave-from-class="opacity-100 scale-100"
              leave-to-class="opacity-0 scale-90"
            >
              <Check v-if="isTaskUrlCopied" key="copied" class="h-4 w-4 text-green-400" />
              <CopyIcon v-else key="copy" class="h-4 w-4" />
            </Transition>
            <span class="ml-1.5">
              {{ isTaskUrlCopied ? 'Copied' : 'Copy URL' }}
            </span>

          </Button>
          <Button
            variant="outline"
            size="sm"
            :loading="isRetrying"
            :disabled="isRetrying || !task"
            @click="openRetryDialog"
          >
            <RefreshCw class="h-4 w-4" />
            Rerun
          </Button>
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
            <TabsTrigger value="timeline">Timeline</TabsTrigger>
            <TabsTrigger value="data">Data</TabsTrigger>
          </TabsList>

          <!-- Overview Tab -->
          <TabsContent value="overview">
            <div class="space-y-6">
              <!-- Task Information -->
              <div class="border border-border-subtle rounded-md p-5">
                <h2 class="text-sm font-medium text-text-primary mb-4">Task Information</h2>

                <div class="space-y-3 text-xs">
                  <div class="flex justify-between py-2 border-b border-border">
                    <span class="text-text-muted">Status</span>
                    <Badge :variant="statusVariant" class="text-xs">
                      {{ statusDisplay }}
                    </Badge>
                  </div>
                  <div v-if="task.hostname" class="flex justify-between py-2 border-b border-border">
                    <span class="text-text-muted">Worker</span>
                    <code class="text-text-primary font-mono">{{ task.hostname }}</code>
                  </div>
                  <div class="flex justify-between py-2 border-b border-border">
                    <span class="text-text-muted">Queue</span>
                    <code class="text-text-primary font-mono">{{ task.routing_key || 'default' }}</code>
                  </div>
                  <div v-if="task.exchange" class="flex justify-between py-2 border-b border-border">
                    <span class="text-text-muted">Exchange</span>
                    <code class="text-text-primary font-mono">{{ task.exchange }}</code>
                  </div>
                  <div class="flex justify-between py-2 border-b border-border">
                    <span class="text-text-muted">Timestamp</span>
                    <TimeDisplay :timestamp="task.timestamp" layout="inline" />
                  </div>
                  <div v-if="task.runtime" class="flex justify-between py-2 border-b border-border">
                    <span class="text-text-muted">Runtime</span>
                    <span class="text-text-primary font-mono tabular-nums">{{ task.runtime.toFixed(3) }}s</span>
                  </div>
                  <div class="flex justify-between py-2 border-b border-border">
                    <span class="text-text-muted">Retries</span>
                    <Badge v-if="task.retries > 0" variant="retry" class="text-xs">
                      {{ task.retries }}
                    </Badge>
                    <span v-else class="text-text-primary font-medium tabular-nums">
                      {{ task.retries }}
                    </span>
                  </div>
                  <div v-if="task.eta" class="flex justify-between py-2 border-b border-border">
                    <span class="text-text-muted">ETA</span>
                    <span class="text-text-primary">{{ task.eta }}</span>
                  </div>
                  <div v-if="task.expires" class="flex justify-between py-2 border-b border-border">
                    <span class="text-text-muted">Expires</span>
                    <span class="text-text-primary">{{ task.expires }}</span>
                  </div>
                </div>
              </div>

              <!-- Exception/Traceback -->
              <div v-if="task.exception || task.traceback" class="border border-status-error-border rounded-md p-5 bg-status-error-bg/20">
                <h2 class="text-sm font-medium text-status-error mb-4">Error Details</h2>

                <div v-if="task.exception" class="mb-4">
                  <div class="text-[10px] uppercase tracking-wider font-medium text-text-muted mb-2">Exception</div>
                  <pre class="text-xs font-mono bg-background-base border border-border-subtle rounded p-3 overflow-x-auto text-status-error">{{ task.exception }}</pre>
                </div>

                <div v-if="task.traceback">
                  <div class="text-[10px] uppercase tracking-wider font-medium text-text-muted mb-2">Traceback</div>
                  <pre class="text-xs font-mono bg-background-base border border-border-subtle rounded p-3 overflow-x-auto text-text-muted whitespace-pre-wrap">{{ task.traceback }}</pre>
                </div>
              </div>

              <!-- Retry Information -->
              <div v-if="task.is_retry || task.has_retries" class="border border-status-retry-border rounded-md p-5 bg-status-retry-bg/20">
                <h2 class="text-sm font-medium text-status-retry mb-4">Retry Information</h2>

                <div class="space-y-3 text-xs">
                  <div v-if="task.is_retry" class="flex justify-between py-2 border-b border-border">
                    <span class="text-text-muted">Is Retry</span>
                    <Badge variant="retry" class="text-xs">Yes</Badge>
                  </div>
                  <div class="flex justify-between py-2 border-b border-border">
                    <span class="text-text-muted">Retry Count</span>
                    <span class="text-text-primary font-medium tabular-nums">{{ task.retry_count }}</span>
                  </div>
                  <div v-if="task.retry_of" class="py-2">
                    <div class="text-text-muted mb-2">Retry Of</div>
                    <NuxtLink :to="`/tasks/${task.retry_of.task_id}`" class="text-xs font-mono text-primary hover:text-primary-hover">
                      {{ task.retry_of.task_id }}
                    </NuxtLink>
                  </div>
                </div>
              </div>

              <!-- Orphan Information -->
              <div v-if="task.is_orphan" class="border border-status-special-border rounded-md p-5 bg-status-special-bg/20">
                <h2 class="text-sm font-medium text-status-special mb-4">Orphan Information</h2>

                <div class="space-y-3 text-xs">
                  <div class="flex justify-between py-2 border-b border-border/50">
                    <span class="text-text-muted">Is Orphan</span>
                    <Badge variant="orphaned" class="text-xs">Yes</Badge>
                  </div>
                  <div v-if="task.orphaned_at" class="flex justify-between py-2">
                    <span class="text-text-muted">Orphaned At</span>
                    <TimeDisplay :timestamp="task.orphaned_at" layout="inline" />
                  </div>
                </div>
              </div>

              <!-- Related Tasks -->
              <div v-if="task.root_id || task.parent_id" class="border border-border-subtle rounded-md p-5">
                <h2 class="text-sm font-medium text-text-primary mb-4">Related Tasks</h2>

                <div class="space-y-3 text-xs">
                  <div v-if="task.root_id" class="py-2 border-b border-border">
                    <div class="text-text-muted mb-2">Root Task</div>
                    <NuxtLink :to="`/tasks/${task.root_id}`" class="text-xs font-mono text-primary hover:text-primary-hover">
                      {{ task.root_id }}
                    </NuxtLink>
                  </div>
                  <div v-if="task.parent_id" class="py-2">
                    <div class="text-text-muted mb-2">Parent Task</div>
                    <NuxtLink :to="`/tasks/${task.parent_id}`" class="text-xs font-mono text-primary hover:text-primary-hover">
                      {{ task.parent_id }}
                    </NuxtLink>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>

          <!-- Timeline Tab -->
          <TabsContent value="timeline">
            <div class="border border-border-subtle rounded-md p-5">
              <h2 class="text-sm font-medium text-text-primary mb-4">Event Timeline</h2>

              <div v-if="allEvents.length > 0" class="space-y-4">
                <div
                  v-for="(event, idx) in allEvents"
                  :key="idx"
                  class="flex gap-4 pb-4"
                  :class="{ 'border-b border-border': idx < allEvents.length - 1 }"
                >
                  <div class="flex flex-col items-center">
                    <div class="w-2 h-2 rounded-full bg-primary mt-1.5" />
                    <div v-if="idx < allEvents.length - 1" class="w-px h-full bg-border mt-1" />
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 mb-1">
                      <Badge :variant="getEventVariant(event.event_type)" class="text-xs">
                        {{ formatEventType(event.event_type) }}
                      </Badge>
                      <TimeDisplay :timestamp="event.timestamp" layout="inline" class="text-xs" />
                    </div>
                    <div v-if="event.hostname" class="text-xs text-text-muted">
                      Worker: <code class="font-mono">{{ event.hostname }}</code>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="text-center py-8 text-text-muted text-sm">
                No events found
              </div>
            </div>
          </TabsContent>

          <!-- Data Tab -->
          <TabsContent value="data">
            <div class="space-y-6">
              <!-- Arguments -->
              <div class="border border-border-subtle rounded-md p-5">
                <h2 class="text-sm font-medium text-text-primary mb-4">Arguments</h2>
                <PayloadTruncationNotice
                  :value="task.args"
                  title="Arguments truncated before reaching Kanchi"
                />
                <pre class="text-xs font-mono bg-background-base border border-border-subtle rounded p-3 overflow-x-auto text-text-primary">{{ formatJson(task.args) }}</pre>
              </div>

              <!-- Keyword Arguments -->
              <div class="border border-border-subtle rounded-md p-5">
                <h2 class="text-sm font-medium text-text-primary mb-4">Keyword Arguments</h2>
                <PayloadTruncationNotice
                  :value="task.kwargs"
                  title="Keyword arguments truncated before reaching Kanchi"
                />
                <pre class="text-xs font-mono bg-background-base border border-border-subtle rounded p-3 overflow-x-auto text-text-primary">{{ formatJson(task.kwargs) }}</pre>
              </div>

              <!-- Result -->
              <div v-if="task.result !== null && task.result !== undefined" class="border border-border-subtle rounded-md p-5">
                <h2 class="text-sm font-medium text-text-primary mb-4">Result</h2>
                <PayloadTruncationNotice
                  :value="task.result"
                  title="Result truncated before reaching Kanchi"
                />
                <pre class="text-xs font-mono bg-background-base border border-border-subtle rounded p-3 overflow-x-auto text-text-primary">{{ formatJson(task.result) }}</pre>
              </div>

              <!-- Raw Task Data -->
              <div class="border border-border-subtle rounded-md p-5">
                <h2 class="text-sm font-medium text-text-primary mb-4">Raw Task Data</h2>
                <p class="text-xs text-text-muted mb-2">
                  This is the internal representation of the task, not the original Celery task payload.
                </p>
                <pre class="text-xs font-mono bg-background-base border border-border rounded p-3 overflow-x-auto text-text-muted">{{ formatJson(task) }}</pre>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </main>

      <!-- Stats Rail (Right Sidebar) -->
      <aside class="w-full lg:w-64 lg:sticky lg:top-6 lg:self-start">
        <div class="space-y-3">
          <div class="border border-border-subtle rounded-md px-4 py-3.5 hover:border-border transition-colors">
            <p class="text-[10px] uppercase tracking-wider text-text-muted mb-1.5 font-medium">Status</p>
            <Badge :variant="statusVariant">{{ statusDisplay }}</Badge>
          </div>

          <div v-if="task.runtime" class="border border-border-subtle rounded-md px-4 py-3.5 hover:border-border transition-colors">
            <p class="text-[10px] uppercase tracking-wider text-text-muted mb-1.5 font-medium">Runtime</p>
            <p class="text-2xl font-semibold text-text-primary tabular-nums">
              {{ task.runtime.toFixed(2) }}<span class="text-sm text-text-muted">s</span>
            </p>
          </div>

          <div class="border border-border-subtle rounded-md px-4 py-3.5 hover:border-border transition-colors">
            <p class="text-[10px] uppercase tracking-wider text-text-muted mb-1.5 font-medium">Retries</p>
            <p class="text-2xl font-semibold tabular-nums" :class="task.retries > 0 ? 'text-status-retry' : 'text-text-primary'">
              {{ task.retries }}
            </p>
          </div>

          <div class="border border-border-subtle rounded-md px-4 py-3.5 hover:border-border transition-colors">
            <p class="text-[10px] uppercase tracking-wider text-text-muted mb-1.5 font-medium">Events</p>
            <p class="text-2xl font-semibold text-text-primary tabular-nums">
              {{ allEvents.length }}
            </p>
          </div>

          <div v-if="task.is_orphan" class="border border-status-special-border rounded-md px-4 py-3.5 bg-status-special-bg/20">
            <p class="text-[10px] uppercase tracking-wider text-status-special mb-1.5 font-medium">Orphaned</p>
            <p class="text-sm text-status-special">
              Yes
            </p>
          </div>
        </div>
      </aside>

    </div>
  </div>

  <!-- Loading State -->
  <div v-else-if="isLoading" class="max-w-7xl mx-auto">
    <div class="h-48 border border-border-subtle rounded-md animate-pulse" />
  </div>

  <!-- Error State -->
  <div v-else-if="error" class="max-w-7xl mx-auto text-center py-24">
    <AlertCircle class="h-10 w-10 text-status-error mx-auto mb-3 opacity-40" />
    <h3 class="text-sm font-medium text-text-primary mb-1">Task not found</h3>
    <p class="text-xs text-text-muted mb-6">{{ error }}</p>
    <NuxtLink to="/">
      <Button size="sm">
        Back to Dashboard
      </Button>
    </NuxtLink>
  </div>

  <!-- Retry Confirmation Dialog -->
  <RetryTaskConfirmDialog
    ref="retryDialogRef"
    :task="task"
    :is-loading="isRetrying"
    @confirm="handleRetryConfirm"
  />
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ChevronLeft, AlertCircle, RefreshCw, CopyIcon, Check } from 'lucide-vue-next'
import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs'
import TimeDisplay from '~/components/TimeDisplay.vue'
import UuidDisplay from '~/components/UuidDisplay.vue'
import PayloadTruncationNotice from '~/components/PayloadTruncationNotice.vue'
import RetryTaskConfirmDialog from '~/components/RetryTaskConfirmDialog.vue'
import type { TaskEventResponse } from '~/services/apiClient'
import { useCopy } from '~/composables/useCopy'

const route = useRoute()
const tasksStore = useTasksStore()
const isRetrying = computed(() => tasksStore.isLoading)
const retryDialogRef = ref<InstanceType<typeof RetryTaskConfirmDialog> | null>(null)

const task = ref<TaskEventResponse | null>(null)
const allEvents = ref<TaskEventResponse[]>([])
const isLoading = ref(true)
const error = ref<string | null>(null)

const { eventTypeToStatus, getStatusVariant, formatStatus } = useTaskStatus()

const statusDisplay = computed(() => {
  if (!task.value) return 'Unknown'
  if (task.value.is_orphan) return formatStatus('ORPHANED')
  return formatStatus(eventTypeToStatus(task.value.event_type))
})

const statusVariant = computed(() => {
  if (!task.value) return 'default'
  if (task.value.is_orphan) return 'orphaned'
  return getStatusVariant(eventTypeToStatus(task.value.event_type))
})

const shareUrl = computed(() => {
  if (typeof window === 'undefined') return ''
  return window.location.href
})

const { copyToClipboard, isCopied } = useCopy()
const shareCopyKey = computed(() => task.value?.task_id ? `task-url-${task.value.task_id}` : 'task-url')
const isTaskUrlCopied = computed(() => isCopied(shareCopyKey.value))

function formatJson(data: any): string {
  try {
    return JSON.stringify(data, null, 2)
  } catch (e) {
    return String(data)
  }
}

function formatEventType(eventType: string): string {
  return eventType.replace('task-', '').replace(/-/g, ' ').toUpperCase()
}

function getEventVariant(eventType: string): string {
  const status = eventTypeToStatus(eventType)
  return getStatusVariant(status)
}

async function fetchTaskData() {
  const taskId = route.params.id as string

  if (!taskId) {
    error.value = 'No task ID provided'
    isLoading.value = false
    return
  }

  try {
    isLoading.value = true
    error.value = null

    const events = await tasksStore.getTaskEvents(taskId)

    if (!events || events.length === 0) {
      error.value = 'Task not found'
      return
    }

    allEvents.value = events.sort((a, b) =>
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    )

    task.value = allEvents.value[0]
  } catch (e: any) {
    console.error('Error fetching task:', e)
    error.value = e.message || 'Failed to load task'
  } finally {
    isLoading.value = false
  }
}

onMounted(async () => {
  await fetchTaskData()
})

const openRetryDialog = () => {
  retryDialogRef.value?.open()
}

const handleRetryConfirm = async () => {
  if (!task.value?.task_id) return

  try {
    await tasksStore.retryTask(task.value.task_id)
    await fetchTaskData()
  } catch (error) {
    console.error('Failed to rerun task:', error)
  }
}

const handleTaskIdUrlCopy = async () => {
  if (!shareUrl.value) return
  await copyToClipboard(shareUrl.value, shareCopyKey.value)
}
</script>
