import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Card, Row, Col, Statistic, Progress, Table, Tag, Typography, Space, Button } from 'antd'
import {
  CloudServerOutlined,
  ClusterOutlined,
  AlertOutlined,
  WarningOutlined,
  ClockCircleOutlined,
  ThunderboltOutlined,
  GlobalOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'
import { overviewApi } from '../services/api'
import type { OverviewStats } from '../types'
import DrawioRenderer from '../components/DrawioRenderer'
import WorldMap from '../components/WorldMap'
import PageContainer from '../components/layout/PageContainer'

const { Text } = Typography

export default function Dashboard() {
  const { t } = useTranslation()
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
    <PageContainer
      title={t('dashboard.infrastructureOverview')}
      icon={<GlobalOutlined />}
      transparent
      extra={
        <Space>
          <Text type="secondary">
            <ClockCircleOutlined className="mr-1" />
            {t('dashboard.lastUpdated')}
          </Text>
        </Space>
      }
    >
      <div className="space-y-6">
        {/* Stats Cards */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={isLoading}>
            <Statistic
              title={t('dashboard.totalServices')}
              value={overview?.services.total || 0}
              prefix={<CloudServerOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={isLoading}>
            <Statistic
              title={t('dashboard.clusters')}
              value={overview?.clusters.total || 0}
              prefix={<ClusterOutlined />}
              suffix={`/ ${overview?.clusters.healthy || 0} ${t('dashboard.healthy')}`}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={isLoading}>
            <Statistic
              title={t('dashboard.activeAlerts')}
              value={overview?.alerts.total || 0}
              prefix={<AlertOutlined />}
              valueStyle={{ color: (overview?.alerts.critical || 0) > 0 ? '#ef4444' : undefined }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title={t('dashboard.systemHealth')}
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
            title={t('dashboard.recentAlerts')}
            extra={<Button type="link" onClick={() => window.location.href = '/alerts'}>{t('dashboard.viewAll')}</Button>}
          >
            <Table
              dataSource={recentAlerts}
              rowKey="id"
              pagination={false}
              size="small"
              columns={[
                {
                  title: t('dashboard.alert'),
                  dataIndex: 'name',
                  key: 'name',
                },
                {
                  title: t('dashboard.severity'),
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
                  title: t('dashboard.service'),
                  dataIndex: 'service',
                  key: 'service',
                },
                {
                  title: t('dashboard.time'),
                  dataIndex: 'time',
                  key: 'time',
                },
              ]}
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card
            title={t('dashboard.recentDeployments')}
            extra={<Button type="link" onClick={() => window.location.href = '/deployments'}>{t('dashboard.viewAll')}</Button>}
          >
            <Table
              dataSource={recentDeployments}
              rowKey="id"
              pagination={false}
              size="small"
              columns={[
                {
                  title: t('dashboard.service'),
                  dataIndex: 'service',
                  key: 'service',
                },
                {
                  title: t('dashboard.version'),
                  dataIndex: 'version',
                  key: 'version',
                },
                {
                  title: t('dashboard.status'),
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
                  title: t('dashboard.time'),
                  dataIndex: 'time',
                  key: 'time',
                },
              ]}
            />
          </Card>
        </Col>
      </Row>

      {/* Resource Usage */}
      <Card title={t('dashboard.globalResourceUsage')}>
        <Row gutter={16}>
          <Col span={6}>
            <div className="text-center mb-2">{t('dashboard.cpu')}</div>
            <Progress percent={65} status="active" strokeColor="#3b82f6" />
            <div className="text-center text-sm text-gray-500 mt-1">4,200 / 6,500 cores</div>
          </Col>
          <Col span={6}>
            <div className="text-center mb-2">{t('dashboard.memory')}</div>
            <Progress percent={78} strokeColor="#22c55e" />
            <div className="text-center text-sm text-gray-500 mt-1">12.5 / 16 TB</div>
          </Col>
          <Col span={6}>
            <div className="text-center mb-2">{t('dashboard.storage')}</div>
            <Progress percent={45} strokeColor="#eab308" />
            <div className="text-center text-sm text-gray-500 mt-1">4.5 / 10 TB</div>
          </Col>
          <Col span={6}>
            <div className="text-center mb-2">{t('dashboard.network')}</div>
            <Progress percent={32} strokeColor="#8b5cf6" />
            <div className="text-center text-sm text-gray-500 mt-1">32 / 100 Gbps</div>
          </Col>
        </Row>
      </Card>

      {/* Quick Links */}
      <Card title={t('dashboard.quickLinks')} size="small">
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
    </PageContainer>
  )
}
