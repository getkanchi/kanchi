import { useAuthStore } from '~/stores/auth'

export default defineNuxtRouteMiddleware((to) => {
  const authStore = useAuthStore()

  if (!process.client) {
    return
  }

  if (!authStore.config && authStore.configLoading) {
    return
  }

  if (authStore.authEnabled && !authStore.isAuthenticated && to.path !== '/login') {
    return navigateTo('/login')
  }

  if (authStore.authEnabled && authStore.isAuthenticated && to.path === '/login') {
    return navigateTo('/')
  }
})
