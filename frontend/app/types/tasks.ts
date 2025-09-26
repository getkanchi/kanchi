export interface Task {
  task_id: string
  task_name: string
  event_type: string
  timestamp: string
  args?: string
  kwargs?: string
  retries: number
  eta?: string | null
  expires?: string | null
  hostname?: string | null
  exchange: string
  routing_key: string
  root_id?: string | null
  parent_id?: string | null
  result?: any
  runtime?: number | null
  exception?: string | null
  traceback?: string | null
  retry_of?: string
  retried_by?: string[]
  is_retry?: boolean
  has_retries?: boolean
  retry_count?: number
}

export interface TaskEventResponse {
  task_id: string
  task_name: string
  event_type: string
  timestamp: string
  args?: string
  kwargs?: string
  retries?: number
  eta?: string | null
  expires?: string | null
  hostname?: string | null
  exchange?: string
  routing_key?: string
  root_id?: string | null
  parent_id?: string | null
  result?: null
  runtime?: number | null
  exception?: string | null
  traceback?: string | null
  retry_of?: string
  retried_by?: string[]
  is_retry?: boolean
  has_retries?: boolean
  retry_count?: number
}

export interface TaskStats {
  total_tasks?: number
  succeeded?: number
  failed?: number
  pending?: number
  retried?: number
  active?: number
}

export type TaskStatus = 'PENDING' | 'RECEIVED' | 'RUNNING' | 'SUCCESS' | 'FAILED' | 'RETRY' | 'REVOKED' | 'UNKNOWN'

export type TaskEventType = 'task-sent' | 'task-received' | 'task-started' | 'task-succeeded' | 'task-failed' | 'task-retried' | 'task-revoked'