<template>
  <div class="relative">
    <div :class="['w-1.5 h-1.5 rounded-full', dotClass]"></div>
    <div 
      v-if="pulse" 
      :class="['absolute inset-0 w-1.5 h-1.5 rounded-full animate-ping', dotClass]"
    ></div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  status: 'online' | 'offline' | 'warning' | 'error' | 'info' | 'success' | 'muted'
  pulse?: boolean
}>()

const dotClass = computed(() => {
  const colors = {
    online: 'bg-status-success',
    success: 'bg-status-success',
    offline: 'bg-status-error',
    error: 'bg-status-error', 
    warning: 'bg-status-warning',
    info: 'bg-status-info',
    muted: 'bg-gray-400',
  }
  return colors[props.status] || 'bg-gray-500'
})
</script>
