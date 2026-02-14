import { useState } from 'react'
import { Card, Table, Tag, Steps, Typography, Timeline, Button, Badge } from 'antd'
import {
  CheckCircleOutlined,
  SyncOutlined,
  ClockCircleOutlined,
  GithubOutlined,
  DockerOutlined,
  RocketOutlined,
} from '@ant-design/icons'

const { Title } = Typography

// Mock data
const mockDeployments = [
  {
    id: 'dep-1',
    service: 'api-gateway',
    version: 'v1.2.3',
    commit: 'a1b2c3d',
    branch: 'main',
    status: 'success',
    syncStatus: 'synced',
    healthStatus: 'healthy',
    deployedAt: '2024-01-15 14:30:00',
    deployedBy: 'John Doe',
  },
  {
    id: 'dep-2',
    service: 'chat-gateway',
    version: 'v2.0.1',
    commit: 'e4f5g6h',
    branch: 'main',
    status: 'running',
    syncStatus: 'out-of-sync',
    healthStatus: 'progressing',
    deployedAt: '2024-01-15 13:00:00',
    deployedBy: 'Jane Smith',
  },
  {
    id: 'dep-3',
    service: 'auth-service',
    version: 'v1.1.0',
    commit: 'i7j8k9l',
    branch: 'release/1.1',
    status: 'failed',
    syncStatus: 'unknown',
    healthStatus: 'degraded',
    deployedAt: '2024-01-15 10:00:00',
    deployedBy: 'Bob Wilson',
  },
]

export default function Deployments() {
  const [selectedDeployment, setSelectedDeployment] = useState<string | null>(null)

  const columns = [
    {
      title: 'Service',
      dataIndex: 'service',
      key: 'service',
      render: (name: string) => <span className="font-medium">{name}</span>,
    },
    {
      title: 'Version',
      dataIndex: 'version',
      key: 'version',
      render: (version: string) => <Tag color="blue">{version}</Tag>,
    },
    {
      title: 'Commit',
      dataIndex: 'commit',
      key: 'commit',
      render: (commit: string) => (
        <a href="#" className="text-primary-600">
          <GithubOutlined className="mr-1" />
          {commit}
        </a>
      ),
    },
    {
      title: 'Branch',
      dataIndex: 'branch',
      key: 'branch',
    },
    {
      title: 'Sync',
      dataIndex: 'syncStatus',
      key: 'syncStatus',
      render: (status: string) => {
        const config: Record<string, { color: string; icon: React.ReactNode }> = {
          synced: { color: 'green', icon: <CheckCircleOutlined /> },
          'out-of-sync': { color: 'orange', icon: <SyncOutlined spin /> },
          unknown: { color: 'default', icon: <ClockCircleOutlined /> },
        }
        const { color, icon } = config[status] || config.unknown
        return (
          <Tag color={color} icon={icon}>
            {status}
          </Tag>
        )
      },
    },
    {
      title: 'Health',
      dataIndex: 'healthStatus',
      key: 'healthStatus',
      render: (status: string) => {
        const config: Record<string, { color: string }> = {
          healthy: { color: 'green' },
          degraded: { color: 'red' },
          progressing: { color: 'blue' },
          unknown: { color: 'default' },
        }
        return <Badge status={config[status]?.color as 'success' | 'error' | 'processing' | 'default'} text={status} />
      },
    },
    {
      title: 'Deployed',
      dataIndex: 'deployedAt',
      key: 'deployedAt',
    },
    {
      title: 'By',
      dataIndex: 'deployedBy',
      key: 'deployedBy',
    },
    {
      title: 'Action',
      key: 'action',
      render: (_: unknown, record: typeof mockDeployments[0]) => (
        <Button type="link" onClick={() => setSelectedDeployment(record.id)}>
          View Chain
        </Button>
      ),
    },
  ]

  const deploymentChain = (
    <Card title="Deployment Chain" className="mt-4">
      <Steps
        current={2}
        items={[
          {
            title: 'Code Commit',
            description: (
              <div className="text-sm">
                <div>
                  <GithubOutlined className="mr-1" />
                  Commit: a1b2c3d
                </div>
                <div>Branch: main</div>
                <div>Message: feat: add new endpoint</div>
              </div>
            ),
            icon: <GithubOutlined />,
            status: 'finish',
          },
          {
            title: 'Build',
            description: (
              <div className="text-sm">
                <div>Jenkins Job: api-gateway-build</div>
                <div>Duration: 2m 30s</div>
                <div>Status: Success</div>
              </div>
            ),
            status: 'finish',
          },
          {
            title: 'Image Push',
            description: (
              <div className="text-sm">
                <div>
                  <DockerOutlined className="mr-1" />
                  harbor.local/api-gateway:v1.2.3
                </div>
                <div>Size: 120MB</div>
                <div>Vulnerabilities: 0</div>
              </div>
            ),
            icon: <DockerOutlined />,
            status: 'finish',
          },
          {
            title: 'Deploy',
            description: (
              <div className="text-sm">
                <div>
                  <RocketOutlined className="mr-1" />
                  ArgoCD: api-gateway-prod
                </div>
                <div>Revision: 42</div>
                <div>Status: Synced & Healthy</div>
              </div>
            ),
            icon: <RocketOutlined />,
            status: 'finish',
          },
        ]}
      />

      <Title level={5} className="mt-6 mb-4">Timeline</Title>
      <Timeline
        items={[
          { children: 'Commit pushed to main branch (14:00:00)', color: 'green' },
          { children: 'Jenkins build started (14:00:30)', color: 'blue' },
          { children: 'Build completed successfully (14:03:00)', color: 'green' },
          { children: 'Image pushed to Harbor (14:03:15)', color: 'green' },
          { children: 'ArgoCD sync triggered (14:03:30)', color: 'blue' },
          { children: 'Deployment completed (14:30:00)', color: 'green' },
        ]}
      />
    </Card>
  )

  return (
    <div className="space-y-6">
      <Title level={4}>Deployments</Title>

      <Card title="Recent Deployments">
        <Table
          dataSource={mockDeployments}
          columns={columns}
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {selectedDeployment && deploymentChain}
    </div>
  )
}
