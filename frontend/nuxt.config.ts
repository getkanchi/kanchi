// https://nuxt.com/docs/api/configuration/nuxt-config
function normalizeBaseURL(value: string | undefined): string {
  const base = value?.trim() || '/'
  const withLeadingSlash = base.startsWith('/') ? base : `/${base}`
  return withLeadingSlash.endsWith('/') ? withLeadingSlash : `${withLeadingSlash}/`
}

export default defineNuxtConfig({
  ssr: false,
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  app: {
    baseURL: normalizeBaseURL(process.env.NUXT_APP_BASE_URL),
  },
  modules: [
    '@nuxtjs/tailwindcss',
    '@pinia/nuxt',
  ],
  runtimeConfig: {
    public: {
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
