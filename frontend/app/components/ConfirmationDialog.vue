<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
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
const dialogRef = ref<HTMLElement | null>(null)
let previousFocusedElement: HTMLElement | null = null

function getFocusableElements() {
  return Array.from(
    dialogRef.value?.querySelectorAll<HTMLElement>(
      'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    ) ?? []
  )
}

function closeDialog() {
  isOpen.value = false
}

function handleKeydown(event: KeyboardEvent) {
  if (!isOpen.value) return

  if (event.key === 'Escape') {
    event.preventDefault()
    if (!props.isLoading) handleCancel()
    return
  }

  if (event.key !== 'Tab') return

  const focusable = getFocusableElements()
  if (focusable.length === 0) {
    event.preventDefault()
    dialogRef.value?.focus()
    return
  }

  const first = focusable[0]
  const last = focusable[focusable.length - 1]
  const active = document.activeElement as HTMLElement | null

  if (event.shiftKey && active === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && active === last) {
    event.preventDefault()
    first.focus()
  }
}

watch(isOpen, async (open) => {
  if (open) {
    previousFocusedElement = document.activeElement as HTMLElement | null
    document.addEventListener('keydown', handleKeydown)
    await nextTick()
    getFocusableElements()[0]?.focus() ?? dialogRef.value?.focus()
    return
  }

  document.removeEventListener('keydown', handleKeydown)
  previousFocusedElement?.focus()
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleKeydown)
})

const handleConfirm = () => {
  emit('confirm')
  if (!props.isLoading) {
    closeDialog()
  }
}

const handleCancel = () => {
  emit('cancel')
  closeDialog()
}

defineExpose({
  open: () => { isOpen.value = true },
  close: closeDialog
})
</script>

<template>
  <div class="contents" @click="isOpen = true">
    <slot name="trigger">
      <Button>Open Dialog</Button>
    </slot>
  </div>

  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4" @click.self="!isLoading && handleCancel()">
    <div
      ref="dialogRef"
      tabindex="-1"
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
