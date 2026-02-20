import { useQuery } from '@tanstack/react-query'
import { Card, Row, Col, Statistic, Progress, Table, Tag, Typography, Space, Button } from 'antd'
import {
  CloudServerOutlined,
  ClusterOutlined,
  AlertOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  ClockCircleOutlined,
  ThunderboltOutlined,
  GlobalOutlined,
} from '@ant-design/icons'
import { overviewApi } from '../services/api'
import type { OverviewStats } from '../types'
import DrawioRenderer from '../components/DrawioRenderer'
import WorldMap from '../components/WorldMap'

const { Title, Text } = Typography

export default function Dashboard() {
  const { data: overview, isLoading } = useQuery({
    queryKey: ['overview'],
    queryFn: async () => {
      const res = await overviewApi.get()
      return res.data as OverviewStats
    },
  })

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
