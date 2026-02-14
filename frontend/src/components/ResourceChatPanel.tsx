import { useState, useRef, useEffect } from 'react'
import {
  Card,
  Input,
  Button,
  Avatar,
  Typography,
  Tag,
  Space,
  Tooltip,
  Progress,
  List,
} from 'antd'
import {
  RobotOutlined,
  SendOutlined,
  CheckCircleOutlined,
  SearchOutlined,
  BugOutlined,
  SafetyOutlined,
  DashboardOutlined,
  CodeOutlined,
  RightOutlined,
  SyncOutlined,
} from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

const { Text, Title } = Typography
const { TextArea } = Input

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  resources?: AnalyzedResource[]
  actions?: SuggestedAction[]
}

export interface AnalyzedResource {
  name: string
  namespace: string
  cluster: string
  status: 'healthy' | 'warning' | 'critical'
  metrics: Record<string, string | number>
  insight: string
}

interface SuggestedAction {
  label: string
  action: string
  type: 'fix' | 'investigate' | 'optimize' | 'info'
}

// Quick action templates
const quickActions = [
  {
    icon: <BugOutlined />,
    label: 'Check failing pods',
    prompt: 'Show me all pods that are failing or in error state',
  },
  {
    icon: <DashboardOutlined />,
    label: 'Resource bottlenecks',
    prompt: 'Analyze resource bottlenecks and identify pods near their limits',
  },
  {
    icon: <SafetyOutlined />,
    label: 'Security audit',
    prompt: 'Run a security audit on all deployments and check for vulnerabilities',
  },
  {
    icon: <CodeOutlined />,
    label: 'Config audit',
    prompt: 'Check for misconfigurations in services and deployments',
  },
]

// Mock AI analysis responses
const mockAnalysisResponses: Record<string, ChatMessage> = {
  'failing': {
    id: '1',
    role: 'assistant',
    timestamp: new Date(),
    content: `## Analysis Results

I found **2 pods** with issues in the selected context:

### Critical Issues
| Pod | Namespace | Issue | Severity |
|-----|-----------|-------|----------|
| test-api-6b7c8 | default | CrashLoopBackOff | Critical |
| worker-9m2n4 | production | OOMKilled | High |

### Root Cause Analysis
The \`test-api-6b7c8\` pod is failing due to:
- Missing environment variable \`DATABASE_URL\`
- Liveness probe failing after 30s timeout

### Recommended Actions
\`\`\`yaml
# Add missing environment variable
env:
  - name: DATABASE_URL
    valueFrom:
      secretKeyRef:
        name: db-credentials
        key: url
\`\`\`
`,
    resources: [
      {
        name: 'test-api-6b7c8',
        namespace: 'default',
        cluster: 'Production Cluster',
        status: 'critical',
        metrics: { restarts: 15, age: '2h', cpu: '0m', memory: '0Mi' },
        insight: 'CrashLoopBackOff due to missing config',
      },
      {
        name: 'worker-9m2n4',
        namespace: 'production',
        cluster: 'Production Cluster',
        status: 'warning',
        metrics: { restarts: 3, age: '5d', cpu: '850m', memory: '890Mi' },
        insight: 'OOMKilled - needs memory increase',
      },
    ],
    actions: [
      { label: 'View pod logs', action: 'logs:test-api-6b7c8', type: 'investigate' },
      { label: 'Apply config fix', action: 'fix:test-api-6b7c8', type: 'fix' },
      { label: 'Increase memory limit', action: 'fix:worker-9m2n4', type: 'optimize' },
    ],
  },
  'bottleneck': {
    id: '2',
    role: 'assistant',
    timestamp: new Date(),
    content: `## Resource Bottleneck Analysis

I analyzed resource usage across all namespaces. Here's what I found:

### High Resource Consumers
The following pods are consuming more than 80% of their allocated resources:

1. **api-gateway-7d8f9** - Memory at 92% of limit
2. **chat-service-3k4j1** - CPU at 85% of limit
3. **redis-master-0** - Memory at 88% of limit

### Resource Quota Status
| Namespace | CPU Quota | Memory Quota | Status |
|-----------|-----------|--------------|--------|
| production | 78% used | 85% used | ⚠️ Warning |
| monitoring | 45% used | 52% used | ✅ Healthy |
| default | 23% used | 31% used | ✅ Healthy |

### Recommendations
- **Immediate**: Increase memory limit for \`api-gateway\` to prevent OOM
- **Short-term**: Scale \`chat-service\` horizontally to distribute load
- **Long-term**: Review and optimize resource requests across all services
`,
    resources: [
      {
        name: 'api-gateway-7d8f9',
        namespace: 'production',
        cluster: 'Production Cluster',
        status: 'critical',
        metrics: { cpu: '450m/500m', memory: '920Mi/1Gi', 'cpu%': 90, 'mem%': 92 },
        insight: 'Memory approaching limit, risk of OOM',
      },
      {
        name: 'chat-service-3k4j1',
        namespace: 'production',
        cluster: 'Production Cluster',
        status: 'warning',
        metrics: { cpu: '425m/500m', memory: '700Mi/1Gi', 'cpu%': 85, 'mem%': 70 },
        insight: 'CPU throttling detected',
      },
    ],
    actions: [
      { label: 'Scale api-gateway', action: 'scale:api-gateway', type: 'optimize' },
      { label: 'Adjust resource limits', action: 'fix:resources', type: 'fix' },
      { label: 'View metrics dashboard', action: 'dashboard:resources', type: 'info' },
    ],
  },
  'default': {
    id: '3',
    role: 'assistant',
    timestamp: new Date(),
    content: `I understand you're asking about your Kubernetes resources.

Here's a quick overview of what I can help you with:

### Available Analysis Types
- **Health Check**: Analyze pod health, readiness, and liveness status
- **Resource Audit**: Review CPU/memory usage and identify bottlenecks
- **Security Scan**: Check for vulnerabilities and misconfigurations
- **Configuration Review**: Validate deployments, services, and configs

### Example Queries
\`\`\`
"Show me all pods with high memory usage"
"Why is my deployment failing?"
"Check security issues in production namespace"
"Analyze resource quotas and limits"
\`\`\`

What would you like to analyze?
`,
    actions: [
      { label: 'Full cluster health check', action: 'analyze:health', type: 'info' },
      { label: 'Security audit', action: 'analyze:security', type: 'investigate' },
    ],
  },
}

