import type { TaskStatus, TaskEventType } from '~/types/tasks'
import type { BadgeVariants } from '~/components/ui/badge'

export const useTaskStatus = () => {
  const eventTypeToStatus = (eventType: string): TaskStatus => {
    switch (eventType) {
      case 'task-sent':
        return 'PENDING'
      case 'task-received':
        return 'RECEIVED'
      case 'task-started':
        return 'RUNNING'
      case 'task-succeeded':
        return 'SUCCESS'
      case 'task-failed':
        return 'FAILED'
      case 'task-retried':
        return 'RETRY'
      case 'task-revoked':
        return 'REVOKED'
      default:
        return 'UNKNOWN'
    }
  }

  const statusVariants: Record<string, BadgeVariants['variant']> = {
    'success': 'success',
    'failed': 'failed',
    'pending': 'pending',
    'running': 'running',
    'retry': 'retry',
    'revoked': 'revoked',
    'received': 'received',
  }

  const getStatusVariant = (status: string): BadgeVariants['variant'] => {
    const statusLower = status.toLowerCase()
    return statusVariants[statusLower] || 'outline'
  }

  const formatStatus = (status: string): string => {
    return status.charAt(0).toUpperCase() + status.slice(1).toLowerCase()
  }

  const getAllStatuses = (): TaskStatus[] => {
    return ['PENDING', 'RECEIVED', 'RUNNING', 'SUCCESS', 'FAILED', 'RETRY', 'REVOKED']
  }

  const getStatusColor = (status: string) => {
    const statusLower = status.toLowerCase()
    
    const colorMap: Record<string, { pill: string; dot: string; ring?: string }> = {
      // Success states
      success: { 
        pill: 'bg-status-success-bg border-status-success-border text-status-success', 
        dot: 'bg-status-success', 
        ring: 'ring-status-success/40' 
      },
      completed: { 
        pill: 'bg-status-success-bg border-status-success-border text-status-success', 
        dot: 'bg-status-success', 
        ring: 'ring-status-success/40' 
      },
      
      // Error states  
      error: { 
        pill: 'bg-status-error-bg border-status-error-border text-status-error', 
        dot: 'bg-status-error', 
        ring: 'ring-status-error/40' 
      },
      failed: { 
        pill: 'bg-status-error-bg border-status-error-border text-status-error', 
        dot: 'bg-status-error', 
        ring: 'ring-status-error/40' 
      },
      failure: { 
        pill: 'bg-status-error-bg border-status-error-border text-status-error', 
        dot: 'bg-status-error', 
        ring: 'ring-status-error/40' 
      },
      
      // Running states
      running: { 
        pill: 'bg-status-info-bg border-status-info-border text-status-info', 
        dot: 'bg-status-info', 
        ring: 'ring-status-info/40' 
      },
      processing: { 
        pill: 'bg-status-info-bg border-status-info-border text-status-info', 
        dot: 'bg-status-info', 
        ring: 'ring-status-info/40' 
      },
      started: { 
        pill: 'bg-status-info-bg border-status-info-border text-status-info', 
        dot: 'bg-status-info', 
        ring: 'ring-status-info/40' 
      },
      
      // Pending states
      pending: { 
        pill: 'bg-status-warning-bg border-status-warning-border text-status-warning', 
        dot: 'bg-status-warning', 
        ring: 'ring-status-warning/40' 
      },
      waiting: { 
        pill: 'bg-status-warning-bg border-status-warning-border text-status-warning', 
        dot: 'bg-status-warning', 
        ring: 'ring-status-warning/40' 
      },
      
      // Special states
      received: { 
        pill: 'bg-status-special-bg border-status-special-border text-status-special', 
        dot: 'bg-status-special', 
        ring: 'ring-status-special/40' 
      },
      
      // Retry states
      retry: { 
        pill: 'bg-status-retry-bg border-status-retry-border text-status-retry', 
        dot: 'bg-status-retry', 
        ring: 'ring-status-retry/40' 
      },
      retrying: { 
        pill: 'bg-status-retry-bg border-status-retry-border text-status-retry', 
        dot: 'bg-status-retry', 
        ring: 'ring-status-retry/40' 
      },
      
      // Neutral states
      cancelled: { 
        pill: 'bg-status-neutral-bg border-status-neutral-border text-status-neutral', 
        dot: 'bg-status-neutral', 
        ring: 'ring-status-neutral/40' 
      },
      revoked: { 
        pill: 'bg-status-neutral-bg border-status-neutral-border text-status-neutral', 
        dot: 'bg-status-neutral', 
        ring: 'ring-status-neutral/40' 
      },
      ignored: { 
        pill: 'bg-status-neutral-bg border-status-neutral-border text-status-neutral', 
        dot: 'bg-status-neutral', 
        ring: 'ring-status-neutral/40' 
      },
      rejected: { 
        pill: 'bg-status-neutral-bg border-status-neutral-border text-status-neutral', 
        dot: 'bg-status-neutral', 
        ring: 'ring-status-neutral/40' 
      },
      
      // Default
      unknown: {
        pill: 'bg-gray-100 border-gray-300 text-gray-600',
        dot: 'bg-gray-500',
        ring: 'ring-gray-400/40'
      }
    }
    
    return colorMap[statusLower] || colorMap.unknown
  }

  const isAnimatedStatus = (status: string): boolean => {
    return ['running', 'processing', 'pending'].includes(status.toLowerCase())
  }

  const getDotColorClass = (status: string): string => {
    const colors: Record<string, string> = {
      online: 'bg-status-success',
      success: 'bg-status-success',
      offline: 'bg-status-error',
      error: 'bg-status-error',
      warning: 'bg-status-warning',
      info: 'bg-status-info',
      muted: 'bg-gray-400',
    }
    return colors[status.toLowerCase()] || 'bg-gray-500'
  }

  return {
    eventTypeToStatus,
    statusVariants,
    getStatusVariant,
    formatStatus,
    getAllStatuses,
    getStatusColor,
    isAnimatedStatus,
    getDotColorClass
  }
}