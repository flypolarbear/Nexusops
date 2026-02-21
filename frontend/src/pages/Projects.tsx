import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  Card,
  Table,
  Tag,
  Typography,
  Button,
  Modal,
  Form,
  Input,
  Select,
  Space,
  Tabs,
  Descriptions,
  Badge,
  Tooltip,
  message,
  Row,
  Col,
  Statistic,
  Alert,
  Popconfirm,
  Divider,
  Progress,
  Steps,
  Result,
  notification,
} from 'antd'
import {
  PlusOutlined,
  EyeOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  RocketOutlined,
  BranchesOutlined,
  HistoryOutlined,
  LinkOutlined,
  UserOutlined,
  CopyOutlined,
  StarFilled,
  SyncOutlined,
  GlobalOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  GithubOutlined,
  ExportOutlined,
  LoadingOutlined,
  CloudUploadOutlined,
  SafetyCertificateOutlined,
} from '@ant-design/icons'
import {
  useVersionStore,
  type Version,
  type Project,
  type VersionSwitchRequest,
  type VersionStatus,
} from '../stores/versionStore'
import { useDeploymentStore } from '../stores/deploymentStore'

const { Title, Text, Link } = Typography
const { TextArea } = Input

// 部署进度步骤
type DeploymentStep = 'idle' | 'building' | 'deploying' | 'healthcheck' | 'completed' | 'failed'

interface DeploymentProgress {
  versionId: string
  codename: string
  step: DeploymentStep
  progress: number
  testUrl: string
  regions: string[]
  message: string
  buildLog?: string
  deployLog?: string
}

// 版本状态配置
const versionStatusConfig = (t: any): Record<VersionStatus, { color: string; label: string; icon: React.ReactNode }> => ({
  testing: { color: 'orange', label: t('projects.testing'), icon: <ClockCircleOutlined /> },
  production: { color: 'green', label: t('projects.production'), icon: <StarFilled /> },
  archived: { color: 'default', label: t('projects.archived'), icon: <HistoryOutlined /> },
})

