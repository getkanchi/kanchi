<template>
  <select
    ref="selectRef"
    :value="normalizedValue"
    @change="handleChange"
    :disabled="disabled"
    :class="cn(selectVariants({ variant, size }), props.class)"
  >
    <slot />
  </select>
</template>

<script lang="ts">
import { cva } from "class-variance-authority"
import type { VariantProps } from "class-variance-authority"

export const selectVariants = cva(
  "border rounded transition-colors focus:outline-none focus:ring-1 font-mono",
  {
    variants: {
      variant: {
        default: "bg-background-surface border-border text-text-primary focus:border-border-highlight focus:ring-border-highlight",
        outline: "bg-transparent border-border text-text-primary hover:bg-background-hover focus:border-primary focus:ring-primary/40",
      },
      size: {
        sm: "px-2 py-1 text-xs",
        default: "px-2 py-1 text-sm",
        lg: "px-3 py-2 text-base",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
)

export type SelectVariants = VariantProps<typeof selectVariants>
</script>

<script setup lang="ts">
import { computed, onMounted, ref, watch, type HTMLAttributes } from "vue"
import { cn } from "@/lib/utils"

const props = defineProps<{
  modelValue?: string | number
  variant?: SelectVariants["variant"]
  size?: SelectVariants["size"]
  disabled?: boolean
  class?: HTMLAttributes["class"]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string | number]
}>()

const selectRef = ref<HTMLSelectElement | null>(null)

const normalizedValue = computed(() => {
  if (props.modelValue === undefined || props.modelValue === null) {
    return ""
  }
  return String(props.modelValue)
})

function handleChange(event: Event) {
  const target = event.target as HTMLSelectElement
  emit('update:modelValue', target.value)
}

function syncSelectValue() {
  const target = selectRef.value
  if (!target) return

  const value = normalizedValue.value
  if (target.value !== value) {
    target.value = value
  }
}

onMounted(() => {
  syncSelectValue()
})

watch(normalizedValue, () => {
  syncSelectValue()
})
</script>
