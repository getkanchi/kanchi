<template>
  <span 
    :class="cn(pillVariants({ variant, size }), props.class)"
  >
    <slot />
  </span>
</template>

<script setup lang="ts">
import type { HTMLAttributes } from "vue"
import type { PillVariants } from "."
import { cn } from "@/lib/utils"
import { pillVariants } from "."

const props = defineProps<{
  variant?: PillVariants["variant"]
  size?: PillVariants["size"]
  class?: HTMLAttributes["class"]
}>()
</script>