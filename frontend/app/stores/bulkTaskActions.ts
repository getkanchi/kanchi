import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { useApiService } from '~/services/apiClient'
import type { BulkTaskActionRequest, BulkTaskActionResult } from '~/src/types/api'

export const useBulkTaskActionsStore = defineStore('bulkTaskActions', () => {
  const apiService = useApiService()
  const preview = ref<BulkTaskActionResult | null>(null)
  const result = ref<BulkTaskActionResult | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const activeResult = computed(() => result.value ?? preview.value)

  async function previewAction(payload: BulkTaskActionRequest) {
    isLoading.value = true
    error.value = null
    try {
      const response = await apiService.bulkTaskAction({ ...payload, dry_run: true })
      preview.value = response
      result.value = null
      return response
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to preview bulk action'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function executeAction(payload: BulkTaskActionRequest) {
    isLoading.value = true
    error.value = null
    try {
      const response = await apiService.bulkTaskAction({ ...payload, dry_run: false })
      result.value = response
      preview.value = null
      return response
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to execute bulk action'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  function reset() {
    preview.value = null
    result.value = null
    error.value = null
  }

  return {
    preview,
    result,
    activeResult,
    isLoading,
    error,
    previewAction,
    executeAction,
    reset,
  }
})
