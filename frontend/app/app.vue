<script setup lang="ts">
import { onMounted } from 'vue'
onMounted(() => {
  // All auth/session bootstrap logic runs in a dedicated plugin.
})
</script>

<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>
