import { useState } from 'react'
import { Card, Table, Tag, Button, Modal, Form, Input, Select, Space, message } from 'antd'
import { PlusOutlined, EditOutlined, EyeOutlined } from '@ant-design/icons'
import { useAuthStore } from '../stores/authStore'
import { useProjectStore } from '../stores/projectStore'
import PageContainer from '../components/layout/PageContainer'

const { TextArea } = Input

const mockTickets = [
  {
    id: 'ticket-1',
    title: 'API Gateway performance degradation',
    description: 'Users reporting slow response times on the API gateway.',
    type: 'bug',
    status: 'open',
    priority: 'high',
    projectId: 'pipecat-app-a',
    reporter: 'John Doe',
    assignee: 'Jane Smith',
    createdAt: '2024-01-15 10:00:00',
  },
  {
    id: 'ticket-2',
    title: 'Add new monitoring dashboard',
    description: 'Need a dashboard to track custom metrics for the chat service.',
    type: 'request',
    status: 'in_progress',
    priority: 'medium',
    projectId: 'chat-platform',
    reporter: 'Bob Wilson',
    assignee: 'Alice Chen',
    createdAt: '2024-01-14 15:30:00',
  },
  {
    id: 'ticket-3',
    title: 'Deploy v2.0 to production',
    description: 'Deploy the new version of chat-gateway to production.',
    type: 'change',
    status: 'open',
    priority: 'critical',
    projectId: 'chat-platform',
    reporter: 'Alice Chen',
    assignee: null,
    createdAt: '2024-01-15 09:00:00',
  },
  {
    id: 'ticket-4',
    title: 'Fix database connection issue',
    description: 'Connection pool exhaustion causing intermittent failures.',
    type: 'vendor_task',
    status: 'resolved',
    priority: 'high',
    projectId: 'infra-core',
    reporter: 'Jane Smith',
    assignee: 'External Vendor',
    createdAt: '2024-01-13 14:00:00',
  },
]

