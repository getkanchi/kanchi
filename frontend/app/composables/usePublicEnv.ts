import { useRuntimeConfig } from '#imports'

interface PublicEnv {
  apiUrl: string
  wsUrl: string
  kanchiVersion: string
}

const FALLBACK_ENV: PublicEnv = {
  apiUrl: 'http://localhost:8765',
  wsUrl: 'ws://localhost:8765/ws',
  kanchiVersion: 'dev',
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

function deriveLocationDefaults(): Partial<PublicEnv> {
  if (typeof window === 'undefined') {
    return {}
  }

  const origin = window.location.origin
  const wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws'

  return {
    apiUrl: origin,
    wsUrl: `${wsScheme}://${window.location.host}/ws`,
  }
}

export function usePublicEnv(): PublicEnv {
  const runtime = useRuntimeConfig()
  const runtimePublic = (runtime?.public ?? {}) as Record<string, string | undefined>
  const windowEnv = readWindowEnv()
  const locationDefaults = deriveLocationDefaults()

  return {
    apiUrl:
      windowEnv.NUXT_PUBLIC_API_URL
      || runtimePublic.apiUrl
      || locationDefaults.apiUrl
      || FALLBACK_ENV.apiUrl,
    wsUrl:
      windowEnv.NUXT_PUBLIC_WS_URL
      || runtimePublic.wsUrl
      || locationDefaults.wsUrl
      || FALLBACK_ENV.wsUrl,
    kanchiVersion:
      windowEnv.NUXT_PUBLIC_KANCHI_VERSION
      || runtimePublic.kanchiVersion
      || FALLBACK_ENV.kanchiVersion,
  }
}
