// https://nuxt.com/docs/api/configuration/nuxt-config
function normalizeBaseURL(value: string | undefined): string {
  const fallback = process.env.NODE_ENV === 'development' ? '/' : '/ui/'
  const base = value?.trim() || fallback
  const withLeadingSlash = base.startsWith('/') ? base : `/${base}`
  return withLeadingSlash.endsWith('/') ? withLeadingSlash : `${withLeadingSlash}/`
}

const baseURL = normalizeBaseURL(process.env.NUXT_APP_BASE_URL)

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
      kanchiVersion: process.env.NUXT_PUBLIC_KANCHI_VERSION || 'dev',
      urlPrefix: process.env.NUXT_PUBLIC_URL_PREFIX || '',
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
