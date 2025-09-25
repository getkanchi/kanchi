<template>
  <NuxtLayout>
    <div class="p-6">

      <!-- Workers Overview -->
      <div class="mb-6">
        <WorkerStatusSummary
          :workers="workers"
          @update="updateWorkerData"
        />
      </div>

      <div class="mb-6">
        <DataTable
          :columns="columns" 
          :data="liveTable.data" 
          :is-live-mode="liveTable.isLiveMode"
          :seconds-since-update="liveTable.secondsSinceUpdate"
          :page-index="liveTable.pageIndex"
          :page-size="liveTable.pageSize"
          :pagination="liveTable.pagination"
          :is-loading="liveTable.isLoading"
          :sorting="liveTable.sorting"
          :search-query="liveTable.searchQuery"
          :filters="liveTable.filters"
          class="relative backdrop-blur-sm bg-card-base border-card-border glow-border"
          @toggle-live-mode="liveTable.toggleLiveMode"
          @set-page-index="liveTable.setPageIndex"
          @set-page-size="liveTable.setPageSize"
          @set-sorting="liveTable.setSorting"
          @set-search-query="liveTable.setSearchQuery"
          @set-filters="liveTable.setFilters"
        />
      </div>
    </div>
  </NuxtLayout>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useAppWebSocket } from "~/composables/useAppWebSocket"
import { useLiveTable } from "~/composables/useLiveTable"
import { getTaskColumns } from "~/config/tableColumns"
import DataTable from "~/components/data-table.vue"
import WorkerStatusSummary from "~/components/WorkerStatusSummary.vue"
import type { WorkerInfo, WorkerEvent } from '~/types'


const { isConnected, messages } = useAppWebSocket("ws://localhost:8765/ws")

const liveTable = useLiveTable([], "http://localhost:8765/api/events/recent")

const workers = ref<WorkerInfo[]>([])
const workerMap = ref<Map<string, WorkerInfo>>(new Map())

const fetchWorkers = async () => {
  try {
    const response = await fetch('http://localhost:8765/api/workers')
    if (response.ok) {
      const data = await response.json()
      data.forEach((worker: WorkerInfo) => {
        workerMap.value.set(worker.hostname, worker)
      })
      workers.value = Array.from(workerMap.value.values())
    }
  } catch (error) {
    console.error('Failed to fetch workers:', error)
  }
}


watch(messages, (newMessages) => {
  if (liveTable.isLiveMode.value && newMessages.length > 0) {
    const latestMessage = newMessages[newMessages.length - 1]
    
    if (typeof latestMessage === 'object' && 'task_id' in latestMessage && 'event_type' in latestMessage) {
      if (liveTable.pageIndex.value === 0) {
        liveTable.fetchData()
      }
    }
    
    if (typeof latestMessage === 'object' && 'event_type' in latestMessage && 
        latestMessage.event_type?.startsWith('worker-')) {
      const workerEvent = latestMessage as WorkerEvent
      
      const hostname = workerEvent.hostname
      let workerInfo = workerMap.value.get(hostname)
      
      if (!workerInfo) {
        workerInfo = {
          hostname,
          status: 'unknown',
          timestamp: workerEvent.timestamp,
          active_tasks: 0,
          processed_tasks: 0
        }
        workerMap.value.set(hostname, workerInfo)
      }
      
      if (workerEvent.event_type === 'worker-online') {
        workerInfo.status = 'online'
      } else if (workerEvent.event_type === 'worker-offline') {
        workerInfo.status = 'offline'
      } else if (workerEvent.event_type === 'worker-heartbeat') {
        workerInfo.status = 'online'
        if (workerEvent.active !== undefined) {
          workerInfo.active_tasks = workerEvent.active
        }
        if (workerEvent.processed !== undefined) {
          workerInfo.processed_tasks = workerEvent.processed
        }
        if (workerEvent.loadavg) {
          workerInfo.loadavg = workerEvent.loadavg
        }
      }
      
      workerInfo.timestamp = workerEvent.timestamp
      
      workers.value = Array.from(workerMap.value.values())
    }
  }
}, { deep: true })


const columns = getTaskColumns()


const updateWorkerData = (hostname: string, updates: Partial<WorkerInfo>) => {
  const worker = workerMap.value.get(hostname)
  if (worker) {
    Object.assign(worker, updates)
    workers.value = Array.from(workerMap.value.values())
  }
}

const handleMouseMove = (e: MouseEvent) => {
  const glowElements = document.querySelectorAll('.glow-border')
  glowElements.forEach(element => {
    const rect = element.getBoundingClientRect()
    
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    
    ;(element as HTMLElement).style.setProperty('--mouse-x', `${x}px`)
    ;(element as HTMLElement).style.setProperty('--mouse-y', `${y}px`)
  })
}

onMounted(() => {
  document.addEventListener('mousemove', handleMouseMove)
  
  fetchWorkers()
  
  const workerInterval = setInterval(fetchWorkers, 30000)
  
  onUnmounted(() => {
    clearInterval(workerInterval)
  })
})

onUnmounted(() => {
  document.removeEventListener('mousemove', handleMouseMove)
})
</script>

<style scoped>
.glow-border {
  --mouse-x: 0px;
  --mouse-y: 0px;
  position: relative;
  background: linear-gradient(#121212, #121212) padding-box,
              radial-gradient(300px at var(--mouse-x) var(--mouse-y),
                rgba(156, 163, 175, 0.4), 
                rgba(156, 163, 175, 0.2) 20%,
                transparent 100%) border-box;
  border: 1px solid rgba(156, 163, 175, 0.1);
  background-origin: border-box;
  background-clip: padding-box, border-box;
}
</style>