function getAnalysisResponse(query: string): ChatMessage {
  const lowerQuery = query.toLowerCase()
  if (lowerQuery.includes('fail') || lowerQuery.includes('error') || lowerQuery.includes('crash')) {
    return mockAnalysisResponses['failing']
  }
  if (lowerQuery.includes('bottleneck') || lowerQuery.includes('resource') || lowerQuery.includes('memory') || lowerQuery.includes('cpu')) {
    return mockAnalysisResponses['bottleneck']
  }
  return { ...mockAnalysisResponses['default'], id: Date.now().toString() }
}

interface ResourceChatPanelProps {
  onResourceSelect?: (resource: AnalyzedResource) => void
  onActionExecute?: (action: string) => void
}

export default function ResourceChatPanel({ onResourceSelect, onActionExecute }: ResourceChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!inputValue.trim()) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)

    // Simulate AI analysis delay
    await new Promise((resolve) => setTimeout(resolve, 1500))

    const response = getAnalysisResponse(inputValue)
    response.id = (Date.now() + 1).toString()
    response.timestamp = new Date()

    setMessages((prev) => [...prev, response])
    setIsLoading(false)
  }

  const handleQuickAction = (prompt: string) => {
    setInputValue(prompt)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return '#22c55e'
      case 'warning':
        return '#eab308'
      case 'critical':
        return '#ef4444'
      default:
        return '#94a3b8'
    }
  }

  const getActionIcon = (type: string) => {
    switch (type) {
      case 'fix':
        return <CheckCircleOutlined className="text-green-500" />
      case 'investigate':
        return <SearchOutlined className="text-blue-500" />
      case 'optimize':
        return <DashboardOutlined className="text-purple-500" />
      default:
        return <RightOutlined />
    }
  }

  return (
    <Card
      className="h-full flex flex-col"
      styles={{ body: { flex: 1, display: 'flex', flexDirection: 'column', padding: 0 } }}
      title={
        <div className="flex items-center gap-2">
          <RobotOutlined className="text-primary-500" />
          <span>K8sGPT Resource Analysis</span>
          <Tag color="blue" className="ml-2">AI-Powered</Tag>
        </div>
      }
    >
      {/* Quick Actions Bar */}
      <div className="p-3 border-b bg-gray-50">
        <Text type="secondary" className="text-xs mb-2 block">Quick Actions</Text>
        <Space wrap size="small">
          {quickActions.map((action, index) => (
            <Tooltip key={index} title={action.prompt}>
              <Button
                size="small"
                icon={action.icon}
                onClick={() => handleQuickAction(action.prompt)}
                className="text-xs"
              >
                {action.label}
              </Button>
            </Tooltip>
          ))}
        </Space>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center">
            <Avatar size={64} icon={<RobotOutlined />} className="bg-primary-500 mb-4" />
            <Title level={5} className="mb-2">K8sGPT Resource Analyzer</Title>
            <Text type="secondary" className="mb-4 max-w-md">
              Ask questions about your Kubernetes resources in natural language.
              I'll analyze and provide actionable insights.
            </Text>
            <div className="space-y-2 w-full max-w-sm">
              <Text type="secondary" className="text-xs">Try asking:</Text>
              <div className="space-y-2">
                {[
                  'Show pods with high memory usage',
                  'Why is my deployment failing?',
                  'Check for security issues',
                ].map((query, i) => (
                  <Button
                    key={i}
                    block
                    size="small"
                    type="dashed"
                    onClick={() => setInputValue(query)}
                    className="text-left"
                  >
                    <SearchOutlined className="mr-2" />
                    {query}
                  </Button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {message.role === 'assistant' && (
                <Avatar icon={<RobotOutlined />} className="bg-primary-500 shrink-0" />
              )}
              <div className={`max-w-[85%] ${message.role === 'user' ? '' : 'w-full'}`}>
                {message.role === 'user' ? (
                  <div className="bg-primary-500 text-white px-4 py-2 rounded-lg">
                    <Text style={{ color: 'white' }}>{message.content}</Text>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {/* Markdown Content */}
                    <div className="bg-gray-50 px-4 py-3 rounded-lg">
                      <div className="prose prose-sm max-w-none">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {message.content}
                        </ReactMarkdown>
                      </div>
                    </div>

                    {/* Analyzed Resources */}
                    {message.resources && message.resources.length > 0 && (
                      <div className="bg-white border rounded-lg p-3">
                        <Text strong className="text-xs text-gray-500 mb-2 block">
                          AFFECTED RESOURCES
                        </Text>
                        <List
                          size="small"
                          dataSource={message.resources}
                          renderItem={(resource) => (
                            <List.Item
                              className="cursor-pointer hover:bg-gray-50 px-2 rounded"
                              onClick={() => onResourceSelect?.(resource)}
                            >
                              <div className="flex items-center justify-between w-full">
                                <div className="flex items-center gap-3">
                                  <div
                                    className="w-2 h-2 rounded-full"
                                    style={{ backgroundColor: getStatusColor(resource.status) }}
                                  />
                                  <div>
                                    <Text strong className="text-sm">{resource.name}</Text>
                                    <Text type="secondary" className="text-xs ml-2">
                                      {resource.namespace}
                                    </Text>
                                  </div>
                                </div>
                                <div className="flex items-center gap-4">
                                  {resource.metrics['cpu%'] !== undefined && (
                                    <Progress
                                      percent={resource.metrics['cpu%'] as number}
                                      size="small"
                                      style={{ width: 60 }}
                                      strokeColor={resource.metrics['cpu%'] as number > 80 ? '#ef4444' : '#22c55e'}
                                      showInfo={false}
                                    />
                                  )}
                                  <Text type="secondary" className="text-xs">
                                    {resource.insight}
                                  </Text>
                                </div>
                              </div>
                            </List.Item>
                          )}
                        />
                      </div>
                    )}

                    {/* Suggested Actions */}
                    {message.actions && message.actions.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {message.actions.map((action, i) => (
                          <Button
                            key={i}
                            size="small"
                            icon={getActionIcon(action.type)}
                            onClick={() => onActionExecute?.(action.action)}
                            type={action.type === 'fix' ? 'primary' : 'default'}
                          >
                            {action.label}
                          </Button>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
              {message.role === 'user' && (
                <Avatar icon={<RobotOutlined />} className="bg-gray-400 shrink-0" />
              )}
            </div>
          ))
        )}

        {isLoading && (
          <div className="flex gap-3">
            <Avatar icon={<RobotOutlined />} className="bg-primary-500" />
            <div className="bg-gray-50 px-4 py-3 rounded-lg flex items-center gap-2">
              <SyncOutlined spin className="text-primary-500" />
              <Text type="secondary">Analyzing resources...</Text>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t p-3">
        <div className="flex gap-2">
          <TextArea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about your K8s resources... (e.g., 'Show pods with errors')"
            autoSize={{ minRows: 1, maxRows: 3 }}
            className="flex-1"
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            disabled={!inputValue.trim() || isLoading}
          />
        </div>
        <Text type="secondary" className="text-xs mt-1 block">
          Press Enter to analyze, Shift+Enter for new line
        </Text>
      </div>
    </Card>
  )
}
