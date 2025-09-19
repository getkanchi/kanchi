<template>
  <div class="relative z-10 bg-background-base text-text-primary border-b border-card-border">
    <div class="container px-6">
      <div class="flex h-14 items-center gap-8">
        <!-- Logo -->
        <div class="flex items-center">
          <img src="/logo.svg" alt="Kanchi" class="h-10 w-auto" style="filter: brightness(0) invert(1) opacity(0.95);" />
        </div>

        <!-- Navigation Menu -->
        <NavigationMenu>
          <NavigationMenuList>
            <NavigationMenuItem>
              <NavigationMenuLink 
                href="#"
                class="group inline-flex h-8 w-max items-center justify-center rounded-md bg-transparent px-3 py-1 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground focus:outline-none disabled:pointer-events-none disabled:opacity-50"
              >
                Workers
              </NavigationMenuLink>
            </NavigationMenuItem>
            <NavigationMenuItem>
              <NavigationMenuLink 
                href="#"
                class="group inline-flex h-8 w-max items-center justify-center rounded-md bg-transparent px-3 py-1 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground focus:outline-none disabled:pointer-events-none disabled:opacity-50"
              >
                Tasks
              </NavigationMenuLink>
            </NavigationMenuItem>
          </NavigationMenuList>
        </NavigationMenu>
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
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');
</style>
