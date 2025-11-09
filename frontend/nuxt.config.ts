// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  modules: [
    '@nuxtjs/tailwindcss',
    '@pinia/nuxt',
  ],
  runtimeConfig: {
    public: {
      wsUrl: process.env.NUXT_PUBLIC_WS_URL || 'ws://localhost:8765/ws',
      apiUrl: process.env.NUXT_PUBLIC_API_URL || 'http://localhost:8765',
      urlPrefix: (process.env.NUXT_PUBLIC_URL_PREFIX || '').replace(/^\/+|\/+$/g, '')
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

