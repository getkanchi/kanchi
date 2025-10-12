<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { CalendarDays, X } from 'lucide-vue-next'
import { Popover, PopoverContent, PopoverTrigger } from '~/components/ui/popover'
import { Button } from '~/components/ui/button'
import BaseIconButton from '~/components/BaseIconButton.vue'
import {
  RangeCalendarRoot,
  RangeCalendarCell,
  RangeCalendarCellTrigger,
  RangeCalendarGrid,
  RangeCalendarGridBody,
  RangeCalendarGridHead,
  RangeCalendarGridRow,
  RangeCalendarHeadCell,
  RangeCalendarHeader,
  RangeCalendarHeading,
  RangeCalendarNext,
  RangeCalendarPrev
} from 'reka-ui'
import { CalendarDate } from '@internationalized/date'
import { cn } from '@/lib/utils'

const route = useRoute()
const router = useRouter()

export interface TimeRange {
  start: Date | null
  end: Date | null
}

interface TimeRangeFilterProps {
  modelValue?: TimeRange
  disabled?: boolean
}

const props = withDefaults(defineProps<TimeRangeFilterProps>(), {
  modelValue: () => ({ start: null, end: null }),
  disabled: false
})

const emit = defineEmits<{
  'update:modelValue': [value: TimeRange]
  'clear': []
  'disableLiveMode': []
}>()

const open = ref(false)

// Initialize from URL query params or props or current date
function getInitialDateRange() {
  // Try URL params first
  const startParam = route.query.start as string
  const endParam = route.query.end as string

  if (startParam && endParam) {
    try {
      const startDate = new Date(startParam)
      const endDate = new Date(endParam)
      if (!isNaN(startDate.getTime()) && !isNaN(endDate.getTime())) {
        return {
          start: new CalendarDate(startDate.getFullYear(), startDate.getMonth() + 1, startDate.getDate()),
          end: new CalendarDate(endDate.getFullYear(), endDate.getMonth() + 1, endDate.getDate())
        }
      }
    } catch (e) {
      console.warn('Invalid date params in URL:', e)
    }
  }

  // Fall back to props
  if (props.modelValue.start && props.modelValue.end) {
    return {
      start: new CalendarDate(
        props.modelValue.start.getFullYear(),
        props.modelValue.start.getMonth() + 1,
        props.modelValue.start.getDate()
      ),
      end: new CalendarDate(
        props.modelValue.end.getFullYear(),
        props.modelValue.end.getMonth() + 1,
        props.modelValue.end.getDate()
      )
    }
  }

  // Default to undefined so no date is selected initially
  return {
    start: undefined,
    end: undefined
  }
}

const dateRange = ref<{ start: CalendarDate | undefined; end: CalendarDate | undefined }>(getInitialDateRange())

// Max date is today (disable future dates)
const maxDate = computed(() => {
  const today = new Date()
  return new CalendarDate(today.getFullYear(), today.getMonth() + 1, today.getDate())
})

// Time inputs
const startTime = ref(
  props.modelValue.start
    ? `${String(props.modelValue.start.getHours()).padStart(2, '0')}:${String(props.modelValue.start.getMinutes()).padStart(2, '0')}`
    : '00:00'
)

const endTime = ref(
  props.modelValue.end
    ? `${String(props.modelValue.end.getHours()).padStart(2, '0')}:${String(props.modelValue.end.getMinutes()).padStart(2, '0')}`
    : '23:59'
)

// Display label for the button
const displayLabel = computed(() => {
  if (!props.modelValue.start || !props.modelValue.end) {
    return ''
  }

  // Check if it's a single day selection
  const isSameDay =
    props.modelValue.start.getFullYear() === props.modelValue.end.getFullYear() &&
    props.modelValue.start.getMonth() === props.modelValue.end.getMonth() &&
    props.modelValue.start.getDate() === props.modelValue.end.getDate()

  // Check if time is at default values (00:00 - 23:59)
  const isDefaultTime =
    props.modelValue.start.getHours() === 0 &&
    props.modelValue.start.getMinutes() === 0 &&
    props.modelValue.end.getHours() === 23 &&
    props.modelValue.end.getMinutes() === 59

  const formatDate = (date: Date, includeTime: boolean) => {
    if (includeTime) {
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } else {
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric'
      })
    }
  }

  // Single day selection
  if (isSameDay && isDefaultTime) {
    return formatDate(props.modelValue.start, false)
  } else if (isSameDay) {
    // Same day with different times
    const startTimeStr = props.modelValue.start.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    })
    const endTimeStr = props.modelValue.end.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    })
    return `${formatDate(props.modelValue.start, false)} (${startTimeStr} - ${endTimeStr})`
  }

  // Date range
  return `${formatDate(props.modelValue.start, !isDefaultTime)} - ${formatDate(props.modelValue.end, !isDefaultTime)}`
})

