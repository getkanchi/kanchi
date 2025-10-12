<script setup lang="ts">
import { CalendarRoot, type CalendarRootEmits, type CalendarRootProps, useForwardPropsEmits } from 'reka-ui'
import { Calendar, type DateValue } from '@internationalized/date'
import { cn } from '@/lib/utils'

const props = withDefaults(
  defineProps<CalendarRootProps>(),
  {
    locale: 'en-US',
    fixedWeeks: true,
    weekdayFormat: 'short',
    weekStartsOn: 0,
  }
)

const emits = defineEmits<CalendarRootEmits>()

const forwarded = useForwardPropsEmits(props, emits)
</script>

<template>
  <CalendarRoot
    v-slot="{ grid, weekDays }"
    :class="cn('rounded-lg border border-border bg-background-surface p-3', $attrs.class ?? '')"
    v-bind="forwarded"
  >
    <div class="flex flex-col gap-y-4 sm:flex-row sm:gap-x-4 sm:gap-y-0">
      <div
        v-for="month in grid"
        :key="month.value.toString()"
        class="space-y-4"
      >
        <div class="flex items-center justify-between">
          <div class="text-sm font-medium text-text-primary">
            {{ month.value.month }} {{ month.value.year }}
          </div>
        </div>
        <table class="w-full border-collapse space-y-1">
          <thead>
            <tr class="flex">
              <th
                v-for="day in weekDays"
                :key="day"
                class="w-9 rounded-md text-[0.8rem] font-normal text-text-muted"
              >
                {{ day }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(weekDates, index) in month.rows"
              :key="`weekDate-${index}`"
              class="mt-2 flex w-full"
            >
              <td
                v-for="weekDate in weekDates"
                :key="weekDate.toString()"
                class="relative p-0 text-center text-sm focus-within:relative focus-within:z-20 [&:has([data-selected])]:bg-background-selected [&:has([data-selected][data-outside-month])]:bg-background-surface/50"
              >
                <button
                  :data-selected="weekDate.isSelected ? '' : undefined"
                  :data-disabled="weekDate.isDisabled ? '' : undefined"
                  :data-unavailable="weekDate.isUnavailable ? '' : undefined"
                  :data-today="weekDate.isToday ? '' : undefined"
                  :data-outside-month="weekDate.isOutsideMonth ? '' : undefined"
                  :class="cn(
                    'inline-flex h-9 w-9 items-center justify-center rounded-md p-0 text-sm font-normal ring-offset-background-base transition-colors',
                    'hover:bg-background-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2',
                    'disabled:pointer-events-none disabled:opacity-50',
                    weekDate.isToday ? 'bg-background-surface text-text-primary font-semibold' : '',
                    weekDate.isSelected ? 'bg-primary text-white hover:bg-primary-hover' : '',
                    weekDate.isOutsideMonth ? 'text-text-muted opacity-50' : '',
                    weekDate.isDisabled ? 'text-text-disabled line-through' : '',
                  )"
                  @click="weekDate.trigger"
                >
                  {{ weekDate.day }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </CalendarRoot>
</template>
