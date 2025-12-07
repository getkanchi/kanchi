<template>
  <div class="flex h-screen w-64 flex-col border-r border-border-subtle bg-background">
    <!-- Logo/App Name -->
    <div class="flex h-16 items-center border-b px-6">
      <div class="flex items-center gap-3">
        <span class="text-2xl font-bold text-primary">Kanchi</span>
        <span class="text-2xl" style="font-family: 'Noto Sans JP', sans-serif;">感知</span>
      </div>
    </div>

    <!-- Navigation Items -->
    <nav class="flex-1 space-y-1 px-3 py-4">
      <NuxtLink
        to="/"
        class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground"
        :class="{ 'bg-accent text-accent-foreground': $route.path === '/' }"
      >
        <UsersIcon class="h-4 w-4" />
        Workers
      </NuxtLink>
      
      <NuxtLink
        to="/tasks"
        class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground"
        :class="{ 'bg-accent text-accent-foreground': $route.path === '/tasks' }"
      >
        <ListChecksIcon class="h-4 w-4" />
        Tasks
      </NuxtLink>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { UsersIcon, ListChecksIcon } from 'lucide-vue-next'

const route = useRoute()
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');
</style>