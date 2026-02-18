import { ReactNode, useState } from 'react'
import { Layout, Menu, Avatar, Dropdown, Badge, Select, Breadcrumb, Button, Tooltip, Tag } from 'antd'
import {
  DashboardOutlined,
  ClusterOutlined,
  RocketOutlined,
  AlertOutlined,
  SolutionOutlined,
  RobotOutlined,
  SettingOutlined,
  LogoutOutlined,
  UserOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  BellOutlined,
  HomeOutlined,
  MessageOutlined,
  AppstoreOutlined,
  ShopOutlined,
  StarFilled,
} from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'
import { useVersionStore } from '../../stores/versionStore'
import AIAssistantDrawer from '../AIAssistantDrawer'

const { Header, Sider, Content } = Layout

interface MainLayoutProps {
  children: ReactNode
}

export default function MainLayout({ children }: MainLayoutProps) {
  const [collapsed, setCollapsed] = useState(false)
  const [aiDrawerOpen, setAiDrawerOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()
  const {
    projects,
    currentProjectId,
    currentVersionId,
    setCurrentProject,
    setCurrentVersion,
  } = useVersionStore()

  // 获取当前选中的项目和版本
  const currentProject = projects.find(p => p.id === currentProjectId)
  const isProductionVersion = currentProject?.productionVersionId === currentVersionId

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
    },
    {
      key: '/projects',
      icon: <AppstoreOutlined />,
      label: 'Projects',
    },
    {
      key: '/resources',
      icon: <ClusterOutlined />,
      label: 'Resources',
    },
    {
      key: '/deployments',
      icon: <RocketOutlined />,
      label: 'Deployments',
    },
    {
      key: '/alerts',
      icon: <AlertOutlined />,
      label: 'Alerts',
    },
    {
      key: '/tickets',
      icon: <SolutionOutlined />,
      label: 'Tickets',
    },
    {
      key: '/agent-store',
      icon: <ShopOutlined />,
      label: 'Agent Store',
    },
  ]

  const userMenuItems = [
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: 'Settings',
      onClick: () => navigate('/settings'),
    },
    {
      key: 'ai-assistant',
      icon: <RobotOutlined />,
      label: 'AI Assistant',
      onClick: () => setAiDrawerOpen(true),
    },
    { type: 'divider' as const },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Logout',
      onClick: () => {
        logout()
        navigate('/login')
      },
    },
  ]

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key)
  }

  const getSelectedKey = () => {
    const path = location.pathname
    const matchedItem = menuItems.find((item) => path.startsWith(item.key))
    return matchedItem?.key || '/dashboard'
  }

  // Generate breadcrumb items
  const getBreadcrumbItems = () => {
    const items: { title: React.ReactNode; href?: string }[] = [{ title: <HomeOutlined key="home" />, href: '/dashboard' }]
    const pathMap: Record<string, string> = {
      '/dashboard': 'Dashboard',
      '/projects': 'Projects',
      '/resources': 'Resources',
      '/deployments': 'Deployments',
      '/alerts': 'Alerts',
      '/tickets': 'Tickets',
      '/settings': 'Settings',
      '/ai-assistant': 'AI Assistant',
    }
    const currentPath = '/' + location.pathname.split('/')[1]
    if (pathMap[currentPath] && currentPath !== '/dashboard') {
      items.push({ title: pathMap[currentPath] })
    }
    return items
  }

  return (
    <Layout className="min-h-screen">
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        className="bg-white shadow-md"
        width={240}
      >
        <div className="h-16 flex items-center justify-center border-b border-gray-200">
          {collapsed ? (
            <span className="text-2xl font-bold text-primary-600">N</span>
          ) : (
            <span className="text-xl font-bold text-primary-600">NexusOps</span>
          )}
        </div>
        <Menu
          mode="inline"
          selectedKeys={[getSelectedKey()]}
          items={menuItems}
          onClick={handleMenuClick}
          className="border-none"
        />
      </Sider>
      <Layout>
        <Header className="bg-white px-4 shadow-sm flex items-center justify-between h-14">
          <div className="flex items-center gap-4">
            {collapsed ? (
              <MenuUnfoldOutlined
                className="text-xl cursor-pointer"
                onClick={() => setCollapsed(false)}
              />
            ) : (
              <MenuFoldOutlined
                className="text-xl cursor-pointer"
                onClick={() => setCollapsed(true)}
              />
            )}
            <Breadcrumb items={getBreadcrumbItems()} />
          </div>

          {/* Project/Version Selector - Hidden on Dashboard */}
          {location.pathname !== '/dashboard' && (
            <div className="flex items-center gap-2">
              <AppstoreOutlined className="text-gray-400" />
              <Select
                value={currentProjectId}
                onChange={(value) => {
                  setCurrentProject(value)
                }}
                style={{ width: 150 }}
                options={projects.map(p => ({ value: p.id, label: p.name }))}
                size="small"
              />
              <Select
                value={currentVersionId}
                onChange={(value) => {
                  setCurrentVersion(value)
                }}
                style={{ width: 130 }}
                size="small"
                className={isProductionVersion ? 'bg-green-50' : 'bg-orange-50'}
              >
                {currentProject?.versions.map(v => (
                  <Select.Option key={v.id} value={v.id}>
                    <div className="flex items-center gap-1">
                      {currentProject.productionVersionId === v.id && (
                        <StarFilled className="text-yellow-500 text-xs" />
                      )}
                      <span>{v.codename}</span>
                      <Tag
                        color={v.status === 'production' ? 'green' : 'orange'}
                        style={{ marginLeft: 4, fontSize: 10, lineHeight: '16px', padding: '0 4px' }}
                      >
                        {v.status === 'production' ? '生产' : '测试'}
                      </Tag>
                    </div>
                  </Select.Option>
                ))}
              </Select>
            </div>
          )}

          <div className="flex items-center gap-3">
            {/* AI Assistant Button */}
            <Tooltip title="AI Assistant (Cmd+K)">
              <Button
                type="primary"
                ghost
                icon={<MessageOutlined />}
                onClick={() => setAiDrawerOpen(true)}
                className="flex items-center"
              >
                Ask AI
              </Button>
            </Tooltip>

            <Badge count={3} size="small">
              <BellOutlined className="text-xl cursor-pointer hover:text-primary-500" />
            </Badge>
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <div className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 px-2 py-1 rounded">
                <Avatar size="small" icon={<UserOutlined />} />
                <span className="text-gray-700 text-sm">{user?.fullName || user?.username}</span>
              </div>
            </Dropdown>
          </div>
        </Header>
        <Content className="m-4 p-6 bg-white rounded-lg shadow-sm min-h-[calc(100vh-100px)] overflow-auto">
          {children}
        </Content>
      </Layout>

      {/* Global AI Assistant Drawer */}
      <AIAssistantDrawer open={aiDrawerOpen} onClose={() => setAiDrawerOpen(false)} />
    </Layout>
  )
}
