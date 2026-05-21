<script setup lang="ts">
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import TimeDisplay from '~/components/TimeDisplay.vue'
import CopyButton from '~/components/CopyButton.vue'
import PythonValueViewer from '~/components/PythonValueViewer.vue'
import { Hash, Database, Cpu, AlertTriangle } from 'lucide-vue-next'

const props = defineProps<{
  taskName: string
  statusLabel: string
  statusVariant: string
  startedTimestamp?: string | null
  runtimeLabel?: string | null
  retryLabel?: string | number | null
  taskId: string
  routingKey?: string | null
  hostname?: string | null
  args?: unknown
  kwargs?: unknown
  result?: unknown
  traceback?: string | null
  showException?: boolean
}>()

const formatResult = (result: unknown): string => {
  if (typeof result === 'string') return result
  try {
    return JSON.stringify(result, null, 2)
  } catch {
    return String(result)
  }
}
</script>

<template>
  <div class="space-y-4 w-full max-w-full min-w-0 px-8 py-6 overflow-hidden">
    <Card class="w-full bg-background-surface/90 border border-border rounded-lg shadow-sm">
      <CardContent class="p-3 md:p-4 space-y-3">
        <div class="flex flex-col gap-2 text-xs text-text-muted">
          <div class="flex w-full flex-wrap items-center gap-3">
            <div class="flex min-w-0 flex-1 flex-wrap items-center gap-3">
              <div class="flex items-center gap-2 min-w-0">
                <span class="text-sm font-semibold text-text-primary truncate">
                  {{ taskName || 'Task' }}
                </span>
                <Badge
                  :variant="statusVariant"
                  class="text-[11px] font-semibold"
                >
                  {{ statusLabel }}
                </Badge>
              </div>
              <div class="flex flex-wrap items-center gap-4 md:gap-6 text-sm text-text-primary">
                <div class="flex items-center gap-2 min-w-0">
                  <Hash class="h-3.5 w-3.5 text-text-muted" />
                  <div class="flex items-center gap-2 min-w-0">
                    <span class="font-semibold truncate">{{ taskId }}</span>
                    <CopyButton
                      :text="taskId"
                      :copy-key="`task-id-${taskId}`"
                      title="Copy task ID"
                      :show-text="false"
                    />
                  </div>
                </div>

                <div class="flex items-center gap-2 min-w-0">
                  <Database class="h-3.5 w-3.5 text-text-muted" />
                  <span class="font-semibold truncate">{{ routingKey || 'default' }}</span>
                </div>

                <div class="flex items-center gap-2 min-w-0">
                  <Cpu class="h-3.5 w-3.5 text-text-muted" />
                  <span class="font-semibold break-words">{{ hostname || '-' }}</span>
                </div>

                <slot name="meta-extra" />
              </div>
            </div>

            <div class="flex gap-2 ml-auto shrink-0">
              <slot name="actions" />
            </div>
          </div>

          <div class="flex flex-wrap items-center gap-2 text-sm text-text-primary">
            <template v-if="startedTimestamp">
              <div class="flex items-center gap-1.5">
                <TimeDisplay
                  :timestamp="startedTimestamp"
                  layout="inline"
                  :short="true"
                  :auto-refresh="true"
                  :refresh-interval="1000"
                  class="text-text-muted"
                />
              </div>
            </template>
            <template v-if="runtimeLabel">
              <span class="text-border-border">•</span>
              <span class="flex items-center gap-1.5">
                <span class="font-medium text-text-secondary">Runtime</span>
                {{ runtimeLabel }}
              </span>
            </template>
            <template v-if="retryLabel !== undefined && retryLabel !== null">
              <span class="text-border-border">•</span>
              <span class="flex items-center gap-1.5">
                <span class="font-medium text-text-secondary">Retries</span>
                {{ retryLabel }}
              </span>
            </template>
          </div>
        </div>

      </CardContent>
    </Card>

    <div class="space-y-4 w-full max-w-full min-w-0">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 w-full max-w-full min-w-0">
        <Card class="w-full bg-background-surface/90 border border-border rounded-lg shadow-sm mb-4">
          <CardContent class="p-3 md:p-4 space-y-3">
            <PythonValueViewer
              :value="args"
              title="Arguments"
              :copy-key="`args-${taskId}`"
              empty-message="No arguments"
            />
          </CardContent>
        </Card>
        
        <Card class="w-full bg-background-surface/90 border border-border rounded-lg shadow-sm mb-4">
          <CardContent class="p-3 md:p-4 space-y-3">
            <PythonValueViewer
              :value="kwargs"
              title="Keyword Arguments"
              :copy-key="`kwargs-${taskId}`"
              empty-message="No keyword arguments"
            />
          </CardContent>
        </Card>
      </div>

      <div
        v-if="result !== undefined && result !== null && result !== ''"
        class="p-4 border border-status-success-border rounded-md bg-background-surface"
      >
        <div class="flex items-center justify-between mb-3">
          <h4 class="text-sm font-medium text-status-success">Result:</h4>
          <CopyButton
            :text="formatResult(result)"
            :copy-key="`result-${taskId}`"
            title="Copy result"
            :show-text="true"
          />
        </div>
        <pre class="bg-status-success-bg border border-status-success-border p-3 rounded text-xs overflow-x-auto text-status-success font-mono">{{ formatResult(result) }}</pre>
      </div>

      <div
        v-if="showException !== false && traceback"
        class="p-4 border border-status-error-border rounded-md bg-background-surface"
      >
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-1.5">
            <AlertTriangle class="h-3.5 w-3.5 text-red-400" />
            <h4 class="text-sm font-medium text-red-400">Error Traceback:</h4>
          </div>
          <CopyButton
            :text="traceback"
            :copy-key="`traceback-${taskId}`"
            title="Copy traceback"
            :show-text="true"
          />
        </div>
        <pre class="bg-red-950/20 border border-red-900/20 p-3 rounded text-xs overflow-x-auto text-red-400 font-mono">{{ traceback }}</pre>
      </div>

      <slot />
    </div>
  </div>
</template>
