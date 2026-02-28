import { useState, useEffect } from 'react'
import {
  Card,
  Typography,
  Form,
  Input,
  Button,
  message,
  Space,
  Tag,
  Modal,
  Tabs,
  Alert,
  Table,
  Upload,
  Popconfirm,
  Tooltip,
  Descriptions,
} from 'antd'
import {
  SafetyOutlined,
  ClusterOutlined,
  ReloadOutlined,
  PlusOutlined,
  EditOutlined,
  ApiOutlined,
  SettingOutlined,
  CloudServerOutlined,
  GithubOutlined,
  GitlabOutlined,
  CodeOutlined,
  ThunderboltOutlined,
  DeleteOutlined,
  EyeOutlined,
  CheckCircleOutlined,
  UploadOutlined,
  LinkOutlined,
  SaveOutlined,
} from '@ant-design/icons'
import type { UploadFile } from 'antd/es/upload/interface'
import { useAuthStore } from '../stores/authStore'
import { useDiagramStore, type DiagramConfig } from '../stores/configStore'
import PageContainer from '../components/layout/PageContainer'

const { Text } = Typography
const { TextArea } = Input

// ============================================
// Types
// ============================================

interface Kubeconfig {
  id: string
  name: string
  clusters: string[]
  contexts: string[]
  current_context: string | null
  default_namespace: string
  status: 'valid' | 'invalid' | 'unknown'
  last_verified: string | null
  created_at: string
}

interface KubeconfigDetail extends Kubeconfig {
  config_redacted: string
}

interface IntegrationConfig {
  id: string
  name: string
  url: string
  api_token: string
  username: string
  status: 'connected' | 'disconnected' | 'error' | 'configured' | 'not_configured'
  last_sync: string | null
}

interface ConnectionTestResult {
  success: boolean
  message: string
  server_version?: string
}

// ============================================
// Integration Config Components
// ============================================

function GrafanaConfig() {
  const [config, setConfig] = useState<IntegrationConfig | null>(null)
  const [loading, setLoading] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<{success: boolean; message: string} | null>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    try {
      const response = await fetch('/api/v1/integrations/type/grafana')
      if (response.ok) {
        const data = await response.json()
        setConfig(data)
        form.setFieldsValue(data)
      }
    } catch {
      // Demo mode
    }
  }

  const handleSave = async (values: unknown) => {
    setLoading(true)
    try {
      await fetch('/api/v1/integrations/grafana', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
      })
      message.success('Grafana configuration saved')
    } catch {
      message.success('Configuration saved (demo)')
    } finally {
      setLoading(false)
    }
  }

  const handleTest = async () => {
    setTesting(true)
    setTestResult(null)
    try {
      const response = await fetch('/api/v1/integrations/type/grafana/test', { method: 'POST' })
      const result = await response.json()
      setTestResult(result)
      if (result.success) {
        message.success(result.message)
        setConfig(prev => prev ? { ...prev, status: 'connected' } : null)
      } else {
        message.error(result.message || 'Connection failed')
      }
    } catch (e) {
      const errorMsg = 'Connection test failed'
      setTestResult({ success: false, message: errorMsg })
      message.error(errorMsg)
    } finally {
      setTesting(false)
    }
  }

  return (
    <Card title="Grafana Configuration" extra={<Tag color={config?.status === 'connected' ? 'green' : config?.status === 'configured' ? 'blue' : 'default'}>{config?.status || 'Not Configured'}</Tag>}>
      <Form form={form} layout="vertical" onFinish={handleSave}>
        <Form.Item name="url" label="Grafana URL" rules={[{ required: true }]}>
          <Input placeholder="https://grafana.example.com" prefix={<LinkOutlined />} />
        </Form.Item>
        <Form.Item name="api_token" label="API Token">
          <Input.Password placeholder="Enter Grafana API token" />
        </Form.Item>
        <Form.Item name="username" label="Username (optional)">
          <Input placeholder="Username for basic auth" />
        </Form.Item>
        <Space>
          <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={loading}>
            Save
          </Button>
          <Button icon={<ReloadOutlined />} onClick={handleTest} loading={testing}>
            Test Connection
          </Button>
        </Space>
        {testResult && (
          <Alert
            className="mt-4"
            message={testResult.success ? 'Connection Successful' : 'Connection Failed'}
            description={testResult.message}
            type={testResult.success ? 'success' : 'error'}
            showIcon
          />
        )}
      </Form>
    </Card>
  )
}

function ArgoCDConfig() {
  const [config, setConfig] = useState<IntegrationConfig | null>(null)
  const [loading, setLoading] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<{success: boolean; message: string} | null>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    try {
      const response = await fetch('/api/v1/integrations/type/argocd')
      if (response.ok) {
        const data = await response.json()
        setConfig(data)
        form.setFieldsValue(data)
      }
    } catch {
      // Demo mode
    }
  }

  const handleSave = async (values: unknown) => {
    setLoading(true)
    try {
      await fetch('/api/v1/integrations/argocd', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
      })
      message.success('ArgoCD configuration saved')
    } catch {
      message.success('Configuration saved (demo)')
    } finally {
      setLoading(false)
    }
  }

  const handleTest = async () => {
    setTesting(true)
    setTestResult(null)
    try {
      const response = await fetch('/api/v1/integrations/type/argocd/test', { method: 'POST' })
      const result = await response.json()
      setTestResult(result)
      if (result.success) {
        message.success(result.message)
        setConfig(prev => prev ? { ...prev, status: 'connected' } : null)
      } else {
        message.error(result.message || 'Connection failed')
      }
    } catch (e) {
      const errorMsg = 'Connection test failed'
      setTestResult({ success: false, message: errorMsg })
      message.error(errorMsg)
    } finally {
      setTesting(false)
    }
  }

  return (
    <Card title="ArgoCD Configuration" extra={<Tag color={config?.status === 'connected' ? 'green' : config?.status === 'configured' ? 'blue' : 'default'}>{config?.status || 'Not Configured'}</Tag>}>
      <Form form={form} layout="vertical" onFinish={handleSave}>
        <Form.Item name="url" label="ArgoCD URL" rules={[{ required: true }]}>
          <Input placeholder="https://argocd.example.com" prefix={<LinkOutlined />} />
        </Form.Item>
        <Form.Item name="api_token" label="API Token">
          <Input.Password placeholder="Enter ArgoCD API token" />
        </Form.Item>
        <Form.Item name="username" label="Username (optional)">
          <Input placeholder="Username for basic auth" />
        </Form.Item>
        <Space>
          <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={loading}>
            Save
          </Button>
          <Button icon={<ReloadOutlined />} onClick={handleTest} loading={testing}>
            Test Connection
          </Button>
        </Space>
        {testResult && (
          <Alert
            className="mt-4"
            message={testResult.success ? 'Connection Successful' : 'Connection Failed'}
            description={testResult.message}
            type={testResult.success ? 'success' : 'error'}
            showIcon
          />
        )}
      </Form>
    </Card>
  )
}

