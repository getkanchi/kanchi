<template>
  <Alert
    v-if="isVisible"
    variant="warning"
    :size="dense ? 'sm' : 'default'"
    class="mt-2"
  >
    <template #title>
      {{ titleText }}
    </template>
    <div class="space-y-1">
      <p v-for="message in messages" :key="message">
        {{ message }}
      </p>
      <p class="text-[11px] text-orange-200/80">
        Celery truncated part of the payload before emitting this event, so Kanchi never received the omitted values.
      </p>
    </div>
  </Alert>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Alert } from '~/components/alert'
import { collectTruncationMessages, containsTruncatedValue } from '~/utils/payload'

interface Props {
  value: unknown
  title?: string
  dense?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  dense: false,
  title: undefined
})

const isVisible = computed(() => containsTruncatedValue(props.value))
const messages = computed(() => collectTruncationMessages(props.value))
const titleText = computed(() => props.title || 'Payload truncated before reaching Kanchi')
</script>
