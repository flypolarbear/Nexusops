import { useState } from 'react'
import { Card, Table, Tag, Select, Space, Badge, Modal, Descriptions } from 'antd'
import { ExclamationCircleOutlined, InfoCircleOutlined, WarningOutlined } from '@ant-design/icons'
import PageContainer from '../components/layout/PageContainer'

const mockAlerts = [
  {
    id: 'alert-1',
    name: 'High CPU Usage',
    source: 'Prometheus',
    severity: 'warning',
    status: 'firing',
    service: 'api-gateway',
    project: 'Platform',
    summary: 'CPU usage above 80% for more than 5 minutes',
    description: 'Current CPU usage is at 85%. Consider scaling the deployment.',
    firedAt: '2024-01-15 14:30:00',
    labels: { severity: 'warning', team: 'platform' },
  },
  {
    id: 'alert-2',
    name: 'Memory Threshold Exceeded',
    source: 'Prometheus',
    severity: 'critical',
    status: 'firing',
    service: 'chat-service',
    project: 'Chat',
    summary: 'Memory usage above 90%',
    description: 'Memory usage is at 92%. OOM kills may occur.',
    firedAt: '2024-01-15 14:25:00',
    labels: { severity: 'critical', team: 'chat' },
  },
  {
    id: 'alert-3',
    name: 'Pod Restart Loop',
    source: 'Kubernetes',
    severity: 'critical',
    status: 'firing',
    service: 'worker',
    project: 'Platform',
    summary: 'Pod has restarted 5 times in the last 10 minutes',
    description: 'Check logs for crash reason.',
    firedAt: '2024-01-15 14:00:00',
    labels: { severity: 'critical', team: 'platform' },
  },
  {
    id: 'alert-4',
    name: 'Low Disk Space',
    source: 'Node Exporter',
    severity: 'warning',
    status: 'resolved',
    service: 'node-1',
    project: 'Infrastructure',
    summary: 'Disk usage above 85%',
    description: 'Consider cleaning up old logs or expanding storage.',
    firedAt: '2024-01-15 10:00:00',
    labels: { severity: 'warning', team: 'infra' },
  },
  {
    id: 'alert-5',
    name: 'API Latency High',
    source: 'Grafana',
    severity: 'info',
    status: 'firing',
    service: 'api-gateway',
    project: 'Platform',
    summary: 'P95 latency above 500ms',
    description: 'Current P95 latency is 650ms.',
    firedAt: '2024-01-15 13:45:00',
    labels: { severity: 'info', team: 'platform' },
  },
]

export default function Alerts() {
  const [severityFilter, setSeverityFilter] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string | null>(null)
  const [selectedAlert, setSelectedAlert] = useState<typeof mockAlerts[0] | null>(null)

  const filteredAlerts = mockAlerts.filter((alert) => {
    if (severityFilter && alert.severity !== severityFilter) return false
    if (statusFilter && alert.status !== statusFilter) return false
    return true
  })

  const columns = [
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      width: 100,
      render: (severity: string) => {
        const config: Record<string, { color: string; icon: React.ReactNode }> = {
          critical: { color: 'red', icon: <ExclamationCircleOutlined /> },
          warning: { color: 'orange', icon: <WarningOutlined /> },
          info: { color: 'blue', icon: <InfoCircleOutlined /> },
        }
        const { color, icon } = config[severity]
        return <Tag color={color} icon={icon}>{severity.toUpperCase()}</Tag>
      },
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Badge
          status={status === 'firing' ? 'error' : 'success'}
          text={status === 'firing' ? 'Firing' : 'Resolved'}
        />
      ),
    },
    {
      title: 'Alert',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => <span className="font-medium">{name}</span>,
    },
    {
      title: 'Service',
      dataIndex: 'service',
      key: 'service',
    },
    {
      title: 'Project',
      dataIndex: 'project',
      key: 'project',
    },
    {
      title: 'Summary',
      dataIndex: 'summary',
      key: 'summary',
      ellipsis: true,
    },
    {
      title: 'Fired At',
      dataIndex: 'firedAt',
      key: 'firedAt',
      width: 160,
    },
    {
      title: 'Action',
      key: 'action',
      width: 80,
      render: (_: unknown, record: typeof mockAlerts[0]) => (
        <a onClick={() => setSelectedAlert(record)}>Details</a>
      ),
    },
  ]

  return (
    <PageContainer title="Alerts" transparent>
      <div className="space-y-6">

      <Card>
        <Space className="mb-4">
          <Select
            placeholder="Filter by severity"
            allowClear
            style={{ width: 150 }}
            onChange={(value) => setSeverityFilter(value)}
            options={[
              { value: 'critical', label: 'Critical' },
              { value: 'warning', label: 'Warning' },
              { value: 'info', label: 'Info' },
            ]}
          />
          <Select
            placeholder="Filter by status"
            allowClear
            style={{ width: 150 }}
            onChange={(value) => setStatusFilter(value)}
            options={[
              { value: 'firing', label: 'Firing' },
              { value: 'resolved', label: 'Resolved' },
            ]}
          />
        </Space>

        <Table
          dataSource={filteredAlerts}
          columns={columns}
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Modal
        title={selectedAlert?.name}
        open={!!selectedAlert}
        onCancel={() => setSelectedAlert(null)}
        footer={null}
        width={700}
      >
        {selectedAlert && (
          <Descriptions bordered column={2}>
            <Descriptions.Item label="Severity">
              <Tag color={selectedAlert.severity === 'critical' ? 'red' : selectedAlert.severity === 'warning' ? 'orange' : 'blue'}>
                {selectedAlert.severity.toUpperCase()}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Status">
              <Badge status={selectedAlert.status === 'firing' ? 'error' : 'success'} text={selectedAlert.status} />
            </Descriptions.Item>
            <Descriptions.Item label="Source">{selectedAlert.source}</Descriptions.Item>
            <Descriptions.Item label="Service">{selectedAlert.service}</Descriptions.Item>
            <Descriptions.Item label="Project">{selectedAlert.project}</Descriptions.Item>
            <Descriptions.Item label="Fired At">{selectedAlert.firedAt}</Descriptions.Item>
            <Descriptions.Item label="Summary" span={2}>{selectedAlert.summary}</Descriptions.Item>
            <Descriptions.Item label="Description" span={2}>{selectedAlert.description}</Descriptions.Item>
            <Descriptions.Item label="Labels" span={2}>
              {Object.entries(selectedAlert.labels).map(([key, value]) => (
                <Tag key={key}>{key}={String(value)}</Tag>
              ))}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
      </div>
    </PageContainer>
  )
}
