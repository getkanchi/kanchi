<script setup lang="ts">
import type { HTMLAttributes } from "vue"
import { Primitive, type PrimitiveProps } from "reka-ui"
import { cn } from "@/lib/utils"
import { buttonVariants, type ButtonVariants } from "./index"
import { computed } from "vue"

interface Props {
  variant?: ButtonVariants["variant"]
  size?: ButtonVariants["size"]
  class?: HTMLAttributes["class"]
  as?: PrimitiveProps["as"]
  asChild?: PrimitiveProps["asChild"]
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  as: "button",
  variant: "default",
  size: "default",
  asChild: false,
  disabled: false,
})

const buttonClass = computed(() => {
  const variantClasses = buttonVariants({ 
    variant: props.variant || "default", 
    size: props.size || "default" 
  })
  console.log('Button props:', { variant: props.variant, size: props.size })
  console.log('Variant classes:', variantClasses)
  const finalClasses = cn(variantClasses, props.class)
  console.log('Final classes:', finalClasses)
  return finalClasses
})
</script>

<template>
  <Primitive
    :as="props.as"
    :as-child="props.asChild"
    :class="buttonClass"
    :disabled="props.disabled"
  >
    <slot />
  </Primitive>
</template>
