import { useState } from 'react'
import { Card, Tree, Table, Tag, Input, Select, Space, Typography, Button, Modal, Descriptions, Progress, Alert, Tooltip, message } from 'antd'
import {
  SearchOutlined,
  FolderOutlined,
  ClusterOutlined,
  CloudOutlined,
  ReloadOutlined,
  BugOutlined,
  SafetyOutlined,
  DashboardOutlined,
  InfoCircleOutlined,
  ToolOutlined,
  LinkOutlined,
  RocketOutlined,
} from '@ant-design/icons'
import type { DataNode } from 'antd/es/tree'
import ResourceChatPanel from '../components/ResourceChatPanel'
import type { AnalyzedResource } from '../components/ResourceChatPanel'
import { useAuthStore } from '../stores/authStore'
import { useProjectStore } from '../stores/projectStore'
import PageContainer from '../components/layout/PageContainer'

const { Text } = Typography
const { Search } = Input

// Mock data for resources
const mockRegions = [
  { id: 'us-east', name: 'US East', code: 'us-east-1' },
  { id: 'us-west', name: 'US West', code: 'us-west-2' },
  { id: 'eu-west', name: 'EU West', code: 'eu-west-1' },
  { id: 'apac', name: 'Asia Pacific', code: 'ap-southeast-1' },
]

const mockClusters = [
  { id: 'cluster-1', name: 'Production Cluster', regionId: 'us-east', status: 'active', provider: 'aws' },
  { id: 'cluster-2', name: 'Development Cluster', regionId: 'us-east', status: 'active', provider: 'aws' },
  { id: 'cluster-3', name: 'EU Production', regionId: 'eu-west', status: 'active', provider: 'gcp' },
]

const mockServices = [
  { id: 'svc-1', name: 'api-gateway', projectId: 'pipecat-app-a', namespace: 'production', cluster: 'Production Cluster', replicas: 3, status: 'running', cpu: 450, cpuLimit: 500, memory: 920, memoryLimit: 1024, restarts: 0, insight: 'Memory at 90%', codename: 'Phoenix', versionId: 'ver-2' },
  { id: 'svc-2', name: 'chat-gateway', projectId: 'chat-platform', namespace: 'production', cluster: 'Production Cluster', replicas: 2, status: 'running', cpu: 200, cpuLimit: 500, memory: 256, memoryLimit: 512, restarts: 0, insight: 'Healthy', codename: 'Aurora', versionId: 'ver-6' },
  { id: 'svc-3', name: 'auth-service', projectId: 'pipecat-app-a', namespace: 'production', cluster: 'Production Cluster', replicas: 2, status: 'running', cpu: 100, cpuLimit: 200, memory: 128, memoryLimit: 256, restarts: 0, insight: 'Healthy', codename: 'Legacy', versionId: 'ver-1' },
  { id: 'svc-4', name: 'grafana', projectId: 'infra-core', namespace: 'monitoring', cluster: 'Production Cluster', replicas: 1, status: 'running', cpu: 50, cpuLimit: 200, memory: 128, memoryLimit: 256, restarts: 0, insight: 'Healthy', codename: '-', versionId: null },
  { id: 'svc-5', name: 'prometheus', projectId: 'infra-core', namespace: 'monitoring', cluster: 'Production Cluster', replicas: 1, status: 'running', cpu: 200, cpuLimit: 500, memory: 512, memoryLimit: 1024, restarts: 0, insight: 'Healthy', codename: '-', versionId: null },
  { id: 'svc-6', name: 'test-api', projectId: 'pipecat-app-a', namespace: 'default', cluster: 'Development Cluster', replicas: 1, status: 'error', cpu: 0, cpuLimit: 200, memory: 0, memoryLimit: 256, restarts: 15, insight: 'CrashLoopBackOff', codename: 'Test', versionId: 'ver-test' },
  { id: 'svc-7', name: 'worker', projectId: 'pipecat-app-a', namespace: 'production', cluster: 'Production Cluster', replicas: 2, status: 'running', cpu: 850, cpuLimit: 1000, memory: 890, memoryLimit: 1024, restarts: 3, insight: 'OOM risk', codename: 'Titan', versionId: 'ver-3' },
]

