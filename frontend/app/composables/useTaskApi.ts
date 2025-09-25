import { ref } from 'vue'

export const useTaskApi = () => {
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  
  const retryTask = async (taskId: string) => {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await fetch(`http://localhost:8765/api/tasks/${taskId}/retry`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }
      
      const result = await response.json()
      return result
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to retry task'
      throw err
    } finally {
      isLoading.value = false
    }
  }
  
  return {
    retryTask,
    isLoading,
    error
  }
}