export default function Projects() {
  const { t } = useTranslation()
  const vsc = versionStatusConfig(t)
  const [activeTab, setActiveTab] = useState('versions')
  const [selectedVersion, setSelectedVersion] = useState<Version | null>(null)
  const [versionDetailOpen, setVersionDetailOpen] = useState(false)
  const [newVersionModalOpen, setNewVersionModalOpen] = useState(false)
  const [switchRequestModalOpen, setSwitchRequestModalOpen] = useState(false)
  const [newProjectModalOpen, setNewProjectModalOpen] = useState(false)
  const [deploymentProgressModalOpen, setDeploymentProgressModalOpen] = useState(false)
  const [deploymentProgress, setDeploymentProgress] = useState<DeploymentProgress | null>(null)
  const [productionDeployRegions, setProductionDeployRegions] = useState<string[]>([])
  const [versionForm] = Form.useForm()
  const [switchForm] = Form.useForm()
  const [projectForm] = Form.useForm()
  const [currentProjectId, setCurrentProjectId] = useState<string | null>(null)
  const [selectedRegions, setSelectedRegions] = useState<string[]>([])

  const {
    projects,
    switchRequests,
    addVersion,
    createSwitchRequest,
    approveSwitchRequest,
    rejectSwitchRequest,
  } = useVersionStore()

  const {
    deployments,
    getDeploymentsByCodename,
    regions,
  } = useDeploymentStore()

  // 自动生成测试 URL
  const generateTestUrl = (projectCode: string, codename: string) => {
    const codenameSlug = codename.toLowerCase().replace(/\s+/g, '-')
    return `https://${projectCode}-${codenameSlug}.test.internal`
  }

  // 模拟部署进度更新
  const simulateDeployment = (versionId: string, codename: string, projectCode: string, regions: string[]) => {
    const testUrl = generateTestUrl(projectCode, codename)

    // 初始状态
    setDeploymentProgress({
      versionId,
      codename,
      step: 'building',
      progress: 0,
      testUrl,
      regions,
      message: 'Starting CI/CD build...',
    })
    setDeploymentProgressModalOpen(true)

    // 模拟构建进度
    let progress = 0
    const progressInterval = setInterval(() => {
      progress += Math.random() * 15
      if (progress > 100) progress = 100

      setDeploymentProgress(prev => {
        if (!prev) return prev

        if (progress < 33) {
          return { ...prev, step: 'building', progress: Math.round(progress), message: 'Building Docker image...' }
        } else if (progress < 66) {
          return { ...prev, step: 'deploying', progress: Math.round(progress), message: t('projects.deployingTest') }
        } else if (progress < 100) {
          return { ...prev, step: 'healthcheck', progress: Math.round(progress), message: 'Health checking...' }
        } else {
          clearInterval(progressInterval)
          // 部署完成通知
          notification.success({
            message: 'Deployment completed',
            description: (
              <div>
                <p>Version <strong>{codename}</strong> successfully deployed to test environment</p>
                <p>测试链接: <a href={testUrl} target="_blank" rel="noopener noreferrer">{testUrl}</a></p>
              </div>
            ),
            duration: 10,
          })
          return { ...prev, step: 'completed', progress: 100, message: 'Deployment completed!' }
        }
      })
    }, 800)

    return () => clearInterval(progressInterval)
  }

  // 创建新版本
  const handleCreateVersion = (projectId: string) => {
    setCurrentProjectId(projectId)
    const project = projects.find(p => p.id === projectId)
    const autoTestUrl = generateTestUrl(project?.code || '', '')
    versionForm.setFieldsValue({
      projectId,
      projectName: project?.name,
      projectCode: project?.code,
      testUrl: autoTestUrl,
    })
    setSelectedRegions([])
    setNewVersionModalOpen(true)
  }

  const handleSubmitVersion = () => {
    versionForm.validateFields().then((values) => {
      // 生成测试 URL
      const testUrl = generateTestUrl(values.projectCode, values.codename)
      const versionId = `ver-${Date.now()}`

      // 添加版本
      addVersion(currentProjectId!, {
        codename: values.codename,
        description: values.description,
        gitBranch: values.gitBranch,
        imageUrl: values.imageUrl,
        owner: values.owner,
        testUrl: testUrl,
        environments: ['dev'],
      })

      setNewVersionModalOpen(false)
      versionForm.resetFields()

      // 如果选择了部署区域，触发部署
      if (selectedRegions.length > 0) {
        simulateDeployment(
          versionId,
          values.codename,
          values.projectCode,
          selectedRegions
        )
      } else {
        message.success(`Version "${values.codename}" created successfully!`)
      }
    })
  }

  // 申请切换生产版本
  const handleRequestSwitch = (project: Project, version: Version) => {
    const currentProd = project.versions.find(v => v.id === project.productionVersionId)
    const versionDeps = getVersionDeployments(version)
    const gitInfo = versionDeps[0]

    switchForm.setFieldsValue({
      projectId: project.id,
      projectName: project.name,
      fromVersionId: currentProd?.id,
      fromVersionCodename: currentProd?.codename || 'N/A',
      toVersionId: version.id,
      toVersionCodename: version.codename,
      gitBranch: gitInfo?.gitBranch || version.gitBranch,
      gitCommit: gitInfo?.gitCommit || 'N/A',
      imageVersion: gitInfo?.imageVersion || version.imageUrl?.split(':').pop() || 'N/A',
      testUrl: version.testUrl,
    })
    setProductionDeployRegions([]) // Reset selected regions
    setSwitchRequestModalOpen(true)
  }

  const handleSubmitSwitchRequest = () => {
    switchForm.validateFields().then((values) => {
      if (productionDeployRegions.length === 0) {
        message.error('Please select at least one deploy region')
        return
      }

      createSwitchRequest({
        projectId: values.projectId,
        projectName: values.projectName,
        fromVersionId: values.fromVersionId,
        fromVersionCodename: values.fromVersionCodename,
        toVersionId: values.toVersionId,
        toVersionCodename: values.toVersionCodename,
        reason: `${values.changeSummary}\n\nTest Results: ${values.testResults}${values.riskAssessment ? `\n\nRisk Assessment: ${values.riskAssessment}` : ''}${values.rollbackPlan ? `\n\nRollback Plan: ${values.rollbackPlan}` : ''}`,
        gitBranch: values.gitBranch,
        gitCommit: values.gitCommit,
        imageVersion: values.imageVersion,
        deployRegions: productionDeployRegions,
        deployStrategy: values.deployStrategy,
        deployOrder: values.deployOrder,
        requester: 'Current User',
        createdAt: new Date().toISOString(),
      })

      notification.success({
        message: 'Prod request submitted',
        description: (
          <div>
            <p>Prod request for version <strong>{values.toVersionCodename}</strong> submitted</p>
            <p>Deploy regions: {productionDeployRegions.length}</p>
            <p>Waiting for Admin approval</p>
          </div>
        ),
      })

      setSwitchRequestModalOpen(false)
      switchForm.resetFields()
      setProductionDeployRegions([])
    })
  }

  // 重新部署
  const handleRedeploy = (version: Version) => {
    // TODO: 调用后端 API 触发重新部署
    message.loading({ content: `Triggering redeploy for ${version.codename}...`, key: 'redeploy' })
    setTimeout(() => {
      message.success({ content: `Redeploy triggered for ${version.codename}`, key: 'redeploy' })
    }, 1500)
  }

  // 审批
  const handleApproveRequest = (requestId: string) => {
    approveSwitchRequest(requestId, 'Admin')
    message.success('Version switch approved!')
  }

  const handleRejectRequest = (requestId: string) => {
    rejectSwitchRequest(requestId, 'Admin')
    message.warning('Version switch request rejected')
  }

  // 复制到剪贴板
  const handleCopy = (text: string, label: string) => {
    navigator.clipboard.writeText(text)
    message.success(`${label} copied`)
  }

  // 获取版本的部署信息
  const getVersionDeployments = (version: Version) => {
    return getDeploymentsByCodename(version.codename)
  }

  // 获取版本部署的区域
  const getVersionRegions = (version: Version) => {
    const deps = getVersionDeployments(version)
    const regions = [...new Set(deps.map(d => d.regionName))]
    return regions
  }

  // 获取版本健康状态
  const getVersionHealth = (version: Version) => {
    const deps = getVersionDeployments(version)
    if (deps.length === 0) return 'unknown'
    const hasError = deps.some(d => d.status === 'error')
    const hasWarning = deps.some(d => d.status === 'warning')
    if (hasError) return 'critical'
    if (hasWarning) return 'warning'
    return 'healthy'
  }

  // 获取所有版本的扁平列表
  const allVersions = projects.flatMap(p =>
    p.versions.map(v => ({
      ...v,
      projectName: p.name,
      projectCode: p.code,
      isProduction: p.productionVersionId === v.id,
      projectId: p.id,
    }))
  )

  // 版本列表列定义
  const versionColumns = [
    {
      title: t('projects.project'),
      dataIndex: 'projectName',
      key: 'projectName',
      width: 130,
      render: (name: string, record: Version & { projectCode: string }) => (
        <div>
          <div className="font-medium">{name}</div>
          <Text type="secondary" className="text-xs">{record.projectCode}</Text>
        </div>
      ),
    },
    {
      title: t('projects.codename'),
      dataIndex: 'codename',
      key: 'codename',
      width: 130,
      render: (codename: string, record: Version & { isProduction: boolean }) => {
        const health = getVersionHealth(record)
        const healthColors: Record<string, string> = {
          healthy: 'text-green-500',
          warning: 'text-yellow-500',
          critical: 'text-red-500',
          unknown: 'text-gray-400',
        }
        return (
          <Space>
            {record.isProduction && (
              <Tooltip title="Current production version">
                <StarFilled className="text-yellow-500" />
              </Tooltip>
            )}
            <span className="font-medium">{codename}</span>
            {health !== 'unknown' && (
              <Tooltip title={`${t('projects.status')}: ${health}`}>
                <span className={healthColors[health]}>●</span>
              </Tooltip>
            )}
          </Space>
        )
      },
    },
    {
      title: t('projects.status'),
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: VersionStatus) => {
        const config = vsc[status]
        return <Tag color={config.color} icon={config.icon}>{config.label}</Tag>
      },
    },
    {
      title: t('projects.regions'),
      key: 'regions',
      width: 180,
      render: (_: unknown, record: Version) => {
        const regions = getVersionRegions(record)
        if (regions.length === 0) {
          return <Text type="secondary">{t('projects.notDeployed')}</Text>
        }
        return (
          <Space size={2} wrap>
            {regions.slice(0, 3).map(r => (
              <Tag key={r} className="text-xs">{r}</Tag>
            ))}
            {regions.length > 3 && (
              <Tooltip title={regions.slice(3).join(', ')}>
                <Tag>+{regions.length - 3}</Tag>
              </Tooltip>
            )}
          </Space>
        )
      },
    },
    {
      title: t('projects.testUrl'),
      dataIndex: 'testUrl',
      key: 'testUrl',
      width: 160,
      render: (url: string | undefined) => url ? (
        <Space size={4}>
          <Tooltip title={url}>
            <Link
              href={url}
              target="_blank"
              className="text-xs"
              style={{ maxWidth: 100 }}
              ellipsis
            >
              {url.replace('https://', '').replace('http://', '')}
            </Link>
          </Tooltip>
          <Button
            type="text"
            size="small"
            icon={<CopyOutlined />}
            onClick={() => handleCopy(url, t('projects.testLink'))}
            style={{ padding: '0 4px' }}
          />
          <Button
            type="text"
            size="small"
            icon={<ExportOutlined />}
            href={url}
            target="_blank"
            style={{ padding: '0 4px' }}
          />
        </Space>
      ) : (
        <Text type="secondary">-</Text>
      ),
    },
    {
      title: t('projects.git'),
      key: 'git',
      width: 140,
      render: (_: unknown, record: Version) => {
        const deps = getVersionDeployments(record)
        const gitInfo = deps[0]
        return gitInfo ? (
          <Space direction="vertical" size={0}>
            <span className="text-xs">
              <GithubOutlined className="mr-1" />
              {gitInfo.gitBranch}
            </span>
            <a
              href={gitInfo.gitCommitUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-gray-500"
            >
              {gitInfo.gitCommit.substring(0, 7)}
            </a>
          </Space>
        ) : (
          <Text type="secondary" className="text-xs">{record.gitBranch}</Text>
        )
      },
    },
    {
      title: t('projects.owner'),
      dataIndex: 'owner',
      key: 'owner',
      width: 80,
    },
    {
      title: t('projects.actions'),
      key: 'actions',
      width: 180,
      fixed: 'right' as const,
      render: (_: unknown, record: Version & { isProduction: boolean; projectName: string; projectId: string }) => {
        const project = projects.find(p => p.id === record.projectId)
        const hasDeployments = getVersionDeployments(record).length > 0
        return (
          <Space size={2}>
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => {
                setSelectedVersion(record)
                setVersionDetailOpen(true)
              }}
            >
              {t('projects.details')}
            </Button>
            <Button
              type="link"
              size="small"
              icon={<SyncOutlined />}
              onClick={() => handleRedeploy(record)}
              disabled={!hasDeployments}
            >
              {t('projects.redeploy')}
            </Button>
            <Button
              type="link"
              size="small"
              icon={<RocketOutlined style={record.status === 'testing' && !record.isProduction && hasDeployments ? { color: '#22c55e' } : undefined} />}
              onClick={() => handleRequestSwitch(project!, record)}
              disabled={!(record.status === 'testing' && !record.isProduction && hasDeployments)}
              style={record.status === 'testing' && !record.isProduction && hasDeployments ? { color: '#22c55e' } : undefined}
            >
              {t('projects.requestOnline')}
            </Button>
          </Space>
        )
      },
    },
  ]

  // 审批请求列定义
  const requestColumns = [
    {
      title: t('projects.project'),
      dataIndex: 'projectName',
      key: 'projectName',
      width: 120,
    },
    {
      title: 'Version Switch',
      key: 'versionChange',
      width: 180,
      render: (_: unknown, record: VersionSwitchRequest) => (
        <Space>
          <Tag>{record.fromVersionCodename}</Tag>
          <span>→</span>
          <Tag color="green" icon={<RocketOutlined />}>{record.toVersionCodename}</Tag>
        </Space>
      ),
    },
    {
      title: t('projects.regions'),
      key: 'deployRegions',
      width: 150,
      render: (_: unknown, record: VersionSwitchRequest) => {
        if (record.deployRegions && record.deployRegions.length > 0) {
          return (
            <Space size={2} wrap>
              {record.deployRegions.slice(0, 2).map(r => (
                <Tag key={r} className="text-xs" icon={<GlobalOutlined />}>{r}</Tag>
              ))}
              {record.deployRegions.length > 2 && (
                <Tooltip title={record.deployRegions.slice(2).join(', ')}>
                  <Tag>+{record.deployRegions.length - 2}</Tag>
                </Tooltip>
              )}
            </Space>
          )
        }
        return <Text type="secondary">-</Text>
      },
    },
    {
      title: 'Deploy Strategy',
      key: 'deployStrategy',
      width: 120,
      render: (_: unknown, record: VersionSwitchRequest) => {
        if (record.deployStrategy) {
          const strategyLabels: Record<string, string> = {
            'rolling': 'Rolling Update',
            'blue-green': 'Blue-Green',
            'canary': 'Canary',
          }
          return <Tag>{strategyLabels[record.deployStrategy] || record.deployStrategy}</Tag>
        }
        return <Text type="secondary">-</Text>
      },
    },
    {
      title: t('projects.status'),
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const config: Record<string, { color: string; label: string; icon: React.ReactNode }> = {
          pending: { color: 'orange', label: 'Pending', icon: <ClockCircleOutlined /> },
          approved: { color: 'green', label: 'Approved', icon: <CheckCircleOutlined /> },
          rejected: { color: 'red', label: 'Rejected', icon: <ExclamationCircleOutlined /> },
          completed: { color: 'blue', label: 'Completed', icon: <CheckCircleOutlined /> },
        }
        const { color, label, icon } = config[status] || { color: 'default', label: status, icon: null }
        return <Tag color={color} icon={icon}>{label}</Tag>
      },
    },
    {
      title: 'Requester',
      dataIndex: 'requester',
      key: 'requester',
      width: 100,
    },
    {
      title: 'Request Time',
      dataIndex: 'createdAt',
      key: 'createdAt',
    },
    {
      title: t('projects.actions'),
      key: 'actions',
      render: (_: unknown, record: VersionSwitchRequest) =>
        record.status === 'pending' ? (
          <Space>
            <Popconfirm
              title={t('projects.confirmApprove')}
              description={t('projects.confirmApproveDesc')}
              onConfirm={() => handleApproveRequest(record.id)}
            >
              <Button type="link" size="small" style={{ color: '#22c55e' }}>
                {t('projects.approve')}
              </Button>
            </Popconfirm>
            <Popconfirm
              title={t('projects.confirmReject')}
              onConfirm={() => handleRejectRequest(record.id)}
            >
              <Button type="link" size="small" danger>
                {t('projects.reject')}
              </Button>
            </Popconfirm>
          </Space>
        ) : (
          <Text type="secondary">-</Text>
        ),
    },
  ]

  // 版本详情中的部署列表
  const versionDeploymentColumns = [
    {
      title: 'Region',
      dataIndex: 'regionName',
      key: 'regionName',
      width: 150,
    },
    {
      title: 'Service',
      dataIndex: 'serviceName',
      key: 'serviceName',
      width: 120,
    },
    {
      title: t('projects.status'),
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: string) => {
        const config: Record<string, { color: string; icon: React.ReactNode }> = {
          running: { color: 'green', icon: <CheckCircleOutlined /> },
          warning: { color: 'orange', icon: <WarningOutlined /> },
          error: { color: 'red', icon: <ExclamationCircleOutlined /> },
        }
        const { color, icon } = config[status] || { color: 'default', icon: null }
        return <Tag color={color} icon={icon}>{status}</Tag>
      },
    },
    {
      title: 'ArgoCD',
      key: 'argocd',
      width: 180,
      render: (_: unknown, record: typeof deployments[0]) => (
        <Space direction="vertical" size={0}>
          <a href={record.argocdUrl} target="_blank" rel="noopener noreferrer" className="text-xs">
            <LinkOutlined className="mr-1" />
            {record.argocdApp}
          </a>
          <Space size={4}>
            <Tag
              color={record.argocdSyncStatus === 'synced' ? 'green' : 'orange'}
              className="text-xs"
              style={{ margin: 0 }}
            >
              {record.argocdSyncStatus}
            </Tag>
            <Tag
              color={record.argocdHealthStatus === 'healthy' ? 'green' : record.argocdHealthStatus === 'degraded' ? 'red' : 'orange'}
              className="text-xs"
              style={{ margin: 0 }}
            >
              {record.argocdHealthStatus}
            </Tag>
          </Space>
        </Space>
      ),
    },
    {
      title: t('projects.actions'),
      key: 'actions',
      width: 80,
      render: () => (
        <Space>
          <Tooltip title={t('projects.viewLogs')}>
            <Button type="link" size="small" icon={<EyeOutlined />} />
          </Tooltip>
        </Space>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <Title level={4} className="m-0">{t('projects.title')}</Title>
        <Space>
          <Button icon={<HistoryOutlined />}>{t('projects.auditLogs')}</Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setNewProjectModalOpen(true)}
          >
            {t('projects.newProject')}
          </Button>
        </Space>
      </div>

      {/* Summary Cards */}
      <Row gutter={16}>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title={t('projects.totalProjects')}
              value={projects.length}
              prefix={<BranchesOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title={t('projects.prodVersions')}
              value={allVersions.filter(v => v.status === 'production').length}
              prefix={<StarFilled style={{ color: '#fbbf24' }} />}
              valueStyle={{ color: '#22c55e' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title={t('projects.testVersions')}
              value={allVersions.filter(v => v.status === 'testing').length}
              prefix={<ClockCircleOutlined style={{ color: '#f97316' }} />}
              valueStyle={{ color: '#f97316' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title={t('projects.pendingApprovals')}
              value={switchRequests.filter(r => r.status === 'pending').length}
              prefix={<ExclamationCircleOutlined style={{ color: '#ef4444' }} />}
              valueStyle={{ color: switchRequests.filter(r => r.status === 'pending').length > 0 ? '#ef4444' : undefined }}
            />
          </Card>
        </Col>
      </Row>

      {/* Vibe Coding 工作流提示 */}
      <Alert
        message={
          <span>
            <strong>{t('projects.workflowTipTitle')}</strong>
            {t('projects.workflowTipDesc')}
          </span>
        }
        type="info"
        showIcon
        closable
      />

      {/* Tabs */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: 'versions',
            label: (
              <span>
                <BranchesOutlined />
                {t('projects.versionList')}
              </span>
            ),
            children: (
              <Card>
                <div className="mb-4">
                  <Space>
                    <Select
                      placeholder={t('projects.filterProject')}
                      allowClear
                      style={{ width: 200 }}
                      options={projects.map(p => ({ value: p.id, label: p.name }))}
                    />
                    <Select
                      placeholder={t('projects.filterStatus')}
                      allowClear
                      style={{ width: 150 }}
                      options={Object.entries(vsc).map(([key, val]) => ({
                        value: key,
                        label: val.label,
                      }))}
                    />
                  </Space>
                </div>
                <Table
                  dataSource={allVersions}
                  columns={versionColumns}
                  rowKey="id"
                  pagination={{ pageSize: 10 }}
                  scroll={{ x: 1300 }}
                />
              </Card>
            ),
          },
          {
            key: 'projects',
            label: (
              <span>
                <BranchesOutlined />
                {t('projects.projectList')}
              </span>
            ),
            children: (
              <Row gutter={[16, 16]}>
                {projects.map(project => {
                  const prodVersion = project.versions.find(v => v.id === project.productionVersionId)
                  const testingVersions = project.versions.filter(v => v.status === 'testing')
                  return (
                    <Col key={project.id} span={12}>
                      <Card
                        title={
                          <Space>
                            <span className="font-medium">{project.name}</span>
                            <Text type="secondary" className="text-sm">{project.code}</Text>
                          </Space>
                        }
                        extra={
                          <Button
                            type="primary"
                            ghost
                            size="small"
                            icon={<PlusOutlined />}
                            onClick={() => handleCreateVersion(project.id)}
                          >
                            {t('projects.createNewVersion')}
                          </Button>
                        }
                      >
                        <Descriptions column={2} size="small">
                          <Descriptions.Item label={t('projects.currentProdVersion')}>
                            {prodVersion && (
                              <Tag color="green" icon={<StarFilled />}>
                                {prodVersion.codename}
                              </Tag>
                            )}
                          </Descriptions.Item>
                          <Descriptions.Item label={t('projects.owner')}>
                            {project.owner}
                          </Descriptions.Item>
                          <Descriptions.Item label={t('projects.totalVersions')} span={2}>
                            {project.versions.length}{t('projects.versionsCount')}
                            {t('projects.testingCount')}{testingVersions.length})
                          </Descriptions.Item>
                        </Descriptions>

                        {testingVersions.length > 0 && (
                          <div className="mt-4">
                            <Text type="secondary" className="text-xs">{t('projects.testVersionLabel')}</Text>
                            <div className="mt-2 flex flex-wrap gap-2">
                              {testingVersions.map(v => {
                                const regions = getVersionRegions(v)
                                const health = getVersionHealth(v)
                                return (
                                  <Tag
                                    key={v.id}
                                    color={health === 'healthy' ? 'orange' : health === 'critical' ? 'red' : 'orange'}
                                    className="cursor-pointer"
                                    onClick={() => {
                                      setSelectedVersion(v)
                                      setVersionDetailOpen(true)
                                    }}
                                  >
                                    {v.codename}
                                    {regions.length > 0 && <span className="ml-1">({regions.length}{t('projects.regionCount')}</span>}
                                    {v.testUrl && (
                                      <CopyOutlined
                                        className="ml-1"
                                        onClick={(e) => {
                                          e.stopPropagation()
                                          handleCopy(v.testUrl!, t('projects.testLink'))
                                        }}
                                      />
                                    )}
                                  </Tag>
                                )
                              })}
                            </div>
                          </div>
                        )}
                      </Card>
                    </Col>
                  )
                })}
              </Row>
            ),
          },
          {
            key: 'requests',
            label: (
              <span>
                <ClockCircleOutlined />
                {t('projects.switchApproval')}
                <Badge
                  count={switchRequests.filter(r => r.status === 'pending').length}
                  size="small"
                  className="ml-2"
                />
              </span>
            ),
            children: (
              <Card>
                <Table
                  dataSource={switchRequests}
                  columns={requestColumns}
                  rowKey="id"
                  pagination={{ pageSize: 10 }}
                />
              </Card>
            ),
          },
        ]}
      />

      {/* 版本详情弹窗 - 增强 */}
      <Modal
        title={
          <Space>
            <span>{t('projects.versionDetails')}</span>
            {selectedVersion && (
              <Tag color={vsc[selectedVersion.status].color}>
                {vsc[selectedVersion.status].label}
              </Tag>
            )}
            {selectedVersion?.status === 'production' && (
              <Tag color="gold" icon={<StarFilled />}>{t('projects.production')}</Tag>
            )}
          </Space>
        }
        open={versionDetailOpen}
        onCancel={() => setVersionDetailOpen(false)}
        footer={
          selectedVersion && (
            <Space>
              <Button
                icon={<SyncOutlined />}
                onClick={() => handleRedeploy(selectedVersion)}
                disabled={getVersionDeployments(selectedVersion).length === 0}
              >
                {t('projects.redeploy')}
              </Button>
              <Button
                icon={<ExportOutlined />}
                href={selectedVersion.testUrl || undefined}
                target={selectedVersion.testUrl ? "_blank" : undefined}
                disabled={!selectedVersion.testUrl}
              >
                {t('projects.openTestEnv')}
              </Button>
              <Button
                type="primary"
                icon={<RocketOutlined />}
                onClick={() => {
                  const project = projects.find(p => p.id === selectedVersion.projectId)
                  if (project) handleRequestSwitch(project, selectedVersion)
                  setVersionDetailOpen(false)
                }}
                disabled={!(selectedVersion.status === 'testing' && getVersionDeployments(selectedVersion).length > 0)}
              >
                {t('projects.requestOnline')}
              </Button>
            </Space>
          )
        }
        width={900}
      >
        {selectedVersion && (
          <div className="space-y-4">
            {/* 基本信息 */}
            <Descriptions bordered column={2} size="small">
              <Descriptions.Item label={t('projects.versionCodename')}>
                <span className="text-lg font-medium">{selectedVersion.codename}</span>
              </Descriptions.Item>
              <Descriptions.Item label={t('projects.status')}>
                <Tag color={vsc[selectedVersion.status].color}>
                  {vsc[selectedVersion.status].label}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label={t('projects.imageVersion')}>
                <code className="bg-gray-100 px-2 py-0.5 rounded text-sm">
                  {selectedVersion.imageUrl?.split(':').pop()}
                </code>
              </Descriptions.Item>
              <Descriptions.Item label={t('projects.owner')}>
                <Space>
                  <UserOutlined />
                  {selectedVersion.owner}
                </Space>
              </Descriptions.Item>
            </Descriptions>

            {/* 测试链接 */}
            {selectedVersion.testUrl && (
              <Card size="small" title={t('projects.testLink')} className="bg-blue-50">
                <Space>
                  <LinkOutlined />
                  <Link href={selectedVersion.testUrl} target="_blank">
                    {selectedVersion.testUrl}
                  </Link>
                  <Button
                    size="small"
                    icon={<CopyOutlined />}
                    onClick={() => handleCopy(selectedVersion.testUrl!, t('projects.testLink'))}
                  >
                    {t('projects.copy')}
                  </Button>
                  <Button
                    size="small"
                    icon={<ExportOutlined />}
                    href={selectedVersion.testUrl}
                    target="_blank"
                  >
                    {t('projects.open')}
                  </Button>
                </Space>
              </Card>
            )}

            {/* 部署详情 */}
            {(() => {
              const versionDeps = getVersionDeployments(selectedVersion)
              if (versionDeps.length === 0) {
                return (
                  <Alert
                    message={t('projects.notDeployedAlert')}
                    description={t('projects.triggerDeployDesc')}
                    type="warning"
                    showIcon
                  />
                )
              }
              const regions = getVersionRegions(selectedVersion)
              return (
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <Text strong>{t('projects.deployDetails')}</Text>
                    <Space>
                      <GlobalOutlined />
                      {regions.map(r => (
                        <Tag key={r}>{r}</Tag>
                      ))}
                    </Space>
                  </div>
                  <Table
                    dataSource={versionDeps}
                    columns={versionDeploymentColumns}
                    rowKey="id"
                    pagination={false}
                    size="small"
                    expandable={{
                      expandedRowRender: (record) => (
                        <div className="p-2 bg-gray-50 space-y-2 text-xs">
                          <div className="flex items-center gap-4">
                            <span className="text-gray-500 w-20">{t('projects.gitRepo')}</span>
                            <a href={record.gitRepo} target="_blank" rel="noopener noreferrer">
                              <GithubOutlined className="mr-1" />
                              {record.gitRepo.replace('https://github.com/', '')}
                            </a>
                          </div>
                          <div className="flex items-center gap-4">
                            <span className="text-gray-500 w-20">{t('projects.branchCommit')}</span>
                            <code className="bg-gray-200 px-2 py-0.5 rounded">{record.gitBranch}</code>
                            <span className="text-gray-400">@</span>
                            <a href={record.gitCommitUrl} target="_blank" rel="noopener noreferrer" className="text-blue-500">
                              {record.gitCommit.substring(0, 7)}
                            </a>
                          </div>
                          <div className="flex items-center gap-4">
                            <span className="text-gray-500 w-20">ArgoCD:</span>
                            <a href={record.argocdUrl} target="_blank" rel="noopener noreferrer" className="text-blue-500">
                              <LinkOutlined className="mr-1" />
                              {record.argocdApp}
                            </a>
                          </div>
                          <div className="flex items-center gap-4">
                            <span className="text-gray-500 w-20">{t('projects.image')}</span>
                            <code className="bg-gray-200 px-2 py-0.5 rounded">{record.imageVersion}</code>
                          </div>
                          <div className="flex items-center gap-4">
                            <span className="text-gray-500 w-20">{t('projects.resources')}</span>
                            <span>{record.cpu} CPU / {record.memory} Memory</span>
                            <span className="text-gray-400 ml-4">{t('projects.replicas')} {record.replicas}</span>
                          </div>
                        </div>
                      ),
                      rowExpandable: () => true,
                    }}
                  />
                </div>
              )
            })()}

            {/* Git 信息 */}
            <Card size="small" title={t('projects.gitInfo')}>
              <Space split={<Divider type="vertical" />}>
                <span>
                  <GithubOutlined className="mr-1" />
                  {t('projects.branch')} <code className="bg-gray-100 px-2 py-0.5 rounded">{selectedVersion.gitBranch}</code>
                </span>
                <span>
                  {t('projects.createdAt')} {new Date(selectedVersion.createdAt).toLocaleString()}
                </span>
              </Space>
            </Card>
          </div>
        )}
      </Modal>

      {/* 新建版本弹窗 - 增强 */}
      <Modal
        title={t('projects.createNewVersion')}
        open={newVersionModalOpen}
        onCancel={() => setNewVersionModalOpen(false)}
        onOk={handleSubmitVersion}
        okText={t('projects.createAndDeploy')}
        width={650}
      >
        <Alert
          message={
            <span>
              <strong>🚀 Vibe Coding:</strong> Creating a version triggers CI/CD build and deploys to test env
            </span>
          }
          type="info"
          showIcon
          className="mb-4"
        />
        <Form form={versionForm} layout="vertical">
          <Form.Item label={t('projects.belongProject')} name="projectName">
            <Input disabled />
          </Form.Item>
          <Form.Item name="projectCode" hidden>
            <Input />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label={t('projects.versionCodename')}
                name="codename"
                rules={[{ required: true, message: 'Please enter codename' }]}
                extra="{t('projects.codenameExample')}"
              >
                <Input placeholder={t('projects.inputCodename')} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label={t('projects.owner')}
                name="owner"
                rules={[{ required: true }]}
              >
                <Input placeholder={t('projects.ownerPlaceholder')} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label={t('projects.gitBranch')}
                name="gitBranch"
                rules={[{ required: true }]}
              >
                <Input placeholder="feature/xxx or main" prefix={<GithubOutlined />} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label={t('projects.imageAddress')}
                name="imageUrl"
                rules={[{ required: true }]}
              >
                <Input placeholder="harbor.local/project:image-tag" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item
            label={t('projects.deployRegions')}
            extra={t('projects.selectDeployRegions')}
          >
            <Select
              mode="multiple"
              placeholder="Select deploy regions"
              value={selectedRegions}
              onChange={setSelectedRegions}
              style={{ width: '100%' }}
              options={regions.map(r => ({
                value: r.id,
                label: (
                  <Space>
                    <GlobalOutlined />
                    {r.name}
                    <Text type="secondary" className="text-xs">({r.id})</Text>
                  </Space>
                ),
              }))}
            />
          </Form.Item>
          <Form.Item
            label={t('projects.testLinkAuto')}
            extra="Test URL will be auto-generated"
          >
            <Input
              prefix={<LinkOutlined />}
              placeholder="https://project-codename.test.internal"
              disabled
              className="bg-gray-50"
            />
          </Form.Item>
          <Form.Item label={t('projects.description')} name="description">
            <TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>

      {/* 版本切换申请弹窗 - VC-003 增强 */}
      <Modal
        title={
          <Space>
            <RocketOutlined style={{ color: '#52c41a' }} />
            <span>{t('projects.requestSwitchProd')}</span>
          </Space>
        }
        open={switchRequestModalOpen}
        onCancel={() => setSwitchRequestModalOpen(false)}
        onOk={handleSubmitSwitchRequest}
        okText={t('projects.submitRequest')}
        width={750}
      >
        <Alert
          message={
            <span>
              <strong>📋 Approval Process:</strong> Submit Request → Admin Review → Auto Deploy to Prod
            </span>
          }
          type="info"
          showIcon
          className="mb-4"
        />
        <Form form={switchForm} layout="vertical">
          {/* 项目和版本信息 */}
          <Card size="small" title={t('projects.versionInfo')} className="mb-4">
            <Row gutter={16}>
              <Col span={8}>
                <Form.Item label="Project" name="projectName">
                  <Input disabled />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item label={t('projects.currentProdVersion')} name="fromVersionCodename">
                  <Input disabled />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item label={t('projects.targetVersion')} name="toVersionCodename">
                  <Input disabled className="font-medium text-green-600" />
                </Form.Item>
              </Col>
            </Row>
            <Row gutter={16}>
              <Col span={8}>
                <Form.Item label={t('projects.gitBranch')} name="gitBranch">
                  <Input disabled prefix={<GithubOutlined />} />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item label="Git Commit" name="gitCommit">
                  <Input disabled className="font-mono text-xs" />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item label={t('projects.imageVersion')} name="imageVersion">
                  <Input disabled className="font-mono text-xs" />
                </Form.Item>
              </Col>
            </Row>
            <Form.Item label={t('projects.testLink')} name="testUrl">
              <Input
                disabled
                prefix={<LinkOutlined />}
                addonAfter={
                  <Button
                    type="link"
                    size="small"
                    icon={<ExportOutlined />}
                    href={switchForm.getFieldValue('testUrl')}
                    target="_blank"
                  >
                    打开
                  </Button>
                }
              />
            </Form.Item>
          </Card>

          {/* 部署配置 */}
          <Card size="small" title={t('projects.deployConfig')} className="mb-4">
            <Form.Item
              label={t('projects.deployRegions')}
              required
              extra={t('projects.selectProdRegions')}
            >
              <Select
                mode="multiple"
                value={productionDeployRegions}
                onChange={setProductionDeployRegions}
                style={{ width: '100%' }}
                options={regions.map(r => ({
                  value: r.id,
                  label: (
                    <Space>
                      <GlobalOutlined />
                      {r.name}
                    </Space>
                  ),
                }))}
              />
            </Form.Item>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  label={t('projects.deployStrategy')}
                  name="deployStrategy"
                  initialValue="rolling"
                >
                  <Select
                    options={[
                      { value: 'rolling', label: t('projects.rollingUpdate') },
                      { value: 'blue-green', label: t('projects.blueGreen') },
                      { value: 'canary', label: t('projects.canary') },
                    ]}
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  label={t('projects.deployOrder')}
                  name="deployOrder"
                  initialValue="sequential"
                >
                  <Select
                    options={[
                      { value: 'sequential', label: t('projects.sequential') },
                      { value: 'parallel', label: t('projects.parallel') },
                    ]}
                  />
                </Form.Item>
              </Col>
            </Row>
          </Card>

          {/* 上线说明 */}
          <Card size="small" title={t('projects.releaseNotes')}>
            <Form.Item
              label={t('projects.changes')}
              name="changeSummary"
              rules={[{ required: true, message: 'Please describe changes' }]}
            >
              <TextArea
                rows={2}
                placeholder="Briefly describe main changes..."
              />
            </Form.Item>
            <Form.Item
              label={t('projects.testResults')}
              name="testResults"
              rules={[{ required: true, message: 'Please describe test results' }]}
            >
              <TextArea
                rows={2}
                placeholder="Describe functional, performance test results..."
              />
            </Form.Item>
            <Form.Item
              label={t('projects.riskAssessment')}
              name="riskAssessment"
            >
              <TextArea rows={2} />
            </Form.Item>
            <Form.Item
              label={t('projects.rollbackPlan')}
              name="rollbackPlan"
            >
              <TextArea rows={2} />
            </Form.Item>
          </Card>
        </Form>
      </Modal>

      {/* 新建项目弹窗 */}
      <Modal
        title={t('projects.newProject')}
        open={newProjectModalOpen}
        onCancel={() => setNewProjectModalOpen(false)}
        onOk={() => {
          projectForm.validateFields().then(() => {
            message.success('Project created successfully!')
            setNewProjectModalOpen(false)
            projectForm.resetFields()
          })
        }}
        okText={t('projects.createProject')}
      >
        <Form form={projectForm} layout="vertical" className="mt-4">
          <Form.Item label={t('projects.projectName')} name="name" rules={[{ required: true }]}>
            <Input placeholder="Pipecat-App-B" />
          </Form.Item>
          <Form.Item label={t('projects.projectCode')} name="code" rules={[{ required: true }]}>
            <Input placeholder="pipecat-app-b" />
          </Form.Item>
          <Form.Item label={t('projects.description')} name="description">
            <TextArea rows={2} />
          </Form.Item>
          <Form.Item label={t('projects.owner')} name="owner" rules={[{ required: true }]}>
            <Input placeholder={t('projects.ownerPlaceholder')} />
          </Form.Item>
        </Form>
      </Modal>

      {/* 部署进度弹窗 */}
      <Modal
        title={
          <Space>
            <RocketOutlined style={{ color: '#1890ff' }} />
            <span>{t('projects.deployProgress')}</span>
            {deploymentProgress && (
              <Tag color="blue">{deploymentProgress.codename}</Tag>
            )}
          </Space>
        }
        open={deploymentProgressModalOpen}
        onCancel={() => {
          if (deploymentProgress?.step === 'completed') {
            setDeploymentProgressModalOpen(false)
            setDeploymentProgress(null)
          }
        }}
        footer={
          deploymentProgress?.step === 'completed' ? (
            <Space>
              <Button
                icon={<ExportOutlined />}
                href={deploymentProgress.testUrl}
                target="_blank"
              >
                {t('projects.openTestEnv')}
              </Button>
              <Button
                type="primary"
                icon={<RocketOutlined />}
                onClick={() => {
                  setDeploymentProgressModalOpen(false)
                  const version = allVersions.find(v => v.codename === deploymentProgress.codename)
                  if (version) {
                    const project = projects.find(p => p.id === version.projectId)
                    if (project) {
                      handleRequestSwitch(project, version)
                    }
                  }
                }}
              >
                {t('projects.requestOnline')}
              </Button>
            </Space>
          ) : null
        }
        width={600}
        closable={deploymentProgress?.step === 'completed'}
        maskClosable={false}
      >
        {deploymentProgress && (
          <div className="space-y-6">
            {/* 整体进度条 */}
            <div className="text-center">
              <Progress
                type="circle"
                percent={deploymentProgress.progress}
                status={deploymentProgress.step === 'completed' ? 'success' : 'active'}
                strokeColor={{
                  '0%': '#108ee9',
                  '100%': '#87d068',
                }}
              />
            </div>

            {/* 部署步骤 */}
            <Steps
              current={
                deploymentProgress.step === 'building' ? 0 :
                deploymentProgress.step === 'deploying' ? 1 :
                deploymentProgress.step === 'healthcheck' ? 2 :
                deploymentProgress.step === 'completed' ? 3 : -1
              }
              status={deploymentProgress.step === 'failed' ? 'error' : 'process'}
              items={[
                {
                  title: t('projects.cicdBuild'),
                  icon: deploymentProgress.step === 'building' ? <LoadingOutlined /> : <CloudUploadOutlined />,
                  description: deploymentProgress.step === 'building' ? t('projects.buildingImage') : undefined,
                },
                {
                  title: t('projects.argocdDeploy'),
                  icon: deploymentProgress.step === 'deploying' ? <LoadingOutlined /> : <RocketOutlined />,
                  description: deploymentProgress.step === 'deploying' ? t('projects.deployingTest') : undefined,
                },
                {
                  title: t('projects.healthCheck'),
                  icon: deploymentProgress.step === 'healthcheck' ? <LoadingOutlined /> : <SafetyCertificateOutlined />,
                  description: deploymentProgress.step === 'healthcheck' ? t('projects.checkingHealth') : undefined,
                },
                {
                  title: t('projects.completed'),
                  icon: deploymentProgress.step === 'completed' ? <CheckCircleOutlined /> : undefined,
                },
              ]}
            />

            {/* 当前状态消息 */}
            <Alert
              message={deploymentProgress.message}
              type={deploymentProgress.step === 'completed' ? 'success' : 'info'}
              showIcon
              icon={
                deploymentProgress.step === 'completed' ? <CheckCircleOutlined /> :
                <LoadingOutlined spin />
              }
            />

            {/* 部署区域 */}
            <div>
              <Text type="secondary">Deploy Regions:</Text>
              <div className="mt-2">
                <Space>
                  {deploymentProgress.regions.map(r => (
                    <Tag key={r} icon={<GlobalOutlined />} color="blue">{r}</Tag>
                  ))}
                </Space>
              </div>
            </div>

            {/* 测试链接 */}
            {deploymentProgress.testUrl && (
              <div>
                <Text type="secondary">{t('projects.testLink')}</Text>
                <div className="mt-2 flex items-center gap-2">
                  <Input
                    value={deploymentProgress.testUrl}
                    readOnly
                    style={{ flex: 1 }}
                  />
                  <Button
                    icon={<CopyOutlined />}
                    onClick={() => handleCopy(deploymentProgress!.testUrl, t('projects.testLink'))}
                  >
                    {t('projects.copy')}
                  </Button>
                  {deploymentProgress.step === 'completed' && (
                    <Button
                      type="primary"
                      icon={<ExportOutlined />}
                      href={deploymentProgress.testUrl}
                      target="_blank"
                    >
                      {t('projects.open')}
                    </Button>
                  )}
                </div>
              </div>
            )}

            {/* 完成后的提示 */}
            {deploymentProgress.step === 'completed' && (
              <Result
                status="success"
                title={t('projects.deploySuccess')}
                subTitle={`Version ${deploymentProgress.codename} ${t('projects.deploySuccessDesc')}`}
              />
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
