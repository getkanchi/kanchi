<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { computed, useAttrs } from 'vue'
import { cn } from '@/lib/utils'
import { buttonVariants, type ButtonVariants } from './index'

interface Props {
  variant?: ButtonVariants['variant']
  size?: ButtonVariants['size']
  class?: HTMLAttributes['class']
  as?: string
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  as: 'button',
  variant: 'default',
  size: 'default',
  disabled: false,
})

const attrs = useAttrs()

const emit = defineEmits<{
  (e: 'click', event: MouseEvent): void
}>()

const buttonClass = computed(() => {
  const variantClasses = buttonVariants({
    variant: props.variant || 'default',
    size: props.size || 'default',
  })
  return cn(variantClasses, props.class)
})

function handleClick(event: MouseEvent) {
  if (props.disabled) {
    event.preventDefault()
    event.stopPropagation()
    return
  }

  emit('click', event)
}
</script>

<template>
  <component
    :is="props.as"
    v-bind="attrs"
    :class="buttonClass"
    :disabled="props.as === 'button' ? props.disabled : undefined"
    :aria-disabled="props.as !== 'button' && props.disabled ? 'true' : undefined"
    @click="handleClick"
  >
    <slot />
  </component>
</template>
