export const eventTypeToStatus = (eventType: string): string => {
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

export const statusVariants: Record<string, string> = {
  'success': 'success',
  'failed': 'failed',
  'pending': 'pending',
  'running': 'running',
  'retry': 'retry',
  'revoked': 'revoked',
  'received': 'received'
}

export const getStatusVariant = (status: string): string => {
  const statusLower = status.toLowerCase()
  return statusVariants[statusLower] || 'outline'
}