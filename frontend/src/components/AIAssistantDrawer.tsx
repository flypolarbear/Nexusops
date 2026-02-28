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
  Statistic,
  Row,
  Col,
  Card,
  Tag,
  Divider,
  List,
} from 'antd'
import {
  RobotOutlined,
  UserOutlined,
  SendOutlined,
  DeleteOutlined,
  PaperClipOutlined,
  ThunderboltOutlined,
  MessageOutlined,
  CheckCircleOutlined,
  RocketOutlined,
  RollbackOutlined,
  LineChartOutlined,
  FileTextOutlined,
  SwapOutlined,
} from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useChatStore } from '../stores/chatStore'
import { useAuthStore } from '../stores/authStore'
import { useVersionStore } from '../stores/versionStore'
import type { Message } from '../types'

const { Text } = Typography
const { TextArea } = Input

interface AIAssistantDrawerProps {
  open: boolean
  onClose: () => void
}

// Slash commands definition
interface SlashCommand {
  command: string
  description: string
  usage: string
  icon: React.ReactNode
  example: string
}

const slashCommands: SlashCommand[] = [
  {
    command: '/deploy',
    description: 'Deploy a version to a region',
    usage: '/deploy <version> to <region>',
    icon: <RocketOutlined />,
    example: '/deploy Phoenix to us-east',
  },
  {
    command: '/rollback',
    description: 'Rollback a version in a region',
    usage: '/rollback <version> in <region>',
    icon: <RollbackOutlined />,
    example: '/rollback Aurora in eu-west',
  },
  {
    command: '/status',
    description: 'Check version status',
    usage: '/status <version>',
    icon: <LineChartOutlined />,
    example: '/status Phoenix',
  },
  {
    command: '/logs',
    description: 'View service logs',
    usage: '/logs <service> --tail <lines>',
    icon: <FileTextOutlined />,
    example: '/logs api-gateway --tail 100',
  },
  {
    command: '/compare',
    description: 'Compare two versions',
    usage: '/compare <v1> vs <v2>',
    icon: <SwapOutlined />,
    example: '/compare Phoenix vs Titan',
  },
]

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
`,
  '/deploy': `## 🚀 Deployment Triggered

**Version:** {version}
**Target Region:** {region}

### Deployment Progress
\`\`\`
[████████░░] 80% - Applying manifests...
\`\`\`

### Steps Completed:
1. ✅ Image pulled successfully
2. ✅ Pre-deployment checks passed
3. 🔄 Applying Kubernetes manifests
4. ⏳ Health check pending

The deployment is in progress. I'll notify you when it completes.

**Track progress:** [View in ArgoCD →](https://argocd.example.com)
`,
  '/rollback': `## ⏪ Rollback Initiated

**Version:** {version}
**Region:** {region}

Rolling back to the previous stable version...

### Rollback Steps:
1. ✅ Previous revision identified (Revision 41)
2. ✅ Rollback command sent to ArgoCD
3. 🔄 Waiting for sync to complete

**Estimated time:** ~2 minutes

[View rollback status →](https://argocd.example.com)
`,
  '/status': `## 📊 Version Status: {version}

### Deployment Summary
| Region | Status | Health | Replicas |
|--------|--------|--------|----------|
| US East | ✅ Synced | 🟢 Healthy | 3/3 |
| US West | ✅ Synced | 🟢 Healthy | 2/2 |
| EU West | ⚠️ Out of Sync | 🟡 Progressing | 1/2 |
| AP East | ❌ Failed | 🔴 Degraded | 0/1 |

### Recent Events
- **14:30** - Deployed to US East
- **14:25** - Deployed to US West
- **14:20** - Deploy started

### Resource Usage
- CPU: 450m / 500m (90%)
- Memory: 768Mi / 1Gi (75%)

**Action Required:** EU West and AP East need attention.
`,
  '/logs': `## 📋 Service Logs: {service}

Showing last **{lines}** lines:

\`\`\`log
2024-01-15 14:32:15 INFO  [main] Request received: GET /api/v1/users
2024-01-15 14:32:15 DEBUG [db] Query executed in 23ms
2024-01-15 14:32:15 INFO  [main] Response sent: 200 OK
2024-01-15 14:32:16 WARN  [cache] Cache miss for key: user_preferences_123
2024-01-15 14:32:16 INFO  [main] Cache refreshed for user_preferences_123
2024-01-15 14:32:17 ERROR [worker] Connection timeout to redis-master
2024-01-15 14:32:18 INFO  [worker] Retrying connection...
2024-01-15 14:32:19 INFO  [worker] Connection restored
2024-01-15 14:32:20 INFO  [main] Health check passed
\`\`\`

**Analysis:** One connection timeout detected but auto-recovered.
[View full logs in Grafana →](https://grafana.example.com)
`,
  '/compare': `## 🔄 Version Comparison

### {v1} vs {v2}

| Aspect | {v1} | {v2} |
|--------|------|------|
| **Git Branch** | feature/phoenix | feature/titan |
| **Image Version** | v1.2.3-rc3 | v1.2.4-beta2 |
| **Deployed Regions** | 5 | 1 |
| **Health Status** | 🟢 4/5 Healthy | 🟢 1/1 Healthy |
| **CPU Usage** | 450m avg | 500m avg |
| **Memory Usage** | 768Mi avg | 1Gi avg |

### Key Differences
- **{v1}**: Production-ready, deployed to multiple regions
- **{v2}**: Testing phase, new translation features

### Recommendation
{v1} is ready for production promotion. {v2} needs more testing before wide deployment.
`,
}

