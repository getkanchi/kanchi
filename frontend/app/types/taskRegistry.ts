/**
 * TaskRegistry types
 * TODO: These should be auto-generated from backend OpenAPI after running:
 * npm run generate:api:local
 */

export interface TaskRegistryResponse {
  id: string
  name: string
  human_readable_name?: string | null
  description?: string | null
  tags: string[]
  created_at: string
  updated_at: string
  first_seen: string
  last_seen: string
}

export interface TaskRegistryUpdate {
  human_readable_name?: string | null
  description?: string | null
  tags?: string[] | null
}

export interface TaskRegistryStats {
  task_name: string
  total_executions: number
  succeeded: number
  failed: number
  pending: number
  retried: number
  avg_runtime?: number | null
  last_execution?: string | null
}

export interface TimelineBucket {
  timestamp: string
  total_executions: number
  succeeded: number
  failed: number
  retried: number
}

export interface TaskTimelineResponse {
  task_name: string
  start_time: string
  end_time: string
  bucket_size_minutes: number
  buckets: TimelineBucket[]
}

export interface TaskDailyStatsResponse {
  task_name: string
  date: string
  total_executions: number
  succeeded: number
  failed: number
  pending: number
  retried: number
  revoked: number
  orphaned: number
  avg_runtime?: number | null
  min_runtime?: number | null
  max_runtime?: number | null
  p50_runtime?: number | null
  p95_runtime?: number | null
  p99_runtime?: number | null
  first_execution?: string | null
  last_execution?: string | null
}

export interface TaskTrendSummary {
  task_name: string
  days: number
  start_date: string
  end_date: string
  total_executions: number
  total_succeeded: number
  total_failed: number
  avg_success_rate: number
  avg_failure_rate: number
  avg_runtime?: number | null
}
