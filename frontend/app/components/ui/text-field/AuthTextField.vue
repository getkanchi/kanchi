<template>
  <label class="block">
    <span v-if="label" class="mb-2 block text-sm font-medium text-text-secondary">
      {{ label }}
    </span>
    <div class="group relative">
      <input
        :id="id"
        :type="type"
        :autocomplete="autocomplete"
        :placeholder="placeholder"
        :disabled="disabled"
        :required="required"
        :class="inputClasses"
        :value="modelValue"
        @input="onInput"
      />
    </div>
    <p v-if="hint" class="mt-2 text-xs text-text-muted">
      {{ hint }}
    </p>
  </label>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  modelValue: string
  id?: string
  type?: string
  placeholder?: string
  autocomplete?: string
  label?: string
  hint?: string
  disabled?: boolean
  required?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text',
  placeholder: '',
  autocomplete: '',
  disabled: false,
  label: undefined,
  hint: undefined,
  id: undefined,
  required: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const inputClasses = computed(() => [
  'h-11 w-full rounded-lg border border-border-subtle bg-background-surface text-sm text-text-primary placeholder:text-text-muted appearance-none',
  'px-3 transition-[background-color,border-color,transform] duration-200 ease-out',
  'hover:bg-background-base focus:bg-background-base',
  'focus:border-primary-border focus:shadow-none focus:outline-none focus:ring-0 focus-visible:ring-0',
  'group-focus-within:border-primary-border',
  props.disabled ? 'cursor-not-allowed opacity-60' : '',
])

function onInput(event: Event) {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.value)
}
</script>

<style scoped>
input {
  background-color: var(--bg-surface);
  transition: background-color 180ms ease, transform 180ms ease;
}

input:hover {
  background-color: var(--bg-base);
}

input:focus {
  background-color: var(--bg-base);
  transform: translateY(-1px);
}

input:disabled {
  background-color: var(--bg-surface);
  transform: none;
}

input:-webkit-autofill,
input:-webkit-autofill:hover,
input:-webkit-autofill:focus,
input:-webkit-autofill:active {
  -webkit-text-fill-color: var(--text-primary);
  transition: background-color 0s ease-in-out 0s;
  box-shadow: 0 0 0px 1000px var(--bg-base) inset;
  caret-color: var(--text-primary);
}

/* no animated glow; rely on color transitions */
</style>
