<script setup lang="ts">
import type { HTMLAttributes } from "vue"
import { useVModel } from "@vueuse/core"
import { cn } from "@/lib/utils"

const props = defineProps<{
  class?: HTMLAttributes["class"]
  defaultValue?: string | number
  modelValue?: string | number
}>()

const emits = defineEmits<{
  (e: "update:modelValue", payload: string | number): void
}>()

const modelValue = useVModel(props, "modelValue", emits, {
  passive: true,
  defaultValue: props.defaultValue,
})
</script>

<template>
  <textarea
    v-model="modelValue"
    :class="cn(
      'flex min-h-[60px] w-full rounded-md border border-border-subtle bg-transparent px-3 py-2 text-sm text-text-primary shadow-sm placeholder:text-text-muted focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary/30 disabled:cursor-not-allowed disabled:opacity-50',
      props.class
    )"
  />
</template>
