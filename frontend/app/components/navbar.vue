<template>
  <div class="relative z-10">
    <div class="container px-6">
      <div class="flex h-14 items-center justify-between">
        <div class="flex items-center gap-8">
          <!-- Logo -->
<!--          <div class="flex items-center">-->
<!--            <img src="/logo.svg" alt="Kanchi" class="h-10 w-auto" style="filter: brightness(0) invert(1) opacity(0.95);" />-->
<!--          </div>-->

          <!-- Navigation Menu -->
          <NavigationMenu>
            <NavigationMenuList>
              <NavigationMenuItem>
              <!-- Right side: Agent Connection Status -->
              <div class="flex items-center">
                <Popover>
                  <PopoverTrigger as-child>
                    <Badge
                      :variant="isConnected ? 'online' : 'offline'"
                      class="cursor-pointer"
                    >
                      <StatusDot
                        :status="isConnected ? 'online' : 'offline'"
                        :pulse="isConnected"
                        class="mr-2"
                      />
                      {{ isConnected ? "Agent Connected" : "Agent Disconnected" }}
                    </Badge>
                  </PopoverTrigger>
                  <PopoverContent class="w-80 bg-card-base border-card-border text-text-primary">
                    <div class="space-y-2">
                      <h4 class="font-medium text-text-primary">Agent Connection Details</h4>
                      <div class="text-sm text-text-secondary space-y-1.5">
                        <p><strong class="text-text-primary">Status:</strong> <span class="font-bold">{{ isConnected ? "Connected" : "Disconnected" }}</span></p>
                        <p><strong class="text-text-primary">WebSocket URL:</strong> <code class="text-xs bg-background-primary px-1 py-0.5 rounded">ws://localhost:8765/ws</code></p>
                        <p><strong class="text-text-primary">Last Update:</strong> <code class="text-xs bg-background-primary px-1 py-0.5 rounded">{{ new Date().toLocaleTimeString() }}</code></p>
                      </div>
                    </div>
                  </PopoverContent>
                </Popover>
              </div>
                </NavigationMenuItem>
            </NavigationMenuList>
          </NavigationMenu>
        </div>

        </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
} from '@/components/ui/navigation-menu'
import { Badge } from "~/components/ui/badge"
import { Popover, PopoverContent, PopoverTrigger } from "~/components/ui/popover"
import StatusDot from "~/components/StatusDot.vue"
import { useWebSocketSingleton } from "~/composables/useWebsocketSingleton"

// Use the singleton websocket composable to get connection status
const { isConnected } = useWebSocketSingleton("ws://localhost:8765/ws")
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');
</style>
