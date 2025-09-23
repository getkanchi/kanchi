<template>
  <div class="relative max-w-md w-full">
    <!-- Main input container with flex layout -->
    <div class="relative flex items-center gap-1 px-2 border border-card-border focus-within:ring-gray-700 rounded-md bg-background-primary/50 focus-within:ring-1  ">
      <!-- Search icon -->
      <Search class="h-4 w-4 text-muted-foreground flex-shrink-0 mx-2" />
      
      <!-- Filter badges -->
      <div v-if="activeFilters.length > 0" class="flex items-center gap-1 flex-shrink-0">
        <FilterBadge
          v-for="(filter, index) in activeFilters"
          :key="`${filter.key}-${filter.value}`"
          :filter="filter"
          @remove="removeFilter(index)"
        />
      </div>
      
      <!-- Actual input field -->
      <input
        ref="inputRef"
        type="text"
        :placeholder="activeFilters.length > 0 ? '' : 'Search or filter...'"
        class="flex-1 bg-transparent border-0 outline-0 text-sm min-w-0 h-7"
        :value="currentInput"
        @input="handleInput"
        @keydown="handleKeydown"
        @focus="showSuggestions = true"
        @blur="handleBlur"
      />
    </div>
    
    <!-- Autocomplete dropdown -->
    <div
      v-if="showSuggestions && (suggestions.length > 0 || currentInput.includes(':'))"
      class="absolute top-full mt-1 w-full bg-card-base border border-card-border rounded-md shadow-lg z-50 max-h-60 overflow-y-auto"
    >
      <!-- Filter key suggestions -->
      <div v-if="!currentFilter.key && !currentInput.includes(':')">
        <div class="px-3 py-2 text-xs text-gray-500 border-b border-card-border">
          Filters
        </div>
        <button
          v-for="key in filterKeys"
          :key="key.value"
          @mousedown.prevent="selectFilterKey(key.value)"
          class="w-full text-left px-3 py-2 text-sm hover:bg-background-primary/50 flex items-center justify-between"
        >
          <span>
            <span class="text-gray-400">{{ key.value }}</span>
            <span class="text-gray-500 ml-1">in</span>
          </span>
          <span class="text-xs text-gray-500">{{ key.description }}</span>
        </button>
      </div>
      
      <!-- Filter value suggestions -->
      <div v-else-if="currentFilter.key">
        <div class="px-3 py-2 text-xs text-gray-500 border-b border-card-border">
          {{ currentFilter.key }} values
        </div>
        <button
          v-for="value in currentSuggestions"
          :key="value"
          @mousedown.prevent="selectFilterValue(value)"
          class="w-full text-left px-3 py-2 text-sm hover:bg-background-primary/50 flex items-center"
        >
          <Badge
            v-if="currentFilter.key === 'state'"
            :variant="getStateVariant(value)"
            class="text-xs normal-case"
          >
            {{ formatStateValue(value) }}
          </Badge>
          <span v-else>{{ value }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { Badge } from '@/components/ui/badge'
import type { BadgeVariants } from '@/components/ui/badge'
import { Search } from 'lucide-vue-next'
import FilterBadge from '~/components/FilterBadge.vue'

interface Filter {
  key: string
  value: string
}

const props = defineProps<{
  modelValue: string
  filters: Filter[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'update:filters': [filters: Filter[]]
}>()

const inputRef = ref<HTMLInputElement>()
const showSuggestions = ref(false)
const currentInput = ref('')
const activeFilters = ref<Filter[]>(props.filters || [])
const currentFilter = ref<{ key: string | null, partial: string }>({ key: null, partial: '' })

// Available filter keys
const filterKeys = [
  { value: 'state', description: 'Filter by task state' },
]

// State values for autocomplete
const stateValues = [
  'PENDING',
  'RECEIVED', 
  'RUNNING',
  'SUCCESS',
  'FAILED',
  'RETRY',
  'REVOKED'
]

const getStateVariant = (state: string): BadgeVariants['variant'] => {
  const variants: Record<string, BadgeVariants['variant']> = {
    'SUCCESS': 'success',
    'RUNNING': 'running',
    'PENDING': 'pending',
    'RECEIVED': 'received',
    'FAILED': 'failed',
    'RETRY': 'retry',
    'REVOKED': 'revoked'
  }
  return variants[state] || 'outline'
}

const formatStateValue = (state: string): string => {
  return state.charAt(0).toUpperCase() + state.slice(1).toLowerCase()
}

// Get suggestions based on current filter being typed
const currentSuggestions = computed(() => {
  if (!currentFilter.value.key) return []
  
  if (currentFilter.value.key === 'state') {
    const partial = currentFilter.value.partial.toUpperCase()
    return stateValues.filter(s => s.startsWith(partial))
  }
  
  return []
})

// Get filter key suggestions
const suggestions = computed(() => {
  if (!currentInput.value) {
    return filterKeys
  }
  
  const input = currentInput.value.toLowerCase()
  return filterKeys.filter(k => k.value.toLowerCase().includes(input))
})

const handleInput = (event: Event) => {
  const value = (event.target as HTMLInputElement).value
  currentInput.value = value
  
  // Check if user is typing a filter (word followed by colon)
  const filterMatch = value.match(/^(\w+):(.*)$/)
  if (filterMatch) {
    const [, key, partial] = filterMatch
    const validKey = filterKeys.find(k => k.value === key.toLowerCase())
    if (validKey) {
      currentFilter.value = { key: validKey.value, partial: partial.trim() }
    }
  } else {
    currentFilter.value = { key: null, partial: '' }
    // If no filter pattern, treat as regular search
    if (activeFilters.value.length === 0) {
      emit('update:modelValue', value)
    }
  }
  
  showSuggestions.value = true
}

const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && currentFilter.value.key && currentFilter.value.partial) {
    // Add the filter
    addFilter(currentFilter.value.key, currentFilter.value.partial)
    event.preventDefault()
  } else if (event.key === 'Escape') {
    showSuggestions.value = false
  } else if (event.key === 'Backspace' && !currentInput.value && activeFilters.value.length > 0) {
    // Remove last filter if backspace on empty input
    removeFilter(activeFilters.value.length - 1)
  }
}

