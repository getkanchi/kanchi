<template>
  <div class="mx-auto max-w-5xl space-y-10 py-6 lg:py-8">
    <section class="rounded-3xl border border-border-subtle bg-background-surface px-8 py-10 shadow-sm">
      <p class="text-xs font-semibold uppercase tracking-[0.3em] text-text-secondary">Workspace</p>
      <h1 class="mt-3 text-3xl font-semibold text-text-primary">Workspace settings</h1>
      <p class="mt-4 max-w-2xl text-sm text-text-secondary">
        Configure how Kanchi behaves for everyone in this environment. Update appearance preferences,
        review resources, and manage workflow integrations.
      </p>
    </section>

    <div class="space-y-6">
      <section class="rounded-2xl border border-border-subtle bg-background-surface p-6 shadow-sm">
        <div class="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 class="text-base font-semibold text-text-primary">Appearance</h2>
            <p class="mt-1 text-sm text-text-secondary">
              Toggle between light and dark themes. Theme applies instantly for your browser.
            </p>
          </div>
          <ThemeToggle />
        </div>
      </section>

      <section class="rounded-2xl border border-border-subtle bg-background-surface p-6 shadow-sm">
        <div class="space-y-5">
          <div>
            <h2 class="text-base font-semibold text-text-primary">Data retention</h2>
            <p class="mt-1 max-w-2xl text-sm text-text-secondary">
              Keep successful task history short, and hold onto failed or retried task history longer for audit and retry analysis.
            </p>
          </div>

          <Alert v-if="loadError" variant="destructive">
            <span>{{ loadError }}</span>
          </Alert>

          <div class="grid gap-4 md:grid-cols-2">
            <div v-for="field in retentionFields" :key="field.key" class="space-y-2">
              <Label :for="field.key">{{ field.label }}</Label>
              <Input
                :id="field.key"
                v-model.number="retentionForm[field.key]"
                type="number"
                min="1"
                max="3650"
                :disabled="isSaving || isLoading"
              />
              <p class="text-xs text-text-secondary">{{ field.description }}</p>
            </div>

            <div class="md:col-span-2 flex flex-wrap items-center gap-3 pt-2">
              <button
                type="button"
                class="inline-flex items-center justify-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-sm transition-colors hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
                :disabled="isSaving || isLoading"
                @click="saveRetention"
              >
                {{ isSaving ? 'Saving…' : 'Save retention settings' }}
              </button>
              <button
                type="button"
                class="inline-flex items-center justify-center gap-2 rounded-md border border-border-subtle bg-background-surface px-4 py-2 text-sm font-medium text-text-primary shadow-sm transition-colors hover:bg-background-subtle disabled:cursor-not-allowed disabled:opacity-50"
                :disabled="isSaving || isLoading"
                @click="resetRetentionForm"
              >
                Reset
              </button>
              <span v-if="saveMessage" class="text-sm text-text-secondary">{{ saveMessage }}</span>
            </div>
          </div>

          <div class="rounded-2xl border border-border-subtle/80 bg-background-subtle p-4 space-y-4">
            <div>
              <h3 class="text-sm font-semibold text-text-primary">Cleanup</h3>
              <p class="mt-1 text-sm text-text-secondary">
                Preview what would be removed, then run cleanup when you are ready.
              </p>
              <div class="mt-3 rounded-xl border border-border-subtle bg-background-surface px-4 py-3 text-sm">
                <p class="text-text-primary">
                  <span class="font-medium">Automatic cleanup:</span>
                  {{ retentionSchedule?.enabled ? `every ${retentionSchedule.interval_hours}h` : 'disabled' }}
                </p>
                <div class="mt-2 space-y-2">
                  <div class="flex items-start justify-between gap-4 rounded-lg bg-background-subtle/60 px-3 py-2">
                    <span class="pt-1 text-xs font-medium uppercase tracking-[0.2em] text-text-secondary">Next run</span>
                    <TimeDisplay
                      v-if="retentionSchedule?.next_run_at"
                      :timestamp="retentionSchedule.next_run_at"
                      :refresh-interval="1000"
                    />
                    <span v-else class="text-sm text-text-secondary">Not scheduled yet</span>
                  </div>
                  <div v-if="retentionSchedule?.last_completed_at" class="flex items-start justify-between gap-4 rounded-lg bg-background-subtle/60 px-3 py-2">
                    <span class="pt-1 text-xs font-medium uppercase tracking-[0.2em] text-text-secondary">Last completed</span>
                    <div class="flex flex-col items-end gap-1">
                      <TimeDisplay
                        :timestamp="retentionSchedule.last_completed_at"
                        :refresh-interval="1000"
                      />
                      <span
                        v-if="retentionSchedule.last_deleted_rows !== null && retentionSchedule.last_deleted_rows !== undefined"
                        class="text-xs text-text-secondary"
                      >
                        Deleted {{ retentionSchedule.last_deleted_rows }} rows
                      </span>
                    </div>
                  </div>
                </div>
                <p v-if="retentionSchedule?.last_error" class="mt-1 text-red-400">
                  Last scheduler error: {{ retentionSchedule.last_error }}
                </p>
              </div>
            </div>

            <div class="flex flex-wrap items-center gap-3">
              <button
                type="button"
                class="inline-flex items-center justify-center gap-2 rounded-md border border-border-subtle bg-background-surface px-4 py-2 text-sm font-medium text-text-primary shadow-sm transition-colors hover:bg-background-subtle disabled:cursor-not-allowed disabled:opacity-50"
                :disabled="cleanupRunning"
                @click="previewCleanup"
              >
                {{ cleanupRunning && cleanupMode === 'dry' ? 'Running preview…' : 'Preview cleanup' }}
              </button>
              <button
                type="button"
                class="inline-flex items-center justify-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-sm transition-colors hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
                :disabled="cleanupRunning"
                @click="showCleanupConfirm = true"
              >
                {{ cleanupRunning && cleanupMode === 'live' ? 'Running cleanup…' : 'Run cleanup now' }}
              </button>
            </div>

            <Alert v-if="cleanupError" variant="destructive">
              <span>{{ cleanupError }}</span>
            </Alert>

            <div v-if="cleanupResult" class="space-y-3">
              <p class="text-sm text-text-primary">
                {{ cleanupResult.dry_run ? 'Preview' : 'Cleanup complete' }} — {{ cleanupResult.total_deleted }} rows
                {{ cleanupResult.dry_run ? 'would be removed' : 'removed' }}.
              </p>
              <div class="overflow-x-auto">
                <table class="min-w-full text-sm">
                  <thead>
                    <tr class="border-b border-border-subtle text-left text-text-secondary">
                      <th class="py-2 pr-4 font-medium">Target</th>
                      <th class="py-2 pr-4 font-medium">Days</th>
                      <th class="py-2 font-medium">Rows</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="result in cleanupResult.results" :key="result.key" class="border-b border-border-subtle/60 last:border-0">
                      <td class="py-2 pr-4 text-text-primary">{{ result.label }}</td>
                      <td class="py-2 pr-4 text-text-secondary">{{ result.retention_days }}</td>
                      <td class="py-2 text-text-secondary">{{ result.deleted }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div v-if="showCleanupConfirm" class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4">
        <div
          class="grid w-full max-w-md gap-4 rounded-lg border border-border-subtle bg-background-surface p-6 shadow-lg"
          role="dialog"
          aria-modal="true"
          aria-labelledby="retention-cleanup-title"
          aria-describedby="retention-cleanup-description"
        >
          <div class="space-y-2">
            <h2 id="retention-cleanup-title" class="text-lg font-semibold text-text-primary">Run retention cleanup?</h2>
            <p id="retention-cleanup-description" class="text-sm text-text-secondary">
              This will permanently delete data that falls outside the configured retention windows. Preview cleanup first if you want to inspect the impact before deleting anything.
            </p>
          </div>
          <div class="flex flex-col-reverse sm:flex-row sm:justify-end sm:gap-2">
            <button
              type="button"
              class="mt-2 inline-flex items-center justify-center gap-2 rounded-md border border-border-subtle bg-background-surface px-4 py-2 text-sm font-medium text-text-primary shadow-sm transition-colors hover:bg-background-subtle disabled:cursor-not-allowed disabled:opacity-50 sm:mt-0"
              :disabled="cleanupRunning"
              @click="showCleanupConfirm = false"
            >
              Cancel
            </button>
            <button
              type="button"
              class="inline-flex items-center justify-center gap-2 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-red-500 disabled:cursor-not-allowed disabled:opacity-50"
              :disabled="cleanupRunning"
              @click="confirmCleanupRun"
            >
              {{ cleanupRunning && cleanupMode === 'live' ? 'Running cleanup…' : 'Run cleanup' }}
            </button>
          </div>
        </div>
      </div>

      <section class="rounded-2xl border border-border-subtle bg-background-surface p-6 shadow-sm">
        <div class="space-y-4">
          <div>
            <h2 class="text-base font-semibold text-text-primary">Resources</h2>
            <p class="mt-1 text-sm text-text-secondary">Stay aligned with releases and contribute to Kanchi.</p>
          </div>
          <div class="grid gap-3 sm:grid-cols-2">
            <Button
              as="a"
              href="https://github.com/getkanchi/kanchi"
              target="_blank"
              rel="noreferrer"
              variant="outline"
              class="justify-start gap-3"
            >
              <Github class="h-4 w-4" />
              View on GitHub
              <ArrowUpRight class="ml-auto h-3.5 w-3.5 text-text-muted" />
            </Button>
            <Button
              as="a"
              href="https://kanchi.io/changelog"
              target="_blank"
              rel="noreferrer"
              variant="outline"
              class="justify-start gap-3"
            >
              <Sparkles class="h-4 w-4" />
              Changelog
              <ArrowUpRight class="ml-auto h-3.5 w-3.5 text-text-muted" />
            </Button>
          </div>
        </div>
      </section>

      <section class="rounded-2xl border border-border-subtle bg-background-surface p-6 shadow-sm">
        <div class="mb-6">
          <h2 class="text-base font-semibold text-text-primary">Slack webhooks</h2>
          <p class="mt-1 text-sm text-text-secondary">
            Configure reusable Slack webhook destinations for workflow notifications and alerts.
          </p>
        </div>
        <WorkflowSlackConfigPanel :active="true" :enable-selection="false" />
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ArrowUpRight, Github, Sparkles } from 'lucide-vue-next'
import { computed, onMounted, ref } from 'vue'
import Alert from '~/components/alert/Alert.vue'
import ThemeToggle from '~/components/ThemeToggle.vue'
import TimeDisplay from '~/components/TimeDisplay.vue'
import WorkflowSlackConfigPanel from '~/components/workflows/WorkflowSlackConfigPanel.vue'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { useConfigStore } from '~/stores/config'
import type { DataRetentionConfigDTO, RetentionCleanupResponseDTO, RetentionScheduleStatusDTO } from '~/services/apiClient'

