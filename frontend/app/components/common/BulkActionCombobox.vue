<script setup lang="ts">
import { Check, CheckCircle2, ChevronsUpDown, RefreshCw, Undo2 } from 'lucide-vue-next'
import { computed, ref } from 'vue'
import { Button } from '~/components/ui/button'
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandList,
} from '~/components/ui/command'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '~/components/ui/popover'
import { cn } from '~/lib/utils'

export type BulkTaskAction = 'rerun' | 'resolve' | 'unresolve'

const props = withDefaults(defineProps<{
  modelValue: BulkTaskAction
  disabled?: boolean
}>(), {
  disabled: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: BulkTaskAction]
}>()

const open = ref(false)
const actions: Array<{ value: BulkTaskAction; label: string; icon: any }> = [
  { value: 'resolve', label: 'Resolve', icon: CheckCircle2 },
  { value: 'unresolve', label: 'Unresolve', icon: Undo2 },
  { value: 'rerun', label: 'Rerun', icon: RefreshCw },
]

const selectedAction = computed(() =>
  actions.find(action => action.value === props.modelValue) ?? actions[0]
)

function selectAction(value: BulkTaskAction) {
  emit('update:modelValue', value)
  open.value = false
}
</script>

<template>
  <Popover v-model:open="open">
    <PopoverTrigger as-child>
      <Button
        variant="outline"
        size="sm"
        class="h-8 min-w-32 justify-between gap-2"
        :disabled="disabled"
      >
        {{ selectedAction.label }}
        <ChevronsUpDown class="h-3.5 w-3.5 text-text-muted" />
      </Button>
    </PopoverTrigger>
    <PopoverContent
      class="w-44 border-border-subtle bg-background-surface p-0 text-text-primary"
      align="end"
    >
      <Command class="bg-background-surface text-text-primary">
        <CommandList class="max-h-none">
          <CommandEmpty class="text-text-muted">No action found.</CommandEmpty>
          <CommandGroup class="text-text-primary">
            <CommandItem
              v-for="action in actions"
              :key="action.value"
              :value="action.value"
              class="cursor-pointer text-text-secondary data-[highlighted]:bg-background-hover-subtle data-[highlighted]:text-text-primary"
              @select="selectAction(action.value)"
            >
              <Check
                :class="cn(
                  'h-4 w-4 text-primary',
                  modelValue === action.value ? 'visible' : 'invisible',
                )"
              />
              <component :is="action.icon" class="h-4 w-4 text-text-muted" />
              {{ action.label }}
            </CommandItem>
          </CommandGroup>
        </CommandList>
      </Command>
    </PopoverContent>
  </Popover>
</template>
