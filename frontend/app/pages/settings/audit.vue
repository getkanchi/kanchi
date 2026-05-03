<template>
  <div class="mx-auto max-w-7xl space-y-8 py-6 lg:py-8">
    <section class="rounded-3xl border border-border-subtle bg-background-surface px-8 py-10 shadow-sm">
      <p class="text-xs font-semibold uppercase tracking-[0.3em] text-text-secondary">Settings · Audit</p>
      <h1 class="mt-3 text-3xl font-semibold text-text-primary">Audit log</h1>
      <p class="mt-4 max-w-2xl text-sm text-text-secondary">
        Review manual operator actions and automated workflow interventions without leaving the settings area.
      </p>
    </section>

    <section class="rounded-2xl border border-border-subtle bg-background-surface p-6 shadow-sm space-y-6">
      <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Input
          v-model="search"
          type="text"
          placeholder="Search actor, action, task..."
          @keyup.enter="loadAudit"
        />
        <Select v-model="sourceFilter">
          <option value="">All sources</option>
          <option value="manual">Manual</option>
          <option value="workflow">Workflow</option>
          <option value="system">System</option>
        </Select>
        <Select v-model="statusFilter">
          <option value="">All statuses</option>
          <option value="success">Success</option>
          <option value="failed">Failed</option>
          <option value="skipped">Skipped</option>
        </Select>
        <Button variant="outline" @click="loadAudit">
          Refresh
        </Button>
      </div>

      <div class="flex flex-wrap items-center gap-2 text-xs text-text-muted">
        <span v-if="taskFilter" class="rounded-full border border-border-subtle px-3 py-1">
          task {{ taskFilter }}
        </span>
        <span v-if="workflowFilter" class="rounded-full border border-border-subtle px-3 py-1">
          workflow {{ workflowFilter }}
        </span>
        <span class="rounded-full border border-border-subtle px-3 py-1">
          {{ auditStore.total }} matching entries
        </span>
      </div>

      <AuditLogList
        :entries="auditStore.entries"
        :loading="auditStore.isLoading"
        empty-title="No audit entries match the current filters"
        empty-description="Try broadening the search or clear scoped query parameters."
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import AuditLogList from '~/components/audit/AuditLogList.vue'
import Select from '~/components/common/Select.vue'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'

const route = useRoute()
const router = useRouter()
const auditStore = useAuditStore()

const search = ref('')
const sourceFilter = ref('')
const statusFilter = ref('')
const taskFilter = ref('')
const workflowFilter = ref('')

function syncFiltersFromRoute() {
  search.value = (route.query.search as string) || ''
  sourceFilter.value = (route.query.source as string) || ''
  statusFilter.value = (route.query.status as string) || ''
  taskFilter.value = (route.query.task_id as string) || ''
  workflowFilter.value = (route.query.workflow_id as string) || ''
}

async function loadAudit() {
  const query = {
    ...route.query,
    ...(search.value ? { search: search.value } : {}),
    ...(sourceFilter.value ? { source: sourceFilter.value } : {}),
    ...(statusFilter.value ? { status: statusFilter.value } : {}),
    ...(taskFilter.value ? { task_id: taskFilter.value } : {}),
    ...(workflowFilter.value ? { workflow_id: workflowFilter.value } : {}),
  }

  for (const key of ['search', 'source', 'status', 'task_id', 'workflow_id'] as const) {
    if (!query[key]) {
      delete query[key]
    }
  }

  const currentQuery = JSON.stringify(route.query)
  const nextQuery = JSON.stringify(query)
  if (currentQuery !== nextQuery) {
    await router.replace({ query })
    return
  }

  await auditStore.fetchAuditLogs({
    limit: 100,
    search: search.value || null,
    source: sourceFilter.value || null,
    status: statusFilter.value || null,
    task_id: taskFilter.value || null,
    workflow_id: workflowFilter.value || null,
  })
}

watch(
  () => route.query,
  () => {
    syncFiltersFromRoute()
    loadAudit()
  },
)

onMounted(() => {
  syncFiltersFromRoute()
  loadAudit()
})
</script>
