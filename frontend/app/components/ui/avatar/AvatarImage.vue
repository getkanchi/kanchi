<template>
  <img
    v-if="!hasError && props.src"
    :src="props.src"
    :alt="props.alt"
    :class="cn('h-full w-full object-cover', props.class)"
    @error="handleError"
  >
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { cn } from '@/lib/utils'

interface Props {
  src?: string | null
  alt?: string
  class?: string
}

const props = withDefaults(defineProps<Props>(), {
  src: '',
  alt: '',
  class: ''
})

const hasError = ref(false)

function handleError() {
  hasError.value = true
}
</script>
