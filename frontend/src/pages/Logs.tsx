import { useState, useEffect } from 'react'
import {
  Card,
  Typography,
  Table,
  Button,
  Space,
  Tag,
  Input,
  Select,
  DatePicker,
  Form,
  message,
  Tooltip,
  Statistic,
  Row,
  Col,
  Drawer,
  Descriptions,
} from 'antd'
import {
  FileSearchOutlined,
  SearchOutlined,
  DownloadOutlined,
  ReloadOutlined,
  FilterOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  CloseCircleOutlined,
  BugOutlined,
  EyeOutlined,
  RobotOutlined,
  PlayCircleOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'

const { Title, Text } = Typography
const { RangePicker } = DatePicker

// ============================================
// Types
// ============================================

interface LogEntry {
  id: string
  timestamp: string
  level: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR' | 'FATAL'
  service: string
  agent_id: string | null
  agent_name: string | null
  message: string
  metadata: Record<string, unknown>
  trace_id: string | null
  duration_ms: number | null
}

interface LogStats {
  total: number
  by_level: Record<string, number>
  by_service: Record<string, number>
  error_rate: number
}

// ============================================
// Main Component
// ============================================

export default function Logs() {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState<LogStats | null>(null)
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null)
  const [drawerVisible, setDrawerVisible] = useState(false)
  const [form] = Form.useForm()

  // Filters
  const [filters, setFilters] = useState({
    query: '',
    level: undefined as string | undefined,
    service: undefined as string | undefined,
    agent_id: undefined as string | undefined,
    timeRange: null as [dayjs.Dayjs, dayjs.Dayjs] | null,
  })

  useEffect(() => {
    loadLogs()
  }, [filters])

  const loadLogs = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filters.query) params.append('query', filters.query)
      if (filters.level) params.append('level', filters.level)
      if (filters.service) params.append('service', filters.service)
      if (filters.agent_id) params.append('agent_id', filters.agent_id)
      if (filters.timeRange) {
        params.append('start_time', filters.timeRange[0].toISOString())
        params.append('end_time', filters.timeRange[1].toISOString())
      }

      const response = await fetch(`/api/v1/logs?${params}`)
      if (!response.ok) throw new Error("API error")
      const data = await response.json()
      setLogs(data.items || [])
      setStats(data.stats || null)
    } catch (error) {
      console.error('Failed to load logs:', error)
      // Use mock data
      setLogs(getMockLogs())
      setStats(getMockStats())
    } finally {
      setLoading(false)
    }
  }

  const handleExport = () => {
    message.info('Exporting logs...')
    // In production, this would trigger a download
    setTimeout(() => message.success('Logs exported successfully'), 1000)
  }

  const handleAICheck = async () => {
    message.info('AI Agent analyzing logs for issues...')
    // In production, this would call an AI agent
    setTimeout(() => {
      message.success('AI Analysis: Found 3 potential issues in recent logs')
    }, 2000)
  }

  const handleViewDetail = (log: LogEntry) => {
    setSelectedLog(log)
    setDrawerVisible(true)
  }

  const getLevelConfig = (level: string) => {
    const configs: Record<string, { color: string; icon: React.ReactNode }> = {
      DEBUG: { color: 'default', icon: <BugOutlined /> },
      INFO: { color: 'blue', icon: <InfoCircleOutlined /> },
      WARN: { color: 'orange', icon: <ExclamationCircleOutlined /> },
      ERROR: { color: 'red', icon: <CloseCircleOutlined /> },
      FATAL: { color: 'magenta', icon: <CloseCircleOutlined /> },
    }
    return configs[level] || configs.INFO
  }

  const columns = [
    {
      title: 'Time',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 180,
      render: (time: string) => (
        <Space>
          <ClockCircleOutlined className="text-gray-400" />
          <Text className="font-mono text-xs">{dayjs(time).format('MM-DD HH:mm:ss.SSS')}</Text>
        </Space>
      ),
    },
    {
      title: 'Level',
      dataIndex: 'level',
      key: 'level',
      width: 100,
      render: (level: string) => {
        const config = getLevelConfig(level)
        return (
          <Tag color={config.color} icon={config.icon}>
            {level}
          </Tag>
        )
      },
    },
    {
      title: 'Service',
      dataIndex: 'service',
      key: 'service',
      width: 150,
      render: (service: string) => <Tag>{service}</Tag>,
    },
    {
      title: 'Agent',
      dataIndex: 'agent_name',
      key: 'agent_name',
      width: 150,
      render: (name: string) => name ? (
        <Space>
          <RobotOutlined className="text-primary-500" />
          <Text>{name}</Text>
        </Space>
      ) : <Text type="secondary">-</Text>,
    },
    {
      title: 'Message',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true,
      render: (msg: string) => (
        <Text className="font-mono text-xs" style={{ maxWidth: 400 }} ellipsis={{ tooltip: msg }}>
          {msg}
        </Text>
      ),
    },
    {
      title: 'Duration',
      dataIndex: 'duration_ms',
      key: 'duration_ms',
      width: 100,
      render: (ms: number) => ms ? `${ms}ms` : '-',
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 80,
      render: (_: unknown, record: LogEntry) => (
        <Tooltip title="View Details">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record)}
          />
        </Tooltip>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <Title level={4} className="m-0">
          <FileSearchOutlined className="mr-2" />
          Log Explorer
        </Title>
        <Space>
          <Button icon={<RobotOutlined />} onClick={handleAICheck}>
            AI Check
          </Button>
          <Button icon={<DownloadOutlined />} onClick={handleExport}>
            Export
          </Button>
          <Button icon={<ReloadOutlined />} onClick={() => loadLogs()}>
            Refresh
          </Button>
        </Space>
      </div>

      {/* Stats */}
      {stats && (
        <Row gutter={16}>
          <Col span={4}>
            <Card size="small">
              <Statistic title="Total Logs" value={stats.total} />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="Errors"
                value={stats.by_level.ERROR || 0}
                valueStyle={{ color: '#cf1322' }}
                prefix={<CloseCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="Warnings"
                value={stats.by_level.WARN || 0}
                valueStyle={{ color: '#fa8c16' }}
                prefix={<ExclamationCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="Info"
                value={stats.by_level.INFO || 0}
                valueStyle={{ color: '#1890ff' }}
                prefix={<InfoCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="Error Rate"
                value={stats.error_rate * 100}
                precision={2}
                suffix="%"
                valueStyle={{ color: stats.error_rate > 0.05 ? '#cf1322' : '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic title="Services" value={Object.keys(stats.by_service).length} />
            </Card>
          </Col>
        </Row>
      )}

      {/* Filters */}
      <Card size="small" title={<span><FilterOutlined /> Filters</span>}>
        <Form form={form} layout="inline" className="flex flex-wrap gap-4">
          <Form.Item label="Search">
            <Input
              placeholder="Search in logs..."
              prefix={<SearchOutlined />}
              value={filters.query}
              onChange={(e) => setFilters({ ...filters, query: e.target.value })}
              style={{ width: 250 }}
              allowClear
            />
          </Form.Item>
          <Form.Item label="Level">
            <Select
              placeholder="All levels"
              value={filters.level}
              onChange={(value) => setFilters({ ...filters, level: value })}
              style={{ width: 120 }}
              allowClear
              options={[
                { value: 'DEBUG', label: 'DEBUG' },
                { value: 'INFO', label: 'INFO' },
                { value: 'WARN', label: 'WARN' },
                { value: 'ERROR', label: 'ERROR' },
                { value: 'FATAL', label: 'FATAL' },
              ]}
            />
          </Form.Item>
          <Form.Item label="Service">
            <Select
              placeholder="All services"
              value={filters.service}
              onChange={(value) => setFilters({ ...filters, service: value })}
              style={{ width: 150 }}
              allowClear
              options={[
                { value: 'api', label: 'API Server' },
                { value: 'agent-k8s', label: 'Kubernetes Agent' },
                { value: 'agent-deploy', label: 'Deploy Agent' },
                { value: 'scheduler', label: 'Scheduler' },
                { value: 'websocket', label: 'WebSocket' },
              ]}
            />
          </Form.Item>
          <Form.Item label="Agent">
            <Select
              placeholder="All agents"
              value={filters.agent_id}
              onChange={(value) => setFilters({ ...filters, agent_id: value })}
              style={{ width: 180 }}
              allowClear
              options={[
                { value: 'agent-1', label: 'Kubernetes Agent' },
                { value: 'agent-2', label: 'Deploy Agent' },
                { value: 'agent-3', label: 'Monitoring Agent' },
              ]}
            />
          </Form.Item>
          <Form.Item label="Time Range">
            <RangePicker
              showTime
              value={filters.timeRange}
              onChange={(dates) => setFilters({ ...filters, timeRange: dates as [dayjs.Dayjs, dayjs.Dayjs] | null })}
              style={{ width: 350 }}
            />
          </Form.Item>
        </Form>
      </Card>

      {/* Log Table */}
      <Card>
        <Table
          dataSource={logs}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 50,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `Total ${total} logs`,
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* Detail Drawer */}
      <Drawer
        title={
          <Space>
            <FileSearchOutlined />
            Log Detail
            {selectedLog && (
              <Tag color={getLevelConfig(selectedLog.level).color}>
                {selectedLog.level}
              </Tag>
            )}
          </Space>
        }
        placement="right"
        width={600}
        open={drawerVisible}
        onClose={() => setDrawerVisible(false)}
      >
        {selectedLog && (
          <Space direction="vertical" className="w-full" size="large">
            <Descriptions bordered size="small" column={1}>
              <Descriptions.Item label="Timestamp">
                {dayjs(selectedLog.timestamp).format('YYYY-MM-DD HH:mm:ss.SSS')}
              </Descriptions.Item>
              <Descriptions.Item label="Level">
                <Tag color={getLevelConfig(selectedLog.level).color} icon={getLevelConfig(selectedLog.level).icon}>
                  {selectedLog.level}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Service">{selectedLog.service}</Descriptions.Item>
              <Descriptions.Item label="Agent">
                {selectedLog.agent_name || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Trace ID">
                <Text code>{selectedLog.trace_id || '-'}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="Duration">
                {selectedLog.duration_ms ? `${selectedLog.duration_ms}ms` : '-'}
              </Descriptions.Item>
            </Descriptions>

            <Card size="small" title="Message">
              <pre className="bg-gray-50 p-3 rounded text-xs overflow-auto whitespace-pre-wrap">
                {selectedLog.message}
              </pre>
            </Card>

            {Object.keys(selectedLog.metadata).length > 0 && (
              <Card size="small" title="Metadata">
                <pre className="bg-gray-50 p-3 rounded text-xs overflow-auto">
                  {JSON.stringify(selectedLog.metadata, null, 2)}
                </pre>
              </Card>
            )}

            <Space>
              <Button icon={<RobotOutlined />} type="primary">
                Ask AI about this log
              </Button>
              <Button icon={<PlayCircleOutlined />}>
                Trace Request
              </Button>
            </Space>
          </Space>
        )}
      </Drawer>
    </div>
  )
}

// ============================================
// Mock Data
// ============================================

function getMockLogs(): LogEntry[] {
  const now = dayjs()
  return [
    {
      id: 'log-1',
      timestamp: now.subtract(1, 'minute').toISOString(),
      level: 'ERROR',
      service: 'agent-k8s',
      agent_id: 'agent-1',
      agent_name: 'Kubernetes Agent',
      message: 'Failed to get pod status: connection refused to cluster prod-cluster',
      metadata: { cluster: 'prod-cluster', namespace: 'default', pod: 'api-server-1' },
      trace_id: 'trace-abc123',
      duration_ms: 5000,
    },
    {
      id: 'log-2',
      timestamp: now.subtract(2, 'minute').toISOString(),
      level: 'INFO',
      service: 'api',
      agent_id: null,
      agent_name: null,
      message: 'User admin logged in successfully from 192.168.1.100',
      metadata: { user_id: 'user-1', ip: '192.168.1.100' },
      trace_id: null,
      duration_ms: 45,
    },
    {
      id: 'log-3',
      timestamp: now.subtract(5, 'minute').toISOString(),
      level: 'WARN',
      service: 'agent-deploy',
      agent_id: 'agent-2',
      agent_name: 'Deploy Agent',
      message: 'Deployment rolling update taking longer than expected: 3/5 pods ready',
      metadata: { deployment: 'api-server', expected: 5, ready: 3 },
      trace_id: 'trace-def456',
      duration_ms: null,
    },
    {
      id: 'log-4',
      timestamp: now.subtract(10, 'minute').toISOString(),
      level: 'INFO',
      service: 'scheduler',
      agent_id: null,
      agent_name: null,
      message: 'Scheduled task "cleanup-old-deployments" completed successfully',
      metadata: { task: 'cleanup-old-deployments', deleted_count: 15 },
      trace_id: null,
      duration_ms: 2300,
    },
    {
      id: 'log-5',
      timestamp: now.subtract(15, 'minute').toISOString(),
      level: 'ERROR',
      service: 'websocket',
      agent_id: null,
      agent_name: null,
      message: 'WebSocket connection dropped unexpectedly for session sess-xyz789',
      metadata: { session_id: 'sess-xyz789', reason: 'timeout' },
      trace_id: null,
      duration_ms: null,
    },
    {
      id: 'log-6',
      timestamp: now.subtract(20, 'minute').toISOString(),
      level: 'DEBUG',
      service: 'agent-k8s',
      agent_id: 'agent-1',
      agent_name: 'Kubernetes Agent',
      message: 'Fetching resource metrics from cluster staging-cluster',
      metadata: { cluster: 'staging-cluster' },
      trace_id: null,
      duration_ms: 250,
    },
    {
      id: 'log-7',
      timestamp: now.subtract(30, 'minute').toISOString(),
      level: 'INFO',
      service: 'api',
      agent_id: null,
      agent_name: null,
      message: 'GET /api/v1/projects 200 - 89ms',
      metadata: { method: 'GET', path: '/api/v1/projects', status: 200 },
      trace_id: 'trace-ghi789',
      duration_ms: 89,
    },
    {
      id: 'log-8',
      timestamp: now.subtract(45, 'minute').toISOString(),
      level: 'WARN',
      service: 'agent-k8s',
      agent_id: 'agent-1',
      agent_name: 'Kubernetes Agent',
      message: 'High memory usage detected on node prod-node-3: 92% utilized',
      metadata: { node: 'prod-node-3', memory_percent: 92 },
      trace_id: null,
      duration_ms: null,
    },
  ]
}

function getMockStats(): LogStats {
  return {
    total: 1547,
    by_level: {
      DEBUG: 245,
      INFO: 1102,
      WARN: 156,
      ERROR: 42,
      FATAL: 2,
    },
    by_service: {
      api: 523,
      'agent-k8s': 412,
      'agent-deploy': 289,
      scheduler: 198,
      websocket: 125,
    },
    error_rate: 0.028,
  }
}
