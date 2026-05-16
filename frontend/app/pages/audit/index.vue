<template>
  <div class="max-w-7xl mx-auto">
    <div class="mb-8 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
      <div>
        <h1 class="text-xl font-semibold text-text-primary">Audit Log</h1>
        <p class="mt-1 text-xs text-text-muted">
          Search manual operator actions and automated workflow interventions.
        </p>
      </div>

      <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Input
          v-model="search"
          type="text"
          placeholder="Search actor, action, task..."
          @keyup.enter="loadAudit"
        />
        <Select v-model="sourceFilter">
          <option value="">All Sources</option>
          <option value="manual">Manual</option>
          <option value="workflow">Workflow</option>
          <option value="system">System</option>
        </Select>
        <Select v-model="statusFilter">
          <option value="">All Statuses</option>
          <option value="success">Success</option>
          <option value="failed">Failed</option>
          <option value="skipped">Skipped</option>
        </Select>
        <Button variant="outline" @click="loadAudit">
          Refresh
        </Button>
      </div>
    </div>

    <div class="mb-4 flex flex-wrap items-center gap-2 text-xs text-text-muted">
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Input } from '~/components/ui/input'
import { Button } from '~/components/ui/button'
import Select from '~/components/common/Select.vue'
import AuditLogList from '~/components/audit/AuditLogList.vue'

const route = useRoute()
const auditStore = useAuditStore()

const search = ref((route.query.search as string) || '')
const sourceFilter = ref((route.query.source as string) || '')
const statusFilter = ref((route.query.status as string) || '')
const taskFilter = ref((route.query.task_id as string) || '')
const workflowFilter = ref((route.query.workflow_id as string) || '')

async function loadAudit() {
  await auditStore.fetchAuditLogs({
    limit: 100,
    search: search.value || null,
    source: sourceFilter.value || null,
    status: statusFilter.value || null,
    task_id: taskFilter.value || null,
    workflow_id: workflowFilter.value || null,
  })
}

onMounted(loadAudit)
</script>
