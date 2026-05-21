<script setup lang="ts">
import { computed } from "vue"
import type { CheckboxRootProps } from "reka-ui"
import type { HTMLAttributes } from "vue"
import { reactiveOmit } from "@vueuse/core"
import { Check, Minus } from "lucide-vue-next"
import { CheckboxIndicator, CheckboxRoot, useForwardProps } from "reka-ui"
import { cn } from "@/lib/utils"

type CheckedState = boolean | "indeterminate"

const props = defineProps<CheckboxRootProps & {
  class?: HTMLAttributes["class"]
  checked?: CheckedState | null
}>()

const emits = defineEmits<{
  "update:modelValue": [value: CheckedState]
  "update:checked": [value: CheckedState]
}>()

const delegatedProps = reactiveOmit(props, "class", "checked", "modelValue")
const forwarded = useForwardProps(delegatedProps)
const checkedState = computed(() => props.checked ?? props.modelValue ?? false)

function handleUpdate(value: CheckedState) {
  emits("update:modelValue", value)
  emits("update:checked", value)
}
</script>

<template>
  <CheckboxRoot
    v-bind="forwarded"
    :model-value="checkedState"
    :class="cn(
      'peer h-4 w-4 shrink-0 rounded-sm border border-border bg-background-raised shadow-sm transition-colors hover:bg-background-hover-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background-base disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:border-primary data-[state=checked]:bg-primary data-[state=checked]:text-white data-[state=indeterminate]:border-primary data-[state=indeterminate]:bg-primary data-[state=indeterminate]:text-white',
      props.class,
    )"
    @update:model-value="handleUpdate"
  >
    <CheckboxIndicator class="flex h-full w-full items-center justify-center text-current">
      <Minus v-if="checkedState === 'indeterminate'" class="h-3 w-3" />
      <Check v-else class="h-3 w-3" />
    </CheckboxIndicator>
  </CheckboxRoot>
</template>
