export interface WorkerInfo {
  hostname: string
  status: string
  timestamp: string
  active_tasks: number
  processed_tasks: number
  sw_ident?: string
  sw_ver?: string
  sw_sys?: string
  loadavg?: number[]
  freq?: number
  error_count?: number
  tasks_per_minute?: number
  queue_depth?: number
  recent_errors?: Array<{
    time: string
    task: string
    error?: string
  }>
  active_task_details?: Array<{
    name: string
    progress: number
    duration: number
    task_id?: string
  }>
  metrics_history?: {
    tasks_per_minute: number[]
    errors: number[]
    latency: number[]
  }
}

export interface WorkerEvent {
  hostname: string
  event_type: string
  timestamp: string
  active?: number
  processed?: number
  pool?: any
  loadavg?: number[]
  freq?: number
}

export type WorkerStatus = 'online' | 'offline' | 'unknown'

export type WorkerEventType = 'worker-online' | 'worker-offline' | 'worker-heartbeat'