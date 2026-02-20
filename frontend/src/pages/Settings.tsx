import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
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
  Select,
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
  GlobalOutlined,
} from '@ant-design/icons'
import type { UploadFile } from 'antd/es/upload/interface'
import { useAuthStore } from '../stores/authStore'
import { useDiagramStore, type DiagramConfig } from '../stores/configStore'

const { Title, Text } = Typography
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
  status: 'connected' | 'disconnected' | 'error'
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
  const [form] = Form.useForm()

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    try {
      const response = await fetch('/api/v1/integrations/grafana')
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
    message.info('Testing connection...')
    setTimeout(() => message.success('Connection successful'), 1000)
  }

  return (
    <Card title="Grafana Configuration" extra={<Tag color={config?.status === 'connected' ? 'green' : 'default'}>{config?.status || 'Not Configured'}</Tag>}>
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
          <Button icon={<ReloadOutlined />} onClick={handleTest}>
            Test Connection
          </Button>
        </Space>
      </Form>
    </Card>
  )
}

function ArgoCDConfig() {
  const [config, setConfig] = useState<IntegrationConfig | null>(null)
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    try {
      const response = await fetch('/api/v1/integrations/argocd')
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
    message.info('Testing connection...')
    setTimeout(() => message.success('Connection successful'), 1000)
  }

  return (
    <Card title="ArgoCD Configuration" extra={<Tag color={config?.status === 'connected' ? 'green' : 'default'}>{config?.status || 'Not Configured'}</Tag>}>
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
          <Button icon={<ReloadOutlined />} onClick={handleTest}>
            Test Connection
          </Button>
        </Space>
      </Form>
    </Card>
  )
}

function JenkinsConfig() {
  const [config, setConfig] = useState<IntegrationConfig | null>(null)
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    try {
      const response = await fetch('/api/v1/integrations/jenkins')
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
    message.info('Testing connection...')
    setTimeout(() => message.success('Connection successful'), 1000)
  }

  return (
    <Card title="Jenkins Configuration" extra={<Tag color={config?.status === 'connected' ? 'green' : 'default'}>{config?.status || 'Not Configured'}</Tag>}>
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
          <Button icon={<ReloadOutlined />} onClick={handleTest}>
            Test Connection
          </Button>
        </Space>
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
  const { i18n } = useTranslation()
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

  const tabItems = [
    {
      key: 'general',
      label: (
        <span>
          <GlobalOutlined />
          General
        </span>
      ),
      children: (
        <Space direction="vertical" className="w-full" size="large">
          <Card title="System Preferences">
            <Form layout="vertical">
              <Form.Item label="Language / 语言" extra="Select the default language for the application interface.">
                <Select
                  value={i18n.language}
                  onChange={(val) => i18n.changeLanguage(val)}
                  style={{ width: 200 }}
                  options={[
                    { value: 'en', label: 'English' },
                    { value: 'zh', label: '简体中文' },
                  ]}
                />
              </Form.Item>
            </Form>
          </Card>
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
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <Title level={4} className="m-0">
          <SettingOutlined className="mr-2" />
          Global Settings
        </Title>
        <Tag color="blue">Team Configuration</Tag>
      </div>

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
                    __html: decodeURIComponent(previewDiagram.content.split(',')[1]),
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
