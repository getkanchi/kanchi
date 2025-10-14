/**
 * Centralized API service using auto-generated types
 */
import { Api } from '../src/types/api'
import type { 
  TaskStats, 
  TaskEventResponse, 
  WorkerInfo
} from '../src/types/api'

class ApiService {
  private api: Api<unknown>

  constructor(baseURL: string) {
    // The axios-generated Api class expects configuration directly
    this.api = new Api({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Add request interceptor to include session ID
    this.api.instance.interceptors.request.use((config) => {
      const sessionId = localStorage.getItem('kanchi_session_id')
      if (sessionId) {
        config.headers['X-Session-Id'] = sessionId
      }
      return config
    })
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
    // Legacy parameters (deprecated)
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

  async getActiveTasks(): Promise<TaskEventResponse[]> {
    const response = await this.api.api.getActiveTasksApiTasksActiveGet()
    return response.data
  }

  async retryTask(taskId: string): Promise<any> {
    const response = await this.api.api.retryTaskApiTasksTaskIdRetryPost(taskId)
    return response.data
  }

  async getOrphanedTasks(): Promise<TaskEventResponse[]> {
    const response = await this.api.api.getOrphanedTasksApiTasksOrphanedGet()
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

  // Action Config endpoints
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

// Create singleton instance with runtime config
let apiService: ApiService | null = null

export function useApiService(): ApiService {
  if (!apiService) {
    const config = useRuntimeConfig()
    apiService = new ApiService(config.public.apiUrl as string)
  }
  return apiService
}

export type { TaskStats, TaskEventResponse, WorkerInfo }

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