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

          <form class="grid gap-4 md:grid-cols-3" @submit.prevent="saveRetention">
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

            <div class="md:col-span-3 grid gap-4 border-t border-border-subtle pt-4 md:grid-cols-3">
              <label
                for="automatic-cleanup"
                class="flex items-center gap-3 text-sm text-text-primary"
              >
                <input
                  id="automatic-cleanup"
                  v-model="scheduleEnabled"
                  type="checkbox"
                  class="h-4 w-4 rounded border-border-subtle text-brand-primary focus:ring-brand-primary"
                  :disabled="isSaving || isLoading"
                />
                Automatic cleanup
              </label>
              <div class="space-y-2">
                <Label for="cleanup-frequency">Frequency</Label>
                <select
                  id="cleanup-frequency"
                  v-model="scheduleForm.frequency"
                  class="w-full rounded-lg border border-border-subtle bg-background-surface px-3 py-2 text-sm text-text-primary focus:border-brand-primary focus:outline-none focus:ring-2 focus:ring-brand-primary/20"
                  :disabled="isSaving || isLoading || !scheduleEnabled"
                >
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                </select>
              </div>
              <div class="space-y-2">
                <Label for="cleanup-run-at">Run time (UTC)</Label>
                <Input
                  id="cleanup-run-at"
                  v-model="scheduleForm.run_at"
                  type="time"
                  :disabled="isSaving || isLoading || !scheduleEnabled"
                />
              </div>
            </div>

            <div class="md:col-span-3 flex flex-wrap items-center gap-3 pt-2">
              <Button type="submit" :disabled="isSaving || isLoading">
                {{ isSaving ? 'Saving…' : 'Save retention settings' }}
              </Button>
              <Button type="button" variant="outline" :disabled="isSaving || isLoading" @click="resetRetentionForm">
                Reset
              </Button>
              <span v-if="saveMessage" :class="['text-sm', saveStatus === 'error' ? 'text-red-500' : 'text-text-secondary']">{{ saveMessage }}</span>
            </div>
          </form>

          <div class="rounded-2xl border border-border-subtle/80 bg-background-subtle p-4 space-y-4">
            <div>
              <h3 class="text-sm font-semibold text-text-primary">Cleanup</h3>
              <p class="mt-1 text-sm text-text-secondary">
                Preview cleanup using the persisted backend policy, then run cleanup when you are ready.
              </p>
              <p class="mt-2 text-xs text-text-secondary">
                Last automatic cleanup: {{ retentionLastRunSummary }}
              </p>
            </div>

            <div class="flex flex-wrap items-center gap-3">
              <Button variant="outline" :disabled="cleanupRunning || hasUnsavedChanges" @click="previewCleanup">
                {{ cleanupRunning && cleanupMode === 'dry' ? 'Running preview…' : 'Preview cleanup' }}
              </Button>
              <ConfirmationDialog
                title="Run retention cleanup?"
                description="This will permanently delete data that falls outside the configured retention windows. Preview cleanup first if you want to inspect the impact before deleting anything."
                confirm-text="Run cleanup"
                cancel-text="Cancel"
                variant="destructive"
                :is-loading="cleanupRunning && cleanupMode === 'live'"
                @confirm="runCleanup"
              >
                <template #trigger>
                  <Button :disabled="cleanupRunning || hasUnsavedChanges">
                    {{ cleanupRunning && cleanupMode === 'live' ? 'Running cleanup…' : 'Run cleanup now' }}
                  </Button>
                </template>
              </ConfirmationDialog>
              <span v-if="hasUnsavedChanges" class="text-sm text-text-secondary">Save changes before previewing cleanup.</span>
            </div>

            <Alert v-if="cleanupError" variant="destructive">
              <span>{{ cleanupError }}</span>
            </Alert>

            <div v-if="cleanupResult" class="space-y-3">
              <p class="text-sm text-text-primary">
                {{ cleanupResult.dry_run ? 'Preview' : 'Cleanup complete' }} — {{ cleanupResult.total_deleted }} rows
                {{ cleanupResult.dry_run ? 'would be removed' : 'removed' }}.
              </p>
              <p class="text-xs text-text-secondary">
                Backend policy used: successful task history {{ cleanupResult.policy.task_successful_days }} days,
                failed task history {{ cleanupResult.policy.task_unsuccessful_days }} days,
                operational logs {{ cleanupResult.policy.worker_events_days }} days.
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
import { computed, onMounted, reactive, ref } from 'vue'
import Alert from '~/components/alert/Alert.vue'
import ConfirmationDialog from '~/components/ConfirmationDialog.vue'
import ThemeToggle from '~/components/ThemeToggle.vue'
import WorkflowSlackConfigPanel from '~/components/workflows/WorkflowSlackConfigPanel.vue'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { useConfigStore } from '~/stores/config'
import type { DataRetentionConfigDTO, RetentionCleanupResponseDTO, RetentionScheduleConfigDTO } from '~/services/apiClient'

