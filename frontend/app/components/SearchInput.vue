<template>
  <div class="relative max-w-2xl w-full">
    <!-- Main input container with flex layout -->
    <div class="relative flex items-center gap-1 px-2 border border-border focus-within:ring-gray-700 rounded-md bg-background-surface/50 focus-within:ring-1">
      <!-- Search icon -->
      <Search class="h-4 w-4 text-muted-foreground flex-shrink-0 mx-2" />

      <!-- Filter badges -->
      <div v-if="activeFilters.length > 0 || currentFilter.field" class="flex items-center gap-1 flex-shrink-0 flex-wrap py-1">
        <!-- Completed filters -->
        <FilterBadge
          v-for="(filter, index) in activeFilters"
          :key="`${filter.field}-${filter.operator}-${filter.values.join(',')}`"
          :filter="filter"
          @remove="removeFilter(index)"
        />

        <!-- In-progress filter pill -->
        <div
          v-if="currentFilter.field"
          class="inline-flex items-center h-6 rounded-md bg-background-surface/80 border border-border text-xs font-mono whitespace-nowrap overflow-hidden"
        >
          <!-- Field segment (completed) -->
          <div class="px-2.5 py-1 text-text-primary border-r border-[hsl(0,0%,15%)]">
            {{ currentFilter.field }}
          </div>

          <!-- Operator segment -->
          <div
            v-if="currentFilter.operator"
            class="px-2 py-1 text-text-primary text-[10px] border-r border-[hsl(0,0%,15%)]"
          >
            {{ formatOperator(currentFilter.operator) }}
          </div>
          <div
            v-else-if="filterStage === 'operator'"
            class="px-2 py-1 text-text-muted text-[10px] border-r border-[hsl(0,0%,15%)] animate-pulse"
          >
            ...
          </div>

          <!-- Values segment -->
          <div
            v-if="currentFilter.values.length > 0 || (currentFilter.operator && filterStage === 'value')"
            class="px-2.5 py-1 flex items-center gap-1"
          >
            <template v-if="currentFilter.values.length > 0">
              <!-- State values with colored badges -->
              <template v-if="currentFilter.field === 'state'">
                <Badge
                  v-for="(value, index) in currentFilter.values"
                  :key="index"
                  :variant="getStatusVariant(value)"
                  class="text-xs px-1 py-0 h-4 normal-case"
                >
                  {{ formatStatus(value) }}
                </Badge>
              </template>
              <!-- UUID values - truncated -->
              <template v-else-if="currentFilter.field === 'id'">
                <span
                  v-for="(value, index) in currentFilter.values"
                  :key="index"
                  class="font-mono text-[10px] text-text-primary bg-background-raised px-1 py-0.5 rounded"
                  :title="value"
                >
                  {{ value.length <= 8 ? value : `${value.substring(0, 8)}...` }}
                </span>
              </template>
              <!-- Regular text values -->
              <template v-else>
                <span v-for="(value, index) in currentFilter.values" :key="index" class="text-text-primary">
                  {{ value }}<span v-if="index < currentFilter.values.length - 1" class="text-text-muted">,</span>
                </span>
              </template>
            </template>
            <span v-else class="text-text-muted animate-pulse">...</span>
          </div>
        </div>
      </div>

      <!-- Actual input field -->
      <input
        ref="inputRef"
        type="text"
        :placeholder="activeFilters.length > 0 || currentFilter.field ? '' : 'Search or filter for state, worker, task and more'"
        class="flex-1 bg-transparent border-0 outline-0 text-sm min-w-0 h-8 py-1"
        :value="currentFilter.field ? currentFilter.partial : currentInput"
        @input="handleInput"
        @keydown="handleKeydown"
        @focus="handleFocus"
        @blur="handleBlur"
      />
    </div>

    <!-- Autocomplete dropdown -->
    <div
      v-if="showSuggestions && (filteredFieldSuggestions.length > 0 || filteredOperatorSuggestions.length > 0 || filterStage === 'value')"
      class="absolute top-full mt-1 w-full bg-background-surface border border-border rounded-md shadow-lg z-50 max-h-60 overflow-y-auto"
    >
      <!-- Field suggestions -->
      <div v-if="filterStage === 'field' && filteredFieldSuggestions.length > 0">
        <div class="px-3 py-2 text-xs text-gray-500 border-b border-border sticky top-0 bg-background-surface">
          Filter by
        </div>
        <button
          v-for="(field, index) in filteredFieldSuggestions"
          :key="field.value"
          @mousedown.prevent="selectField(field.value)"
          :class="[
            'w-full text-left px-3 py-2 text-sm hover:bg-background-hover-subtle flex items-center justify-between transition-colors',
            index === selectedSuggestionIndex ? 'bg-background-hover-subtle' : ''
          ]"
        >
          <span>
            <span class="text-gray-300">{{ field.label }}</span>
          </span>
          <span class="text-xs text-gray-500">{{ field.description }}</span>
        </button>
      </div>

      <!-- Operator suggestions -->
      <div v-else-if="filterStage === 'operator' && filteredOperatorSuggestions.length > 0">
        <div class="px-3 py-2 text-xs text-gray-500 border-b border-border sticky top-0 bg-background-surface">
          Choose operator for <span class="text-gray-300">{{ currentFilter.field }}</span>
        </div>
        <button
          v-for="(op, index) in filteredOperatorSuggestions"
          :key="op.value"
          @mousedown.prevent="selectOperator(op.value)"
          :class="[
            'w-full text-left px-3 py-2 text-sm hover:bg-background-hover-subtle flex items-center justify-between transition-colors',
            index === selectedSuggestionIndex ? 'bg-background-hover-subtle' : ''
          ]"
        >
          <span class="text-gray-300">{{ op.label }}</span>
          <span class="text-xs text-gray-500">{{ op.description }}</span>
        </button>
      </div>

      <!-- Value suggestions -->
      <div v-else-if="filterStage === 'value'">
        <!-- Show suggestions if we have them -->
        <div v-if="filteredValueSuggestions.length > 0">
          <div class="px-3 py-2 text-xs text-gray-500 border-b border-border sticky top-0 bg-background-surface">
            Select value{{currentFilter.operator === 'in' || currentFilter.operator === 'not_in' ? 's' : ''}} for <span class="text-gray-300">{{ currentFilter.field }}</span>
          </div>
          <button
            v-for="(value, index) in filteredValueSuggestions"
            :key="value"
            @mousedown.prevent="selectValue(value)"
            :class="[
              'w-full text-left px-3 py-2 text-sm hover:bg-background-hover-subtle flex items-center transition-colors',
              index === selectedSuggestionIndex ? 'bg-background-hover-subtle' : ''
            ]"
          >
            <Badge
              v-if="currentFilter.field === 'state'"
              :variant="getStatusVariant(value)"
              class="text-xs normal-case"
            >
              {{ formatStatus(value) }}
            </Badge>
            <span v-else class="text-gray-300">{{ value }}</span>
          </button>
        </div>
        <!-- Show hint if no suggestions available -->
        <div v-else class="px-3 py-2 text-xs text-gray-400">
          <div class="mb-1">Type a value and press <kbd class="px-1.5 py-0.5 text-[10px] bg-gray-700 rounded border border-gray-600">Enter</kbd> to add filter</div>
          <div v-if="currentFilter.operator === 'in' || currentFilter.operator === 'not_in'" class="text-gray-500">
            Use commas to separate multiple values
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { Badge } from '@/components/ui/badge'
import { Search } from 'lucide-vue-next'
import FilterBadge from '~/components/FilterBadge.vue'
import type { ParsedFilter, FilterField, FilterOperator } from '~/composables/useFilterParser'

