import { defineStore } from 'pinia'
import { readonly, ref } from 'vue'
import { useApiService } from '~/services/apiClient'
import type { AuditLogEntryDTO, AuditLogListResponseDTO } from '~/services/apiClient'

export interface AuditLogQuery {
  limit?: number
  offset?: number
  search?: string | null
  source?: string | null
  status?: string | null
  action_type?: string | null
  target_type?: string | null
  target_id?: string | null
  workflow_id?: string | null
  task_id?: string | null
  actor?: string | null
}

export const useAuditStore = defineStore('audit', () => {
  const apiService = useApiService()

  const entries = ref<AuditLogEntryDTO[]>([])
  const total = ref(0)
  const taskEntries = ref<Record<string, AuditLogEntryDTO[]>>({})
  const workflowEntries = ref<Record<string, AuditLogEntryDTO[]>>({})
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function fetchAuditLogs(query: AuditLogQuery = {}): Promise<AuditLogListResponseDTO> {
    try {
      isLoading.value = true
      error.value = null
      const response = await apiService.getAuditLogs(query)
      entries.value = response.items
      total.value = response.total
      return response
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch audit log'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchTaskAuditLogs(taskId: string, limit = 25): Promise<AuditLogEntryDTO[]> {
    try {
      isLoading.value = true
      error.value = null
      const response = await apiService.getTaskAuditLogs(taskId, { limit })
      taskEntries.value = {
        ...taskEntries.value,
        [taskId]: response.items,
      }
      return response.items
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch task audit log'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchWorkflowAuditLogs(workflowId: string, limit = 25): Promise<AuditLogEntryDTO[]> {
    try {
      isLoading.value = true
      error.value = null
      const response = await apiService.getWorkflowAuditLogs(workflowId, { limit })
      workflowEntries.value = {
        ...workflowEntries.value,
        [workflowId]: response.items,
      }
      return response.items
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch workflow audit log'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  function getTaskAudit(taskId: string): AuditLogEntryDTO[] {
    return taskEntries.value[taskId] || []
  }

  function getWorkflowAudit(workflowId: string): AuditLogEntryDTO[] {
    return workflowEntries.value[workflowId] || []
  }

  return {
    entries: readonly(entries),
    total: readonly(total),
    taskEntries: readonly(taskEntries),
    workflowEntries: readonly(workflowEntries),
    isLoading: readonly(isLoading),
    error: readonly(error),
    fetchAuditLogs,
    fetchTaskAuditLogs,
    fetchWorkflowAuditLogs,
    getTaskAudit,
    getWorkflowAudit,
  }
})
