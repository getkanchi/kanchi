import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'
import { useApiService } from '../services/apiClient'
import type {
  WorkflowDefinition,
  WorkflowCreateRequest,
  WorkflowUpdateRequest,
  WorkflowExecutionRecord,
  ActionConfigDefinition,
  ActionConfigCreateRequest,
  ActionConfigUpdateRequest
} from '~/types/workflow'

export const useWorkflowsStore = defineStore('workflows', () => {
  const apiService = useApiService()

  const workflows = ref<WorkflowDefinition[]>([])
  const currentWorkflow = ref<WorkflowDefinition | null>(null)
  const executions = ref<WorkflowExecutionRecord[]>([])
  const actionConfigs = ref<ActionConfigDefinition[]>([])

  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const enabledWorkflows = computed(() =>
    workflows.value.filter(w => w.enabled)
  )

  const activeWorkflowsCount = computed(() => enabledWorkflows.value.length)

  const workflowsByTrigger = computed(() => {
    const grouped: Record<string, WorkflowDefinition[]> = {}
    workflows.value.forEach(workflow => {
      const trigger = workflow.trigger.type
      if (!grouped[trigger]) {
        grouped[trigger] = []
      }
      grouped[trigger].push(workflow)
    })
    return grouped
  })

  async function fetchWorkflows(params?: {
    enabled_only?: boolean
    trigger_type?: string
  }) {
    try {
      isLoading.value = true
      error.value = null
      workflows.value = await apiService.getWorkflows(params)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch workflows'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchWorkflow(workflowId: string) {
    try {
      isLoading.value = true
      error.value = null
      currentWorkflow.value = await apiService.getWorkflow(workflowId)
      return currentWorkflow.value
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch workflow'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function createWorkflow(data: WorkflowCreateRequest) {
    try {
      isLoading.value = true
      error.value = null
      const workflow = await apiService.createWorkflow(data)
      workflows.value.unshift(workflow)
      return workflow
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to create workflow'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function updateWorkflow(workflowId: string, data: WorkflowUpdateRequest) {
    try {
      isLoading.value = true
      error.value = null
      const updated = await apiService.updateWorkflow(workflowId, data)

      const index = workflows.value.findIndex(w => w.id === workflowId)
      if (index !== -1) {
        workflows.value[index] = updated
      }

      if (currentWorkflow.value?.id === workflowId) {
        currentWorkflow.value = updated
      }

      return updated
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to update workflow'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function deleteWorkflow(workflowId: string) {
    try {
      isLoading.value = true
      error.value = null
      await apiService.deleteWorkflow(workflowId)

      workflows.value = workflows.value.filter(w => w.id !== workflowId)

      if (currentWorkflow.value?.id === workflowId) {
        currentWorkflow.value = null
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to delete workflow'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function toggleWorkflow(workflowId: string) {
    const workflow = workflows.value.find(w => w.id === workflowId)
    if (!workflow) return

    return updateWorkflow(workflowId, { enabled: !workflow.enabled })
  }

  async function fetchWorkflowExecutions(workflowId: string, params?: {
    limit?: number
    offset?: number
  }) {
    try {
      isLoading.value = true
      error.value = null
      executions.value = await apiService.getWorkflowExecutions(workflowId, params)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch executions'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchRecentExecutions(params?: {
    status?: string
    limit?: number
  }) {
    try {
      isLoading.value = true
      error.value = null
      executions.value = await apiService.getRecentWorkflowExecutions(params)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch recent executions'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function testWorkflow(workflowId: string, testContext: any) {
    try {
      error.value = null
      return await apiService.testWorkflow(workflowId, testContext)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to test workflow'
      throw err
    }
  }

  async function fetchActionConfigs(params?: { action_type?: string }) {
    try {
      isLoading.value = true
      error.value = null
      actionConfigs.value = await apiService.getActionConfigs(params)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch action configs'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function createActionConfig(data: ActionConfigCreateRequest) {
    try {
      isLoading.value = true
      error.value = null
      const config = await apiService.createActionConfig(data)
      actionConfigs.value.unshift(config)
      return config
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to create action config'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function updateActionConfig(configId: string, data: ActionConfigUpdateRequest) {
    try {
      isLoading.value = true
      error.value = null
      const updated = await apiService.updateActionConfig(configId, data)

      const index = actionConfigs.value.findIndex(c => c.id === configId)
      if (index !== -1) {
        actionConfigs.value[index] = updated
      }

      return updated
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to update action config'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function deleteActionConfig(configId: string) {
    try {
      isLoading.value = true
      error.value = null
      await apiService.deleteActionConfig(configId)
      actionConfigs.value = actionConfigs.value.filter(c => c.id !== configId)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to delete action config'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  function clearError() {
    error.value = null
  }

  function setCurrentWorkflow(workflow: WorkflowDefinition | null) {
    currentWorkflow.value = workflow
  }

  return {
    workflows: readonly(workflows),
    currentWorkflow: readonly(currentWorkflow),
    executions: readonly(executions),
    actionConfigs: readonly(actionConfigs),
    isLoading: readonly(isLoading),
    error: readonly(error),

    enabledWorkflows,
    activeWorkflowsCount,
    workflowsByTrigger,

    fetchWorkflows,
    fetchWorkflow,
    createWorkflow,
    updateWorkflow,
    deleteWorkflow,
    toggleWorkflow,
    fetchWorkflowExecutions,
    fetchRecentExecutions,
    testWorkflow,
    fetchActionConfigs,
    createActionConfig,
    updateActionConfig,
    deleteActionConfig,
    clearError,
    setCurrentWorkflow
  }
})
