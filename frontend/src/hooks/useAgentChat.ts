import { useState, useCallback } from 'react'
import { useChatStore } from '../stores/chatStore'

interface AgentInvokeRequest {
  request_id: string
  conversation_id: string
  agent_id: string
  query: string
  input: Record<string, unknown>
  context: Record<string, unknown>
}

interface AgentInvokeResponse {
  request_id: string
  status: 'success' | 'error'
  content?: {
    text: string
    format: string
    data: unknown
  }
  metadata?: {
    operation: string
    latency_ms: number
    trace_id: string
  }
  error?: {
    code: string
    message: string
  }
}

const API_BASE = import.meta.env.VITE_API_URL || '/api/v1'

export function useAgentChat() {
  const { messages, addMessage, setTyping, currentConversation, clearMessages } = useChatStore()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim()) return

    const requestId = `req-${Date.now()}`
    const conversationId = currentConversation?.id || `conv-${Date.now()}`

    // Add user message
    addMessage({
      id: `user-${Date.now()}`,
      conversationId,
      role: 'user',
      content,
      createdAt: new Date().toISOString(),
    })

    setIsLoading(true)
    setTyping(true)
    setError(null)

    try {
      const request: AgentInvokeRequest = {
        request_id: requestId,
        conversation_id: conversationId,
        agent_id: 'nexusops.chat',
        query: content,
        input: { message: content },
        context: {
          project_id: 'default',
        },
      }

      const response = await fetch(`${API_BASE}/agents/nexusops.chat/invoke`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      })

      const data: AgentInvokeResponse = await response.json()

      if (data.status === 'success' && data.content) {
        addMessage({
          id: `assistant-${Date.now()}`,
          conversationId,
          role: 'assistant',
          content: data.content.text,
          createdAt: new Date().toISOString(),
        })
      } else if (data.error) {
        setError(data.error.message)
        addMessage({
          id: `assistant-${Date.now()}`,
          conversationId,
          role: 'assistant',
          content: `Error: ${data.error.message}`,
          createdAt: new Date().toISOString(),
        })
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message'
      setError(errorMessage)
      addMessage({
        id: `assistant-${Date.now()}`,
        conversationId,
        role: 'assistant',
        content: `Connection error: ${errorMessage}. Please check if the backend is running.`,
        createdAt: new Date().toISOString(),
      })
    } finally {
      setIsLoading(false)
      setTyping(false)
    }
  }, [addMessage, currentConversation, setTyping])

  const startNewConversation = useCallback(() => {
    clearMessages()
    setError(null)
  }, [clearMessages])

  return {
    messages,
    sendMessage,
    isLoading,
    isTyping: isLoading,
    error,
    startNewConversation,
    isConnected: true, // REST API is always "connected"
  }
}
