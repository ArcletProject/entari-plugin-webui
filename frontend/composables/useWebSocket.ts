/**
 * WebSocket 连接管理
 */

interface UseWebSocketOptions {
  onMessage?: (data: any) => void
  onError?: (error: Event) => void
  onClose?: () => void
  autoReconnect?: boolean
  reconnectInterval?: number
}

export const useWebSocketConnection = (path: string, wsOptions: UseWebSocketOptions = {}) => {
  const config = useRuntimeConfig()
  const auth = useAuth()

  const {
    onMessage,
    onError,
    onClose,
    autoReconnect = true,
    reconnectInterval = 3000,
  } = wsOptions

  const ws = ref<WebSocket | null>(null)
  const connected = ref(false)
  const reconnectTimer = ref<NodeJS.Timeout | null>(null)

  // 构建 WebSocket URL
  const getWsUrl = () => {
    if (import.meta.client) {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = window.location.host
      return `${protocol}//${host}${path}`
    }
    return ''
  }

  // 连接
  const connect = () => {
    if (!import.meta.client) return

    const url = getWsUrl()
    if (!url) return

    try {
      ws.value = new WebSocket(url)

      ws.value.onopen = () => {
        connected.value = true
        // 清除重连定时器
        if (reconnectTimer.value) {
          clearTimeout(reconnectTimer.value)
          reconnectTimer.value = null
        }
      }

      ws.value.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          onMessage?.(data)
        } catch {
          onMessage?.(event.data)
        }
      }

      ws.value.onerror = (error) => {
        onError?.(error)
      }

      ws.value.onclose = () => {
        connected.value = false
        onClose?.()

        // 自动重连
        if (autoReconnect && !reconnectTimer.value) {
          reconnectTimer.value = setTimeout(() => {
            reconnectTimer.value = null
            connect()
          }, reconnectInterval)
        }
      }
    } catch (e) {
      console.error('WebSocket connection error:', e)
    }
  }

  // 断开
  const disconnect = () => {
    if (reconnectTimer.value) {
      clearTimeout(reconnectTimer.value)
      reconnectTimer.value = null
    }

    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
    connected.value = false
  }

  // 发送消息
  const send = (data: any) => {
    if (ws.value && connected.value) {
      ws.value.send(typeof data === 'string' ? data : JSON.stringify(data))
    }
  }

  // 组件卸载时断开连接
  onUnmounted(() => {
    disconnect()
  })

  return {
    ws,
    connected,
    connect,
    disconnect,
    send,
  }
}