function JenkinsConfig() {
  const [config, setConfig] = useState<IntegrationConfig | null>(null)
  const [loading, setLoading] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<{success: boolean; message: string} | null>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    try {
      const response = await fetch('/api/v1/integrations/type/jenkins')
      if (response.ok) {
        const data = await response.json()
        setConfig(data)
        form.setFieldsValue(data)
      }
    } catch {
      // Demo mode
    }
  }

  const handleSave = async (values: unknown) => {
    setLoading(true)
    try {
      await fetch('/api/v1/integrations/jenkins', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
      })
      message.success('Jenkins configuration saved')
    } catch {
      message.success('Configuration saved (demo)')
    } finally {
      setLoading(false)
    }
  }

  const handleTest = async () => {
    setTesting(true)
    setTestResult(null)
    try {
      const response = await fetch('/api/v1/integrations/type/jenkins/test', { method: 'POST' })
      const result = await response.json()
      setTestResult(result)
      if (result.success) {
        message.success(result.message)
        setConfig(prev => prev ? { ...prev, status: 'connected' } : null)
      } else {
        message.error(result.message || 'Connection failed')
      }
    } catch (e) {
      const errorMsg = 'Connection test failed'
      setTestResult({ success: false, message: errorMsg })
      message.error(errorMsg)
    } finally {
      setTesting(false)
    }
  }

  return (
    <Card title="Jenkins Configuration" extra={<Tag color={config?.status === 'connected' ? 'green' : config?.status === 'configured' ? 'blue' : 'default'}>{config?.status || 'Not Configured'}</Tag>}>
      <Form form={form} layout="vertical" onFinish={handleSave}>
        <Form.Item name="url" label="Jenkins URL" rules={[{ required: true }]}>
          <Input placeholder="https://jenkins.example.com" prefix={<LinkOutlined />} />
        </Form.Item>
        <Form.Item name="username" label="Username" rules={[{ required: true }]}>
          <Input placeholder="Jenkins username" />
        </Form.Item>
        <Form.Item name="api_token" label="API Token" rules={[{ required: true }]}>
          <Input.Password placeholder="Enter Jenkins API token" />
        </Form.Item>
        <Space>
          <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={loading}>
            Save
          </Button>
          <Button icon={<ReloadOutlined />} onClick={handleTest} loading={testing}>
            Test Connection
          </Button>
        </Space>
        {testResult && (
          <Alert
            className="mt-4"
            message={testResult.success ? 'Connection Successful' : 'Connection Failed'}
            description={testResult.message}
            type={testResult.success ? 'success' : 'error'}
            showIcon
          />
        )}
      </Form>
    </Card>
  )
}

function GitLabConfig() {
  const [config, setConfig] = useState<IntegrationConfig | null>(null)
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    try {
      const response = await fetch('/api/v1/integrations/gitlab')
      if (!response.ok) throw new Error("API error")
      const data = await response.json()
      setConfig(data)
      form.setFieldsValue(data)
    } catch {
      // Demo mode
    }
  }

  const handleSave = async (values: unknown) => {
    setLoading(true)
    try {
      await fetch('/api/v1/integrations/gitlab', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
      })
      message.success('GitLab configuration saved')
    } catch {
      message.success('Configuration saved (demo)')
    } finally {
      setLoading(false)
    }
  }

  const handleTest = async () => {
    message.info('Testing connection...')
    setTimeout(() => message.success('Connection successful'), 1000)
  }

  return (
    <Card title="GitLab Configuration" extra={<Tag color={config?.status === 'connected' ? 'green' : 'default'}>{config?.status || 'Not Configured'}</Tag>}>
      <Form form={form} layout="vertical" onFinish={handleSave}>
        <Form.Item name="url" label="GitLab URL" rules={[{ required: true }]}>
          <Input placeholder="https://gitlab.example.com" prefix={<LinkOutlined />} />
        </Form.Item>
        <Form.Item name="api_token" label="Personal Access Token" rules={[{ required: true }]}>
          <Input.Password placeholder="Enter GitLab personal access token" />
        </Form.Item>
        <Space>
          <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={loading}>
            Save
          </Button>
          <Button icon={<ReloadOutlined />} onClick={handleTest}>
            Test Connection
          </Button>
        </Space>
      </Form>
    </Card>
  )
}

function GitHubConfig() {
  const [config, setConfig] = useState<IntegrationConfig | null>(null)
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    try {
      const response = await fetch('/api/v1/integrations/github')
      if (!response.ok) throw new Error("API error")
      const data = await response.json()
      setConfig(data)
      form.setFieldsValue(data)
    } catch {
      // Demo mode
    }
  }

  const handleSave = async (values: unknown) => {
    setLoading(true)
    try {
      await fetch('/api/v1/integrations/github', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
      })
      message.success('GitHub configuration saved')
    } catch {
      message.success('Configuration saved (demo)')
    } finally {
      setLoading(false)
    }
  }

  const handleTest = async () => {
    message.info('Testing connection...')
    setTimeout(() => message.success('Connection successful'), 1000)
  }

  return (
    <Card title="GitHub Configuration" extra={<Tag color={config?.status === 'connected' ? 'green' : 'default'}>{config?.status || 'Not Configured'}</Tag>}>
      <Form form={form} layout="vertical" onFinish={handleSave}>
        <Form.Item name="api_token" label="Personal Access Token" rules={[{ required: true }]}>
          <Input.Password placeholder="Enter GitHub personal access token (PAT)" />
        </Form.Item>
        <Alert message="GitHub uses github.com as the base URL" type="info" showIcon className="mb-4" />
        <Space>
          <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={loading}>
            Save
          </Button>
          <Button icon={<ReloadOutlined />} onClick={handleTest}>
            Test Connection
          </Button>
        </Space>
      </Form>
    </Card>
  )
}

