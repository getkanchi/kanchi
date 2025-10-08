<template>
  <div class="inline-flex items-center gap-1.5">
    <TooltipProvider>
      <TooltipRoot>
        <TooltipTrigger as-child>
          <code
            class="text-xs bg-background-surface px-1 py-0.5 rounded font-mono cursor-default"
            :class="sizeClasses"
          >
            {{ displayValue }}
          </code>
        </TooltipTrigger>
        <TooltipContent class="bg-background-raised">
          <p class="font-mono text-xs">{{ uuid }}</p>
        </TooltipContent>
      </TooltipRoot>
    </TooltipProvider>

    <CopyButton
      v-if="showCopy"
      :text="uuid"
      :copy-key="`uuid-${uuid}`"
      :title="copyTitle"
      :show-text="showCopyText"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import CopyButton from '~/components/CopyButton.vue'
import {
  TooltipRoot,
  TooltipContent,
  TooltipTrigger,
  TooltipProvider,
} from '@/components/ui/tooltip'

interface Props {
  uuid: string
  showCopy?: boolean
  showCopyText?: boolean
  copyTitle?: string
  truncateLength?: number
  size?: 'xs' | 'sm' | 'md'
}

const props = withDefaults(defineProps<Props>(), {
  showCopy: false,
  showCopyText: true,
  copyTitle: 'Copy UUID',
  truncateLength: 12,
  size: 'xs'
})

const displayValue = computed(() => {
  if (props.uuid.length <= props.truncateLength) {
    return props.uuid
  }
  return `${props.uuid.substring(0, props.truncateLength)}...`
})

const sizeClasses = computed(() => {
  switch (props.size) {
    case 'xs':
      return 'text-xs'
    case 'sm':
      return 'text-sm'
    case 'md':
      return 'text-base'
    default:
      return 'text-xs'
  }
})
</script>
