<script setup lang="ts">
type MetricTone = 'default' | 'primary' | 'success' | 'warning' | 'error' | 'muted'

defineProps<{
  metrics: Array<{
    label: string
    value: string | number
    tone?: MetricTone
  }>
}>()

function toneClass(tone: MetricTone = 'default') {
  switch (tone) {
    case 'primary':
      return 'text-primary'
    case 'success':
      return 'text-status-success'
    case 'warning':
      return 'text-status-warning'
    case 'error':
      return 'text-status-error'
    case 'muted':
      return 'text-text-muted'
    default:
      return 'text-text-primary'
  }
}
</script>

<template>
  <div class="flex flex-wrap items-center gap-x-4 gap-y-2">
    <div
      v-for="metric in metrics"
      :key="metric.label"
      class="flex min-w-0 items-baseline gap-2"
    >
      <span class="text-[11px] leading-none text-text-muted">{{ metric.label }}</span>
      <span
        class="font-mono text-[13px] font-medium leading-none tabular-nums"
        :class="toneClass(metric.tone)"
      >
        {{ metric.value }}
      </span>
    </div>
  </div>
</template>
