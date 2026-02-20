import { useState } from 'react'
import {
  Card,
  Typography,
  Form,
  Input,
  Select,
  Switch,
  Button,
  Divider,
  message,
  Space,
  Avatar,
  Upload,
} from 'antd'
import { UserOutlined, CameraOutlined, BellOutlined, BulbOutlined, SyncOutlined, CompressOutlined } from '@ant-design/icons'
import { useAuthStore } from '../stores/authStore'

const { Title, Text } = Typography

export default function ProfileSettings() {
  const { user, updateUser } = useAuthStore()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  const handleSaveProfile = async (values: unknown) => {
    setLoading(true)
    try {
      // In production, this would call the API
      // await fetch('/api/v1/users/me', { method: 'PUT', body: JSON.stringify(values) })
      updateUser(values as Parameters<typeof updateUser>[0])
      message.success('Profile updated successfully')
    } catch {
      message.error('Failed to update profile')
    } finally {
      setLoading(false)
    }
  }

  const handleAvatarUpload = (_file: File) => {
    // In production, this would upload to server
    message.success('Avatar uploaded successfully')
    return false
  }

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <Title level={4}>
        <UserOutlined className="mr-2" />
        Personal Settings
      </Title>

      {/* Avatar Section */}
      <Card>
        <div className="flex items-center gap-6">
          <div className="relative">
            <Avatar size={80} icon={<UserOutlined />} />
            <Upload
              showUploadList={false}
              beforeUpload={handleAvatarUpload}
              accept="image/*"
            >
              <Button
                size="small"
                shape="circle"
                icon={<CameraOutlined />}
                className="absolute bottom-0 right-0"
              />
            </Upload>
          </div>
          <div>
            <Text strong className="block text-lg">
              {user?.fullName || user?.username}
            </Text>
            <Text type="secondary">{user?.email}</Text>
            <br />
            <Text type="secondary" className="text-xs">
              Click the camera icon to change your avatar
            </Text>
          </div>
        </div>
      </Card>

      {/* Profile Information */}
      <Card title="Profile Information">
        <Form
          form={form}
          layout="vertical"
          initialValues={user || {}}
          onFinish={handleSaveProfile}
        >
          <div className="grid grid-cols-2 gap-4">
            <Form.Item label="Username" name="username">
              <Input disabled />
            </Form.Item>
            <Form.Item label="Email" name="email">
              <Input disabled />
            </Form.Item>
            <Form.Item label="Full Name" name="fullName">
              <Input placeholder="Enter your full name" />
            </Form.Item>
            <Form.Item label="Role" name="role">
              <Select
                disabled
                options={[
                  { value: 'admin', label: 'Admin' },
                  { value: 'internal', label: 'Internal' },
                  { value: 'vendor', label: 'Vendor' },
                ]}
              />
            </Form.Item>
          </div>
          <Form.Item label="Bio" name="bio">
            <Input.TextArea
              rows={3}
              placeholder="Tell us about yourself..."
            />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>
            Save Profile
          </Button>
        </Form>
      </Card>

      {/* Preferences */}
      <Card title="Preferences">
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <BellOutlined className="text-lg text-gray-500" />
              <div>
                <Text strong>Email Notifications</Text>
                <br />
                <Text type="secondary" className="text-sm">
                  Receive email notifications for critical alerts and updates
                </Text>
              </div>
            </div>
            <Switch defaultChecked />
          </div>

          <Divider className="my-4" />

          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <BulbOutlined className="text-lg text-gray-500" />
              <div>
                <Text strong>Dark Mode</Text>
                <br />
                <Text type="secondary" className="text-sm">
                  Use dark theme for the interface
                </Text>
              </div>
            </div>
            <Switch />
          </div>

          <Divider className="my-4" />

          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <SyncOutlined className="text-lg text-gray-500" />
              <div>
                <Text strong>Auto-refresh Dashboard</Text>
                <br />
                <Text type="secondary" className="text-sm">
                  Automatically refresh dashboard data every 30 seconds
                </Text>
              </div>
            </div>
            <Switch defaultChecked />
          </div>

          <Divider className="my-4" />

          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <CompressOutlined className="text-lg text-gray-500" />
              <div>
                <Text strong>Compact View</Text>
                <br />
                <Text type="secondary" className="text-sm">
                  Use compact layout for tables and cards
                </Text>
              </div>
            </div>
            <Switch />
          </div>
        </div>
      </Card>

      {/* Danger Zone */}
      <Card title="Account Actions" className="border-red-200">
        <Space direction="vertical" className="w-full">
          <div className="flex justify-between items-center">
            <div>
              <Text strong>Change Password</Text>
              <br />
              <Text type="secondary" className="text-sm">
                Update your account password
              </Text>
            </div>
            <Button>Change Password</Button>
          </div>
          <Divider className="my-4" />
          <div className="flex justify-between items-center">
            <div>
              <Text strong type="danger">
                Delete Account
              </Text>
              <br />
              <Text type="secondary" className="text-sm">
                Permanently delete your account and all data
              </Text>
            </div>
            <Button danger>Delete Account</Button>
          </div>
        </Space>
      </Card>
    </div>
  )
}