function getMockResponse(query: string): string {
  const lowerQuery = query.toLowerCase()

  // Handle slash commands
  if (query.startsWith('/deploy')) {
    const match = query.match(/\/deploy\s+(\w+)\s+to\s+(\w+)/i)
    if (match) {
      return mockResponses['/deploy']
        .replace('{version}', match[1])
        .replace('{region}', match[2])
    }
    return `**Usage:** \`/deploy <version> to <region>\`\n\nExample: \`/deploy Phoenix to us-east\``
  }

  if (query.startsWith('/rollback')) {
    const match = query.match(/\/rollback\s+(\w+)\s+in\s+(\w+)/i)
    if (match) {
      return mockResponses['/rollback']
        .replace('{version}', match[1])
        .replace('{region}', match[2])
    }
    return `**Usage:** \`/rollback <version> in <region>\`\n\nExample: \`/rollback Aurora in eu-west\``
  }

  if (query.startsWith('/status')) {
    const match = query.match(/\/status\s+(\w+)/i)
    if (match) {
      return mockResponses['/status'].replace(/{version}/g, match[1])
    }
    return `**Usage:** \`/status <version>\`\n\nExample: \`/status Phoenix\``
  }

  if (query.startsWith('/logs')) {
    const match = query.match(/\/logs\s+(\S+)(?:\s+--tail\s+(\d+))?/i)
    if (match) {
      return mockResponses['/logs']
        .replace('{service}', match[1])
        .replace('{lines}', match[2] || '50')
    }
    return `**Usage:** \`/logs <service> --tail <lines>\`\n\nExample: \`/logs api-gateway --tail 100\``
  }

  if (query.startsWith('/compare')) {
    const match = query.match(/\/compare\s+(\w+)\s+vs\s+(\w+)/i)
    if (match) {
      return mockResponses['/compare']
        .replace(/{v1}/g, match[1])
        .replace(/{v2}/g, match[2])
    }
    return `**Usage:** \`/compare <v1> vs <v2>\`\n\nExample: \`/compare Phoenix vs Titan\``
  }

  // Regular queries
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
  const [showCommands, setShowCommands] = useState(false)
  const [filteredCommands, setFilteredCommands] = useState<SlashCommand[]>(slashCommands)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<any>(null)

  const { messages, isTyping, addMessage, setTyping, clearMessages } = useChatStore()
  useAuthStore() // Keep auth store initialized
  useVersionStore() // Keep version store initialized

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Filter commands based on input
  useEffect(() => {
    if (inputValue.startsWith('/')) {
      const query = inputValue.toLowerCase()
      const filtered = slashCommands.filter(cmd =>
        cmd.command.toLowerCase().startsWith(query) ||
        cmd.description.toLowerCase().includes(query.slice(1))
      )
      setFilteredCommands(filtered)
      setShowCommands(true)
    } else {
      setShowCommands(false)
    }
  }, [inputValue])

  const handleSend = useCallback(async () => {
    if (!inputValue.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      conversationId: 'demo',
      role: 'user',
      content: inputValue.trim(),
      createdAt: new Date().toISOString(),
    }
    addMessage(userMessage)
    const queryToSend = inputValue.trim()
    setInputValue('')
    setShowCommands(false)
    setTyping(true)

    try {
      // Call real backend API
      const response = await fetch('/api/v1/agents/nexusops.chat/invoke', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          request_id: `req-${Date.now()}`,
          conversation_id: 'demo',
          agent_id: 'nexusops.chat',
          query: queryToSend,
        }),
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      const data = await response.json()

      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        conversationId: 'demo',
        role: 'assistant',
        content: data.content?.text || data.content || 'Sorry, I could not process your request.',
        createdAt: new Date().toISOString(),
      }
      addMessage(aiResponse)
    } catch (error) {
      console.error('AI API error:', error)
      // Fallback to mock response on error
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        conversationId: 'demo',
        role: 'assistant',
        content: getMockResponse(userMessage.content),
        createdAt: new Date().toISOString(),
      }
      addMessage(aiResponse)
    } finally {
      setTyping(false)
    }
  }, [inputValue, addMessage, setTyping])

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleCommandSelect = (cmd: SlashCommand) => {
    setInputValue(cmd.example)
    setShowCommands(false)
    inputRef.current?.focus()
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
          <Tag color="purple" className="ml-2">OPS-003</Tag>
        </div>
      }
      placement="right"
      width={500}
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
      {/* Conversation Stats */}
      <div className="p-4 border-b bg-gray-50">
        <Row gutter={12}>
          <Col span={12}>
            <Card size="small" className="text-center">
              <Statistic
                title="Today's Conversations"
                value={12847}
                prefix={<MessageOutlined className="text-blue-500" />}
                valueStyle={{ fontSize: 18, color: '#3b82f6' }}
              />
              <Tag color="green" className="mt-1">+12% vs yesterday</Tag>
            </Card>
          </Col>
          <Col span={12}>
            <Card size="small" className="text-center">
              <Statistic
                title="Success Rate"
                value={99.2}
                suffix="%"
                prefix={<CheckCircleOutlined className="text-green-500" />}
                valueStyle={{ fontSize: 18, color: '#22c55e' }}
              />
              <Tag color="green" className="mt-1">+0.3%</Tag>
            </Card>
          </Col>
        </Row>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center">
            <Avatar size={64} icon={<RobotOutlined />} className="bg-primary-500 mb-4" />
            <Text strong className="text-lg mb-2">How can I help you today?</Text>
            <Text type="secondary" className="mb-4">
              Ask me about resources, alerts, deployments, or use slash commands.
            </Text>

            {/* Slash Commands Quick Reference */}
            <div className="w-full max-w-sm mb-4">
              <Divider className="text-xs text-gray-400">Quick Commands</Divider>
              <div className="space-y-2">
                {slashCommands.slice(0, 3).map((cmd, i) => (
                  <Button
                    key={i}
                    block
                    size="small"
                    type="dashed"
                    onClick={() => handleCommandSelect(cmd)}
                    className="text-left"
                  >
                    {cmd.icon}
                    <span className="ml-2 font-mono text-xs">{cmd.command}</span>
                    <span className="ml-2 text-gray-400">{cmd.description}</span>
                  </Button>
                ))}
                <Button
                  block
                  size="small"
                  type="link"
                  onClick={() => {
                    setInputValue('/')
                    setShowCommands(true)
                  }}
                >
                  View all commands...
                </Button>
              </div>
            </div>

            {/* Regular Quick Queries */}
            <div className="space-y-2 w-full max-w-xs">
              <Divider className="text-xs text-gray-400">Common Queries</Divider>
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
                    : 'bg-slate-50/85 border border-slate-100'
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

      {/* Command Autocomplete */}
      {showCommands && filteredCommands.length > 0 && (
        <div className="border-t bg-white p-2 max-h-48 overflow-auto">
          <Text type="secondary" className="text-xs px-2">Available Commands</Text>
          <List
            size="small"
            dataSource={filteredCommands}
            renderItem={(cmd) => (
              <List.Item
                className="cursor-pointer hover:bg-gray-50 px-2 rounded"
                onClick={() => handleCommandSelect(cmd)}
              >
                <div className="flex items-center gap-3 w-full">
                  <span className="text-primary-500">{cmd.icon}</span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <code className="text-sm font-medium">{cmd.command}</code>
                      <Text type="secondary" className="text-xs">{cmd.description}</Text>
                    </div>
                    <Text type="secondary" className="text-xs">{cmd.usage}</Text>
                  </div>
                </div>
              </List.Item>
            )}
          />
        </div>
      )}

      {/* Input Area */}
      <div className="border-t p-4">
        <div className="flex gap-2 mb-2">
          <Tooltip title="Attach file (coming soon)">
            <Button icon={<PaperClipOutlined />} disabled />
          </Tooltip>
          <Tooltip title="Show commands">
            <Button
              icon={<ThunderboltOutlined />}
              onClick={() => {
                setInputValue('/')
                setShowCommands(true)
                inputRef.current?.focus()
              }}
            />
          </Tooltip>
        </div>
        <div className="flex gap-2">
          <TextArea
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about resources, alerts, deployments... or use /commands"
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
          Press Enter to send • Type <code>/</code> for commands • Shift+Enter for new line
        </Text>
      </div>
    </Drawer>
  )
}
