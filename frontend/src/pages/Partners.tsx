import { useState, useEffect } from 'react'
import {
  Card,
  Typography,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  message,
  Popconfirm,
  Tooltip,
  Descriptions,
  Divider,
  Avatar,
  List,
  Checkbox,
  Alert,
} from 'antd'
import {
  TeamOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  UserOutlined,
  MailOutlined,
  PhoneOutlined,
  GlobalOutlined,
  EyeOutlined,
  CopyOutlined,
} from '@ant-design/icons'

const { Title, Text } = Typography

// ============================================
// Types
// ============================================

interface Partner {
  id: string
  name: string
  company: string
  contact_person: string
  email: string
  phone: string
  website: string
  status: 'active' | 'inactive' | 'pending'
  access_level: 'read_only' | 'limited' | 'standard'
  permissions: string[]
  expires_at: string | null
  created_at: string
  last_login: string | null
  avatar_url: string | null
  notes: string
}

// ============================================
// Available Permissions
// ============================================

const AVAILABLE_PERMISSIONS = [
  { id: 'dashboard', label: 'Dashboard', description: 'View main dashboard' },
  { id: 'projects', label: 'Projects', description: 'View projects list' },
  { id: 'resources', label: 'Resources', description: 'View cluster resources' },
  { id: 'deployments', label: 'Deployments', description: 'View deployment history' },
  { id: 'agent_store', label: 'Agent Store', description: 'Browse available agents' },
]

const ACCESS_LEVELS = [
  { value: 'read_only', label: 'Read Only', color: 'default', description: 'Can only view, no actions' },
  { value: 'limited', label: 'Limited', color: 'orange', description: 'View + limited actions' },
  { value: 'standard', label: 'Standard', color: 'green', description: 'Full access to permitted features' },
]

// ============================================
// Main Component
// ============================================

