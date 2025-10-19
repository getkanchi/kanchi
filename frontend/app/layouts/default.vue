<template>
  <div class="min-h-screen bg-background-base text-text-primary relative">
    <!-- Dotted grid background -->
    <div
      class="absolute inset-0 opacity-20 pointer-events-none bg-dots"
    ></div>
    
    <!-- Top Navigation Bar -->
    <Navbar />
    
    <!-- Main Content -->
    <main class="relative z-10 p-6">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import Navbar from '~/components/navbar.vue'
import { useEnvironmentStore } from '~/stores/environment'

const environmentStore = useEnvironmentStore()

onMounted(async () => {
  await environmentStore.initialize()
})
</script>
