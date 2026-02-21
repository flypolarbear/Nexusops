import { useState, useRef, useEffect } from 'react'
import { Card, Typography, Input, Button, Space, Avatar, Spin, Empty, List, Typography as AntTypography } from 'antd'
import { SendOutlined, RobotOutlined, UserOutlined, PlusOutlined, HistoryOutlined } from '@ant-design/icons'
import { useChatStore } from '../stores/chatStore'
import { useWebSocket } from '../hooks/useWebSocket'
import PageContainer from '../components/layout/PageContainer'

const { Title, Text } = Typography
const { TextArea } = Input
const { Paragraph } = AntTypography

const mockConversations = [
  { id: 'conv-1', title: 'Resource status check', createdAt: '2024-01-15 14:00' },
  { id: 'conv-2', title: 'Deployment issues', createdAt: '2024-01-15 10:30' },
  { id: 'conv-3', title: 'Alert investigation', createdAt: '2024-01-14 16:00' },
]

export default function AIAssistant() {
  const [inputValue, setInputValue] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { messages, isTyping, isConnected, currentConversation, setCurrentConversation, clearMessages } = useChatStore()
  const { sendMessage } = useWebSocket()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = () => {
    if (!inputValue.trim()) return

    sendMessage(inputValue.trim())
    setInputValue('')
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const quickQueries = [
    'What is the current status of api-gateway?',
    'Show me alerts from the last 24 hours',
    'Which services are using the most resources?',
    'List recent failed deployments',
  ]

  return (
    <PageContainer transparent fullHeight>
      <div className="h-full flex gap-4">
        {/* Conversation Sidebar */}
      <Card className="w-64 shrink-0" title="Conversations" extra={<Button type="text" icon={<PlusOutlined />} onClick={clearMessages} />}>
        <List
          dataSource={mockConversations}
          renderItem={(item) => (
            <List.Item
              className="cursor-pointer hover:bg-gray-50 px-2 rounded"
              onClick={() => setCurrentConversation({ id: item.id, title: item.title } as any)}
            >
              <div className="flex items-center gap-2">
                <HistoryOutlined className="text-gray-400" />
                <div>
                  <div className="text-sm font-medium">{item.title}</div>
                  <div className="text-xs text-gray-400">{item.createdAt}</div>
                </div>
              </div>
            </List.Item>
          )}
        />
      </Card>

      {/* Main Chat Area */}
      <Card className="flex-1 flex flex-col" bodyStyle={{ flex: 1, display: 'flex', flexDirection: 'column', padding: 0 }}>
        {/* Status Bar */}
        <div className="px-4 py-2 border-b border-gray-200 flex items-center justify-between">
          <Title level={5} className="m-0">
            {currentConversation?.title || 'New Conversation'}
          </Title>
          <Space>
            <Text type="secondary">
              {isConnected ? (
                <span className="text-green-500">Connected</span>
              ) : (
                <span className="text-red-500">Disconnected</span>
              )}
            </Text>
          </Space>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center">
              <Empty description="Start a conversation with the AI Assistant">
                <div className="mt-4 space-y-2">
                  <Text type="secondary">Try asking:</Text>
                  {quickQueries.map((query, index) => (
                    <div key={index}>
                      <Button
                        type="dashed"
                        size="small"
                        onClick={() => {
                          setInputValue(query)
                        }}
                      >
                        {query}
                      </Button>
                    </div>
                  ))}
                </div>
              </Empty>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {message.role === 'assistant' && (
                  <Avatar icon={<RobotOutlined />} className="bg-primary-500" />
                )}
                <div
                  className={`max-w-[70%] px-4 py-2 rounded-lg ${
                    message.role === 'user'
                      ? 'bg-primary-500 text-white'
                      : 'bg-gray-100'
                  }`}
                >
                  <Paragraph className="m-0" style={{ color: message.role === 'user' ? 'white' : 'inherit' }}>
                    {message.content}
                  </Paragraph>
                </div>
                {message.role === 'user' && (
                  <Avatar icon={<UserOutlined />} className="bg-gray-400" />
                )}
              </div>
            ))
          )}

          {isTyping && (
            <div className="flex gap-3">
              <Avatar icon={<RobotOutlined />} className="bg-primary-500" />
              <div className="bg-gray-100 px-4 py-2 rounded-lg">
                <Spin size="small" />
                <Text className="ml-2">Thinking...</Text>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-gray-200">
          <Space.Compact className="w-full">
            <TextArea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about resources, alerts, deployments..."
              autoSize={{ minRows: 1, maxRows: 4 }}
              className="rounded-l-lg"
            />
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSend}
              disabled={!inputValue.trim() || !isConnected}
              className="h-auto"
            >
              Send
            </Button>
          </Space.Compact>
          <Text type="secondary" className="text-xs mt-1 block">
            AI responses are read-only and provide suggestions with links to relevant pages.
          </Text>
        </div>
      </Card>
      </div>
    </PageContainer>
  )
}
