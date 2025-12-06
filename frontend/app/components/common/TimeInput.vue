<template>
  <input
    :value="modelValue"
    @input="handleInput"
    type="time"
    :disabled="disabled"
    :class="cn(timeInputVariants({ size }), props.class)"
  />
</template>

<script lang="ts">
import { cva } from "class-variance-authority"
import type { VariantProps } from "class-variance-authority"

export const timeInputVariants = cva(
  "border border-border-subtle rounded bg-background-surface text-text-primary focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary font-mono transition-colors",
  {
    variants: {
      size: {
        sm: "px-2 py-1 text-xs",
        default: "px-3 py-2 text-sm",
        lg: "px-4 py-3 text-base",
      },
    },
    defaultVariants: {
      size: "default",
    },
  },
)

export type TimeInputVariants = VariantProps<typeof timeInputVariants>
</script>

<script setup lang="ts">
import type { HTMLAttributes} from "vue"
import { cn } from "@/lib/utils"

const props = defineProps<{
  modelValue?: string
  size?: TimeInputVariants["size"]
  disabled?: boolean
  class?: HTMLAttributes["class"]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

function handleInput(event: Event) {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.value)
}
</script>

<style scoped>
/* Hide time input controls (clock icons) */
input[type="time"]::-webkit-calendar-picker-indicator {
  display: none;
}

input[type="time"]::-webkit-inner-spin-button,
input[type="time"]::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

input[type="time"] {
  -moz-appearance: textfield;
}
</style>
