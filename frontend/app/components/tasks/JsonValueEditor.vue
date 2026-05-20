<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
  ChevronDown,
  CopyPlus,
  Plus,
  RotateCcw,
  Trash2,
  ArrowUp,
  ArrowDown,
  AlertTriangle,
} from 'lucide-vue-next'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { isPayloadPlaceholder } from '~/utils/payload'

defineOptions({ name: 'JsonValueEditor' })

type JsonKind = 'string' | 'number' | 'boolean' | 'null' | 'array' | 'object'

const props = withDefaults(defineProps<{
  modelValue: any
  path: string
  label?: string | number
  baselineValue?: any
  disabled?: boolean
  issuePaths?: string[]
  search?: string
  root?: boolean
}>(), {
  label: undefined,
  baselineValue: undefined,
  disabled: false,
  issuePaths: () => [],
  search: '',
  root: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: any]
  remove: []
  duplicate: []
  moveUp: []
  moveDown: []
  rename: [key: string]
}>()

const open = ref(true)
const keyDraft = ref(String(props.label ?? ''))
const numberDraft = ref('')

const kind = computed<JsonKind>(() => {
  if (Array.isArray(props.modelValue)) return 'array'
  if (props.modelValue === null) return 'null'
  if (typeof props.modelValue === 'object') return 'object'
  if (typeof props.modelValue === 'number') return 'number'
  if (typeof props.modelValue === 'boolean') return 'boolean'
  return 'string'
})

const isComplex = computed(() => kind.value === 'array' || kind.value === 'object')
const entries = computed(() => {
  if (Array.isArray(props.modelValue)) {
    return props.modelValue.map((value, index) => ({ key: index, value }))
  }
  if (props.modelValue && typeof props.modelValue === 'object') {
    return Object.entries(props.modelValue).map(([key, value]) => ({ key, value }))
  }
  return []
})

const issueHere = computed(() => props.issuePaths.includes(props.path))
const descendantIssue = computed(() =>
  props.issuePaths.some(path => path !== props.path && path.startsWith(props.path))
)

const searchText = computed(() => props.search.trim().toLowerCase())
const matchesSearch = computed(() => {
  if (!searchText.value) return false
  return `${props.path} ${String(props.label ?? '')} ${JSON.stringify(props.modelValue)}`
    .toLowerCase()
    .includes(searchText.value)
})

const changed = computed(() => {
  if (props.baselineValue === undefined) return false
  return stableStringify(props.modelValue) !== stableStringify(props.baselineValue)
})

watch(() => props.label, (label) => {
  keyDraft.value = String(label ?? '')
})

watch(() => props.modelValue, (value) => {
  numberDraft.value = typeof value === 'number' ? String(value) : ''
}, { immediate: true })

watch([searchText, descendantIssue], ([query, hasIssue]) => {
  if (query || hasIssue) open.value = true
}, { immediate: true })

function stableStringify(value: any) {
  try {
    return JSON.stringify(value)
  } catch {
    return String(value)
  }
}

function pathFor(key: string | number) {
  if (typeof key === 'number') return `${props.path}[${key}]`
  return `${props.path}.${key}`
}

function baselineFor(key: string | number) {
  const baseline = props.baselineValue
  if (Array.isArray(baseline) && typeof key === 'number') return baseline[key]
  if (baseline && typeof baseline === 'object' && !Array.isArray(baseline)) return baseline[String(key)]
  return undefined
}

function updateChild(key: string | number, value: any) {
  if (props.disabled) return
  if (Array.isArray(props.modelValue) && typeof key === 'number') {
    const next = [...props.modelValue]
    next[key] = value
    emit('update:modelValue', next)
    return
  }

  const next = { ...(props.modelValue || {}) }
  next[String(key)] = value
  emit('update:modelValue', next)
}

function removeChild(key: string | number) {
  if (props.disabled) return
  if (Array.isArray(props.modelValue) && typeof key === 'number') {
    emit('update:modelValue', props.modelValue.filter((_: any, index: number) => index !== key))
    return
  }
  const next = { ...(props.modelValue || {}) }
  delete next[String(key)]
  emit('update:modelValue', next)
}