function parseTime(timeStr: string): { hour: number; minute: number } {
  const [hourStr, minuteStr] = timeStr.split(':')
  return {
    hour: Math.max(0, Math.min(23, parseInt(hourStr, 10) || 0)),
    minute: Math.max(0, Math.min(59, parseInt(minuteStr, 10) || 0))
  }
}

function handleDateRangeChange(value: any) {
  if (value) {
    dateRange.value = {
      start: value.start,
      end: value.end
    }
  }
}

function applyRange() {
  if (!dateRange.value.start) {
    return
  }

  const startTimeParsed = parseTime(startTime.value)
  const endTimeParsed = parseTime(endTime.value)

  const start = new Date(
    dateRange.value.start.year,
    dateRange.value.start.month - 1,
    dateRange.value.start.day,
    startTimeParsed.hour,
    startTimeParsed.minute,
    0,
    0
  )

  // If no end date selected, use the start date
  const endDate = dateRange.value.end || dateRange.value.start

  const end = new Date(
    endDate.year,
    endDate.month - 1,
    endDate.day,
    endTimeParsed.hour,
    endTimeParsed.minute,
    0,
    0
  )

  // Update URL query params
  router.push({
    query: {
      ...route.query,
      start: start.toISOString(),
      end: end.toISOString()
    }
  })
  emit('update:modelValue', { start, end })
  open.value = false
}

function clearRange() {
  dateRange.value = {
    start: undefined,
    end: undefined
  }
  startTime.value = '00:00'
  endTime.value = '23:59'

  // Clear URL query params
  const query = { ...route.query }
  delete query.start
  delete query.end
  router.push({ query })

  emit('clear')
  emit('update:modelValue', { start: null, end: null })
  open.value = false
}

// Handle button click - disable live mode if active
function handleButtonClick() {
  if (props.disabled) {
    emit('disableLiveMode')
  }
  open.value = true
}

// Handle clear button click
function handleClearClick() {
  clearRange()
}

// Initialize from URL on mount
onMounted(() => {
  const startParam = route.query.start as string
  const endParam = route.query.end as string

  if (startParam && endParam) {
    try {
      const start = new Date(startParam)
      const end = new Date(endParam)
      if (!isNaN(start.getTime()) && !isNaN(end.getTime())) {
        emit('update:modelValue', { start, end })
      }
    } catch (e) {
      console.warn('Invalid date params in URL:', e)
    }
  }
})
</script>

