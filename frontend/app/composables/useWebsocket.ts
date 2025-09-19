// composables/useWebSocket.js
import { ref, onMounted, onUnmounted } from 'vue'
import type {TaskEventResponse} from "~~/src/types/data-contracts";

export const useWebSocket = (url: string) => {
  const socket = ref<WebSocket>(null)
  const isConnected = ref(false)
  const messages = ref([])
  const error = ref(null)

  const connect = () => {
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
        // Or handle different message types
        handleMessage(data)
      }

      socket.value.onerror = (err) => {
        console.error('WebSocket error:', err)
        error.value = err
      }

      socket.value.onclose = () => {
        console.log('WebSocket disconnected')
        isConnected.value = false
        // Optional: implement reconnection logic
        setTimeout(() => {
          if (!isConnected.value) {
            connect()
          }
        }, 5000)
      }
    } catch (err) {
      error.value = err
    }
  }

  const sendMessage = (message) => {
    if (socket.value && socket.value.readyState === WebSocket.OPEN) {
      socket.value.send(JSON.stringify(message))
    }
  }

  const disconnect = () => {
    if (socket.value) {
      socket.value.close()
    }
  }

  const handleMessage = (data: TaskEventResponse) => {
    // Handle different message types
    switch(data.event_type) {
      case 'task-sent':
        console.log("Task sent:", data)
        break
      case 'notification':
        // Handle notification
        break
      default:
        // Handle default
        console.log('Received message:', data)
        break
    }
  }

  onMounted(() => {
    connect()
  })

  onUnmounted(() => {
    disconnect()
  })

  return {
    isConnected,
    messages,
    error,
    sendMessage,
    connect,
    disconnect
  }
}
