import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { useApiService } from '../services/apiClient'
import type {
  RerunPreflightResponseDTO,
  RerunSubmitItemDTO,
  TaskActionDetailDTO,
  TaskActionListResponseDTO,
  TaskActionSummaryDTO,
  TaskActionType,
  TaskEventResponse,
} from '../services/apiClient'

const DISMISSED_KEY = 'kanchi.taskActions.dismissed'

function loadDismissed(): string[] {
  if (!process.client) return []
  try {
    const raw = window.localStorage.getItem(DISMISSED_KEY)
    const parsed = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? parsed.filter(Boolean) : []
  } catch {
    return []
  }
}

function saveDismissed(ids: string[]) {
  if (!process.client) return
  window.localStorage.setItem(DISMISSED_KEY, JSON.stringify(ids.slice(0, 200)))
}

export const useTaskActionsStore = defineStore('taskActions', () => {
  const apiService = useApiService()

  const actions = ref<TaskActionSummaryDTO[]>([])
  const focusedActionId = ref<string | null>(null)
  const focusedAction = ref<TaskActionDetailDTO | null>(null)
  const isDrawerOpen = ref(false)
  const isLoading = ref(false)
  const isCreating = ref(false)
  const isPreflighting = ref(false)
  const error = ref<string | null>(null)
  const maxSelectionSize = ref(100)
  const dismissedActionIds = ref<string[]>(loadDismissed())

  const activeActions = computed(() =>
    actions.value.filter(action => !dismissedActionIds.value.includes(action.id))
  )

  const runningActions = computed(() =>
    activeActions.value.filter(action => action.status === 'running')
  )

  const latestAction = computed(() => activeActions.value[0] || null)

  function upsertSummary(summary: TaskActionSummaryDTO) {
    const index = actions.value.findIndex(action => action.id === summary.id)
    const next = index >= 0
      ? actions.value.map((action, idx) => (idx === index ? { ...action, ...summary } : action))
      : [summary, ...actions.value]
    actions.value = next.sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at))
  }

  async function fetchConfig() {
    const response = await apiService.getTaskActionConfig()
    maxSelectionSize.value = response.max_selection_size || 100
  }

  async function fetchActions(limit = 20): Promise<TaskActionListResponseDTO> {
    try {
      isLoading.value = true
      error.value = null
      const response = await apiService.listTaskActions({ limit })
      actions.value = response.data
      maxSelectionSize.value = response.max_selection_size || maxSelectionSize.value
      return response
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch task actions'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchAction(actionId: string): Promise<TaskActionDetailDTO> {
    try {
      isLoading.value = true
      error.value = null
      const detail = await apiService.getTaskAction(actionId)
      upsertSummary(detail)
      if (focusedActionId.value === actionId) {
        focusedAction.value = detail
      }
      return detail
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch task action'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function preflightRerun(taskIds: string[]): Promise<RerunPreflightResponseDTO> {
    try {
      isPreflighting.value = true
      error.value = null
      const response = await apiService.preflightTaskActionRerun(taskIds)
      maxSelectionSize.value = response.max_selection_size || maxSelectionSize.value
      return response
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to check rerun availability'
      throw err
    } finally {
      isPreflighting.value = false
    }
  }

  async function createAction(actionType: TaskActionType, taskIds: string[]): Promise<TaskActionDetailDTO> {
    try {
      isCreating.value = true
      error.value = null
      const detail = await apiService.createTaskAction(actionType, taskIds)
      upsertSummary(detail)
      focusAction(detail.id, { detail, autoOpen: true })
      return detail
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to create task action'
      throw err
    } finally {
      isCreating.value = false
    }
  }

  async function submitRerunReview(items: RerunSubmitItemDTO[]): Promise<TaskActionDetailDTO> {
    try {
      isCreating.value = true
      error.value = null
      const detail = await apiService.submitRerunReview(items)
      upsertSummary(detail)
      focusAction(detail.id, { detail, autoOpen: true })
      return detail
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to submit rerun review'
      throw err
    } finally {
      isCreating.value = false
    }
  }

  function focusAction(
    actionId: string,
    options: { detail?: TaskActionDetailDTO; autoOpen?: boolean } = {}
  ) {
    focusedActionId.value = actionId
    if (options.detail) {
      focusedAction.value = options.detail
    } else {
      fetchAction(actionId).catch(() => {})
    }
    if (options.autoOpen) {
      isDrawerOpen.value = true
    }
  }

  function openDrawer(actionId?: string) {
    if (actionId) {
      focusAction(actionId, { autoOpen: true })
      return
    }
    if (!focusedActionId.value && latestAction.value) {
      focusAction(latestAction.value.id)
    }
    isDrawerOpen.value = true
  }

  function closeDrawer() {
    isDrawerOpen.value = false
  }

  function dismissAction(actionId: string) {
    if (!dismissedActionIds.value.includes(actionId)) {
      dismissedActionIds.value = [actionId, ...dismissedActionIds.value]
      saveDismissed(dismissedActionIds.value)
    }
  }

  function handleLiveEvent(event: TaskActionDetailDTO) {
    upsertSummary(event)
    if (focusedActionId.value === event.id) {
      focusedAction.value = event
    }

    const currentSessionId = apiService.getSessionId()
    if (currentSessionId && event.initiated_session_id === currentSessionId) {
      focusAction(event.id, { detail: event, autoOpen: true })
    }
  }

  function handleTaskLifecycleEvent(event: TaskEventResponse) {
    if (!focusedAction.value || !event.task_id) return

    const matchingItem = focusedAction.value.items.find(item => item.rerun_task_id === event.task_id)
    if (!matchingItem) return

    matchingItem.rerun_task = event
    const counts: Record<string, number> = {}
    focusedAction.value.items.forEach(item => {
      const eventType = item.rerun_task?.event_type
      if (!eventType) return
      counts[eventType] = (counts[eventType] || 0) + 1
    })
    focusedAction.value.rerun_lifecycle_counts = counts
  }

  return {
    actions,
    activeActions,
    runningActions,
    latestAction,
    focusedActionId,
    focusedAction,
    isDrawerOpen,
    isLoading,
    isCreating,
    isPreflighting,
    error,
    maxSelectionSize,
    dismissedActionIds,

    fetchConfig,
    fetchActions,
    fetchAction,
    preflightRerun,
    createAction,
    submitRerunReview,
    focusAction,
    openDrawer,
    closeDrawer,
    dismissAction,
    handleLiveEvent,
    handleTaskLifecycleEvent,
  }
})