export default function Partners() {
  const [partners, setPartners] = useState<Partner[]>([])
  const [modalVisible, setModalVisible] = useState(false)
  const [editingPartner, setEditingPartner] = useState<Partner | null>(null)
  const [detailVisible, setDetailVisible] = useState(false)
  const [selectedPartner, setSelectedPartner] = useState<Partner | null>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    loadPartners()
  }, [])

  const loadPartners = async () => {
    try {
      const response = await fetch('/api/v1/partners')
      const data = await response.json()
      setPartners(data)
    } catch {
      setPartners(getMockPartners())
    }
  }

  const openModal = (partner?: Partner) => {
    if (partner) {
      setEditingPartner(partner)
      form.setFieldsValue({
        name: partner.name,
        company: partner.company,
        contact_person: partner.contact_person,
        email: partner.email,
        phone: partner.phone,
        website: partner.website,
        access_level: partner.access_level,
        permissions: partner.permissions,
        expires_at: partner.expires_at,
        notes: partner.notes,
        status: partner.status,
      })
    } else {
      setEditingPartner(null)
      form.resetFields()
      form.setFieldsValue({ status: 'pending', access_level: 'limited' })
    }
    setModalVisible(true)
  }

  const handleSave = async (values: unknown) => {
    try {
      const url = editingPartner
        ? `/api/v1/partners/${editingPartner.id}`
        : '/api/v1/partners'
      const method = editingPartner ? 'PUT' : 'POST'

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
      })

      if (response.ok) {
        message.success(editingPartner ? 'Partner updated' : 'Partner created')
        setModalVisible(false)
        loadPartners()
      } else {
        message.error('Operation failed')
      }
    } catch {
      message.success('Operation successful (demo)')
      setModalVisible(false)
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await fetch(`/api/v1/partners/${id}`, { method: 'DELETE' })
      message.success('Partner deleted')
      loadPartners()
    } catch {
      message.success('Partner deleted (demo)')
    }
  }

  const handleToggleStatus = async (partner: Partner) => {
    const newStatus = partner.status === 'active' ? 'inactive' : 'active'
    try {
      await fetch(`/api/v1/partners/${partner.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      })
      message.success(`Partner ${newStatus === 'active' ? 'activated' : 'deactivated'}`)
      loadPartners()
    } catch {
      message.success(`Partner ${newStatus === 'active' ? 'activated' : 'deactivated'} (demo)`)
    }
  }

  const handleGenerateAccessLink = (partner: Partner) => {
    const link = `${window.location.origin}/partner-access/${partner.id}?token=xxx`
    navigator.clipboard.writeText(link)
    message.success('Access link copied to clipboard')
  }

  const handleViewDetail = (partner: Partner) => {
    setSelectedPartner(partner)
    setDetailVisible(true)
  }

  const columns = [
    {
      title: 'Partner',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: Partner) => (
        <Space>
          <Avatar icon={<TeamOutlined />} src={record.avatar_url} />
          <div>
            <Text strong>{name}</Text>
            <br />
            <Text type="secondary" className="text-xs">{record.company}</Text>
          </div>
        </Space>
      ),
    },
    {
      title: 'Contact',
      key: 'contact',
      render: (_: unknown, record: Partner) => (
        <div>
          <Text>{record.contact_person}</Text>
          <br />
          <Text type="secondary" className="text-xs">{record.email}</Text>
        </div>
      ),
    },
    {
      title: 'Access Level',
      dataIndex: 'access_level',
      key: 'access_level',
      render: (level: string) => {
        const config = ACCESS_LEVELS.find(l => l.value === level)
        return <Tag color={config?.color}>{config?.label || level}</Tag>
      },
    },
    {
      title: 'Permissions',
      dataIndex: 'permissions',
      key: 'permissions',
      render: (permissions: string[]) => (
        <Space size={2} wrap>
          {permissions.slice(0, 3).map(p => {
            const perm = AVAILABLE_PERMISSIONS.find(ap => ap.id === p)
            return <Tag key={p}>{perm?.label || p}</Tag>
          })}
          {permissions.length > 3 && <Tag>+{permissions.length - 3}</Tag>}
        </Space>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const config: Record<string, { color: string }> = {
          active: { color: 'green' },
          inactive: { color: 'default' },
          pending: { color: 'orange' },
        }
        return <Tag color={config[status]?.color}>{status.toUpperCase()}</Tag>
      },
    },
    {
      title: 'Last Login',
      dataIndex: 'last_login',
      key: 'last_login',
      render: (time: string) => time ? new Date(time).toLocaleString() : 'Never',
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: unknown, record: Partner) => (
        <Space>
          <Tooltip title="View Details">
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleViewDetail(record)}
            />
          </Tooltip>
          <Tooltip title="Copy Access Link">
            <Button
              type="link"
              size="small"
              icon={<CopyOutlined />}
              onClick={() => handleGenerateAccessLink(record)}
            />
          </Tooltip>
          <Tooltip title="Edit">
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => openModal(record)}
            />
          </Tooltip>
          <Tooltip title={record.status === 'active' ? 'Deactivate' : 'Activate'}>
            <Button
              type="link"
              size="small"
              onClick={() => handleToggleStatus(record)}
            >
              {record.status === 'active' ? 'Disable' : 'Enable'}
            </Button>
          </Tooltip>
          <Popconfirm title="Delete this partner?" onConfirm={() => handleDelete(record.id)}>
            <Tooltip title="Delete">
              <Button type="link" size="small" danger icon={<DeleteOutlined />} />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <Title level={4} className="m-0">
          <TeamOutlined className="mr-2" />
          Partners & Vendors
        </Title>
        <Space>
          <Tag color="blue">{partners.filter(p => p.status === 'active').length} Active</Tag>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => openModal()}>
            Add Partner
          </Button>
        </Space>
      </div>

      <Alert
        message="Partner Access Management"
        description="Manage external partners and vendors who need limited access to your platform. Assign specific permissions and access levels to control what they can see and do."
        type="info"
        showIcon
      />

      <Card>
        <Table
          dataSource={partners}
          columns={columns}
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {/* Add/Edit Modal */}
      <Modal
        title={editingPartner ? 'Edit Partner' : 'Add Partner'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
        width={700}
      >
        <Form form={form} layout="vertical" onFinish={handleSave}>
          <div className="grid grid-cols-2 gap-4">
            <Form.Item name="name" label="Partner Name" rules={[{ required: true }]}>
              <Input placeholder="e.g., ABC Consulting" />
            </Form.Item>
            <Form.Item name="company" label="Company" rules={[{ required: true }]}>
              <Input placeholder="Company name" />
            </Form.Item>
            <Form.Item name="contact_person" label="Contact Person" rules={[{ required: true }]}>
              <Input placeholder="Full name" prefix={<UserOutlined />} />
            </Form.Item>
            <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email' }]}>
              <Input placeholder="email@example.com" prefix={<MailOutlined />} />
            </Form.Item>
            <Form.Item name="phone" label="Phone">
              <Input placeholder="+1 234 567 8900" prefix={<PhoneOutlined />} />
            </Form.Item>
            <Form.Item name="website" label="Website">
              <Input placeholder="https://example.com" prefix={<GlobalOutlined />} />
            </Form.Item>
          </div>

          <Divider />

          <Form.Item name="access_level" label="Access Level" rules={[{ required: true }]}>
            <Select options={ACCESS_LEVELS.map(l => ({ value: l.value, label: `${l.label} - ${l.description}` }))} />
          </Form.Item>

          <Form.Item name="permissions" label="Permissions" rules={[{ required: true }]}>
            <Checkbox.Group className="w-full">
              <div className="grid grid-cols-2 gap-2">
                {AVAILABLE_PERMISSIONS.map(perm => (
                  <Checkbox key={perm.id} value={perm.id}>
                    <div>
                      <Text strong>{perm.label}</Text>
                      <br />
                      <Text type="secondary" className="text-xs">{perm.description}</Text>
                    </div>
                  </Checkbox>
                ))}
              </div>
            </Checkbox.Group>
          </Form.Item>

          <Form.Item name="status" label="Status">
            <Select options={[
              { value: 'active', label: 'Active' },
              { value: 'inactive', label: 'Inactive' },
              { value: 'pending', label: 'Pending' },
            ]} />
          </Form.Item>

          <Form.Item name="notes" label="Notes">
            <Input.TextArea rows={3} placeholder="Additional notes about this partner..." />
          </Form.Item>
        </Form>
      </Modal>

      {/* Detail Modal */}
      <Modal
        title={
          <Space>
            <Avatar icon={<TeamOutlined />} src={selectedPartner?.avatar_url} />
            <span>{selectedPartner?.name}</span>
            {selectedPartner && (
              <Tag color={selectedPartner.status === 'active' ? 'green' : 'default'}>
                {selectedPartner.status}
              </Tag>
            )}
          </Space>
        }
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={null}
        width={700}
      >
        {selectedPartner && (
          <Space direction="vertical" className="w-full" size="large">
            <Descriptions bordered size="small" column={2}>
              <Descriptions.Item label="Company">{selectedPartner.company}</Descriptions.Item>
              <Descriptions.Item label="Contact">{selectedPartner.contact_person}</Descriptions.Item>
              <Descriptions.Item label="Email">{selectedPartner.email}</Descriptions.Item>
              <Descriptions.Item label="Phone">{selectedPartner.phone || '-'}</Descriptions.Item>
              <Descriptions.Item label="Website">{selectedPartner.website || '-'}</Descriptions.Item>
              <Descriptions.Item label="Access Level">
                <Tag color={ACCESS_LEVELS.find(l => l.value === selectedPartner.access_level)?.color}>
                  {ACCESS_LEVELS.find(l => l.value === selectedPartner.access_level)?.label}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Created">{new Date(selectedPartner.created_at).toLocaleDateString()}</Descriptions.Item>
              <Descriptions.Item label="Expires">{selectedPartner.expires_at ? new Date(selectedPartner.expires_at).toLocaleDateString() : 'No expiry'}</Descriptions.Item>
            </Descriptions>

            <Card size="small" title="Granted Permissions">
              <List
                grid={{ gutter: 8, column: 2 }}
                dataSource={selectedPartner.permissions}
                renderItem={(permId) => {
                  const perm = AVAILABLE_PERMISSIONS.find(p => p.id === permId)
                  return (
                    <List.Item>
                      <Tag color="blue">{perm?.label || permId}</Tag>
                    </List.Item>
                  )
                }}
              />
            </Card>

            {selectedPartner.notes && (
              <Card size="small" title="Notes">
                <Text>{selectedPartner.notes}</Text>
              </Card>
            )}

            <Space>
              <Button icon={<CopyOutlined />} onClick={() => handleGenerateAccessLink(selectedPartner)}>
                Copy Access Link
              </Button>
              <Button icon={<EditOutlined />} onClick={() => { setDetailVisible(false); openModal(selectedPartner) }}>
                Edit Partner
              </Button>
            </Space>
          </Space>
        )}
      </Modal>
    </div>
  )
}

// ============================================
// Mock Data
// ============================================

function getMockPartners(): Partner[] {
  return [
    {
      id: 'partner-1',
      name: 'TechCorp Solutions',
      company: 'TechCorp Inc.',
      contact_person: 'John Smith',
      email: 'john@techcorp.com',
      phone: '+1 555 123 4567',
      website: 'https://techcorp.com',
      status: 'active',
      access_level: 'standard',
      permissions: ['dashboard', 'projects', 'resources', 'deployments'],
      expires_at: '2025-12-31',
      created_at: '2024-01-15',
      last_login: new Date().toISOString(),
      avatar_url: null,
      notes: 'Primary development partner for cloud migration project.',
    },
    {
      id: 'partner-2',
      name: 'DevTeam Pro',
      company: 'DevTeam Pro Ltd.',
      contact_person: 'Jane Doe',
      email: 'jane@devteampro.io',
      phone: '+1 555 987 6543',
      website: 'https://devteampro.io',
      status: 'active',
      access_level: 'limited',
      permissions: ['dashboard', 'projects', 'agent_store'],
      expires_at: '2025-06-30',
      created_at: '2024-02-01',
      last_login: new Date(Date.now() - 86400000).toISOString(),
      avatar_url: null,
      notes: 'Backend development contractor.',
    },
    {
      id: 'partner-3',
      name: 'Security Audit Inc',
      company: 'Security Audit Inc.',
      contact_person: 'Bob Wilson',
      email: 'bob@securityaudit.com',
      phone: '+1 555 456 7890',
      website: 'https://securityaudit.com',
      status: 'pending',
      access_level: 'read_only',
      permissions: ['dashboard', 'resources'],
      expires_at: null,
      created_at: '2024-03-01',
      last_login: null,
      avatar_url: null,
      notes: 'External security audit team - awaiting contract signature.',
    },
  ]
}
