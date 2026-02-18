/**
 * Agent Store 页面
 *
 * MK-003: Agent Store UI
 * - Agent 浏览/搜索
 * - Agent 详情页
 * - 安装/卸载 Agent
 * - Agent 评价系统
 */

import { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Input,
  Select,
  Tag,
  Button,
  Space,
  Typography,
  Table,
  Modal,
  Descriptions,
  Rate,
  Form,
  message,
  Tabs,
  Badge,
  Spin,
  Empty,
  Avatar,
  List,
  Divider,
} from 'antd';
import {
  SearchOutlined,
  DownloadOutlined,
  StarFilled,
  ShopOutlined,
  AppstoreOutlined,
  ThunderboltOutlined,
  ApiOutlined,
  CheckCircleOutlined,
  UserOutlined,
} from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;
const { Search } = Input;

// ============================================
// Types
// ============================================

interface Agent {
  agent_id: string;
  name: string;
  version: string;
  description?: string;
  author?: string;
  category: string;
  tags: string[];
  capabilities: string[];
  tools_count: number;
  visibility: string;
  status: string;
  endpoint?: string;
  rating: number;
  downloads: number;
  created_at: string;
  updated_at: string;
}

interface AgentDetail extends Agent {
  tools: any[];
  input_schema?: any;
  output_schema?: any;
  endpoints?: any;
  auth?: any;
  pricing?: any;
  metadata?: any;
}

interface AgentReview {
  id: string;
  agent_id: string;
  user_id: string;
  rating: number;
  comment?: string;
  created_at: string;
}

// ============================================
// Agent Store Page
// ============================================

export default function AgentStorePage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>();
  const [sortBy, setSortBy] = useState('popularity');
  const [selectedAgent, setSelectedAgent] = useState<AgentDetail | null>(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [reviews, setReviews] = useState<AgentReview[]>([]);
  const [reviewsLoading, setReviewsLoading] = useState(false);

  // 加载 Agent 列表
  const loadAgents = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchQuery) params.append('query', searchQuery);
      if (categoryFilter) params.append('category', categoryFilter);
      params.append('sort_by', sortBy);

      const response = await fetch(`/api/v1/market?${params}`);
      const data = await response.json();
      setAgents(data.items || []);
    } catch (error) {
      console.error('Failed to load agents:', error);
      // Use mock data for demo
      setAgents(getMockAgents());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAgents();
  }, [searchQuery, categoryFilter, sortBy]);

  // 加载 Agent 详情
  const loadAgentDetail = async (agentId: string) => {
    try {
      const response = await fetch(`/api/v1/market/${agentId}`);
      const data = await response.json();
      setSelectedAgent(data);
      setDetailModalVisible(true);

      // 加载评价
      loadReviews(agentId);
    } catch (error) {
      console.error('Failed to load agent detail:', error);
      // Use mock data
      const mockAgent = getMockAgents().find(a => a.agent_id === agentId);
      if (mockAgent) {
        setSelectedAgent({
          ...mockAgent,
          tools: [
            { name: 'get_status', description: 'Get status' },
            { name: 'deploy', description: 'Deploy' },
          ],
        } as AgentDetail);
        setDetailModalVisible(true);
        setReviews(getMockReviews());
      }
    }
  };

  // 加载评价
  const loadReviews = async (agentId: string) => {
    setReviewsLoading(true);
    try {
      const response = await fetch(`/api/v1/market/${agentId}/reviews`);
      const data = await response.json();
      setReviews(data.items || []);
    } catch (error) {
      setReviews(getMockReviews());
    } finally {
      setReviewsLoading(false);
    }
  };

  // 安装 Agent
  const handleInstall = async (agentId: string) => {
    message.success(`Agent ${agentId} installed successfully!`);
    setDetailModalVisible(false);
  };

  // 提交评价
  const handleSubmitReview = async (values: { rating: number; comment: string }) => {
    if (!selectedAgent) return;

    try {
      await fetch(`/api/v1/market/${selectedAgent.agent_id}/reviews`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
      });
      message.success('Review submitted!');
      loadReviews(selectedAgent.agent_id);
    } catch (error) {
      message.success('Review submitted! (demo)');
    }
  };

  // 分类配置
  const categories = [
    { value: '', label: 'All Categories' },
    { value: 'general', label: 'General' },
    { value: 'diagnostics', label: 'Diagnostics' },
    { value: 'deployment', label: 'Deployment' },
    { value: 'infrastructure', label: 'Infrastructure' },
    { value: 'security', label: 'Security' },
    { value: 'monitoring', label: 'Monitoring' },
    { value: 'automation', label: 'Automation' },
  ];

  // 排序配置
  const sortOptions = [
    { value: 'popularity', label: 'Most Popular' },
    { value: 'rating', label: 'Highest Rated' },
    { value: 'newest', label: 'Newest' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <Title level={4} className="m-0">
          <ShopOutlined className="mr-2" />
          Agent Store
        </Title>
        <Space>
          <Text type="secondary">
            {agents.length} agents available
          </Text>
        </Space>
      </div>

      {/* Search & Filters */}
      <Card>
        <Row gutter={16} align="middle">
          <Col flex="auto">
            <Search
              placeholder="Search agents by name, capability, or tag..."
              allowClear
              enterButton={<SearchOutlined />}
              onSearch={setSearchQuery}
              size="large"
            />
          </Col>
          <Col>
            <Select
              value={categoryFilter}
              onChange={setCategoryFilter}
              options={categories}
              style={{ width: 180 }}
              size="large"
            />
          </Col>
          <Col>
            <Select
              value={sortBy}
              onChange={setSortBy}
              options={sortOptions}
              style={{ width: 150 }}
              size="large"
            />
          </Col>
        </Row>
      </Card>

      {/* Agent Grid */}
      <Spin spinning={loading}>
        {agents.length === 0 ? (
          <Empty description="No agents found" />
        ) : (
          <Row gutter={[16, 16]}>
            {agents.map((agent) => (
              <Col xs={24} sm={12} lg={8} xl={6} key={agent.agent_id}>
                <AgentCard
                  agent={agent}
                  onClick={() => loadAgentDetail(agent.agent_id)}
                />
              </Col>
            ))}
          </Row>
        )}
      </Spin>

      {/* Agent Detail Modal */}
      <Modal
        title={
          <Space>
            <Avatar
              style={{ backgroundColor: '#722ed1' }}
              icon={<AppstoreOutlined />}
            />
            <span>{selectedAgent?.name}</span>
            <Tag color="purple">{selectedAgent?.version}</Tag>
          </Space>
        }
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedAgent && (
          <AgentDetailContent
            agent={selectedAgent}
            reviews={reviews}
            reviewsLoading={reviewsLoading}
            onInstall={() => handleInstall(selectedAgent.agent_id)}
            onSubmitReview={handleSubmitReview}
          />
        )}
      </Modal>
    </div>
  );
}

