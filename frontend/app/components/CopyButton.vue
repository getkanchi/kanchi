<script setup lang="ts">
import { Copy, Check } from 'lucide-vue-next'
import type { HTMLAttributes } from 'vue'
import { Button, type ButtonVariants } from '~/components/ui/button'
import { useCopy } from '~/composables/useCopy'

const props = defineProps<{
  text: string
  copyKey?: string
  title?: string
  showText?: boolean
  label?: string
  variant?: ButtonVariants['variant']
  size?: ButtonVariants['size']
  class?: HTMLAttributes['class']
}>()

const { copyToClipboard, isCopied } = useCopy()

const handleCopy = async () => {
  await copyToClipboard(props.text, props.copyKey || props.text)
}

const isItemCopied = computed(() => 
  props.copyKey ? isCopied(props.copyKey) : isCopied(props.text)
)
</script>

<template>
  <Button
    v-if="label"
    type="button"
    :variant="variant || 'outline'"
    :size="size || 'xs'"
    :class="props.class"
    :title="title || `Copy ${label.toLowerCase()}`"
    @click.stop="handleCopy"
  >
    <Check v-if="isItemCopied" class="h-3.5 w-3.5 text-green-400" />
    <Copy v-else class="h-3.5 w-3.5" />
    <span :class="isItemCopied ? 'text-green-400' : ''">
      {{ isItemCopied ? 'Copied' : label }}
    </span>
  </Button>
  <button 
    v-else
    @click.stop="handleCopy"
    :class="props.class || 'flex min-h-[25px] items-center gap-1.5 p-1 text-gray-400 transition-colors hover:text-gray-300'"
    :title="title || 'Copy to clipboard'"
  >
    <template v-if="isItemCopied">
      <Check class="h-3 w-3 text-green-400" />
      <span v-if="showText" class="text-xs text-green-400">Copied</span>
    </template>
    <template v-else>
      <Copy class="h-3 w-3" />
    </template>
  </button>
</template>
