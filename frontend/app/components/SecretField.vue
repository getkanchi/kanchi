<template>
  <div class="flex items-center gap-2">
    <code class="text-xs font-mono bg-background-surface px-2 py-1 rounded flex-1 truncate">
      {{ displayValue }}
    </code>
    <button
      @click="toggleVisibility"
      class="text-text-muted hover:text-text-primary transition-colors flex-shrink-0 p-1 hover:bg-background-hover rounded"
      :title="isVisible ? 'Hide' : 'Show'"
    >
      <Eye v-if="!isVisible" class="h-3.5 w-3.5" />
      <EyeOff v-else class="h-3.5 w-3.5" />
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Eye, EyeOff } from 'lucide-vue-next'

interface Props {
  value: string
  maskedValue?: string
}

const props = withDefaults(defineProps<Props>(), {
  maskedValue: '***'
})

const isVisible = ref(false)

const displayValue = computed(() => {
  return isVisible.value ? props.value : props.maskedValue
})

const toggleVisibility = () => {
  isVisible.value = !isVisible.value
}
</script>