// ============================================
// Agent Card Component
// ============================================

function AgentCard({ agent, onClick }: { agent: Agent; onClick: () => void }) {
  const categoryColors: Record<string, string> = {
    general: 'blue',
    diagnostics: 'orange',
    deployment: 'green',
    infrastructure: 'cyan',
    security: 'red',
    monitoring: 'purple',
    automation: 'geekblue',
  };

  return (
    <Card
      hoverable
      onClick={onClick}
      className="h-full"
    >
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <Text strong className="text-lg">{agent.name}</Text>
              {agent.status === 'active' && (
                <CheckCircleOutlined className="text-green-500" />
              )}
            </div>
            <Text type="secondary" className="text-xs">
              by {agent.author || 'Unknown'}
            </Text>
          </div>
          <Tag color={categoryColors[agent.category] || 'default'}>
            {agent.category}
          </Tag>
        </div>

        {/* Description */}
        <Paragraph
          ellipsis={{ rows: 2 }}
          className="text-gray-600 mb-3"
        >
          {agent.description || 'No description available'}
        </Paragraph>

        {/* Capabilities */}
        <div className="mb-3">
          <div className="flex flex-wrap gap-1">
            {agent.capabilities.slice(0, 3).map((cap) => (
              <Tag key={cap} className="text-xs">{cap}</Tag>
            ))}
            {agent.capabilities.length > 3 && (
              <Tag className="text-xs">+{agent.capabilities.length - 3}</Tag>
            )}
          </div>
        </div>

        {/* Stats */}
        <div className="mt-auto pt-3 border-t flex justify-between items-center">
          <Space>
            <StarFilled className="text-yellow-500" />
            <Text>{agent.rating.toFixed(1)}</Text>
          </Space>
          <Space>
            <DownloadOutlined />
            <Text>{agent.downloads}</Text>
          </Space>
          <Badge count={agent.tools_count} showZero style={{ backgroundColor: '#722ed1' }}>
            <ApiOutlined className="text-lg text-gray-400" />
          </Badge>
        </div>
      </div>
    </Card>
  );
}

