// ============================================================================
// Helper Functions for Date Comparisons
// ============================================================================

const isToday = (date: Date): boolean => {
  const now = new Date()
  return (
    date.getDate() === now.getDate() &&
    date.getMonth() === now.getMonth() &&
    date.getFullYear() === now.getFullYear()
  )
}

const isYesterday = (date: Date): boolean => {
  const yesterday = new Date()
  yesterday.setDate(yesterday.getDate() - 1)
  return (
    date.getDate() === yesterday.getDate() &&
    date.getMonth() === yesterday.getMonth() &&
    date.getFullYear() === yesterday.getFullYear()
  )
}

const isThisWeek = (date: Date): boolean => {
  const now = new Date()
  const weekStart = new Date(now)
  weekStart.setDate(now.getDate() - now.getDay())
  weekStart.setHours(0, 0, 0, 0)

  const weekEnd = new Date(weekStart)
  weekEnd.setDate(weekStart.getDate() + 7)

  return date >= weekStart && date < weekEnd
}

const isThisYear = (date: Date): boolean => {
  const now = new Date()
  return date.getFullYear() === now.getFullYear()
}

// ============================================================================
// Smart Time Formatting (Dual-Layer Display)
// ============================================================================

export interface SmartTimeFormat {
  contextLabel: string
  timeStr: string
  colorClass: string
  fullDateTime: string
  diffSeconds: number
}

export const formatSmartTime = (timestamp: string, currentTime?: Date): SmartTimeFormat => {
  if (!timestamp) {
    return {
      contextLabel: '-',
      timeStr: '-',
      colorClass: 'text-gray-500',
      fullDateTime: '',
      diffSeconds: 0
    }
  }

  const date = new Date(timestamp)
  const now = currentTime || new Date()
  const diff = now.getTime() - date.getTime()
  const seconds = Math.floor(diff / 1000)

  // Time always with seconds (HH:mm:ss format)
  const timeStr = date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })

  // Full datetime for tooltip
  const fullDateTime = date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true
  })

  // Determine context label and color based on recency
  let contextLabel = ''
  let colorClass = 'text-gray-500'

  if (seconds < 0) {
    // Future timestamp (clock skew)
    contextLabel = 'Just now'
    colorClass = 'text-emerald-400'
  } else if (seconds < 60) {
    // Less than 1 minute
    contextLabel = `${seconds}s ago`
    colorClass = 'text-emerald-400'
  } else if (seconds < 3600) {
    // 1-59 minutes
    const minutes = Math.floor(seconds / 60)
    contextLabel = `${minutes}m ago`
    colorClass = 'text-emerald-400'
  } else if (seconds < 21600) {
    // 1-6 hours
    const hours = Math.floor(seconds / 3600)
    contextLabel = `${hours}h ago`
    colorClass = 'text-gray-300'
  } else if (isToday(date)) {
    // Today (but > 6 hours ago)
    contextLabel = 'Today'
    colorClass = 'text-gray-400'
  } else if (isYesterday(date)) {
    // Yesterday
    contextLabel = 'Yesterday'
    colorClass = 'text-gray-500'
  } else if (isThisWeek(date)) {
    // This week (Mon, Tue, etc.)
    contextLabel = date.toLocaleDateString('en-US', { weekday: 'short' })
    colorClass = 'text-gray-500'
  } else if (isThisYear(date)) {
    // This year (Jan 15, Feb 3, etc.)
    contextLabel = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    colorClass = 'text-gray-500'
  } else {
    // Older (Jan 15, 2024)
    contextLabel = date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
    colorClass = 'text-gray-600'
  }

  return {
    contextLabel,
    timeStr,
    colorClass,
    fullDateTime,
    diffSeconds: seconds
  }
}

// ============================================================================
// Legacy Functions (Preserved for Backward Compatibility)
// ============================================================================

export const formatTime = (timestamp: string): string => {
  if (!timestamp) return '-'
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
}

export const calculateDuration = (started: string, completed: string | null): string => {
  if (!started) return '-'

  const start = new Date(started).getTime()
  const end = completed ? new Date(completed).getTime() : Date.now()
  const duration = end - start

  if (duration < 1000) return `${duration}ms`
  if (duration < 60000) return `${(duration / 1000).toFixed(1)}s`
  if (duration < 3600000) return `${Math.floor(duration / 60000)}m ${Math.floor((duration % 60000) / 1000)}s`
  return `${Math.floor(duration / 3600000)}h ${Math.floor((duration % 3600000) / 60000)}m`
}

export const formatTimestamp = (timestamp: string): string => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  if (diff < 60000) return `${Math.floor(diff / 1000)}s ago`
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })
}

export const formatDuration = (seconds: number): string => {
  if (seconds < 60) return `${seconds.toFixed(0)}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${(seconds % 60).toFixed(0)}s`
  return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`
}