function duplicateChild(key: string | number) {
  if (props.disabled) return
  const value = cloneValue(Array.isArray(props.modelValue) ? props.modelValue[key as number] : props.modelValue[String(key)])
  if (Array.isArray(props.modelValue) && typeof key === 'number') {
    const next = [...props.modelValue]
    next.splice(key + 1, 0, value)
    emit('update:modelValue', next)
    return
  }
  const next = { ...(props.modelValue || {}) }
  let candidate = `${String(key)}_copy`
  let index = 2
  while (Object.prototype.hasOwnProperty.call(next, candidate)) {
    candidate = `${String(key)}_copy_${index}`
    index += 1
  }
  next[candidate] = value
  emit('update:modelValue', next)
}

function moveChild(key: number, offset: -1 | 1) {
  if (props.disabled || !Array.isArray(props.modelValue)) return
  const target = key + offset
  if (target < 0 || target >= props.modelValue.length) return
  const next = [...props.modelValue]
  const [moved] = next.splice(key, 1)
  next.splice(target, 0, moved)
  emit('update:modelValue', next)
}

function renameChild(oldKey: string | number, newKey: string) {
  if (props.disabled || Array.isArray(props.modelValue)) return
  const normalized = newKey.trim()
  if (!normalized || normalized === oldKey) return
  const next: Record<string, any> = {}
  Object.entries(props.modelValue || {}).forEach(([key, value]) => {
    next[key === oldKey ? normalized : key] = value
  })
  emit('update:modelValue', next)
}

function addChild() {
  if (props.disabled) return
  if (Array.isArray(props.modelValue)) {
    emit('update:modelValue', [...props.modelValue, null])
    open.value = true
    return
  }
  const next = { ...(props.modelValue || {}) }
  let key = 'value'
  let index = 2
  while (Object.prototype.hasOwnProperty.call(next, key)) {
    key = `value_${index}`
    index += 1
  }
  next[key] = null
  emit('update:modelValue', next)
  open.value = true
}

function setKind(nextKind: JsonKind) {
  if (props.disabled || nextKind === kind.value) return
  const nextValueByKind: Record<JsonKind, any> = {
    string: '',
    number: 0,
    boolean: false,
    null: null,
    array: [],
    object: {},
  }
  emit('update:modelValue', nextValueByKind[nextKind])
}

function setNumber(value: string | number) {
  if (props.disabled) return
  numberDraft.value = String(value)
  const parsed = Number(value)
  if (!Number.isNaN(parsed) && Number.isFinite(parsed)) {
    emit('update:modelValue', parsed)
  }
}

function cloneValue(value: any) {
  return JSON.parse(JSON.stringify(value))
}

function resetValue() {
  if (props.disabled || props.baselineValue === undefined) return
  emit('update:modelValue', cloneValue(props.baselineValue))
}
</script>

