<script setup lang="ts">
import { Copy, Check } from 'lucide-vue-next'
import { useCopy } from '~/composables/useCopy'

const props = defineProps<{
  text: string
  copyKey?: string
  title?: string
  showText?: boolean
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
  <button 
    @click.stop="handleCopy"
    class="flex items-center gap-1.5 text-gray-400 hover:text-gray-300 p-1 transition-colors min-h-[25px]"
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
