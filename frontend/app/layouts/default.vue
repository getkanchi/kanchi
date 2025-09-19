<template>
  <div class="min-h-screen bg-background-base text-text-primary relative">
    <!-- Dotted grid background -->
    <div
      class="absolute inset-0 opacity-20 pointer-events-none"
      style="
        background-image: radial-gradient(circle, rgb(255,255,255) 1px, transparent 1px);
        background-size: 25px 25px;
      "
    ></div>
    
    <!-- Top Navigation Bar -->
    <Navbar />
    
    <!-- Main Content -->
    <main class="relative z-10">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import Navbar from '~/components/navbar.vue'
</script>