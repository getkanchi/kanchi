import { defineStore } from 'pinia'
import { ref, computed, readonly, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useAuthStore } from './auth'
import { useTasksStore } from './tasks'
import { useWorkersStore } from './workers'
import { useOrphanTasksStore } from './orphanTasks'
import { useFailedTasksStore } from './failedTasks'

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
  const failedTasksStore = useFailedTasksStore()

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

  const authStore = useAuthStore()
  const { authEnabled, isAuthenticated, accessToken, configLoading } = storeToRefs(authStore)

  const canReconnect = computed(() =>
    reconnectAttempts.value < maxReconnectAttempts
  )

  function connect() {
    if (isConnected.value || isConnecting.value) {
      return
    }

    if (authEnabled.value && !isAuthenticated.value) {
      return
    }

    try {
      isConnecting.value = true
      error.value = null

      const config = useRuntimeConfig()
      let wsUrl = config.public.wsUrl as string

      if (authEnabled.value && accessToken.value) {
        try {
          const parsed = new URL(wsUrl)
          parsed.searchParams.set('token', accessToken.value)
          wsUrl = parsed.toString()
        } catch (err) {
          console.error('[WebSocket] Invalid WS URL:', err)
        }
      }

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
          failedTasksStore.updateFromLiveEvent(message)
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
    watch([authEnabled, isAuthenticated, accessToken], () => {
      if (configLoading.value) {
        return
      }

      if (!authEnabled.value) {
        if (!isConnected.value) {
          connect()
        }
        return
      }

      if (isAuthenticated.value) {
        disconnect()
        connect()
      } else {
        disconnect()
      }
    }, { immediate: true })
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