const configStore = useConfigStore()

const retentionFields: Array<{ key: keyof DataRetentionConfigDTO; label: string; description: string }> = [
  {
    key: 'task_successful_days',
    label: 'Successful tasks',
    description: 'How long to keep successful task snapshots, events, progress, and steps.',
  },
  {
    key: 'task_unsuccessful_days',
    label: 'Unsuccessful tasks',
    description: 'How long to keep failed, retried, revoked, or orphaned task history.',
  },
  {
    key: 'worker_events_days',
    label: 'Worker events',
    description: 'How long to keep worker lifecycle and status events.',
  },
  {
    key: 'workflow_executions_days',
    label: 'Workflow executions',
    description: 'How long to keep workflow execution records.',
  },
  {
    key: 'task_daily_stats_days',
    label: 'Daily task stats',
    description: 'How long to keep aggregated daily task statistics.',
  },
  {
    key: 'inactive_sessions_days',
    label: 'Inactive sessions',
    description: 'How long to keep inactive anonymous sessions before cleanup.',
  },
]

const retentionForm = ref<DataRetentionConfigDTO>({
  task_successful_days: 14,
  task_unsuccessful_days: 30,
  worker_events_days: 30,
  workflow_executions_days: 30,
  task_daily_stats_days: 365,
  inactive_sessions_days: 30,
})
const isSaving = ref(false)
const saveMessage = ref('')
const cleanupRunning = ref(false)
const cleanupMode = ref<'dry' | 'live' | null>(null)
const cleanupResult = ref<RetentionCleanupResponseDTO | null>(null)
const cleanupError = ref('')
const showCleanupConfirm = ref(false)
const retentionSchedule = ref<RetentionScheduleStatusDTO | null>(null)

