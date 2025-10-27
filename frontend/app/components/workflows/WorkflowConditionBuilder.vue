<template>
  <div>
    <div v-if="!conditions || conditions.conditions.length === 0" class="border-2 border-dashed border-border rounded-lg p-6 text-center">
      <Filter class="h-8 w-8 text-text-muted mx-auto mb-2" />
      <p class="text-sm text-text-secondary mb-3">No conditions (workflow will always execute)</p>
      <Button size="sm" variant="outline" @click="addCondition">
        <Plus class="h-3.5 w-3.5 mr-1.5" />
        Add Condition
      </Button>
    </div>

    <div v-else class="space-y-3">
      <!-- Operator Toggle -->
      <div class="flex items-center gap-2 mb-2">
        <span class="text-xs text-text-muted">Match</span>
        <Select :model-value="conditions.operator" @update:model-value="updateOperator" class="w-20 h-7 text-xs" size="sm">
          <option value="AND">ALL</option>
          <option value="OR">ANY</option>
        </Select>
        <span class="text-xs text-text-muted">conditions</span>
      </div>

      <!-- Conditions List -->
      <div class="space-y-2">
        <div
          v-for="(condition, index) in conditions.conditions"
          :key="index"
          class="border border-border rounded-lg p-3 bg-background-raised"
        >
          <div class="flex items-start gap-2">
            <div class="flex-1 grid grid-cols-[1fr_auto_1fr] gap-2 items-center">
              <!-- Field -->
              <Select :model-value="condition.field" @update:model-value="updateConditionField(index, $event)" class="h-8 text-xs" size="sm">
                <option v-for="field in availableFields" :key="field.value" :value="field.value">
                  {{ field.label }}
                </option>
              </Select>

              <!-- Operator -->
              <Select :model-value="condition.operator" @update:model-value="updateConditionOperator(index, $event)" class="h-8 text-xs w-32" size="sm">
                <option v-for="op in operators" :key="op.value" :value="op.value">
                  {{ op.label }}
                </option>
              </Select>

              <!-- Value -->
              <Input
                :value="condition.value"
                @input="updateConditionValue(index, ($event.target as HTMLInputElement).value)"
                placeholder="Value"
                class="h-8 text-xs"
              />
            </div>

            <!-- Remove Button -->
            <Button
              variant="ghost"
              size="sm"
              class="h-8 w-8 p-0"
              @click="removeCondition(index)"
            >
              <X class="h-3.5 w-3.5 text-status-error" />
            </Button>
          </div>
        </div>
      </div>

      <!-- Add Condition Button -->
      <Button size="sm" variant="outline" @click="addCondition" class="w-full">
        <Plus class="h-3.5 w-3.5 mr-1.5" />
        Add Condition
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Plus, X, Filter } from 'lucide-vue-next'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import Select from '~/components/common/Select.vue'
import type { ConditionGroup, Condition } from '~/types/workflow'

const props = defineProps<{
  conditions?: ConditionGroup
}>()

const emit = defineEmits<{
  'update:conditions': [conditions?: ConditionGroup]
}>()

// Available fields (from WORKFLOW_SYSTEM_PLAN.md context fields)
const availableFields = [
  { value: 'task_name', label: 'Task Name' },
  { value: 'task_id', label: 'Task ID' },
  { value: 'root_id', label: 'Root ID (Task Chain)' },
  { value: 'parent_id', label: 'Parent ID' },
  { value: 'queue', label: 'Queue' },
  { value: 'routing_key', label: 'Routing Key' },
  { value: 'retry_count', label: 'Retry Count' },
  { value: 'exception', label: 'Exception' },
  { value: 'runtime', label: 'Runtime (seconds)' },
  { value: 'hostname', label: 'Hostname' },
  { value: 'worker_name', label: 'Worker Name' },
  { value: 'event_type', label: 'Event Type' },
  { value: 'state', label: 'State' }
]

// Available operators
const operators = [
  { value: 'equals', label: 'equals' },
  { value: 'not_equals', label: 'not equals' },
  { value: 'contains', label: 'contains' },
  { value: 'matches', label: 'matches (regex)' },
  { value: 'starts_with', label: 'starts with' },
  { value: 'ends_with', label: 'ends with' },
  { value: 'gt', label: '>' },
  { value: 'gte', label: '>=' },
  { value: 'lt', label: '<' },
  { value: 'lte', label: '<=' },
  { value: 'in', label: 'in list' },
  { value: 'not_in', label: 'not in list' }
]

function addCondition() {
  const newCondition: Condition = {
    field: 'task_name',
    operator: 'equals',
    value: ''
  }

  if (!props.conditions) {
    emit('update:conditions', {
      operator: 'AND',
      conditions: [newCondition]
    })
  } else {
    emit('update:conditions', {
      ...props.conditions,
      conditions: [...props.conditions.conditions, newCondition]
    })
  }
}

function removeCondition(index: number) {
  if (!props.conditions) return

  const newConditions = props.conditions.conditions.filter((_, i) => i !== index)

  if (newConditions.length === 0) {
    emit('update:conditions', undefined)
  } else {
    emit('update:conditions', {
      ...props.conditions,
      conditions: newConditions
    })
  }
}

function updateOperator(operator: 'AND' | 'OR') {
  if (!props.conditions) return

  emit('update:conditions', {
    ...props.conditions,
    operator
  })
}

function updateConditionField(index: number, field: string) {
  if (!props.conditions) return

  const updated = [...props.conditions.conditions]
  updated[index] = { ...updated[index], field }

  emit('update:conditions', {
    ...props.conditions,
    conditions: updated
  })
}

function updateConditionOperator(index: number, operator: string) {
  if (!props.conditions) return

  const updated = [...props.conditions.conditions]
  updated[index] = { ...updated[index], operator: operator as any }

  emit('update:conditions', {
    ...props.conditions,
    conditions: updated
  })
}

function updateConditionValue(index: number, value: string) {
  if (!props.conditions) return

  const updated = [...props.conditions.conditions]
  const numericOperators = ['gt', 'gte', 'lt', 'lte']
  const parsedValue = numericOperators.includes(updated[index].operator) && !isNaN(Number(value))
    ? Number(value)
    : value

  updated[index] = { ...updated[index], value: parsedValue }

  emit('update:conditions', {
    ...props.conditions,
    conditions: updated
  })
}
</script>
