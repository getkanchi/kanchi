<template>
  <div class="flex ml-auto items-center gap-4">
    <EnvironmentSwitcher v-if="showEnvironmentSwitcher" />

    <DropdownMenu>
      <DropdownMenuTrigger as-child>
        <button
          type="button"
          class="relative inline-flex h-10 w-10 items-center justify-center rounded-full border border-border bg-background-surface transition hover:border-primary-border focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-border"
        >
          <Avatar class="h-9 w-9">
            <AvatarImage v-if="avatarSrc" :src="avatarSrc" :alt="currentUserName" />
            <AvatarFallback>{{ avatarFallback }}</AvatarFallback>
          </Avatar>
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align="end"
        class="w-64 rounded-xl border border-border bg-background-surface p-0 shadow-xl"
      >
        <div class="flex items-center gap-3 px-4 pt-4 pb-3">
          <Avatar class="h-10 w-10">
            <AvatarImage v-if="avatarSrc" :src="avatarSrc" :alt="currentUserName" />
            <AvatarFallback class="text-sm">{{ avatarFallback }}</AvatarFallback>
          </Avatar>
          <div class="min-w-0">
            <p class="text-sm font-semibold text-text-primary truncate">
              {{ currentUserName }}
            </p>
            <p class="text-xs text-text-secondary truncate">
              {{ currentUserEmail }}
            </p>
          </div>
        </div>

        <DropdownMenuSeparator />

        <div class="space-y-2 p-3">
          <button
            type="button"
            class="flex items-center justify-between w-full rounded-lg border border-border bg-background-base px-3 py-2 text-left transition hover:border-primary-border hover:text-primary hover:bg-background-hover cursor-default focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-border"
            @click="toggleTheme"
          >
            <span class="text-sm font-medium">Toggle theme</span>
            <ThemeToggle :interactive="false" />
          </button>

          <DropdownMenuItem as-child>
            <NuxtLink
              to="/settings/workspace"
              class="flex items-center justify-between rounded-lg border border-border bg-background-base px-3 py-2 text-sm font-medium text-text-primary transition hover:border-primary-border hover:text-primary"
            >
              Workspace settings
              <ArrowUpRight class="h-3.5 w-3.5 text-text-muted" />
            </NuxtLink>
          </DropdownMenuItem>

          <DropdownMenuItem as-child>
            <a
              href="https://github.com/getkanchi/kanchi/issues"
              target="_blank"
              rel="noreferrer"
              class="flex items-center justify-between rounded-lg border border-border bg-background-base px-3 py-2 text-sm font-medium text-text-primary transition hover:border-primary-border hover:text-primary"
            >
              Report an issue
              <ArrowUpRight class="h-3.5 w-3.5 text-text-muted" />
            </a>
          </DropdownMenuItem>

          <DropdownMenuItem
            v-if="authEnabled && isAuthenticated"
            class="flex items-center justify-between rounded-lg bg-background-base px-3 py-2 text-sm font-medium text-text-primary transition hover:bg-background-hover"
            @select="handleLogout"
          >
            <span>Sign out</span>
            <LogOut class="h-4 w-4 text-text-muted" />
          </DropdownMenuItem>

          <DropdownMenuItem
            v-else-if="authEnabled"
            as-child
          >
            <NuxtLink
              to="/login"
              class="flex items-center justify-between rounded-lg border border-border bg-background-base px-3 py-2 text-sm font-medium text-text-primary transition hover:border-primary-border hover:text-primary"
            >
              Sign in
              <LogIn class="h-4 w-4 text-text-muted" />
            </NuxtLink>
          </DropdownMenuItem>
        </div>

        <div class="px-4 pb-4">
          <a
            :href="changelogUrl"
            target="_blank"
            rel="noreferrer"
            class="inline-flex"
          >
            <Badge variant="outline" class="text-[11px] font-semibold px-2 py-1 gap-1 inline-flex items-center hover:bg-background-hover">
              {{ displayVersion }}
              <ArrowUpRight class="h-3.5 w-3.5" />
            </Badge>
          </a>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ArrowUpRight, LogIn, LogOut } from 'lucide-vue-next'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '~/components/ui/dropdown-menu'
import { Badge } from "~/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from '~/components/ui/avatar'
import EnvironmentSwitcher from "~/components/EnvironmentSwitcher.vue"
import ThemeToggle from '~/components/ThemeToggle.vue'
import { useTheme } from '~/composables/useTheme'
import { useAuthStore } from '~/stores/auth'
import { storeToRefs } from 'pinia'
import { useAppVersion } from '~/composables/useAppVersion'

const authStore = useAuthStore()
const { authEnabled, isAuthenticated, user } = storeToRefs(authStore)
const { displayVersion, changelogUrl } = useAppVersion()
const { toggleTheme } = useTheme()

const showEnvironmentSwitcher = computed(() => !authEnabled.value || isAuthenticated.value)
const currentUserName = computed(() => user.value?.name || user.value?.email || 'Kanchi user')
const currentUserEmail = computed(() => user.value?.email || (authEnabled.value ? 'Signed out' : 'Welcome'))
const avatarSrc = computed(() => user.value?.avatar_url || null)
const avatarFallback = computed(() => {
  const source = user.value?.name || user.value?.email || 'Kanchi'
  const trimmed = source.trim()
  return trimmed ? trimmed.charAt(0).toUpperCase() : 'K'
})

async function handleLogout() {
  await authStore.logout()
  await navigateTo('/login')
}
</script>
