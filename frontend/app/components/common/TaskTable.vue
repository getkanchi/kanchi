<template>
  <div :class="containerClasses">
    <div
      v-if="hasHeader"
      :class="headerClasses"
      @click="collapsible && headerClickable ? toggle() : undefined"
    >
      <slot name="header" :is-expanded="isExpanded" :toggle="toggle" />
    </div>

    <Transition v-if="collapsible" :name="transitionName">
      <div v-if="isExpanded" :class="bodyClasses">
        <slot :is-expanded="isExpanded" :toggle="toggle" />
      </div>
    </Transition>
    <div v-else :class="bodyClasses">
      <slot :is-expanded="isExpanded" :toggle="toggle" />
    </div>

    <div v-if="hasFooter" :class="footerClasses">
      <slot name="footer" :is-expanded="isExpanded" :toggle="toggle" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, useSlots, watch } from 'vue'

const props = withDefaults(defineProps<{
  collapsible?: boolean
  defaultExpanded?: boolean
  transitionName?: string
  containerClass?: string
  headerClass?: string
  bodyClass?: string
  footerClass?: string
  glow?: boolean
  bordered?: boolean
  headerClickable?: boolean
}>(), {
  collapsible: false,
  defaultExpanded: true,
  transitionName: 'fade',
  containerClass: '',
  headerClass: '',
  bodyClass: '',
  footerClass: '',
  glow: false,
  bordered: true,
  headerClickable: true,
})

const slots = useSlots()

const isExpanded = ref(props.collapsible ? props.defaultExpanded : true)

watch(() => props.collapsible, (next, prev) => {
  if (!next) {
    isExpanded.value = true
  } else if (!prev) {
    isExpanded.value = props.defaultExpanded
  }
})

watch(() => props.defaultExpanded, (next) => {
  if (props.collapsible) {
    isExpanded.value = next
  }
})

const toggle = () => {
  if (!props.collapsible) return
  isExpanded.value = !isExpanded.value
}

const hasHeader = computed(() => Boolean(slots.header))
const hasFooter = computed(() => Boolean(slots.footer))

const containerClasses = computed(() => [
  'rounded-md bg-background-surface',
  props.bordered ? 'border border-border' : '',
  props.glow ? 'glow-border' : '',
  props.containerClass,
].filter(Boolean).join(' '))

const headerClasses = computed(() => [
  props.headerClass,
  props.collapsible && props.headerClickable ? 'cursor-pointer select-none' : '',
].filter(Boolean).join(' '))

const bodyClasses = computed(() => props.bodyClass)
const footerClasses = computed(() => props.footerClass)
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
