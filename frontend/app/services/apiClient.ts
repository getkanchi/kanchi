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
  }

  // Task-related endpoints
  async getTaskStats(): Promise<TaskStats> {
    const response = await this.api.api.getTaskStatsApiStatsGet()
    return response.data
  }

  async getRecentEvents(params?: {
    limit?: number
    page?: number
    aggregate?: boolean
    sort_by?: string | null
    sort_order?: string
    search?: string | null
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