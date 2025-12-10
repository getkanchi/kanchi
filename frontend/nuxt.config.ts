// https://nuxt.com/docs/api/configuration/nuxt-config
const baseURL = process.env.NUXT_APP_BASE_URL
  || (process.env.NODE_ENV === 'development' ? '/' : '/ui/')

export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  app: {
    baseURL,
  },
  modules: [
    '@nuxtjs/tailwindcss',
    '@pinia/nuxt',
  ],
  runtimeConfig: {
    public: {
      wsUrl: process.env.NUXT_PUBLIC_WS_URL || 'ws://localhost:8765/ws',
      apiUrl: process.env.NUXT_PUBLIC_API_URL || 'http://localhost:8765',
      kanchiVersion: process.env.NUXT_PUBLIC_KANCHI_VERSION || 'dev'
    }
  },
  vite: {
    server: {
      fs: {
        strict: false
      }
    },
    optimizeDeps: {
      include: ['@vue/devtools-core', '@vue/devtools-kit']
    }
  }
})