const props = defineProps<{
  modelValue: string
  filters: ParsedFilter[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'update:filters': [filters: ParsedFilter[]]
}>()

const inputRef = ref<HTMLInputElement>()
const showSuggestions = ref(false)
const currentInput = ref('')
const activeFilters = ref<ParsedFilter[]>(props.filters || [])
const selectedSuggestionIndex = ref(0)

// Current filter being built
const currentFilter = ref<{
  field: FilterField | null
  operator: FilterOperator | null
  values: string[]
  partial: string
}>({
  field: null,
  operator: null,
  values: [],
  partial: ''
})

// Determine what stage of filter building we're in
type FilterStage = 'field' | 'operator' | 'value'
const filterStage = computed<FilterStage>(() => {
  if (!currentFilter.value.field) return 'field'
  if (!currentFilter.value.operator) return 'operator'
  return 'value'
})

const {
  filterFields,
  operatorLabels,
  parseFilter,
  filtersToQueryString,
  getOperatorsForField,
  getSuggestionsForField,
  isUUID,
  formatOperator
} = useFilterParser()

const { getStatusVariant, formatStatus } = useTaskStatus()

// Filter suggestions based on current input
const filteredFieldSuggestions = computed(() => {
  const input = currentFilter.value.partial.toLowerCase()
  if (!input) return filterFields
  return filterFields.filter(f =>
    f.value.toLowerCase().includes(input) ||
    f.label.toLowerCase().includes(input)
  )
})

const filteredOperatorSuggestions = computed(() => {
  if (!currentFilter.value.field) return []
  const operators = getOperatorsForField(currentFilter.value.field)
  const input = currentFilter.value.partial.toLowerCase()

  const opsList = operators.map(op => ({
    value: op,
    label: operatorLabels[op].label,
    description: operatorLabels[op].description
  }))

  if (!input) return opsList
  return opsList.filter(op =>
    op.value.toLowerCase().includes(input) ||
    op.label.toLowerCase().includes(input)
  )
})

const filteredValueSuggestions = computed(() => {
  if (!currentFilter.value.field) return []
  const suggestions = getSuggestionsForField(currentFilter.value.field)
  const input = currentFilter.value.partial.toLowerCase()

  if (!input) return suggestions
  return suggestions.filter(s => s.toLowerCase().includes(input))
})

// Reset suggestion index when suggestions change
watch([filteredFieldSuggestions, filteredOperatorSuggestions, filteredValueSuggestions], () => {
  selectedSuggestionIndex.value = 0
})

const handleInput = (event: Event) => {
  const value = (event.target as HTMLInputElement).value

  // If we're already building a filter (field is set), just update the partial
  if (currentFilter.value.field) {
    currentFilter.value.partial = value
    currentInput.value = value
    showSuggestions.value = true
    return
  }

  // Otherwise, parse from scratch (user is typing a new filter or search)
  currentInput.value = value

  // Parse the current input to determine filter stage
  const parts = value.split(':')

  if (parts.length === 1) {
    // Still typing field
    currentFilter.value = {
      field: null,
      operator: null,
      values: [],
      partial: parts[0].trim()
    }
  } else if (parts.length === 2) {
    // Field entered, typing operator or value (if operator is default 'is')
    const field = parts[0].trim().toLowerCase() as FilterField
    const fieldExists = filterFields.find(f => f.value === field)

    if (fieldExists) {
      currentFilter.value = {
        field,
        operator: null,
        values: [],
        partial: parts[1].trim()
      }
    }
  } else if (parts.length >= 3) {
    // Field and operator entered, typing value
    const field = parts[0].trim().toLowerCase() as FilterField
    const operator = parts[1].trim().toLowerCase() as FilterOperator
    const valueStr = parts.slice(2).join(':').trim()

    const fieldExists = filterFields.find(f => f.value === field)
    if (fieldExists) {
      currentFilter.value = {
        field,
        operator,
        values: [],
        partial: valueStr
      }
    }
  }

  showSuggestions.value = true

  // Emit regular search if no filter pattern detected
  if (!value.includes(':')) {
    emit('update:modelValue', value)
  }
}

const handleKeydown = (event: KeyboardEvent) => {
  if (showSuggestions.value) {
    const suggestions =
      filterStage.value === 'field' ? filteredFieldSuggestions.value :
      filterStage.value === 'operator' ? filteredOperatorSuggestions.value :
      filteredValueSuggestions.value

    if (event.key === 'ArrowDown') {
      event.preventDefault()
      selectedSuggestionIndex.value = Math.min(selectedSuggestionIndex.value + 1, suggestions.length - 1)
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      selectedSuggestionIndex.value = Math.max(selectedSuggestionIndex.value - 1, 0)
    } else if (event.key === 'Enter') {
      event.preventDefault()

      if (suggestions.length > 0) {
        // Select highlighted suggestion
        if (filterStage.value === 'field') {
          selectField(filteredFieldSuggestions.value[selectedSuggestionIndex.value].value)
        } else if (filterStage.value === 'operator') {
          selectOperator(filteredOperatorSuggestions.value[selectedSuggestionIndex.value].value)
        } else if (filterStage.value === 'value') {
          selectValue(filteredValueSuggestions.value[selectedSuggestionIndex.value])
        }
      } else if (currentFilter.value.field && currentFilter.value.operator && currentFilter.value.partial) {
        // No suggestions but we have a complete filter, add it
        addFilter()
      }
    } else if (event.key === 'Escape') {
      showSuggestions.value = false
    }
  }

  if (event.key === 'Backspace') {
    // If building a filter and partial is empty, go back a stage
    if (currentFilter.value.field && currentFilter.value.partial === '') {
      event.preventDefault()
      if (currentFilter.value.operator) {
        // At value stage, go back to operator stage
        if (currentFilter.value.values.length > 0) {
          // If there are values (multi-value operator), remove last value
          currentFilter.value.values.pop()
        } else {
          // Otherwise go back to operator selection
          currentFilter.value.operator = null
        }
      } else {
        // At operator stage, go back to field stage (clear filter)
        currentFilter.value = {
          field: null,
          operator: null,
          values: [],
          partial: ''
        }
        currentInput.value = ''
      }
    } else if (!currentFilter.value.field && !currentInput.value && activeFilters.value.length > 0) {
      // Not building a filter and input is empty, remove last completed filter
      removeFilter(activeFilters.value.length - 1)
    }
  }
}

const handleFocus = () => {
  // Only show suggestions if there's input or a filter being built
  if (currentInput.value || currentFilter.value.field) {
    showSuggestions.value = true
  }
}

const handleBlur = () => {
  // Delay to allow click on suggestions
  setTimeout(() => {
    showSuggestions.value = false
  }, 200)
}

const selectField = (field: FilterField) => {
  currentInput.value = ''
  currentFilter.value = {
    field,
    operator: null,
    values: [],
    partial: ''
  }
  selectedSuggestionIndex.value = 0
  showSuggestions.value = true
  nextTick(() => {
    inputRef.value?.focus()
  })
}

const selectOperator = (operator: FilterOperator) => {
  if (!currentFilter.value.field) return

  currentInput.value = ''
  currentFilter.value = {
    ...currentFilter.value,
    operator,
    partial: ''
  }
  selectedSuggestionIndex.value = 0
  showSuggestions.value = true
  nextTick(() => {
    inputRef.value?.focus()
  })
}

const selectValue = (value: string) => {
  if (!currentFilter.value.field || !currentFilter.value.operator) return

  // For multi-value operators, allow adding multiple values
  if (currentFilter.value.operator === 'in' || currentFilter.value.operator === 'not_in') {
    currentFilter.value.values.push(value)
    currentInput.value = ''
    currentFilter.value.partial = ''
    showSuggestions.value = true
  } else {
    // For single-value operators, complete the filter
    currentFilter.value.values = [value]
    addFilter()
  }

  nextTick(() => {
    inputRef.value?.focus()
  })
}

const addFilter = () => {
  if (!currentFilter.value.field || !currentFilter.value.operator) return

  // Get values - either from values array or from partial input
  let values = currentFilter.value.values
  if (values.length === 0 && currentFilter.value.partial) {
    // Parse values from partial input (might be comma-separated)
    if (currentFilter.value.operator === 'in' || currentFilter.value.operator === 'not_in') {
      values = currentFilter.value.partial.split(',').map(v => v.trim()).filter(v => v)
    } else {
      values = [currentFilter.value.partial]
    }
  }

  if (values.length === 0) return

  const newFilter: ParsedFilter = {
    field: currentFilter.value.field,
    operator: currentFilter.value.operator,
    values,
    raw: filtersToQueryString([{
      field: currentFilter.value.field,
      operator: currentFilter.value.operator,
      values,
      raw: ''
    }])
  }

  // Check if filter already exists
  const exists = activeFilters.value.some(f =>
    f.field === newFilter.field &&
    f.operator === newFilter.operator &&
    JSON.stringify(f.values.sort()) === JSON.stringify(newFilter.values.sort())
  )

  if (!exists) {
    activeFilters.value.push(newFilter)
    emit('update:filters', activeFilters.value)
  }

  // Reset
  currentInput.value = ''
  currentFilter.value = {
    field: null,
    operator: null,
    values: [],
    partial: ''
  }
  selectedSuggestionIndex.value = 0
  showSuggestions.value = false
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
}, { deep: true })

// Watch for external search changes
watch(() => props.modelValue, (newValue) => {
  if (newValue !== currentInput.value && activeFilters.value.length === 0) {
    currentInput.value = newValue || ''
  }
})
</script>
