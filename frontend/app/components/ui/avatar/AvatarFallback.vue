<template>
  <span
    :class="cn(
      'flex h-full w-full items-center justify-center bg-background-muted text-xs font-medium uppercase text-text-secondary',
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
