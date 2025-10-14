<template>
  <Button
    :variant="variant"
    :size="size"
    :disabled="disabled"
    :class="cn('p-0', computedSizeClasses, className)"
    @click="$emit('click', $event)"
  >
    <component 
      :is="icon" 
      :class="cn(iconClasses, { 'animate-spin': loading })"
    />
  </Button>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Button } from '~/components/ui/button'
import type { ButtonVariants } from '~/components/ui/button'
import { cn } from '@/lib/utils'
import type { LucideIcon } from 'lucide-vue-next'

interface Props {
  icon: LucideIcon
  variant?: ButtonVariants['variant']
  size?: 'xs' | 'sm' | 'md' | 'lg'
  disabled?: boolean
  loading?: boolean
  class?: string
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'ghost',
  size: 'md',
  disabled: false,
  loading: false,
})

defineEmits<{
  click: [event: MouseEvent]
}>()

const className = computed(() => props.class)

const computedSizeClasses = computed(() => {
  const sizeMap = {
    xs: 'h-6 w-6',
    sm: 'h-7 w-7',
    md: 'h-8 w-8',
    lg: 'h-9 w-9',
  }
  return sizeMap[props.size]
})

const iconClasses = computed(() => {
  const iconSizeMap = {
    xs: 'h-3 w-3',
    sm: 'h-3.5 w-3.5',
    md: 'h-4 w-4',
    lg: 'h-4.5 w-4.5',
  }
  return iconSizeMap[props.size]
})
</script>