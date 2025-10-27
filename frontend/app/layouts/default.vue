<template>
  <div class="min-h-screen bg-background-base text-text-primary relative">
    <!-- Top Navigation Bar -->
    <Navbar />
    
    <!-- Main Content -->
    <main class="max-w-7xl mx-auto relative z-10 p-6">
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