export default function Tickets() {
  const { user } = useAuthStore()
  const { projects, globalSelectedProjectId } = useProjectStore()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedTicket, setSelectedTicket] = useState<typeof mockTickets[0] | null>(null)
  const [form] = Form.useForm()

  const handleCreate = () => {
    form.resetFields()
    setSelectedTicket(null)
    setIsModalOpen(true)
  }

  const handleEdit = (ticket: typeof mockTickets[0]) => {
    setSelectedTicket(ticket)
    form.setFieldsValue(ticket)
    setIsModalOpen(true)
  }

  const handleSubmit = () => {
    form.validateFields().then((values) => {
      console.log('Submit:', values)
      message.success(selectedTicket ? 'Ticket updated!' : 'Ticket created!')
      setIsModalOpen(false)
    })
  }

  const filteredTickets = mockTickets.filter((t) => {
    const hasProjectPermission = user?.role === 'admin' || user?.allowedProjects?.includes(t.projectId)
    if (!hasProjectPermission) return false
    
    if (globalSelectedProjectId !== 'all' && t.projectId !== globalSelectedProjectId) return false
    
    return true
  })

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 100,
      render: (id: string) => <span className="text-gray-500">{id}</span>,
    },
    {
      title: 'Title',
      dataIndex: 'title',
      key: 'title',
      render: (title: string) => <span className="font-medium">{title}</span>,
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      width: 100,
      render: (type: string) => {
        const colors: Record<string, string> = {
          bug: 'red',
          request: 'blue',
          change: 'purple',
          vendor_task: 'orange',
        }
        return <Tag color={colors[type]}>{type.replace('_', ' ').toUpperCase()}</Tag>
      },
    },
    {
      title: 'Priority',
      dataIndex: 'priority',
      key: 'priority',
      width: 100,
      render: (priority: string) => {
        const colors: Record<string, string> = {
          critical: 'red',
          high: 'orange',
          medium: 'gold',
          low: 'default',
        }
        return <Tag color={colors[priority]}>{priority.toUpperCase()}</Tag>
      },
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: string) => {
        const colors: Record<string, string> = {
          open: 'blue',
          in_progress: 'processing',
          resolved: 'green',
          closed: 'default',
        }
        return <Tag color={colors[status]}>{status.replace('_', ' ').toUpperCase()}</Tag>
      },
    },
    {
      title: 'Project',
      dataIndex: 'projectId',
      key: 'projectId',
      render: (projectId: string) => {
        const project = projects.find(p => p.id === projectId)
        return project ? project.name : projectId
      }
    },
    {
      title: 'Assignee',
      dataIndex: 'assignee',
      key: 'assignee',
      render: (assignee: string | null) => assignee || <span className="text-gray-400">Unassigned</span>,
    },
    {
      title: 'Created',
      dataIndex: 'createdAt',
      key: 'createdAt',
      width: 160,
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_: unknown, record: typeof mockTickets[0]) => (
        <Space>
          <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => setSelectedTicket(record)} />
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)} />
        </Space>
      ),
    },
  ]

  return (
    <PageContainer
      title="Tickets"
      icon={<EditOutlined />}
      transparent
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          New Ticket
        </Button>
      }
    >
      <div className="space-y-6">

      <Card>
        <Table
          dataSource={filteredTickets}
          columns={columns}
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Modal
        title={selectedTicket ? 'Edit Ticket' : 'New Ticket'}
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        onOk={handleSubmit}
        width={600}
      >
        <Form form={form} layout="vertical" className="mt-4">
          <Form.Item name="title" label="Title" rules={[{ required: true }]}>
            <Input placeholder="Ticket title" />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <TextArea rows={4} placeholder="Describe the issue or request" />
          </Form.Item>
          <div className="grid grid-cols-2 gap-4">
            <Form.Item name="type" label="Type" rules={[{ required: true }]}>
              <Select
                options={[
                  { value: 'bug', label: 'Bug' },
                  { value: 'request', label: 'Request' },
                  { value: 'change', label: 'Change' },
                  { value: 'vendor_task', label: 'Vendor Task' },
                ]}
              />
            </Form.Item>
            <Form.Item name="priority" label="Priority" rules={[{ required: true }]}>
              <Select
                options={[
                  { value: 'critical', label: 'Critical' },
                  { value: 'high', label: 'High' },
                  { value: 'medium', label: 'Medium' },
                  { value: 'low', label: 'Low' },
                ]}
              />
            </Form.Item>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Form.Item name="projectId" label="Project" rules={[{ required: true }]}>
              <Select
                options={projects.map(p => ({ value: p.id, label: p.name }))}
              />
            </Form.Item>
            <Form.Item name="assignee" label="Assignee">
              <Select
                allowClear
                options={[
                  { value: 'Jane Smith', label: 'Jane Smith' },
                  { value: 'Alice Chen', label: 'Alice Chen' },
                  { value: 'Bob Wilson', label: 'Bob Wilson' },
                ]}
              />
            </Form.Item>
          </div>
        </Form>
      </Modal>

      <Modal
        title={selectedTicket?.title}
        open={!!selectedTicket && !isModalOpen}
        onCancel={() => setSelectedTicket(null)}
        footer={null}
        width={600}
      >
        {selectedTicket && (
          <div className="space-y-4">
            <div>
              <span className="font-medium">Description:</span>
              <p className="text-gray-600 mt-1">{selectedTicket.description}</p>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="font-medium">Type:</span> {selectedTicket.type}
              </div>
              <div>
                <span className="font-medium">Priority:</span> {selectedTicket.priority}
              </div>
              <div>
                <span className="font-medium">Status:</span> {selectedTicket.status}
              </div>
              <div>
                <span className="font-medium">Project:</span> {projects.find(p => p.id === selectedTicket.projectId)?.name || selectedTicket.projectId}
              </div>
              <div>
                <span className="font-medium">Reporter:</span> {selectedTicket.reporter}
              </div>
              <div>
                <span className="font-medium">Assignee:</span> {selectedTicket.assignee || 'Unassigned'}
              </div>
            </div>
          </div>
        )}
      </Modal>
      </div>
    </PageContainer>
  )
}