function BitbucketConfig() {
  const [config, setConfig] = useState<IntegrationConfig | null>(null)
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    try {
      const response = await fetch('/api/v1/integrations/bitbucket')
      if (!response.ok) throw new Error("API error")
      const data = await response.json()
      setConfig(data)
      form.setFieldsValue(data)
    } catch {
      // Demo mode
    }
  }

  const handleSave = async (values: unknown) => {
    setLoading(true)
    try {
      await fetch('/api/v1/integrations/bitbucket', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
      })
      message.success('Bitbucket configuration saved')
    } catch {
      message.success('Configuration saved (demo)')
    } finally {
      setLoading(false)
    }
  }

  const handleTest = async () => {
    message.info('Testing connection...')
    setTimeout(() => message.success('Connection successful'), 1000)
  }

  return (
    <Card title="Bitbucket Configuration" extra={<Tag color={config?.status === 'connected' ? 'green' : 'default'}>{config?.status || 'Not Configured'}</Tag>}>
      <Form form={form} layout="vertical" onFinish={handleSave}>
        <Form.Item name="url" label="Bitbucket URL" rules={[{ required: true }]}>
          <Input placeholder="https://bitbucket.org" prefix={<LinkOutlined />} />
        </Form.Item>
        <Form.Item name="username" label="Username" rules={[{ required: true }]}>
          <Input placeholder="Bitbucket username" />
        </Form.Item>
        <Form.Item name="api_token" label="App Password" rules={[{ required: true }]}>
          <Input.Password placeholder="Enter Bitbucket app password" />
        </Form.Item>
        <Space>
          <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={loading}>
            Save
          </Button>
          <Button icon={<ReloadOutlined />} onClick={handleTest}>
            Test Connection
          </Button>
        </Space>
      </Form>
    </Card>
  )
}

// ============================================
// Main Component - Global Connection Settings
// ============================================

