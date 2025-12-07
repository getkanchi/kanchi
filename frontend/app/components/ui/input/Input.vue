<template>
  <input
    :class="cn(
      'flex h-9 w-full rounded-md border border-border-subtle bg-transparent px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-text-muted focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary/30 disabled:cursor-not-allowed disabled:opacity-50',
      props.class
    )"
    v-bind="$attrs"
  />
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