const configStore = useConfigStore()

const retentionFields: Array<{ key: keyof DataRetentionConfigDTO; label: string; description: string }> = [
  {
    key: 'task_successful_days',
    label: 'Successful task history',
    description: 'How long to keep successful task snapshots, events, progress, and steps.',
  },
  {
    key: 'task_unsuccessful_days',
    label: 'Failed task history',
    description: 'How long to keep failed, retried, revoked, or orphaned task history.',
  },
  {
    key: 'worker_events_days',
    label: 'Operational logs',
    description: 'How long to keep worker events and workflow execution records.',
  },
]

const retentionForm = reactive<DataRetentionConfigDTO>({
  task_successful_days: 14,
  task_unsuccessful_days: 30,
  worker_events_days: 30,
  workflow_executions_days: 30,
  task_daily_stats_days: 365,
  inactive_sessions_days: 30,
})
const scheduleForm = reactive<RetentionScheduleConfigDTO>({
  enabled: false,
  frequency: 'daily',
  run_at: '03:00',
})
const scheduleEnabled = ref(false)
const isSaving = ref(false)
const saveMessage = ref('')
const saveStatus = ref<'success' | 'error' | ''>('')
const cleanupRunning = ref(false)
const cleanupMode = ref<'dry' | 'live' | null>(null)
const cleanupResult = ref<RetentionCleanupResponseDTO | null>(null)
const cleanupError = ref('')

const isLoading = computed(() => configStore.isLoading)
const loadError = computed(() => configStore.error)
const retentionLastRunSummary = computed(() => {
  const lastRun = configStore.retentionLastRun
  if (lastRun.status === 'never') {
    return 'never run'
  }
  if (lastRun.status === 'running') {
    return 'running now'
  }
  const finishedAt = lastRun.finished_at ? new Date(lastRun.finished_at).toLocaleString() : 'unknown finish time'
  if (lastRun.status === 'error') {
    return `failed at ${finishedAt}${lastRun.error ? `: ${lastRun.error}` : ''}`
  }
  return `${lastRun.total_deleted} rows removed at ${finishedAt}`
})
const hasUnsavedChanges = computed(() => {
  return JSON.stringify(retentionForm) !== JSON.stringify(configStore.dataRetention)
    || JSON.stringify({ ...scheduleForm, enabled: scheduleEnabled.value }) !== JSON.stringify(configStore.retentionSchedule)
})

function syncFormFromStore() {
  Object.assign(retentionForm, configStore.dataRetention)
  Object.assign(scheduleForm, configStore.retentionSchedule)
  scheduleEnabled.value = configStore.retentionSchedule.enabled
}

function resetRetentionForm() {
  syncFormFromStore()
  saveMessage.value = ''
  saveStatus.value = ''
}

async function saveRetention() {
  try {
    isSaving.value = true
    saveMessage.value = ''
    saveStatus.value = ''
    await configStore.updateDataRetention({
      ...retentionForm,
      workflow_executions_days: retentionForm.worker_events_days,
    })
    await configStore.updateRetentionSchedule({ ...scheduleForm, enabled: scheduleEnabled.value })
    syncFormFromStore()
    saveMessage.value = 'Retention settings saved.'
    saveStatus.value = 'success'
  } catch (err) {
    saveMessage.value = err instanceof Error ? err.message : 'Failed to save retention settings.'
    saveStatus.value = 'error'
  } finally {
    isSaving.value = false
  }
}

async function executeCleanup(dryRun: boolean) {
  if (hasUnsavedChanges.value) {
    cleanupError.value = 'Save retention settings before previewing or running cleanup.'
    return
  }

  try {
    cleanupRunning.value = true
    cleanupMode.value = dryRun ? 'dry' : 'live'
    cleanupError.value = ''
    cleanupResult.value = await configStore.runRetentionCleanup(dryRun)
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

onMounted(async () => {
  if (!configStore.config) {
    await configStore.fetchConfig()
  }
  syncFormFromStore()
})

definePageMeta({
  middleware: [],
})
</script>
