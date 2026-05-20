<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { AlignJustify, Braces, Search, Shrink, Wand2 } from 'lucide-vue-next'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs'
import CodemirrorJsonEditor from './CodemirrorJsonEditor.client.vue'
import JsonValueEditor from './JsonValueEditor.vue'
import type { RerunInputIssueDTO } from '~/services/apiClient'

const props = withDefaults(defineProps<{
  args: any[]
  kwargs: Record<string, any>
  baselineArgs: any[]
  baselineKwargs: Record<string, any>
  issues?: RerunInputIssueDTO[]
  disabled?: boolean
}>(), {
  issues: () => [],
  disabled: false,
})

const emit = defineEmits<{
  update: [args: any[], kwargs: Record<string, any>]
}>()

const mode = ref<'structured' | 'raw'>('structured')
const rawText = ref('')
const rawError = ref<string | null>(null)
const search = ref('')

const issuePaths = computed(() => props.issues.map(issue => issue.path))

watch(mode, (next) => {
  if (next === 'raw') {
    rawText.value = stringifyDocument({ args: props.args, kwargs: props.kwargs }, 2)
    rawError.value = null
  }
})

watch(() => [props.args, props.kwargs], () => {
  if (mode.value === 'raw' && !rawError.value) {
    rawText.value = stringifyDocument({ args: props.args, kwargs: props.kwargs }, 2)
  }
}, { deep: true })

function stringifyDocument(value: any, spaces: number | undefined) {
  return JSON.stringify(value, null, spaces)
}

function updateArgs(value: any) {
  if (!Array.isArray(value)) return
  emit('update', value, props.kwargs)
}

function updateKwargs(value: any) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return
  emit('update', props.args, value)
}

function parseRaw() {
  try {
    assertNoDuplicateKeys(rawText.value)
    const parsed = JSON.parse(rawText.value)
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
      throw new Error('Use one JSON object with args and kwargs.')
    }
    if (!Array.isArray(parsed.args)) {
      throw new Error('Positional arguments must be a JSON array.')
    }
    if (!parsed.kwargs || typeof parsed.kwargs !== 'object' || Array.isArray(parsed.kwargs)) {
      throw new Error('Keyword arguments must be a JSON object.')
    }
    rawError.value = null
    emit('update', parsed.args, parsed.kwargs)
  } catch (error) {
    rawError.value = error instanceof Error ? error.message : 'Invalid JSON document.'
  }
}

function updateRawText(value: string) {
  rawText.value = value
  parseRaw()
}

function formatRaw() {
  parseRaw()
  if (!rawError.value) {
    rawText.value = stringifyDocument({ args: props.args, kwargs: props.kwargs }, 2)
  }
}

function compactRaw() {
  parseRaw()
  if (!rawError.value) {
    rawText.value = stringifyDocument({ args: props.args, kwargs: props.kwargs }, undefined)
  }
}

function assertNoDuplicateKeys(source: string) {
  let index = 0

  function error(message: string): never {
    throw new Error(`${message} at character ${index}`)
  }

  function skipWhitespace() {
    while (/\s/.test(source[index] || '')) index += 1
  }

  function parseString(): string {
    if (source[index] !== '"') error('Expected string')
    index += 1
    let value = ''
    while (index < source.length) {
      const char = source[index]
      if (char === '"') {
        index += 1
        return value
      }
      if (char === '\\') {
        value += char
        index += 1
        if (index >= source.length) error('Unterminated escape')
        value += source[index]
        index += 1
        continue
      }
      value += char
      index += 1
    }
    error('Unterminated string')
  }

  function parseNumber() {
    const match = source.slice(index).match(/^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?/)
    if (!match) error('Invalid number')
    index += match[0].length
  }

  function parseLiteral(literal: string) {
    if (source.slice(index, index + literal.length) !== literal) error(`Expected ${literal}`)
    index += literal.length
  }

  function parseArray() {
    index += 1
    skipWhitespace()
    if (source[index] === ']') {
      index += 1
      return
    }
    while (index < source.length) {
      parseValue()
      skipWhitespace()
      if (source[index] === ']') {
        index += 1
        return
      }
      if (source[index] !== ',') error('Expected comma')
      index += 1
      skipWhitespace()
    }
    error('Unterminated array')
  }

  function parseObject() {
    index += 1
    const keys = new Set<string>()
    skipWhitespace()
    if (source[index] === '}') {
      index += 1
      return
    }
    while (index < source.length) {
      skipWhitespace()
      const key = parseString()
      if (keys.has(key)) error(`Duplicate object key "${key}"`)
      keys.add(key)
      skipWhitespace()
      if (source[index] !== ':') error('Expected colon')
      index += 1
      parseValue()
      skipWhitespace()
      if (source[index] === '}') {
        index += 1
        return
      }
      if (source[index] !== ',') error('Expected comma')
      index += 1
    }
    error('Unterminated object')
  }

  function parseValue() {
    skipWhitespace()
    const char = source[index]
    if (char === '{') return parseObject()
    if (char === '[') return parseArray()
    if (char === '"') return parseString()
    if (char === '-' || /\d/.test(char || '')) return parseNumber()
    if (char === 't') return parseLiteral('true')
    if (char === 'f') return parseLiteral('false')
    if (char === 'n') return parseLiteral('null')
    error('Expected JSON value')
  }

  parseValue()
  skipWhitespace()
  if (index !== source.length) error('Unexpected content')
}
</script>

