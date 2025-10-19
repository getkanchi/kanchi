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

<script lang="ts">
import { cva } from "class-variance-authority"
import type { VariantProps } from "class-variance-authority"

export const tagVariants = cva(
  "inline-flex items-center gap-1.5 font-mono font-medium transition-all duration-200 uppercase tracking-wide",
  {
    variants: {
      variant: {
        default: "bg-background-raised text-text-secondary border border-border hover:bg-background-hover hover:border-border-highlight",
        primary: "bg-primary-bg text-primary border border-primary-border hover:bg-primary/10",
        subtle: "bg-background-surface text-text-muted border border-border-subtle hover:text-text-secondary",
        outlined: "bg-transparent text-text-secondary border border-border hover:bg-background-surface",
        solid: "bg-background-hover text-text-primary border border-transparent hover:bg-background-active",
      },
      size: {
        xs: "text-[9px] px-1.5 py-0.5 rounded gap-1",
        sm: "text-[10px] px-2 py-0.5 rounded-md gap-1.5",
        default: "text-[11px] px-2.5 py-1 rounded-md gap-1.5",
        md: "text-xs px-3 py-1.5 rounded-md gap-2",
      },
      interactive: {
        true: "cursor-pointer hover:scale-[1.02] active:scale-[0.98]",
        false: "cursor-default",
      }
    },
    defaultVariants: {
      variant: "default",
      size: "sm",
      interactive: false,
    },
  },
)

export type TagVariants = VariantProps<typeof tagVariants>
</script>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { HTMLAttributes } from "vue"
import { cn } from "~/lib/utils"
import { getTagColor } from "~/lib/tagColors.ts"

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
