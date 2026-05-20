<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = withDefaults(defineProps<{
  modelValue: string
  disabled?: boolean
}>(), {
  disabled: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const container = ref<HTMLElement | null>(null)
let view: any = null
let editableCompartment: any = null
let EditorViewCtor: any = null

onMounted(async () => {
  const [
    stateModule,
    viewModule,
    commandsModule,
    jsonModule,
  ] = await Promise.all([
    import('@codemirror/state'),
    import('@codemirror/view'),
    import('@codemirror/commands'),
    import('@codemirror/lang-json'),
  ])

  const { EditorState, Compartment } = stateModule
  const { EditorView, keymap, lineNumbers } = viewModule
  const { defaultKeymap, history, historyKeymap } = commandsModule
  const { json } = jsonModule
  EditorViewCtor = EditorView
  editableCompartment = new Compartment()

  view = new EditorView({
    parent: container.value || undefined,
    state: EditorState.create({
      doc: props.modelValue,
      extensions: [
        lineNumbers(),
        history(),
        keymap.of([...defaultKeymap, ...historyKeymap]),
        json(),
        EditorView.lineWrapping,
        editableCompartment.of(EditorView.editable.of(!props.disabled)),
        EditorView.updateListener.of((update: any) => {
          if (update.docChanged) {
            emit('update:modelValue', update.state.doc.toString())
          }
        }),
        EditorView.theme({
          '&': {
            minHeight: '420px',
            border: '1px solid var(--border-subtle)',
            borderRadius: '6px',
            backgroundColor: 'var(--bg-base)',
            color: 'var(--text-primary)',
            fontSize: '12px',
          },
          '.cm-scroller': {
            fontFamily: 'var(--font-geist-mono), ui-monospace, SFMono-Regular, Menlo, monospace',
            lineHeight: '1.6',
          },
          '.cm-gutters': {
            backgroundColor: 'var(--bg-surface)',
            color: 'var(--text-muted)',
            borderRight: '1px solid var(--border-subtle)',
          },
          '.cm-activeLineGutter, .cm-activeLine': {
            backgroundColor: 'var(--bg-hover-subtle)',
          },
          '&.cm-focused': {
            outline: '1px solid var(--primary-border)',
          },
        }),
      ],
    }),
  })
})

watch(() => props.modelValue, (next) => {
  if (!view) return
  const current = view.state.doc.toString()
  if (current === next) return
  view.dispatch({
    changes: { from: 0, to: current.length, insert: next },
  })
})

watch(() => props.disabled, (disabled) => {
  if (!view || !editableCompartment || !EditorViewCtor) return
  view.dispatch({
    effects: editableCompartment.reconfigure(EditorViewCtor.editable.of(!disabled)),
  })
})

onBeforeUnmount(() => {
  if (view) {
    view.destroy()
    view = null
  }
})
</script>

<template>
  <div ref="container" class="min-h-[420px]" />
</template>
