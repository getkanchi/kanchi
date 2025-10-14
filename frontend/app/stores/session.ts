/**
 * Pinia store for anonymous session management
 * Handles persistent user identity without authentication
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { v4 as uuidv4 } from '@lukeed/uuid'
import { useApiService, type UserSessionResponse } from '~/services/apiClient'

export const useSessionStore = defineStore('session', () => {
  const apiService = useApiService()

  // State
  const sessionId = ref<string | null>(null)
  const session = ref<UserSessionResponse | null>(null)
  const isInitialized = ref(false)
  const loading = ref(false)
  const error = ref<string | null>(null)

  /**
   * Initialize session - call this once on app mount
   * Reads session_id from localStorage or creates new one
   */
  async function initialize() {
    if (isInitialized.value) {
      return
    }

    loading.value = true
    error.value = null

    try {
      // Try to get session_id from localStorage
      let storedSessionId = localStorage.getItem('kanchi_session_id')

      if (!storedSessionId) {
        // Generate new session_id
        storedSessionId = uuidv4()
        localStorage.setItem('kanchi_session_id', storedSessionId)
      }

      sessionId.value = storedSessionId

      // Initialize session with backend
      // Backend will either load existing session or create new one
      session.value = await apiService.initializeSession(storedSessionId)
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

  /**
   * Update session preferences
   */
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

  /**
   * Set active environment for this session
   */
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

  /**
   * Get current session info
   */
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

  /**
   * Reset session - generates new session_id
   * Use this if you want to "log out" or start fresh
   */
  function reset() {
    localStorage.removeItem('kanchi_session_id')
    sessionId.value = null
    session.value = null
    isInitialized.value = false
    window.location.reload()
  }

  return {
    // State
    sessionId,
    session,
    isInitialized,
    loading,
    error,

    // Actions
    initialize,
    updatePreferences,
    setActiveEnvironment,
    refresh,
    reset
  }
})
