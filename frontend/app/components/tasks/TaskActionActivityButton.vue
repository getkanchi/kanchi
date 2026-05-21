<script setup lang="ts">
import { Activity, AlertCircle } from 'lucide-vue-next'
import { computed } from 'vue'
import { Button } from '~/components/ui/button'
import ButtonCounter from '~/components/common/ButtonCounter.vue'

const taskActionsStore = useTaskActionsStore()

const label = computed(() => {
  if (taskActionsStore.runningActions.length > 0) {
    return 'Running'
  }
  if (taskActionsStore.activeActions.length > 0) {
    return 'Activity'
  }
  return 'No activity'
})

const hasFailures = computed(() =>
  taskActionsStore.activeActions.some(action => action.item_failed > 0)
)
</script>

<template>
  <Button
    variant="default"
    size="sm"
    class="gap-2"
    @click="taskActionsStore.openDrawer()"
  >
    <Activity class="h-4 w-4" />
    {{ label }}
    <ButtonCounter
      v-if="taskActionsStore.runningActions.length > 0"
      :value="taskActionsStore.runningActions.length"
      tone="primary"
      class="ml-1"
    />
    <AlertCircle v-if="hasFailures" class="h-3.5 w-3.5 text-status-error" />
  </Button>
</template>
