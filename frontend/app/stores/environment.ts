import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { useApiService } from '~/services/apiClient'
import { useSessionStore } from '~/stores/session'

export interface Environment {
  id: string
  name: string
  description?: string
  queue_patterns: string[]
  worker_patterns: string[]
  is_active: boolean
  is_default: boolean
  created_at: string
  updated_at: string
}

export interface EnvironmentCreate {
  name: string
  description?: string
  queue_patterns: string[]
  worker_patterns: string[]
  is_default?: boolean
}

export interface EnvironmentUpdate {
  name?: string
  description?: string
  queue_patterns?: string[]
  worker_patterns?: string[]
  is_default?: boolean
}

export const useEnvironmentStore = defineStore('environment', () => {
  const environments = ref<Environment[]>([])
  const activeEnvironment = ref<Environment | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const apiService = useApiService()
  const sessionStore = useSessionStore()

  const hasActiveEnvironment = computed(() => activeEnvironment.value !== null)
  const defaultEnvironment = computed(() =>
    environments.value.find(env => env.is_default) || null
  )

  watch(
    () => sessionStore.session?.active_environment_id,
    (newEnvironmentId) => {
      if (newEnvironmentId && environments.value.length > 0) {
        const env = environments.value.find(e => e.id === newEnvironmentId)
        if (env) {
          activeEnvironment.value = env
        }
      } else {
        activeEnvironment.value = null
      }
    }
  )

  async function fetchEnvironments() {
    loading.value = true
    error.value = null
    try {
      const data = await apiService.getEnvironments()
      environments.value = data

      const active = environments.value.find(env => env.is_active)
      activeEnvironment.value = active || null

      if (active) {
        localStorage.setItem('kanchi_active_environment', active.id)
      } else {
        localStorage.removeItem('kanchi_active_environment')
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch environments'
      console.error('Error fetching environments:', err)
    } finally {
      loading.value = false
    }
  }

  async function fetchActiveEnvironment() {
    try {
      const data = await apiService.getActiveEnvironment()
      activeEnvironment.value = data

      if (data) {
        localStorage.setItem('kanchi_active_environment', data.id)
      } else {
        localStorage.removeItem('kanchi_active_environment')
      }
    } catch (err: any) {
      console.error('Error fetching active environment:', err)
    }
  }

  async function createEnvironment(envCreate: EnvironmentCreate) {
    loading.value = true
    error.value = null
    try {
      const data = await apiService.createEnvironment(envCreate)
      environments.value.push(data)
      return data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to create environment'
      console.error('Error creating environment:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateEnvironment(id: string, envUpdate: EnvironmentUpdate) {
    loading.value = true
    error.value = null
    try {
      const data = await apiService.updateEnvironment(id, envUpdate)
      const index = environments.value.findIndex(env => env.id === id)
      if (index !== -1) {
        environments.value[index] = data
      }

      if (activeEnvironment.value?.id === id) {
        activeEnvironment.value = data
      }

      return data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to update environment'
      console.error('Error updating environment:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteEnvironment(id: string) {
    loading.value = true
    error.value = null
    try {
      await apiService.deleteEnvironment(id)
      environments.value = environments.value.filter(env => env.id !== id)
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to delete environment'
      console.error('Error deleting environment:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function activateEnvironment(id: string) {
    loading.value = true
    error.value = null
    try {
      await sessionStore.setActiveEnvironment(id)

      const env = environments.value.find(e => e.id === id)
      if (env) {
        activeEnvironment.value = env
      }

      return env
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to activate environment'
      console.error('Error activating environment:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deactivateAll() {
    loading.value = true
    error.value = null
    try {
      await sessionStore.setActiveEnvironment(null)

      activeEnvironment.value = null
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to deactivate environments'
      console.error('Error deactivating environments:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function initialize() {
    await fetchEnvironments()

    if (sessionStore.session?.active_environment_id) {
      const env = environments.value.find(
        e => e.id === sessionStore.session?.active_environment_id
      )
      if (env) {
        activeEnvironment.value = env
      }
    }
  }

  return {
    environments,
    activeEnvironment,
    loading,
    error,

    hasActiveEnvironment,
    defaultEnvironment,

    fetchEnvironments,
    fetchActiveEnvironment,
    createEnvironment,
    updateEnvironment,
    deleteEnvironment,
    activateEnvironment,
    deactivateAll,
    initialize
  }
})
