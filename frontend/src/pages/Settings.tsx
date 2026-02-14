import { useState } from 'react'
import { Card, Typography, Form, Input, Select, Switch, Button, Divider, message, Table, Space, Upload, Popconfirm, Tag, Modal } from 'antd'
import { UploadOutlined, DeleteOutlined, EyeOutlined, CheckCircleOutlined } from '@ant-design/icons'
import type { UploadFile } from 'antd/es/upload/interface'
import { useAuthStore } from '../stores/authStore'
import { useDiagramStore, type DiagramConfig } from '../stores/configStore'

const { Title, Text } = Typography

export default function Settings() {
  const { user } = useAuthStore()
  const [form] = Form.useForm()
  const { diagrams, activeDiagramId, setActiveDiagram, addDiagram, removeDiagram } = useDiagramStore()
  const [previewDiagram, setPreviewDiagram] = useState<DiagramConfig | null>(null)

  const handleSave = () => {
    message.success('Settings saved!')
  }

  const handleDiagramUpload = async (file: UploadFile) => {
    const uploadFile = file.originFileObj
    if (!uploadFile) return false

    const fileName = uploadFile.name.toLowerCase()
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

      let fileContent = content
      if (type === 'png') {
        // Keep as data URL
      } else if (type === 'drawio') {
        fileContent = btoa(content)
      } else {
        if (!content.startsWith('data:')) {
          fileContent = `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(content)))}`
        }
      }

      const newDiagram: DiagramConfig = {
        id: `diagram-${Date.now()}`,
        name: uploadFile.name.replace(/\.[^/.]+$/, ''),
        type,
        content: fileContent,
        lastUpdated: new Date().toISOString(),
        uploadedBy: user?.username || 'unknown',
      }

      addDiagram(newDiagram)
      message.success(`Diagram "${newDiagram.name}" uploaded successfully`)
    }

    if (fileName.endsWith('.png')) {
      reader.readAsDataURL(uploadFile)
    } else {
      reader.readAsText(uploadFile)
    }

    return false
  }

  const handleDeleteDiagram = (id: string) => {
    removeDiagram(id)
    message.success('Diagram deleted')
  }

  const handleSetActive = (id: string) => {
    setActiveDiagram(id)
    message.success('Diagram set as active for dashboard')
  }

  const diagramColumns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: DiagramConfig) => (
        <Space>
          {name}
          {record.id === activeDiagramId && (
            <Tag color="green" icon={<CheckCircleOutlined />}>Active</Tag>
          )}
        </Space>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Tag>{type.toUpperCase()}</Tag>
      ),
    },
    {
      title: 'Last Updated',
      dataIndex: 'lastUpdated',
      key: 'lastUpdated',
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: 'Uploaded By',
      dataIndex: 'uploadedBy',
      key: 'uploadedBy',
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: unknown, record: DiagramConfig) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => setPreviewDiagram(record)}
          >
            Preview
          </Button>
          {record.id !== activeDiagramId && (
            <Button
              type="link"
              size="small"
              onClick={() => handleSetActive(record.id)}
            >
              Set Active
            </Button>
          )}
          <Popconfirm
            title="Delete this diagram?"
            description="This action cannot be undone."
            onConfirm={() => handleDeleteDiagram(record.id)}
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              Delete
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <Title level={4}>Settings</Title>

      <Card title="Profile">
        <Form form={form} layout="vertical" initialValues={user || {}}>
          <div className="grid grid-cols-2 gap-4">
            <Form.Item label="Username" name="username">
              <Input disabled />
            </Form.Item>
            <Form.Item label="Email" name="email">
              <Input disabled />
            </Form.Item>
            <Form.Item label="Full Name" name="fullName">
              <Input />
            </Form.Item>
            <Form.Item label="Role" name="role">
              <Select disabled options={[
                { value: 'admin', label: 'Admin' },
                { value: 'internal', label: 'Internal' },
                { value: 'vendor', label: 'Vendor' },
              ]} />
            </Form.Item>
          </div>
          <Button type="primary" onClick={handleSave}>Save Profile</Button>
        </Form>
      </Card>

      {/* Infrastructure Diagrams Management */}
      <Card
        title="Infrastructure Diagrams"
        extra={
          <Upload
            accept=".drawio,.xml,.svg,.png"
            showUploadList={false}
            beforeUpload={handleDiagramUpload}
          >
            <Button type="primary" icon={<UploadOutlined />}>
              Upload Diagram
            </Button>
          </Upload>
        }
      >
        <Text type="secondary" className="mb-4 block">
          Upload draw.io diagrams (.drawio, .xml), SVG, or PNG files to display on the dashboard.
          The active diagram will be shown on the main dashboard page.
        </Text>

        <Table
          dataSource={diagrams}
          columns={diagramColumns}
          rowKey="id"
          pagination={false}
        />
      </Card>

      <Card title="Preferences">
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <Text strong>Email Notifications</Text>
              <br />
              <Text type="secondary">Receive email notifications for critical alerts</Text>
            </div>
            <Switch defaultChecked />
          </div>
          <Divider className="my-2" />
          <div className="flex justify-between items-center">
            <div>
              <Text strong>Dark Mode</Text>
              <br />
              <Text type="secondary">Use dark theme for the interface</Text>
            </div>
            <Switch />
          </div>
          <Divider className="my-2" />
          <div className="flex justify-between items-center">
            <div>
              <Text strong>Auto-refresh Dashboard</Text>
              <br />
              <Text type="secondary">Automatically refresh dashboard data</Text>
            </div>
            <Switch defaultChecked />
          </div>
        </div>
      </Card>

      <Card title="Integrations">
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <Text strong>Grafana</Text>
              <br />
              <Text type="secondary">Connected to grafana.example.com</Text>
            </div>
            <Button>Configure</Button>
          </div>
          <Divider className="my-2" />
          <div className="flex justify-between items-center">
            <div>
              <Text strong>ArgoCD</Text>
              <br />
              <Text type="secondary">Connected to argocd.example.com</Text>
            </div>
            <Button>Configure</Button>
          </div>
          <Divider className="my-2" />
          <div className="flex justify-between items-center">
            <div>
              <Text strong>Jenkins</Text>
              <br />
              <Text type="secondary">Connected to jenkins.example.com</Text>
            </div>
            <Button>Configure</Button>
          </div>
        </div>
      </Card>

      {/* Diagram Preview Modal */}
      <Modal
        open={!!previewDiagram}
        onCancel={() => setPreviewDiagram(null)}
        footer={null}
        width={800}
        title={previewDiagram?.name}
      >
        {previewDiagram && (
          <div className="space-y-4">
            <div className="flex gap-4">
              <Tag>{previewDiagram.type.toUpperCase()}</Tag>
              <Text type="secondary">
                Last updated: {new Date(previewDiagram.lastUpdated).toLocaleString()}
              </Text>
            </div>
            <div
              className="border rounded-lg bg-gray-50 p-4"
              style={{ height: 400, overflow: 'auto' }}
            >
              {previewDiagram.type === 'svg' && previewDiagram.content.startsWith('data:image/svg+xml') && (
                <div
                  dangerouslySetInnerHTML={{
                    __html: decodeURIComponent(previewDiagram.content.split(',')[1])
                  }}
                  style={{ width: '100%', height: '100%' }}
                />
              )}
              {previewDiagram.type === 'svg' && !previewDiagram.content.startsWith('data:') && (
                <div
                  dangerouslySetInnerHTML={{ __html: previewDiagram.content }}
                  style={{ width: '100%', height: '100%' }}
                />
              )}
              {previewDiagram.type === 'png' && (
                <img
                  src={previewDiagram.content}
                  alt={previewDiagram.name}
                  style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
                />
              )}
              {previewDiagram.type === 'drawio' && (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <div className="text-4xl mb-4">📊</div>
                    <Text>Draw.io diagram preview requires integration</Text>
                  </div>
                </div>
              )}
            </div>
            <Space>
              <Button
                type="primary"
                onClick={() => {
                  handleSetActive(previewDiagram.id)
                  setPreviewDiagram(null)
                }}
                disabled={previewDiagram.id === activeDiagramId}
              >
                Set as Active
              </Button>
              <Button onClick={() => setPreviewDiagram(null)}>Close</Button>
            </Space>
          </div>
        )}
      </Modal>
    </div>
  )
}
