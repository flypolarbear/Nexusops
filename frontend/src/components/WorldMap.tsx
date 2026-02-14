import { useEffect, useRef } from 'react'
import * as echarts from 'echarts'
import { Card, Tooltip as AntTooltip } from 'antd'

interface RegionData {
  name: string
  coordinates: [number, number]
  status: 'healthy' | 'warning' | 'critical'
  clusters: number
  cpu: number
  memory: number
}

const mockRegions: RegionData[] = [
  {
    name: 'US East (AWS)',
    coordinates: [-77.0369, 38.9072],
    status: 'healthy',
    clusters: 3,
    cpu: 65,
    memory: 72,
  },
  {
    name: 'US West (AWS)',
    coordinates: [-122.4194, 37.7749],
    status: 'healthy',
    clusters: 2,
    cpu: 45,
    memory: 58,
  },
  {
    name: 'EU West (GCP)',
    coordinates: [-0.1276, 51.5074],
    status: 'warning',
    clusters: 2,
    cpu: 78,
    memory: 82,
  },
  {
    name: 'EU Central (AWS)',
    coordinates: [8.6821, 50.1109],
    status: 'healthy',
    clusters: 1,
    cpu: 52,
    memory: 61,
  },
  {
    name: 'Asia Pacific (AliCloud)',
    coordinates: [121.4737, 31.2304],
    status: 'critical',
    clusters: 2,
    cpu: 92,
    memory: 88,
  },
  {
    name: 'AP Southeast (AWS)',
    coordinates: [103.8198, 1.3521],
    status: 'healthy',
    clusters: 1,
    cpu: 38,
    memory: 45,
  },
]

const getStatusColor = (status: string): string => {
  switch (status) {
    case 'healthy':
      return '#22c55e'
    case 'warning':
      return '#eab308'
    case 'critical':
      return '#ef4444'
    default:
      return '#94a3b8'
  }
}

export default function WorldMap() {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)

  useEffect(() => {
    if (!chartRef.current) return

    chartInstance.current = echarts.init(chartRef.current)

    const option: echarts.EChartsOption = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => {
          if (params.seriesType === 'scatter') {
            const data = params.data
            return `
              <div style="padding: 8px;">
                <strong>${data.name}</strong><br/>
                Status: <span style="color: ${getStatusColor(data.status)}">${data.status.toUpperCase()}</span><br/>
                Clusters: ${data.clusters}<br/>
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
        silent: true,
      },
      series: [
        {
          type: 'scatter',
          coordinateSystem: 'geo',
          data: mockRegions.map((region) => ({
            name: region.name,
            value: [...region.coordinates, region.clusters],
            status: region.status,
            clusters: region.clusters,
            cpu: region.cpu,
            memory: region.memory,
            itemStyle: {
              color: getStatusColor(region.status),
              shadowBlur: 10,
              shadowColor: getStatusColor(region.status),
            },
          })),
          symbolSize: (val: number[]) => {
            return Math.max(15, Math.min(30, val[2] * 8))
          },
          itemStyle: {
            borderWidth: 2,
            borderColor: '#fff',
          },
          emphasis: {
            itemStyle: {
              borderWidth: 3,
              borderColor: '#fff',
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
              status: region.status,
              itemStyle: {
                color: getStatusColor(region.status),
              },
            })),
          symbolSize: 8,
          showEffectOn: 'render',
          rippleEffect: {
            brushType: 'stroke',
            scale: 3,
          },
        },
      ],
    }

    // Register world map (simplified version)
    fetch('https://cdn.jsdelivr.net/npm/echarts@5/map/json/world.json')
      .then((response) => response.json())
      .then((worldJson) => {
        echarts.registerMap('world', worldJson)
        chartInstance.current?.setOption(option)
      })
      .catch(() => {
        // Fallback to basic scatter without map
        const fallbackOption: echarts.EChartsOption = {
          backgroundColor: 'transparent',
          tooltip: {
            trigger: 'item',
          },
          xAxis: { type: 'value', show: false },
          yAxis: { type: 'value', show: false },
          series: [
            {
              type: 'scatter',
              data: mockRegions.map((region) => ({
                name: region.name,
                value: region.coordinates,
                itemStyle: { color: getStatusColor(region.status) },
              })),
              symbolSize: 20,
            },
          ],
        }
        chartInstance.current?.setOption(fallbackOption)
      })

    const handleResize = () => {
      chartInstance.current?.resize()
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chartInstance.current?.dispose()
    }
  }, [])

  return (
    <Card
      title="Global Infrastructure"
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
    </Card>
  )
}
