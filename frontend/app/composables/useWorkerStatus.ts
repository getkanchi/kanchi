export type WorkerStatusType = 'online' | 'offline' | 'warning' | 'error' | 'info' | 'success'

export const useWorkerStatus = () => {
  const getWorkerStatusType = (status: string): WorkerStatusType => {
    switch (status.toLowerCase()) {
      case 'online':
        return 'online'
      case 'offline':
        return 'offline'
      case 'heartbeat':
        return 'info'
      case 'warning':
        return 'warning'
      case 'error':
        return 'error'
      default:
        return 'offline'
    }
  }

  const getWorkerBadgeVariant = (status: string): string => {
    const statusType = getWorkerStatusType(status)
    const variantMap: Record<WorkerStatusType, string> = {
      online: 'online',
      offline: 'offline',
      info: 'heartbeat',
      warning: 'warning',
      error: 'failed',
      success: 'success'
    }
    return variantMap[statusType] || 'offline'
  }

  const getWorkerDotColor = (status: string): string => {
    const colors: Record<string, string> = {
      online: 'bg-status-success',
      offline: 'bg-status-error',
      heartbeat: 'bg-status-info',
      warning: 'bg-status-warning',
      error: 'bg-status-error',
    }
    return colors[status.toLowerCase()] || 'bg-gray-500'
  }

  return {
    getWorkerStatusType,
    getWorkerBadgeVariant,
    getWorkerDotColor
  }
}