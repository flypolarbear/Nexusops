import { useEffect, useRef, useState } from 'react'
import * as echarts from 'echarts'
import { Card, Tooltip as AntTooltip, Modal, Descriptions, Tag, Table, Typography, Select, Space } from 'antd'
import { CheckCircleOutlined, WarningOutlined, ExclamationCircleOutlined, GithubOutlined, LinkOutlined, FilterOutlined } from '@ant-design/icons'
import { useDeploymentStore } from '../stores/deploymentStore'
import { useVersionStore } from '../stores/versionStore'
import type { VersionDeployment } from '../types'

const { Text } = Typography

// 区域坐标配置
const regionCoordinates: Record<string, [number, number]> = {
  'us-east': [-77.0369, 38.9072],
  'us-west': [-122.4194, 37.7749],
  'eu-west': [-0.1276, 51.5074],
  'eu-central': [8.6821, 50.1109],
  'ap-east': [121.4737, 31.2304],
  'ap-southeast': [103.8198, 1.3521],
}

const regionNames: Record<string, string> = {
  'us-east': 'US East (AWS)',
  'us-west': 'US West (AWS)',
  'eu-west': 'EU West (GCP)',
  'eu-central': 'EU Central (AWS)',
  'ap-east': 'Asia Pacific (AliCloud)',
  'ap-southeast': 'AP Southeast (AWS)',
}

const getStatusColor = (status: string): string => {
  switch (status) {
    case 'healthy':
    case 'running':
    case 'synced':
      return '#22c55e'
    case 'warning':
    case 'out-of-sync':
      return '#eab308'
    case 'critical':
    case 'error':
    case 'degraded':
      return '#ef4444'
    default:
      return '#94a3b8'
  }
}

