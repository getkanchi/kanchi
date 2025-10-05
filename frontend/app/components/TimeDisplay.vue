<!--
  TimeDisplay Component - Smart Contextual Time Display

  UX Design for Developer Monitoring Dashboard:

  Problem Solved:
  - Developers need both context ("how long ago?") and precision ("exact time with seconds")
  - Without dates, "14:30:45" is meaningless (is it today? yesterday? last week?)
  - Mental math required to calculate time elapsed
  - Inconsistent time display across different views

  Solution:
  - Dual-layer stacked display: Context (top) + Precision (bottom)
  - Smart contextual labels based on recency
  - Color-coded freshness (green = recent, gray = older)
  - Always shows seconds for log correlation
  - Auto-refreshes relative times every 10s
  - Responsive: stacked on desktop, inline on mobile
  - Full datetime tooltip on hover
  - ARIA labels for accessibility

  Format Rules:
  - 0-60s      → "30s ago" + "14:30:45"  (emerald-400)
  - 1-59m      → "15m ago" + "14:30:45"  (emerald-400)
  - 1-6h       → "2h ago" + "14:30:45"   (gray-300)
  - 6-24h      → "Today" + "14:30:45"    (gray-400)
  - Yesterday  → "Yesterday" + "14:30:45" (gray-500)
  - This week  → "Mon" + "14:30:45"      (gray-500)
  - This year  → "Jan 15" + "14:30:45"   (gray-500)
  - Older      → "Jan 15, 2024" + "14:30:45" (gray-600)

  Performance:
  - Memoized formatting via computed
  - Optional auto-refresh (can be disabled)
  - Cleanup on unmount

  Usage:
  <TimeDisplay
    :timestamp="task.timestamp"
    :auto-refresh="true"
    :refresh-interval="10000"
  />
-->
<template>
  <div
    class="time-display-container group/time"
    :title="timeData.fullDateTime"
    :aria-label="`Timestamp: ${timeData.fullDateTime}`"
  >
    <!-- Desktop: Stacked Layout -->
    <div class="hidden sm:flex flex-col gap-0.5 min-w-[90px]">
      <!-- Context Label (Top) -->
      <span
        class="text-xs font-medium transition-colors duration-200"
        :class="[
          timeData.colorClass,
          'group-hover/time:text-gray-200'
        ]"
      >
        {{ timeData.contextLabel }}
      </span>

      <!-- Precise Time (Bottom) -->
      <span
        class="text-[11px] font-mono text-gray-500 tabular-nums tracking-tight transition-colors duration-200 group-hover/time:text-gray-400"
      >
        {{ timeData.timeStr }}
      </span>

      <!-- Visual freshness indicator (for very recent items) -->
      <div
        v-if="timeData.diffSeconds < 300"
        class="h-0.5 w-full bg-gradient-to-r from-emerald-400/20 to-transparent rounded-full mt-0.5"
        :style="{
          opacity: Math.max(0, 1 - timeData.diffSeconds / 300)
        }"
      />
    </div>

    <!-- Mobile: Compact Inline Layout -->
    <div class="flex sm:hidden items-center gap-1.5 text-xs">
      <span
        class="font-medium"
        :class="timeData.colorClass"
      >
        {{ timeData.contextLabel }}
      </span>
      <span class="text-gray-600">•</span>
      <span class="font-mono text-gray-500 tabular-nums text-[11px]">
        {{ timeData.timeStr }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { formatSmartTime, type SmartTimeFormat } from '~/composables/useDateTimeFormatters'
import { useTimeRefresh } from '~/composables/useTimeRefresh'

interface Props {
  timestamp: string
  autoRefresh?: boolean
  refreshInterval?: number
}

const props = withDefaults(defineProps<Props>(), {
  autoRefresh: true,
  refreshInterval: 10000 // 10 seconds default
})

// Use the time refresh composable (with Page Visibility API integration)
const { currentTime } = props.autoRefresh
  ? useTimeRefresh(props.refreshInterval)
  : { currentTime: computed(() => new Date()) }

// Compute time data
const timeData = computed<SmartTimeFormat>(() => {
  return formatSmartTime(props.timestamp, currentTime.value)
})
</script>

<style scoped>
/* Ensure consistent layout */
.time-display-container {
  @apply select-none;
}

/* Smooth transitions */
.time-display-container * {
  @apply transition-colors duration-200;
}
</style>
