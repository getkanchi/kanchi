import { ref, watch, computed, onUnmounted } from 'vue'
import { useWebSocket } from '@vueuse/core'
import type { TaskEventResponse } from '~~/src/types/data-contracts'

let socket: ReturnType<typeof useWebSocket> | null = null
const messages = ref<TaskEventResponse[]>([])
let connectionCount = 0

const createConnection = (url: string) => {
  if (socket) {
    return socket
  }

  socket = useWebSocket(url, {
    autoReconnect: {
      retries: 3,
      delay: 1000,
      onFailed() {
        console.error('Failed to connect WebSocket after retries')
      }
    },
    heartbeat: {
      message: 'ping',
      interval: 30000,
      pongTimeout: 10000
    },
    immediate: true
  })

  watch(socket.data, (newData) => {
    if (newData) {
      try {
        const parsedMessage = JSON.parse(newData) as TaskEventResponse
        messages.value.push(parsedMessage)
        handleMessage(parsedMessage)
      } catch (error) {
        console.error('Error parsing WebSocket message:', error)
      }
    }
  })

  return socket
}

const handleMessage = (data: TaskEventResponse) => {
  switch (data.event_type) {
    case 'task-sent':
      console.log('Task sent:', data)
      break
    case 'notification':
      break
    default:
      console.log('Received message:', data)
      break
  }
}

export const useAppWebSocket = (url: string = 'ws://localhost:8765/ws') => {
  connectionCount++
  
  const ws = createConnection(url)
  
  const sendMessage = (message: any) => {
    if (socket && socket.status.value === 'OPEN') {
      socket.send(JSON.stringify(message))
    }
  }
  
  onUnmounted(() => {
    connectionCount--
    if (connectionCount === 0 && socket) {
      socket.close()
      socket = null
    }
  })

  return {
    isConnected: computed(() => ws.status.value === 'OPEN'),
    messages,
    status: computed(() => ws.status.value || 'CLOSED'),
    sendMessage,
    close: () => ws.close(),
    open: () => ws.open()
  }
}
