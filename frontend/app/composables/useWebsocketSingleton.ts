// composables/useWebsocketSingleton.ts
import { ref, onUnmounted } from 'vue'
import type { TaskEventResponse } from "~~/src/types/data-contracts"

// Singleton state - shared across all component instances
const socket = ref<WebSocket | null>(null)
const isConnected = ref(false)
const messages = ref<any[]>([])
const error = ref<any>(null)
let connectionCount = 0

const connect = (url: string) => {
  // Only connect if not already connected
  if (socket.value && socket.value.readyState === WebSocket.OPEN) {
    return
  }
  
  try {
    socket.value = new WebSocket(url)

    socket.value.onopen = () => {
      console.log('WebSocket connected')
      isConnected.value = true
      error.value = null
    }

    socket.value.onmessage = (event) => {
      const data = JSON.parse(event.data)
      messages.value.push(data)
      handleMessage(data)
    }

    socket.value.onerror = (err) => {
      console.error('WebSocket error:', err)
      error.value = err
    }

    socket.value.onclose = () => {
      console.log('WebSocket disconnected')
      isConnected.value = false
      // Reconnection logic
      setTimeout(() => {
        if (!isConnected.value && connectionCount > 0) {
          connect(url)
        }
      }, 5000)
    }
  } catch (err) {
    error.value = err
  }
}

const sendMessage = (message: any) => {
  if (socket.value && socket.value.readyState === WebSocket.OPEN) {
    socket.value.send(JSON.stringify(message))
  }
}

const disconnect = () => {
  if (socket.value && connectionCount === 0) {
    socket.value.close()
    socket.value = null
  }
}

const handleMessage = (data: TaskEventResponse) => {
  switch(data.event_type) {
    case 'task-sent':
      console.log("Task sent:", data)
      break
    case 'notification':
      break
    default:
      console.log('Received message:', data)
      break
  }
}

export const useWebSocketSingleton = (url: string) => {
  // Track component usage
  connectionCount++
  
  // Connect on first use
  if (connectionCount === 1) {
    connect(url)
  }
  
  onUnmounted(() => {
    connectionCount--
    // Disconnect when no components are using it
    if (connectionCount === 0) {
      disconnect()
    }
  })
  
  return {
    isConnected,
    messages,
    error,
    sendMessage,
    connect: () => connect(url),
    disconnect
  }
}