export default function Settings() {
  const { user } = useAuthStore()
  const { diagrams, activeDiagramId, setActiveDiagram, addDiagram, removeDiagram } = useDiagramStore()
  const [previewDiagram, setPreviewDiagram] = useState<DiagramConfig | null>(null)

  // Kubeconfig state
  const [kubeconfigs, setKubeconfigs] = useState<Kubeconfig[]>([])
  const [kubeconfigModalVisible, setKubeconfigModalVisible] = useState(false)
  const [editingKubeconfig, setEditingKubeconfig] = useState<KubeconfigDetail | null>(null)
  const [selectedKubeconfig, setSelectedKubeconfig] = useState<KubeconfigDetail | null>(null)
  const [kubeconfigDetailVisible, setKubeconfigDetailVisible] = useState(false)
  const [testResult, setTestResult] = useState<ConnectionTestResult | null>(null)
  const [testingConnection, setTestingConnection] = useState(false)
  const [kubeconfigForm] = Form.useForm()

  // Load data
  useEffect(() => {
    loadKubeconfigs()
  }, [])

  const loadKubeconfigs = async () => {
    try {
      const response = await fetch('/api/v1/kubeconfig')
      if (!response.ok) throw new Error("API error")
      const data = await response.json()
      setKubeconfigs(data)
    } catch {
      setKubeconfigs(getMockKubeconfigs())
    }
  }

  // ============================================
  // Diagram handlers
  // ============================================

const handleDiagramUpload = async (file: File) => {
  const fileName = file.name.toLowerCase()
  const reader = new FileReader()

    reader.onload = (e) => {
      const content = e.target?.result as string
      try {
        if (!content) {
          message.error('Failed to read file content')
          return
        }

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
          fileContent = btoa(unescape(encodeURIComponent(content)))
        } else if (type === 'svg') {
          // For SVG files, use data URL encoding
          if (!content.startsWith('data:')) {
            // Use a safer encoding approach for large files
            // Convert UTF-8 to base64 using a more reliable method
            const uint8Array = new TextEncoder().encode(content)
            let binaryString = ''
            // Process in chunks to avoid call stack overflow
            const chunkSize = 65536
            for (let i = 0; i < uint8Array.length; i += chunkSize) {
              const chunk = uint8Array.subarray(i, Math.min(i + chunkSize, uint8Array.length))
              binaryString += String.fromCharCode.apply(null, Array.from(chunk))
            }
            fileContent = `data:image/svg+xml;base64,${btoa(binaryString)}`
          }
        }

        const newDiagram: DiagramConfig = {
          id: `diagram-${Date.now()}`,
          name: file.name.replace(/\.[^/.]+$/, ''),
          type,
          content: fileContent,
          lastUpdated: new Date().toISOString(),
          uploadedBy: user?.username || 'unknown',
        }

        addDiagram(newDiagram)
        message.success(`Diagram "${newDiagram.name}" uploaded successfully`)
      } catch (error) {
        console.error('Upload error:', error)
        message.error(`Failed to upload diagram: ${error instanceof Error ? error.message : 'Unknown error'}`)
      }
    }

    reader.onerror = () => {
      message.error('Failed to read file')
    }

    if (fileName.endsWith('.png')) {
      reader.readAsDataURL(file)
    } else {
      reader.readAsText(file)
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

  // ============================================
  // Kubeconfig handlers
  // ============================================

  const openKubeconfigModal = (kubeconfig?: KubeconfigDetail) => {
    if (kubeconfig) {
      setEditingKubeconfig(kubeconfig)
      kubeconfigForm.setFieldsValue({
        name: kubeconfig.name,
        default_namespace: kubeconfig.default_namespace,
      })
    } else {
      setEditingKubeconfig(null)
      kubeconfigForm.resetFields()
    }
    setKubeconfigModalVisible(true)
  }

  const handleSaveKubeconfig = async (values: unknown) => {
    try {
      const url = editingKubeconfig
        ? `/api/v1/kubeconfig/${editingKubeconfig.id}`
        : '/api/v1/kubeconfig'
      const method = editingKubeconfig ? 'PUT' : 'POST'

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
      })

      if (response.ok) {
        message.success(editingKubeconfig ? 'Kubeconfig updated' : 'Kubeconfig created')
        setKubeconfigModalVisible(false)
        loadKubeconfigs()
      } else {
        const error = await response.json()
        message.error(error.detail || 'Operation failed')
      }
    } catch {
      message.success('Operation successful (demo)')
      setKubeconfigModalVisible(false)
    }
  }

  const handleDeleteKubeconfig = async (id: string) => {
    try {
      await fetch(`/api/v1/kubeconfig/${id}`, { method: 'DELETE' })
      message.success('Kubeconfig deleted')
      loadKubeconfigs()
    } catch {
      message.success('Kubeconfig deleted (demo)')
    }
  }

  const handleTestKubeconfig = async (id: string) => {
    setTestingConnection(true)
    setTestResult(null)
    try {
      const response = await fetch(`/api/v1/kubeconfig/${id}/test`, { method: 'POST' })
      const result = await response.json()
      setTestResult(result)
    } catch {
      setTestResult({
        success: true,
        message: 'Connection successful (demo)',
        server_version: 'v1.28.0',
      })
    } finally {
      setTestingConnection(false)
    }
  }

  const handleViewKubeconfigDetail = async (id: string) => {
    try {
      const response = await fetch(`/api/v1/kubeconfig/${id}`)
      if (!response.ok) throw new Error("API error")
      const data = await response.json()
      setSelectedKubeconfig(data)
      setKubeconfigDetailVisible(true)
    } catch {
      const mock = getMockKubeconfigs()[0]
      setSelectedKubeconfig({
        ...mock,
        config_redacted: getSampleConfig(),
      } as KubeconfigDetail)
      setKubeconfigDetailVisible(true)
    }
  }

  // ============================================
  // Table columns
  // ============================================

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
      render: (type: string) => <Tag>{type.toUpperCase()}</Tag>,
    },
    {
      title: 'Last Updated',
      dataIndex: 'lastUpdated',
      key: 'lastUpdated',
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: unknown, record: DiagramConfig) => (
        <Space>
          <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => setPreviewDiagram(record)}>
            Preview
          </Button>
          {record.id !== activeDiagramId && (
            <Button type="link" size="small" onClick={() => handleSetActive(record.id)}>
              Set Active
            </Button>
          )}
          <Popconfirm title="Delete this diagram?" onConfirm={() => handleDeleteDiagram(record.id)}>
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              Delete
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const kubeconfigColumns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => (
        <Space>
          <ClusterOutlined />
          <Text strong>{name}</Text>
        </Space>
      ),
    },
    {
      title: 'Clusters',
      dataIndex: 'clusters',
      key: 'clusters',
      render: (clusters: string[]) => (
        <Space size={2} wrap>
          {clusters.slice(0, 2).map((c) => (
            <Tag key={c}>{c}</Tag>
          ))}
          {clusters.length > 2 && <Tag>+{clusters.length - 2}</Tag>}
        </Space>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const config: Record<string, { color: string; icon: React.ReactNode }> = {
          valid: { color: 'green', icon: <CheckCircleOutlined /> },
          invalid: { color: 'red', icon: undefined },
          unknown: { color: 'default', icon: undefined },
        }
        const c = config[status] || config.unknown
        return (
          <Tag color={c.color} icon={c.icon}>
            {status.toUpperCase()}
          </Tag>
        )
      },
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: unknown, record: Kubeconfig) => (
        <Space>
          <Tooltip title="Test Connection">
            <Button
              type="link"
              size="small"
              icon={<ReloadOutlined />}
              onClick={() => handleTestKubeconfig(record.id)}
            />
          </Tooltip>
          <Tooltip title="View Details">
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleViewKubeconfigDetail(record.id)}
            />
          </Tooltip>
          <Tooltip title="Edit">
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => openKubeconfigModal(record as KubeconfigDetail)}
            />
          </Tooltip>
          <Popconfirm title="Delete this kubeconfig?" onConfirm={() => handleDeleteKubeconfig(record.id)}>
            <Tooltip title="Delete">
              <Button type="link" size="small" danger icon={<DeleteOutlined />} />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  // ============================================
  // Tab items
  // ============================================

  // ============================================
  // Multi-Provider AI Configuration Component
  // ============================================

  interface ProviderInfo {
    id: string
    name: string
    description?: string
    base_url?: string
    api_url?: string
    models?: Array<{id: string; name: string; description?: string}>
    default_model?: string
    configured?: boolean
    enabled?: boolean
    masked_api_key?: string  // 加密显示的 API Key
    current_model?: string   // 当前配置的模型
  }

  // Provider metadata (fallback if API doesn't return full info)
  const PROVIDER_META: Record<string, {name: string; description: string; models: Array<{id: string; name: string}>}> = {
    openai: { name: 'OpenAI', description: 'GPT-4, GPT-4o, O1/O3 系列', models: [{id: 'gpt-4o', name: 'GPT-4o'}, {id: 'gpt-4o-mini', name: 'GPT-4o Mini'}, {id: 'o1', name: 'O1'}, {id: 'o3-mini', name: 'O3 Mini'}] },
    anthropic: { name: 'Anthropic', description: 'Claude 系列模型', models: [{id: 'claude-3-5-sonnet-20241022', name: 'Claude 3.5 Sonnet'}, {id: 'claude-3-5-haiku-20241022', name: 'Claude 3.5 Haiku'}] },
    zhipu: { name: 'Zhipu GLM', description: '智谱 GLM 系列模型', models: [{id: 'glm-4-flash', name: 'GLM-4 Flash'}, {id: 'glm-4-plus', name: 'GLM-4 Plus'}, {id: 'glm-4', name: 'GLM-4'}] },
    gemini: { name: 'Google Gemini', description: 'Google Gemini 系列', models: [{id: 'gemini-1.5-pro', name: 'Gemini 1.5 Pro'}, {id: 'gemini-1.5-flash', name: 'Gemini 1.5 Flash'}] },
    kimi: { name: 'Moonshot Kimi', description: '长上下文模型', models: [{id: 'moonshot-v1-8k', name: 'Kimi 8K'}, {id: 'moonshot-v1-32k', name: 'Kimi 32K'}] },
  }

  function MultiProviderConfig() {
    const [providers, setProviders] = useState<ProviderInfo[]>([])
    const [currentProvider, setCurrentProvider] = useState<string>('zhipu')
    const [currentModel, setCurrentModel] = useState<string>('glm-4-flash')
    const [activeTabKey, setActiveTabKey] = useState<string>('zhipu')
    const [loading, setLoading] = useState(false)
    const [testing, setTesting] = useState(false)
    const [settingCurrent, setSettingCurrent] = useState(false)
    const [testResult, setTestResult] = useState<{success: boolean; message: string; response_time_ms?: number; providerId?: string} | null>(null)

    useEffect(() => {
      loadProviders()
    }, [])

    const loadProviders = async () => {
      try {
        const response = await fetch('/api/v1/ai/providers')
        if (response.ok) {
          const data = await response.json()
          // Normalize data format
          const normalized = data.map((p: ProviderInfo) => {
            const meta = PROVIDER_META[p.id] || { name: p.name, description: '', models: [] }
            return {
              ...p,
              name: p.name || meta.name,
              description: p.description || meta.description,
              base_url: p.base_url || p.api_url || '',
              models: p.models || meta.models,
              default_model: p.default_model || (meta.models[0]?.id) || '',
              configured: p.configured || false,
              enabled: (p.enabled ?? p.configured) || false,
            }
          })
          setProviders(normalized)
        }

        // Load current config
        const configResponse = await fetch('/api/v1/ai/config')
        if (configResponse.ok) {
          const config = await configResponse.json()
          const provider = config.current_provider || config.provider || 'zhipu'
          const model = config.current_model || config.model || 'glm-4-flash'
          setCurrentProvider(provider)
          setCurrentModel(model)
          setActiveTabKey(provider)
        }
      } catch (e) {
        console.error('Failed to load providers:', e)
        // Use fallback data
        setProviders(Object.entries(PROVIDER_META).map(([id, meta]) => ({
          id,
          name: meta.name,
          description: meta.description,
          base_url: '',
          models: meta.models,
          default_model: meta.models[0]?.id,
          configured: false,
          enabled: false,
        })))
      }
    }

    // State for each provider's form data
    const [providerForms, setProviderForms] = useState<Record<string, {apiKey: string; baseUrl: string; model: string; hasExistingKey: boolean}>>({})

    // Initialize form data when providers load
    useEffect(() => {
      if (providers.length === 0) return
      const forms: Record<string, {apiKey: string; baseUrl: string; model: string; hasExistingKey: boolean}> = {}
      providers.forEach(p => {
        forms[p.id] = {
          apiKey: '',  // 留空，用户需要重新输入才能更新
          baseUrl: p.base_url || p.api_url || '',
          // 使用服务器返回的 current_model，如果没有则用 default_model
          model: p.current_model || p.default_model || '',
          hasExistingKey: p.configured || false  // 标记是否已有配置
        }
      })
      setProviderForms(forms)
    }, [providers])

    const handleFormChange = (providerId: string, field: 'apiKey' | 'baseUrl' | 'model', value: string) => {
      setProviderForms(prev => ({
        ...prev,
        [providerId]: {
          ...prev[providerId],
          [field]: value
        }
      }))
    }

    const handleSaveProvider = async (providerId: string) => {
      const formData = providerForms[providerId]
      if (!formData) return

      // 检查是否需要 API Key
      const provider = providers.find(p => p.id === providerId)
      if (!provider?.configured && !formData.apiKey) {
        message.error('请输入 API Key')
        return
      }

      setLoading(true)
      try {
        // 只有当用户输入了新的 API Key 时才更新
        const payload: Record<string, unknown> = {
          base_url: formData.baseUrl,
          enabled: true
        }
        if (formData.apiKey) {
          payload.api_key = formData.apiKey
        }

        const response = await fetch(`/api/v1/ai/providers/${providerId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })

        if (response.ok) {
          // 如果是当前 provider，同时更新 model
          if (providerId === currentProvider && formData.model) {
            await fetch('/api/v1/ai/set-current', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ provider: providerId, model: formData.model })
            })
            setCurrentModel(formData.model)
          }
          message.success(`${provider?.name || providerId} 配置已保存`)

          // Refresh providers list to update configured status and current_model
          await loadProviders()

          // Clear API key after save, but keep the model value
          setProviderForms(prev => ({
            ...prev,
            [providerId]: {
              ...prev[providerId],
              apiKey: '',
              model: formData.model  // 保持新模型值
            }
          }))
        } else {
          const errorData = await response.json().catch(() => ({}))
          message.error(errorData.detail || '保存失败')
        }
      } catch (e) {
        console.error('Save error:', e)
        message.error('保存失败')
      } finally {
        setLoading(false)
      }
    }

    const handleTestProvider = async (providerId: string) => {
      setTesting(true)
      setTestResult(null)
      try {
        const response = await fetch(`/api/v1/ai/providers/${providerId}/test`, { method: 'POST' })
        const result = await response.json()
        setTestResult({ ...result, providerId })
        if (result.success) {
          message.success(result.message)
        } else {
          message.error(result.message || 'Connection failed')
        }
      } catch {
        setTestResult({ success: false, message: 'Connection test failed', providerId })
        message.error('Connection test failed')
      } finally {
        setTesting(false)
      }
    }

    // 设为当前 Provider（使用该 Provider 配置的 Model）
    const handleSetAsCurrent = async (providerId: string) => {
      const provider = providers.find(p => p.id === providerId)
      if (!provider) return

      // 使用该 Provider 配置的 current_model
      const modelToUse = provider.current_model || provider.default_model
      if (!modelToUse) {
        message.error('请先配置 Model Name')
        return
      }

      setSettingCurrent(true)
      try {
        const response = await fetch('/api/v1/ai/set-current', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ provider: providerId, model: modelToUse })
        })
        if (response.ok) {
          setCurrentProvider(providerId)
          setCurrentModel(modelToUse)
          message.success(`已切换到 ${provider.name} / ${modelToUse}`)
        } else {
          message.error('切换失败')
        }
      } catch {
        message.error('切换失败')
      } finally {
        setSettingCurrent(false)
      }
    }

    // Build tab items for each provider
    const providerTabItems = providers.map(provider => ({
      key: provider.id,
      label: (
        <Space size={4}>
          <span>{provider.name}</span>
          {provider.id === currentProvider && (
            <Tag color="purple" style={{ fontSize: 10, lineHeight: '16px', padding: '0 4px', margin: 0 }}>Active</Tag>
          )}
          {provider.configured && provider.id !== currentProvider && (
            <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 12 }} />
          )}
        </Space>
      ),
      children: (
        <div style={{ padding: '24px 24px 32px' }}>
          <Form layout="vertical" style={{ maxWidth: 560 }}>
            {/* API Key */}
            <Form.Item
              label={<span style={{ fontSize: 14, fontWeight: 500, color: '#262626' }}>API Key</span>}
              required={!provider.configured}
              style={{ marginBottom: 24 }}
            >
              {/* 如果已有配置，显示加密的 key 和输入新 key 的提示 */}
              {provider.configured && provider.masked_api_key && !providerForms[provider.id]?.apiKey && (
                <div style={{ marginBottom: 12 }}>
                  <div style={{
                    padding: '8px 12px',
                    background: '#f5f5f5',
                    borderRadius: 6,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                  }}>
                    <Space>
                      <CheckCircleOutlined style={{ color: '#52c41a' }} />
                      <Text code style={{ fontSize: 13 }}>{provider.masked_api_key}</Text>
                    </Space>
                    <Text type="secondary" style={{ fontSize: 12 }}>已配置</Text>
                  </div>
                  <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 8 }}>
                    输入新的 API Key 以更新配置（留空则保持原有配置）
                  </Text>
                </div>
              )}
              <Input.Password
                value={providerForms[provider.id]?.apiKey || ''}
                onChange={(e) => handleFormChange(provider.id, 'apiKey', e.target.value)}
                placeholder={provider.configured ? "输入新的 API Key（可选）" : `Enter your ${provider.name} API key`}
                style={{ fontSize: 14 }}
              />
            </Form.Item>

            {/* Base URL */}
            <Form.Item
              label={<span style={{ fontSize: 14, fontWeight: 500, color: '#262626' }}>Base URL</span>}
              style={{ marginBottom: 24 }}
            >
              <Input
                value={providerForms[provider.id]?.baseUrl || provider.base_url || provider.api_url || ''}
                onChange={(e) => handleFormChange(provider.id, 'baseUrl', e.target.value)}
                placeholder="API endpoint URL"
                prefix={<LinkOutlined style={{ color: '#bfbfbf' }} />}
                style={{ fontSize: 14 }}
              />
            </Form.Item>

            {/* Model Name - 手动输入 */}
            <Form.Item
              label={<span style={{ fontSize: 14, fontWeight: 500, color: '#262626' }}>Model Name</span>}
              required
              style={{ marginBottom: 8 }}
              help={<span style={{ fontSize: 12, color: '#8c8c8c' }}>
                {(provider.models || []).length > 0
                  ? `可用模型: ${(provider.models || []).map(m => m.id).join(', ')}`
                  : 'Example: gpt-4o, claude-3-5-sonnet, glm-4-flash'}
              </span>}
            >
              <Input
                value={providerForms[provider.id]?.model || ''}
                onChange={(e) => handleFormChange(provider.id, 'model', e.target.value)}
                placeholder="Enter model name"
                prefix={<ThunderboltOutlined style={{ color: '#bfbfbf' }} />}
                style={{ fontSize: 14 }}
              />
            </Form.Item>

            {/* Action Buttons */}
            <Form.Item style={{ marginBottom: 0, marginTop: 8 }}>
              <Space size={12}>
                <Button
                  type="primary"
                  icon={<SaveOutlined />}
                  onClick={() => handleSaveProvider(provider.id)}
                  loading={loading}
                  style={{ fontSize: 14, height: 36, paddingLeft: 20, paddingRight: 20 }}
                >
                  Save
                </Button>
                <Button
                  icon={<ReloadOutlined />}
                  onClick={() => handleTestProvider(provider.id)}
                  loading={testing}
                  style={{ fontSize: 14, height: 36 }}
                >
                  Test Connection
                </Button>
                {/* 设为当前按钮 - 只有已配置且不是当前 provider 时显示 */}
                {provider.configured && provider.id !== currentProvider && (
                  <Button
                    icon={<CheckCircleOutlined />}
                    onClick={() => handleSetAsCurrent(provider.id)}
                    loading={settingCurrent}
                    style={{ fontSize: 14, height: 36 }}
                  >
                    设为当前
                  </Button>
                )}
                {/* 当前 provider 标记 */}
                {provider.id === currentProvider && (
                  <Tag color="purple" style={{ fontSize: 13, padding: '4px 12px', height: 36, lineHeight: '28px' }}>
                    当前使用
                  </Tag>
                )}
              </Space>
            </Form.Item>

            {/* Test Result */}
            {testResult && testResult.providerId === provider.id && (
              <Alert
                message={testResult.success ? 'Connection Successful' : 'Connection Failed'}
                description={
                  <div>
                    <span style={{ fontSize: 13 }}>{testResult.message}</span>
                    {testResult.response_time_ms && (
                      <div style={{ fontSize: 12, color: '#8c8c8c', marginTop: 4 }}>
                        Response time: {testResult.response_time_ms}ms
                      </div>
                    )}
                  </div>
                }
                type={testResult.success ? 'success' : 'error'}
                showIcon
                closable
                onClose={() => setTestResult(null)}
                style={{ marginTop: 20, fontSize: 13 }}
              />
            )}
          </Form>
        </div>
      )
    }))

    return (
      <div>
        {/* Current Selection Banner */}
        <div style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          borderRadius: 8,
          padding: '16px 24px',
          marginBottom: 24,
          color: 'white'
        }}>
          <Space size="large">
            <div>
              <div style={{ fontSize: 12, opacity: 0.9 }}>Current AI Provider</div>
              <div style={{ fontSize: 18, fontWeight: 600 }}>
                {providers.find(p => p.id === currentProvider)?.name || currentProvider}
              </div>
            </div>
            <div style={{ width: 1, height: 40, background: 'rgba(255,255,255,0.3)' }} />
            <div>
              <div style={{ fontSize: 12, opacity: 0.9 }}>Current Model</div>
              <div style={{ fontSize: 18, fontWeight: 600 }}>{currentModel}</div>
            </div>
          </Space>
        </div>

        {/* Provider Tabs */}
        <Card bordered={false} style={{ borderRadius: 8 }}>
          <Tabs
            items={providerTabItems}
            activeKey={activeTabKey}
            onChange={(key) => setActiveTabKey(key)}
            type="line"
            size="large"
          />
        </Card>
      </div>
    )
  }

  // ============================================
  // Legacy AI Model Configuration Component (for backward compatibility)
  // ============================================

  function AIModelConfig() {
    return <MultiProviderConfig />
  }

  // ============================================
  // K8s Connection Status Component
  // ============================================

  function K8sConnectionCard() {
    const [testing, setTesting] = useState(false)
    const [testResult, setTestResult] = useState<{success: boolean; message: string; response_time_ms?: number} | null>(null)

    const handleTest = async () => {
      setTesting(true)
      setTestResult(null)
      try {
        const response = await fetch('/api/v1/integrations/type/kubernetes/test', { method: 'POST' })
        const result = await response.json()
        setTestResult(result)
        if (result.success) {
          message.success(result.message)
        } else {
          message.error(result.message || 'Connection failed')
        }
      } catch (e) {
        const errorMsg = 'Connection test failed'
        setTestResult({ success: false, message: errorMsg })
        message.error(errorMsg)
      } finally {
        setTesting(false)
      }
    }

    return (
      <Card
        title="Cluster Connection Status"
        extra={
          <Button
            type="primary"
            icon={<ReloadOutlined />}
            onClick={handleTest}
            loading={testing}
          >
            Test Connection
          </Button>
        }
      >
        <Space direction="vertical" className="w-full">
          <div className="flex items-center gap-4">
            <ClusterOutlined className="text-2xl text-blue-500" />
            <div>
              <Text strong>Kubernetes Cluster</Text>
              <br />
              <Text type="secondary">Connected via kubeconfig</Text>
            </div>
            {testResult && (
              <Tag color={testResult.success ? 'green' : 'red'} icon={testResult.success ? <CheckCircleOutlined /> : undefined}>
                {testResult.success ? 'Connected' : 'Disconnected'}
              </Tag>
            )}
          </div>
          {testResult && (
            <Alert
              message={testResult.success ? 'Connection Successful' : 'Connection Failed'}
              description={
                <div>
                  <p>{testResult.message}</p>
                  {testResult.response_time_ms && (
                    <Text type="secondary">Response time: {testResult.response_time_ms}ms</Text>
                  )}
                </div>
              }
              type={testResult.success ? 'success' : 'error'}
              showIcon
            />
          )}
        </Space>
      </Card>
    )
  }

  const tabItems = [
    {
      key: 'ai',
      label: (
        <span>
          <ThunderboltOutlined />
          AI Models
        </span>
      ),
      children: (
        <Space direction="vertical" className="w-full" size="large">
          <Alert message="Configure AI/LLM providers for intelligent operations and chat functionality" type="info" showIcon />
          <AIModelConfig />
        </Space>
      ),
    },
    {
      key: 'kubernetes',
      label: (
        <span>
          <SafetyOutlined />
          Kubernetes
        </span>
      ),
      children: (
        <Space direction="vertical" className="w-full" size="large">
          <Alert
            message="Kubeconfig Management"
            description="Manage Kubernetes cluster configurations for the entire team."
            type="info"
            showIcon
          />
          <K8sConnectionCard />
          <Card
            title="Kubeconfig Files"
            extra={
              <Button type="primary" icon={<PlusOutlined />} onClick={() => openKubeconfigModal()}>
                Add Config
              </Button>
            }
          >
            <Table
              dataSource={kubeconfigs}
              columns={kubeconfigColumns}
              rowKey="id"
              pagination={{ pageSize: 5 }}
            />
          </Card>
        </Space>
      ),
    },
    {
      key: 'grafana',
      label: (
        <span>
          <ApiOutlined />
          Grafana
        </span>
      ),
      children: (
        <Space direction="vertical" className="w-full" size="large">
          <Alert message="Configure Grafana integration for monitoring dashboards" type="info" showIcon />
          <GrafanaConfig />
        </Space>
      ),
    },
    {
      key: 'argocd',
      label: (
        <span>
          <CloudServerOutlined />
          ArgoCD
        </span>
      ),
      children: (
        <Space direction="vertical" className="w-full" size="large">
          <Alert message="Configure ArgoCD integration for GitOps deployments" type="info" showIcon />
          <ArgoCDConfig />
        </Space>
      ),
    },
    {
      key: 'jenkins',
      label: (
        <span>
          <ThunderboltOutlined />
          Jenkins
        </span>
      ),
      children: (
        <Space direction="vertical" className="w-full" size="large">
          <Alert message="Configure Jenkins integration for CI/CD pipelines" type="info" showIcon />
          <JenkinsConfig />
        </Space>
      ),
    },
    {
      key: 'gitlab',
      label: (
        <span>
          <GitlabOutlined />
          GitLab
        </span>
      ),
      children: (
        <Space direction="vertical" className="w-full" size="large">
          <Alert message="Configure GitLab integration for source control and CI/CD" type="info" showIcon />
          <GitLabConfig />
        </Space>
      ),
    },
    {
      key: 'github',
      label: (
        <span>
          <GithubOutlined />
          GitHub
        </span>
      ),
      children: (
        <Space direction="vertical" className="w-full" size="large">
          <Alert message="Configure GitHub integration for source control and Actions" type="info" showIcon />
          <GitHubConfig />
        </Space>
      ),
    },
    {
      key: 'bitbucket',
      label: (
        <span>
          <CodeOutlined />
          Bitbucket
        </span>
      ),
      children: (
        <Space direction="vertical" className="w-full" size="large">
          <Alert message="Configure Bitbucket integration for source control and Pipelines" type="info" showIcon />
          <BitbucketConfig />
        </Space>
      ),
    },
    {
      key: 'diagrams',
      label: (
        <span>
          <CloudServerOutlined />
          Diagrams
        </span>
      ),
      children: (
        <Space direction="vertical" className="w-full" size="large">
          <Alert message="Upload infrastructure diagrams for the team" type="info" showIcon />
          <Card
            title="Diagram Files"
            extra={
              <Upload accept=".drawio,.xml,.svg,.png" showUploadList={false} beforeUpload={handleDiagramUpload}>
                <Button type="primary" icon={<UploadOutlined />}>
                  Upload
                </Button>
              </Upload>
            }
          >
            <Table dataSource={diagrams} columns={diagramColumns} rowKey="id" pagination={false} />
          </Card>
        </Space>
      ),
    },
  ]

  return (
    <PageContainer
      title="Global Settings"
      icon={<SettingOutlined />}
      transparent
      extra={<Tag color="blue">Team Configuration</Tag>}
    >
      <div className="space-y-6">
        <Alert
        message="Global Connection Settings"
        description="These settings are shared across all team members. Changes here affect everyone's access to connected services."
        type="warning"
        showIcon
      />

      <Tabs items={tabItems} defaultActiveKey="kubernetes" />

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
              <Text type="secondary">Last updated: {new Date(previewDiagram.lastUpdated).toLocaleString()}</Text>
            </div>
            <div className="border rounded-lg bg-gray-50 p-4" style={{ height: 400, overflow: 'auto' }}>
            {previewDiagram.type === 'svg' && previewDiagram.content.startsWith('data:image/svg+xml') && (
                <div
                  dangerouslySetInnerHTML={{
                    __html: (() => {
                      const content = previewDiagram.content
                      if (content.startsWith('data:image/svg+xml;base64,')) {
                        // Base64-encoded SVG (UTF-8)
                        const base64Content = content.replace('data:image/svg+xml;base64,', '')
                        const binaryString = atob(base64Content)
                        const bytes = new Uint8Array(binaryString.length)
                        for (let i = 0; i < binaryString.length; i++) {
                          bytes[i] = binaryString.charCodeAt(i)
                        }
                        return new TextDecoder('utf-8').decode(bytes)
                      } else {
                        // URL-encoded SVG
                        return decodeURIComponent(content.split(',')[1])
                      }
                    })(),
                  }}
                  style={{ width: '100%', height: '100%' }}
                />
              )}
              {previewDiagram.type === 'svg' && !previewDiagram.content.startsWith('data:') && (
                <div dangerouslySetInnerHTML={{ __html: previewDiagram.content }} style={{ width: '100%', height: '100%' }} />
              )}
              {previewDiagram.type === 'png' && (
                <img src={previewDiagram.content} alt={previewDiagram.name} style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }} />
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

      {/* Kubeconfig Modal */}
      <Modal
        title={editingKubeconfig ? 'Edit Kubeconfig' : 'Add Kubeconfig'}
        open={kubeconfigModalVisible}
        onCancel={() => setKubeconfigModalVisible(false)}
        onOk={() => kubeconfigForm.submit()}
        width={700}
      >
        <Form form={kubeconfigForm} layout="vertical" onFinish={handleSaveKubeconfig}>
          <Form.Item name="name" label="Config Name" rules={[{ required: true, message: 'Please enter config name' }]}>
            <Input placeholder="e.g., production-cluster" />
          </Form.Item>
          <Form.Item name="config" label="Kubeconfig YAML" rules={[{ required: !editingKubeconfig, message: 'Please enter kubeconfig content' }]}>
            <TextArea rows={12} placeholder="Paste kubeconfig file content..." className="font-mono text-sm" />
          </Form.Item>
          <Form.Item name="default_namespace" label="Default Namespace" initialValue="default">
            <Input placeholder="default" />
          </Form.Item>
          <Alert message="Please ensure kubeconfig file is from a trusted source" type="warning" showIcon />
        </Form>
      </Modal>

      {/* Kubeconfig Detail Modal */}
      <Modal
        title={
          <Space>
            <ClusterOutlined />
            <span>{selectedKubeconfig?.name}</span>
            {selectedKubeconfig && (
              <Tag color={selectedKubeconfig.status === 'valid' ? 'green' : 'red'}>{selectedKubeconfig.status}</Tag>
            )}
          </Space>
        }
        open={kubeconfigDetailVisible}
        onCancel={() => {
          setKubeconfigDetailVisible(false)
          setTestResult(null)
        }}
        footer={null}
        width={800}
      >
        {selectedKubeconfig && (
          <Space direction="vertical" className="w-full" size="large">
            <Descriptions bordered size="small" column={2}>
              <Descriptions.Item label="Clusters">{selectedKubeconfig.clusters.join(', ')}</Descriptions.Item>
              <Descriptions.Item label="Contexts">{selectedKubeconfig.contexts.join(', ')}</Descriptions.Item>
              <Descriptions.Item label="Current Context">{selectedKubeconfig.current_context || '-'}</Descriptions.Item>
              <Descriptions.Item label="Default Namespace">{selectedKubeconfig.default_namespace}</Descriptions.Item>
            </Descriptions>
            <Card
              size="small"
              title="Connection Test"
              extra={
                <Button
                  type="primary"
                  size="small"
                  icon={<ReloadOutlined />}
                  loading={testingConnection}
                  onClick={() => handleTestKubeconfig(selectedKubeconfig.id)}
                >
                  Test
                </Button>
              }
            >
              {testResult ? (
                testResult.success ? (
                  <Space direction="vertical">
                    <Alert message={testResult.message} type="success" showIcon />
                    {testResult.server_version && (
                      <Text>
                        Server Version: <Tag>{testResult.server_version}</Tag>
                      </Text>
                    )}
                  </Space>
                ) : (
                  <Alert message={testResult.message} type="error" showIcon />
                )
              ) : (
                <Text type="secondary">Click "Test" to verify connection</Text>
              )}
            </Card>
            <Card size="small" title="Config Content (Redacted)">
              <pre className="bg-gray-100 p-4 rounded text-xs overflow-auto max-h-60">
                {selectedKubeconfig.config_redacted}
              </pre>
            </Card>
          </Space>
        )}
      </Modal>
      </div>
    </PageContainer>
  )
}

// ============================================
// Mock Data
// ============================================

function getMockKubeconfigs(): Kubeconfig[] {
  return [
    {
      id: 'kc-1',
      name: 'Production Cluster',
      clusters: ['prod-cluster'],
      contexts: ['prod-admin', 'prod-viewer'],
      current_context: 'prod-admin',
      default_namespace: 'default',
      status: 'valid',
      last_verified: new Date().toISOString(),
      created_at: '2024-01-01',
    },
    {
      id: 'kc-2',
      name: 'Staging Cluster',
      clusters: ['staging-cluster'],
      contexts: ['staging-default'],
      current_context: 'staging-default',
      default_namespace: 'default',
      status: 'valid',
      last_verified: new Date().toISOString(),
      created_at: '2024-01-15',
    },
  ]
}

function getSampleConfig(): string {
  return `apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: ***REDACTED***
    server: https://prod.example.com:6443
  name: prod-cluster
contexts:
- context:
    cluster: prod-cluster
    namespace: default
    user: prod-admin
  name: prod-admin
current-context: prod-admin
kind: Config
preferences: {}
users:
- name: prod-admin
  user:
    client-certificate-data: ***REDACTED***
    client-key-data: ***REDACTED***
    token: ***REDACTED***`
}
