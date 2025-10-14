<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import {
  Activity,
  Pause,
  RotateCcw,
  Search,
} from "lucide-vue-next"

import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator, CommandShortcut,
} from "~/components/ui/command"
import Pill from "~/components/common/Pill.vue"
import StatusPill from "~/components/StatusPill.vue"
import {Badge} from "~/components/ui/badge";

const { eventTypeToStatus, getStatusVariant, formatStatus } = useTaskStatus()

const props = defineProps<{
  isLiveMode?: boolean
}>()

const emit = defineEmits<{
  'toggle-live-mode': []
  'rerun-task': [taskId: string]
}>()

const open = ref(false)
const commandRef = ref<HTMLElement | null>(null)
const justOpened = ref(false)
const isFiltering = ref(false)
const isRerunMode = ref(false)
const searchQuery = ref('')
const selectedTask = ref<any>(null)
const selectedIndex = ref(0)
const availableCommands = ref<string[]>(['toggle-live', 'rerun-task'])

const toggleLiveMode = () => {
  emit('toggle-live-mode')
  open.value = false
}

const enterRerunMode = () => {
  isRerunMode.value = true
  searchQuery.value = ''
  selectedTask.value = null
  selectedIndex.value = 0
}

const exitRerunMode = () => {
  isRerunMode.value = false
  searchQuery.value = ''
  selectedTask.value = null
  selectedIndex.value = 0
}

const executeSelectedCommand = () => {
  if (isRerunMode.value) {
    executeRerun()
  } else {
    const commands = ['toggle-live', 'rerun-task']
    const selectedCommand = commands[selectedIndex.value]
    if (selectedCommand === 'toggle-live') {
      toggleLiveMode()
    } else if (selectedCommand === 'rerun-task') {
      enterRerunMode()
    }
  }
}

const navigateUp = () => {
  if (!isRerunMode.value) {
    selectedIndex.value = Math.max(0, selectedIndex.value - 1)
  }
}

const navigateDown = () => {
  if (!isRerunMode.value) {
    const maxIndex = availableCommands.value.length - 1
    selectedIndex.value = Math.min(maxIndex, selectedIndex.value + 1)
  }
}

const executeRerun = () => {
  if (selectedTask.value) {
    emit('rerun-task', selectedTask.value.task_id)
    open.value = false
    exitRerunMode()
  }
}

const handleKeydown = (e: KeyboardEvent) => {
  // ESC key to close command palette or exit rerun mode
  if (e.key === 'Escape' && open.value) {
    e.preventDefault()
    if (isRerunMode.value) {
      exitRerunMode()
    } else {
      open.value = false
    }
    return
  }
  
  // Arrow key navigation
  if ((e.key === 'ArrowUp' || e.key === 'ArrowDown') && open.value) {
    e.preventDefault()
    if (e.key === 'ArrowUp') {
      navigateUp()
    } else {
      navigateDown()
    }
    return
  }
  
  // Enter key
  if (e.key === 'Enter' && open.value) {
    e.preventDefault()
    if (isRerunMode.value && selectedTask.value) {
      executeRerun()
    } else if (!isRerunMode.value) {
      executeSelectedCommand()
    }
    return
  }
  
  // Command palette toggle
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault()
    if (!open.value) {
      open.value = true
      justOpened.value = true
      selectedIndex.value = 0
      nextTick(() => {
        setTimeout(() => {
          justOpened.value = false
        }, 300)
      })
    } else {
      open.value = false
    }
  }
  
  // Quick actions when palette is closed
  if (!open.value) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'l') {
      e.preventDefault()
      emit('toggle-live-mode')
    }
  }
}

const handleMouseMove = (e: MouseEvent) => {
  if (commandRef.value?.$el) {
    const rect = commandRef.value.$el.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    
    commandRef.value.$el.style.setProperty('--mouse-x', `${x}px`)
    commandRef.value.$el.style.setProperty('--mouse-y', `${y}px`)
  }
}

const handleInputChange = (value: string) => {
  searchQuery.value = value
  isFiltering.value = value.length > 0
  
  if (isRerunMode.value && value.length > 0) {
    lookupTask(value)
  } else {
    selectedTask.value = null
  }
}

const lookupTask = async (taskId: string) => {
  try {
    // Clean the task ID (remove any non-alphanumeric characters except hyphens)
    const cleanTaskId = taskId.trim().replace(/[^\w-]/g, '')
    if (cleanTaskId.length < 3) {
      selectedTask.value = null
      return
    }
    
    const response = await fetch(`http://localhost:8765/api/events/recent?limit=1000`)
    if (response.ok) {
      const responseData = await response.json()

      // Handle different response formats
      let events = []
      if (Array.isArray(responseData)) {
        events = responseData
      } else if (responseData.data && Array.isArray(responseData.data)) {
        events = responseData.data
      } else if (responseData.events && Array.isArray(responseData.events)) {
        events = responseData.events
      } else {
        selectedTask.value = null
        return
      }

      const task = events.find((event: any) => {
        // Try multiple possible field names and matching strategies
        const taskIdFields = [event.task_id, event.taskId, event.id, event.task]
        return taskIdFields.some(field =>
          field && field.toString().toLowerCase().includes(cleanTaskId.toLowerCase())
        )
      })

      selectedTask.value = task || null
    }
  } catch (error) {
    console.error('Failed to lookup task:', error)
    selectedTask.value = null
  }
}

const formatTimestamp = (timestamp: string) => {
  if (!timestamp) return 'N/A'
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  
  if (hours > 0) return `${hours}h ago`
  if (minutes > 0) return `${minutes}m ago`
  if (seconds > 0) return `${seconds}s ago`
  return 'just now'
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
  document.addEventListener('mousemove', handleMouseMove)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  document.removeEventListener('mousemove', handleMouseMove)
})
</script>