<template>
  <div class="flex min-h-0 flex-1 flex-col gap-3">
    <div class="flex flex-wrap items-center gap-2">
      <Tabs v-model="mode" class="min-w-0 flex-1">
        <TabsList class="h-9">
          <TabsTrigger value="structured" class="gap-1 text-xs">
            <AlignJustify class="h-3.5 w-3.5" />
            Structured
          </TabsTrigger>
          <TabsTrigger value="raw" class="gap-1 text-xs">
            <Braces class="h-3.5 w-3.5" />
            Raw JSON
          </TabsTrigger>
        </TabsList>
      </Tabs>

      <div class="relative min-w-[180px] flex-1 sm:max-w-xs">
        <Search class="absolute left-2 top-2.5 h-3.5 w-3.5 text-text-muted" />
        <Input v-model="search" class="h-9 pl-8 text-xs" placeholder="Search inputs" />
      </div>
    </div>

    <Tabs v-model="mode" class="min-h-0 flex-1">
      <TabsContent value="structured" class="mt-0 min-h-0">
        <div class="space-y-3">
          <section class="rounded-md border border-border-subtle bg-background-surface p-2">
            <div class="mb-1 px-2 text-xs font-medium text-text-secondary">Positional arguments</div>
            <JsonValueEditor
              :model-value="args"
              path="$.args"
              label="Positional arguments"
              :baseline-value="baselineArgs"
              :disabled="disabled"
              :issue-paths="issuePaths"
              :search="search"
              root
              @update:model-value="updateArgs"
            />
          </section>

          <section class="rounded-md border border-border-subtle bg-background-surface p-2">
            <div class="mb-1 px-2 text-xs font-medium text-text-secondary">Keyword arguments</div>
            <JsonValueEditor
              :model-value="kwargs"
              path="$.kwargs"
              label="Keyword arguments"
              :baseline-value="baselineKwargs"
              :disabled="disabled"
              :issue-paths="issuePaths"
              :search="search"
              root
              @update:model-value="updateKwargs"
            />
          </section>
        </div>
      </TabsContent>

      <TabsContent value="raw" class="mt-0">
        <div class="space-y-2">
          <CodemirrorJsonEditor
            :model-value="rawText"
            :disabled="disabled"
            @update:model-value="updateRawText"
          />
          <div class="flex flex-wrap items-center justify-between gap-2">
            <p class="min-h-5 text-xs" :class="rawError ? 'text-status-error' : 'text-text-muted'">
              {{ rawError || 'Edit the same draft as JSON. The document must contain args and kwargs.' }}
            </p>
            <div class="flex items-center gap-2">
              <Button type="button" variant="outline" size="xs" :disabled="disabled" @click="formatRaw">
                <Wand2 class="h-3.5 w-3.5" />
                Format
              </Button>
              <Button type="button" variant="outline" size="xs" :disabled="disabled" @click="compactRaw">
                <Shrink class="h-3.5 w-3.5" />
                Compact
              </Button>
            </div>
          </div>
        </div>
      </TabsContent>
    </Tabs>
  </div>
</template>
