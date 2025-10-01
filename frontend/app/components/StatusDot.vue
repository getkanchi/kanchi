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

const { getDotColorClass } = useTaskStatus()

const props = defineProps<{
  status: 'online' | 'offline' | 'warning' | 'error' | 'info' | 'success' | 'muted'
  pulse?: boolean
}>()

const dotClass = computed(() => {
  return getDotColorClass(props.status)
})
</script>
