<template>
  <span
    :class="cn(
      'relative inline-flex h-9 w-9 shrink-0 overflow-hidden rounded-full border border-border-subtle bg-background-surface text-sm text-text-primary',
      props.class
    )"
  >
    <slot />
  </span>
</template>

<script setup lang="ts">
import { cn } from '@/lib/utils'

interface Props {
  class?: string
}

const props = withDefaults(defineProps<Props>(), {
  class: ''
})
</script>
