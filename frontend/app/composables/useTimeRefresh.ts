import { ref, onMounted, onUnmounted } from 'vue'

/**
 * Auto-refresh composable with Page Visibility API integration
 *
 * Pauses auto-refresh when page is hidden to save resources
 * Resumes when page becomes visible again
 *
 * Usage:
 * const { currentTime } = useTimeRefresh(10000)
 */
export function useTimeRefresh(intervalMs: number = 10000) {
  const currentTime = ref(new Date())
  let intervalId: ReturnType<typeof setInterval> | null = null
  let isPageVisible = true

  const updateTime = () => {
    currentTime.value = new Date()
  }

  // Start interval
  const startInterval = () => {
    if (intervalId) return
    intervalId = setInterval(updateTime, intervalMs)
  }

  // Stop interval
  const stopInterval = () => {
    if (intervalId) {
      clearInterval(intervalId)
      intervalId = null
    }
  }

  const handleVisibilityChange = () => {
    if (document.hidden) {
      isPageVisible = false
      stopInterval()
    } else {
      isPageVisible = true
      updateTime() // Immediately update when page becomes visible
      startInterval()
    }
  }

  onMounted(() => {
    startInterval()
    document.addEventListener('visibilitychange', handleVisibilityChange)
  })

  onUnmounted(() => {
    stopInterval()
    document.removeEventListener('visibilitychange', handleVisibilityChange)
  })

  return {
    currentTime,
    isPageVisible
  }
}
