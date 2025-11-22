<template>
  <component
    :is="interactive ? Button : 'div'"
    v-bind="interactive ? buttonAttrs : {}"
    class="relative inline-flex items-center justify-center w-6 h-6 rounded-lg transition-all duration-200 bg-background-base hover:bg-background-surface border border-border group"
    :aria-label="interactive ? `Switch to ${nextThemeLabel} theme` : undefined"
    :role="interactive ? undefined : 'presentation'"
  >
    <!-- Dark mode icon -->
    <svg
      v-if="resolvedTheme === 'dark'"
      xmlns="http://www.w3.org/2000/svg"
      class="w-4 h-4 text-text-primary transition-transform duration-200 group-hover:rotate-12"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="2"
        d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
      />
    </svg>

    <!-- Light mode icon -->
    <svg
      v-else
      xmlns="http://www.w3.org/2000/svg"
      class="w-4 h-4 text-text-primary transition-transform duration-200 group-hover:rotate-45"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="2"
        d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
      />
    </svg>
  </component>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useTheme } from '~/composables/useTheme'
import { Button } from '~/components/ui/button'

const props = withDefaults(defineProps<{
  interactive?: boolean
}>(), {
  interactive: true
})

const { theme, resolvedTheme, toggleTheme } = useTheme()

const nextThemeLabel = computed(() => {
  switch (theme.value) {
    case 'dark':
      return 'light'
    case 'light':
      return 'dark'
    case 'system':
      return 'dark'
    default:
      return 'dark'
  }
})

const buttonAttrs = computed(() => props.interactive ? { type: 'button', onClick: toggleTheme } : {})
</script>
