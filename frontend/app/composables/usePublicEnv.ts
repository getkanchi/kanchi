import { useRuntimeConfig } from '#imports'

interface PublicEnv {
  apiUrl: string
  wsUrl: string
  kanchiVersion: string
  urlPrefix: string
}

const FALLBACK_ENV: PublicEnv = {
  apiUrl: 'http://localhost:8765',
  wsUrl: 'ws://localhost:8765/ws',
  kanchiVersion: 'dev',
  urlPrefix: '',
}

type WindowEnv = Record<string, string>

function readWindowEnv(): WindowEnv {
  if (typeof window === 'undefined') {
    return {}
  }
  const env = (window as any).__KANCHI_UI_ENV__
  if (!env || typeof env !== 'object') {
    return {}
  }
  return env as WindowEnv
}

function normalizePrefix(prefix: string | undefined): string {
  if (!prefix) {
    return ''
  }
  let normalized = prefix.trim()
  if (!normalized.startsWith('/')) {
    normalized = `/${normalized}`
  }
  if (normalized.length > 1 && normalized.endsWith('/')) {
    normalized = normalized.slice(0, -1)
  }
  return normalized
}

function applyHttpPrefix(url: string | undefined, prefix: string): string | undefined {
  if (!url) {
    return undefined
  }
  if (!prefix) {
    return url
  }
  const parsed = new URL(url)
  const trimmed = parsed.pathname.replace(/\/+$/, '')
  parsed.pathname = `${trimmed}${prefix}`
  return parsed.toString().replace(/\/$/, '')
}

function applyWsPrefix(url: string | undefined, prefix: string): string | undefined {
  if (!url) {
    return undefined
  }
  if (!prefix) {
    return url
  }
  const parsed = new URL(url)
  parsed.pathname = `${prefix}/ws`
  return parsed.toString()
}

export function usePublicEnv(): PublicEnv {
  const runtime = useRuntimeConfig()
  const runtimePublic = (runtime?.public ?? {}) as Record<string, string | undefined>
  const windowEnv = readWindowEnv()
  const urlPrefix = normalizePrefix(
    windowEnv.NUXT_PUBLIC_URL_PREFIX || runtimePublic.urlPrefix
  )
  const apiUrl = windowEnv.NUXT_PUBLIC_API_URL || runtimePublic.apiUrl || FALLBACK_ENV.apiUrl
  const wsUrl = windowEnv.NUXT_PUBLIC_WS_URL || runtimePublic.wsUrl || FALLBACK_ENV.wsUrl

  return {
    apiUrl: applyHttpPrefix(apiUrl, urlPrefix) || FALLBACK_ENV.apiUrl,
    wsUrl: applyWsPrefix(wsUrl, urlPrefix) || FALLBACK_ENV.wsUrl,
    kanchiVersion:
      windowEnv.NUXT_PUBLIC_KANCHI_VERSION
      || runtimePublic.kanchiVersion
      || FALLBACK_ENV.kanchiVersion,
    urlPrefix,
  }
}
