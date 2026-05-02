<template>
  <aside class="flex h-full w-[280px] flex-col border-r border-border-subtle bg-background-surface/95 backdrop-blur-sm">
    <div class="flex h-16 items-center gap-3 border-b border-border-subtle px-5">
      <div>
        <p class="text-sm font-semibold tracking-[0.24em] text-text-secondary uppercase">Kanchi</p>
        <p class="text-lg font-semibold text-text-primary">Control center</p>
      </div>
    </div>

    <div class="flex min-h-0 flex-1 flex-col px-3 py-4">
      <div class="space-y-1">
        <p class="px-3 pb-2 text-[11px] font-semibold uppercase tracking-[0.28em] text-text-muted">Workspace</p>
        <NuxtLink
          v-for="item in primaryItems"
          :key="item.to"
          :to="item.to"
          class="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors"
          :class="linkClass(item.active())"
        >
          <component :is="item.icon" class="h-4 w-4" />
          <span>{{ item.label }}</span>
        </NuxtLink>
      </div>

      <div class="mt-auto space-y-3 pt-6">
        <div class="rounded-2xl border border-border-subtle bg-background-base/80 p-2">
          <Collapsible v-model:open="settingsOpen">
            <CollapsibleTrigger as-child>
              <button
                type="button"
                class="flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-left text-sm font-medium transition-colors"
                :class="linkClass(isSettingsRoute)"
              >
                <span class="flex items-center gap-3">
                  <Settings2 class="h-4 w-4" />
                  Settings
                </span>
                <ChevronDown class="h-4 w-4 transition-transform" :class="settingsOpen ? 'rotate-180' : ''" />
              </button>
            </CollapsibleTrigger>
            <CollapsibleContent class="space-y-1 px-2 pb-2 pt-1">
              <NuxtLink
                v-for="item in settingsItems"
                :key="item.to"
                :to="item.to"
                class="flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition-colors"
                :class="subLinkClass(item.active())"
              >
                <component :is="item.icon" class="h-4 w-4" />
                <span>{{ item.label }}</span>
              </NuxtLink>
            </CollapsibleContent>
          </Collapsible>
        </div>

        <div class="rounded-2xl border border-border-subtle bg-background-base/80 p-4 space-y-3">
          <div class="flex items-center justify-between gap-3">
            <div>
              <p class="text-sm font-medium text-text-primary">Agent link</p>
              <p class="text-xs text-text-secondary">Realtime connectivity</p>
            </div>
            <Popover>
              <PopoverTrigger as-child>
                <Badge :variant="displayConnected ? 'online' : 'offline'" class="cursor-pointer">
                  <StatusDot :status="displayConnected ? 'online' : 'offline'" :pulse="displayConnected" class="mr-2" />
                  {{ displayConnected ? 'Connected' : 'Offline' }}
                </Badge>
              </PopoverTrigger>
              <PopoverContent class="w-[360px] bg-background-surface border-border-subtle text-text-primary p-4">
                <div class="mb-3">
                  <h3 class="font-semibold text-sm text-text-primary">Agent connection details</h3>
                </div>
                <AgentConnectionDetails />
              </PopoverContent>
            </Popover>
          </div>

          <div class="rounded-xl border border-border-subtle bg-background-surface px-3 py-2">
            <UserControls />
          </div>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from '#imports'
import { ChevronDown, ClipboardList, LayoutDashboard, ScrollText, Settings2, Workflow } from 'lucide-vue-next'
import { Badge } from '~/components/ui/badge'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '~/components/ui/collapsible'
import { Popover, PopoverContent, PopoverTrigger } from '~/components/ui/popover'
import AgentConnectionDetails from '~/components/AgentConnectionDetails.vue'
import StatusDot from '~/components/StatusDot.vue'
import UserControls from '~/components/UserControls.vue'
import { useAuthStore } from '~/stores/auth'
import { storeToRefs } from 'pinia'

const route = useRoute()
const wsStore = useWebSocketStore()
const authStore = useAuthStore()
const { authEnabled, isAuthenticated } = storeToRefs(authStore)

const isClientSide = ref(false)
const settingsOpen = ref(route.path.startsWith('/settings'))

onMounted(() => {
  isClientSide.value = true
})

watch(
  () => route.path,
  (path) => {
    if (path.startsWith('/settings')) {
      settingsOpen.value = true
    }
  },
)

const displayConnected = computed(() => isClientSide.value && wsStore.isConnected)
const canNavigate = computed(() => !authEnabled.value || isAuthenticated.value)
const isSettingsRoute = computed(() => route.path.startsWith('/settings'))

const primaryItems = computed(() => {
  if (!canNavigate.value) return []
  return [
    { label: 'Dashboard', to: '/', icon: LayoutDashboard, active: () => route.path === '/' },
    { label: 'Tasks', to: '/tasks', icon: ClipboardList, active: () => route.path.startsWith('/tasks') },
    { label: 'Workflows', to: '/workflows', icon: Workflow, active: () => route.path.startsWith('/workflows') },
  ]
})

const settingsItems = computed(() => {
  if (!canNavigate.value) return []
  return [
    { label: 'Workspace', to: '/settings/workspace', icon: Settings2, active: () => route.path.startsWith('/settings/workspace') },
    { label: 'Audit log', to: '/settings/audit', icon: ScrollText, active: () => route.path.startsWith('/settings/audit') },
  ]
})

function linkClass(active: boolean) {
  return active
    ? 'bg-primary/10 text-text-primary border border-primary/20'
    : 'text-text-secondary hover:bg-background-hover hover:text-text-primary border border-transparent'
}

function subLinkClass(active: boolean) {
  return active
    ? 'bg-background-hover text-text-primary'
    : 'text-text-secondary hover:bg-background-hover hover:text-text-primary'
}
</script>
