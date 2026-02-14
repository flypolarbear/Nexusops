import { useState, useRef, useEffect, useCallback } from 'react'
import {
  Drawer,
  Input,
  Button,
  Avatar,
  Spin,
  Space,
  Typography,
  Tooltip,
  message,
} from 'antd'
import {
  RobotOutlined,
  UserOutlined,
  SendOutlined,
  DeleteOutlined,
  PaperClipOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useChatStore } from '../stores/chatStore'
import { useAuthStore } from '../stores/authStore'
import type { Message } from '../types'

const { Text } = Typography
const { TextArea } = Input

interface AIAssistantDrawerProps {
  open: boolean
  onClose: () => void
}

// Mock AI responses for demo
const mockResponses: Record<string, string> = {
  'alerts': `## Current Alerts Summary

I found **3 active alerts** in the system:

| Severity | Service | Issue |
|----------|---------|-------|
| Critical | chat-service | Memory usage above 90% |
| Warning | api-gateway | CPU usage above 80% |
| Info | api-gateway | P95 latency above 500ms |

**Recommendation**: Check the [Alerts page](/alerts) for details and consider scaling the chat-service deployment.

\`\`\`bash
kubectl top pods -n production
\`\`\`
`,
  'deployments': `## Recent Deployments

Here's the status of recent deployments:

1. **api-gateway** v1.2.3 - Synced & Healthy
2. **chat-gateway** v2.0.1 - Out of Sync
3. **auth-service** v1.1.0 - Failed

The chat-gateway deployment needs attention. View the [Deployments page](/deployments) for the full chain.
`,
  'resources': `## Resource Overview

**US East Region:**
- Production Cluster: 85% CPU, 72% Memory
- Development Cluster: 25% CPU, 40% Memory

**EU West Region:**
- EU Production: 60% CPU, 55% Memory

Resource usage is within normal parameters. Check the [Resources page](/resources) for detailed metrics.
`,
  'default': `I understand you're asking about: "{query}"

Let me help you with that. Based on the current system state, here's what I found:

- All services are operational
- No critical incidents in the last 24 hours
- Resource utilization is within expected ranges

Would you like me to:
1. Check specific service health?
2. Review recent deployments?
3. Analyze resource trends?
`
}

function getMockResponse(query: string): string {
  const lowerQuery = query.toLowerCase()
  if (lowerQuery.includes('alert') || lowerQuery.includes('warning') || lowerQuery.includes('critical')) {
    return mockResponses['alerts']
  }
  if (lowerQuery.includes('deploy') || lowerQuery.includes('build') || lowerQuery.includes('release')) {
    return mockResponses['deployments']
  }
  if (lowerQuery.includes('resource') || lowerQuery.includes('cpu') || lowerQuery.includes('memory') || lowerQuery.includes('cluster')) {
    return mockResponses['resources']
  }
  return mockResponses['default'].replace('{query}', query)
}

export default function AIAssistantDrawer({ open, onClose }: AIAssistantDrawerProps) {
  const [inputValue, setInputValue] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { messages, isTyping, addMessage, setTyping, clearMessages } = useChatStore()
  useAuthStore() // Keep auth store initialized

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = useCallback(() => {
    if (!inputValue.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      conversationId: 'demo',
      role: 'user',
      content: inputValue.trim(),
      createdAt: new Date().toISOString(),
    }
    addMessage(userMessage)
    setInputValue('')
    setTyping(true)

    // Simulate AI response with delay
    setTimeout(() => {
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        conversationId: 'demo',
        role: 'assistant',
        content: getMockResponse(userMessage.content),
        createdAt: new Date().toISOString(),
      }
      addMessage(aiResponse)
      setTyping(false)
    }, 1000 + Math.random() * 1000)
  }, [inputValue, addMessage, setTyping])

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const quickQueries = [
    { icon: 'alert', text: 'Check current alerts' },
    { icon: 'deploy', text: 'Recent deployments' },
    { icon: 'resource', text: 'Resource status' },
  ]

  return (
    <Drawer
      title={
        <div className="flex items-center gap-2">
          <RobotOutlined className="text-primary-500" />
          <span>AI Operations Assistant</span>
        </div>
      }
      placement="right"
      width={480}
      onClose={onClose}
      open={open}
      extra={
        <Space>
          <Tooltip title="Clear conversation">
            <Button
              type="text"
              icon={<DeleteOutlined />}
              onClick={() => {
                clearMessages()
                message.success('Conversation cleared')
              }}
            />
          </Tooltip>
        </Space>
      }
      styles={{
        body: { display: 'flex', flexDirection: 'column', padding: 0 },
      }}
    >
      {/* Messages Area */}
      <div className="flex-1 overflow-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center">
            <Avatar size={64} icon={<RobotOutlined />} className="bg-primary-500 mb-4" />
            <Text strong className="text-lg mb-2">How can I help you today?</Text>
            <Text type="secondary" className="mb-4">
              Ask me about resources, alerts, deployments, or any operations question.
            </Text>
            <div className="space-y-2 w-full max-w-xs">
              {quickQueries.map((q, i) => (
                <Button
                  key={i}
                  block
                  onClick={() => {
                    setInputValue(q.text)
                  }}
                  className="text-left"
                >
                  <ThunderboltOutlined className="mr-2" />
                  {q.text}
                </Button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.role === 'assistant' && (
                <Avatar icon={<RobotOutlined />} className="bg-primary-500 shrink-0" />
              )}
              <div
                className={`max-w-[85%] px-4 py-3 rounded-lg ${
                  msg.role === 'user'
                    ? 'bg-primary-500 text-white'
                    : 'bg-gray-100 dark:bg-gray-800'
                }`}
              >
                {msg.role === 'assistant' ? (
                  <div className="prose prose-sm max-w-none dark:prose-invert">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <Text style={{ color: 'white' }}>{msg.content}</Text>
                )}
              </div>
              {msg.role === 'user' && (
                <Avatar icon={<UserOutlined />} className="bg-gray-400 shrink-0" />
              )}
            </div>
          ))
        )}

        {isTyping && (
          <div className="flex gap-3">
            <Avatar icon={<RobotOutlined />} className="bg-primary-500" />
            <div className="bg-gray-100 px-4 py-3 rounded-lg">
              <Spin size="small" />
              <Text className="ml-2 text-gray-500">Thinking...</Text>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t p-4">
        <div className="flex gap-2 mb-2">
          <Tooltip title="Attach file (coming soon)">
            <Button icon={<PaperClipOutlined />} disabled />
          </Tooltip>
        </div>
        <div className="flex gap-2">
          <TextArea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about resources, alerts, deployments..."
            autoSize={{ minRows: 1, maxRows: 4 }}
            className="flex-1"
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            disabled={!inputValue.trim()}
          />
        </div>
        <Text type="secondary" className="text-xs mt-2 block">
          Press Enter to send, Shift+Enter for new line
        </Text>
      </div>
    </Drawer>
  )
}
