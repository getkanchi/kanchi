import { defineStore } from 'pinia'
import { ref } from 'vue'
import { v4 as uuidv4 } from '@lukeed/uuid'
import { useApiService, type UserSessionResponse } from '~/services/apiClient'

interface InitializeOptions {
  persist?: boolean
}

interface ResetOptions {
  reload?: boolean
}

export const useSessionStore = defineStore('session', () => {
  const apiService = useApiService()

  const sessionId = ref<string | null>(null)
  const session = ref<UserSessionResponse | null>(null)
  const isInitialized = ref(false)
  const loading = ref(false)
  const error = ref<string | null>(null)

  function setSessionId(id: string | null, persist = true) {
    sessionId.value = id
    apiService.setAuthContext(apiService.getAccessToken(), id)

    if (!process.client) {
      return
    }

    if (persist) {
      if (id) {
        localStorage.setItem('kanchi_session_id', id)
      } else {
        localStorage.removeItem('kanchi_session_id')
      }
    }
  }

  async function initialize(providedSessionId?: string, options: InitializeOptions = {}) {
    if (isInitialized.value) {
      return
    }

    loading.value = true
    error.value = null

    try {
      const persist = options.persist ?? true
      let activeSessionId = providedSessionId || sessionId.value

      if (!activeSessionId && process.client) {
        activeSessionId = localStorage.getItem('kanchi_session_id')
      }

      if (!activeSessionId) {
        activeSessionId = uuidv4()
      }

      setSessionId(activeSessionId, persist)

      session.value = await apiService.initializeSession(activeSessionId)
      isInitialized.value = true

      console.log('[Session] Initialized:', session.value.session_id)
    } catch (err: any) {
      error.value = err.message || 'Failed to initialize session'
      console.error('[Session] Initialization failed:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function ensureInitialized(options: InitializeOptions = {}) {
    if (!isInitialized.value) {
      await initialize(undefined, options)
    }
  }

  async function initializeWithSessionId(id: string, options: InitializeOptions = {}) {
    setSessionId(id, options.persist ?? true)
    await ensureInitialized(options)
  }

  async function updatePreferences(preferences: Record<string, any>) {
    if (!sessionId.value) {
      throw new Error('Session not initialized')
    }

    loading.value = true
    error.value = null

    try {
      session.value = await apiService.updateSession(sessionId.value, { preferences })
    } catch (err: any) {
      error.value = err.message || 'Failed to update preferences'
      console.error('[Session] Failed to update preferences:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function setActiveEnvironment(environmentId: string | null) {
    if (!sessionId.value) {
      throw new Error('Session not initialized')
    }

    loading.value = true
    error.value = null

    try {
      if (environmentId) {
        session.value = await apiService.setSessionEnvironment(sessionId.value, environmentId)
      } else {
        session.value = await apiService.clearSessionEnvironment(sessionId.value)
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to set environment'
      console.error('[Session] Failed to set environment:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function refresh() {
    if (!sessionId.value) {
      throw new Error('Session not initialized')
    }

    loading.value = true
    error.value = null

    try {
      session.value = await apiService.getCurrentSession(sessionId.value)
    } catch (err: any) {
      error.value = err.message || 'Failed to refresh session'
      console.error('[Session] Failed to refresh:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  function adoptSession(sessionResponse: UserSessionResponse, options: InitializeOptions = {}) {
    session.value = sessionResponse
    isInitialized.value = true
    setSessionId(sessionResponse.session_id, options.persist ?? true)
  }

  function reset(options: ResetOptions = {}) {
    const reload = options.reload ?? true

    if (process.client) {
      localStorage.removeItem('kanchi_session_id')
    }

    setSessionId(null, false)
    session.value = null
    isInitialized.value = false

    if (reload) {
      window.location.reload()
    }
  }

  return {
    sessionId,
    session,
    isInitialized,
    loading,
    error,

    initialize,
    ensureInitialized,
    initializeWithSessionId,
    adoptSession,
    updatePreferences,
    setActiveEnvironment,
    refresh,
    reset,
    setSessionId,
  }
})
