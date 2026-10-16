<template>
  <Popover v-model:open="editorOpen">
    <PopoverTrigger as-child>
      <Button type="button" variant="outline" class="h-8 shrink-0 gap-1.5 px-2" aria-label="Add filter" @click="changeField('state')">
        <ListFilter class="h-4 w-4" aria-hidden="true" />
        <span class="hidden sm:inline">Add filter</span>
      </Button>
    </PopoverTrigger>
    <PopoverContent
      align="end"
      :collision-padding="16"
      class="w-80 max-w-[calc(100vw-2rem)] max-h-[var(--reka-popover-content-available-height)] overflow-y-auto border-border bg-background-surface text-text-primary"
      aria-label="Add task filter"
    >
      <form class="space-y-4" @submit.prevent="applyFilter">
        <p class="text-sm font-medium">Add filter</p>
        <div class="grid grid-cols-2 gap-3">
          <div class="space-y-1.5">
            <label :for="id + '-field'" class="text-xs text-text-secondary">Field</label>
            <Select :id="id + '-field'" :model-value="field" class="h-10 w-full" @update:model-value="changeField">
              <option v-for="item in filterFields" :key="item.value" :value="item.value">{{ item.label }}</option>
            </Select>
          </div>
          <div class="space-y-1.5">
            <label :for="id + '-operator'" class="text-xs text-text-secondary">Condition</label>
            <Select :id="id + '-operator'" v-model="operator" class="h-10 w-full">
              <option v-for="item in operators" :key="item" :value="item">{{ operatorLabels[item].label }}</option>
            </Select>
          </div>
        </div>

        <fieldset v-if="field === 'state' && isMultiple" class="space-y-2">
          <legend class="text-xs text-text-secondary">States</legend>
          <div class="grid grid-cols-2 gap-1">
            <label v-for="state in states" :key="state" class="flex min-h-10 cursor-pointer items-center gap-2 rounded-md px-2 hover:bg-background-hover">
              <input v-model="selectedStates" type="checkbox" :value="state" class="h-4 w-4 accent-primary" />
              <Badge :variant="getStatusVariant(state)" class="normal-case">{{ formatStatus(state) }}</Badge>
            </label>
          </div>
          <p class="text-xs text-text-muted">Choose one or more states, then apply.</p>
        </fieldset>
        <div v-else-if="field === 'state'" class="space-y-1.5">
          <label :for="id + '-state'" class="text-xs text-text-secondary">State</label>
          <Select :id="id + '-state'" :model-value="selectedStates[0] || ''" class="h-10 w-full" @update:model-value="selectedStates = [String($event)]">
            <option value="" disabled>Select a state</option>
            <option v-for="state in states" :key="state" :value="state">{{ formatStatus(state) }}</option>
          </Select>
          <Badge v-if="selectedStates[0]" :variant="getStatusVariant(selectedStates[0])" class="normal-case">{{ formatStatus(selectedStates[0]) }}</Badge>
        </div>
        <div v-else class="space-y-1.5">
          <label :for="id + '-value'" class="text-xs text-text-secondary">{{ isMultiple ? 'Values' : 'Value' }}</label>
          <Input
            :id="id + '-value'"
            v-model="textValue"
            :placeholder="valuePlaceholder"
            :aria-describedby="valueError ? id + '-hint ' + id + '-error' : id + '-hint'"
            :aria-invalid="Boolean(valueError)"
            class="h-10"
          />
          <p :id="id + '-hint'" class="text-xs text-text-muted">{{ isMultiple ? 'Separate values with commas.' : operatorLabels[operator].description }}</p>
          <p v-if="valueError" :id="id + '-error'" role="alert" class="text-xs text-status-error">{{ valueError }}</p>
        </div>

        <div class="flex justify-end gap-2 border-t border-border pt-3">
          <Button type="button" variant="ghost" class="h-10" @click="editorOpen = false">Cancel</Button>
          <Button type="submit" class="h-10" :disabled="!canApply">Apply filter</Button>
        </div>
      </form>
    </PopoverContent>
  </Popover>
</template>

<script setup lang="ts">
import { computed, ref, useId } from 'vue'
import { ListFilter } from 'lucide-vue-next'
import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import { Input } from '~/components/ui/input'
import { Popover, PopoverContent, PopoverTrigger } from '~/components/ui/popover'
import { Select } from '~/components/common'
import type { ParsedFilter, FilterField, FilterOperator } from '~/composables/useFilterParser'

const props = defineProps<{ filters: ParsedFilter[] }>()
const emit = defineEmits<{ 'update:filters': [filters: ParsedFilter[]] }>()
const { filterFields, operatorLabels, getOperatorsForField, serializeFilter } = useFilterParser()
const { getAllStatuses, formatStatus, getStatusVariant } = useTaskStatus()
const id = useId()
const editorOpen = ref(false)
const field = ref<FilterField>('state')
const operator = ref<FilterOperator>('is')
const selectedStates = ref<string[]>([])
const textValue = ref('')
const states = getAllStatuses()
const operators = computed(() => getOperatorsForField(field.value))
const isMultiple = computed(() => operator.value === 'in' || operator.value === 'not_in')
const values = computed(() => {
  if (field.value === 'state') return isMultiple.value ? selectedStates.value : selectedStates.value.slice(0, 1)
  return isMultiple.value ? textValue.value.split(',').map(value => value.trim()) : [textValue.value.trim()]
})
const draftFilter = computed<ParsedFilter>(() => ({ field: field.value, operator: operator.value, values: values.value, raw: '' }))
const valueError = computed(() => {
  if (field.value === 'state') return ''
  if (textValue.value.includes(';')) return 'Semicolons cannot be used in a filter value.'
  if (isMultiple.value && textValue.value.trim() && values.value.some(value => !value)) return 'Enter a value between each comma.'
  return ''
})
const canApply = computed(() => !valueError.value && values.value.length > 0 && values.value.every(value => value.trim()))
const valuePlaceholder = computed(() => ({ worker: 'e.g. worker-prod', task: 'e.g. process_payment', queue: 'e.g. celery', id: 'Task ID', state: '' })[field.value])

function changeField(value: string | number) {
  field.value = value as FilterField
  operator.value = field.value === 'state' ? 'is' : 'contains'
  selectedStates.value = []
  textValue.value = ''
}

function applyFilter() {
  if (!canApply.value) return
  const filter = { ...draftFilter.value, values: [...new Set(values.value)] }
  filter.raw = serializeFilter(filter)
  const exists = props.filters.some(existing =>
    existing.field === filter.field && existing.operator === filter.operator &&
    new Set(existing.values).size === filter.values.length && existing.values.every(value => filter.values.includes(value))
  )
  if (!exists) emit('update:filters', [...props.filters, filter])
  editorOpen.value = false
}
</script>
