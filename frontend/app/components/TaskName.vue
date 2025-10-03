<script setup lang="ts">
import { ref, computed } from 'vue'
import { ChevronDown, ChevronUp } from 'lucide-vue-next'

interface Props {
  name: string
  size?: 'sm' | 'md' | 'lg'
  maxLength?: number
  showFullOnHover?: boolean
  expandable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  maxLength: 40,
  showFullOnHover: true,
  expandable: true
})

const isExpanded = ref(false)

// Extract the function name (last part after final dot)
const functionName = computed(() => {
  const parts = props.name.split('.')
  return parts[parts.length - 1]
})

// Extract the module path (everything before the function name)
const modulePath = computed(() => {
  const parts = props.name.split('.')
  return parts.slice(0, -1).join('.')
})

// Smart truncation: prioritize showing the function name
const smartTruncated = computed(() => {
  if (props.name.length <= props.maxLength) {
    return props.name
  }
  
  // If function name alone is too long, truncate it
  if (functionName.value.length > props.maxLength - 3) {
    return functionName.value.slice(0, props.maxLength - 3) + '...'
  }
  
  // Show truncated module path + full function name
  const availableForModule = props.maxLength - functionName.value.length - 4 // account for "..." and "."
  if (modulePath.value.length > availableForModule) {
    return '...' + modulePath.value.slice(-(availableForModule)) + '.' + functionName.value
  }
  
  return props.name
})

const shouldTruncate = computed(() => props.name.length > props.maxLength)

// CSS classes based on size
const sizeClasses = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'text-sm'
    case 'lg':
      return 'text-lg font-semibold'
    default:
      return 'text-base'
  }
})

const toggleExpanded = () => {
  if (props.expandable && shouldTruncate.value) {
    isExpanded.value = !isExpanded.value
  }
}
</script>

<template>
  <div class="task-name-container">
    <!-- Tooltip wrapper for hover behavior -->
    <div 
      v-if="showFullOnHover && shouldTruncate && !isExpanded"
      class="group relative inline-block"
    >
      <!-- Truncated display with fade effect -->
      <div 
        :class="[
          sizeClasses,
          'relative inline-block max-w-full',
          expandable && shouldTruncate ? 'cursor-pointer hover:text-blue-400 transition-colors' : ''
        ]"
        @click="toggleExpanded"
      >
        <!-- Background fade gradient -->
        <div 
          v-if="shouldTruncate"
          class="absolute right-0 top-0 bottom-0 w-8 bg-gradient-to-l from-card-base via-card-base/80 to-transparent pointer-events-none"
        />
        
        <!-- Text content -->
        <span class="inline-block pr-8">{{ smartTruncated }}</span>
        
        <!-- Expand indicator -->
        <ChevronDown 
          v-if="expandable && shouldTruncate"
          class="inline-block w-3 h-3 ml-1 opacity-60 group-hover:opacity-100 transition-opacity"
        />
      </div>
      
      <!-- Tooltip -->
      <div class="invisible group-hover:visible absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 z-50">
        <div class="bg-gray-900 text-white text-sm rounded-lg px-3 py-2 shadow-lg max-w-md whitespace-pre-wrap break-all">
          <div class="text-xs text-gray-400 mb-1">Full task name:</div>
          <div class="font-mono">{{ name }}</div>
          <div class="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
        </div>
      </div>
    </div>
    
    <!-- Expanded or non-truncated display -->
    <div 
      v-else
      :class="[
        sizeClasses,
        expandable && shouldTruncate && isExpanded ? 'cursor-pointer hover:text-blue-400 transition-colors' : ''
      ]"
      @click="toggleExpanded"
    >
      <!-- Module path with subtle styling -->
      <span v-if="isExpanded && modulePath" class="text-text-secondary">
        {{ modulePath }}.
      </span>
      <!-- Function name emphasized -->
      <span class="text-text-primary font-medium">
        {{ isExpanded ? functionName : name }}
      </span>
      
      <!-- Collapse indicator -->
      <ChevronUp 
        v-if="expandable && shouldTruncate && isExpanded"
        class="inline-block w-3 h-3 ml-1 opacity-60 hover:opacity-100 transition-opacity"
      />
    </div>
  </div>
</template>

<style scoped>
.task-name-container {
  /* Ensure proper text wrapping behavior */
  word-break: break-word;
  overflow-wrap: break-word;
}
</style>