<template>
  <Teleport to="body">
    <Transition name="command-palette" appear>
      <div v-if="open" class="fixed inset-0 z-50 bg-black/30" @click.self="open = false">
        <div class="absolute left-1/2 top-[25vh] transform -translate-x-1/2 w-full max-w-md mx-4" @click.stop>
          <Command 
            ref="commandRef"
            :class="[
              'command-palette-container',
              'relative bg-background-surface border border-border shadow-2xl',
              'rounded-xl overflow-hidden backdrop-blur-sm',
              justOpened ? 'glow-border-animate' : 'glow-border'
            ]"
          >
              <CommandInput
                :placeholder="isRerunMode ? 'Enter task ID to rerun...' : 'Type a command or search...'" 
                class="command-input bg-transparent border-0 text-text-primary placeholder-text-tertiary focus:ring-0 px-4 py-3 text-sm"
                :model-value="searchQuery"
                @update:model-value="handleInputChange"
              />
            <CommandList class="command-list bg-transparent pt-1">
              <!-- Normal mode commands -->
              <template v-if="!isRerunMode">
                <CommandEmpty class="text-text-secondary py-4 text-center text-sm">No results found.</CommandEmpty>
                <CommandGroup heading="Actions" class="command-group text-text-secondary">
                  <div 
                    @click="toggleLiveMode"
                    :class="[
                      'command-item cursor-pointer',
                      { 'bg-background-surface/40 border-border': selectedIndex === 0 }
                    ]"
                  >
                    <Activity v-if="isLiveMode" class="w-4 h-4 text-status-success" />
                    <Pause v-else class="w-4 h-4 text-text-secondary" />
                    <span class="text-text-primary">{{ isLiveMode ? 'Disable Live Mode' : 'Enable Live Mode' }}</span>
                    <Pill variant="shortcut" size="sm">⌘L</Pill>
                  </div>
                  <div 
                    @click="enterRerunMode"
                    :class="[
                      'command-item cursor-pointer',
                      { 'bg-background-surface/40 border-border': selectedIndex === 1 }
                    ]"
                  >
                    <RotateCcw class="w-4 h-4 text-text-secondary" />
                    <span class="text-text-primary">Rerun Task...</span>
                  </div>
                </CommandGroup>
              </template>
              
              <!-- Rerun mode task details -->
              <template v-else>
                <div v-if="selectedTask" class="px-4 py-3 border-t border-border/30">
                  <div class="flex items-center justify-between mb-2">
                    <div class="flex items-center gap-2">
                      <Badge
                        :variant="getStatusVariant(eventTypeToStatus(selectedTask.event_type))"
                        class="text-xs"
                      >{{ formatStatus(eventTypeToStatus(selectedTask.event_type)) }}</Badge>
                    </div>
                  </div>
                  <div class="text-xs text-text-secondary space-y-1">
                    <div><span class="text-text-muted">Task:</span> {{ selectedTask.task_name || 'N/A' }}</div>
                    <div><span class="text-text-muted">Worker:</span> {{ selectedTask.hostname || 'N/A' }}</div>
                    <div><span class="text-text-muted">Time:</span> {{ formatTimestamp(selectedTask.timestamp) }}</div>
                  </div>
                  <div class="mt-3 pt-2 border-t border-border/20">
                    <div class="text-xs text-text-muted">Press Enter to rerun this task</div>
                  </div>
                </div>
                <div v-else-if="searchQuery.length > 0" class="px-4 py-3 text-text-secondary text-sm text-center">
                  No task found with ID "{{ searchQuery }}"
                </div>
                <div v-else class="px-4 py-3 text-text-secondary text-sm text-center">
                  Enter a task ID to search...
                </div>
              </template>
            </CommandList>
          </Command>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* Glow effects are now handled by global CSS utilities */

/* Command palette transitions */
.command-palette-enter-active,
.command-palette-leave-active {
  transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);
}

.command-palette-enter-active .command-palette-container,
.command-palette-leave-active .command-palette-container {
  transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);
}

.command-palette-enter-from,
.command-palette-leave-to {
  opacity: 0;
}

.command-palette-enter-from .command-palette-container,
.command-palette-leave-to .command-palette-container {
  opacity: 0;
  transform: scale(0.95) translateY(-20px);
}

/* Custom styling for command components */
:deep(.command-input) {
  font-size: 0.875rem;
  border-bottom: 1px solid theme(colors.card.border / 0.3);
}

:deep(.command-input:focus) {
  outline: none;
  box-shadow: none;
}

:deep(.command-list) {
  max-height: 350px;
}

:deep(.command-group) {
  padding: 0;
}

:deep(.command-group [cmdk-group-heading]) {
  font-size: 0.6875rem;
  font-weight: 600;
  color: theme(colors.text.secondary);
  padding: 0.5rem 0.75rem 0.375rem;
  text-transform: uppercase;
  letter-spacing: 0.075em;
}

:deep(.command-item) {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.75rem;
  margin: 0.0625rem 0;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 150ms cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid transparent;
}

/* Disable default command item selection to use our custom highlighting */
:deep(.command-item[aria-selected="true"]) {
  background: transparent;
  border-color: transparent;
}

:deep(.command-item:hover) {
  background: theme(colors.background.surface)/50;
}

:deep(.command-item[aria-disabled="true"]) {
  cursor: not-allowed;
  opacity: 0.4;
}

:deep(.command-item [cmdk-item-icon]) {
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
}

:deep(.command-item span) {
  flex: 1;
}

/* Pill components handle shortcut styling now */

:deep(.command-separator) {
  height: 1px;
  background: theme(colors.card.border);
  margin: 0.375rem 0.75rem;
}
</style>
