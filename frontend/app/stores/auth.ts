import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { useApiService, type AuthConfigDTO, type LoginResponseDTO, type UserInfoDTO } from '~/services/apiClient'
import { useSessionStore } from './session'

const ACCESS_TOKEN_KEY = 'kanchi_access_token'
const REFRESH_TOKEN_KEY = 'kanchi_refresh_token'
const SESSION_ID_KEY = 'kanchi_session_id'

export const useAuthStore = defineStore('auth', () => {
  const apiService = useApiService()
  const sessionStore = useSessionStore()

  const config = ref<AuthConfigDTO | null>(null)
  const configLoading = ref(false)
  const configError = ref<string | null>(null)

  const user = ref<UserInfoDTO | null>(null)
  const accessToken = ref<string | null>(null)
  const refreshToken = ref<string | null>(null)
  const sessionId = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const authEnabled = computed(() => !!config.value?.auth_enabled)
  const oauthProviders = computed(() => config.value?.oauth_providers ?? [])
  const isAuthenticated = computed(() => !!user.value)
  const needsLogin = computed(() => authEnabled.value && !isAuthenticated.value)

  function applyAuthContext() {
    apiService.setAuthContext(accessToken.value, sessionId.value)
    if (authEnabled.value) {
      apiService.registerUnauthorizedHandler(async () => {
        if (!refreshToken.value) {
          return false
        }
        try {
          await refreshTokens()
          return true
        } catch (refreshError) {
          console.error('[Auth] Failed to refresh token:', refreshError)
          clearAuthState({ persist: true })
          return false
        }
      })
    } else {
      apiService.registerUnauthorizedHandler(null)
    }
  }

  function persistTokens() {
    if (!process.client) return
    if (accessToken.value) {
      localStorage.setItem(ACCESS_TOKEN_KEY, accessToken.value)
    } else {
      localStorage.removeItem(ACCESS_TOKEN_KEY)
    }

    if (refreshToken.value) {
      localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken.value)
    } else {
      localStorage.removeItem(REFRESH_TOKEN_KEY)
    }
  }

  function clearAuthState(options: { persist?: boolean } = {}) {
    const persist = options.persist ?? true

    user.value = null
    accessToken.value = null
    refreshToken.value = null
    sessionId.value = null
    apiService.setAuthContext(null, null)
    apiService.registerUnauthorizedHandler(null)

    if (persist && process.client) {
      localStorage.removeItem(ACCESS_TOKEN_KEY)
      localStorage.removeItem(REFRESH_TOKEN_KEY)
    }
  }

  async function applyLoginResponse(payload: LoginResponseDTO, options: { persistSession?: boolean } = {}) {
    user.value = payload.user
    accessToken.value = payload.tokens.access_token
    refreshToken.value = payload.tokens.refresh_token
    sessionId.value = payload.tokens.session_id

    persistTokens()
    applyAuthContext()

    const persistSession = options.persistSession ?? true
    await sessionStore.initializeWithSessionId(payload.tokens.session_id, { persist: persistSession })
  }

  async function bootstrap() {
    if (configLoading.value) {
      return
    }

    configLoading.value = true
    configError.value = null

    try {
      const fetchedConfig = await apiService.getAuthConfig()
      config.value = fetchedConfig

      if (!fetchedConfig.auth_enabled) {
        clearAuthState({ persist: true })
        await sessionStore.ensureInitialized({ persist: true })
        return
      }

      let storedSessionId: string | null = null

      if (process.client) {
        accessToken.value = localStorage.getItem(ACCESS_TOKEN_KEY)
        refreshToken.value = localStorage.getItem(REFRESH_TOKEN_KEY)
        storedSessionId = localStorage.getItem(SESSION_ID_KEY)
      }

      if (storedSessionId && !sessionStore.sessionId) {
        sessionStore.setSessionId(storedSessionId, true)
      }

      sessionId.value = sessionStore.sessionId as string | null

      if (accessToken.value && refreshToken.value) {
        applyAuthContext()
        try {
          user.value = await apiService.getCurrentUser()
          if (sessionId.value) {
            await sessionStore.initializeWithSessionId(sessionId.value, { persist: true })
          } else {
            await sessionStore.ensureInitialized({ persist: true })
            sessionId.value = sessionStore.sessionId as string | null
            applyAuthContext()
          }
        } catch (err) {
          console.warn('[Auth] Existing credentials invalid, clearing session.', err)
          clearAuthState({ persist: true })
          await sessionStore.ensureInitialized({ persist: true })
          sessionId.value = sessionStore.sessionId as string | null
        }
      } else {
        clearAuthState({ persist: true })
        if (storedSessionId) {
          sessionStore.setSessionId(storedSessionId, true)
        }
        await sessionStore.ensureInitialized({ persist: true })
        sessionId.value = sessionStore.sessionId as string | null
      }
    } catch (err: any) {
      configError.value = err?.message || 'Unable to load authentication configuration'
      console.error('[Auth] Failed to load config:', err)
      throw err
    } finally {
      configLoading.value = false
    }
  }

  async function loginWithBasic(username: string, password: string) {
    if (!authEnabled.value) {
      throw new Error('Authentication is disabled')
    }

    loading.value = true
    error.value = null

    try {
      await sessionStore.ensureInitialized({ persist: false })
      const activeSessionId = sessionStore.sessionId as string | null
      const response = await apiService.loginWithBasic(username, password, activeSessionId || undefined)
      await applyLoginResponse(response)
    } catch (err: any) {
      error.value = err?.message || 'Login failed'
      console.error('[Auth] Basic login failed:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function refreshTokens() {
    if (!refreshToken.value) {
      throw new Error('Refresh token unavailable')
    }

    const response = await apiService.refreshAuthToken(refreshToken.value)
    await applyLoginResponse(response, { persistSession: true })
  }

  async function logout() {
    if (!authEnabled.value) {
      return
    }

    try {
      if (sessionId.value) {
        await apiService.logout(sessionId.value)
      }
    } catch (err) {
      console.warn('[Auth] Logout request failed (ignored):', err)
    } finally {
      clearAuthState({ persist: true })
      sessionStore.reset({ reload: false })
      await sessionStore.ensureInitialized({ persist: true })
      sessionId.value = sessionStore.sessionId as string | null
    }
  }

  async function handleOAuthLogin(response: LoginResponseDTO) {
    if (!authEnabled.value) {
      console.warn('[Auth] Received OAuth response while auth disabled')
      return
    }
    await applyLoginResponse(response)
  }

  return {
    // state
    config,
    configLoading,
    configError,
    user,
    accessToken,
    refreshToken,
    sessionId,
    loading,
    error,

    // computed
    authEnabled,
    oauthProviders,
    isAuthenticated,
    needsLogin,

    // actions
    bootstrap,
    loginWithBasic,
    refreshTokens,
    logout,
    handleOAuthLogin,
    clearAuthState,
    applyAuthContext,
  }
})
