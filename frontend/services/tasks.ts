// services/users.ts
import { api } from '../utils/api'

export interface Task {
    id: string
    name: string
    queue: string
    status: string
    started_at: string
    completed_at: string
    retries: number
    args?: any[]
    kwargs?: Record<string, any>
    result?: any
    traceback?: string
    worker?: string
    runtime?: number
    eta?: string
}

export const taskService = {
  async getAll(): Promise<Task[]> {
    return api.get('/tasks')
  },

}