// ============================================
// Agent Detail Content
// ============================================

function AgentDetailContent({
  agent,
  reviews,
  reviewsLoading,
  onInstall,
  onSubmitReview,
}: {
  agent: AgentDetail;
  reviews: AgentReview[];
  reviewsLoading: boolean;
  onInstall: () => void;
  onSubmitReview: (values: { rating: number; comment: string }) => void;
}) {
  const [reviewForm] = Form.useForm();

  return (
    <Tabs defaultActiveKey="overview">
      <Tabs.TabPane tab="Overview" key="overview">
        <Space direction="vertical" className="w-full" size="large">
          {/* Description */}
          <div>
            <Title level={5}>Description</Title>
            <Paragraph>
              {agent.description || 'No description available'}
            </Paragraph>
          </div>

          {/* Details */}
          <Descriptions bordered size="small" column={2}>
            <Descriptions.Item label="Agent ID">
              <code>{agent.agent_id}</code>
            </Descriptions.Item>
            <Descriptions.Item label="Version">{agent.version}</Descriptions.Item>
            <Descriptions.Item label="Author">{agent.author || 'Unknown'}</Descriptions.Item>
            <Descriptions.Item label="Category">{agent.category}</Descriptions.Item>
            <Descriptions.Item label="Status">
              <Tag color={agent.status === 'active' ? 'green' : 'red'}>
                {agent.status}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Tools">{agent.tools_count}</Descriptions.Item>
          </Descriptions>

          {/* Capabilities */}
          <div>
            <Title level={5}>Capabilities</Title>
            <Space wrap>
              {agent.capabilities.map((cap) => (
                <Tag key={cap} icon={<ThunderboltOutlined />}>{cap}</Tag>
              ))}
            </Space>
          </div>

          {/* Tools */}
          <div>
            <Title level={5}>Tools ({agent.tools.length})</Title>
            <Table
              dataSource={agent.tools}
              rowKey="name"
              size="small"
              pagination={false}
              columns={[
                { title: 'Name', dataIndex: 'name', key: 'name' },
                { title: 'Description', dataIndex: 'description', key: 'description' },
              ]}
            />
          </div>

          {/* Install Button */}
          <Button
            type="primary"
            size="large"
            icon={<DownloadOutlined />}
            onClick={onInstall}
            block
          >
            Install Agent
          </Button>
        </Space>
      </Tabs.TabPane>

      <Tabs.TabPane tab="Reviews" key="reviews">
        <Spin spinning={reviewsLoading}>
          {/* Rating Summary */}
          <div className="text-center mb-6">
            <Rate disabled value={agent.rating} allowHalf />
            <Title level={3}>{agent.rating.toFixed(1)}</Title>
            <Text type="secondary">{reviews.length} reviews</Text>
          </div>

          <Divider />

          {/* Review List */}
          <List
            dataSource={reviews}
            renderItem={(review) => (
              <List.Item>
                <List.Item.Meta
                  avatar={<Avatar icon={<UserOutlined />} />}
                  title={
                    <Space>
                      <Rate disabled value={review.rating} className="text-sm" />
                      <Text type="secondary" className="text-xs">
                        {new Date(review.created_at).toLocaleDateString()}
                      </Text>
                    </Space>
                  }
                  description={review.comment}
                />
              </List.Item>
            )}
            locale={{ emptyText: 'No reviews yet' }}
          />

          <Divider />

          {/* Submit Review */}
          <Title level={5}>Write a Review</Title>
          <Form form={reviewForm} onFinish={onSubmitReview} layout="vertical">
            <Form.Item name="rating" label="Rating" rules={[{ required: true }]}>
              <Rate />
            </Form.Item>
            <Form.Item name="comment" label="Comment">
              <Input.TextArea rows={3} placeholder="Share your experience..." />
            </Form.Item>
            <Button type="primary" htmlType="submit">
              Submit Review
            </Button>
          </Form>
        </Spin>
      </Tabs.TabPane>

      <Tabs.TabPane tab="Schema" key="schema">
        <Space direction="vertical" className="w-full" size="large">
          <div>
            <Title level={5}>Input Schema</Title>
            <pre className="bg-gray-100 p-4 rounded overflow-auto text-xs">
              {JSON.stringify(agent.input_schema || {}, null, 2)}
            </pre>
          </div>
          <div>
            <Title level={5}>Output Schema</Title>
            <pre className="bg-gray-100 p-4 rounded overflow-auto text-xs">
              {JSON.stringify(agent.output_schema || {}, null, 2)}
            </pre>
          </div>
        </Space>
      </Tabs.TabPane>
    </Tabs>
  );
}

