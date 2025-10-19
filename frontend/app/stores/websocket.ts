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

  const ws = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const isConnecting = ref(false)
  const connectionInfo = ref<ConnectionInfo | null>(null)
  const error = ref<string | null>(null)
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = 5
  const reconnectDelay = ref(1000)

  const clientFilters = ref<Record<string, any>>({})
  const clientMode = ref<'live' | 'static'>('live')

  const canReconnect = computed(() =>
    reconnectAttempts.value < maxReconnectAttempts
  )

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
            reconnectDelay.value *= 2
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
    reconnectAttempts.value = maxReconnectAttempts
  }

  function sendMessage(message: WebSocketMessage) {
    if (isConnected.value && ws.value) {
      ws.value.send(JSON.stringify(message))
    }
  }

  function handleMessage(message: any) {
    const messageType = message.type
    if (messageType) {
      switch (messageType) {
        case 'connection':
          connectionInfo.value = message
          break

        case 'pong':
          break

        case 'subscription_response':
          break

        case 'mode_changed':
          if (message.mode) {
            clientMode.value = message.mode
          }
          break

        case 'stored_events_sent':
          break

        default:
          console.warn('Unknown response type:', messageType, message)
      }
      return
    }

    const eventType = message.event_type
    if (eventType) {
      if (clientMode.value === 'live') {
        if (eventType.startsWith('task-')) {
          tasksStore.handleLiveEvent(message)
          orphanTasksStore.updateFromLiveEvent(message)
        }
        else if (eventType.startsWith('worker-')) {
          workersStore.updateFromLiveEvent(message)
        }
      }
    } else {
      console.warn('Unknown message type:', messageType, message)
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

  if (process.client) {
    connect()
  }

  return {
    isConnected: readonly(isConnected),
    isConnecting: readonly(isConnecting),
    connectionInfo: readonly(connectionInfo),
    error: readonly(error),
    reconnectAttempts: readonly(reconnectAttempts),
    clientFilters: readonly(clientFilters),
    clientMode: readonly(clientMode),

    canReconnect,

    connect,
    disconnect,
    sendMessage,
    subscribe,
    setMode,
    getStoredEvents,
    ping,
  }
})