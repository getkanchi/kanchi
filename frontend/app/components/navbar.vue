<template>
  <div class="navbar sticky top-0 z-50 bg-background-surface border-b border-border-subtle backdrop-blur-sm bg-opacity-95 relative overflow-hidden">
    <div class="px-6">
      <div class="flex h-14 items-center">
        <div class="flex items-center gap-6">
          <!-- Logo -->
<!--          <div class="flex items-center">-->
<!--            <img src="/logo.svg" alt="Kanchi" class="h-10 w-auto" style="filter: brightness(0) invert(1) opacity(0.95);" />-->
<!--          </div>-->

          <!-- Navigation Menu -->
          <NavigationMenu v-if="showNavigationMenu">
            <NavigationMenuList class="flex items-center gap-2">
              <NavigationMenuItem v-for="item in navItems" :key="item.path">
                <NavigationMenuLink
                  as-child
                  :active="isActive(item.path)"
                >
                  <NuxtLink
                    :to="item.path"
                    class="nav-link"
                    :class="linkClass(item.path)"
                  >
                    {{ item.label }}
                  </NuxtLink>
                </NavigationMenuLink>
              </NavigationMenuItem>

              <div class="h-4 w-px bg-border mx-2"></div>

              <NavigationMenuItem>
                <!-- Agent Connection Status -->
                <Popover>
                  <PopoverTrigger as-child>
                    <Badge
                      :variant="displayConnected ? 'online' : 'offline'"
                      class="cursor-pointer hover:bg-background-hover"
                    >
                      <StatusDot
                        :status="displayConnected ? 'online' : 'offline'"
                        :pulse="displayConnected"
                        class="mr-2"
                      />
                      {{ displayConnected ? "Connected" : "Disconnected" }}
                    </Badge>
                  </PopoverTrigger>
                  <PopoverContent class="w-[420px] bg-background-surface border-border-subtle text-text-primary p-4">
                    <div class="mb-3">
                      <h3 class="font-semibold text-sm text-text-primary">Agent Connection Details</h3>
                    </div>
                    <AgentConnectionDetails ref="connectionDetailsRef" />
                  </PopoverContent>
                </Popover>
              </NavigationMenuItem>
            </NavigationMenuList>
          </NavigationMenu>
          <div v-else-if="showAuthPrompt" class="text-sm text-text-secondary">
            Please sign in to access navigation.
          </div>
          <div v-else-if="isLoginRoute" class="text-sm font-medium text-text-secondary">
            Kanchi
          </div>
        </div>
        <UserControls v-if="showUserControls" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from '#imports'
import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
} from '@/components/ui/navigation-menu'
import { Badge } from "~/components/ui/badge"
import StatusDot from "~/components/StatusDot.vue"
import AgentConnectionDetails from "~/components/AgentConnectionDetails.vue"
import { useAuthStore } from '~/stores/auth'
import { storeToRefs } from 'pinia'
import { Popover, PopoverContent, PopoverTrigger } from "~/components/ui/popover"
import UserControls from '~/components/UserControls.vue'

// Use the WebSocket store instead of the composable
const wsStore = useWebSocketStore()
const connectionDetailsRef = ref<InstanceType<typeof AgentConnectionDetails> | null>(null)
const route = useRoute()

const authStore = useAuthStore()
const { authEnabled, isAuthenticated } = storeToRefs(authStore)

// Force client-side only rendering to avoid hydration mismatch
const isClientSide = ref(false)
onMounted(() => {
  isClientSide.value = true
})

const displayConnected = computed(() => isClientSide.value && wsStore.isConnected)

const isLoginRoute = computed(() => route.path === '/login')
const showNavigationMenu = computed(() => !isLoginRoute.value && (!authEnabled.value || isAuthenticated.value))
const showAuthPrompt = computed(() => !isLoginRoute.value && authEnabled.value && !isAuthenticated.value)
const showUserControls = computed(() => !isLoginRoute.value)
const navItems = [
  { label: 'Dashboard', path: '/' },
  { label: 'Tasks', path: '/tasks' },
  { label: 'Workflows', path: '/workflows' },
]

const isActive = (path: string) => {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

const linkClass = (path: string) => {
  const active = isActive(path)
  return active
    ? 'active'
    : 'inactive'
}

onMounted(() => {
  // client only
})
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');

.nav-link {
  position: relative;
  padding: 0.5rem 1rem;
  font-size: 0.85rem;
  border-radius: 0.5rem;
  transition: color 180ms ease, background-color 180ms ease, border-color 180ms ease;
}

.nav-link::after {
  content: '';
  position: absolute;
  left: 12%;
  right: 12%;
  bottom: -6px;
  height: 2px;
  border-radius: 9999px;
  background: currentColor;
  transform-origin: center;
  transform: scaleX(0);
  transition: transform 200ms ease;
}

.nav-link.active {
  color: var(--color-text-primary, #fff);
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.08);
}

.nav-link.active::after {
  transform: scaleX(1);
}

.nav-link.inactive {
  color: var(--color-text-secondary, #94a3b8);
}

.nav-link.inactive:hover {
  color: var(--color-text-primary, #fff);
}

.navbar::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--border-subtle), transparent);
}
</style>
