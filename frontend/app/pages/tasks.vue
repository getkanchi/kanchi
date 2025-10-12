<template>
      <div class="mb-6">
        <h1 class="text-2xl font-bold text-text-primary mb-2">Task Registry</h1>
        <p class="text-text-secondary">Monitor and manage your Celery tasks</p>
      </div>

      <!-- Search and Filters -->
      <div class="mb-6 flex items-center gap-4">
        <div class="flex-1">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search tasks..."
            class="w-full px-4 py-2 bg-background-surface border border-border rounded-lg text-text-primary placeholder-text-muted focus:outline-none focus:border-border-highlight transition-colors"
          />
        </div>

        <!-- Tags Dropdown -->
        <DropdownMenu>
          <DropdownMenuTrigger as-child>
            <button
              class="px-4 py-2 bg-background-surface border border-border rounded-lg text-text-primary hover:bg-background-hover transition-colors flex items-center gap-2 min-w-[150px]"
            >
              <Filter class="h-4 w-4" />
              <span v-if="selectedTags.length > 0" class="flex-1 text-left flex items-center gap-1 overflow-hidden">
                <BaseTag
                  v-for="tag in selectedTags.slice(0, 2)"
                  :key="tag"
                  size="xs"
                  colored
                  :text="tag"
                >
                  {{ tag }}
                </BaseTag>
                <span v-if="selectedTags.length > 2" class="text-xs text-text-muted">
                  +{{ selectedTags.length - 2 }}
                </span>
              </span>
              <span v-else class="flex-1 text-left text-sm">All Tags</span>
              <ChevronDown class="h-4 w-4 text-text-muted" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            align="end"
            class="w-[250px] max-h-[400px] overflow-y-auto bg-background-surface border-border text-text-primary"
          >
            <DropdownMenuLabel class="text-[10px] font-mono uppercase tracking-wider text-text-muted">
              Filter by Tag
            </DropdownMenuLabel>
            <DropdownMenuSeparator class="bg-border" />
            <DropdownMenuItem
              class="cursor-pointer focus:bg-background-hover text-text-primary"
              @click.prevent="clearTags"
              @select.prevent
            >
              <div class="flex items-center justify-between w-full">
                <span class="text-sm">Clear All</span>
                <X v-if="selectedTags.length > 0" class="h-4 w-4 text-text-muted" />
              </div>
            </DropdownMenuItem>
            <DropdownMenuSeparator v-if="taskRegistryStore.tags.length > 0" class="bg-border" />
            <DropdownMenuItem
              v-for="tag in taskRegistryStore.tags"
              :key="tag"
              class="cursor-pointer focus:bg-background-hover text-text-primary"
              @click.prevent="toggleTag(tag)"
              @select.prevent
            >
              <div class="flex items-center justify-between w-full gap-2">
                <BaseTag size="xs" colored :text="tag">{{ tag }}</BaseTag>
                <Check v-if="selectedTags.includes(tag)" class="h-4 w-4 text-primary flex-shrink-0" />
              </div>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <!-- Task Cards Grid -->
      <div v-if="taskRegistryStore.isLoading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <!-- Loading skeletons -->
        <div v-for="i in 8" :key="i" class="h-48 bg-background-surface border border-border rounded-lg animate-pulse"></div>
      </div>

      <div v-else-if="filteredTasks.length === 0" class="text-center py-12">
        <p class="text-text-muted">No tasks found</p>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <TaskCard
          v-for="task in filteredTasks"
          :key="task.id"
          :task="task"
          @click="handleTaskClick(task)"
        />
      </div>

      <!-- Task Detail Sheet -->
      <TaskDetailSheet
        :is-open="!!selectedTask"
        :task="selectedTask"
        @close="selectedTask = null"
        @update="handleTaskUpdate"
      />
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { Filter, ChevronDown, Check, X } from 'lucide-vue-next'
import TaskCard from '~/components/tasks/TaskCard.vue'
import TaskDetailSheet from '~/components/tasks/TaskDetailSheet.vue'
import { BaseTag } from '~/components/ui/tag'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from '~/components/ui/dropdown-menu'

const taskRegistryStore = useTaskRegistryStore()
const environmentStore = useEnvironmentStore()

// URL query sync
const urlQuerySync = useUrlQuerySync()

// State
const searchQuery = ref('')
const selectedTags = ref<string[]>([])
const selectedTask = ref(null)

// Track if we're initializing from URL
const isInitializing = ref(true)

// Computed
const filteredTasks = computed(() => {
  let tasks = taskRegistryStore.tasks

  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    tasks = tasks.filter(task =>
      task.name.toLowerCase().includes(query) ||
      (task.human_readable_name && task.human_readable_name.toLowerCase().includes(query)) ||
      (task.description && task.description.toLowerCase().includes(query))
    )
  }

  // Filter by tags (task must have ALL selected tags)
  if (selectedTags.value.length > 0) {
    tasks = tasks.filter(task =>
      task.tags && selectedTags.value.every(selectedTag => task.tags.includes(selectedTag))
    )
  }

  return tasks
})

// Actions
function handleTaskClick(task: any) {
  selectedTask.value = task
}

function handleTaskUpdate(updatedTask: any) {
  // Update the selected task with the new data
  selectedTask.value = updatedTask
}

function toggleTag(tag: string) {
  const index = selectedTags.value.indexOf(tag)
  if (index > -1) {
    // Tag is selected, remove it
    selectedTags.value.splice(index, 1)
  } else {
    // Tag is not selected, add it
    selectedTags.value.push(tag)
  }
}

function clearTags() {
  selectedTags.value = []
}

// Get current state for URL sync
const getCurrentState = computed(() => ({
  search: searchQuery.value || null,
  filters: selectedTags.value.length > 0 ? selectedTags.value.join(',') : null,
  environment: environmentStore.activeEnvironment?.id || null
}))

// Apply state from URL
function applyStateFromUrl(state: any) {
  // Apply environment first if specified
  if (state.environment && state.environment !== environmentStore.activeEnvironment?.id) {
    environmentStore.activateEnvironment(state.environment)
  }

  // Apply search
  if (state.search) {
    searchQuery.value = state.search
  }

  // Apply tags (stored as comma-separated in filters param)
  if (state.filters) {
    selectedTags.value = state.filters.split(',').filter((t: string) => t.trim())
  }
}

// Initialize from URL on mount
urlQuerySync.initializeFromUrl((state) => {
  applyStateFromUrl(state)
})

// Watch state changes and sync to URL
let syncTimeout: ReturnType<typeof setTimeout> | null = null
watch(getCurrentState, (newState) => {
  if (isInitializing.value) return

  if (syncTimeout) clearTimeout(syncTimeout)
  syncTimeout = setTimeout(() => {
    urlQuerySync.updateQueryParams(newState as any, true)
  }, 300)
}, { deep: true })

// Lifecycle
onMounted(async () => {
  await Promise.all([
    taskRegistryStore.fetchTasks(),
    taskRegistryStore.fetchAllTags()
  ])

  // Mark initialization as complete
  isInitializing.value = false
})

// Watch for environment changes and refresh data
watch(() => environmentStore.activeEnvironment, async () => {
  console.log('[Tasks Page] Environment changed, refreshing data...')
  await Promise.all([
    taskRegistryStore.fetchTasks(),
    taskRegistryStore.fetchAllTags()
  ])
})
</script>
