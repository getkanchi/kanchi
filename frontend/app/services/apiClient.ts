/**
 * Centralized API service using auto-generated types
 */
import { Api } from '../src/types/api'
import type {
  AppConfigSnapshot,
  DataRetentionConfig,
  RetentionCleanupResponse,
  RetentionCleanupResult,
  RetentionLastRun,
  RetentionScheduleConfig,
  TaskStats,
  TaskEvent,
  TaskIssueConfig,
  WorkerInfo
} from '../src/types/api'

export type AuthProvider = 'google' | 'github'
export type TaskEventResponse = TaskEvent & {
  submitted_rerun_args?: any[] | null
  submitted_rerun_kwargs?: Record<string, any> | null
  submitted_rerun_kind?: RerunKind | null
}

export interface UserInfoDTO {
  id: string
  email: string
  provider: string
  name?: string | null
  avatar_url?: string | null
}

export interface AuthTokensDTO {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  refresh_expires_in: number
  session_id: string
}

export interface AuthConfigDTO {
  auth_enabled: boolean
  basic_enabled: boolean
  oauth_providers: string[]
  allowed_email_patterns: string[]
}

export interface LoginResponseDTO {
  user: UserInfoDTO
  tokens: AuthTokensDTO
  provider: string
}

export type AppSettingValueType = 'string' | 'number' | 'boolean' | 'json'

export interface AppSettingDTO {
  key: string
  value: any
  value_type: AppSettingValueType
  label?: string | null
  description?: string | null
  category?: string | null
  created_at: string
  updated_at: string
}

export interface AppSettingInput {
  value: any
  value_type?: AppSettingValueType
  label?: string | null
  description?: string | null
  category?: string | null
}

export type TaskIssueConfigDTO = TaskIssueConfig
export type DataRetentionConfigDTO = DataRetentionConfig
export type RetentionCleanupResultDTO = RetentionCleanupResult
export type RetentionCleanupResponseDTO = RetentionCleanupResponse
export type RetentionScheduleConfigDTO = RetentionScheduleConfig
export type RetentionLastRunDTO = RetentionLastRun
export type AppConfigSnapshotDTO = AppConfigSnapshot

export interface TaskStepDefinition {
  key: string
  label: string
  description?: string | null
  total?: number | null
  order?: number | null
}

export interface TaskProgressEventResponse {
  task_id: string
  task_name: string
  progress: number
  timestamp: string
  step_key?: string | null
  message?: string | null
  meta?: Record<string, any> | null
  event_type: 'kanchi-task-progress'
}

export interface TaskStepsEventResponse {
  task_id: string
  task_name: string
  steps: TaskStepDefinition[]
  timestamp: string
  event_type: 'kanchi-task-steps'
}

export interface TaskProgressSnapshotResponse {
  task_id: string
  latest?: TaskProgressEventResponse | null
  steps: TaskStepDefinition[]
  history: TaskProgressEventResponse[]
}

export type TaskActionType = 'rerun' | 'resolve' | 'unresolve'
export type TaskActionStatus = 'running' | 'completed' | 'partial_success' | 'failed'
export type TaskActionItemOutcome = 'pending' | 'changed' | 'noop' | 'created' | 'skipped_unavailable' | 'user_skipped' | 'blocked_skipped' | 'failed'
export type RerunReviewState = 'replayable' | 'repairable' | 'blocked'
export type RerunSubmitDecision = 'submit' | 'user_skip' | 'blocked_skip'
export type RerunKind = 'replay' | 'edited_override' | 'repaired_override'

export interface RerunInputIssueDTO {
  path: string
  reason_code: string
  message: string
}

export interface RerunInputBaselineDTO {
  args: any[]
  kwargs: Record<string, any>
  source: string
  source_version?: string | null
}

export interface RerunSubmissionTargetDTO {
  task_name?: string | null
  queue?: string | null
  routing_key?: string | null
  exchange?: string | null
}

export interface RerunPreflightItemDTO {
  task_id: string
  task_name?: string | null
  ready: boolean
  review_state: RerunReviewState
  reason_code?: string | null
  reason?: string | null
  task?: TaskEventResponse | null
  baseline: RerunInputBaselineDTO
  target: RerunSubmissionTargetDTO
  required_replacements: RerunInputIssueDTO[]
  fingerprint?: string | null
}

