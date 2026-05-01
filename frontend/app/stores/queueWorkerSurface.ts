import { defineStore } from 'pinia'
import { computed, readonly, ref } from 'vue'
import { useApiService, type QueueWorkerSurfaceResponse } from '../services/apiClient'

export const useQueueWorkerSurfaceStore = defineStore('queueWorkerSurface', () => {
  const api = useApiService()
  const surface = ref<QueueWorkerSurfaceResponse>({ queues: [], workers: [], notes: [] })
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const criticalQueues = computed(() => surface.value.queues.filter(queue => queue.status === 'critical'))
  const notedEntities = computed(() => new Set(surface.value.notes.map(note => `${note.entity_type}:${note.entity_key}`)))

  async function fetchSurface() {
    try {
      isLoading.value = true
      error.value = null
      surface.value = await api.getQueueWorkerSurface()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch queue/worker surface'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function saveNote(payload: { entity_type: 'queue' | 'worker'; entity_key: string; note: string; author?: string | null }) {
    const note = await api.saveQueueWorkerNote(payload)
    surface.value.notes = [
      note,
      ...surface.value.notes.filter(existing => !(existing.entity_type === note.entity_type && existing.entity_key === note.entity_key)),
    ]
    return note
  }

  return {
    surface: readonly(surface),
    isLoading: readonly(isLoading),
    error: readonly(error),
    criticalQueues,
    notedEntities,
    fetchSurface,
    saveNote,
  }
})
