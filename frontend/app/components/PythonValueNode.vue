<script setup lang="ts">
import { ref, computed } from 'vue'
import { ChevronRight } from 'lucide-vue-next'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'

interface Props {
  value: any
  keyName?: string | number
  depth?: number
  isArrayItem?: boolean
  index?: number
}

const props = withDefaults(defineProps<Props>(), {
  depth: 0,
  isArrayItem: false,
  index: 0
})

const isOpen = ref(true)  // Expand by default

// Determine the type of the value
const valueType = computed(() => {
  if (props.value === null) return 'none'
  if (props.value === undefined) return 'undefined'
  if (Array.isArray(props.value)) return 'list'
  if (typeof props.value === 'object') return 'dict'
  if (typeof props.value === 'string') return 'str'
  if (typeof props.value === 'number') {
    return Number.isInteger(props.value) ? 'int' : 'float'
  }
  if (typeof props.value === 'boolean') return 'bool'
  return 'unknown'
})

const isComplex = computed(() => {
  return valueType.value === 'dict' || valueType.value === 'list'
})

const formattedValue = computed(() => {
  if (valueType.value === 'str') return `"${props.value}"`
  if (valueType.value === 'none') return 'None'
  if (valueType.value === 'undefined') return 'undefined'
  if (valueType.value === 'bool') return props.value ? 'True' : 'False'
  return String(props.value)
})

const children = computed(() => {
  if (valueType.value === 'dict') {
    return Object.entries(props.value).map(([key, val]) => ({
      key,
      value: val
    }))
  }
  if (valueType.value === 'list') {
    return props.value.map((val: any, idx: number) => ({
      key: idx,
      value: val
    }))
  }
  return []
})

const itemCount = computed(() => {
  if (valueType.value === 'dict') return Object.keys(props.value).length
  if (valueType.value === 'list') return props.value.length
  return 0
})

// Value color based on type - minimal colors
const valueColor = computed(() => {
  const colors = {
    str: 'text-text-primary',
    int: 'text-text-primary',
    float: 'text-text-primary',
    bool: 'text-text-primary',
    none: 'text-text-muted',
    list: 'text-text-primary',
    dict: 'text-text-primary',
    undefined: 'text-text-muted',
    unknown: 'text-text-muted'
  }
  return colors[valueType.value as keyof typeof colors] || colors.unknown
})
</script>

<template>
  <div class="leading-relaxed">
    <!-- Simple values -->
    <div v-if="!isComplex" class="flex items-baseline gap-2 py-1.5 border-b border-border-subtle">
      <!-- Key name -->
      <span v-if="keyName !== undefined" class="text-text-secondary text-xs font-mono flex-shrink-0">
        <span v-if="typeof keyName === 'string'">{{ keyName }}</span>
        <span v-else class="text-text-muted">[{{ keyName }}]</span>
        <span class="text-text-muted mx-1">:</span>
      </span>

      <!-- Value -->
      <span :class="valueColor" class="font-mono text-xs break-all">
        {{ formattedValue }}
      </span>
    </div>

    <!-- Complex values (dict/list) -->
    <Collapsible v-else v-model:open="isOpen" class="group">
      <CollapsibleTrigger
        class="flex items-baseline gap-2 w-full py-1.5 border-b border-border-subtle hover:bg-background-hover-subtle transition-colors"
      >
        <!-- Chevron -->
        <ChevronRight
          class="h-3 w-3 text-text-muted transition-transform flex-shrink-0 mt-0.5"
          :class="{ 'rotate-90': isOpen }"
        />

        <!-- Key name -->
        <span v-if="keyName !== undefined" class="text-text-secondary text-xs font-mono flex-shrink-0">
          <span v-if="typeof keyName === 'string'">{{ keyName }}</span>
          <span v-else class="text-text-muted">[{{ keyName }}]</span>
          <span class="text-text-muted mx-1">:</span>
        </span>

        <!-- Type indicator -->
        <span class="text-text-muted text-xs font-mono">
          {{ valueType === 'dict' ? '{' : '[' }}
          <span v-if="!isOpen" class="text-text-muted">{{ itemCount }}</span>
          {{ valueType === 'dict' ? '}' : ']' }}
        </span>
      </CollapsibleTrigger>

      <CollapsibleContent>
        <div class="ml-4 border-l border-border pl-3">
          <PythonValueNode
            v-for="(child, idx) in children"
            :key="idx"
            :value="child.value"
            :key-name="child.key"
            :depth="depth + 1"
            :is-array-item="valueType === 'list'"
            :index="idx"
          />
        </div>
      </CollapsibleContent>
    </Collapsible>
  </div>
</template>
