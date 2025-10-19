<script setup lang="ts">
import { onMounted } from 'vue'
import { useSessionStore } from '~/stores/session'

const sessionStore = useSessionStore()

onMounted(async () => {
  try {
    await sessionStore.initialize()
  } catch (err) {
    console.error('[App] Failed to initialize session:', err)
    // App can still work without session, just won't have persistent prefs
  }
})
</script>

<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>
