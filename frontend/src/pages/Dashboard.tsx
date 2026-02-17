import { useQuery } from '@tanstack/react-query'
import { Card, Row, Col, Statistic, Progress, Table, Tag, Typography, Space, Button, Tooltip, Badge } from 'antd'
import {
  CloudServerOutlined,
  ClusterOutlined,
  AlertOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  ClockCircleOutlined,
  ThunderboltOutlined,
  GlobalOutlined,
  RocketOutlined,
  EyeOutlined,
  StarFilled,
} from '@ant-design/icons'
import { overviewApi } from '../services/api'
import type { OverviewStats } from '../types'
import DrawioRenderer from '../components/DrawioRenderer'
import WorldMap from '../components/WorldMap'
import { useVersionStore } from '../stores/versionStore'
import { useDeploymentStore } from '../stores/deploymentStore'

const { Title, Text } = Typography

export default function Dashboard() {
  const { data: overview, isLoading } = useQuery({
    queryKey: ['overview'],
    queryFn: async () => {
      const res = await overviewApi.get()
      return res.data as OverviewStats
    },
  })

  const { projects } = useVersionStore()
  const { getDeploymentsByCodename } = useDeploymentStore()

  // 获取所有测试版本
  const testingVersions = projects.flatMap(p =>
    p.versions
      .filter(v => v.status === 'testing')
      .map(v => {
        const deployments = getDeploymentsByCodename(v.codename)
        const versionRegions = [...new Set(deployments.map(d => d.regionName))]
        const hasError = deployments.some(d => d.status === 'error')
        const hasWarning = deployments.some(d => d.status === 'warning')
        const health = deployments.length === 0 ? 'unknown' : hasError ? 'critical' : hasWarning ? 'warning' : 'healthy'
        return {
          ...v,
          projectName: p.name,
          projectId: p.id,
          regions: versionRegions,
          health,
          isProduction: p.productionVersionId === v.id,
        }
      })
  )

  const recentAlerts = [
    { id: '1', name: 'High CPU Usage', severity: 'warning', service: 'api-gateway', time: '5m ago' },
    { id: '2', name: 'Memory Threshold', severity: 'critical', service: 'chat-service', time: '12m ago' },
    { id: '3', name: 'Pod Restart', severity: 'info', service: 'worker', time: '30m ago' },
  ]

  const recentDeployments = [
    { id: '1', service: 'api-gateway', version: 'v1.2.3', status: 'success', time: '1h ago' },
    { id: '2', service: 'chat-gateway', version: 'v2.0.1', status: 'running', time: '2h ago' },
    { id: '3', service: 'auth-service', version: 'v1.1.0', status: 'failed', time: '4h ago' },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <Title level={4} className="m-0">Infrastructure Overview</Title>
        <Space>
          <Text type="secondary">
            <ClockCircleOutlined className="mr-1" />
            Last updated: just now
          </Text>
        </Space>
      </div>

      {/* Stats Cards */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={isLoading}>
            <Statistic
              title="Total Services"
              value={overview?.services.total || 0}
              prefix={<CloudServerOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={isLoading}>
            <Statistic
              title="Clusters"
              value={overview?.clusters.total || 0}
              prefix={<ClusterOutlined />}
              suffix={`/ ${overview?.clusters.healthy || 0} healthy`}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={isLoading}>
            <Statistic
              title="Active Alerts"
              value={overview?.alerts.total || 0}
              prefix={<AlertOutlined />}
              valueStyle={{ color: (overview?.alerts.critical || 0) > 0 ? '#ef4444' : undefined }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="System Health"
              value={85}
              suffix="%"
              valueStyle={{ color: '#22c55e' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Infrastructure Diagram and World Map */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <DrawioRenderer height={400} />
        </Col>
        <Col xs={24} lg={12}>
          <WorldMap />
        </Col>
      </Row>

      {/* VC-004: 测试版本概览 */}
      <Card
        title={
          <Space>
            <ClockCircleOutlined style={{ color: '#f97316' }} />
            <span>测试版本概览</span>
            <Badge count={testingVersions.length} style={{ backgroundColor: '#f97316' }} />
          </Space>
        }
        extra={<Button type="link" href="/projects">查看全部版本</Button>}
      >
        {testingVersions.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <ClockCircleOutlined style={{ fontSize: 48 }} />
            <p className="mt-4">暂无测试版本</p>
          </div>
        ) : (
          <Table
            dataSource={testingVersions}
            rowKey="id"
            pagination={false}
            size="small"
            columns={[
              {
                title: '项目',
                dataIndex: 'projectName',
                key: 'projectName',
                width: 130,
                render: (name: string) => <span className="font-medium">{name}</span>,
              },
              {
                title: '版本代号',
                dataIndex: 'codename',
                key: 'codename',
                width: 120,
                render: (codename: string, record) => (
                  <Space>
                    {record.isProduction && (
                      <Tooltip title="当前生产版本">
                        <StarFilled className="text-yellow-500" />
                      </Tooltip>
                    )}
                    <span className="font-medium">{codename}</span>
                  </Space>
                ),
              },
              {
                title: '健康状态',
                key: 'health',
                width: 100,
                render: (_: unknown, record) => {
                  const healthConfig: Record<string, { color: string; icon: React.ReactNode; label: string }> = {
                    healthy: { color: 'green', icon: <CheckCircleOutlined />, label: '健康' },
                    warning: { color: 'orange', icon: <WarningOutlined />, label: '警告' },
                    critical: { color: 'red', icon: <WarningOutlined />, label: '异常' },
                    unknown: { color: 'default', icon: <ClockCircleOutlined />, label: '未知' },
                  }
                  const config = healthConfig[record.health]
                  return (
                    <Tag color={config.color} icon={config.icon}>
                      {config.label}
                    </Tag>
                  )
                },
              },
              {
                title: '部署区域',
                dataIndex: 'regions',
                key: 'regions',
                width: 200,
                render: (regions: string[]) => (
                  <Space size={2} wrap>
                    {regions.length === 0 ? (
                      <Text type="secondary">未部署</Text>
                    ) : (
                      regions.slice(0, 3).map(r => (
                        <Tag key={r} icon={<GlobalOutlined />} className="text-xs">{r}</Tag>
                      ))
                    )}
                    {regions.length > 3 && (
                      <Tooltip title={regions.slice(3).join(', ')}>
                        <Tag>+{regions.length - 3}</Tag>
                      </Tooltip>
                    )}
                  </Space>
                ),
              },
              {
                title: '测试链接',
                dataIndex: 'testUrl',
                key: 'testUrl',
                width: 150,
                render: (url: string) => url ? (
                  <a href={url} target="_blank" rel="noopener noreferrer" className="text-xs">
                    {url.replace('https://', '').replace('http://', '')}
                  </a>
                ) : (
                  <Text type="secondary">-</Text>
                ),
              },
              {
                title: '操作',
                key: 'actions',
                width: 120,
                render: (_: unknown, record) => (
                  <Space>
                    <Tooltip title="查看详情">
                      <Button
                        type="link"
                        size="small"
                        icon={<EyeOutlined />}
                        href={`/projects?version=${record.id}`}
                      />
                    </Tooltip>
                    {record.regions.length > 0 && (
                      <Tooltip title="申请上线">
                        <Button
                          type="link"
                          size="small"
                          icon={<RocketOutlined style={{ color: '#22c55e' }} />}
                          href={`/projects?apply=${record.id}`}
                        />
                      </Tooltip>
                    )}
                  </Space>
                ),
              },
            ]}
          />
        )}
      </Card>

      {/* Recent Activity */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card
            title="Recent Alerts"
            extra={<Button type="link" onClick={() => window.location.href = '/alerts'}>View All</Button>}
          >
            <Table
              dataSource={recentAlerts}
              rowKey="id"
              pagination={false}
              size="small"
              columns={[
                {
                  title: 'Alert',
                  dataIndex: 'name',
                  key: 'name',
                },
                {
                  title: 'Severity',
                  dataIndex: 'severity',
                  key: 'severity',
                  render: (severity: string) => {
                    const colors: Record<string, string> = {
                      critical: 'red',
                      warning: 'gold',
                      info: 'blue',
                    }
                    return <Tag color={colors[severity]}>{severity.toUpperCase()}</Tag>
                  },
                },
                {
                  title: 'Service',
                  dataIndex: 'service',
                  key: 'service',
                },
                {
                  title: 'Time',
                  dataIndex: 'time',
                  key: 'time',
                },
              ]}
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card
            title="Recent Deployments"
            extra={<Button type="link" onClick={() => window.location.href = '/deployments'}>View All</Button>}
          >
            <Table
              dataSource={recentDeployments}
              rowKey="id"
              pagination={false}
              size="small"
              columns={[
                {
                  title: 'Service',
                  dataIndex: 'service',
                  key: 'service',
                },
                {
                  title: 'Version',
                  dataIndex: 'version',
                  key: 'version',
                },
                {
                  title: 'Status',
                  dataIndex: 'status',
                  key: 'status',
                  render: (status: string) => {
                    const icons: Record<string, React.ReactNode> = {
                      success: <CheckCircleOutlined className="text-green-500" />,
                      running: <WarningOutlined className="text-yellow-500" />,
                      failed: <WarningOutlined className="text-red-500" />,
                    }
                    return (
                      <span className="flex items-center gap-1">
                        {icons[status]} {status}
                      </span>
                    )
                  },
                },
                {
                  title: 'Time',
                  dataIndex: 'time',
                  key: 'time',
                },
              ]}
            />
          </Card>
        </Col>
      </Row>

      {/* Resource Usage */}
      <Card title="Global Resource Usage">
        <Row gutter={16}>
          <Col span={6}>
            <div className="text-center mb-2">CPU</div>
            <Progress percent={65} status="active" strokeColor="#3b82f6" />
            <div className="text-center text-sm text-gray-500 mt-1">4,200 / 6,500 cores</div>
          </Col>
          <Col span={6}>
            <div className="text-center mb-2">Memory</div>
            <Progress percent={78} strokeColor="#22c55e" />
            <div className="text-center text-sm text-gray-500 mt-1">12.5 / 16 TB</div>
          </Col>
          <Col span={6}>
            <div className="text-center mb-2">Storage</div>
            <Progress percent={45} strokeColor="#eab308" />
            <div className="text-center text-sm text-gray-500 mt-1">4.5 / 10 TB</div>
          </Col>
          <Col span={6}>
            <div className="text-center mb-2">Network</div>
            <Progress percent={32} strokeColor="#8b5cf6" />
            <div className="text-center text-sm text-gray-500 mt-1">32 / 100 Gbps</div>
          </Col>
        </Row>
      </Card>

      {/* Quick Links */}
      <Card title="Quick Links" size="small">
        <Space wrap>
          <Button icon={<GlobalOutlined />} href="https://grafana.example.com" target="_blank">
            Grafana Dashboards
          </Button>
          <Button icon={<ClusterOutlined />} href="https://argocd.example.com" target="_blank">
            ArgoCD
          </Button>
          <Button icon={<ThunderboltOutlined />} href="https://jenkins.example.com" target="_blank">
            Jenkins
          </Button>
        </Space>
      </Card>
    </div>
  )
}
