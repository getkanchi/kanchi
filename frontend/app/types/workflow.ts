/**
 * Workflow automation types
 * Based on backend Pydantic models from WORKFLOW_SYSTEM_PLAN.md
 */

// ==================== Condition Types ====================

export type ConditionOperator =
  | 'equals'
  | 'not_equals'
  | 'in'
  | 'not_in'
  | 'matches'
  | 'gt'
  | 'lt'
  | 'gte'
  | 'lte'
  | 'contains'
  | 'starts_with'
  | 'ends_with'

export interface Condition {
  field: string
  operator: ConditionOperator
  value: any
}

export interface ConditionGroup {
  operator: 'AND' | 'OR'
  conditions: Condition[]
}

// ==================== Trigger Types ====================

export interface TriggerConfig {
  type: string
  config?: Record<string, any>
}

// ==================== Circuit Breaker Types ====================

export interface CircuitBreakerConfig {
  enabled: boolean
  max_executions: number
  window_seconds: number
  context_field?: string
}

// ==================== Action Types ====================

export interface ActionConfig {
  type: string
  config_id?: string
  params: Record<string, any>
  continue_on_failure?: boolean
}

export interface ActionResult {
  action_type: string
  status: 'success' | 'failed' | 'skipped'
  result?: Record<string, any>
  error_message?: string
  duration_ms: number
}

// ==================== Workflow Types ====================

export interface WorkflowDefinition {
  id?: string
  name: string
  description?: string
  enabled: boolean
  trigger: TriggerConfig
  conditions?: ConditionGroup
  actions: ActionConfig[]
  priority: number
  max_executions_per_hour?: number
  cooldown_seconds: number
  circuit_breaker?: CircuitBreakerConfig
  created_at?: string
  updated_at?: string
  created_by?: string
  execution_count: number
  last_executed_at?: string
  success_count: number
  failure_count: number
}

export interface WorkflowCreateRequest {
  name: string
  description?: string
  enabled: boolean
  trigger: TriggerConfig
  conditions?: ConditionGroup
  actions: ActionConfig[]
  priority?: number
  max_executions_per_hour?: number
  cooldown_seconds?: number
  circuit_breaker?: CircuitBreakerConfig
}

export interface WorkflowUpdateRequest {
  name?: string
  description?: string
  enabled?: boolean
  trigger?: TriggerConfig
  conditions?: ConditionGroup
  actions?: ActionConfig[]
  priority?: number
  max_executions_per_hour?: number
  cooldown_seconds?: number
  circuit_breaker?: CircuitBreakerConfig
}

// ==================== Workflow Execution Types ====================

export type WorkflowExecutionStatus =
  | 'pending'
  | 'running'
  | 'completed'
  | 'failed'
  | 'rate_limited'
  | 'circuit_open'

export interface WorkflowExecutionRecord {
  id: number
  workflow_id: string
  triggered_at: string
  trigger_type: string
  trigger_event: Record<string, any>
  status: WorkflowExecutionStatus
  actions_executed?: ActionResult[]
  error_message?: string
  stack_trace?: string
  started_at?: string
  completed_at?: string
  duration_ms?: number
  workflow_snapshot?: Record<string, any>
}

export interface WorkflowReplayRequest {
  start_time?: string
  end_time?: string
  limit: number
  dry_run: boolean
}

export interface WorkflowReplayMatch {
  event_type: string
  timestamp: string
  task_id?: string
  task_name?: string
  hostname?: string
  summary: string
  context: Record<string, any>
}

export interface WorkflowReplayResponse {
  workflow_id: string
  workflow_name: string
  dry_run: boolean
  scanned_count: number
  matched_count: number
  executed_count: number
  truncated: boolean
  matches: WorkflowReplayMatch[]
}

// ==================== Action Config Types ====================

export interface ActionConfigDefinition {
  id?: string
  name: string
  description?: string
  action_type: string
  config: Record<string, any>
  created_at?: string
  updated_at?: string
  created_by?: string
  usage_count: number
  last_used_at?: string
}

export interface ActionConfigCreateRequest {
  name: string
  description?: string
  action_type: string
  config: Record<string, any>
}

export interface ActionConfigUpdateRequest {
  name?: string
  description?: string
  config?: Record<string, any>
}

// ==================== Metadata Types ====================

export interface TriggerMetadata {
  type: string
  label: string
  description: string
  category: 'task' | 'worker' | 'schedule'
  contextFields: string[]
}

export interface ActionTypeMetadata {
  type: string
  label: string
  description: string
  category: string
  requiredParams: string[]
  optionalParams: string[]
}

// ==================== UI Helper Types ====================

export interface WorkflowTestRequest {
  workflow_id: string
  test_context: Record<string, any>
}

export interface WorkflowTestResponse {
  workflow_id: string
  workflow_name: string
  test_context: Record<string, any>
  conditions_met: boolean
  would_execute: boolean
  actions: string[]
}
