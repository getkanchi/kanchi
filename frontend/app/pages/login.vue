<template>
  <div class="flex min-h-screen bg-background-base">
    <div class="mx-auto grid min-h-screen w-full max-w-6xl gap-16 px-6 py-12 content-center lg:grid-cols-[1fr_minmax(0,420px)] lg:items-center lg:py-20">
      <div class="hidden w-full max-w-lg flex-col gap-6 lg:flex">
        <Badge variant="outline" class="w-fit border-primary-border text-primary">Kanchi</Badge>
        <h1 class="text-4xl font-semibold leading-tight text-text-primary">
          Real-time clarity for every Celery task.
        </h1>
        <p class="text-base text-text-secondary">
          Stream task events, stay ahead of failures, and keep your queues healthy without hopping across dashboards.
        </p>
        <div class="space-y-4 rounded-2xl border border-border-subtle bg-background-surface p-6 shadow-sm">
          <div class="flex items-center gap-3">
            <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-primary-bg text-primary">
              <Sparkles class="h-5 w-5" />
            </div>
            <div class="space-y-1">
              <p class="text-sm font-medium text-text-primary">Unified visibility</p>
              <p class="text-xs text-text-secondary">
                One surface for queues, workers, workflows, and historical context.
              </p>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-background-raised text-text-secondary">
              <Activity class="h-5 w-5" />
            </div>
            <div class="space-y-1">
              <p class="text-sm font-medium text-text-primary">Instant insight</p>
              <p class="text-xs text-text-secondary">
                Jump from alert to root cause with task timelines and worker state.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div class="w-full max-w-md justify-self-center">
        <Card class="shadow-xl">
          <CardHeader class="space-y-2 pb-4">
            <CardTitle class="text-2xl font-semibold text-text-primary">Sign in to Kanchi</CardTitle>
            <CardDescription v-if="authEnabled" class="text-sm text-text-secondary">
              Choose your preferred sign-in method. Sessions persist until you sign out.
            </CardDescription>
            <CardDescription v-else class="text-sm text-text-secondary">
              Authentication is disabled for this workspace.
            </CardDescription>
          </CardHeader>
          <CardContent class="space-y-5">
            <form
              v-if="authEnabled && config?.basic_enabled"
              class="space-y-4"
              @submit.prevent="submitBasic"
            >
              <AuthTextField
                id="username"
                v-model="username"
                label="Username"
                type="text"
                autocomplete="username"
                placeholder="your.name"
                required
              />
              <AuthTextField
                id="password"
                v-model="password"
                label="Password"
                type="password"
                autocomplete="current-password"
                placeholder="••••••••"
                required
              />
              <Button
                type="submit"
                variant="primary"
                class="flex h-11 w-full items-center justify-center rounded-md text-sm font-medium transition-all duration-200 shadow-none hover:shadow-glow-sm"
                :disabled="submitting"
              >
                {{ submitting ? 'Signing in…' : 'Sign in' }}
              </Button>
            </form>

            <div v-if="authEnabled && hasOAuthAndBasic" class="relative">
              <div class="absolute inset-x-0 top-1/2 -translate-y-1/2 flex items-center justify-center">
                <span class="bg-background-surface px-2 text-[11px] uppercase tracking-[0.2em] text-text-muted">
                  or
                </span>
              </div>
              <div class="border-t border-border-subtle" />
            </div>

            <div
              v-if="authEnabled && providerOptions.length"
              :class="[
                'grid gap-3',
                providerOptions.length > 1 ? 'sm:grid-cols-2' : 'grid-cols-1',
              ]"
            >
              <Button
                v-for="provider in providerOptions"
                :key="provider.id"
                type="button"
                variant="outline"
                :class="[
                  'flex w-full items-center gap-3 rounded-md border border-border-subtle bg-background-surface text-sm text-text-primary transition-colors duration-200 group cursor-pointer',
                  providerOptions.length === 1
                    ? 'h-11 justify-center font-medium hover:border-primary-border hover:bg-background-base'
                    : 'h-10 justify-start hover:border-primary-border hover:bg-background-base',
                ]"
                :disabled="oauthInProgress === provider.id || submitting"
                @click="startOAuth(provider.id)"
              >
                <component
                  :is="provider.icon"
                  :class="[
                    providerOptions.length === 1 ? 'h-5 w-5' : 'h-4 w-4',
                  ]"
                />
                <span>{{ `Continue with ${provider.label}` }}</span>
                <Loader2
                  v-if="oauthInProgress === provider.id"
                  :class="[
                    'animate-spin',
                    providerOptions.length === 1 ? 'ml-3 h-4 w-4' : 'ml-auto h-4 w-4',
                  ]"
                />
              </Button>
            </div>

            <div
              v-if="authEnabled && error"
              class="rounded-lg border border-status-error-border bg-status-error-bg px-3 py-2 text-sm text-status-error"
            >
              {{ error }}
            </div>

            <div v-if="!authEnabled" class="space-y-3">
              <p class="text-sm text-text-secondary">
                Anyone with the link can explore the dashboard. Return to the main view when you're ready.
              </p>
              <Button as="NuxtLink" to="/" variant="secondary" class="w-full">
                Go to dashboard
              </Button>
            </div>
          </CardContent>
        </Card>
        <p v-if="authEnabled" class="mt-6 text-center text-xs text-text-muted">
          Single sign-on honours your workspace policies. Sessions can be revoked from Workspace settings.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Component } from 'vue'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useAuthStore } from '~/stores/auth'
