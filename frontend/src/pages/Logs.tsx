import { useState, useRef, useEffect } from 'react'
import {
  Card,
  Input,
  Button,
  Select,
  DatePicker,
  Space,
  Typography,
  Avatar,
  message,
  Divider,
  Tag,
  Tooltip,
} from 'antd'
import {
  SendOutlined,
  DownloadOutlined,
  RobotOutlined,
  UserOutlined,
  ThunderboltOutlined,
  HistoryOutlined,
  PlusOutlined,
  MessageOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { AgentResponseRenderer } from '../components/AgentResponseRenderer'
import type { AgentMessage, AgentAction } from '../types/agent'
import PageContainer from '../components/layout/PageContainer'

const { Title, Text } = Typography
const { RangePicker } = DatePicker
const { TextArea } = Input

// ============================================
// Types & Mocks
// ============================================

const INITIAL_MESSAGES: AgentMessage[] = [
  {
    id: 'msg-init-1',
    role: 'assistant',
    content: '**Log Analysis Agent initialized.**\n\nI am connected to your logging infrastructure via MCP. You can ask me to analyze errors, find specific traces, or summarize log trends for a specific service and time range.\n\n*Example queries:*\n- "Find the root cause of the 500 errors in auth-service in the last hour"\n- "Summarize the warnings from the payment gateway"\n- "Check for any memory leak traces in frontend"',
    created_at: new Date().toISOString(),
    conversation_id: 'default',
    agent_id: 'nexusops.log',
  },
]

const MOCK_HISTORY = [
  { id: 'sess-1', title: '500 errors in auth-service', date: '2 hours ago', mcp: 'aws-cloudwatch' },
  { id: 'sess-2', title: 'Memory leak in frontend', date: 'Yesterday', mcp: 'datadog' },
  { id: 'sess-3', title: 'Payment gateway timeouts', date: 'Last week', mcp: 'elasticsearch' },
  { id: 'sess-4', title: 'Redis slow queries', date: '2 weeks ago', mcp: 'fluent-bit' },
]

// ============================================
// Main Component
// ============================================

export default function Logs() {
  const [messages, setMessages] = useState<AgentMessage[]>(INITIAL_MESSAGES)
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [historyVisible, setHistoryVisible] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Filters
  const [service, setService] = useState('auth-service')
  const [mcp, setMcp] = useState('aws-cloudwatch')
  const [timeRange, setTimeRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>([
    dayjs().subtract(1, 'hour'),
    dayjs(),
  ])

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = () => {
    if (!inputValue.trim() || loading) return

    const userMessage: AgentMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      created_at: new Date().toISOString(),
      conversation_id: 'default',
    }

    setMessages((prev) => [...prev, userMessage])
    setInputValue('')
    setLoading(true)

    // Simulate Agent processing delay
    setTimeout(() => {
      let assistantMessage: AgentMessage

      const lowerInput = userMessage.content.toLowerCase()

      if (lowerInput.includes('error') || lowerInput.includes('500') || lowerInput.includes('crash') || lowerInput.includes('cause')) {
        assistantMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `I queried the \`${service}\` logs via **${mcp}** MCP for the selected time range. I used my \`log-analysis\` skill to aggregate the traces and found 12 occurrences of HTTP 500 errors. Here is the root cause analysis:`,
          created_at: new Date().toISOString(),
          conversation_id: 'default',
          agent_id: 'nexusops.log',
          structured_output: {
            type: 'error_diagnosis',
            data: {
              error_type: 'DatabaseConnectionTimeout',
              error_message: 'Timeout waiting for idle object from pool in auth-service.',
              root_cause: 'The RDS instance `nexus-db-prod` experienced a CPU spike, causing all incoming connection requests from `auth-service` to queue up and eventually time out.',
              affected_resources: ['auth-service', 'nexus-db-prod'],
              fix_steps: [
                'Scale up the RDS instance to a larger tier',
                'Increase the connection pool timeout in auth-service configuration',
                'Check for slow queries causing the CPU spike in the database'
              ]
            }
          },
          suggested_actions: [
            {
              id: 'scale_db',
              type: 'scale',
              label: 'Scale RDS Instance',
              params: { resource: 'nexus-db-prod' }
            },
            {
              id: 'query_slow_logs',
              type: 'query',
              label: 'Query DB Slow Logs',
              params: { action: 'fetch_slow_logs' }
            }
          ],
        }
      } else {
        assistantMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `I analyzed the logs from \`${service}\` via **${mcp}** MCP.\n\nThe log volume is normal (~450 req/min). There are no critical errors, but I noticed a slight increase in latency for the \`/api/health\` endpoint. Let me know if you want me to dig deeper into the latency traces.`,
          created_at: new Date().toISOString(),
          conversation_id: 'default',
          agent_id: 'nexusops.log',
          suggested_actions: [
            {
              id: 'analyze_latency',
              type: 'query',
              label: 'Analyze Latency Traces',
              params: { action: 'analyze_latency' }
            }
          ]
        }
      }

      setMessages((prev) => [...prev, assistantMessage])
      setLoading(false)
    }, 2000)
  }

  const handleDownload5Min = () => {
    message.loading({ content: `Downloading raw logs for the last 5 minutes from ${mcp}...`, key: 'dl' })
    setTimeout(() => {
      message.success({ content: `Successfully downloaded context logs (nexus_${service}_5m.csv)`, key: 'dl' })
    }, 1500)
  }

  const handleClear = () => {
    setMessages(INITIAL_MESSAGES)
    message.info('Chat history cleared')
  }

  const handleActionClick = (action: AgentAction) => {
    if (action.type === 'query') {
      setInputValue(action.label)
      setTimeout(handleSend, 100)
    } else {
      message.success(`Executing action: ${action.label}`)
    }
  }

  return (
    <PageContainer transparent fullHeight contentClassName="flex gap-4">
      {/* History Sidebar */}
      {historyVisible && (
        <div className="w-64 bg-white rounded-lg shadow-sm border border-gray-200 flex flex-col overflow-hidden shrink-0 transition-all duration-300">
          <div className="p-3 border-b border-gray-200 flex justify-between items-center bg-gray-50">
            <Space>
              <HistoryOutlined className="text-gray-500" />
              <Text strong>History</Text>
            </Space>
            <Tooltip title="New Chat">
              <Button type="text" icon={<PlusOutlined />} size="small" onClick={handleClear} />
            </Tooltip>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {MOCK_HISTORY.map(h => (
              <div 
                key={h.id} 
                className="p-3 hover:bg-gray-100 rounded-lg cursor-pointer text-sm transition-colors border border-transparent hover:border-gray-200"
                onClick={() => {
                  message.info(`Loading history: ${h.title}`)
                  setMcp(h.mcp)
                }}
              >
                <div className="flex items-start gap-2">
                  <MessageOutlined className="text-gray-400 mt-1" />
                  <div className="flex-1 min-w-0">
                    <div className="truncate font-medium text-gray-700">{h.title}</div>
                    <div className="flex justify-between items-center mt-2">
                      <Text type="secondary" style={{ fontSize: '10px' }}>{h.date}</Text>
                      <Tag style={{ fontSize: '10px', margin: 0, padding: '0 4px', lineHeight: '14px' }}>
                        {h.mcp}
                      </Tag>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col space-y-4 min-w-0">
        {/* Header / Control Bar */}
        <Card size="small" className="shadow-sm border-b-0 shrink-0">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <Tooltip title={historyVisible ? "Hide History" : "Show History"}>
                <Button 
                  type="text" 
                  icon={<HistoryOutlined />} 
                  onClick={() => setHistoryVisible(!historyVisible)}
                  className={historyVisible ? "text-primary-500 bg-primary-50" : "text-gray-500"}
                />
              </Tooltip>
              <Divider type="vertical" className="m-0" />
              <Space>
                <ThunderboltOutlined className="text-primary-500 text-lg" />
                <Title level={5} className="m-0">Log Analysis Agent</Title>
              </Space>
              <Divider type="vertical" />
              <Space>
                <Text type="secondary">MCP:</Text>
                <Select
                  value={mcp}
                  onChange={setMcp}
                  style={{ width: 160 }}
                  options={[
                    { value: 'aws-cloudwatch', label: 'AWS CloudWatch' },
                    { value: 'elasticsearch', label: 'Elasticsearch' },
                    { value: 'datadog', label: 'Datadog' },
                    { value: 'fluent-bit', label: 'Fluent Bit' },
                  ]}
                />
              </Space>
              <Space>
                <Text type="secondary">Service:</Text>
                <Select
                  value={service}
                  onChange={setService}
                  style={{ width: 140 }}
                  options={[
                    { value: 'all', label: 'All Services' },
                    { value: 'auth-service', label: 'auth-service' },
                    { value: 'payment-service', label: 'payment-service' },
                    { value: 'frontend', label: 'frontend' },
                  ]}
                />
              </Space>
              <Space>
                <Text type="secondary">Time Range:</Text>
                <RangePicker
                  showTime
                  value={timeRange}
                  onChange={(dates) => setTimeRange(dates as any)}
                  style={{ width: 320 }}
                />
              </Space>
            </div>
            <Space>
              <Button
                type="primary"
                ghost
                icon={<DownloadOutlined />}
                onClick={handleDownload5Min}
              >
                Download Last 5-Min Logs
              </Button>
            </Space>
          </div>
        </Card>

        {/* Chat Area */}
        <Card className="flex-1 overflow-hidden flex flex-col shadow-sm" bodyStyle={{ padding: 0, display: 'flex', flexDirection: 'column', height: '100%' }}>
          {/* Messages List */}
          <div className="flex-1 overflow-y-auto p-4 space-y-6 bg-gray-50">
            {messages.map((msg, idx) => (
              <div
                key={msg.id || idx}
                className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
              >
                <Avatar
                  size="large"
                  icon={msg.role === 'user' ? <UserOutlined /> : <RobotOutlined />}
                  className={msg.role === 'user' ? 'bg-blue-500' : 'bg-green-500'}
                />
                <div className={`max-w-[80%] flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                  <div className="flex items-center gap-2 mb-1">
                    <Text type="secondary" className="text-xs">
                      {msg.role === 'user' ? 'You' : 'Log Agent'}
                    </Text>
                    <Text type="secondary" className="text-xs" style={{ fontSize: '10px' }}>
                      {new Date(msg.created_at).toLocaleTimeString()}
                    </Text>
                  </div>
                  
                  {msg.role === 'user' ? (
                    <div className="bg-blue-500 text-white px-4 py-2 rounded-lg rounded-tr-none shadow-sm text-[14px]">
                      {msg.content}
                    </div>
                  ) : (
                    <div className="w-full">
                      <AgentResponseRenderer
                        message={msg}
                        onActionClick={handleActionClick}
                        className="bg-white border border-gray-100 shadow-sm rounded-lg rounded-tl-none p-4 w-full"
                      />
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex gap-3 flex-row">
                <Avatar size="large" icon={<RobotOutlined />} className="bg-green-500" />
                <div className="max-w-[80%] flex flex-col items-start">
                  <div className="flex items-center gap-2 mb-1">
                    <Text type="secondary" className="text-xs">Log Agent</Text>
                  </div>
                  <AgentResponseRenderer
                    message={{ id: 'loading', conversation_id: 'default', role: 'assistant', content: '', created_at: new Date().toISOString() }}
                    loading={true}
                    className="bg-white border border-gray-100 shadow-sm rounded-lg rounded-tl-none p-4 w-64"
                  />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="p-4 bg-white border-t border-gray-200">
            <div className="relative">
              <TextArea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onPressEnter={(e) => {
                  if (!e.shiftKey) {
                    e.preventDefault()
                    handleSend()
                  }
                }}
                placeholder="e.g., Analyze the 500 errors in auth-service in the last hour..."
                autoSize={{ minRows: 2, maxRows: 6 }}
                className="pr-12 py-3 rounded-lg resize-none shadow-inner"
                disabled={loading}
              />
              <Button
                type="primary"
                shape="circle"
                icon={<SendOutlined />}
                onClick={handleSend}
                loading={loading}
                disabled={!inputValue.trim()}
                className="absolute right-3 bottom-3 z-10"
              />
            </div>
            <div className="mt-2 text-xs text-gray-400 flex items-center justify-between">
              <span>Powered by Model Context Protocol (MCP) & Log Analysis Skills</span>
              <span>Press Enter to send, Shift + Enter for new line</span>
            </div>
          </div>
        </Card>
      </div>
    </PageContainer>
  )
}
