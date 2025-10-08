<script setup lang="ts">
import { computed } from 'vue'
import PythonValueNode from './PythonValueNode.vue'
import CopyButton from './CopyButton.vue'

interface Props {
  value: any  // Can be object (from API/WebSocket) or string (legacy)
  title: string
  copyKey: string
  emptyMessage?: string
}

const props = withDefaults(defineProps<Props>(), {
  emptyMessage: 'No data'
})

// Parse the value (can be object or JSON string)
const parsedValue = computed(() => {
  if (!props.value) return null

  // If already an object, use it directly
  if (typeof props.value === 'object') {
    return props.value
  }

  // If string, try to parse as JSON
  if (typeof props.value === 'string') {
    try {
      return JSON.parse(props.value)
    } catch (e) {
      // If it's not valid JSON, return as string
      return props.value
    }
  }

  return props.value
})

// Check if value is empty
const isEmpty = computed(() => {
  if (!parsedValue.value) return true
  if (Array.isArray(parsedValue.value) && parsedValue.value.length === 0) return true
  if (typeof parsedValue.value === 'object' && Object.keys(parsedValue.value).length === 0) return true
  return false
})

// Get item count for display
const itemCount = computed(() => {
  if (!parsedValue.value) return 0
  if (Array.isArray(parsedValue.value)) return parsedValue.value.length
  if (typeof parsedValue.value === 'object') return Object.keys(parsedValue.value).length
  return 0
})

// Determine display type
const displayType = computed(() => {
  if (!parsedValue.value) return null
  if (Array.isArray(parsedValue.value)) return 'tuple'
  if (typeof parsedValue.value === 'object') return 'dict'
  return 'value'
})

// Computed value for copying (always stringify if object)
const copyValue = computed(() => {
  if (!props.value) return ''
  if (typeof props.value === 'object') {
    return JSON.stringify(props.value, null, 2)
  }
  return props.value
})
</script>

<template>
  <div class="space-y-2">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-baseline gap-2">
        <h4 class="text-xs font-medium text-text-muted uppercase tracking-wide">{{ title }}</h4>
        <span v-if="!isEmpty && displayType !== 'value'" class="text-xs text-text-muted font-mono">
          ({{ itemCount }})
        </span>
      </div>
      <CopyButton
        v-if="value"
        :text="copyValue"
        :copy-key="copyKey"
        :title="`Copy ${title.toLowerCase()}`"
        :show-text="false"
      />
    </div>

    <!-- Empty state -->
    <div
      v-if="isEmpty"
      class="py-4 text-center text-text-muted text-xs"
    >
      {{ emptyMessage }}
    </div>

    <!-- Content -->
    <div v-else class="bg-background-base border border-border rounded-md p-3">
      <!-- Simple value (single string/number) -->
      <div v-if="displayType === 'value'" class="font-mono text-xs text-text-primary">
        {{ parsedValue }}
      </div>

      <!-- Complex structure -->
      <div v-else class="space-y-0">
        <!-- For tuples (arrays), display with index -->
        <template v-if="displayType === 'tuple'">
          <PythonValueNode
            v-for="(item, idx) in parsedValue"
            :key="idx"
            :value="item"
            :key-name="idx"
            :depth="0"
            :index="idx"
          />
        </template>

        <!-- For dicts (objects), display with keys -->
        <template v-else-if="displayType === 'dict'">
          <PythonValueNode
            v-for="(val, key, idx) in parsedValue"
            :key="key"
            :value="val"
            :key-name="key"
            :depth="0"
            :index="idx"
          />
        </template>
      </div>
    </div>
  </div>
</template>
