import { useState } from 'react'
import { Card, Tree, Table, Tag, Input, Select, Space } from 'antd'
import { SearchOutlined, FolderOutlined, ClusterOutlined, CloudOutlined } from '@ant-design/icons'
import type { DataNode } from 'antd/es/tree'
import PageContainer from '../components/layout/PageContainer'
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

// Namespace data for future enhancement
// const mockNamespaces = [
//   { id: 'ns-1', name: 'default', clusterId: 'cluster-1', services: 5 },
//   { id: 'ns-2', name: 'monitoring', clusterId: 'cluster-1', services: 3 },
//   { id: 'ns-3', name: 'production', clusterId: 'cluster-1', services: 12 },
//   { id: 'ns-4', name: 'default', clusterId: 'cluster-2', services: 2 },
// ]

const mockServices = [
  { id: 'svc-1', name: 'api-gateway', namespace: 'production', cluster: 'Production Cluster', replicas: 3, status: 'running', cpu: '450m', memory: '512Mi' },
  { id: 'svc-2', name: 'chat-gateway', namespace: 'production', cluster: 'Production Cluster', replicas: 2, status: 'running', cpu: '200m', memory: '256Mi' },
  { id: 'svc-3', name: 'auth-service', namespace: 'production', cluster: 'Production Cluster', replicas: 2, status: 'running', cpu: '100m', memory: '128Mi' },
  { id: 'svc-4', name: 'grafana', namespace: 'monitoring', cluster: 'Production Cluster', replicas: 1, status: 'running', cpu: '50m', memory: '128Mi' },
  { id: 'svc-5', name: 'prometheus', namespace: 'monitoring', cluster: 'Production Cluster', replicas: 1, status: 'running', cpu: '200m', memory: '512Mi' },
  { id: 'svc-6', name: 'test-api', namespace: 'default', cluster: 'Development Cluster', replicas: 1, status: 'error', cpu: '0m', memory: '0Mi' },
]

export default function Resources() {
  const [, setSelectedRegion] = useState<string | null>(null)
  const [selectedCluster, setSelectedCluster] = useState<string | null>(null)
  const [searchText, setSearchText] = useState('')

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
    const matchesSearch =
      service.name.toLowerCase().includes(searchText.toLowerCase()) ||
      service.namespace.toLowerCase().includes(searchText.toLowerCase())
    const matchesCluster = !selectedCluster || service.cluster.includes(selectedCluster)
    return matchesSearch && matchesCluster
  })

  const columns = [
    {
      title: 'Service',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => <span className="font-medium">{name}</span>,
    },
    {
      title: 'Namespace',
      dataIndex: 'namespace',
      key: 'namespace',
    },
    {
      title: 'Cluster',
      dataIndex: 'cluster',
      key: 'cluster',
    },
    {
      title: 'Replicas',
      dataIndex: 'replicas',
      key: 'replicas',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colors: Record<string, string> = {
          running: 'green',
          stopped: 'default',
          error: 'red',
        }
        return <Tag color={colors[status]}>{status.toUpperCase()}</Tag>
      },
    },
    {
      title: 'CPU',
      dataIndex: 'cpu',
      key: 'cpu',
    },
    {
      title: 'Memory',
      dataIndex: 'memory',
      key: 'memory',
    },
  ]

  return (
    <PageContainer title="Resources" transparent>
      <div className="flex gap-6">
        {/* Region/Cluster Tree */}
        <Card className="w-80 shrink-0" title="Regions & Clusters">
          <Tree
            showIcon
            treeData={treeData}
            onSelect={(keys) => {
              const key = keys[0] as string
              if (key.startsWith('cluster')) {
                setSelectedCluster(key)
              } else {
                setSelectedRegion(key)
                setSelectedCluster(null)
              }
            }}
            defaultExpandAll
          />
        </Card>

        {/* Services Table */}
        <Card className="flex-1" title="Services">
          <Space className="mb-4">
            <Search
              placeholder="Search services..."
              allowClear
              style={{ width: 300 }}
              prefix={<SearchOutlined />}
              onChange={(e) => setSearchText(e.target.value)}
            />
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
          </Space>

          <Table
            dataSource={filteredServices}
            columns={columns}
            rowKey="id"
            pagination={{ pageSize: 10 }}
          />
        </Card>
      </div>
    </PageContainer>
  )
}
