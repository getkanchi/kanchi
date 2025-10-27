<template>
  <div class="space-y-4">
    <!-- Enable Circuit Breaker Toggle -->
    <div class="flex items-center justify-between rounded-lg border border-border px-4 py-3 bg-background-raised">
      <div class="flex-1">
        <label class="text-sm font-medium text-text-primary">
          Enable Circuit Breaker
        </label>
        <p class="text-xs text-text-muted mt-0.5">
          Prevent workflows from executing too frequently for the same context
        </p>
      </div>
      <Switch
        :model-value="switchChecked"
        @update:model-value="toggleEnabled"
      />
    </div>

    <!-- Circuit Breaker Configuration (shown when enabled) -->
    <div v-if="localConfig?.enabled" class="space-y-4 pl-4 border-l-2 border-primary/20">
      <!-- Context Field Selection -->
      <div>
        <label class="text-xs font-medium text-text-secondary mb-1.5 block">
          Group executions by
        </label>
        <Select
          :model-value="localConfig.context_field || ''"
          @update:model-value="updateContextField"
          class="w-full"
          size="sm"
        >
          <option value="">Auto (recommended)</option>
          <optgroup label="Task Context">
            <option value="root_id">Task Chain (root_id)</option>
            <option value="task_id">Individual Task (task_id)</option>
            <option value="task_name">Task Name</option>
          </optgroup>
          <optgroup label="Worker Context">
            <option value="hostname">Hostname</option>
            <option value="worker_name">Worker Name</option>
          </optgroup>
          <optgroup label="Queue Context">
            <option value="queue">Queue</option>
            <option value="routing_key">Routing Key</option>
          </optgroup>
        </Select>
        <p class="text-xs text-text-muted mt-1.5">
          <span v-if="!localConfig.context_field || localConfig.context_field === ''">
            Auto mode uses <code class="px-1 py-0.5 rounded bg-background-base text-primary font-mono text-[10px]">root_id</code> for task triggers (recommended for retry chains)
          </span>
          <span v-else-if="localConfig.context_field === 'root_id'">
            Groups entire task retry chains together
          </span>
          <span v-else-if="localConfig.context_field === 'task_id'">
            ⚠️ Each retry will be treated separately - may cause duplicate executions
          </span>
          <span v-else-if="localConfig.context_field === 'task_name'">
            Groups all tasks with the same name
          </span>
          <span v-else-if="localConfig.context_field === 'hostname'">
            Groups tasks by worker hostname
          </span>
          <span v-else-if="localConfig.context_field === 'worker_name'">
            Groups tasks by worker name
          </span>
          <span v-else-if="localConfig.context_field === 'queue'">
            Groups tasks by queue name
          </span>
          <span v-else-if="localConfig.context_field === 'routing_key'">
            Groups tasks by routing key
          </span>
        </p>
      </div>

      <!-- Execution Limits -->
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="text-xs font-medium text-text-secondary mb-1.5 block">
            Max executions
          </label>
          <Input
            :value="localConfig.max_executions"
            @input="updateMaxExecutions(($event.target as HTMLInputElement).value)"
            type="number"
            min="1"
            class="w-full"
          />
          <p class="text-xs text-text-muted mt-1">
            Execution limit per window
          </p>
        </div>
        <div>
          <label class="text-xs font-medium text-text-secondary mb-1.5 block">
            Window (seconds)
          </label>
          <Input
            :value="localConfig.window_seconds"
            @input="updateWindowSeconds(($event.target as HTMLInputElement).value)"
            type="number"
            min="1"
            class="w-full"
          />
          <p class="text-xs text-text-muted mt-1">
            Sliding time window
          </p>
        </div>
      </div>

      <!-- Visual Summary -->
      <div class="rounded-lg border border-status-info-border bg-status-info-bg px-3.5 py-2.5">
        <div class="flex items-start gap-2">
          <Info class="h-4 w-4 text-status-info mt-0.5 flex-shrink-0" />
          <div class="text-xs text-status-info">
            <span class="font-medium">Circuit breaker active:</span>
            Max {{ localConfig.max_executions }} execution{{ localConfig.max_executions > 1 ? 's' : '' }}
            per {{ formatDuration(localConfig.window_seconds) }}
            <span v-if="localConfig.context_field">
              for each unique <code class="px-1 py-0.5 rounded bg-status-info/10 font-mono text-[10px]">{{ localConfig.context_field }}</code>
            </span>
            <span v-else>
              per context group
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Info } from 'lucide-vue-next'
import { Switch } from '~/components/ui/switch'
import { Input } from '~/components/ui/input'
import Select from '~/components/common/Select.vue'
import type { CircuitBreakerConfig } from '~/types/workflow'

const props = defineProps<{
  config?: CircuitBreakerConfig
}>()

const emit = defineEmits<{
  'update:config': [config?: CircuitBreakerConfig]
}>()

const localConfig = computed(() => props.config)
const switchChecked = computed(() => props.config?.enabled === true)

function toggleEnabled(checked: boolean) {
  if (!checked) {
    emit('update:config', undefined)
  } else {
    emit('update:config', {
      enabled: true,
      max_executions: 1,
      window_seconds: 300,
      context_field: undefined
    })
  }
}

function updateContextField(value: string) {
  if (!localConfig.value) return
  const updated = {
    ...localConfig.value,
    context_field: value === '' ? undefined : value
  }
  emit('update:config', updated)
}

function updateMaxExecutions(value: string) {
  if (!localConfig.value) return
  const num = parseInt(value, 10)
  if (!isNaN(num) && num >= 1) {
    const updated = {
      ...localConfig.value,
      max_executions: num
    }
    emit('update:config', updated)
  }
}

function updateWindowSeconds(value: string) {
  if (!localConfig.value) return
  const num = parseInt(value, 10)
  if (!isNaN(num) && num >= 1) {
    const updated = {
      ...localConfig.value,
      window_seconds: num
    }
    emit('update:config', updated)
  }
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`
  return `${Math.floor(seconds / 86400)}d`
}
</script>
