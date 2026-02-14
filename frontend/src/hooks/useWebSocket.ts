import { useEffect, useRef, useCallback } from 'react'
import { useChatStore } from '../stores/chatStore'
import { useAuthStore } from '../stores/authStore'

interface WebSocketMessage {
  type: 'message' | 'typing' | 'connected' | 'error'
  content?: string
  conversationId?: string
}

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null)
  const { token } = useAuthStore()
  const { addMessage, setConnected, setTyping, currentConversation } = useChatStore()

  const connect = useCallback(() => {
    if (!token || wsRef.current?.readyState === WebSocket.OPEN) return

    const wsUrl = `${import.meta.env.VITE_WS_URL || 'ws://localhost:8081'}/ws?token=${token}`
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('WebSocket connected')
      setConnected(true)
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
      setConnected(false)
      // Reconnect after 3 seconds
      setTimeout(connect, 3000)
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    ws.onmessage = (event) => {
      const data: WebSocketMessage = JSON.parse(event.data)

      switch (data.type) {
        case 'message':
          if (data.content) {
            addMessage({
              id: Date.now().toString(),
              conversationId: data.conversationId || '',
              role: 'assistant',
              content: data.content,
              createdAt: new Date().toISOString(),
            })
          }
          setTyping(false)
          break
        case 'typing':
          setTyping(true)
          break
        case 'error':
          console.error('Server error:', data.content)
          setTyping(false)
          break
      }
    }

    wsRef.current = ws
  }, [token, addMessage, setConnected, setTyping])

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [])

  const sendMessage = useCallback((content: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'message',
        content,
        conversationId: currentConversation?.id,
      }))

      // Add user message to store
      addMessage({
        id: Date.now().toString(),
        conversationId: currentConversation?.id || '',
        role: 'user',
        content,
        createdAt: new Date().toISOString(),
      })

      setTyping(true)
    }
  }, [currentConversation, addMessage, setTyping])

  useEffect(() => {
    connect()
    return () => disconnect()
  }, [connect, disconnect])

  return {
    sendMessage,
    disconnect,
    reconnect: connect,
  }
}