<template>
  <div class="flex items-center gap-1">
    <Popover v-model:open="open">
      <PopoverTrigger as-child>
        <Button
          variant="outline"
          @click="handleButtonClick"
          :class="[
            'justify-start text-left font-mono',
            modelValue.start && modelValue.end ? 'font-semibold' : 'font-normal',
            !modelValue.start && !modelValue.end && 'text-text-muted',
            disabled && 'opacity-60'
          ]"
        >
          <CalendarDays class="h-4 w-4" />
          {{ displayLabel }}
        </Button>
      </PopoverTrigger>
    <PopoverContent class="w-auto p-4 bg-background-raised border-border border" align="start">
      <div class="space-y-4" @keydown.enter="applyRange">
        <!-- Calendar -->
        <RangeCalendarRoot
          v-slot="{ grid, weekDays }"
          v-model="dateRange"
          locale="en-US"
          :number-of-months="1"
          :fixed-weeks="true"
          weekday-format="short"
          :week-starts-on="0"
          :max-value="maxDate"
          :class="cn('rounded-lg border border-border bg-background-raised p-3')"
          @update:model-value="handleDateRangeChange"
        >
          <RangeCalendarHeader class="flex items-center justify-between mb-4">
            <RangeCalendarPrev class="inline-flex h-7 w-7 items-center justify-center rounded-md p-0 hover:bg-background-hover text-text-primary">
              ‹
            </RangeCalendarPrev>
            <RangeCalendarHeading class="text-sm font-medium text-text-primary" />
            <RangeCalendarNext class="inline-flex h-7 w-7 items-center justify-center rounded-md p-0 hover:bg-background-hover text-text-primary">
              ›
            </RangeCalendarNext>
          </RangeCalendarHeader>
          <div>
            <RangeCalendarGrid
              v-for="month in grid"
              :key="month.value.toString()"
            >
              <RangeCalendarGridHead>
                <RangeCalendarGridRow class="flex">
                  <RangeCalendarHeadCell
                    v-for="day in weekDays"
                    :key="day"
                    class="w-9 rounded-md text-[0.8rem] font-normal text-text-muted"
                  >
                    {{ day }}
                  </RangeCalendarHeadCell>
                </RangeCalendarGridRow>
              </RangeCalendarGridHead>
              <RangeCalendarGridBody>
                <RangeCalendarGridRow
                  v-for="(weekDates, index) in month.rows"
                  :key="`weekDate-${index}`"
                  class="mt-2 flex w-full"
                >
                  <RangeCalendarCell
                    v-for="weekDate in weekDates"
                    :key="weekDate.toString()"
                    :date="weekDate"
                    class="relative p-0 text-center text-sm focus-within:relative focus-within:z-20 [&:has([data-selection-start])]:rounded-l-md [&:has([data-selection-end])]:rounded-r-md first:[&:has([data-selected])]:rounded-l-md last:[&:has([data-selected])]:rounded-r-md [&:has([data-selected])]:bg-primary-bg/50"
                  >
                    <RangeCalendarCellTrigger
                      :day="weekDate"
                      :month="month.value"
                      :class="cn(
                        'inline-flex h-9 w-9 items-center justify-center rounded-md p-0 text-sm font-normal transition-colors cursor-pointer font-mono',
                        'text-text-primary bg-transparent',
                        'hover:bg-background-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40',
                        'disabled:pointer-events-none disabled:opacity-50',
                        'data-[today]:text-primary data-[today]:bg-background-hover',
                        'data-[selected]:bg-primary-bg data-[selected]:text-primary data-[selected]:font-semibold',
                        'data-[selection-start]:bg-primary data-[selection-start]:text-white data-[selection-start]:font-bold data-[selection-end]:bg-primary data-[selection-end]:text-white data-[selection-end]:font-bold',
                        'data-[outside-month]:text-text-muted data-[outside-month]:opacity-60',
                        'data-[disabled]:text-text-disabled data-[disabled]:opacity-25'
                      )"
                    >
                      {{ weekDate.day }}
                    </RangeCalendarCellTrigger>
                  </RangeCalendarCell>
                </RangeCalendarGridRow>
              </RangeCalendarGridBody>
            </RangeCalendarGrid>
          </div>
        </RangeCalendarRoot>

        <!-- Time inputs -->
        <div class="flex items-center gap-3 pt-2">
          <div class="flex-1">
            <label class="text-xs text-text-muted mb-1 block">Start</label>
            <input
              v-model="startTime"
              type="time"
              class="w-full px-3 py-2 text-sm border border-border rounded-md bg-background-surface text-text-primary focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary font-mono"
            />
          </div>
          <div class="flex-1">
            <label class="text-xs text-text-muted mb-1 block">End</label>
            <input
              v-model="endTime"
              type="time"
              class="w-full px-3 py-2 text-sm border border-border rounded-md bg-background-surface text-text-primary focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary font-mono"
            />
          </div>
        </div>

        <!-- Action buttons -->
        <div class="flex items-center justify-end gap-2 pt-2">
          <Button
            variant="primary"
            @click="applyRange"
          >
            Apply
          </Button>
        </div>
      </div>
    </PopoverContent>
  </Popover>

  <BaseIconButton
    v-if="modelValue.start && modelValue.end"
    :icon="X"
    size="sm"
    variant="ghost"
    @click="handleClearClick"
    class="text-text-muted hover:text-text-primary"
  />
  </div>
</template>

<style scoped>
/* Hide time input controls (clock icons) */
input[type="time"]::-webkit-calendar-picker-indicator {
  display: none;
}

input[type="time"]::-webkit-inner-spin-button,
input[type="time"]::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

input[type="time"] {
  -moz-appearance: textfield;
}
</style>
