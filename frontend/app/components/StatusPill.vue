<template>
  <div 
    class="inline-flex items-center gap-1.5 px-2 py-1 rounded-full transition-all duration-200 group relative overflow-hidden"
    :class="[pillClass, { 'ring-1 ring-offset-1 ring-offset-background-base': isCurrent }]"
  >
    <!-- Gradient animation overlay for running states -->
    <div 
      v-if="isRunning"
      class="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent animate-shimmer"
    />
    
    <!-- Status indicator dot -->
    <div class="relative flex items-center">
      <div :class="['w-1.5 h-1.5 rounded-full', dotClass]" />
      <div 
        v-if="isRunning" 
        :class="['absolute inset-0 w-1.5 h-1.5 rounded-full animate-ping', dotClass]"
      />
    </div>
    
    <!-- Label (optional) -->
    <span v-if="label" class="text-[10px] font-medium uppercase tracking-wider opacity-70">
      {{ label }}
    </span>
    
    <!-- Task ID -->
    <code class="text-[11px] font-mono relative">
      {{ displayId }}
    </code>
    
    <!-- Timestamp -->
    <span v-if="timestamp" class="text-[10px] opacity-60 ml-0.5">
      {{ formatTimestamp(timestamp) }}
    </span>
    
    <!-- Copy button (shows on hover) -->
    <button
      @click.stop="copyToClipboard"
      class="opacity-0 group-hover:opacity-100 transition-opacity duration-150 ml-0.5"
      :title="`Copy task ID: ${taskId}`"
    >
      <Copy v-if="!copied" class="h-3 w-3" />
      <Check v-else class="h-3 w-3 text-green-400" />
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Copy, Check } from 'lucide-vue-next'

const { isAnimatedStatus, getStatusColor } = useTaskStatus()

const props = defineProps<{
  status: string
  taskId: string
  timestamp?: string
  label?: string
  isCurrent?: boolean
}>()

const copied = ref(false)

const displayId = computed(() => {
  return props.taskId.substring(0, 8)
})

const isRunning = computed(() => {
  return isAnimatedStatus(props.status || '')
})

const pillClass = computed(() => {
  const config = getStatusColor(props.status || 'pending')
  const base = `border ${config.pill}`
  return props.isCurrent && config.ring ? `${base} ${config.ring}` : base
})

const dotClass = computed(() => {
  const config = getStatusColor(props.status || 'pending')
  return config.dot
})

const formatTimestamp = (timestamp: string) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  
  if (days > 0) return `${days}d ago`
  if (hours > 0) return `${hours}h ago`
  if (minutes > 0) return `${minutes}m ago`
  if (seconds > 0) return `${seconds}s ago`
  return 'just now'
}

const copyToClipboard = async () => {
  try {
    await navigator.clipboard.writeText(props.taskId)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (err) {
    console.error('Failed to copy:', err)
  }
}
</script>

<style scoped>
@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

.animate-shimmer {
  animation: shimmer 2s infinite;
}
</style>