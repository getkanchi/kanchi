<script setup lang="ts">
import type { HTMLAttributes } from "vue"
import { cn } from "@/lib/utils"

const props = defineProps<{
  class?: HTMLAttributes["class"]
}>()
</script>

<template>
  <div
    :class="
      cn(
        'rounded-xl border border-border bg-background-surface text-text-primary shadow-sm',
        props.class,
      )
    "
  >
    <slot />
  </div>
</template>
