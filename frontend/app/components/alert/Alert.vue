<script setup lang="ts">
import { computed } from 'vue'
import { AlertTriangle, CheckCircle, Info, XCircle } from 'lucide-vue-next'
import type { AlertVariants } from './index'

interface Props {
  variant?: AlertVariants['variant']
  size?: AlertVariants['size']
  showIcon?: boolean
  dismissible?: boolean
  title?: string
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'info',
  size: 'default',
  showIcon: true,
  dismissible: false
})

const emit = defineEmits<{
  dismiss: []
}>()

// Icon mapping for each variant
const iconMap = {
  success: CheckCircle,
  warning: AlertTriangle,
  error: XCircle,
  info: Info
}

// Color schemes for each variant
const variantClasses = computed(() => {
  const variants = {
    success: {
      container: 'bg-green-500/10 border-green-500/30',
      icon: 'text-green-400',
      title: 'text-green-200',
      content: 'text-green-300/90'
    },
    warning: {
      container: 'bg-orange-500/10 border-orange-500/30',
      icon: 'text-orange-400',
      title: 'text-orange-200',
      content: 'text-orange-300/80'
    },
    error: {
      container: 'bg-red-500/10 border-red-500/30',
      icon: 'text-red-400',
      title: 'text-red-200',
      content: 'text-red-300/90'
    },
    info: {
      container: 'bg-blue-500/10 border-blue-500/30',
      icon: 'text-blue-400',
      title: 'text-blue-200',
      content: 'text-blue-300/90'
    }
  }
  return variants[props.variant]
})

const sizeClasses = computed(() => {
  const sizes = {
    sm: 'p-2 text-xs',
    default: 'p-3 text-sm',
    lg: 'p-4 text-base'
  }
  return sizes[props.size]
})

const iconSizeClasses = computed(() => {
  const sizes = {
    sm: 'h-3 w-3',
    default: 'h-4 w-4',
    lg: 'h-5 w-5'
  }
  return sizes[props.size]
})

const IconComponent = computed(() => iconMap[props.variant])
</script>

<template>
  <div 
    :class="[
      'border rounded-lg relative',
      variantClasses.container,
      sizeClasses
    ]"
  >
    <!-- Dismiss button -->
    <button
      v-if="dismissible"
      @click="emit('dismiss')"
      class="absolute right-2 top-2 rounded-sm opacity-70 hover:opacity-100 transition-opacity focus:outline-none focus:ring-2 focus:ring-primary/30 focus:ring-offset-2"
    >
      <XCircle :class="['w-3 h-3', variantClasses.icon]" />
      <span class="sr-only">Dismiss</span>
    </button>

    <div class="flex items-start gap-2">
      <!-- Icon -->
      <component
        v-if="showIcon"
        :is="IconComponent"
        :class="[
          iconSizeClasses,
          variantClasses.icon,
          'mt-0.5 flex-shrink-0'
        ]"
      />
      
      <!-- Content -->
      <div class="flex-1 min-w-0">
        <!-- Title -->
        <div
          v-if="title || $slots.title"
          :class="[
            'font-medium mb-1',
            variantClasses.title
          ]"
        >
          <slot name="title">{{ title }}</slot>
        </div>
        
        <!-- Content -->
        <div :class="variantClasses.content">
          <slot />
        </div>
      </div>
    </div>
  </div>
</template>
