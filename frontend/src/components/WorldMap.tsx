import { useEffect, useRef, useState } from 'react'
import * as echarts from 'echarts'
import { Card, Tooltip as AntTooltip, Modal, Descriptions, Tag, Table, Typography } from 'antd'
import { CheckCircleOutlined, WarningOutlined, ExclamationCircleOutlined } from '@ant-design/icons'

const { Text } = Typography

interface ServiceDeployment {
  name: string
  imageVersion: string      // 镜像版本，如 v1.2.3
  codename: string | null   // 版本代号，如 Phoenix、Titan
  status: 'running' | 'warning' | 'error'
  replicas: number
  cpu: string
  memory: string
}

interface RegionData {
  id: string
  name: string
  coordinates: [number, number]
  status: 'healthy' | 'warning' | 'critical'
  clusters: number
  cpu: number
  memory: number
  services: ServiceDeployment[]
}

const mockRegions: RegionData[] = [
  {
    id: 'us-east',
    name: 'US East (AWS)',
    coordinates: [-77.0369, 38.9072],
    status: 'healthy',
    clusters: 3,
    cpu: 65,
    memory: 72,
    services: [
      { name: 'api-gateway', imageVersion: 'v1.2.3', codename: 'Phoenix', status: 'running', replicas: 3, cpu: '450m', memory: '512Mi' },
      { name: 'chat-gateway', imageVersion: 'v2.0.1', codename: 'Aurora', status: 'running', replicas: 2, cpu: '200m', memory: '256Mi' },
      { name: 'auth-service', imageVersion: 'v1.1.0', codename: null, status: 'running', replicas: 2, cpu: '100m', memory: '128Mi' },
      { name: 'worker', imageVersion: 'v1.0.5', codename: 'Titan', status: 'running', replicas: 5, cpu: '500m', memory: '1Gi' },
    ],
  },
  {
    id: 'us-west',
    name: 'US West (AWS)',
    coordinates: [-122.4194, 37.7749],
    status: 'healthy',
    clusters: 2,
    cpu: 45,
    memory: 58,
    services: [
      { name: 'api-gateway', imageVersion: 'v1.2.3', codename: 'Phoenix', status: 'running', replicas: 2, cpu: '300m', memory: '384Mi' },
      { name: 'chat-gateway', imageVersion: 'v2.0.1', codename: 'Aurora', status: 'running', replicas: 2, cpu: '180m', memory: '220Mi' },
    ],
  },
  {
    id: 'eu-west',
    name: 'EU West (GCP)',
    coordinates: [-0.1276, 51.5074],
    status: 'warning',
    clusters: 2,
    cpu: 78,
    memory: 82,
    services: [
      { name: 'api-gateway', imageVersion: 'v1.2.2', codename: 'legacy', status: 'warning', replicas: 2, cpu: '650m', memory: '780Mi' },
      { name: 'chat-gateway', imageVersion: 'v2.0.0', codename: 'stable', status: 'running', replicas: 2, cpu: '200m', memory: '256Mi' },
      { name: 'auth-service', imageVersion: 'v1.1.0', codename: null, status: 'running', replicas: 1, cpu: '80m', memory: '96Mi' },
    ],
  },
  {
    id: 'eu-central',
    name: 'EU Central (AWS)',
    coordinates: [8.6821, 50.1109],
    status: 'healthy',
    clusters: 1,
    cpu: 52,
    memory: 61,
    services: [
      { name: 'api-gateway', imageVersion: 'v1.2.3', codename: 'Phoenix', status: 'running', replicas: 2, cpu: '280m', memory: '320Mi' },
    ],
  },
  {
    id: 'ap-east',
    name: 'Asia Pacific (AliCloud)',
    coordinates: [121.4737, 31.2304],
    status: 'critical',
    clusters: 2,
    cpu: 92,
    memory: 88,
    services: [
      { name: 'api-gateway', imageVersion: 'v1.2.3', codename: 'Phoenix', status: 'error', replicas: 1, cpu: '950m', memory: '920Mi' },
      { name: 'chat-gateway', imageVersion: 'v2.0.1', codename: 'Aurora', status: 'warning', replicas: 2, cpu: '400m', memory: '480Mi' },
      { name: 'worker', imageVersion: 'v1.0.5', codename: 'Titan', status: 'error', replicas: 0, cpu: '0m', memory: '0Mi' },
    ],
  },
  {
    id: 'ap-southeast',
    name: 'AP Southeast (AWS)',
    coordinates: [103.8198, 1.3521],
    status: 'healthy',
    clusters: 1,
    cpu: 38,
    memory: 45,
    services: [
      { name: 'api-gateway', imageVersion: 'v1.2.3', codename: 'Phoenix', status: 'running', replicas: 1, cpu: '150m', memory: '192Mi' },
    ],
  },
]