export interface RerunPreflightResponseDTO {
  total: number
  ready_count: number
  unavailable_count: number
  replayable_count: number
  repairable_count: number
  blocked_count: number
  max_selection_size: number
  items: RerunPreflightItemDTO[]
}

export interface RerunSubmitItemDTO {
  task_id: string
  decision: RerunSubmitDecision
  fingerprint: string
  args?: any[] | null
  kwargs?: Record<string, any> | null
}

export interface TaskActionItemDTO {
  id: number
  action_id: string
  original_task_id: string
  original_task_name?: string | null
  outcome: TaskActionItemOutcome
  reason_code?: string | null
  reason?: string | null
  rerun_task_id?: string | null
  rerun_task_name?: string | null
  rerun_task?: TaskEventResponse | null
  attempted_task_id?: string | null
  submitted_args?: any[] | null
  submitted_kwargs?: Record<string, any> | null
  rerun_kind?: RerunKind | null
  skip_category?: string | null
  review_fingerprint?: string | null
  target_queue?: string | null
  created_at: string
  updated_at: string
}

export interface TaskActionSummaryDTO {
  id: string
  action_type: TaskActionType
  status: TaskActionStatus
  initiated_by_user_id?: string | null
  initiated_by?: string | null
  initiated_session_id?: string | null
  created_at: string
  started_at?: string | null
  completed_at?: string | null
  original_task_ids: string[]
  selection_size: number
  item_total: number
  item_changed: number
  item_noop: number
  item_created: number
  item_skipped: number
  item_failed: number
  summary?: Record<string, any>
}

export interface TaskActionDetailDTO extends TaskActionSummaryDTO {
  items: TaskActionItemDTO[]
  rerun_lifecycle_counts: Record<string, number>
  event_type?: 'kanchi-task-action'
}

export interface TaskActionListResponseDTO {
  data: TaskActionSummaryDTO[]
  max_selection_size: number
}

class ApiService {
  private api: Api<unknown>

  private accessToken: string | null = null

  private sessionId: string | null = null

  private onUnauthorized: (() => Promise<boolean>) | null = null