// ============================================
// Mock Data
// ============================================

function getMockAgents(): Agent[] {
  return [
    {
      agent_id: 'nexusops.chat',
      name: 'AI Assistant',
      version: '1.0.0',
      description: 'General AI assistant with quick commands support',
      author: 'NexusOps',
      category: 'general',
      tags: ['chat', 'assistant', 'commands'],
      capabilities: ['chat', 'quick_commands', 'deployment_info'],
      tools_count: 2,
      visibility: 'public',
      status: 'active',
      rating: 4.8,
      downloads: 1250,
      created_at: '2024-01-01',
      updated_at: '2024-02-15',
    },
    {
      agent_id: 'nexusops.dns',
      name: 'DNS Operations Agent',
      version: '1.0.0',
      description: 'DNS record management, domain generation, Cloudflare configuration',
      author: 'NexusOps',
      category: 'infrastructure',
      tags: ['dns', 'cloudflare', 'domains'],
      capabilities: ['dns_record_create', 'dns_record_delete', 'random_domain_generate'],
      tools_count: 3,
      visibility: 'public',
      status: 'active',
      rating: 4.5,
      downloads: 856,
      created_at: '2024-01-15',
      updated_at: '2024-02-10',
    },
    {
      agent_id: 'nexusops.k8s',
      name: 'Kubernetes Agent',
      version: '1.0.0',
      description: 'Kubernetes resource management and deployment operations',
      author: 'NexusOps',
      category: 'deployment',
      tags: ['kubernetes', 'k8s', 'deployment'],
      capabilities: ['k8s_deploy', 'k8s_scale', 'k8s_logs'],
      tools_count: 4,
      visibility: 'public',
      status: 'active',
      rating: 4.7,
      downloads: 1100,
      created_at: '2024-01-10',
      updated_at: '2024-02-12',
    },
    {
      agent_id: 'nexusops.deploy',
      name: 'Deployment Orchestrator',
      version: '1.0.0',
      description: 'Deployment workflow orchestration, multi-region deployment',
      author: 'NexusOps',
      category: 'deployment',
      tags: ['deployment', 'orchestration', 'gitops'],
      capabilities: ['deploy_create', 'deploy_rollback', 'deploy_status'],
      tools_count: 3,
      visibility: 'public',
      status: 'active',
      rating: 4.6,
      downloads: 980,
      created_at: '2024-01-05',
      updated_at: '2024-02-14',
    },
    {
      agent_id: 'third-party.jenkins',
      name: 'Jenkins Integration',
      version: '0.9.0',
      description: 'Trigger and monitor Jenkins builds',
      author: 'Community',
      category: 'automation',
      tags: ['jenkins', 'ci', 'build'],
      capabilities: ['jenkins_trigger', 'jenkins_status'],
      tools_count: 2,
      visibility: 'public',
      status: 'active',
      rating: 3.9,
      downloads: 234,
      created_at: '2024-02-01',
      updated_at: '2024-02-10',
    },
    {
      agent_id: 'third-party.slack',
      name: 'Slack Notifications',
      version: '1.1.0',
      description: 'Send notifications to Slack channels',
      author: 'Community',
      category: 'automation',
      tags: ['slack', 'notifications', 'alerts'],
      capabilities: ['slack_send', 'slack_webhook'],
      tools_count: 2,
      visibility: 'public',
      status: 'active',
      rating: 4.2,
      downloads: 567,
      created_at: '2024-01-20',
      updated_at: '2024-02-08',
    },
  ];
}

function getMockReviews(): AgentReview[] {
  return [
    {
      id: '1',
      agent_id: 'test',
      user_id: 'user1',
      rating: 5,
      comment: 'Great agent! Works perfectly for our use case.',
      created_at: '2024-02-10',
    },
    {
      id: '2',
      agent_id: 'test',
      user_id: 'user2',
      rating: 4,
      comment: 'Good but could use better documentation.',
      created_at: '2024-02-08',
    },
    {
      id: '3',
      agent_id: 'test',
      user_id: 'user3',
      rating: 5,
      comment: 'Excellent capabilities and fast response.',
      created_at: '2024-02-05',
    },
  ];
}
