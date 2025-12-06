<template>
  <div class="sticky top-0 z-50 bg-background-surface border-b border-border-subtle backdrop-blur-sm bg-opacity-95">
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
              <NavigationMenuItem>
                <NavigationMenuLink
                  as-child
                  :active="$route.path === '/'"
                >
                  <NuxtLink
                    to="/"
                    class="px-4 py-2 text-sm font-medium rounded-md transition-colors"
                    :class="$route.path === '/'
                      ? 'bg-background-active text-text-primary'
                      : 'text-text-secondary hover:bg-background-hover hover:text-text-primary'"
                  >
                    Dashboard
                  </NuxtLink>
                </NavigationMenuLink>
              </NavigationMenuItem>

              <NavigationMenuItem>
                <NavigationMenuLink
                  as-child
                  :active="$route.path.startsWith('/tasks')"
                >
                  <NuxtLink
                    to="/tasks"
                    class="px-4 py-2 text-sm font-medium rounded-md transition-colors"
                    :class="$route.path.startsWith('/tasks')
                      ? 'bg-background-active text-text-primary'
                      : 'text-text-secondary hover:bg-background-hover hover:text-text-primary'"
                  >
                    Tasks
                  </NuxtLink>
                </NavigationMenuLink>
              </NavigationMenuItem>

              <NavigationMenuItem>
                <NavigationMenuLink
                  as-child
                  :active="$route.path.startsWith('/workflows')"
                >
                  <NuxtLink
                    to="/workflows"
                    class="px-4 py-2 text-sm font-medium rounded-md transition-colors"
                    :class="$route.path.startsWith('/workflows')
                      ? 'bg-background-active text-text-primary'
                      : 'text-text-secondary hover:bg-background-hover hover:text-text-primary'"
                  >
                    Workflows
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
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');
</style>