  constructor(baseURL: string) {
    // The axios-generated Api class expects configuration directly
    this.api = new Api({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.api.instance.interceptors.request.use((config) => {
      if (this.sessionId) {
        config.headers['X-Session-Id'] = this.sessionId
      }
      if (this.accessToken) {
        config.headers['Authorization'] = `Bearer ${this.accessToken}`
      }
      return config
    })

    this.api.instance.interceptors.response.use(
      (response) => response,
      async (error) => {
        const status = error?.response?.status
        const requestConfig = (error?.config ?? {}) as any

        if (status === 401 && this.onUnauthorized && !requestConfig.__isRetryRequest) {
          requestConfig.__isRetryRequest = true
          const refreshed = await this.onUnauthorized()
          if (refreshed) {
            return this.api.instance.request(requestConfig)
          }
        }

        return Promise.reject(error)
      }
    )
  }

  setAuthContext(accessToken: string | null, sessionId: string | null) {
    this.accessToken = accessToken
    this.sessionId = sessionId
  }

  clearAuthContext() {
    this.accessToken = null
    this.sessionId = null
  }

  registerUnauthorizedHandler(handler: (() => Promise<boolean>) | null) {
    this.onUnauthorized = handler
  }

  getSessionId(): string | null {
    return this.sessionId
  }

  getAccessToken(): string | null {
    return this.accessToken
  }

  // Configuration endpoints
  async getAppConfig(): Promise<AppConfigSnapshotDTO> {
    const response = await this.api.request({
      path: '/api/config',
      method: 'GET'
    })
    return response.data
  }

  async listSettings(): Promise<AppSettingDTO[]> {
    const response = await this.api.request({
      path: '/api/config/settings',
      method: 'GET'
    })
    return response.data
  }

  async upsertSetting(key: string, payload: AppSettingInput): Promise<AppSettingDTO> {
    const response = await this.api.request({
      path: `/api/config/settings/${encodeURIComponent(key)}`,
      method: 'PUT',
      body: payload
    })
    return response.data
  }

  async deleteSetting(key: string): Promise<void> {
    await this.api.request({
      path: `/api/config/settings/${encodeURIComponent(key)}`,
      method: 'DELETE'
    })
  }

  async getRetentionConfig(): Promise<DataRetentionConfigDTO> {
    const response = await this.api.request({
      path: '/api/config/retention',
      method: 'GET'
    })
    return response.data
  }

  async runRetentionCleanup(dryRun = true): Promise<RetentionCleanupResponseDTO> {
    const response = await this.api.request({
      path: `/api/config/retention/cleanup?dry_run=${dryRun ? 'true' : 'false'}`,
      method: 'POST'
    })
    return response.data
  }

  async getAuthConfig(): Promise<AuthConfigDTO> {
    const response = await this.api.instance.get<AuthConfigDTO>('/api/auth/config')
    return response.data
  }

  async loginWithBasic(username: string, password: string, sessionId?: string): Promise<LoginResponseDTO> {
    const response = await this.api.instance.post<LoginResponseDTO>('/api/auth/basic/login', {
      username,
      password,
      session_id: sessionId,
    })
    return response.data
  }

  async refreshAuthToken(refreshToken: string): Promise<LoginResponseDTO> {
    const response = await this.api.instance.post<LoginResponseDTO>('/api/auth/refresh', {
      refresh_token: refreshToken,
    })
    return response.data
  }

  async logout(sessionId?: string): Promise<void> {
    await this.api.instance.post('/api/auth/logout', {
      session_id: sessionId,
    })
  }

  async getCurrentUser(): Promise<UserInfoDTO> {
    const response = await this.api.instance.get<UserInfoDTO>('/api/auth/me')
    return response.data
  }

  async getOAuthAuthorizationUrl(
    provider: AuthProvider,
    params?: { redirectTo?: string; sessionId?: string }
  ): Promise<{ authorization_url: string; state: string }> {
    const response = await this.api.instance.get<{ authorization_url: string; state: string }>(
      `/api/auth/oauth/${provider}/authorize`,
      {
        params: {
          redirect_to: params?.redirectTo,
          session_id: params?.sessionId,
        },
      }
    )
    return response.data
  }

  // Task-related endpoints
  async getTaskStats(): Promise<TaskStats> {
    // Stats endpoint removed - return empty stats
    return {
      total_tasks: 0,
      succeeded: 0,
      failed: 0,
      pending: 0,
      retried: 0,
      active: 0
    } as TaskStats
  }

  async getRecentEvents(params?: {
    limit?: number
    page?: number
    aggregate?: boolean
    sort_by?: string | null
    sort_order?: string
    search?: string | null
    filters?: string | null
    start_time?: string | null
    end_time?: string | null
    filter_state?: string | null
    filter_worker?: string | null
    filter_task?: string | null
    filter_queue?: string | null
  }): Promise<object> {
    const response = await this.api.api.getRecentEventsApiEventsRecentGet(params)
    return response.data
  }

  async getTaskEvents(taskId: string): Promise<TaskEventResponse[]> {
    const response = await this.api.api.getTaskEventsApiEventsTaskIdGet(taskId)
    return response.data
  }

  async getTaskProgress(taskId: string): Promise<TaskProgressSnapshotResponse> {
    const response = await this.api.request({
      path: `/api/tasks/${encodeURIComponent(taskId)}/progress`,
      method: 'GET'
    })
    return response.data
  }

  async getActiveTasks(): Promise<TaskEventResponse[]> {
    const response = await this.api.api.getActiveTasksApiTasksActiveGet()
    return response.data
  }

  async retryTask(taskId: string): Promise<any> {
    const response = await this.rerunTask(taskId)
    return response
  }

  async preflightTaskActionRerun(taskIds: string[]): Promise<RerunPreflightResponseDTO> {
    const response = await this.api.request({
      path: '/api/task-actions/rerun/preflight',
      method: 'POST',
      body: { task_ids: taskIds }
    })
    return response.data
  }

  async submitRerunReview(items: RerunSubmitItemDTO[]): Promise<TaskActionDetailDTO> {
    const response = await this.api.request({
      path: '/api/task-actions/rerun',
      method: 'POST',
      body: { items }
    })
    return response.data
  }

  async createTaskAction(actionType: TaskActionType, taskIds: string[]): Promise<TaskActionDetailDTO> {
    const response = await this.api.request({
      path: '/api/task-actions',
      method: 'POST',
      body: {
        action_type: actionType,
        task_ids: taskIds
      }
    })
    return response.data
  }

  async listTaskActions(params?: { limit?: number }): Promise<TaskActionListResponseDTO> {
    const response = await this.api.request({
      path: '/api/task-actions',
      method: 'GET',
      query: params
    })
    return response.data
  }

  async getTaskAction(actionId: string): Promise<TaskActionDetailDTO> {
    const response = await this.api.request({
      path: `/api/task-actions/${encodeURIComponent(actionId)}`,
      method: 'GET'
    })
    return response.data
  }

  async getTaskActionConfig(): Promise<{ max_selection_size: number }> {
    const response = await this.api.request({
      path: '/api/task-actions/config',
      method: 'GET'
    })
    return response.data
  }

  async preflightTaskRerun(taskId: string): Promise<RerunPreflightResponseDTO> {
    const response = await this.api.request({
      path: `/api/tasks/${encodeURIComponent(taskId)}/rerun/preflight`,
      method: 'POST'
    })
    return response.data
  }

  async rerunTask(taskId: string): Promise<TaskActionDetailDTO> {
    const response = await this.api.request({
      path: `/api/tasks/${encodeURIComponent(taskId)}/rerun`,
      method: 'POST'
    })
    return response.data
  }

  async resolveTask(taskId: string, resolvedBy?: string | null): Promise<any> {
    const response = await this.api.request({
      path: `/api/tasks/${taskId}/resolve`,
      method: 'POST',
      body: resolvedBy ? { resolved_by: resolvedBy } : undefined
    })
    return response.data
  }

  async clearTaskResolution(taskId: string): Promise<any> {
    const response = await this.api.request({
      path: `/api/tasks/${taskId}/resolve`,
      method: 'DELETE'
    })
    return response.data
  }

  async getOrphanedTasks(): Promise<TaskEventResponse[]> {
    const response = await this.api.api.getOrphanedTasksApiTasksOrphanedGet()
    return response.data
  }

  async getRecentFailedTasks(params?: { hours?: number; limit?: number; include_retried?: boolean }): Promise<TaskEventResponse[]> {
    const response = await this.api.request({
      path: '/api/tasks/failed/recent',
      method: 'GET',
      query: params
    })
    return response.data
  }

  // Worker-related endpoints
  async getWorkers(): Promise<WorkerInfo[]> {
    const response = await this.api.api.getWorkersApiWorkersGet()
    return response.data
  }

  async getWorker(hostname: string): Promise<WorkerInfo> {
    const response = await this.api.api.getWorkerApiWorkersHostnameGet(hostname)
    return response.data
  }

  async getRecentWorkerEvents(limit = 50): Promise<any> {
    const response = await this.api.api.getRecentWorkerEventsApiWorkersEventsRecentGet({ limit })
    return response.data
  }

  // Health check
  async healthCheck(): Promise<any> {
    const response = await this.api.api.healthCheckApiHealthGet()
    return response.data
  }

  // Health details check
  async healthDetailsCheck(): Promise<any> {
    const response = await this.api.api.healthDetailsApiHealthDetailsGet()
    return response.data
  }

  // WebSocket message types
  async getWebSocketMessageTypes(): Promise<any> {
    const response = await this.api.api.getWebsocketMessageTypesApiWebsocketMessageTypesGet()
    return response.data
  }

  // Registry endpoints
  async getRegistryTasks(params?: { tag?: string; name?: string }): Promise<any> {
    const response = await this.api.request({
      path: '/api/registry/tasks',
      method: 'GET',
      query: params
    })
    return response.data
  }

  async getRegistryTask(taskName: string): Promise<any> {
    const response = await this.api.request({
      path: `/api/registry/tasks/${encodeURIComponent(taskName)}`,
      method: 'GET'
    })
    return response.data
  }

  async updateRegistryTask(taskName: string, update: any): Promise<any> {
    const response = await this.api.request({
      path: `/api/registry/tasks/${encodeURIComponent(taskName)}`,
      method: 'PUT',
      body: update
    })
    return response.data
  }

  async getRegistryTaskStats(taskName: string, hours: number = 24): Promise<any> {
    const response = await this.api.request({
      path: `/api/registry/tasks/${encodeURIComponent(taskName)}/stats`,
      method: 'GET',
      query: { hours }
    })
    return response.data
  }

  async getRegistryTaskTimeline(taskName: string, hours: number = 24, bucketSizeMinutes: number = 60): Promise<any> {
    const response = await this.api.request({
      path: `/api/registry/tasks/${encodeURIComponent(taskName)}/timeline`,
      method: 'GET',
      query: { hours, bucket_size_minutes: bucketSizeMinutes }
    })
    return response.data
  }

  async getRegistryTaskDailyStats(taskName: string, params?: { start_date?: string; end_date?: string; days?: number }): Promise<any> {
    const response = await this.api.request({
      path: `/api/registry/tasks/${encodeURIComponent(taskName)}/daily-stats`,
      method: 'GET',
      query: params
    })
    return response.data
  }

  async getRegistryTaskTrend(taskName: string, days: number = 7): Promise<any> {
    const response = await this.api.request({
      path: `/api/registry/tasks/${encodeURIComponent(taskName)}/trend`,
      method: 'GET',
      query: { days }
    })
    return response.data
  }

  async getRegistryTags(): Promise<string[]> {
    const response = await this.api.request({
      path: '/api/registry/tags',
      method: 'GET'
    })
    return response.data
  }

  async getTaskFailures(taskName: string, hours: number = 24, limit: number = 10): Promise<TaskEventResponse[]> {
    const startTime = new Date(Date.now() - hours * 3600000).toISOString()
    const response = await this.getRecentEvents({
      filters: `task:is:${taskName};state:is:FAILED`,
      start_time: startTime,
      sort_by: 'timestamp',
      sort_order: 'desc',
      limit,
      aggregate: false
    })
    return response.data?.events || response.data || []
  }

  // Environment endpoints
  async getEnvironments(): Promise<any[]> {
    const response = await this.api.request({
      path: '/api/environments',
      method: 'GET'
    })
    return response.data
  }

  async getActiveEnvironment(): Promise<any> {
    const response = await this.api.request({
      path: '/api/environments/active',
      method: 'GET'
    })
    return response.data
  }

  async getEnvironment(id: string): Promise<any> {
    const response = await this.api.request({
      path: `/api/environments/${id}`,
      method: 'GET'
    })
    return response.data
  }

  async createEnvironment(data: any): Promise<any> {
    const response = await this.api.request({
      path: '/api/environments',
      method: 'POST',
      body: data
    })
    return response.data
  }

  async updateEnvironment(id: string, data: any): Promise<any> {
    const response = await this.api.request({
      path: `/api/environments/${id}`,
      method: 'PATCH',
      body: data
    })
    return response.data
  }

  async deleteEnvironment(id: string): Promise<void> {
    await this.api.request({
      path: `/api/environments/${id}`,
      method: 'DELETE'
    })
  }

  async activateEnvironment(id: string): Promise<any> {
    const response = await this.api.request({
      path: `/api/environments/${id}/activate`,
      method: 'POST'
    })
    return response.data
  }

  async deactivateAllEnvironments(): Promise<void> {
    await this.api.request({
      path: '/api/environments/deactivate-all',
      method: 'POST'
    })
  }

  // Session endpoints
  async initializeSession(sessionId: string): Promise<any> {
    const response = await this.api.api.initializeSessionApiSessionsInitPost({
      headers: {
        'X-Session-Id': sessionId
      }
    })
    return response.data
  }

  async getCurrentSession(sessionId: string): Promise<any> {
    const response = await this.api.api.getCurrentSessionApiSessionsMeGet({
      headers: {
        'X-Session-Id': sessionId
      }
    })
    return response.data
  }

  async updateSession(sessionId: string, data: any): Promise<any> {
    const response = await this.api.api.updateCurrentSessionApiSessionsMePatch(data, {
      headers: {
        'X-Session-Id': sessionId
      }
    })
    return response.data
  }

  async setSessionEnvironment(sessionId: string, environmentId: string): Promise<any> {
    const response = await this.api.api.setSessionEnvironmentApiSessionsMeEnvironmentEnvironmentIdPost(
      environmentId,
      {
        headers: {
          'X-Session-Id': sessionId
        }
      }
    )
    return response.data
  }

  async clearSessionEnvironment(sessionId: string): Promise<any> {
    const response = await this.api.api.clearSessionEnvironmentApiSessionsMeEnvironmentDelete({
      headers: {
        'X-Session-Id': sessionId
      }
    })
    return response.data
  }

  // Workflow endpoints
  async getWorkflows(params?: {
    enabled_only?: boolean
    trigger_type?: string
    limit?: number
    offset?: number
  }): Promise<any[]> {
    const response = await this.api.request({
      path: '/api/workflows',
      method: 'GET',
      query: params
    })
    return response.data
  }

  async getWorkflowMetadata(): Promise<any> {
    const response = await this.api.request({
      path: '/api/workflows/metadata',
      method: 'GET'
    })
    return response.data
  }

  async getWorkflow(workflowId: string): Promise<any> {
    const response = await this.api.request({
      path: `/api/workflows/${workflowId}`,
      method: 'GET'
    })
    return response.data
  }

  async createWorkflow(data: any): Promise<any> {
    const response = await this.api.request({
      path: '/api/workflows',
      method: 'POST',
      body: data
    })
    return response.data
  }

  async updateWorkflow(workflowId: string, data: any): Promise<any> {
    const response = await this.api.request({
      path: `/api/workflows/${workflowId}`,
      method: 'PUT',
      body: data
    })
    return response.data
  }

  async deleteWorkflow(workflowId: string): Promise<void> {
    await this.api.request({
      path: `/api/workflows/${workflowId}`,
      method: 'DELETE'
    })
  }

  async getWorkflowExecutions(workflowId: string, params?: {
    limit?: number
    offset?: number
  }): Promise<any[]> {
    const response = await this.api.request({
      path: `/api/workflows/${workflowId}/executions`,
      method: 'GET',
      query: params
    })
    return response.data
  }

  async getRecentWorkflowExecutions(params?: {
    status?: string
    limit?: number
    offset?: number
  }): Promise<any[]> {
    const response = await this.api.request({
      path: '/api/workflows/executions/recent',
      method: 'GET',
      query: params
    })
    return response.data
  }

  async testWorkflow(workflowId: string, testContext: any): Promise<any> {
    const response = await this.api.request({
      path: `/api/workflows/${workflowId}/test`,
      method: 'POST',
      body: testContext
    })
    return response.data
  }

  async getActionConfigs(params?: {
    action_type?: string
    limit?: number
    offset?: number
  }): Promise<any[]> {
    const response = await this.api.request({
      path: '/api/action-configs',
      method: 'GET',
      query: params
    })
    return response.data
  }

  async getActionConfig(configId: string): Promise<any> {
    const response = await this.api.request({
      path: `/api/action-configs/${configId}`,
      method: 'GET'
    })
    return response.data
  }

  async createActionConfig(data: any): Promise<any> {
    const response = await this.api.request({
      path: '/api/action-configs',
      method: 'POST',
      body: data
    })
    return response.data
  }

  async updateActionConfig(configId: string, data: any): Promise<any> {
    const response = await this.api.request({
      path: `/api/action-configs/${configId}`,
      method: 'PUT',
      body: data
    })
    return response.data
  }

  async deleteActionConfig(configId: string): Promise<void> {
    await this.api.request({
      path: `/api/action-configs/${configId}`,
      method: 'DELETE'
    })
  }

}

let apiService: ApiService | null = null

export function useApiService(): ApiService {
  if (!apiService) {
    const config = useRuntimeConfig()
    apiService = new ApiService(config.public.apiUrl as string)
  }
  return apiService
}

export type {
  TaskStats,
  TaskEventResponse,
  WorkerInfo,
  AppConfigSnapshotDTO,
  AppSettingDTO,
  AppSettingInput,
  TaskIssueConfigDTO,
  DataRetentionConfigDTO,
  RetentionCleanupResponseDTO,
  RetentionScheduleConfigDTO,
  RetentionLastRunDTO
}

// Re-export session types from auto-generated API
export type { UserSessionResponse, UserSessionUpdate } from '../src/types/api'

// Re-export registry types
export type {
  TaskRegistryResponse,
  TaskRegistryUpdate,
  TaskRegistryStats,
  TaskDailyStatsResponse,
  TaskTimelineResponse,
  TaskTrendSummary,
  TimelineBucket
} from '~/types/taskRegistry'
