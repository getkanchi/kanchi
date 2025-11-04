<template>
  <div class="space-y-3">
    <!-- Connection Health Section -->
    <div>
      <h4 class="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-2">Connection Health</h4>
      <div class="space-y-1.5">
        <div class="flex justify-between items-center text-xs">
          <span class="text-text-muted">Status</span>
          <div class="flex items-center gap-1.5">
            <StatusDot :status="displayConnected ? 'online' : 'offline'" :pulse="displayConnected" />
            <span class="font-mono font-medium">{{ displayConnected ? "Connected" : "Disconnected" }}</span>
          </div>
        </div>
        <div class="flex justify-between items-center text-xs">
          <span class="text-text-muted">Active Connections</span>
          <span class="font-mono">{{ healthData?.connections ?? 0 }}</span>
        </div>
        <div class="flex justify-between items-center text-xs">
          <span class="text-text-muted">Celery Monitor</span>
          <div class="flex items-center gap-1.5">
            <CheckCircle v-if="healthData?.monitor_running" class="h-3 w-3 text-status-success" />
            <XCircle v-else class="h-3 w-3 text-status-error" />
            <span class="font-mono">{{ healthData?.monitor_running ? "Running" : "Stopped" }}</span>
          </div>
        </div>
        <div class="flex justify-between items-center text-xs">
          <span class="text-text-muted">Workers Online</span>
          <span class="font-mono">{{ healthData?.workers ?? 0 }}</span>
        </div>
      </div>
    </div>

    <Separator class="bg-border" />

    <!-- System Information Section -->
    <div>
      <h4 class="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-2">System Information</h4>
      <div class="space-y-1.5">
        <div class="flex justify-between items-center text-xs">
          <span class="text-text-muted">Uptime</span>
          <span class="font-mono">{{ formattedUptime }}</span>
        </div>
        <div class="flex justify-between items-center text-xs">
          <span class="text-text-muted">Python</span>
          <span class="font-mono">{{ healthData?.python_version ?? 'N/A' }}</span>
        </div>
        <div class="flex justify-between items-center text-xs">
          <span class="text-text-muted">Platform</span>
          <span class="font-mono truncate max-w-[200px]" :title="healthData?.platform">{{ healthData?.system ?? 'N/A' }}</span>
        </div>
        <div class="flex justify-between items-center text-xs">
          <span class="text-text-muted">API Version</span>
          <span class="font-mono">{{ healthData?.api_version ?? 'N/A' }}</span>
        </div>
      </div>
    </div>

    <Separator class="bg-border" />

    <!-- Configuration Section -->
    <div>
      <h4 class="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-2">Configuration</h4>
      <div class="space-y-2">
        <div class="text-xs">
          <div class="flex items-center gap-1.5 mb-1">
            <Database class="h-3 w-3 text-text-muted" />
            <span class="text-text-muted">Database</span>
          </div>
          <SecretField
            :value="healthData?.database_url_full ?? 'N/A'"
            :masked-value="healthData?.database_url ?? 'N/A'"
          />
        </div>
        <div class="text-xs">
          <div class="flex items-center gap-1.5 mb-1">
            <Server class="h-3 w-3 text-text-muted" />
            <span class="text-text-muted">Broker</span>
          </div>
          <SecretField
            :value="healthData?.broker_url_full ?? 'N/A'"
            :masked-value="healthData?.broker_url ?? 'N/A'"
          />
        </div>
        <div class="flex justify-between items-center text-xs">
          <span class="text-text-muted">Log Level</span>
          <span class="font-mono">{{ healthData?.log_level ?? 'N/A' }}</span>
        </div>
      </div>
    </div>

    <Separator class="bg-border" />

    <!-- Statistics Section -->
    <div>
      <h4 class="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-2">Statistics</h4>
      <div class="space-y-1.5">
        <div class="flex justify-between items-center text-xs">
          <span class="text-text-muted">Total Tasks Processed</span>
          <span class="font-mono">{{ healthData?.total_tasks_processed?.toLocaleString() ?? 0 }}</span>
        </div>
        <div class="flex justify-between items-center text-xs">
          <span class="text-text-muted">First Task</span>
          <span class="font-mono text-xs" :title="healthData?.first_task_at">
            {{ formattedFirstTask }}
          </span>
        </div>
      </div>
    </div>

    <div class="pt-1 flex items-center justify-between text-xs text-text-muted border-t border-border">
      <span>Last updated</span>
      <span class="font-mono">{{ lastUpdated }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { CheckCircle, XCircle, Database, Server } from 'lucide-vue-next'
import StatusDot from '~/components/StatusDot.vue'
import SecretField from '~/components/SecretField.vue'
import { Separator } from '@/components/ui/separator'

const wsStore = useWebSocketStore()
const healthStore = useHealthStore()

const authStore = useAuthStore()
const { isAuthenticated } = storeToRefs(authStore)

const healthData = ref<HealthData | null>(null)
const lastUpdated = ref<string>('')
const isClientSide = ref(false)

onMounted(async () => {
  isClientSide.value = true
  await fetchHealthData()
})

const displayConnected = computed(() => isClientSide.value && wsStore.isConnected)

const fetchHealthData = async () => {
  try {
    if (! isAuthenticated.value) {
      await healthStore.fetchHealth()
    } else {
      await healthStore.fetchHealthDetails()
    }
    healthData.value = healthStore.health
    lastUpdated.value = new Date().toLocaleTimeString()
  } catch (error) {
    console.error('Failed to fetch health data:', error)
  }
}

const formattedUptime = computed(() => {
  if (!healthData.value?.uptime_seconds) return 'N/A'

  const seconds = healthData.value.uptime_seconds
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)

  if (days > 0) {
    return `${days}d ${hours}h ${minutes}m`
  } else if (hours > 0) {
    return `${hours}h ${minutes}m`
  } else {
    return `${minutes}m`
  }
})

const formattedFirstTask = computed(() => {
  if (!healthData.value?.first_task_at) return 'No tasks yet'

  try {
    const date = new Date(healthData.value.first_task_at)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffDays > 7) {
      return date.toLocaleDateString()
    } else if (diffDays > 0) {
      return `${diffDays}d ago`
    } else {
      return 'Today'
    }
  } catch {
    return 'Invalid date'
  }
})

// Expose refresh function for parent
defineExpose({
  refresh: fetchHealthData
})
</script>
