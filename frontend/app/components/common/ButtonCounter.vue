<script setup lang="ts">
import { computed } from 'vue'
import { cn } from '~/lib/utils'

const props = withDefaults(defineProps<{
  value: string | number
  tone?: 'primary' | 'failed' | 'neutral'
  class?: string
}>(), {
  tone: 'primary',
})

const toneClass = computed(() => {
  if (props.tone === 'failed') {
    return 'border-status-error-border bg-status-error text-white'
  }
  if (props.tone === 'neutral') {
    return 'border-border bg-background-selected text-text-primary'
  }
  return 'border-primary-border bg-primary text-white'
})
</script>

<template>
  <span
    :class="cn(
      'inline-flex h-5 min-w-5 items-center justify-center rounded border px-1.5 text-[10px] font-mono font-medium leading-none',
      toneClass,
      props.class,
    )"
  >
    {{ value }}
  </span>
</template>