const isLoading = computed(() => configStore.isLoading)
const loadError = computed(() => configStore.error)

function syncFormFromStore() {
  retentionForm.value = { ...configStore.dataRetention }
}

async function refreshRetentionSchedule() {
  retentionSchedule.value = await configStore.getRetentionSchedule()
}

function resetRetentionForm() {
  syncFormFromStore()
  saveMessage.value = ''
}

async function saveRetention() {
  try {
    isSaving.value = true
    saveMessage.value = ''
    await configStore.updateDataRetention(retentionForm.value)
    saveMessage.value = 'Retention settings saved.'
  } catch (err) {
    saveMessage.value = err instanceof Error ? err.message : 'Failed to save retention settings.'
  } finally {
    isSaving.value = false
  }
}

async function executeCleanup(dryRun: boolean) {
  try {
    cleanupRunning.value = true
    cleanupMode.value = dryRun ? 'dry' : 'live'
    cleanupError.value = ''
    cleanupResult.value = await configStore.runRetentionCleanup(dryRun)
    await refreshRetentionSchedule()
  } catch (err) {
    cleanupError.value = err instanceof Error ? err.message : 'Cleanup request failed.'
  } finally {
    cleanupRunning.value = false
  }
}

async function previewCleanup() {
  await executeCleanup(true)
}

async function runCleanup() {
  await executeCleanup(false)
}

async function confirmCleanupRun() {
  showCleanupConfirm.value = false
  await runCleanup()
}

onMounted(async () => {
  if (!configStore.config) {
    await configStore.fetchConfig()
  }
  syncFormFromStore()
  await refreshRetentionSchedule()
})

definePageMeta({
  middleware: [],
})
</script>
