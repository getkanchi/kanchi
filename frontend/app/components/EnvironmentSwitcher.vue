<template>
  <DropdownMenu>
    <DropdownMenuTrigger as-child>
      <button
        class="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-md transition-colors border border-border bg-background-surface hover:bg-background-hover text-text-primary"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 3v18h18"/>
          <path d="M18 17V9"/>
          <path d="M13 17V5"/>
          <path d="M8 17v-3"/>
        </svg>
        <span>{{ displayName }}</span>
        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="6 9 12 15 18 9"/>
        </svg>
      </button>
    </DropdownMenuTrigger>

    <DropdownMenuContent class="w-64 bg-background-surface border-border" align="end">
      <DropdownMenuLabel class="text-text-secondary text-xs font-semibold uppercase">
        Environment Filter
      </DropdownMenuLabel>
      <DropdownMenuSeparator class="bg-border" />

      <DropdownMenuItem
        class="cursor-pointer text-text-primary hover:bg-background-hover focus:bg-background-hover"
        :class="{ 'bg-background-active': !environmentStore.hasActiveEnvironment }"
        @click="deactivateAll"
      >
        <div class="flex items-center justify-between w-full">
          <span>All Environments</span>
          <Badge v-if="!environmentStore.hasActiveEnvironment" variant="online" class="ml-2">Active</Badge>
        </div>
      </DropdownMenuItem>

      <DropdownMenuSeparator v-if="environmentStore.environments.length > 0" class="bg-border" />

      <DropdownMenuItem
        v-for="env in environmentStore.environments"
        :key="env.id"
        class="cursor-pointer text-text-primary hover:bg-background-hover focus:bg-background-hover"
        :class="{ 'bg-background-active': env.is_active }"
        @click="activateEnvironment(env.id)"
      >
        <div class="flex flex-col w-full">
          <div class="flex items-center justify-between">
            <span class="font-medium">{{ env.name }}</span>
            <Badge v-if="env.is_active" variant="online" class="ml-2">Active</Badge>
            <Badge v-else-if="env.is_default" variant="default" class="ml-2">Default</Badge>
          </div>
          <div v-if="env.description" class="text-xs text-text-secondary mt-0.5">
            {{ env.description }}
          </div>
          <div class="text-xs text-text-secondary mt-1 space-y-0.5">
            <div v-if="env.queue_patterns.length > 0">
              <span class="font-semibold">Queues:</span> {{ env.queue_patterns.join(', ') }}
            </div>
            <div v-if="env.worker_patterns.length > 0">
              <span class="font-semibold">Workers:</span> {{ env.worker_patterns.join(', ') }}
            </div>
          </div>
        </div>
      </DropdownMenuItem>

      <DropdownMenuSeparator class="bg-border" />

      <DropdownMenuItem
        class="cursor-pointer text-text-secondary hover:text-text-primary hover:bg-background-hover focus:bg-background-hover"
        @click="openManageDialog"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-2">
          <circle cx="12" cy="12" r="3"/>
          <path d="M12 1v6m0 6v6"/>
          <path d="m4.93 4.93 4.24 4.24m5.66 5.66 4.24 4.24"/>
          <path d="M1 12h6m6 0h6"/>
          <path d="m4.93 19.07 4.24-4.24m5.66-5.66 4.24-4.24"/>
        </svg>
        Manage Environments...
      </DropdownMenuItem>
    </DropdownMenuContent>
  </DropdownMenu>

  <!-- Management Dialog -->
  <EnvironmentManagementDialog v-model:open="isManageDialogOpen" />
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useEnvironmentStore } from '~/stores/environment'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '~/components/ui/dropdown-menu'
import { Badge } from '~/components/ui/badge'
import EnvironmentManagementDialog from '~/components/EnvironmentManagementDialog.vue'

const environmentStore = useEnvironmentStore()
const isManageDialogOpen = ref(false)

const displayName = computed(() => {
  if (environmentStore.activeEnvironment) {
    return environmentStore.activeEnvironment.name
  }
  return 'All Environments'
})

async function activateEnvironment(id: string) {
  try {
    await environmentStore.activateEnvironment(id)
  } catch (err) {
    console.error('Failed to activate environment:', err)
  }
}

async function deactivateAll() {
  try {
    await environmentStore.deactivateAll()
  } catch (err) {
    console.error('Failed to deactivate environments:', err)
  }
}

function openManageDialog() {
  isManageDialogOpen.value = true
}
</script>
