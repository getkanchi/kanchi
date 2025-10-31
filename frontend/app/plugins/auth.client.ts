import { useAuthStore } from '~/stores/auth'

export default defineNuxtPlugin(async () => {
  const authStore = useAuthStore()

  if (authStore.configLoading || authStore.config) {
    return
  }

  try {
    await authStore.bootstrap()
  } catch (err) {
    console.error('[AuthPlugin] Failed to bootstrap authentication:', err)
  }
})
