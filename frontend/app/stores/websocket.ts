/**
 * Pinia store for WebSocket management
 */
import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'
import { useTasksStore } from './tasks'
import { useWorkersStore } from './workers'
import { useOrphanTasksStore } from './orphanTasks'

export interface WebSocketMessage {
  type: string
  [key: string]: any
}

export interface ConnectionInfo {
  status: string
  timestamp: string
  message: string
  total_connections: number
}

export const useWebSocketStore = defineStore('websocket', () => {
  const tasksStore = useTasksStore()
  const workersStore = useWorkersStore()
  const orphanTasksStore = useOrphanTasksStore()

  // State
  const ws = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const isConnecting = ref(false)
  const connectionInfo = ref<ConnectionInfo | null>(null)
  const error = ref<string | null>(null)
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = 5
  const reconnectDelay = ref(1000)

  // Client state
  const clientFilters = ref<Record<string, any>>({})
  const clientMode = ref<'live' | 'static'>('live')

  // Computed
  const canReconnect = computed(() => 
    reconnectAttempts.value < maxReconnectAttempts
  )

  // Actions
  function connect() {
    if (isConnected.value || isConnecting.value) {
      return
    }

    try {
      isConnecting.value = true
      error.value = null

      const config = useRuntimeConfig()
      const wsUrl = config.public.wsUrl as string

      ws.value = new WebSocket(wsUrl)

      ws.value.onopen = () => {
        isConnected.value = true
        isConnecting.value = false
        reconnectAttempts.value = 0
        reconnectDelay.value = 1000

        // Send initial ping and set mode
        sendMessage({ type: 'ping' })
        sendMessage({ type: 'set_mode', mode: clientMode.value })
      }

      ws.value.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          handleMessage(message)
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err)
        }
      }

      ws.value.onclose = () => {
        isConnected.value = false
        isConnecting.value = false
        
        if (canReconnect.value) {
          setTimeout(() => {
            reconnectAttempts.value++
            reconnectDelay.value *= 2 // Exponential backoff
            connect()
          }, reconnectDelay.value)
        }
      }

      ws.value.onerror = (err) => {
        error.value = 'WebSocket connection error'
        console.error('WebSocket error:', err)
      }

    } catch (err) {
      isConnecting.value = false
      error.value = err instanceof Error ? err.message : 'Failed to connect'
    }
  }

  function disconnect() {
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
    isConnected.value = false
    isConnecting.value = false
    reconnectAttempts.value = maxReconnectAttempts // Prevent auto-reconnect
  }

  function sendMessage(message: WebSocketMessage) {
    if (isConnected.value && ws.value) {
      ws.value.send(JSON.stringify(message))
    }
  }

  function handleMessage(message: any) {
    // Handle backend response messages (with .type field)
    const messageType = message.type
    if (messageType) {
      switch (messageType) {
        case 'connection':
          connectionInfo.value = message
          break

        case 'pong':
          // Handle pong response
          break

        case 'subscription_response':
          // Handle subscription acknowledgment
          break

        case 'mode_changed':
          // Confirm mode change from backend
          if (message.mode) {
            clientMode.value = message.mode
          }
          break

        case 'stored_events_sent':
          // Handle stored events response
          break

        default:
          console.log('Unknown response type:', messageType, message)
      }
      return
    }

    // Handle live event messages (with .event_type field)
    const eventType = message.event_type
    if (eventType) {
      if (clientMode.value === 'live') {
        // Handle task events
        if (eventType.startsWith('task-')) {
          tasksStore.handleLiveEvent(message)
          orphanTasksStore.updateFromLiveEvent(message)
        }
        // Handle worker events  
        else if (eventType.startsWith('worker-')) {
          workersStore.updateFromLiveEvent(message)
        }
      }
    } else {
      console.log('Unknown message type:', messageType, message)
    }
  }

  function subscribe(filters: Record<string, any> = {}) {
    clientFilters.value = filters
    sendMessage({
      type: 'subscribe',
      filters
    })
  }

  function setMode(mode: 'live' | 'static') {
    clientMode.value = mode
    if (isConnected.value) {
      sendMessage({
        type: 'set_mode',
        mode
      })
    }
  }

  function getStoredEvents(limit = 1000) {
    sendMessage({
      type: 'get_stored',
      limit
    })
  }

  function ping() {
    sendMessage({ type: 'ping' })
  }

  // Auto-connect only on client side
  if (process.client) {
    connect()
  }

  return {
    // State
    isConnected: readonly(isConnected),
    isConnecting: readonly(isConnecting),
    connectionInfo: readonly(connectionInfo),
    error: readonly(error),
    reconnectAttempts: readonly(reconnectAttempts),
    clientFilters: readonly(clientFilters),
    clientMode: readonly(clientMode),

    // Computed
    canReconnect,

    // Actions
    connect,
    disconnect,
    sendMessage,
    subscribe,
    setMode,
    getStoredEvents,
    ping,
  }
})