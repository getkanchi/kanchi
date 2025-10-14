<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Input } from '~/components/ui/input'
import { cn } from '@/lib/utils'

interface TimePickerProps {
  modelValue?: { hour: number; minute: number }
  disabled?: boolean
}

const props = withDefaults(defineProps<TimePickerProps>(), {
  modelValue: () => ({ hour: 0, minute: 0 }),
  disabled: false
})

const emit = defineEmits<{
  'update:modelValue': [value: { hour: number; minute: number }]
}>()

const hourInput = ref<string>(String(props.modelValue.hour).padStart(2, '0'))
const minuteInput = ref<string>(String(props.modelValue.minute).padStart(2, '0'))

watch(() => props.modelValue, (newVal) => {
  hourInput.value = String(newVal.hour).padStart(2, '0')
  minuteInput.value = String(newVal.minute).padStart(2, '0')
})

function validateAndUpdateHour() {
  let hour = parseInt(hourInput.value) || 0
  hour = Math.max(0, Math.min(23, hour))
  hourInput.value = String(hour).padStart(2, '0')
  emit('update:modelValue', { hour, minute: parseInt(minuteInput.value) || 0 })
}

function validateAndUpdateMinute() {
  let minute = parseInt(minuteInput.value) || 0
  minute = Math.max(0, Math.min(59, minute))
  minuteInput.value = String(minute).padStart(2, '0')
  emit('update:modelValue', { hour: parseInt(hourInput.value) || 0, minute })
}

function incrementHour() {
  if (props.disabled) return
  let hour = (parseInt(hourInput.value) || 0) + 1
  if (hour > 23) hour = 0
  hourInput.value = String(hour).padStart(2, '0')
  validateAndUpdateHour()
}

function decrementHour() {
  if (props.disabled) return
  let hour = (parseInt(hourInput.value) || 0) - 1
  if (hour < 0) hour = 23
  hourInput.value = String(hour).padStart(2, '0')
  validateAndUpdateHour()
}

function incrementMinute() {
  if (props.disabled) return
  let minute = (parseInt(minuteInput.value) || 0) + 1
  if (minute > 59) minute = 0
  minuteInput.value = String(minute).padStart(2, '0')
  validateAndUpdateMinute()
}

function decrementMinute() {
  if (props.disabled) return
  let minute = (parseInt(minuteInput.value) || 0) - 1
  if (minute < 0) minute = 59
  minuteInput.value = String(minute).padStart(2, '0')
  validateAndUpdateMinute()
}
</script>

<template>
  <div class="flex items-center gap-2">
    <div class="flex flex-col items-center">
      <button
        type="button"
        :disabled="disabled"
        @click="incrementHour"
        class="px-2 py-1 text-xs rounded hover:bg-background-hover disabled:opacity-50 disabled:cursor-not-allowed"
      >
        ▲
      </button>
      <Input
        v-model="hourInput"
        :disabled="disabled"
        type="text"
        maxlength="2"
        class="w-14 text-center"
        @blur="validateAndUpdateHour"
        @keypress.enter="validateAndUpdateHour"
      />
      <button
        type="button"
        :disabled="disabled"
        @click="decrementHour"
        class="px-2 py-1 text-xs rounded hover:bg-background-hover disabled:opacity-50 disabled:cursor-not-allowed"
      >
        ▼
      </button>
    </div>
    <span class="text-lg font-semibold">:</span>
    <div class="flex flex-col items-center">
      <button
        type="button"
        :disabled="disabled"
        @click="incrementMinute"
        class="px-2 py-1 text-xs rounded hover:bg-background-hover disabled:opacity-50 disabled:cursor-not-allowed"
      >
        ▲
      </button>
      <Input
        v-model="minuteInput"
        :disabled="disabled"
        type="text"
        maxlength="2"
        class="w-14 text-center"
        @blur="validateAndUpdateMinute"
        @keypress.enter="validateAndUpdateMinute"
      />
      <button
        type="button"
        :disabled="disabled"
        @click="decrementMinute"
        class="px-2 py-1 text-xs rounded hover:bg-background-hover disabled:opacity-50 disabled:cursor-not-allowed"
      >
        ▼
      </button>
    </div>
  </div>
</template>
