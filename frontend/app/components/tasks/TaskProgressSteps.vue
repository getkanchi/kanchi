<template>
  <div v-if="stepItems.length" class="space-y-2">
    <div
      v-for="item in stepItems"
      :key="item.step.key"
      class="flex items-start gap-3"
    >
      <div class="mt-0.5 flex h-4 w-4 items-center justify-center">
        <Check v-if="item.status === 'completed'" class="h-4 w-4 text-status-success" />
        <div v-else-if="item.status === 'active'" class="relative h-2 w-2">
          <div class="h-2 w-2 rounded-full bg-primary" />
          <div
            class="absolute inset-0 h-2 w-2 rounded-full bg-primary opacity-60 animate-ping motion-reduce:animate-none"
          />
        </div>
        <div v-else class="h-2 w-2 rounded-full bg-border" />
      </div>

      <div class="flex-1 min-w-0">
        <p
          class="text-sm font-medium"
          :class="getTextColor(item.status)"
        >
          {{ item.step.label }}
        </p>
        <p v-if="item.step.description" class="text-xs text-text-muted">
          {{ item.step.description }}
        </p>
      </div>

      <div class="text-[11px] font-mono text-text-muted whitespace-nowrap">
        <template v-if="item.status === 'completed'">Done</template>
        <template v-else-if="item.status === 'active'">{{ item.progress }}%</template>
        <template v-else>Pending</template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Check } from 'lucide-vue-next'
import type { TaskProgressSnapshotResponse, TaskProgressEventResponse } from '~/services/apiClient'
import Tooltip from "~/components/ui/tooltip/Tooltip.vue";
import {TooltipProvider, TooltipTrigger} from "~/components/ui/tooltip";
import {ToolbarRoot} from "reka-ui";

type StepStatus = 'completed' | 'active' | 'pending'

const props = defineProps<{
  snapshot?: TaskProgressSnapshotResponse | null
}>()

const orderedSteps = computed(() => {
  const steps = props.snapshot?.steps || []
  return [...steps].sort((a, b) => {
    const orderA = a.order ?? Number.MAX_SAFE_INTEGER
    const orderB = b.order ?? Number.MAX_SAFE_INTEGER
    return orderA - orderB
  })
})

const latestByStep = computed(() => {
  const history = props.snapshot?.history || []
  const map = new Map<string, TaskProgressEventResponse>()

  for (const entry of history) {
    if (!entry.step_key) continue
    const existing = map.get(entry.step_key)
    if (!existing) {
      map.set(entry.step_key, entry)
      continue
    }
    const existingTs = new Date(existing.timestamp).getTime()
    const incomingTs = new Date(entry.timestamp).getTime()
    if (incomingTs >= existingTs) {
      map.set(entry.step_key, entry)
    }
  }

  return map
})

const latestStepEvent = computed(() => {
  const history = props.snapshot?.history || []
  let latest: TaskProgressEventResponse | null = null
  let latestTs = -1

  for (const entry of history) {
    if (!entry.step_key) continue
    const ts = new Date(entry.timestamp).getTime()
    if (ts > latestTs) {
      latest = entry
      latestTs = ts
    }
  }

  return latest
})

const latestStepIndex = computed(() => {
  if (!latestStepEvent.value?.step_key) return -1
  return orderedSteps.value.findIndex((step) => step.key === latestStepEvent.value?.step_key)
})

const overallCompleted = computed(() => {
  return (props.snapshot?.latest?.progress ?? 0) >= 100
})

const activeStepKey = computed(() => {
  if (overallCompleted.value) return null
  if (!latestStepEvent.value) return null
  if ((latestStepEvent.value.progress ?? 0) >= 100) return null
  return latestStepEvent.value.step_key ?? null
})

const stepItems = computed(() => {
  return orderedSteps.value.map((step, index) => {
    const event = latestByStep.value.get(step.key)
    const progress = overallCompleted.value ? 100 : event ? Math.round(event.progress ?? 0) : 0
    const completed = overallCompleted.value
      || (event?.progress ?? 0) >= 100
      || (latestStepIndex.value >= 0 && index < latestStepIndex.value)
      || (latestStepIndex.value === index && activeStepKey.value === null && (latestStepEvent.value?.progress ?? 0) >= 100)
    const status: StepStatus = completed
      ? 'completed'
      : step.key === activeStepKey.value
        ? 'active'
        : 'pending'

    return {
      step,
      progress,
      status,
    }
  })
})

const getTextColor = (status: string) => {
  let textColor = 'text-text-muted';
  if (status === 'completed') {
    return 'text-text-primary';
  } else if (status === 'active') {
    return 'text-shimmer'
  }
  return textColor;
}

</script>

<style scoped>
.text-shimmer {
  display: inline-block;

  color: transparent;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  -webkit-background-clip: text;

  background-image: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0.25) 0%,
    rgba(255, 255, 255, 0.25) 40%,
    rgba(255, 255, 255, 0.85) 50%,
    rgba(255, 255, 255, 0.25) 60%,
    rgba(255, 255, 255, 0.25) 100%
  );
  background-size: 300% 100%;
  background-position: -150% 0;

  animation: shimmer 3.2s linear reverse infinite;
  will-change: background-position;
}

@keyframes shimmer {
  0% {
    background-position: -150% 0;
  }
  100% {
    background-position: 150% 0;
  }
}
</style>
