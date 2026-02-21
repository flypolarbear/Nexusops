import { useState, useMemo } from 'react'
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
  Row,
  Col,
  Tooltip,
  Descriptions,
  message,
  Alert,
  Result,
  Steps,
  Menu,
} from 'antd'
import {
  AppstoreOutlined,
  PlusOutlined,
  RocketOutlined,
  HistoryOutlined,
  StarFilled,
  GithubOutlined,
  ProjectOutlined,
} from '@ant-design/icons'
import { useVersionStore, type Service, type Version, type VersionStatus } from '../stores/versionStore'
import { useDeploymentStore } from '../stores/deploymentStore'

const { Title, Text } = Typography
const { TextArea } = Input

type DeployStep = 'init' | 'building' | 'deploying' | 'healthcheck' | 'completed'

interface DeploymentProgress {
  codename: string
  step: DeployStep
  progress: number
  testUrl: string
  regions: string[]
  message: string
  buildLog?: string
  deployLog?: string
}

export default function Projects() {
  const [selectedService, setSelectedService] = useState<Service | null>(null)
  const [selectedVersion, setSelectedVersion] = useState<Version | null>(null)
  
  const [versionDetailOpen, setVersionDetailOpen] = useState(false)
  const [newVersionModalOpen, setNewVersionModalOpen] = useState(false)
  const [switchRequestModalOpen, setSwitchRequestModalOpen] = useState(false)
  const [newProjectModalOpen, setNewProjectModalOpen] = useState(false)
  const [newServiceModalOpen, setNewServiceModalOpen] = useState(false)
  
  const [deploymentProgressModalOpen, setDeploymentProgressModalOpen] = useState(false)
  const [deploymentProgress, setDeploymentProgress] = useState<DeploymentProgress | null>(null)
  const [productionDeployRegions, setProductionDeployRegions] = useState<string[]>([])
  
  const [versionForm] = Form.useForm()
  const [switchForm] = Form.useForm()
  const [projectForm] = Form.useForm()
  const [serviceForm] = Form.useForm()
  const [selectedRegions, setSelectedRegions] = useState<string[]>([])

  const {
    projects,
    switchRequests,
    currentProjectId,
    setCurrentProject,
    addProject,
    addService,
    addVersion,
    createSwitchRequest,
    approveSwitchRequest,
    rejectSwitchRequest,
  } = useVersionStore()

  const {
    regions,
  } = useDeploymentStore()

  const currentProject = useMemo(() => {
    return projects.find(p => p.id === currentProjectId) || projects[0]
  }, [projects, currentProjectId])
  // Using to satisfy TS even if unused locally
  console.log(currentProject)

  const generateTestUrl = (serviceName: string, codename: string) => {
    const codenameSlug = codename.toLowerCase().replace(/\s+/g, '-')
    return `https://${serviceName}-${codenameSlug}.test.pipecat.internal`
  }

  // Handle forms
  const handleCreateProject = async () => {
    try {
      const values = await projectForm.validateFields()
      addProject({
        name: values.name,
        code: values.code,
        description: values.description || '',
        owner: values.owner,
      })
      setNewProjectModalOpen(false)
      projectForm.resetFields()
      message.success('Project created successfully!')
    } catch (e) { }
  }

  const handleCreateService = async () => {
    try {
      const values = await serviceForm.validateFields()
      addService(currentProject.id, {
        name: values.name,
        gitRepo: values.gitRepo,
        gitBranch: values.gitBranch,
        owner: values.owner,
      })
      setNewServiceModalOpen(false)
      serviceForm.resetFields()
      message.success(`Service ${values.name} created!`)
    } catch (e) { }
  }

  const handleCreateVersion = (service: Service) => {
    setSelectedService(service)
    versionForm.setFieldsValue({
      gitBranch: service.gitBranch,
      owner: service.owner,
      imageUrl: `harbor.local/${service.name}:`,
    })
    setSelectedRegions([])
    setNewVersionModalOpen(true)
  }

  const handleSubmitVersion = async () => {
    try {
      const values = await versionForm.validateFields()
      const testUrl = generateTestUrl(selectedService!.name, values.codename)
      
      setNewVersionModalOpen(false)
      versionForm.resetFields()
      
      addVersion(currentProject.id, selectedService!.id, {
        codename: values.codename,
        description: values.description || '',
        imageUrl: values.imageUrl,
        owner: values.owner,
        testUrl: testUrl,
        environments: ['testing'],
      })

      if (selectedRegions.length > 0) {
        setDeploymentProgress({
          codename: values.codename,
          step: 'init',
          progress: 0,
          testUrl: testUrl,
          regions: selectedRegions.map(rid => regions.find(r => r.id === rid)?.name || rid),
          message: 'Starting CI/CD build...',
        })
        setDeploymentProgressModalOpen(true)

        // Simulate deployment steps
        let progress = 0
        const interval = setInterval(() => {
          progress += 5
          if (progress < 40) {
            setDeploymentProgress(prev => prev ? { ...prev, step: 'building', progress: Math.round(progress), message: 'Building Docker image...' } : null)
          } else if (progress < 80) {
            setDeploymentProgress(prev => prev ? { ...prev, step: 'deploying', progress: Math.round(progress), message: 'Deploying to test environment...' } : null)
          } else if (progress < 100) {
            setDeploymentProgress(prev => prev ? { ...prev, step: 'healthcheck', progress: Math.round(progress), message: 'Health checking...' } : null)
          } else {
            clearInterval(interval)
            setDeploymentProgress(prev => prev ? { ...prev, step: 'completed', progress: 100, message: 'Deployment completed!' } : null)
            message.success(`Version "${values.codename}" created successfully!`)
          }
        }, 300)
      } else {
        message.success(`Version "${values.codename}" created successfully!`)
      }
    } catch (e) { }
  }

  const handleRequestSwitch = (service: Service, version: Version) => {
    setSelectedService(service)
    const currentProdVersion = service.versions.find(v => v.id === service.productionVersionId)
    
    switchForm.setFieldsValue({
      fromVersionId: currentProdVersion?.id,
      fromVersionCodename: currentProdVersion?.codename || 'None',
      toVersionId: version.id,
      toVersionCodename: version.codename,
      testUrl: version.testUrl,
    })
    setProductionDeployRegions([])
    setSwitchRequestModalOpen(true)
  }

  const handleSubmitSwitchRequest = async () => {
    try {
      const values = await switchForm.validateFields()
      if (productionDeployRegions.length === 0) {
        message.error('Please select at least one deployment region')
        return
      }
      
      createSwitchRequest({
        serviceId: selectedService!.id,
        serviceName: selectedService!.name,
        fromVersionId: values.fromVersionId,
        fromVersionCodename: values.fromVersionCodename,
        toVersionId: values.toVersionId,
        toVersionCodename: values.toVersionCodename,
        reason: `${values.changeSummary}\n\nTest Results: ${values.testResults}${values.riskAssessment ? `\n\nRisk Assessment: ${values.riskAssessment}` : ''}${values.rollbackPlan ? `\n\nRollback Plan: ${values.rollbackPlan}` : ''}`,
        requester: 'Admin',
        deployRegions: productionDeployRegions,
        deployStrategy: values.deployStrategy,
        deployOrder: values.deployOrder,
      })
      
      setSwitchRequestModalOpen(false)
      switchForm.resetFields()
      message.success({
        content: (
          <div>
            <p>Prod request for version <strong>{values.toVersionCodename}</strong> submitted</p>
            <p>Deploy regions: {productionDeployRegions.length}</p>
            <p>Waiting for Admin approval</p>
          </div>
        ),
        duration: 5,
      })
    } catch (e) { }
  }

  const handleRedeploy = (version: Version) => {
    message.loading({ content: `Triggering redeploy for ${version.codename}...`, key: 'redeploy' })
    setTimeout(() => {
      message.success({ content: `Redeploy triggered for ${version.codename}`, key: 'redeploy' })
    }, 1500)
  }

  // @ts-ignore
  const handleCopy = (text: string, label: string) => {
    navigator.clipboard.writeText(text)
    message.success(`${label} copied`)
  }

  // Table Columns
  const versionColumns = [
    {
      title: 'Codename',
      dataIndex: 'codename',
      key: 'codename',
      render: (codename: string, record: Version) => {
        const isProd = selectedService?.productionVersionId === record.id
        return (
          <Space>
            <Text strong>{codename}</Text>
            {isProd && (
              <Tooltip title="Current production version">
                <StarFilled className="text-yellow-500 text-xs" />
              </Tooltip>
            )}
          </Space>
        )
      },
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: VersionStatus) => {
        const colors = {
          testing: 'orange',
          production: 'green',
          archived: 'default'
        }
        return <Tag color={colors[status]}>{status.toUpperCase()}</Tag>
      },
    },
    {
      title: 'Image',
      dataIndex: 'imageUrl',
      key: 'imageUrl',
      render: (url: string) => <code className="text-xs bg-gray-100 px-1 rounded">{url.split('/').pop()}</code>
    },
    {
      title: 'Test URL',
      dataIndex: 'testUrl',
      key: 'testUrl',
      render: (url: string | undefined) => url ? (
        <a href={url} target="_blank" rel="noopener noreferrer" className="text-xs">{url.replace('https://', '')}</a>
      ) : <Text type="secondary">-</Text>
    },
    {
      title: 'Updated',
      dataIndex: 'updatedAt',
      key: 'updatedAt',
      render: (date: string) => <span className="text-xs text-gray-500">{date}</span>
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 250,
      render: (_: unknown, record: Version) => {
        const isTesting = record.status === 'testing'
        const isProd = selectedService?.productionVersionId === record.id
        // @ts-ignore
        const deployments = []
        return (
          <Space>
            <Button size="small" type="link" onClick={() => { setSelectedVersion(record); setVersionDetailOpen(true) }}>Details</Button>
            <Button size="small" type="link" onClick={() => handleRedeploy(record)} disabled={!isTesting && !isProd}>Redeploy</Button>
            <Button size="small" type="link" 
              onClick={() => handleRequestSwitch(selectedService!, record)}
              disabled={!isTesting}
              style={isTesting ? { color: '#22c55e' } : undefined}
            >
              Request Prod
            </Button>
          </Space>
        )
      }
    }
  ]

  return (
    <div className="h-[calc(100vh-64px)] flex bg-white" style={{ margin: '-24px', padding: 0 }}>
      {/* Sidebar - Project List */}
      <div className="w-64 border-r border-gray-200 flex flex-col bg-gray-50 shrink-0 h-full">
        <div className="p-4 border-b border-gray-200 flex justify-between items-center bg-white shrink-0">
          <Text strong>Projects</Text>
          <Button type="text" size="small" icon={<PlusOutlined />} onClick={() => setNewProjectModalOpen(true)} />
        </div>
        <div className="flex-1 overflow-y-auto">
          <Menu
            mode="inline"
            className="border-none bg-transparent"
            selectedKeys={[currentProjectId || '']}
            onClick={(e) => setCurrentProject(e.key)}
            items={projects.map(p => ({
              key: p.id,
              icon: <ProjectOutlined />,
              label: p.name,
            }))}
          />
        </div>
      </div>

      {/* Main Content - Services & Versions */}
      <div className="flex-1 overflow-auto p-6 bg-white min-w-0">
        {currentProject && (
          <div className="space-y-6 max-w-6xl mx-auto">
            <div className="flex justify-between items-start">
              <div>
                <Title level={3} className="m-0 mb-1">{currentProject.name}</Title>
                <Text type="secondary">{currentProject.description}</Text>
              </div>
              <Space>
                <Button icon={<HistoryOutlined />}>Audit Logs</Button>
                <Button type="primary" icon={<PlusOutlined />} onClick={() => setNewServiceModalOpen(true)}>
                  New Service
                </Button>
              </Space>
            </div>

            {/* Pending Approvals Alert */}
            {switchRequests.filter(r => r.status === 'pending').length > 0 && (
              <Alert
                message="Pending Version Switch Approvals"
                description={
                  <ul className="pl-4 mt-2 mb-0 space-y-1">
                    {switchRequests.filter(r => r.status === 'pending').map(req => (
                      <li key={req.id} className="flex justify-between items-center">
                        <span>
                          <strong>{req.serviceName}</strong>: <Tag>{req.fromVersionCodename}</Tag> → <Tag color="green">{req.toVersionCodename}</Tag>
                        </span>
                        <Space size="small">
                          <Button size="small" type="link" onClick={() => approveSwitchRequest(req.id, 'Admin')} style={{color: '#22c55e'}}>Approve</Button>
                          <Button size="small" type="link" danger onClick={() => rejectSwitchRequest(req.id, 'Admin')}>Reject</Button>
                        </Space>
                      </li>
                    ))}
                  </ul>
                }
                type="warning"
                showIcon
                className="mb-4"
              />
            )}

            {/* Services List */}
            <div className="space-y-6">
              {currentProject.services.length === 0 ? (
                <div className="text-center py-12 bg-gray-50 border border-dashed rounded-lg">
                  <Text type="secondary">No services created yet in this project.</Text>
                </div>
              ) : (
                currentProject.services.map(svc => {
                  const prodVer = svc.versions.find(v => v.id === svc.productionVersionId)
                  const testVers = svc.versions.filter(v => v.status === 'testing')
                  
                  return (
                    <Card 
                      key={svc.id} 
                      className="shadow-sm border border-gray-200 overflow-hidden"
                      bodyStyle={{ padding: 0 }}
                    >
                      <div className="bg-gray-50 p-4 border-b border-gray-200 flex justify-between items-center">
                        <Space>
                          <AppstoreOutlined className="text-xl text-primary-500" />
                          <Title level={5} className="m-0">{svc.name}</Title>
                          <a href={svc.gitRepo} target="_blank" rel="noreferrer" className="text-xs text-gray-500 flex items-center ml-2"><GithubOutlined className="mr-1"/> Repository</a>
                        </Space>
                        <Button type="primary" ghost size="small" icon={<PlusOutlined />} onClick={() => handleCreateVersion(svc)}>
                          Create Version
                        </Button>
                      </div>
                      
                      <div className="p-4 grid grid-cols-1 md:grid-cols-4 gap-4 bg-white border-b border-gray-100">
                        <div>
                          <Text type="secondary" className="text-xs uppercase block mb-1">Production</Text>
                          {prodVer ? (
                            <Tag color="green" icon={<StarFilled />}>{prodVer.codename}</Tag>
                          ) : <Text type="secondary" className="text-sm">-</Text>}
                        </div>
                        <div className="md:col-span-2">
                          <Text type="secondary" className="text-xs uppercase block mb-1">Testing Environments</Text>
                          {testVers.length > 0 ? (
                            <Space wrap size={4}>
                              {testVers.map(v => (
                                <Tag key={v.id} color="orange" className="cursor-pointer" onClick={() => { setSelectedService(svc); setSelectedVersion(v); setVersionDetailOpen(true) }}>
                                  {v.codename}
                                </Tag>
                              ))}
                            </Space>
                          ) : <Text type="secondary" className="text-sm">No versions in testing</Text>}
                        </div>
                        <div>
                          <Text type="secondary" className="text-xs uppercase block mb-1">Total Versions</Text>
                          <Text className="text-lg font-medium">{svc.versions.length}</Text>
                        </div>
                      </div>

                      <Table
                        dataSource={svc.versions.slice().reverse()} // Show newest first
                        columns={versionColumns}
                        rowKey="id"
                        pagination={false}
                        size="small"
                        onRow={() => ({
                          onMouseEnter: () => setSelectedService(svc) // Ensure context is correct when hovering actions
                        })}
                      />
                    </Card>
                  )
                })
              )}
            </div>
          </div>
        )}
      </div>

      {/* --- Modals Below --- */}

      {/* New Project Modal */}
      <Modal
        title="Create Project"
        open={newProjectModalOpen}
        onCancel={() => setNewProjectModalOpen(false)}
        onOk={handleCreateProject}
      >
        <Form form={projectForm} layout="vertical">
          <Form.Item label="Project Name" name="name" rules={[{ required: true }]}>
            <Input placeholder="E-Commerce Core" />
          </Form.Item>
          <Form.Item label="Project Code" name="code" rules={[{ required: true }]}>
            <Input placeholder="ecommerce-core" />
          </Form.Item>
          <Form.Item label="Owner" name="owner" rules={[{ required: true }]}>
            <Input placeholder="Team Name or Email" />
          </Form.Item>
          <Form.Item label="Description" name="description">
            <TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>

      {/* New Service Modal */}
      <Modal
        title={`Add Service to ${currentProject?.name}`}
        open={newServiceModalOpen}
        onCancel={() => setNewServiceModalOpen(false)}
        onOk={handleCreateService}
      >
        <Form form={serviceForm} layout="vertical">
          <Form.Item label="Service Name" name="name" rules={[{ required: true }]}>
            <Input placeholder="e.g. auth-service" />
          </Form.Item>
          <Form.Item label="Git Repository URL" name="gitRepo" rules={[{ required: true }]}>
            <Input placeholder="https://github.com/..." prefix={<GithubOutlined />} />
          </Form.Item>
          <Form.Item label="Default Branch" name="gitBranch" initialValue="main">
            <Input />
          </Form.Item>
          <Form.Item label="Owner" name="owner" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
        </Form>
      </Modal>

      {/* New Version Modal */}
      <Modal
        title={`Create Version for ${selectedService?.name}`}
        open={newVersionModalOpen}
        onCancel={() => setNewVersionModalOpen(false)}
        onOk={handleSubmitVersion}
        okText="Create & Deploy"
      >
        <Alert
          message={<strong>🚀 Vibe Coding Workflow:</strong>}
          description="Creating a version triggers CI/CD build and deploys to the test environment automatically."
          type="info"
          showIcon
          className="mb-4 bg-blue-50"
        />
        <Form form={versionForm} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="Version Codename" name="codename" rules={[{ required: true }]}>
                <Input placeholder="e.g. Phoenix" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Owner" name="owner" rules={[{ required: true }]}>
                <Input />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="Git Branch/Commit" name="gitBranch" rules={[{ required: true }]}>
                <Input prefix={<GithubOutlined />} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Target Image URL" name="imageUrl" rules={[{ required: true }]}>
                <Input />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item label="Deploy Regions">
            <Select
              mode="multiple"
              placeholder="Select test regions"
              value={selectedRegions}
              onChange={setSelectedRegions}
              options={regions.map(r => ({ value: r.id, label: r.name }))}
            />
          </Form.Item>
          <Form.Item label="Description" name="description">
            <TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>

      {/* Switch Request Modal */}
      <Modal
        title={<Space><RocketOutlined className="text-green-500" /><span>Request Prod Deployment</span></Space>}
        open={switchRequestModalOpen}
        onCancel={() => setSwitchRequestModalOpen(false)}
        onOk={handleSubmitSwitchRequest}
        okText="Submit Request"
        width={700}
      >
        <Form form={switchForm} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="Current Production" name="fromVersionCodename">
                <Input disabled className="bg-gray-50 text-gray-500" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Target Version" name="toVersionCodename">
                <Input disabled className="bg-green-50 text-green-700 font-bold border-green-200" />
              </Form.Item>
            </Col>
            <Form.Item name="fromVersionId" hidden><Input /></Form.Item>
            <Form.Item name="toVersionId" hidden><Input /></Form.Item>
            <Form.Item name="testUrl" hidden><Input /></Form.Item>
          </Row>

          <Card size="small" title="Deployment Config" className="mb-4 bg-gray-50">
            <Form.Item label="Production Regions" required>
              <Select
                mode="multiple"
                value={productionDeployRegions}
                onChange={setProductionDeployRegions}
                options={regions.map(r => ({ value: r.id, label: r.name }))}
              />
            </Form.Item>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="Strategy" name="deployStrategy" initialValue="rolling">
                  <Select options={[
                    { value: 'rolling', label: 'Rolling Update' },
                    { value: 'blue-green', label: 'Blue-Green' },
                    { value: 'canary', label: 'Canary' }
                  ]} />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="Order" name="deployOrder" initialValue="sequential">
                  <Select options={[
                    { value: 'sequential', label: 'Sequential' },
                    { value: 'parallel', label: 'Parallel' }
                  ]} />
                </Form.Item>
              </Col>
            </Row>
          </Card>

          <Card size="small" title="Release Notes" className="bg-gray-50">
            <Form.Item label="Changes Summary" name="changeSummary" rules={[{ required: true }]}>
              <TextArea rows={2} />
            </Form.Item>
            <Form.Item label="Test Results" name="testResults" rules={[{ required: true }]}>
              <TextArea rows={2} />
            </Form.Item>
          </Card>
        </Form>
      </Modal>

      {/* Version Detail Modal */}
      <Modal
        title={<Space>Version Details <Tag>{selectedVersion?.codename}</Tag></Space>}
        open={versionDetailOpen}
        onCancel={() => setVersionDetailOpen(false)}
        footer={null}
        width={600}
      >
        {selectedVersion && (
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="Status">
              <Tag color={selectedVersion.status === 'production' ? 'green' : selectedVersion.status === 'testing' ? 'orange' : 'default'}>
                {selectedVersion.status.toUpperCase()}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Image">{selectedVersion.imageUrl}</Descriptions.Item>
            <Descriptions.Item label="Branch">{selectedService?.gitBranch}</Descriptions.Item>
            <Descriptions.Item label="Created">{new Date(selectedVersion.createdAt).toLocaleString()}</Descriptions.Item>
            <Descriptions.Item label="Test URL">
              {selectedVersion.testUrl ? (
                <a href={selectedVersion.testUrl} target="_blank" rel="noopener noreferrer">{selectedVersion.testUrl}</a>
              ) : '-'}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      {/* Deployment Progress Modal */}
      <Modal
        title="Deploying to Test Environment"
        open={deploymentProgressModalOpen}
        footer={null}
        closable={deploymentProgress?.step === 'completed'}
        maskClosable={false}
      >
        {deploymentProgress && (
          <div className="py-4 space-y-6">
            <Steps
              direction="vertical"
              current={['init', 'building', 'deploying', 'healthcheck', 'completed'].indexOf(deploymentProgress.step)}
              items={[
                { title: 'CI/CD Build', description: deploymentProgress.step === 'building' ? 'Building Docker image...' : '' },
                { title: 'ArgoCD Deploy', description: deploymentProgress.step === 'deploying' ? 'Deploying to regions...' : '' },
                { title: 'Health Check', description: deploymentProgress.step === 'healthcheck' ? 'Waiting for pods to be ready...' : '' },
                { title: 'Completed' },
              ]}
            />
            {deploymentProgress.step === 'completed' && (
              <Result
                status="success"
                title="Deployment Successful"
                subTitle={`Version ${deploymentProgress.codename} is ready for testing.`}
                extra={[
                  <Button type="primary" key="open" href={deploymentProgress.testUrl} target="_blank">
                    Open Test Environment
                  </Button>,
                  <Button key="close" onClick={() => setDeploymentProgressModalOpen(false)}>
                    Close
                  </Button>
                ]}
              />
            )}
          </div>
        )}
      </Modal>

    </div>
  )
}
