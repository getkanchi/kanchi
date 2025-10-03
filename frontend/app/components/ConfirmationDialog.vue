<script setup lang="ts">
import { ref } from 'vue'
import { AlertTriangle, Loader2 } from 'lucide-vue-next'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
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

const handleOpenChange = (open: boolean) => {
  // Don't allow closing when loading
  if (!props.isLoading) {
    isOpen.value = open
  }
}

// Expose method to open dialog programmatically
defineExpose({
  open: () => { isOpen.value = true },
  close: () => { isOpen.value = false }
})
</script>

<template>
  <Dialog v-model:open="isOpen" @update:open="handleOpenChange">
    <DialogTrigger as-child>
      <slot name="trigger">
        <Button>Open Dialog</Button>
      </slot>
    </DialogTrigger>
    
    <DialogContent class="sm:max-w-md">
      <DialogHeader>
        <DialogTitle class="flex items-center gap-2">
          <AlertTriangle 
            v-if="variant === 'destructive'" 
            class="h-5 w-5 text-red-500" 
          />
          {{ title }}
        </DialogTitle>
        <DialogDescription v-if="description" class="text-left">
          {{ description }}
        </DialogDescription>
      </DialogHeader>
      
      <!-- Custom content slot -->
      <div v-if="$slots.content" class="py-2">
        <slot name="content" />
      </div>
      
      <DialogFooter class="flex-col-reverse sm:flex-row sm:justify-end sm:gap-2">
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
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
