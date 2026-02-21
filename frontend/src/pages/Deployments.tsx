import { useState } from 'react'
import {
  Card,
  Table,
  Tag,
  Steps,
  Typography,
  Timeline,
  Button,
  Badge,
  Modal,
  Descriptions,
  Space,
  Tooltip,
  message,
  Popconfirm,
  Alert,
  Divider,
} from 'antd'
import {
  CheckCircleOutlined,
  SyncOutlined,
  ClockCircleOutlined,
  GithubOutlined,
  RocketOutlined,
  ExclamationCircleOutlined,
  RollbackOutlined,
  RedoOutlined,
  LinkOutlined,
  GlobalOutlined,
  EyeOutlined,
  WarningOutlined,
  LoadingOutlined,
  UserOutlined,
} from '@ant-design/icons'
import PageContainer from '../components/layout/PageContainer'

const { Text } = Typography

// 部署链步骤类型
interface DeploymentChainStep {
  id: string
  name: string
  status: 'pending' | 'running' | 'success' | 'failed'
  startTime?: string
  endTime?: string
  duration?: string
  message?: string
  details?: {
    [key: string]: string
  }
}

// Mock 部署链数据
const mockDeploymentChains: Record<string, DeploymentChainStep[]> = {
  'dep-1': [
    {
      id: 'git',
      name: 'Git Commit',
      status: 'success',
      startTime: '2024-01-15 14:00:00',
      endTime: '2024-01-15 14:00:01',
      duration: '1s',
      details: {
        commit: 'a1b2c3d',
        branch: 'main',
        message: 'feat: add new API endpoint',
        author: 'John Doe',
      },
    },
    {
      id: 'build',
      name: 'CI/CD Build',
      status: 'success',
      startTime: '2024-01-15 14:00:30',
      endTime: '2024-01-15 14:03:00',
      duration: '2m 30s',
      details: {
        job: 'api-gateway-build',
        stage: 'Build & Test',
        runner: 'jenkins-agent-01',
      },
    },
    {
      id: 'image',
      name: 'Image Push',
      status: 'success',
      startTime: '2024-01-15 14:03:00',
      endTime: '2024-01-15 14:03:30',
      duration: '30s',
      details: {
        image: 'harbor.local/api-gateway:v1.2.3',
        size: '120MB',
        vulnerabilities: '0',
      },
    },
    {
      id: 'argocd',
      name: 'ArgoCD Sync',
      status: 'success',
      startTime: '2024-01-15 14:03:30',
      endTime: '2024-01-15 14:05:00',
      duration: '1m 30s',
      details: {
        app: 'api-gateway-prod',
        revision: '42',
        syncStatus: 'Synced',
      },
    },
    {
      id: 'health',
      name: 'Health Check',
      status: 'success',
      startTime: '2024-01-15 14:05:00',
      endTime: '2024-01-15 14:05:30',
      duration: '30s',
      details: {
        checks: 'Liveness, Readiness, Startup',
        result: 'All Passed',
        pods: '3/3 Ready',
      },
    },
  ],
  'dep-2': [
    {
      id: 'git',
      name: 'Git Commit',
      status: 'success',
      startTime: '2024-01-15 13:00:00',
      duration: '1s',
      details: {
        commit: 'e4f5g6h',
        branch: 'main',
        message: 'fix: update config',
        author: 'Jane Smith',
      },
    },
    {
      id: 'build',
      name: 'CI/CD Build',
      status: 'success',
      startTime: '2024-01-15 13:00:30',
      endTime: '2024-01-15 13:03:00',
      duration: '2m 30s',
      details: {
        job: 'chat-gateway-build',
        stage: 'Build & Test',
        runner: 'jenkins-agent-02',
      },
    },
    {
      id: 'image',
      name: 'Image Push',
      status: 'success',
      startTime: '2024-01-15 13:03:00',
      endTime: '2024-01-15 13:03:30',
      duration: '30s',
      details: {
        image: 'harbor.local/chat-gateway:v2.0.1',
        size: '95MB',
        vulnerabilities: '2 (low)',
      },
    },
    {
      id: 'argocd',
      name: 'ArgoCD Sync',
      status: 'running',
      startTime: '2024-01-15 13:03:30',
      details: {
        app: 'chat-gateway-prod',
        revision: '15',
        syncStatus: 'Syncing...',
      },
      message: 'Applying manifests to cluster...',
    },
    {
      id: 'health',
      name: 'Health Check',
      status: 'pending',
      message: 'Waiting for ArgoCD sync to complete',
    },
  ],
  'dep-3': [
    {
      id: 'git',
      name: 'Git Commit',
      status: 'success',
      startTime: '2024-01-15 10:00:00',
      duration: '1s',
      details: {
        commit: 'i7j8k9l',
        branch: 'release/1.1',
        message: 'release: v1.1.0',
        author: 'Bob Wilson',
      },
    },
    {
      id: 'build',
      name: 'CI/CD Build',
      status: 'success',
      startTime: '2024-01-15 10:00:30',
      endTime: '2024-01-15 10:02:30',
      duration: '2m',
      details: {
        job: 'auth-service-build',
        stage: 'Build & Test',
        runner: 'jenkins-agent-01',
      },
    },
    {
      id: 'image',
      name: 'Image Push',
      status: 'success',
      startTime: '2024-01-15 10:02:30',
      endTime: '2024-01-15 10:03:00',
      duration: '30s',
      details: {
        image: 'harbor.local/auth-service:v1.1.0',
        size: '80MB',
        vulnerabilities: '0',
      },
    },
    {
      id: 'argocd',
      name: 'ArgoCD Sync',
      status: 'failed',
      startTime: '2024-01-15 10:03:00',
      endTime: '2024-01-15 10:04:00',
      duration: '1m',
      details: {
        app: 'auth-service-prod',
        revision: '8',
        syncStatus: 'Failed',
      },
      message: 'Error: deployment.apps "auth-service" exceeded progress deadline',
    },
    {
      id: 'health',
      name: 'Health Check',
      status: 'pending',
      message: 'Skipped due to sync failure',
    },
  ],
}