const handleBlur = () => {
  // Delay to allow click on suggestions
  setTimeout(() => {
    showSuggestions.value = false
  }, 200)
}

const selectFilterKey = (key: string) => {
  currentInput.value = `${key}: `
  currentFilter.value = { key, partial: '' }
  nextTick(() => {
    inputRef.value?.focus()
  })
}

const selectFilterValue = (value: string) => {
  if (currentFilter.value.key) {
    addFilter(currentFilter.value.key, value)
  }
}

const addFilter = (key: string, value: string) => {
  const newFilter = { key, value }
  
  // Check if this filter already exists
  const exists = activeFilters.value.some(f => f.key === key && f.value === value)
  if (!exists) {
    activeFilters.value.push(newFilter)
    emit('update:filters', activeFilters.value)
  }
  
  // Clear input
  currentInput.value = ''
  currentFilter.value = { key: null, partial: '' }
  nextTick(() => {
    inputRef.value?.focus()
  })
}

const removeFilter = (index: number) => {
  activeFilters.value.splice(index, 1)
  emit('update:filters', activeFilters.value)
  nextTick(() => {
    inputRef.value?.focus()
  })
}

// Watch for external filter changes
watch(() => props.filters, (newFilters) => {
  if (newFilters) {
    activeFilters.value = [...newFilters]
  }
})

// Watch for external search changes
watch(() => props.modelValue, (newValue) => {
  if (newValue !== currentInput.value && activeFilters.value.length === 0) {
    currentInput.value = newValue || ''
  }
})
</script>
