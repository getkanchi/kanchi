<template>
  <span
    :class="cn(tagVariants({ variant, size, interactive }), colored && 'hover:brightness-125', props.class)"
    :style="coloredStyle"
    @click="handleClick"
    @mouseenter="isHovered = true"
    @mouseleave="isHovered = false"
  >
    <slot name="icon">
      <span v-if="icon" class="text-current">{{ icon }}</span>
    </slot>
    <slot />
    <button
      v-if="removable"
      type="button"
      class="ml-0.5 -mr-0.5 hover:opacity-80 transition-opacity"
      @click.stop="$emit('remove')"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="12"
        height="12"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <line x1="18" y1="6" x2="6" y2="18"></line>
        <line x1="6" y1="6" x2="18" y2="18"></line>
      </svg>
    </button>
  </span>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { HTMLAttributes } from "vue"
import type { TagVariants } from "."
import { cn } from "~/lib/utils"
import { tagVariants } from "."
import { getTagColor } from "~/lib/tagColors"

const props = defineProps<{
  variant?: TagVariants["variant"]
  size?: TagVariants["size"]
  interactive?: TagVariants["interactive"]
  icon?: string
  removable?: boolean
  colored?: boolean
  text?: string
  class?: HTMLAttributes["class"]
}>()

const emit = defineEmits<{
  click: []
  remove: []
}>()

const isHovered = ref(false)

// Generate colored style based on text prop with hover effect
const coloredStyle = computed(() => {
  if (!props.colored || !props.text) return undefined

  const colors = getTagColor(props.text)

  // Parse HSL values and brighten on hover
  if (isHovered.value) {
    const bgMatch = colors.bg.match(/hsl\((\d+),\s*(\d+)%,\s*(\d+)%\)/)
    const borderMatch = colors.border.match(/hsl\((\d+),\s*(\d+)%,\s*(\d+)%\)/)

    if (bgMatch && borderMatch) {
      return {
        backgroundColor: `hsl(${bgMatch[1]}, ${bgMatch[2]}%, ${parseInt(bgMatch[3]) + 3}%)`,
        borderColor: `hsl(${borderMatch[1]}, ${borderMatch[2]}%, ${parseInt(borderMatch[3]) + 5}%)`,
        color: colors.text,
      }
    }
  }

  return {
    backgroundColor: colors.bg,
    borderColor: colors.border,
    color: colors.text,
  }
})

function handleClick() {
  if (props.interactive) {
    emit('click')
  }
}
</script>