// Mock 部署数据 - 使用 deploymentStore
const mockDeployments = [
  {
    id: 'dep-1',
    service: 'api-gateway',
    codename: 'Phoenix',
    version: 'v1.2.3-rc3',
    commit: 'a1b2c3d',
    branch: 'main',
    region: 'US East',
    status: 'success',
    syncStatus: 'synced',
    healthStatus: 'healthy',
    deployedAt: '2024-01-15 14:30:00',
    deployedBy: 'John Doe',
    argocdApp: 'api-gateway-prod',
    argocdUrl: 'https://argocd.example.com/applications/api-gateway-prod',
  },
  {
    id: 'dep-2',
    service: 'chat-gateway',
    codename: 'Aurora',
    version: 'v2.0.1-beta1',
    commit: 'e4f5g6h',
    branch: 'main',
    region: 'US East',
    status: 'running',
    syncStatus: 'out-of-sync',
    healthStatus: 'progressing',
    deployedAt: '2024-01-15 13:00:00',
    deployedBy: 'Jane Smith',
    argocdApp: 'chat-gateway-prod',
    argocdUrl: 'https://argocd.example.com/applications/chat-gateway-prod',
  },
  {
    id: 'dep-3',
    service: 'auth-service',
    codename: 'Legacy',
    version: 'v1.1.0',
    commit: 'i7j8k9l',
    branch: 'release/1.1',
    region: 'EU West',
    status: 'failed',
    syncStatus: 'unknown',
    healthStatus: 'degraded',
    deployedAt: '2024-01-15 10:00:00',
    deployedBy: 'Bob Wilson',
    argocdApp: 'auth-service-prod',
    argocdUrl: 'https://argocd.example.com/applications/auth-service-prod',
  },
  {
    id: 'dep-4',
    service: 'worker',
    codename: 'Titan',
    version: 'v1.2.4-beta2',
    commit: 'g7h8i9j',
    branch: 'feature/titan-translation',
    region: 'US East',
    status: 'success',
    syncStatus: 'synced',
    healthStatus: 'healthy',
    deployedAt: '2024-01-14 15:00:00',
    deployedBy: 'Bob Wilson',
    argocdApp: 'worker-prod',
    argocdUrl: 'https://argocd.example.com/applications/worker-prod',
  },
]