import { useSessionStore } from '~/stores/session'
import { useApiService } from '~/services/apiClient'
import type { AuthProvider, LoginResponseDTO } from '~/services/apiClient'
import { Badge } from '~/components/ui/badge'
import { Button } from '~/components/ui/button'
import AuthTextField from '~/components/ui/text-field/AuthTextField.vue'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '~/components/ui/card'
import IconBrandGoogle from '~/components/icons/IconBrandGoogle.vue'
import { Activity, Github, Loader2, Sparkles } from 'lucide-vue-next'
import { usePublicEnv } from '~/composables/usePublicEnv'

const router = useRouter()
const authStore = useAuthStore()
const sessionStore = useSessionStore()
const apiService = useApiService()
const { apiUrl } = usePublicEnv()

const { authEnabled, oauthProviders, isAuthenticated, config } = storeToRefs(authStore)

const username = ref('')
const password = ref('')
const submitting = ref(false)
const error = ref<string | null>(null)
const oauthInProgress = ref<AuthProvider | null>(null)

interface ProviderMeta {
  label: string
  icon: Component
}

const providerMeta: Record<AuthProvider, ProviderMeta> = {
  github: {
    label: 'GitHub',
    icon: Github,
  },
  google: {
    label: 'Google',
    icon: IconBrandGoogle,
  },
}

const providerOptions = computed(() => {
  return oauthProviders.value
    .map(provider => provider as AuthProvider)
    .filter(provider => providerMeta[provider])
    .map(provider => ({
      id: provider,
      ...providerMeta[provider],
    }))
    .sort((a, b) => a.label.localeCompare(b.label))
})

const hasOAuthAndBasic = computed(() =>
  Boolean(config.value?.basic_enabled && providerOptions.value.length)
)

function resolveAllowedOrigins(): Set<string> {
  const origins = new Set<string>()
  if (process.client) {
    origins.add(window.location.origin)
  }
  if (apiUrl) {
    try {
      origins.add(new URL(apiUrl).origin)
    } catch (err) {
      console.warn('[OAuth] Failed to parse apiUrl origin:', err)
    }
  }
  return origins
}

async function handleOAuthMessage(event: MessageEvent) {
  if (!event?.data || typeof event.data !== 'object') {
    return
  }

  const allowedOrigins = resolveAllowedOrigins()
  if (!allowedOrigins.has(event.origin)) {
    return
  }

  const { type, payload } = event.data as { type: string; payload?: unknown }

  if (type === 'oauth-complete') {
    oauthInProgress.value = null
    if ((payload as any)?.error) {
      error.value = (payload as any).error as string
      return
    }

    try {
      await authStore.handleOAuthLogin(payload as LoginResponseDTO)
      await router.push('/')
    } catch (err: any) {
      console.error('[Auth] Failed to process OAuth payload:', err)
      error.value = err?.message || 'OAuth login failed'
    }
  }
}

onMounted(async () => {
  window.addEventListener('message', handleOAuthMessage)

  if (authEnabled.value) {
    await sessionStore.ensureInitialized({ persist: false })
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('message', handleOAuthMessage)
})

watch(isAuthenticated, (newValue) => {
  if (newValue && authEnabled.value) {
    router.push('/')
  }
})

async function submitBasic() {
  submitting.value = true
  error.value = null

  try {
    await authStore.loginWithBasic(username.value, password.value)
    router.push('/')
  } catch (err: any) {
    error.value = err?.message || 'Login failed'
  } finally {
    submitting.value = false
  }
}

async function startOAuth(provider: AuthProvider) {
  error.value = null
  oauthInProgress.value = provider

  try {
    await sessionStore.ensureInitialized({ persist: false })
    const authUrl = await apiService.getOAuthAuthorizationUrl(provider, {
      sessionId: sessionStore.sessionId as string | undefined,
      redirectTo: window.location.origin + '/login',
    })

    window.open(authUrl.authorization_url, 'kanchi-oauth', 'width=480,height=640')
  } catch (err: any) {
    error.value = err?.message || 'Unable to start OAuth flow'
    oauthInProgress.value = null
  }
}

watch(authEnabled, (enabled) => {
  if (!enabled) {
    router.push('/')
  }
})
</script>
