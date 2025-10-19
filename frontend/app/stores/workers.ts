import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'
import { useApiService } from '../services/apiClient'
import type { WorkerInfo } from '../services/apiClient'

export const useWorkersStore = defineStore('workers', () => {
  const apiService = useApiService()

  const workers = ref<WorkerInfo[]>([])
  const recentWorkerEvents = ref<any[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const activeWorkers = computed(() =>
    workers.value.filter(worker => worker.status === 'online')
  )

  const offlineWorkers = computed(() =>
    workers.value.filter(worker => worker.status === 'offline')
  )

  const totalWorkers = computed(() => workers.value.length)
  const activeWorkersCount = computed(() => activeWorkers.value.length)
  const offlineWorkersCount = computed(() => offlineWorkers.value.length)

  const workersByHostname = computed(() => {
    const map = new Map<string, WorkerInfo>()
    workers.value.forEach(worker => {
      map.set(worker.hostname, worker)
    })
    return map
  })

  async function fetchWorkers() {
    try {
      isLoading.value = true
      error.value = null
      workers.value = await apiService.getWorkers()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch workers'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchWorker(hostname: string): Promise<WorkerInfo> {
    try {
      error.value = null
      const worker = await apiService.getWorker(hostname)

      const index = workers.value.findIndex(w => w.hostname === hostname)
      if (index !== -1) {
        workers.value[index] = worker
      } else {
        workers.value.push(worker)
      }
      
      return worker
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch worker'
      throw err
    }
  }

  async function fetchRecentWorkerEvents(limit = 50) {
    try {
      isLoading.value = true
      error.value = null
      recentWorkerEvents.value = await apiService.getRecentWorkerEvents(limit)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch worker events'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  function getWorkerByHostname(hostname: string): WorkerInfo | undefined {
    return workersByHostname.value.get(hostname)
  }

  function updateWorker(hostname: string, updates: Partial<WorkerInfo>) {
    const index = workers.value.findIndex(w => w.hostname === hostname)
    if (index !== -1) {
      workers.value[index] = { ...workers.value[index], ...updates }
    }
  }

  function updateWorkers(newWorkers: WorkerInfo[]) {
    workers.value = newWorkers
  }

  function updateFromLiveEvent(event: any) {
    const environmentStore = useEnvironmentStore()
    const { matchesEnvironment } = useEnvironmentMatcher()

    if (event.hostname) {
      const taskEventForMatching = {
        hostname: event.hostname,
        queue: null,
      } as TaskEventResponse

      if (!matchesEnvironment(taskEventForMatching, environmentStore.activeEnvironment)) {
        return
      }

      const existingWorkerIndex = workers.value.findIndex(w => w.hostname === event.hostname)
      if (existingWorkerIndex !== -1) {
        workers.value[existingWorkerIndex] = {
          ...workers.value[existingWorkerIndex],
          status: 'online',
          active: event.active || 0,
          processed: event.processed || 0,
          timestamp: event.timestamp,
        }
      }
    }
  }

  return {
    workers: readonly(workers),
    recentWorkerEvents: readonly(recentWorkerEvents),
    isLoading: readonly(isLoading),
    error: readonly(error),

    activeWorkers,
    offlineWorkers,
    totalWorkers,
    activeWorkersCount,
    offlineWorkersCount,
    workersByHostname,

    fetchWorkers,
    fetchWorker,
    fetchRecentWorkerEvents,
    getWorkerByHostname,
    updateWorker,
    updateWorkers,
    updateFromLiveEvent,
  }
})