export default function Deployments() {
  const [selectedDeployment, setSelectedDeployment] = useState<string | null>(null)
  const [chainModalOpen, setChainModalOpen] = useState(false)
  const [selectedDeploymentData, setSelectedDeploymentData] = useState<typeof mockDeployments[0] | null>(null)
  const [syncing, setSyncing] = useState(false)
  const [rollingBack, setRollingBack] = useState(false)

  // 获取部署链
  const getDeploymentChain = (depId: string): DeploymentChainStep[] => {
    return mockDeploymentChains[depId] || mockDeploymentChains['dep-1']
  }

  // 获取当前步骤索引
  const getCurrentStep = (chain: DeploymentChainStep[]): number => {
    const failedIndex = chain.findIndex(s => s.status === 'failed')
    if (failedIndex !== -1) return failedIndex
    const runningIndex = chain.findIndex(s => s.status === 'running')
    if (runningIndex !== -1) return runningIndex
    return chain.filter(s => s.status === 'success').length - 1
  }

  // 强制同步
  const handleForceSync = (deployment: typeof mockDeployments[0]) => {
    setSyncing(true)
    message.loading({ content: `Triggering force sync for ${deployment.argocdApp}...`, key: 'sync' })
    setTimeout(() => {
      setSyncing(false)
      message.success({ content: `Force sync triggered for ${deployment.argocdApp}`, key: 'sync' })
    }, 2000)
  }

  // 快速回滚
  const handleRollback = (deployment: typeof mockDeployments[0]) => {
    setRollingBack(true)
    message.loading({ content: `Rolling back ${deployment.argocdApp} to previous version...`, key: 'rollback' })
    setTimeout(() => {
      setRollingBack(false)
      message.success({ content: `${deployment.argocdApp} rolled back to previous version`, key: 'rollback' })
    }, 2000)
  }

  // 查看部署链详情
  const handleViewChain = (deployment: typeof mockDeployments[0]) => {
    setSelectedDeploymentData(deployment)
    setSelectedDeployment(deployment.id)
    setChainModalOpen(true)
  }

  const columns = [
    {
      title: 'Service',
      dataIndex: 'service',
      key: 'service',
      width: 130,
      render: (name: string, record: typeof mockDeployments[0]) => (
        <Space direction="vertical" size={0}>
          <span className="font-medium">{name}</span>
          <Tag color="purple" className="text-xs">{record.codename}</Tag>
        </Space>
      ),
    },
    {
      title: 'Version',
      dataIndex: 'version',
      key: 'version',
      width: 120,
      render: (version: string) => <Tag color="blue">{version}</Tag>,
    },
    {
      title: 'Git',
      key: 'git',
      width: 140,
      render: (_: unknown, record: typeof mockDeployments[0]) => (
        <Space direction="vertical" size={0}>
          <span className="text-xs">
            <GithubOutlined className="mr-1" />
            {record.branch}
          </span>
          <a href="#" className="text-xs text-gray-500">{record.commit}</a>
        </Space>
      ),
    },
    {
      title: 'Region',
      dataIndex: 'region',
      key: 'region',
      width: 100,
      render: (region: string) => (
        <Tag icon={<GlobalOutlined />} color="geekblue">{region}</Tag>
      ),
    },
    {
      title: 'Sync',
      dataIndex: 'syncStatus',
      key: 'syncStatus',
      width: 100,
      render: (status: string) => {
        const config: Record<string, { color: string; icon: React.ReactNode }> = {
          synced: { color: 'green', icon: <CheckCircleOutlined /> },
          'out-of-sync': { color: 'orange', icon: <SyncOutlined spin /> },
          unknown: { color: 'default', icon: <ClockCircleOutlined /> },
        }
        const { color, icon } = config[status] || config.unknown
        return <Tag color={color} icon={icon}>{status}</Tag>
      },
    },
    {
      title: 'Health',
      dataIndex: 'healthStatus',
      key: 'healthStatus',
      width: 110,
      render: (status: string) => {
        const config: Record<string, { color: 'success' | 'error' | 'processing' | 'warning' | 'default'; text: string }> = {
          healthy: { color: 'success', text: 'Healthy' },
          degraded: { color: 'error', text: 'Degraded' },
          progressing: { color: 'processing', text: 'Progressing' },
          unknown: { color: 'default', text: 'Unknown' },
        }
        const { color, text } = config[status] || config.unknown
        return <Badge status={color} text={text} />
      },
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const config: Record<string, { color: string; icon: React.ReactNode }> = {
          success: { color: 'green', icon: <CheckCircleOutlined /> },
          running: { color: 'blue', icon: <LoadingOutlined /> },
          failed: { color: 'red', icon: <ExclamationCircleOutlined /> },
        }
        const { color, icon } = config[status] || { color: 'default', icon: <ClockCircleOutlined /> }
        return <Tag color={color} icon={icon}>{status.toUpperCase()}</Tag>
      },
    },
    {
      title: 'Deployed',
      dataIndex: 'deployedAt',
      key: 'deployedAt',
      width: 130,
    },
    {
      title: 'By',
      dataIndex: 'deployedBy',
      key: 'deployedBy',
      width: 100,
      render: (by: string) => (
        <Space>
          <UserOutlined />
          <span>{by}</span>
        </Space>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 200,
      fixed: 'right' as const,
      render: (_: unknown, record: typeof mockDeployments[0]) => (
        <Space size={2}>
          <Tooltip title="View Chain">
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleViewChain(record)}
            />
          </Tooltip>
          <Tooltip title="ArgoCD">
            <Button
              type="link"
              size="small"
              icon={<LinkOutlined />}
              href={record.argocdUrl}
              target="_blank"
            />
          </Tooltip>
          <Popconfirm
            title="Force sync this application?"
            description="This will trigger an immediate sync in ArgoCD"
            onConfirm={() => handleForceSync(record)}
          >
            <Tooltip title="Force Sync">
              <Button
                type="link"
                size="small"
                icon={<RedoOutlined />}
                loading={syncing}
              />
            </Tooltip>
          </Popconfirm>
          <Popconfirm
            title="Rollback to previous version?"
            description="This will revert to the last successful deployment"
            onConfirm={() => handleRollback(record)}
          >
            <Tooltip title="Rollback">
              <Button
                type="link"
                size="small"
                danger
                icon={<RollbackOutlined />}
                loading={rollingBack}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  // 渲染部署链步骤
  const renderChainSteps = (chain: DeploymentChainStep[]) => {
    const currentStep = getCurrentStep(chain)
    const failedStep = chain.find(s => s.status === 'failed')

    return (
      <div className="space-y-4">
        {/* 失败警告 */}
        {failedStep && (
          <Alert
            message="Deployment Failed"
            description={failedStep.message}
            type="error"
            showIcon
            icon={<ExclamationCircleOutlined />}
            className="mb-4"
          />
        )}

        {/* 部署链 Steps */}
        <Steps
          current={currentStep}
          status={failedStep ? 'error' : 'process'}
          items={chain.map((step) => ({
            title: step.name,
            status: step.status === 'failed' ? 'error' :
                    step.status === 'running' ? 'process' :
                    step.status === 'success' ? 'finish' : 'wait',
            icon: step.status === 'running' ? <LoadingOutlined /> :
                  step.status === 'failed' ? <ExclamationCircleOutlined /> :
                  step.status === 'success' ? <CheckCircleOutlined /> : <ClockCircleOutlined />,
            description: (
              <div className="text-xs">
                {step.duration && <div>Duration: {step.duration}</div>}
                {step.status === 'running' && step.message && (
                  <div className="text-blue-500">{step.message}</div>
                )}
                {step.status === 'failed' && step.message && (
                  <div className="text-red-500">{step.message}</div>
                )}
              </div>
            ),
          }))}
        />

        {/* 详细时间线 */}
        <Divider>Timeline</Divider>
        <Timeline
          items={chain.map((step) => ({
            color: step.status === 'success' ? 'green' :
                   step.status === 'failed' ? 'red' :
                   step.status === 'running' ? 'blue' : 'gray',
            children: (
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{step.name}</span>
                  <Tag
                    color={step.status === 'success' ? 'green' :
                           step.status === 'failed' ? 'red' :
                           step.status === 'running' ? 'blue' : 'default'}
                  >
                    {step.status}
                  </Tag>
                  {step.duration && <Text type="secondary" className="text-xs">({step.duration})</Text>}
                </div>
                {step.startTime && (
                  <Text type="secondary" className="text-xs">{step.startTime}</Text>
                )}
                {step.details && (
                  <div className="mt-2 p-2 bg-gray-50 rounded text-xs space-y-1">
                    {Object.entries(step.details).map(([key, value]) => (
                      <div key={key} className="flex gap-2">
                        <span className="text-gray-500 w-24">{key}:</span>
                        <span>{value}</span>
                      </div>
                    ))}
                  </div>
                )}
                {step.message && step.status !== 'success' && (
                  <div className={`mt-1 text-xs ${step.status === 'failed' ? 'text-red-500' : 'text-blue-500'}`}>
                    {step.message}
                  </div>
                )}
              </div>
            ),
          }))}
        />

        {/* 快速操作 */}
        <Divider>Quick Actions</Divider>
        <Space>
          <Button
            icon={<RedoOutlined />}
            onClick={() => selectedDeploymentData && handleForceSync(selectedDeploymentData)}
          >
            Force Sync
          </Button>
          <Button
            danger
            icon={<RollbackOutlined />}
            onClick={() => selectedDeploymentData && handleRollback(selectedDeploymentData)}
          >
            Rollback
          </Button>
          {selectedDeploymentData && (
            <Button
              icon={<LinkOutlined />}
              href={selectedDeploymentData.argocdUrl}
              target="_blank"
            >
              Open ArgoCD
            </Button>
          )}
        </Space>
      </div>
    )
  }

  return (
    <PageContainer
      title="Deployments"
      transparent
      extra={
        <Space>
          <Button icon={<SyncOutlined />}>Refresh</Button>
        </Space>
      }
    >
      <div className="space-y-6">
        {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4">
        <Card size="small">
          <div className="flex items-center gap-2">
            <CheckCircleOutlined className="text-green-500 text-xl" />
            <div>
              <div className="text-2xl font-bold">
                {mockDeployments.filter(d => d.status === 'success').length}
              </div>
              <div className="text-xs text-gray-500">Successful</div>
            </div>
          </div>
        </Card>
        <Card size="small">
          <div className="flex items-center gap-2">
            <LoadingOutlined className="text-blue-500 text-xl" />
            <div>
              <div className="text-2xl font-bold">
                {mockDeployments.filter(d => d.status === 'running').length}
              </div>
              <div className="text-xs text-gray-500">In Progress</div>
            </div>
          </div>
        </Card>
        <Card size="small">
          <div className="flex items-center gap-2">
            <ExclamationCircleOutlined className="text-red-500 text-xl" />
            <div>
              <div className="text-2xl font-bold">
                {mockDeployments.filter(d => d.status === 'failed').length}
              </div>
              <div className="text-xs text-gray-500">Failed</div>
            </div>
          </div>
        </Card>
        <Card size="small">
          <div className="flex items-center gap-2">
            <WarningOutlined className="text-orange-500 text-xl" />
            <div>
              <div className="text-2xl font-bold">
                {mockDeployments.filter(d => d.syncStatus === 'out-of-sync').length}
              </div>
              <div className="text-xs text-gray-500">Out of Sync</div>
            </div>
          </div>
        </Card>
      </div>

      {/* Deployments Table */}
      <Card title="Recent Deployments">
        <Table
          dataSource={mockDeployments}
          columns={columns}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          scroll={{ x: 1400 }}
          rowClassName={(record) => record.status === 'failed' ? 'bg-red-50' : ''}
        />
      </Card>

      {/* Deployment Chain Modal */}
      <Modal
        title={
          <Space>
            <RocketOutlined />
            <span>Deployment Chain</span>
            {selectedDeploymentData && (
              <Tag color="blue">{selectedDeploymentData.service}</Tag>
            )}
          </Space>
        }
        open={chainModalOpen}
        onCancel={() => {
          setChainModalOpen(false)
          setSelectedDeployment(null)
          setSelectedDeploymentData(null)
        }}
        footer={null}
        width={800}
      >
        {selectedDeployment && (
          <>
            {/* 基本信息 */}
            {selectedDeploymentData && (
              <Descriptions bordered column={2} size="small" className="mb-4">
                <Descriptions.Item label="Service">{selectedDeploymentData.service}</Descriptions.Item>
                <Descriptions.Item label="Codename">
                  <Tag color="purple">{selectedDeploymentData.codename}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="Version">{selectedDeploymentData.version}</Descriptions.Item>
                <Descriptions.Item label="Region">
                  <Tag icon={<GlobalOutlined />}>{selectedDeploymentData.region}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="ArgoCD App">
                  <a href={selectedDeploymentData.argocdUrl} target="_blank" rel="noopener noreferrer">
                    {selectedDeploymentData.argocdApp}
                  </a>
                </Descriptions.Item>
                <Descriptions.Item label="Deployed By">
                  <Space><UserOutlined />{selectedDeploymentData.deployedBy}</Space>
                </Descriptions.Item>
              </Descriptions>
            )}

            {/* 部署链 */}
            {renderChainSteps(getDeploymentChain(selectedDeployment))}
          </>
        )}
      </Modal>
      </div>
    </PageContainer>
  )
}
