import { Form, Input, Button, Card, Typography, message } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useAuthStore } from '../stores/authStore'

const { Title, Text } = Typography

export default function Login() {
  const { login } = useAuthStore()
  const [form] = Form.useForm()

  const handleSubmit = async (values: { username: string; password: string }) => {
    // TODO: Replace with actual API call
    if (values.username && values.password) {
      login(
        {
          id: '1',
          username: values.username,
          email: `${values.username}@nexusops.local`,
          fullName: values.username,
          role: 'admin',
          isActive: true,
          allowedProjects: values.username === 'admin' ? ['pipecat-app-a', 'chat-platform', 'infra-core'] : ['pipecat-app-a'], // Mock permissions
        },
        'mock-jwt-token'
      )
      message.success('Login successful!')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <Card className="w-96 shadow-lg">
        <div className="text-center mb-6">
          <Title level={3} className="text-primary-600 mb-2">NexusOps</Title>
          <Text type="secondary">AI Native Operations Platform</Text>
        </div>

        <Form form={form} onFinish={handleSubmit} layout="vertical">
          <Form.Item
            name="username"
            rules={[{ required: true, message: 'Please enter your username' }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="Username"
              size="large"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: 'Please enter your password' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Password"
              size="large"
            />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" block size="large">
              Login
            </Button>
          </Form.Item>
        </Form>

        <div className="text-center text-gray-400 text-sm">
          <p>Demo: Enter any username/password to login</p>
        </div>
      </Card>
    </div>
  )
}