export default function WorldMap() {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [selectedCodename, setSelectedCodename] = useState<string | null>(null)

  const { deployments } = useDeploymentStore()
  const { projects } = useVersionStore()

  // 获取所有唯一的 codenames
  const allCodenames = [...new Set(deployments.map(d => d.codename))]

  // 根据 codename 过滤部署数据
  const filteredDeployments = selectedCodename
    ? deployments.filter(d => d.codename === selectedCodename)
    : deployments

  // 获取版本详情（用于 tooltip）
  const getVersionInfo = (codename: string) => {
    for (const project of projects) {
      const version = project.services.flatMap(s => s.versions).find(v => v.codename === codename)
      if (version) {
        return {
          testUrl: version.testUrl,
          gitBranch: project.services.find(s => s.id === version.serviceId)?.gitBranch || "",
          owner: version.owner,
        }
      }
    }
    return null
  }

  // 获取各区域统计（基于过滤后的部署数据）
  const getRegionStats = () => {
    const regionIds = Object.keys(regionCoordinates)
    return regionIds.map(regionId => {
      const regionDeployments = filteredDeployments.filter(d => d.regionId === regionId)
      const status = regionDeployments.length === 0 ? 'healthy' :
        regionDeployments.some(d => d.status === 'error') ? 'critical' :
        regionDeployments.some(d => d.status === 'warning') ? 'warning' : 'healthy'
      const clusters = new Set(regionDeployments.map(d => d.argocdApp)).size || 1
      const cpuAvg = regionDeployments.length > 0
        ? Math.round(regionDeployments.reduce((sum, d) => sum + parseInt(d.cpu) || 0, 0) / regionDeployments.length)
        : 0
      const memoryAvg = regionDeployments.length > 0
        ? Math.round(regionDeployments.reduce((sum, d) => sum + parseInt(d.memory) || 0, 0) / regionDeployments.length)
        : 0

      return {
        id: regionId,
        name: regionNames[regionId] || regionId,
        coordinates: regionCoordinates[regionId],
        status,
        clusters,
        serviceCount: regionDeployments.length,
        cpu: cpuAvg,
        memory: memoryAvg,
        codenames: [...new Set(regionDeployments.map(d => d.codename))],
      }
    })
  }

  useEffect(() => {
    if (!chartRef.current) return

    chartInstance.current = echarts.init(chartRef.current)
    const regionStats = getRegionStats()

    const option: echarts.EChartsOption = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => {
          if (params.seriesType === 'scatter' || params.seriesType === 'effectScatter') {
            const data = params.data
            const codenamesHtml = data.codenames && data.codenames.length > 0
              ? `<br/>Versions: ${data.codenames.map((c: string) => `<span style="color: #8b5cf6">${c}</span>`).join(', ')}`
              : ''
            return `
              <div style="padding: 8px;">
                <strong>${data.name}</strong><br/>
                Status: <span style="color: ${getStatusColor(data.status)}">${data.status.toUpperCase()}</span><br/>
                Clusters: ${data.clusters}<br/>
                Deployments: ${data.serviceCount}${codenamesHtml}<br/>
                Avg CPU: ${data.cpu}m<br/>
                Avg Memory: ${data.memory}Mi
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
          data: regionStats.map((region) => ({
            name: region.name,
            value: [...region.coordinates, region.clusters],
            regionId: region.id,
            status: region.status,
            clusters: region.clusters,
            serviceCount: region.serviceCount,
            cpu: region.cpu,
            memory: region.memory,
            codenames: region.codenames,
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
          data: regionStats
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

    // Register world map - use local file to avoid CORS issues
    const loadMap = async () => {
      try {
        const response = await fetch('/assets/world.json')
        if (response.ok) {
          const worldJson = await response.json()
          echarts.registerMap('world', worldJson)
          chartInstance.current?.setOption(option)

          // Add click event
          chartInstance.current?.on('click', (params: any) => {
            if (params.data && params.data.regionId) {
              setSelectedRegion(params.data.regionId)
              setModalOpen(true)
            }
          })
          return
        }
      } catch (e) {
        console.error('Failed to load local map:', e)
      }

      // Fallback: scatter plot without map
      console.warn('Using scatter fallback')
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
            data: regionStats.map((region) => ({
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
          setSelectedRegion(params.data.regionId)
          setModalOpen(true)
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
  }, [filteredDeployments])

  const regionDeployments = selectedRegion
    ? filteredDeployments.filter(d => d.regionId === selectedRegion)
    : []

  const regionStatus = selectedRegion && regionDeployments.length > 0
    ? regionDeployments.some(d => d.status === 'error') ? 'critical'
    : regionDeployments.some(d => d.status === 'warning') ? 'warning' : 'healthy'
    : 'healthy'

  const serviceColumns = [
    {
      title: 'Service',
      dataIndex: 'serviceName',
      key: 'serviceName',
      render: (name: string) => <span className="font-medium">{name}</span>,
    },
    {
      title: 'Project',
      dataIndex: 'projectName',
      key: 'projectName',
      render: (name: string, record: VersionDeployment) => (
        <span>
          {name}
          {record.projectId !== 'proj-1' && <Tag color="cyan" className="ml-1">External</Tag>}
        </span>
      ),
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
      render: (codename: string) => codename
        ? <Tag color={codename === 'legacy' ? 'default' : 'purple'}>{codename}</Tag>
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
      title: 'CPU/Mem',
      key: 'resources',
      render: (_: unknown, record: VersionDeployment) => (
        <span className="text-xs">{record.cpu} / {record.memory}</span>
      ),
    },
  ]

  const regionStats = getRegionStats()

  return (
    <>
      <Card
        title="WorldMap"
        className="h-full"
        extra={
          <Space>
            {/* VC-005: 版本选择器 */}
            <Select
              placeholder="Filter versions"
              allowClear
              style={{ width: 140 }}
              value={selectedCodename}
              onChange={(value) => setSelectedCodename(value)}
              suffixIcon={<FilterOutlined />}
              options={allCodenames.map(c => {
                const versionInfo = getVersionInfo(c)
                return {
                  value: c,
                  label: (
                    <AntTooltip
                      title={
                        versionInfo ? (
                          <div>
                            <div>Git: {versionInfo.gitBranch}</div>
                            {versionInfo.testUrl && <div>URL: {versionInfo.testUrl}</div>}
                            <div>Owner: {versionInfo.owner}</div>
                          </div>
                        ) : null
                      }
                    >
                      <span>{c}</span>
                    </AntTooltip>
                  ),
                }
              })}
            />
            <div className="flex gap-3">
              <AntTooltip title="Healthy">
                <span className="flex items-center gap-1">
                  <span className="w-3 h-3 rounded-full bg-green-500" />
                  <span className="text-sm text-gray-500">{regionStats.filter(r => r.status === 'healthy').length}</span>
                </span>
              </AntTooltip>
              <AntTooltip title="Warning">
                <span className="flex items-center gap-1">
                  <span className="w-3 h-3 rounded-full bg-yellow-500" />
                  <span className="text-sm text-gray-500">{regionStats.filter(r => r.status === 'warning').length}</span>
                </span>
              </AntTooltip>
              <AntTooltip title="Critical">
                <span className="flex items-center gap-1">
                  <span className="w-3 h-3 rounded-full bg-red-500" />
                  <span className="text-sm text-gray-500">{regionStats.filter(r => r.status === 'critical').length}</span>
                </span>
              </AntTooltip>
            </div>
          </Space>
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
            Region: {regionNames[selectedRegion || '']}
            <Tag
              color={regionStatus === 'healthy' ? 'green' : regionStatus === 'warning' ? 'orange' : 'red'}
              className="ml-2"
            >
              {regionStatus.toUpperCase()}
            </Tag>
          </span>
        }
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        footer={null}
        width={900}
      >
        {selectedRegion && regionDeployments.length > 0 && (
          <div className="space-y-4">
            {/* 按版本分组统计 */}
            <Descriptions bordered column={3} size="small">
              <Descriptions.Item label="Total Deployments">{regionDeployments.length}</Descriptions.Item>
              <Descriptions.Item label="Versions">
                {Array.from(new Set(regionDeployments.map(d => d.codename))).map(codename => (
                  <Tag key={codename} color="purple" className="mr-1">{codename}</Tag>
                ))}
              </Descriptions.Item>
              <Descriptions.Item label="Projects">
                {Array.from(new Set(regionDeployments.map(d => d.projectName))).join(', ')}
              </Descriptions.Item>
            </Descriptions>

            {/* 部署详情表格 */}
            <div>
              <Text strong className="mb-2 block">Deployed Services</Text>
              <Table
                dataSource={regionDeployments}
                columns={serviceColumns}
                rowKey="id"
                pagination={false}
                size="small"
                expandable={{
                  expandedRowRender: (record) => (
                    <div className="p-2 bg-gray-50 space-y-2">
                      <div className="flex items-center gap-4">
                        <span className="text-gray-500 w-20">Git Repo:</span>
                        <a href={record.gitRepo} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1">
                          <GithubOutlined />
                          {record.gitRepo.replace('https://github.com/', '')}
                        </a>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="text-gray-500 w-20">Branch:</span>
                        <code className="bg-gray-200 px-2 py-0.5 rounded text-sm">{record.gitBranch}</code>
                        <span className="text-gray-400">@</span>
                        <a href={record.gitCommitUrl} target="_blank" rel="noopener noreferrer" className="text-blue-500 text-sm">
                          {record.gitCommit.substring(0, 7)}
                        </a>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="text-gray-500 w-20">ArgoCD App:</span>
                        <a href={record.argocdUrl} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-blue-500">
                          <LinkOutlined />
                          {record.argocdApp}
                        </a>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="text-gray-500 w-20">Sync Status:</span>
                        <Tag color={record.argocdSyncStatus === 'synced' ? 'green' : 'orange'}>
                          {record.argocdSyncStatus.toUpperCase()}
                        </Tag>
                        <span className="text-gray-500 ml-4">Health:</span>
                        <Tag color={record.argocdHealthStatus === 'healthy' ? 'green' : record.argocdHealthStatus === 'degraded' ? 'red' : 'orange'}>
                          {record.argocdHealthStatus.toUpperCase()}
                        </Tag>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="text-gray-500 w-20">Deployed:</span>
                        <span>{record.deployedAt}</span>
                        <span className="text-gray-400">by</span>
                        <span>{record.deployedBy}</span>
                      </div>
                    </div>
                  ),
                  rowExpandable: () => true,
                }}
              />
            </div>
          </div>
        )}
      </Modal>
    </>
  )
}
