import { useState } from 'react'
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
} from 'antd'
import {
  PlusOutlined,
  EyeOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  RocketOutlined,
  BranchesOutlined,
  HistoryOutlined,
  CodeOutlined,
  LinkOutlined,
  UserOutlined,
  CopyOutlined,
  StarFilled,
} from '@ant-design/icons'
import {
  useVersionStore,
  type Version,
  type Project,
  type VersionSwitchRequest,
  type VersionStatus,
} from '../stores/versionStore'

const { Title, Text } = Typography
const { TextArea } = Input

// 版本状态配置 - 简化
const versionStatusConfig: Record<VersionStatus, { color: string; label: string; icon: React.ReactNode }> = {
  testing: { color: 'orange', label: '测试版本', icon: <ClockCircleOutlined /> },
  production: { color: 'green', label: '生产版本', icon: <StarFilled /> },
  archived: { color: 'default', label: '已归档', icon: <HistoryOutlined /> },
}

// 环境颜色
const envColors: Record<string, string> = {
  dev: 'blue',
  staging: 'orange',
  production: 'red',
}

export default function Projects() {
  const [activeTab, setActiveTab] = useState('versions')
  const [selectedVersion, setSelectedVersion] = useState<Version | null>(null)
  const [versionDetailOpen, setVersionDetailOpen] = useState(false)
  const [newVersionModalOpen, setNewVersionModalOpen] = useState(false)
  const [switchRequestModalOpen, setSwitchRequestModalOpen] = useState(false)
  const [newProjectModalOpen, setNewProjectModalOpen] = useState(false)
  const [versionForm] = Form.useForm()
  const [switchForm] = Form.useForm()
  const [projectForm] = Form.useForm()
  const [currentProjectId, setCurrentProjectId] = useState<string | null>(null)

  const {
    projects,
    switchRequests,
    addVersion,
    createSwitchRequest,
    approveSwitchRequest,
    rejectSwitchRequest,
  } = useVersionStore()

  // 创建新版本
  const handleCreateVersion = (projectId: string) => {
    setCurrentProjectId(projectId)
    const project = projects.find(p => p.id === projectId)
    versionForm.setFieldsValue({
      projectId,
      projectName: project?.name,
    })
    setNewVersionModalOpen(true)
  }

  const handleSubmitVersion = () => {
    versionForm.validateFields().then((values) => {
      addVersion(currentProjectId!, {
        codename: values.codename,
        description: values.description,
        gitBranch: values.gitBranch,
        imageUrl: values.imageUrl,
        owner: values.owner,
        testUrl: values.testUrl,
        environments: ['dev'],
      })
      message.success(`版本 "${values.codename}" 创建成功!`)
      setNewVersionModalOpen(false)
      versionForm.resetFields()
    })
  }

  // 申请切换生产版本
  const handleRequestSwitch = (project: Project, version: Version) => {
    const currentProd = project.versions.find(v => v.id === project.productionVersionId)
    switchForm.setFieldsValue({
      projectId: project.id,
      projectName: project.name,
      fromVersionId: currentProd?.id,
      fromVersionCodename: currentProd?.codename,
      toVersionId: version.id,
      toVersionCodename: version.codename,
    })
    setSwitchRequestModalOpen(true)
  }

  const handleSubmitSwitchRequest = () => {
    switchForm.validateFields().then((values) => {
      createSwitchRequest({
        projectId: values.projectId,
        projectName: values.projectName,
        fromVersionId: values.fromVersionId,
        fromVersionCodename: values.fromVersionCodename,
        toVersionId: values.toVersionId,
        toVersionCodename: values.toVersionCodename,
        reason: values.reason,
        requester: 'Current User', // 实际应从 auth store 获取
        createdAt: new Date().toISOString(),
      })
      message.success('版本切换申请已提交，等待 Admin 审批')
      setSwitchRequestModalOpen(false)
      switchForm.resetFields()
    })
  }

  // 审批
  const handleApproveRequest = (requestId: string) => {
    approveSwitchRequest(requestId, 'Admin')
    message.success('已批准版本切换!')
  }

  const handleRejectRequest = (requestId: string) => {
    rejectSwitchRequest(requestId, 'Admin')
    message.warning('已拒绝版本切换申请')
  }

  // 复制测试链接
  const handleCopyTestUrl = (url: string) => {
    navigator.clipboard.writeText(url)
    message.success('测试链接已复制到剪贴板')
  }

  // 获取所有版本的扁平列表
  const allVersions = projects.flatMap(p =>
    p.versions.map(v => ({
      ...v,
      projectName: p.name,
      projectCode: p.code,
      isProduction: p.productionVersionId === v.id,
    }))
  )

  // 版本列表列定义
  const versionColumns = [
    {
      title: '项目',
      dataIndex: 'projectName',
      key: 'projectName',
      width: 140,
      render: (name: string, record: Version & { projectCode: string }) => (
        <div>
          <div className="font-medium">{name}</div>
          <Text type="secondary" className="text-xs">{record.projectCode}</Text>
        </div>
      ),
    },
    {
      title: '版本代号',
      dataIndex: 'codename',
      key: 'codename',
      width: 120,
      render: (codename: string, record: Version & { isProduction: boolean }) => (
        <Space>
          {record.isProduction && (
            <Tooltip title="当前生产版本">
              <StarFilled className="text-yellow-500" />
            </Tooltip>
          )}
          <span className="font-medium">{codename}</span>
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: VersionStatus) => {
        const config = versionStatusConfig[status]
        return <Tag color={config.color} icon={config.icon}>{config.label}</Tag>
      },
    },
    {
      title: '环境',
      dataIndex: 'environments',
      key: 'environments',
      width: 120,
      render: (envs: string[]) => (
        <Space size={4}>
          {envs.map(env => (
            <Tag key={env} color={envColors[env] || 'default'} style={{ margin: 0 }}>
              {env}
            </Tag>
          ))}
        </Space>
      ),
    },
    {
      title: '测试链接',
      dataIndex: 'testUrl',
      key: 'testUrl',
      width: 180,
      ellipsis: true,
      render: (url: string | undefined) => url ? (
        <Space size={4}>
          <Tooltip title={url}>
            <Text className="text-primary-500" style={{ maxWidth: 120 }} ellipsis>
              {url.replace('https://', '')}
            </Text>
          </Tooltip>
          <Button
            type="text"
            size="small"
            icon={<CopyOutlined />}
            onClick={() => handleCopyTestUrl(url)}
            style={{ padding: '0 4px' }}
          />
        </Space>
      ) : (
        <Text type="secondary">-</Text>
      ),
    },
    {
      title: '负责人',
      dataIndex: 'owner',
      key: 'owner',
      width: 90,
    },
    {
      title: '更新时间',
      dataIndex: 'updatedAt',
      key: 'updatedAt',
      width: 100,
      render: (date: string) => new Date(date).toLocaleDateString(),
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_: unknown, record: Version & { isProduction: boolean; projectName: string }) => {
        const project = projects.find(p => p.id === record.projectId)
        return (
          <Space size={4}>
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => {
                setSelectedVersion(record)
                setVersionDetailOpen(true)
              }}
            >
              详情
            </Button>
            {record.status === 'testing' && !record.isProduction && (
              <Tooltip title="申请切换为生产版本">
                <Button
                  type="link"
                  size="small"
                  icon={<RocketOutlined />}
                  onClick={() => handleRequestSwitch(project!, record)}
                >
                  上线
                </Button>
              </Tooltip>
            )}
          </Space>
        )
      },
    },
  ]

  // 审批请求列定义
  const requestColumns = [
    {
      title: '项目',
      dataIndex: 'projectName',
      key: 'projectName',
    },
    {
      title: '版本切换',
      key: 'versionChange',
      render: (_: unknown, record: VersionSwitchRequest) => (
        <Space>
          <Tag>{record.fromVersionCodename}</Tag>
          <span>→</span>
          <Tag color="blue">{record.toVersionCodename}</Tag>
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const config: Record<string, { color: string; label: string }> = {
          pending: { color: 'orange', label: '待审批' },
          approved: { color: 'green', label: '已批准' },
          rejected: { color: 'red', label: '已拒绝' },
          completed: { color: 'blue', label: '已完成' },
        }
        const { color, label } = config[status] || { color: 'default', label: status }
        return <Tag color={color}>{label}</Tag>
      },
    },
    {
      title: '申请人',
      dataIndex: 'requester',
      key: 'requester',
    },
    {
      title: '申请时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: unknown, record: VersionSwitchRequest) =>
        record.status === 'pending' ? (
          <Space>
            <Popconfirm
              title="确认批准此版本切换?"
              description="批准后将切换生产版本"
              onConfirm={() => handleApproveRequest(record.id)}
            >
              <Button type="link" size="small" style={{ color: '#22c55e' }}>
                批准
              </Button>
            </Popconfirm>
            <Popconfirm
              title="确认拒绝此申请?"
              onConfirm={() => handleRejectRequest(record.id)}
            >
              <Button type="link" size="small" danger>
                拒绝
              </Button>
            </Popconfirm>
          </Space>
        ) : (
          <Text type="secondary">-</Text>
        ),
    },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <Title level={4} className="m-0">项目版本管理</Title>
        <Space>
          <Button icon={<HistoryOutlined />}>审计日志</Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setNewProjectModalOpen(true)}
          >
            新建项目
          </Button>
        </Space>
      </div>

      {/* Summary Cards */}
      <Row gutter={16}>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="项目总数"
              value={projects.length}
              prefix={<BranchesOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="生产版本"
              value={allVersions.filter(v => v.status === 'production').length}
              prefix={<StarFilled style={{ color: '#fbbf24' }} />}
              valueStyle={{ color: '#22c55e' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="测试版本"
              value={allVersions.filter(v => v.status === 'testing').length}
              prefix={<ClockCircleOutlined style={{ color: '#f97316' }} />}
              valueStyle={{ color: '#f97316' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="待审批"
              value={switchRequests.filter(r => r.status === 'pending').length}
              prefix={<ExclamationCircleOutlined style={{ color: '#ef4444' }} />}
              valueStyle={{ color: switchRequests.filter(r => r.status === 'pending').length > 0 ? '#ef4444' : undefined }}
            />
          </Card>
        </Col>
      </Row>

      {/* 提示信息 */}
      <Alert
        message={
          <span>
            <strong>版本管理说明：</strong>
            每个版本有独立的代号（如 Phoenix、Titan）。测试版本可并行运行，各版本有独立的测试 URL。
            切换生产版本需要 Admin 审批。
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
                版本列表
              </span>
            ),
            children: (
              <Card>
                <div className="mb-4">
                  <Space>
                    <Select
                      placeholder="筛选项目"
                      allowClear
                      style={{ width: 200 }}
                      options={projects.map(p => ({ value: p.id, label: p.name }))}
                    />
                    <Select
                      placeholder="筛选状态"
                      allowClear
                      style={{ width: 150 }}
                      options={Object.entries(versionStatusConfig).map(([key, val]) => ({
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
                  scroll={{ x: 1200 }}
                />
              </Card>
            ),
          },
          {
            key: 'projects',
            label: (
              <span>
                <BranchesOutlined />
                项目列表
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
                            新建版本
                          </Button>
                        }
                      >
                        <Descriptions column={2} size="small">
                          <Descriptions.Item label="当前生产版本">
                            {prodVersion && (
                              <Tag color="green" icon={<StarFilled />}>
                                {prodVersion.codename}
                              </Tag>
                            )}
                          </Descriptions.Item>
                          <Descriptions.Item label="负责人">
                            {project.owner}
                          </Descriptions.Item>
                          <Descriptions.Item label="版本总数" span={2}>
                            {project.versions.length} 个版本
                            (测试中: {testingVersions.length})
                          </Descriptions.Item>
                        </Descriptions>

                        {testingVersions.length > 0 && (
                          <div className="mt-4">
                            <Text type="secondary" className="text-xs">测试版本:</Text>
                            <div className="mt-2 flex flex-wrap gap-2">
                              {testingVersions.map(v => (
                                <Tag key={v.id} color="orange">
                                  {v.codename}
                                  {v.testUrl && (
                                    <Tooltip title="复制测试链接">
                                      <CopyOutlined
                                        className="ml-1 cursor-pointer"
                                        onClick={() => handleCopyTestUrl(v.testUrl!)}
                                      />
                                    </Tooltip>
                                  )}
                                </Tag>
                              ))}
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
                切换审批
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

      {/* 版本详情弹窗 */}
      <Modal
        title={
          <Space>
            <span>版本详情</span>
            {selectedVersion?.status === 'production' && (
              <Tag color="gold" icon={<StarFilled />}>生产版本</Tag>
            )}
          </Space>
        }
        open={versionDetailOpen}
        onCancel={() => setVersionDetailOpen(false)}
        footer={null}
        width={700}
      >
        {selectedVersion && (
          <div className="space-y-4">
            <Descriptions bordered column={2}>
              <Descriptions.Item label="版本代号">
                <span className="text-lg font-medium">{selectedVersion.codename}</span>
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={versionStatusConfig[selectedVersion.status].color}>
                  {versionStatusConfig[selectedVersion.status].label}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Git 分支">
                <Space>
                  <CodeOutlined />
                  <code className="bg-gray-100 px-2 py-0.5 rounded text-sm">
                    {selectedVersion.gitBranch}
                  </code>
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="负责人">
                <Space>
                  <UserOutlined />
                  {selectedVersion.owner}
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="镜像地址" span={2}>
                <code className="bg-gray-100 px-2 py-1 rounded text-xs block">
                  {selectedVersion.imageUrl}
                </code>
              </Descriptions.Item>
              <Descriptions.Item label="描述" span={2}>
                {selectedVersion.description}
              </Descriptions.Item>
              <Descriptions.Item label="已部署环境">
                <Space>
                  {selectedVersion.environments.map(env => (
                    <Tag key={env} color={envColors[env]}>{env}</Tag>
                  ))}
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">
                {new Date(selectedVersion.createdAt).toLocaleString()}
              </Descriptions.Item>
            </Descriptions>

            {selectedVersion.testUrl && (
              <Card size="small" title="测试链接" className="bg-gray-50">
                <Space>
                  <LinkOutlined />
                  <a href={selectedVersion.testUrl} target="_blank" rel="noopener noreferrer">
                    {selectedVersion.testUrl}
                  </a>
                  <Button
                    size="small"
                    icon={<CopyOutlined />}
                    onClick={() => handleCopyTestUrl(selectedVersion.testUrl!)}
                  >
                    复制
                  </Button>
                </Space>
              </Card>
            )}
          </div>
        )}
      </Modal>

      {/* 新建版本弹窗 */}
      <Modal
        title="创建新版本"
        open={newVersionModalOpen}
        onCancel={() => setNewVersionModalOpen(false)}
        onOk={handleSubmitVersion}
        okText="创建版本"
        width={600}
      >
        <Alert
          message="创建新版本无需审批，创建后默认为测试版本"
          type="info"
          showIcon
          className="mb-4"
        />
        <Form form={versionForm} layout="vertical">
          <Form.Item label="所属项目" name="projectName">
            <Input disabled />
          </Form.Item>
          <Form.Item
            label="版本代号"
            name="codename"
            rules={[{ required: true, message: '请输入版本代号' }]}
            extra="如: Phoenix, Titan, Nova 等"
          >
            <Input placeholder="输入内部代号" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="Git 分支"
                name="gitBranch"
                rules={[{ required: true }]}
              >
                <Input placeholder="feature/xxx 或 main" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="负责人"
                name="owner"
                rules={[{ required: true }]}
              >
                <Input placeholder="负责人姓名" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item
            label="镜像地址"
            name="imageUrl"
            rules={[{ required: true }]}
          >
            <Input placeholder="harbor.local/project:image-tag" />
          </Form.Item>
          <Form.Item
            label="测试链接"
            name="testUrl"
            extra="测试版本的访问地址"
          >
            <Input placeholder="https://xxx.test.internal" />
          </Form.Item>
          <Form.Item label="描述" name="description">
            <TextArea rows={2} placeholder="版本描述、主要变更等" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 版本切换申请弹窗 */}
      <Modal
        title="申请切换生产版本"
        open={switchRequestModalOpen}
        onCancel={() => setSwitchRequestModalOpen(false)}
        onOk={handleSubmitSwitchRequest}
        okText="提交申请"
        width={600}
      >
        <Alert
          message="切换生产版本需要 Admin 审批"
          type="warning"
          showIcon
          className="mb-4"
        />
        <Form form={switchForm} layout="vertical">
          <Form.Item label="项目" name="projectName">
            <Input disabled />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="当前生产版本" name="fromVersionCodename">
                <Input disabled />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="目标版本" name="toVersionCodename">
                <Input disabled />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item
            label="切换原因"
            name="reason"
            rules={[{ required: true, message: '请说明切换原因' }]}
          >
            <TextArea
              rows={4}
              placeholder="请详细说明为什么要切换到此版本，测试结果如何..."
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 新建项目弹窗 */}
      <Modal
        title="新建项目"
        open={newProjectModalOpen}
        onCancel={() => setNewProjectModalOpen(false)}
        onOk={() => {
          projectForm.validateFields().then(() => {
            message.success('项目创建成功!')
            setNewProjectModalOpen(false)
            projectForm.resetFields()
          })
        }}
        okText="创建项目"
      >
        <Form form={projectForm} layout="vertical" className="mt-4">
          <Form.Item label="项目名称" name="name" rules={[{ required: true }]}>
            <Input placeholder="Pipecat-App-B" />
          </Form.Item>
          <Form.Item label="项目代码" name="code" rules={[{ required: true }]}>
            <Input placeholder="pipecat-app-b" />
          </Form.Item>
          <Form.Item label="描述" name="description">
            <TextArea rows={2} />
          </Form.Item>
          <Form.Item label="负责人" name="owner" rules={[{ required: true }]}>
            <Input placeholder="负责人姓名" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