<template>
  <div
    class="rounded border border-transparent"
    :class="[
      matchesSearch ? 'bg-primary-bg/30 ring-1 ring-primary/30' : '',
      issueHere ? 'border-status-warning-border bg-status-warning-bg/20' : '',
      changed && !issueHere ? 'border-primary-border/60 bg-primary-bg/10' : '',
    ]"
  >
    <div class="flex min-h-9 items-center gap-2 px-2 py-1.5">
      <button
        v-if="isComplex"
        type="button"
        class="flex h-6 w-6 items-center justify-center rounded text-text-muted hover:bg-background-hover-subtle hover:text-text-primary"
        @click="open = !open"
      >
        <ChevronDown class="h-3.5 w-3.5 transition-transform" :class="{ '-rotate-90': !open }" />
      </button>
      <span v-else class="h-6 w-6" />

      <Input
        v-if="typeof label === 'string' && !root"
        v-model="keyDraft"
        :disabled="disabled"
        class="h-7 w-36 shrink-0 font-mono text-xs"
        @change="emit('rename', keyDraft)"
      />
      <div v-else-if="label !== undefined && !root" class="w-16 shrink-0 font-mono text-xs text-text-muted">
        [{{ label }}]
      </div>
      <div v-else class="min-w-24 shrink-0 text-xs font-medium text-text-secondary">
        {{ label || 'value' }}
      </div>

      <select
        :value="kind"
        :disabled="disabled"
        class="h-7 rounded border border-border-subtle bg-background-base px-2 text-xs text-text-primary"
        @change="setKind(($event.target as HTMLSelectElement).value as JsonKind)"
      >
        <option value="string">string</option>
        <option value="number">number</option>
        <option value="boolean">boolean</option>
        <option value="null">null</option>
        <option value="array">array</option>
        <option value="object">object</option>
      </select>

      <Input
        v-if="kind === 'string'"
        :model-value="modelValue"
        :disabled="disabled"
        class="h-7 min-w-0 flex-1 font-mono text-xs"
        @update:model-value="emit('update:modelValue', $event)"
      />
      <Input
        v-else-if="kind === 'number'"
        :model-value="numberDraft"
        :disabled="disabled"
        class="h-7 min-w-0 flex-1 font-mono text-xs"
        inputmode="decimal"
        @update:model-value="setNumber"
      />
      <label v-else-if="kind === 'boolean'" class="flex items-center gap-2 text-xs text-text-secondary">
        <input
          type="checkbox"
          :checked="Boolean(modelValue)"
          :disabled="disabled"
          class="h-4 w-4 rounded border-border-subtle"
          @change="emit('update:modelValue', ($event.target as HTMLInputElement).checked)"
        />
        {{ modelValue ? 'true' : 'false' }}
      </label>
      <code v-else-if="kind === 'null'" class="text-xs text-text-muted">null</code>
      <code v-else class="text-xs text-text-muted">
        {{ kind === 'array' ? `${entries.length} items` : `${entries.length} keys` }}
      </code>

      <div class="ml-auto flex shrink-0 items-center gap-1">
        <AlertTriangle v-if="issueHere || isPayloadPlaceholder(modelValue)" class="h-3.5 w-3.5 text-status-warning" />
        <Button
          v-if="typeof label === 'number'"
          type="button"
          variant="ghost"
          size="icon"
          :disabled="disabled"
          title="Move up"
          @click="emit('moveUp')"
        >
          <ArrowUp class="h-3.5 w-3.5" />
        </Button>
        <Button
          v-if="typeof label === 'number'"
          type="button"
          variant="ghost"
          size="icon"
          :disabled="disabled"
          title="Move down"
          @click="emit('moveDown')"
        >
          <ArrowDown class="h-3.5 w-3.5" />
        </Button>
        <Button
          v-if="changed"
          type="button"
          variant="ghost"
          size="icon"
          :disabled="disabled"
          title="Reset value"
          @click="resetValue"
        >
          <RotateCcw class="h-3.5 w-3.5" />
        </Button>
        <Button v-if="!root" type="button" variant="ghost" size="icon" :disabled="disabled" title="Duplicate value" @click="emit('duplicate')">
          <CopyPlus class="h-3.5 w-3.5" />
        </Button>
        <Button v-if="!root" type="button" variant="ghost" size="icon" :disabled="disabled" title="Remove value" @click="emit('remove')">
          <Trash2 class="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>

    <div v-if="issueHere" class="px-10 pb-2 text-xs text-status-warning">
      Replace this value
    </div>

    <div v-if="isComplex && open">
      <div class="ml-5 border-l border-border-subtle pl-3">
        <JsonValueEditor
          v-for="(entry, index) in entries"
          :key="`${path}-${String(entry.key)}-${index}`"
          :model-value="entry.value"
          :path="pathFor(entry.key)"
          :label="entry.key"
          :baseline-value="baselineFor(entry.key)"
          :disabled="disabled"
          :issue-paths="issuePaths"
          :search="search"
          @update:model-value="updateChild(entry.key, $event)"
          @remove="removeChild(entry.key)"
          @duplicate="duplicateChild(entry.key)"
          @move-up="typeof entry.key === 'number' && moveChild(entry.key, -1)"
          @move-down="typeof entry.key === 'number' && moveChild(entry.key, 1)"
          @rename="renameChild(entry.key, $event)"
        />

        <div class="flex items-center gap-1 px-2 py-2">
          <Button type="button" variant="outline" size="xs" :disabled="disabled" @click="addChild">
            <Plus class="h-3.5 w-3.5" />
            Add value
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>