export default function Resources() {
  const { user } = useAuthStore()
  const { globalSelectedProjectId } = useProjectStore()
  const [selectedCluster, setSelectedCluster] = useState<string | null>(null)
  const [searchText, setSearchText] = useState('')
  const [selectedResource, setSelectedResource] = useState<AnalyzedResource | null>(null)
  const [detailModalOpen, setDetailModalOpen] = useState(false)
  const [viewMode, setViewMode] = useState<'split' | 'chat' | 'table'>('split')

  // Build tree data
  const treeData: DataNode[] = mockRegions.map((region) => ({
    title: (
      <span>
        <CloudOutlined className="mr-2" />
        {region.name}
      </span>
    ),
    key: region.id,
    icon: <FolderOutlined />,
    children: mockClusters
      .filter((c) => c.regionId === region.id)
      .map((cluster) => ({
        title: (
          <span>
            <ClusterOutlined className="mr-2" />
            {cluster.name}
            <Tag color={cluster.status === 'active' ? 'green' : 'default'} className="ml-2">
              {cluster.status}
            </Tag>
          </span>
        ),
        key: cluster.id,
        isLeaf: false,
      })),
  }))

  const filteredServices = mockServices.filter((service) => {
    // Project Level Permissions
    const hasProjectPermission = user?.role === 'admin' || user?.allowedProjects?.includes(service.projectId)
    if (!hasProjectPermission) return false
    
    // Global Project Selection
    if (globalSelectedProjectId !== 'all' && service.projectId !== globalSelectedProjectId) return false

    const matchesSearch =
      service.name.toLowerCase().includes(searchText.toLowerCase()) ||
      service.namespace.toLowerCase().includes(searchText.toLowerCase())
    const matchesCluster = !selectedCluster || service.cluster.includes(selectedCluster.split('-')[1] === '1' ? 'Production' : 'Development')
    return matchesSearch && matchesCluster
  })

  const handleResourceSelect = (resource: AnalyzedResource) => {
    setSelectedResource(resource)
    setDetailModalOpen(true)
  }

  const handleActionExecute = (action: string) => {
    console.log('Executing action:', action)
    // Handle different action types
    if (action.startsWith('fix:')) {
      const target = action.replace('fix:', '')
      Modal.confirm({
        title: 'Apply Fix',
        icon: <SafetyOutlined />,
        content: (
          <div className="space-y-2">
            <p>This will apply the recommended fix for <strong>{target}</strong>.</p>
            <Alert
              message="Recommended Fix"
              description={
                <div className="text-xs">
                  <p><strong>Fix Type:</strong> Configuration Update</p>
                  <p><strong>Impact:</strong> Pod will be restarted</p>
                </div>
              }
              type="info"
              className="mt-2"
            />
          </div>
        ),
        okText: 'Apply Fix',
        onOk: () => {
          message.loading({ content: `Applying fix for ${target}...`, key: 'fix' })
          setTimeout(() => {
            message.success({ content: `Fix applied successfully for ${target}`, key: 'fix' })
          }, 2000)
        },
      })
    } else if (action.startsWith('scale:')) {
      const target = action.replace('scale:', '')
      Modal.confirm({
        title: 'Scale Resource',
        icon: <DashboardOutlined />,
        content: (
          <div className="space-y-2">
            <p>Scale <strong>{target}</strong> horizontally to distribute load.</p>
            <Select
              defaultValue={3}
              style={{ width: '100%' }}
              options={[
                { value: 2, label: '2 replicas' },
                { value: 3, label: '3 replicas' },
                { value: 5, label: '5 replicas' },
              ]}
            />
          </div>
        ),
        okText: 'Scale',
        onOk: () => {
          message.loading({ content: `Scaling ${target}...`, key: 'scale' })
          setTimeout(() => {
            message.success({ content: `${target} scaled successfully`, key: 'scale' })
          }, 1500)
        },
      })
    } else {
      Modal.info({
        title: 'Action Triggered',
        content: `Action "${action}" would be executed here. In production, this would apply fixes or navigate to detailed views.`,
      })
    }
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      running: 'green',
      stopped: 'default',
      error: 'red',
    }
    return colors[status] || 'default'
  }

  const getInsightColor = (insight: string) => {
    if (insight.includes('OOM') || insight.includes('CrashLoop')) return 'red'
    if (insight.includes('90%') || insight.includes('risk')) return 'orange'
    return 'green'
  }

  const columns = [
    {
      title: 'Service',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: typeof mockServices[0]) => (
        <Space direction="vertical" size={0}>
          <span className="font-medium">{name}</span>
          {record.codename && record.codename !== '-' && (
            <Tooltip title={`Version: ${record.codename}`}>
              <Tag color="purple" className="text-xs cursor-pointer" onClick={() => window.location.href = `/projects?version=${record.versionId}`}>
                <RocketOutlined className="mr-1" />
                {record.codename}
              </Tag>
            </Tooltip>
          )}
        </Space>
      ),
    },
    {
      title: 'Namespace',
      dataIndex: 'namespace',
      key: 'namespace',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>{status.toUpperCase()}</Tag>
      ),
    },
    {
      title: 'CPU',
      key: 'cpu',
      render: (_: unknown, record: typeof mockServices[0]) => (
        <div className="w-24">
          <Progress
            percent={Math.round((record.cpu / record.cpuLimit) * 100)}
            size="small"
            strokeColor={record.cpu / record.cpuLimit > 0.8 ? '#ef4444' : '#3b82f6'}
            format={() => `${record.cpu}m`}
          />
        </div>
      ),
    },
    {
      title: 'Memory',
      key: 'memory',
      render: (_: unknown, record: typeof mockServices[0]) => (
        <div className="w-24">
          <Progress
            percent={Math.round((record.memory / record.memoryLimit) * 100)}
            size="small"
            strokeColor={record.memory / record.memoryLimit > 0.8 ? '#ef4444' : '#22c55e'}
            format={() => `${record.memory}Mi`}
          />
        </div>
      ),
    },
    {
      title: 'Restarts',
      dataIndex: 'restarts',
      key: 'restarts',
      render: (restarts: number) => (
        <Tag color={restarts > 5 ? 'red' : restarts > 0 ? 'orange' : 'green'}>
          {restarts}
        </Tag>
      ),
    },
    {
      title: 'AI Insight',
      dataIndex: 'insight',
      key: 'insight',
      render: (insight: string) => (
        <Tag color={getInsightColor(insight)}>
          <InfoCircleOutlined className="mr-1" />
          {insight}
        </Tag>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 150,
      render: (_: unknown, record: typeof mockServices[0]) => (
        <Space size={2}>
          <Tooltip title="K8sGPT Diagnose">
            <Button
              type="link"
              size="small"
              icon={<ToolOutlined style={{ color: '#8b5cf6' }} />}
              onClick={() => {
                setViewMode('chat')
                // Trigger diagnosis in chat panel
              }}
            />
          </Tooltip>
          <Button type="link" size="small" icon={<BugOutlined />}>
            Debug
          </Button>
          <Button type="link" size="small" icon={<DashboardOutlined />}>
            Metrics
          </Button>
          {record.versionId && (
            <Tooltip title="Go to Version">
              <Button
                type="link"
                size="small"
                icon={<LinkOutlined />}
                href={`/projects?version=${record.versionId}`}
              />
            </Tooltip>
          )}
        </Space>
      ),
    },
  ]

  return (
    <PageContainer
      title="Resources"
      icon={<ClusterOutlined />}
      transparent
      fullHeight={viewMode !== 'table'}
      extra={
        <Space>
          <Select
            value={viewMode}
            onChange={setViewMode}
            style={{ width: 150 }}
            options={[
              { value: 'split', label: 'Split View' },
              { value: 'chat', label: 'Chat Focus' },
              { value: 'table', label: 'Table View' },
            ]}
          />
          <Button icon={<ReloadOutlined />}>Refresh</Button>
        </Space>
      }
    >
      <div className="space-y-4">
        {/* AI Insight Banner */}
      <Alert
        message={
          <div className="flex items-center gap-2">
            <BugOutlined />
            <span>
              <strong>AI Detected:</strong> 2 pods with potential issues in production namespace.
              <Button type="link" size="small" onClick={() => setViewMode('chat')}>
                View Analysis →
              </Button>
            </span>
          </div>
        }
        type="warning"
        showIcon={false}
        className="bg-orange-50 border-orange-200"
      />

      {/* Main Content */}
      {viewMode === 'split' && (
        <div className="grid grid-cols-12 gap-4">
          {/* Left Panel - Resource Tree & Quick Actions */}
          <div className="col-span-3 space-y-4">
            <Card title="Clusters" size="small" className="h-64 overflow-auto">
              <Tree
                showIcon
                treeData={treeData}
                onSelect={(keys) => {
                  const key = keys[0] as string
                  if (key?.startsWith('cluster')) {
                    setSelectedCluster(key)
                  }
                }}
                defaultExpandAll
              />
            </Card>

            <Card title="Quick Actions" size="small">
              <Space direction="vertical" className="w-full">
                <Button block icon={<BugOutlined />} type="dashed">
                  Debug Failing Pods
                </Button>
                <Button block icon={<SafetyOutlined />} type="dashed">
                  Security Scan
                </Button>
                <Button block icon={<DashboardOutlined />} type="dashed">
                  Resource Audit
                </Button>
              </Space>
            </Card>

            {/* Cluster Stats */}
            <Card title="Cluster Health" size="small">
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <Text>CPU Allocation</Text>
                    <Text strong>72%</Text>
                  </div>
                  <Progress percent={72} size="small" showInfo={false} />
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <Text>Memory Allocation</Text>
                    <Text strong>85%</Text>
                  </div>
                  <Progress percent={85} size="small" strokeColor="#eab308" showInfo={false} />
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <Text>Pod Density</Text>
                    <Text strong>45/100</Text>
                  </div>
                  <Progress percent={45} size="small" strokeColor="#3b82f6" showInfo={false} />
                </div>
              </div>
            </Card>
          </div>

          {/* Middle Panel - Resource Table */}
          <div className="col-span-5">
            <Card
              title="Workloads"
              extra={
                <Search
                  placeholder="Search..."
                  allowClear
                  style={{ width: 200 }}
                  prefix={<SearchOutlined />}
                  onChange={(e) => setSearchText(e.target.value)}
                />
              }
            >
              <Table
                dataSource={filteredServices}
                columns={columns}
                rowKey="id"
                size="small"
                pagination={{ pageSize: 10 }}
                scroll={{ x: 900 }}
              />
            </Card>
          </div>

          {/* Right Panel - K8sGPT Chat */}
          <div className="col-span-4">
            <ResourceChatPanel
              onResourceSelect={handleResourceSelect}
              onActionExecute={handleActionExecute}
            />
          </div>
        </div>
      )}

      {viewMode === 'chat' && (
        <div className="grid grid-cols-12 gap-4">
          <div className="col-span-3">
            <Card title="Clusters" size="small" className="mb-4">
              <Tree
                showIcon
                treeData={treeData}
                onSelect={(keys) => {
                  const key = keys[0] as string
                  if (key?.startsWith('cluster')) {
                    setSelectedCluster(key)
                  }
                }}
                defaultExpandAll
              />
            </Card>
          </div>
          <div className="col-span-9">
            <ResourceChatPanel
              onResourceSelect={handleResourceSelect}
              onActionExecute={handleActionExecute}
            />
          </div>
        </div>
      )}

      {viewMode === 'table' && (
        <div className="grid grid-cols-12 gap-4">
          <div className="col-span-2">
            <Card title="Clusters" size="small">
              <Tree
                showIcon
                treeData={treeData}
                onSelect={(keys) => {
                  const key = keys[0] as string
                  if (key?.startsWith('cluster')) {
                    setSelectedCluster(key)
                  }
                }}
                defaultExpandAll
              />
            </Card>
          </div>
          <div className="col-span-10">
            <Card
              title="All Workloads"
              extra={
                <Space>
                  <Select
                    placeholder="Filter by status"
                    allowClear
                    style={{ width: 150 }}
                    options={[
                      { value: 'running', label: 'Running' },
                      { value: 'stopped', label: 'Stopped' },
                      { value: 'error', label: 'Error' },
                    ]}
                  />
                  <Search
                    placeholder="Search services..."
                    allowClear
                    style={{ width: 250 }}
                    prefix={<SearchOutlined />}
                    onChange={(e) => setSearchText(e.target.value)}
                  />
                </Space>
              }
            >
              <Table
                dataSource={filteredServices}
                columns={columns}
                rowKey="id"
                pagination={{ pageSize: 15 }}
                scroll={{ x: 1000 }}
              />
            </Card>
          </div>
        </div>
      )}

      {/* Resource Detail Modal */}
      <Modal
        title={selectedResource?.name}
        open={detailModalOpen}
        onCancel={() => setDetailModalOpen(false)}
        footer={null}
        width={700}
      >
        {selectedResource && (
          <div className="space-y-4">
            <Descriptions bordered column={2}>
              <Descriptions.Item label="Name">{selectedResource.name}</Descriptions.Item>
              <Descriptions.Item label="Namespace">{selectedResource.namespace}</Descriptions.Item>
              <Descriptions.Item label="Cluster">{selectedResource.cluster}</Descriptions.Item>
              <Descriptions.Item label="Status">
                <Tag color={selectedResource.status === 'healthy' ? 'green' : selectedResource.status === 'warning' ? 'orange' : 'red'}>
                  {selectedResource.status.toUpperCase()}
                </Tag>
              </Descriptions.Item>
            </Descriptions>

            <Card title="AI Insight" size="small">
              <Alert
                message={selectedResource.insight}
                type={selectedResource.status === 'critical' ? 'error' : 'warning'}
                showIcon
              />
            </Card>

            <Card title="Metrics" size="small">
              <div className="grid grid-cols-2 gap-4">
                {Object.entries(selectedResource.metrics).map(([key, value]) => (
                  <div key={key}>
                    <Text type="secondary" className="text-xs">{key}</Text>
                    <div className="text-lg font-medium">{value}</div>
                  </div>
                ))}
              </div>
            </Card>

            <Space>
              <Button type="primary">View Logs</Button>
              <Button>View YAML</Button>
              <Button danger>Delete Pod</Button>
            </Space>
          </div>
        )}
      </Modal>
      </div>
    </PageContainer>
  )
}