const getStatusColor = (status: string): string => {
  switch (status) {
    case 'healthy':
    case 'running':
      return '#22c55e'
    case 'warning':
      return '#eab308'
    case 'critical':
    case 'error':
      return '#ef4444'
    default:
      return '#94a3b8'
  }
}

export default function WorldMap() {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)
  const [selectedRegion, setSelectedRegion] = useState<RegionData | null>(null)
  const [modalOpen, setModalOpen] = useState(false)

  const handleRegionClick = (regionId: string) => {
    const region = mockRegions.find(r => r.id === regionId)
    if (region) {
      setSelectedRegion(region)
      setModalOpen(true)
    }
  }

  useEffect(() => {
    if (!chartRef.current) return

    chartInstance.current = echarts.init(chartRef.current)

    const option: echarts.EChartsOption = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => {
          if (params.seriesType === 'scatter' || params.seriesType === 'effectScatter') {
            const data = params.data
            return `
              <div style="padding: 8px;">
                <strong>${data.name}</strong><br/>
                Status: <span style="color: ${getStatusColor(data.status)}">${data.status.toUpperCase()}</span><br/>
                Clusters: ${data.clusters}<br/>
                Services: ${data.serviceCount}<br/>
                CPU: ${data.cpu}%<br/>
                Memory: ${data.memory}%
              </div>
            `
          }
          return ''
        },
      },
      geo: {
        map: 'world',
        roam: true,
        zoom: 1.2,
        center: [0, 20],
        scaleLimit: {
          min: 1,
          max: 5,
        },
        itemStyle: {
          areaColor: '#f1f5f9',
          borderColor: '#cbd5e1',
          borderWidth: 0.5,
        },
        emphasis: {
          itemStyle: {
            areaColor: '#e2e8f0',
          },
        },
        silent: false,
      },
      series: [
        {
          type: 'scatter',
          coordinateSystem: 'geo',
          data: mockRegions.map((region) => ({
            name: region.name,
            value: [...region.coordinates, region.clusters],
            regionId: region.id,
            status: region.status,
            clusters: region.clusters,
            serviceCount: region.services.length,
            cpu: region.cpu,
            memory: region.memory,
            itemStyle: {
              color: getStatusColor(region.status),
              shadowBlur: 10,
              shadowColor: getStatusColor(region.status),
            },
          })),
          symbolSize: (val: number[]) => {
            return Math.max(18, Math.min(35, val[2] * 10))
          },
          itemStyle: {
            borderWidth: 2,
            borderColor: '#fff',
          },
          emphasis: {
            itemStyle: {
              borderWidth: 3,
              borderColor: '#fff',
              shadowBlur: 15,
            },
          },
        },
        {
          type: 'effectScatter',
          coordinateSystem: 'geo',
          data: mockRegions
            .filter((r) => r.status === 'critical' || r.status === 'warning')
            .map((region) => ({
              name: region.name,
              value: [...region.coordinates, region.clusters],
              regionId: region.id,
              status: region.status,
              itemStyle: {
                color: getStatusColor(region.status),
              },
            })),
          symbolSize: 10,
          showEffectOn: 'render',
          rippleEffect: {
            brushType: 'stroke',
            scale: 3,
          },
        },
      ],
    }

    // Register world map - try multiple CDNs for reliability
    const mapUrls = [
      'https://echarts.apache.org/examples/data/asset/geo/world.json',
      'https://unpkg.com/echarts@5.4.3/map/json/world.json',
      'https://cdnjs.cloudflare.com/ajax/libs/echarts/5.4.3/map/json/world.json',
    ]

    const loadMap = async () => {
      for (const url of mapUrls) {
        try {
          const response = await fetch(url)
          if (response.ok) {
            const worldJson = await response.json()
            echarts.registerMap('world', worldJson)
            chartInstance.current?.setOption(option)

            // Add click event
            chartInstance.current?.on('click', (params: any) => {
              if (params.data && params.data.regionId) {
                handleRegionClick(params.data.regionId)
              }
            })
            return // Success, exit
          }
        } catch (e) {
          console.warn(`Failed to load map from ${url}:`, e)
        }
      }

      // All CDNs failed, use scatter plot fallback
      console.error('All map CDNs failed, using scatter fallback')
      const fallbackOption: echarts.EChartsOption = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'item',
          formatter: (params: any) => {
            const data = params.data
            return `<div style="padding: 8px;"><strong>${data.name}</strong><br/>Status: ${data.status}</div>`
          },
        },
        xAxis: { type: 'value', show: false, min: -180, max: 180 },
        yAxis: { type: 'value', show: false, min: -90, max: 90 },
        grid: { left: 0, right: 0, top: 0, bottom: 0 },
        series: [
          {
            type: 'scatter',
            data: mockRegions.map((region) => ({
              name: region.name,
              value: region.coordinates,
              regionId: region.id,
              status: region.status,
              itemStyle: { color: getStatusColor(region.status) },
            })),
            symbolSize: 25,
          },
        ],
      }
      chartInstance.current?.setOption(fallbackOption)

      chartInstance.current?.on('click', (params: any) => {
        if (params.data && params.data.regionId) {
          handleRegionClick(params.data.regionId)
        }
      })
    }

    loadMap()

    const handleResize = () => {
      chartInstance.current?.resize()
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chartInstance.current?.dispose()
    }
  }, [])

  const serviceColumns = [
    {
      title: 'Service',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => <span className="font-medium">{name}</span>,
    },
    {
      title: 'Image Version',
      dataIndex: 'imageVersion',
      key: 'imageVersion',
      render: (version: string) => <Tag color="blue">{version}</Tag>,
    },
    {
      title: 'Codename',
      dataIndex: 'codename',
      key: 'codename',
      render: (codename: string | null) => codename
        ? <Tag color="purple">{codename}</Tag>
        : <span className="text-gray-400">-</span>,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const config: Record<string, { color: string; icon: React.ReactNode }> = {
          running: { color: 'green', icon: <CheckCircleOutlined /> },
          warning: { color: 'orange', icon: <WarningOutlined /> },
          error: { color: 'red', icon: <ExclamationCircleOutlined /> },
        }
        const { color, icon } = config[status] || { color: 'default', icon: null }
        return <Tag color={color} icon={icon}>{status.toUpperCase()}</Tag>
      },
    },
    {
      title: 'Replicas',
      dataIndex: 'replicas',
      key: 'replicas',
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
    <>
      <Card
        title="WorldMap"
        className="h-full"
        extra={
          <div className="flex gap-3">
            <AntTooltip title="Healthy">
              <span className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-full bg-green-500" />
                <span className="text-sm text-gray-500">{mockRegions.filter(r => r.status === 'healthy').length}</span>
              </span>
            </AntTooltip>
            <AntTooltip title="Warning">
              <span className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-full bg-yellow-500" />
                <span className="text-sm text-gray-500">{mockRegions.filter(r => r.status === 'warning').length}</span>
              </span>
            </AntTooltip>
            <AntTooltip title="Critical">
              <span className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-full bg-red-500" />
                <span className="text-sm text-gray-500">{mockRegions.filter(r => r.status === 'critical').length}</span>
              </span>
            </AntTooltip>
          </div>
        }
      >
        <div ref={chartRef} style={{ height: 300, width: '100%' }} />
        <Text type="secondary" className="text-xs mt-2 block text-center">
          Click on a region to view deployed services
        </Text>
      </Card>

      <Modal
        title={
          <span>
            Region: {selectedRegion?.name}
            <Tag
              color={selectedRegion?.status === 'healthy' ? 'green' : selectedRegion?.status === 'warning' ? 'orange' : 'red'}
              className="ml-2"
            >
              {selectedRegion?.status?.toUpperCase()}
            </Tag>
          </span>
        }
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        footer={null}
        width={700}
      >
        {selectedRegion && (
          <div className="space-y-4">
            <Descriptions bordered column={2} size="small">
              <Descriptions.Item label="Clusters">{selectedRegion.clusters}</Descriptions.Item>
              <Descriptions.Item label="Services">{selectedRegion.services.length}</Descriptions.Item>
              <Descriptions.Item label="CPU Usage">
                <Tag color={selectedRegion.cpu > 80 ? 'red' : selectedRegion.cpu > 60 ? 'orange' : 'green'}>
                  {selectedRegion.cpu}%
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Memory Usage">
                <Tag color={selectedRegion.memory > 80 ? 'red' : selectedRegion.memory > 60 ? 'orange' : 'green'}>
                  {selectedRegion.memory}%
                </Tag>
              </Descriptions.Item>
            </Descriptions>

            <div>
              <Text strong className="mb-2 block">Deployed Services</Text>
              <Table
                dataSource={selectedRegion.services}
                columns={serviceColumns}
                rowKey="name"
                pagination={false}
                size="small"
              />
            </div>
          </div>
        )}
      </Modal>
    </>
  )
}
