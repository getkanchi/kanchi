<script setup lang="ts">
import { ref } from 'vue'
import { AlertTriangle, Loader2 } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'

interface Props {
  title?: string
  description?: string
  confirmText?: string
  cancelText?: string
  variant?: 'default' | 'destructive'
  isLoading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  title: 'Confirm Action',
  description: 'Are you sure you want to continue?',
  confirmText: 'Confirm',
  cancelText: 'Cancel',
  variant: 'default',
  isLoading: false
})

const emit = defineEmits<{
  confirm: []
  cancel: []
}>()

const isOpen = ref(false)

const handleConfirm = () => {
  emit('confirm')
  if (!props.isLoading) {
    isOpen.value = false
  }
}

const handleCancel = () => {
  emit('cancel')
  isOpen.value = false
}

defineExpose({
  open: () => { isOpen.value = true },
  close: () => { isOpen.value = false }
})
</script>

<template>
  <div class="contents" @click="isOpen = true">
    <slot name="trigger">
      <Button>Open Dialog</Button>
    </slot>
  </div>

  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4">
    <div
      class="grid w-full max-w-md gap-4 rounded-lg border border-border-subtle bg-background-surface p-6 shadow-lg"
      role="dialog"
      aria-modal="true"
      :aria-labelledby="'confirmation-dialog-title'"
      :aria-describedby="'confirmation-dialog-description'"
    >
      <div class="space-y-2">
        <h2 id="confirmation-dialog-title" class="flex items-center gap-2 text-lg font-semibold text-text-primary">
          <AlertTriangle v-if="variant === 'destructive'" class="h-5 w-5 text-red-500" />
          {{ title }}
        </h2>
        <p id="confirmation-dialog-description" v-if="description" class="text-sm text-text-secondary">
          {{ description }}
        </p>
      </div>

      <div v-if="$slots.content" class="py-2">
        <slot name="content" />
      </div>

      <div class="flex flex-col-reverse sm:flex-row sm:justify-end sm:gap-2">
        <Button
          variant="outline"
          @click="handleCancel"
          :disabled="isLoading"
          class="mt-2 sm:mt-0"
        >
          {{ cancelText }}
        </Button>
        <Button
          :variant="variant === 'destructive' ? 'destructive' : 'default'"
          @click="handleConfirm"
          :disabled="isLoading"
          class="flex items-center gap-2"
        >
          <Loader2 v-if="isLoading" class="h-4 w-4 animate-spin" />
          {{ confirmText }}
        </Button>
      </div>
    </div>
  </div>
</template>
