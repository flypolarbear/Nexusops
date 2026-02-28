import { useEffect, useRef, useState } from 'react'
import { Card, Button, Upload, message, Space, Modal, Typography, Spin, Dropdown, Empty } from 'antd'
import {
  UploadOutlined,
  ReloadOutlined,
  FullscreenOutlined,
  DownloadOutlined,
  FileImageOutlined,
} from '@ant-design/icons'
import type { UploadFile } from 'antd/es/upload/interface'
import { useDiagramStore, type DiagramConfig } from '../stores/configStore'

const { Text } = Typography

interface DrawioRendererProps {
  height?: number
  showControls?: boolean
}

export default function DrawioRenderer({ height = 400, showControls = true }: DrawioRendererProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [loading, setLoading] = useState(false)
  const [fullscreen, setFullscreen] = useState(false)
  const { diagrams, activeDiagramId, setActiveDiagram, addDiagram } = useDiagramStore()

  const activeDiagram = diagrams.find((d) => d.id === activeDiagramId)

  useEffect(() => {
    renderDiagram()
  }, [activeDiagram])

  const renderDiagram = async () => {
    if (!containerRef.current || !activeDiagram) return

    setLoading(true)
    containerRef.current.innerHTML = ''

    try {
      if (activeDiagram.type === 'drawio') {
        // Render draw.io XML using mxGraph
        await renderDrawioXml(activeDiagram.content)
      } else if (activeDiagram.type === 'svg') {
        // Render SVG directly
        await renderSvg(activeDiagram.content)
      } else if (activeDiagram.type === 'png') {
        // Render PNG image
        await renderPng(activeDiagram.content)
      }
    } catch (error) {
      console.error('Failed to render diagram:', error)
      containerRef.current.innerHTML = `
        <div class="flex items-center justify-center h-full text-red-500">
          Failed to render diagram
        </div>
      `
    }

    setLoading(false)
  }

  const renderDrawioXml = async (content: string) => {
    if (!containerRef.current) return

    // For draw.io XML files, we can either:
    // 1. Use the draw.io viewer library (graphviewer)
    // 2. Parse and render with mxGraph
    // 3. Convert to SVG server-side

    // For demo, we'll show a message and render a placeholder
    // In production, you'd use: https://www.drawio.com/blog/embed-html

    try {
      // Decode base64 content
      const xmlContent = atob(content)
      const parser = new DOMParser()
      const xmlDoc = parser.parseFromString(xmlContent, 'text/xml')

      // Check if it's valid draw.io XML
      const mxfile = xmlDoc.querySelector('mxfile')
      if (!mxfile) {
        throw new Error('Invalid draw.io file')
      }

      // For now, display an embed link
      // In production, integrate with draw.io viewer
      containerRef.current.innerHTML = `
        <div class="flex flex-col items-center justify-center h-full bg-gray-50 rounded-lg p-4">
          <div class="text-4xl mb-4">📊</div>
          <div class="text-lg font-medium mb-2">Draw.io Diagram Loaded</div>
          <div class="text-sm text-gray-500 mb-4">File contains ${xmlContent.length} bytes of diagram data</div>
          <div class="text-xs text-gray-400">
            To render draw.io files, integrate with:
            <br/>
            <a href="https://www.drawio.com/blog/embed-html" target="_blank" class="text-blue-500">draw.io Embed Viewer</a>
          </div>
        </div>
      `
    } catch {
      // If decoding fails, try as raw XML
      containerRef.current.innerHTML = `
        <div class="flex items-center justify-center h-full">
          <div class="text-center">
            <div class="text-2xl mb-2">📐</div>
            <div class="text-gray-500">Draw.io diagram (XML format)</div>
            <div class="text-xs text-gray-400 mt-1">Preview requires draw.io integration</div>
          </div>
        </div>
      `
    }
  }

  const renderSvg = async (content: string) => {
    if (!containerRef.current) return

    try {
      // Check if it's a data URL or raw SVG
      if (content.startsWith('data:image/svg+xml,')) {
        // URL-encoded SVG data URL
        const svgContent = decodeURIComponent(content.replace('data:image/svg+xml,', ''))
        containerRef.current.innerHTML = svgContent
      } else if (content.startsWith('data:image/svg+xml;base64,')) {
        // Base64-encoded SVG data URL (UTF-8)
        const base64Content = content.replace('data:image/svg+xml;base64,', '')
        // Decode base64 to bytes, then decode UTF-8 properly
        const binaryString = atob(base64Content)
        const bytes = new Uint8Array(binaryString.length)
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i)
        }
        const svgContent = new TextDecoder('utf-8').decode(bytes)
        containerRef.current.innerHTML = svgContent
        // Raw SVG content
        containerRef.current.innerHTML = content
      } else if (content.startsWith('http')) {
        // URL to SVG
        containerRef.current.innerHTML = `<img src="${content}" style="width: 100%; height: 100%; object-fit: contain;" />`
        return // Don't try to modify SVG attributes for img tags
      }

      // Make SVG responsive
      const svg = containerRef.current.querySelector('svg')
      if (svg) {
        svg.style.width = '100%'
        svg.style.height = '100%'
        svg.removeAttribute('width')
        svg.removeAttribute('height')
      }
    } catch (error) {
      console.error('Failed to render SVG:', error)
      containerRef.current.innerHTML = `
        <div class="flex items-center justify-center h-full text-red-500">
          Failed to render SVG diagram
        </div>
      `
    }
  }

  const renderPng = async (content: string) => {
    if (!containerRef.current) return

    if (content.startsWith('data:image/png') || content.startsWith('http')) {
      containerRef.current.innerHTML = `<img src="${content}" style="width: 100%; height: 100%; object-fit: contain;" />`
    } else {
      // Assume it's base64 without prefix
      containerRef.current.innerHTML = `<img src="data:image/png;base64,${content}" style="width: 100%; height: 100%; object-fit: contain;" />`
    }
  }

  const handleUpload = async (file: File) => {
  const fileName = file.name.toLowerCase()
  const reader = new FileReader()

  reader.onload = (e) => {
      const content = e.target?.result as string

      let type: 'drawio' | 'svg' | 'png' = 'svg'
      if (fileName.endsWith('.drawio') || fileName.endsWith('.xml')) {
        type = 'drawio'
      } else if (fileName.endsWith('.png')) {
        type = 'png'
      } else if (fileName.endsWith('.svg')) {
        type = 'svg'
      }

      // For binary files (PNG), use base64
      let fileContent = content
      if (type === 'png') {
        fileContent = content // Already base64 from readAsDataURL
      } else if (type === 'drawio') {
        // For XML files, encode to base64
        fileContent = btoa(content)
      } else {
        // For SVG, use as-is or encode as data URL
        if (!content.startsWith('data:')) {
          fileContent = `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(content)))}`
        }
      }

      const newDiagram: DiagramConfig = {
        id: `diagram-${Date.now()}`,
        name: file.name.replace(/\.[^/.]+$/, ''),
        type,
        content: fileContent,
        lastUpdated: new Date().toISOString(),
        uploadedBy: 'current-user',
      }

      addDiagram(newDiagram)
      setActiveDiagram(newDiagram.id)
      message.success(`Diagram "${newDiagram.name}" uploaded successfully`)
    }

    if (fileName.endsWith('.png')) {
      reader.readAsDataURL(file)
    } else {
      reader.readAsText(file)
    }

    return false // Prevent default upload behavior
  }

  const handleExport = () => {
    if (!activeDiagram) return

    const link = document.createElement('a')
    link.download = `${activeDiagram.name}.${activeDiagram.type}`
    link.href = activeDiagram.content
    link.click()
  }

  const diagramOptions = diagrams.map((d) => ({
    key: d.id,
    label: (
      <div className="flex items-center justify-between">
        <span>{d.name}</span>
        <Text type="secondary" className="text-xs">
          .{d.type}
        </Text>
      </div>
    ),
    onClick: () => setActiveDiagram(d.id),
  }))

  if (!activeDiagram && diagrams.length === 0) {
    return (
      <Card
        title="Infrastructure Diagram"
        className="h-full"
        extra={
          showControls && (
            <Upload
              accept=".drawio,.xml,.svg,.png"
              showUploadList={false}
              beforeUpload={handleUpload}
            >
              <Button icon={<UploadOutlined />}>Upload Diagram</Button>
            </Upload>
          )
        }
      >
        <Empty
          description="No infrastructure diagram configured"
          className="flex flex-col items-center justify-center"
          style={{ height: height - 100 }}
        >
          <Upload
            accept=".drawio,.xml,.svg,.png"
            showUploadList={false}
            beforeUpload={handleUpload}
          >
            <Button type="primary" icon={<UploadOutlined />}>
              Upload draw.io File
            </Button>
          </Upload>
          <Text type="secondary" className="mt-3 text-xs">
            Supports .drawio, .xml, .svg, .png formats
          </Text>
        </Empty>
      </Card>
    )
  }

  const cardContent = (
    <Card
      title={
        <div className="flex items-center gap-2">
          <FileImageOutlined />
          <Dropdown menu={{ items: diagramOptions }} trigger={['click']}>
            <span className="cursor-pointer hover:text-primary-500">
              {activeDiagram?.name || 'Infrastructure Diagram'}
            </span>
          </Dropdown>
        </div>
      }
      className="h-full"
      extra={
        showControls && (
          <Space>
            <Tooltip title="Refresh">
              <Button type="text" icon={<ReloadOutlined />} onClick={renderDiagram} />
            </Tooltip>
            <Tooltip title="Export">
              <Button type="text" icon={<DownloadOutlined />} onClick={handleExport} />
            </Tooltip>
            <Tooltip title="Fullscreen">
              <Button type="text" icon={<FullscreenOutlined />} onClick={() => setFullscreen(true)} />
            </Tooltip>
            <Upload
              accept=".drawio,.xml,.svg,.png"
              showUploadList={false}
              beforeUpload={handleUpload}
            >
              <Tooltip title="Upload New">
                <Button type="text" icon={<UploadOutlined />} />
              </Tooltip>
            </Upload>
          </Space>
        )
      }
    >
      <Spin spinning={loading}>
        <div
          ref={containerRef}
          style={{ height: height - 100, overflow: 'hidden' }}
          className="border rounded-lg bg-gray-50"
        />
      </Spin>
      {activeDiagram && (
        <div className="mt-2 flex items-center justify-between text-xs text-gray-400">
          <span>Last updated: {new Date(activeDiagram.lastUpdated).toLocaleString()}</span>
          <span>By: {activeDiagram.uploadedBy}</span>
        </div>
      )}
    </Card>
  )

  return (
    <>
      {cardContent}

      <Modal
        open={fullscreen}
        onCancel={() => setFullscreen(false)}
        footer={null}
        width="90vw"
        style={{ top: 20 }}
        title={
          <div className="flex items-center gap-2">
            <FileImageOutlined />
            {activeDiagram?.name}
          </div>
        }
      >
        <div
          ref={(el) => {
            if (el && fullscreen && activeDiagram) {
              // Re-render in fullscreen modal
              if (activeDiagram.type === 'svg') {
                if (activeDiagram.content.startsWith('data:image/svg+xml')) {
                  const svgContent = decodeURIComponent(activeDiagram.content.split(',')[1])
                  el.innerHTML = svgContent
                } else {
                  el.innerHTML = activeDiagram.content
                }
              } else if (activeDiagram.type === 'png') {
                el.innerHTML = `<img src="${activeDiagram.content}" style="width: 100%; height: 100%; object-fit: contain;" />`
              }
            }
          }}
          style={{ height: 'calc(100vh - 150px)', overflow: 'auto' }}
          className="border rounded-lg bg-gray-50 p-4"
        />
      </Modal>
    </>
  )
}

// Tooltip component for antd
function Tooltip({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <span title={title}>
      {children}
    </span>
  )
}
