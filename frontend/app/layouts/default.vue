<template>
  <div class="min-h-screen bg-background-base text-text-primary relative">
    <!-- Top Navigation Bar -->
    <Navbar />
    
    <!-- Main Content -->
    <main class="w-full max-w-screen-2xl 2xl:max-w-[calc(60vw-3rem)] mx-auto relative z-10 px-4 sm:px-6 lg:px-8 py-6">
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
