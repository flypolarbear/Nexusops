/**
 * Agent Store 页面
 *
 * Built-in Agents:
 * - Kubernetes Agent: 执行 K8s 相关命令
 * - Log Agent: 查询云平台日志
 * - Deploy Agent: 部署管理
 * - Monitor Agent: 监控告警
 */

import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  Card,
  Typography,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Descriptions,
  Badge,
  Avatar,
  Tooltip,
  Alert,
  Collapse,
  Divider,
  Switch,
  message,
} from 'antd'
import {
  ShopOutlined,
  SafetyOutlined,
  FileSearchOutlined,
  RocketOutlined,
  DashboardOutlined,
  ThunderboltOutlined,
  SettingOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  CodeOutlined,
  BookOutlined,
} from '@ant-design/icons'

const { Title, Text } = Typography

// ============================================
// Types
// ============================================

interface AgentSkill {
  id: string
  name: string
  description: string
  command: string
  parameters: string[]
  example: string
}

interface Agent {
  id: string
  name: string
  description: string
  icon: React.ReactNode
  category: 'infrastructure' | 'operations' | 'monitoring' | 'deployment'
  status: 'builtin' | 'installed' | 'available'
  version: string
  skills: AgentSkill[]
  config_required: boolean
  enabled: boolean
}

// ============================================
// Built-in Agents Definition
// ============================================

const BUILTIN_AGENTS: Agent[] = [
  {
    id: 'agent-kubernetes',
    name: 'Kubernetes Agent',
    description: 'Execute Kubernetes cluster commands, manage pods, deployments, services, etc.',
    icon: <SafetyOutlined />,
    category: 'infrastructure',
    status: 'builtin',
    version: '1.0.0',
    enabled: true,
    config_required: true,
    skills: [
      {
        id: 'k8s-get-pods',
        name: 'Get Pod List',
        description: 'List Pods in a specific namespace',
        command: 'kubectl get pods',
        parameters: ['namespace', 'label_selector', 'field_selector'],
        example: 'kubectl get pods -n production -l app=api-server',
      },
      {
        id: 'k8s-describe-pod',
        name: 'View Pod Details',
        description: 'Get detailed info and events of a Pod',
        command: 'kubectl describe pod',
        parameters: ['pod_name', 'namespace'],
        example: 'kubectl describe pod api-server-1 -n production',
      },
      {
        id: 'k8s-logs',
        name: 'Get Pod Logs',
        description: 'View Pod container logs',
        command: 'kubectl logs',
        parameters: ['pod_name', 'namespace', 'container', 'tail_lines', 'follow'],
        example: 'kubectl logs api-server-1 -n production --tail=100',
      },
      {
        id: 'k8s-exec',
        name: 'Exec Container Command',
        description: 'Execute a command inside a Pod container',
        command: 'kubectl exec',
        parameters: ['pod_name', 'namespace', 'container', 'command'],
        example: 'kubectl exec api-server-1 -n production -- ls /app',
      },
      {
        id: 'k8s-apply',
        name: 'Apply YAML Config',
        description: 'Apply Kubernetes YAML configuration file',
        command: 'kubectl apply',
        parameters: ['manifest', 'namespace'],
        example: 'kubectl apply -f deployment.yaml -n production',
      },
      {
        id: 'k8s-scale',
        name: 'Scale Deployment',
        description: 'Adjust Deployment replica count',
        command: 'kubectl scale',
        parameters: ['deployment_name', 'namespace', 'replicas'],
        example: 'kubectl scale deployment api-server --replicas=3 -n production',
      },
      {
        id: 'k8s-rollout',
        name: 'Manage Rollout',
        description: 'View and rollback Deployment rollouts',
        command: 'kubectl rollout',
        parameters: ['deployment_name', 'namespace', 'action'],
        example: 'kubectl rollout status deployment/api-server -n production',
      },
      {
        id: 'k8s-port-forward',
        name: 'Port Forwarding',
        description: 'Forward local port to Pod',
        command: 'kubectl port-forward',
        parameters: ['pod_name', 'namespace', 'local_port', 'remote_port'],
        example: 'kubectl port-forward api-server-1 8080:80 -n production',
      },
    ],
  },
  {
    id: 'agent-log',
    name: 'Log Agent',
    description: 'Query cloud platform logs with multi-source, smart analysis and alerts',
    icon: <FileSearchOutlined />,
    category: 'operations',
    status: 'builtin',
    version: '1.0.0',
    enabled: true,
    config_required: true,
    skills: [
      {
        id: 'log-query',
        name: 'Log Query',
        description: 'Query logs based on conditions',
        command: 'log query',
        parameters: ['query', 'time_range', 'service', 'level', 'limit'],
        example: 'log query "error AND api-server" --time-range 1h --level ERROR',
      },
      {
        id: 'log-search',
        name: 'Keyword Search',
        description: 'Search keywords in logs',
        command: 'log search',
        parameters: ['keyword', 'time_range', 'case_sensitive'],
        example: 'log search "OutOfMemoryError" --time-range 24h',
      },
      {
        id: 'log-aggregate',
        name: 'Log Aggregate',
        description: 'Aggregate and count logs by fields',
        command: 'log aggregate',
        parameters: ['query', 'group_by', 'aggregation', 'time_range'],
        example: 'log aggregate "*" --group-by service,level --sum count',
      },
      {
        id: 'log-trace',
        name: 'Trace Route',
        description: 'Trace full request chain using trace_id',
        command: 'log trace',
        parameters: ['trace_id', 'time_range'],
        example: 'log trace abc-123-def --time-range 1h',
      },
      {
        id: 'log-analyze',
        name: 'Smart Analysis',
        description: 'Use AI to analyze log patterns and anomalies',
        command: 'log analyze',
        parameters: ['query', 'time_range', 'analysis_type'],
        example: 'log analyze "service=api" --time-range 6h --type anomaly',
      },
      {
        id: 'log-tail',
        name: 'Real-time Log Stream',
        description: 'View live log stream',
        command: 'log tail',
        parameters: ['service', 'level', 'filter'],
        example: 'log tail --service api-server --level WARN',
      },
      {
        id: 'log-export',
        name: 'Export Logs',
        description: 'Export logs to a file',
        command: 'log export',
        parameters: ['query', 'time_range', 'format', 'output'],
        example: 'log export "*" --time-range 24h --format json',
      },
    ],
  },
  {
    id: 'agent-deploy',
    name: 'Deploy Agent',
    description: 'Manage app deployment flow, support GitOps and ArgoCD integration',
    icon: <RocketOutlined />,
    category: 'deployment',
    status: 'builtin',
    version: '1.0.0',
    enabled: true,
    config_required: true,
    skills: [
      {
        id: 'deploy-create',
        name: 'Create Deployment',
        description: 'Create a new deployment task',
        command: 'deploy create',
        parameters: ['project', 'version', 'environment', 'config'],
        example: 'deploy create --project api --version v1.2.0 --env production',
      },
      {
        id: 'deploy-status',
        name: 'Query Status',
        description: 'Query deployment status and progress',
        command: 'deploy status',
        parameters: ['deployment_id', 'follow'],
        example: 'deploy status deploy-123 --follow',
      },
      {
        id: 'deploy-rollback',
        name: 'Rollback Deployment',
        description: 'Rollback to a specific version',
        command: 'deploy rollback',
        parameters: ['deployment_id', 'target_version', 'reason'],
        example: 'deploy rollback deploy-123 --version v1.1.0',
      },
      {
        id: 'deploy-history',
        name: 'Deployment History',
        description: 'View deployment history records',
        command: 'deploy history',
        parameters: ['project', 'environment', 'limit'],
        example: 'deploy history --project api --env production --limit 20',
      },
      {
        id: 'deploy-validate',
        name: 'Validate Config',
        description: 'Verify if the deployment configuration is correct',
        command: 'deploy validate',
        parameters: ['config_path', 'environment'],
        example: 'deploy validate --config ./deploy.yaml --env production',
      },
    ],
  },
  {
    id: 'agent-monitor',
    name: 'Monitor Agent',
    description: 'Monitor services and infrastructure, configure alert rules',
    icon: <DashboardOutlined />,
    category: 'monitoring',
    status: 'builtin',
    version: '1.0.0',
    enabled: true,
    config_required: true,
    skills: [
      {
        id: 'monitor-metrics',
        name: 'Get Metrics',
        description: 'Query system and service metrics',
        command: 'monitor metrics',
        parameters: ['service', 'metric_name', 'time_range', 'aggregation'],
        example: 'monitor metrics --service api --name cpu_usage --time-range 1h',
      },
      {
        id: 'monitor-health',
        name: 'Health Check',
        description: 'Check service health status',
        command: 'monitor health',
        parameters: ['service', 'detailed'],
        example: 'monitor health --service api-server --detailed',
      },
      {
        id: 'monitor-alert',
        name: 'Manage Alerts',
        description: 'Create and manage alert rules',
        command: 'monitor alert',
        parameters: ['action', 'rule_name', 'condition', 'severity'],
        example: 'monitor alert create --name high-cpu --condition "cpu>80%" --severity warning',
      },
      {
        id: 'monitor-dashboard',
        name: 'Generate Report',
        description: 'Generate monitoring reports',
        command: 'monitor report',
        parameters: ['time_range', 'services', 'format'],
        example: 'monitor report --time-range 7d --services api,db --format pdf',
      },
    ],
  },
  {
    id: 'agent-cost',
    name: 'Cost Agent',
    description: 'Cloud cost analysis, optimization suggestions, budget management',
    icon: <ThunderboltOutlined />,
    category: 'operations',
    status: 'builtin',
    version: '1.0.0',
    enabled: true,
    config_required: true,
    skills: [
      {
        id: 'cost-overview',
        name: 'Cost Overview',
        description: 'Get cloud resource cost overview and trends',
        command: 'cost overview',
        parameters: ['time_range', 'group_by', 'provider'],
        example: 'cost overview --time-range 30d --group-by service --provider aws',
      },
      {
        id: 'cost-breakdown',
        name: 'Cost Breakdown',
        description: 'Breakdown costs by service and resource type',
        command: 'cost breakdown',
        parameters: ['time_range', 'service', 'resource_type'],
        example: 'cost breakdown --time-range 7d --service ec2 --type compute',
      },
      {
        id: 'cost-forecast',
        name: 'Cost Forecast',
        description: 'Predict future cost trends',
        command: 'cost forecast',
        parameters: ['time_range', 'forecast_days', 'service'],
        example: 'cost forecast --time-range 90d --forecast 30 --service all',
      },
      {
        id: 'cost-optimize',
        name: 'Optimization Suggestions',
        description: 'AI analysis and generation of cost optimization suggestions',
        command: 'cost optimize',
        parameters: ['service', 'threshold', 'min_savings'],
        example: 'cost optimize --service ec2 --threshold 20% --min-savings 100',
      },
      {
        id: 'cost-budget',
        name: 'Budget Management',
        description: 'Create and manage budgets and alerts',
        command: 'cost budget',
        parameters: ['action', 'budget_name', 'amount', 'alert_threshold'],
        example: 'cost budget create --name monthly-budget --amount 10000 --alert 80%',
      },
      {
        id: 'cost-rid',
        name: 'Idle Resources',
        description: 'Identify underutilized or idle resources',
        command: 'cost idle',
        parameters: ['resource_type', 'utilization_threshold', 'time_range'],
        example: 'cost idle --type ec2 --threshold 5% --time-range 14d',
      },
      {
        id: 'cost-tags',
        name: 'Tag Analysis',
        description: 'Analyze costs grouped by tags',
        command: 'cost tags',
        parameters: ['tag_key', 'time_range', 'sort_by'],
        example: 'cost tags --key environment --time-range 30d --sort cost',
      },
      {
        id: 'cost-export',
        name: 'Export Costs',
        description: 'Export cost reports',
        command: 'cost export',
        parameters: ['time_range', 'format', 'group_by'],
        example: 'cost export --time-range 30d --format csv --group-by service',
      },
    ],
  },
  {
    id: 'agent-cicd',
    name: 'CI/CD Agent',
    description: 'CI/CD pipeline management, supporting Jenkins, GitLab CI, GitHub Actions',
    icon: <CodeOutlined />,
    category: 'deployment',
    status: 'builtin',
    version: '1.0.0',
    enabled: true,
    config_required: true,
    skills: [
      {
        id: 'cicd-pipeline-list',
        name: 'Pipeline List',
        description: 'List all CI/CD pipelines',
        command: 'cicd list',
        parameters: ['project', 'status', 'platform'],
        example: 'cicd list --project api --status running --platform jenkins',
      },
      {
        id: 'cicd-pipeline-trigger',
        name: 'Trigger Pipeline',
        description: 'Manually trigger a CI/CD pipeline',
        command: 'cicd trigger',
        parameters: ['pipeline_id', 'branch', 'parameters', 'environment'],
        example: 'cicd trigger --pipeline api-build --branch main --env staging',
      },
      {
        id: 'cicd-pipeline-status',
        name: 'Pipeline Status',
        description: 'Query pipeline execution status and details',
        command: 'cicd status',
        parameters: ['build_id', 'follow', 'logs'],
        example: 'cicd status --build build-123 --follow --logs',
      },
      {
        id: 'cicd-pipeline-cancel',
        name: 'Cancel Pipeline',
        description: 'Cancel a running pipeline',
        command: 'cicd cancel',
        parameters: ['build_id', 'reason'],
        example: 'cicd cancel --build build-123 --reason "Deployment frozen"',
      },
      {
        id: 'cicd-pipeline-logs',
        name: 'Build Logs',
        description: 'Get pipeline build logs',
        command: 'cicd logs',
        parameters: ['build_id', 'stage', 'tail_lines'],
        example: 'cicd logs --build build-123 --stage deploy --tail 100',
      },
      {
        id: 'cicd-pipeline-history',
        name: 'Build History',
        description: 'View pipeline history execution records',
        command: 'cicd history',
        parameters: ['pipeline_id', 'time_range', 'status', 'limit'],
        example: 'cicd history --pipeline api-build --time-range 7d --status failed --limit 20',
      },
      {
        id: 'cicd-artifact-list',
        name: 'Artifacts List',
        description: 'List build artifacts',
        command: 'cicd artifacts',
        parameters: ['build_id', 'type', 'name_pattern'],
        example: 'cicd artifacts --build build-123 --type docker',
      },
      {
        id: 'cicd-webhook-manage',
        name: 'Webhook Management',
        description: 'Manage CI/CD webhooks',
        command: 'cicd webhook',
        parameters: ['action', 'pipeline_id', 'events', 'url'],
        example: 'cicd webhook create --pipeline api-build --events push,pr',
      },
      {
        id: 'cicd-template-apply',
        name: 'Template Apply',
        description: 'Apply predefined pipeline templates',
        command: 'cicd template',
        parameters: ['template_name', 'project', 'customize'],
        example: 'cicd template apply --name nodejs-app --project api',
      },
      {
        id: 'cicd-metrics',
        name: 'CI/CD Metrics',
        description: 'Get CI/CD performance metrics and statistics',
        command: 'cicd metrics',
        parameters: ['time_range', 'pipeline_id', 'metrics'],
        example: 'cicd metrics --time-range 30d --metrics success_rate,duration',
      },
    ],
  },
]

// ============================================
// Agent Store Page
// ============================================

export default function AgentStore() {
  const { t } = useTranslation()
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)
  const [detailVisible, setDetailVisible] = useState(false)
  const [agents, setAgents] = useState(BUILTIN_AGENTS)

  const handleViewDetail = (agent: Agent) => {
    setSelectedAgent(agent)
    setDetailVisible(true)
  }

  const handleToggleAgent = (agentId: string, enabled: boolean) => {
    setAgents(agents.map(a => a.id === agentId ? { ...a, enabled } : a))
    message.success(`Agent ${enabled ? 'enabled' : 'disabled'}`)
  }

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      infrastructure: 'blue',
      operations: 'green',
      monitoring: 'orange',
      deployment: 'purple',
    }
    return colors[category] || 'default'
  }

  const getCategoryLabel = (category: string) => {
    const labels: Record<string, string> = {
      infrastructure: 'Infrastructure',
      operations: 'Operations',
      monitoring: 'Monitoring',
      deployment: 'Deployment',
    }
    return labels[category] || category
  }

  const columns = [
    {
      title: t('agentStore.agent'),
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: Agent) => (
        <Space>
          <Avatar
            style={{ backgroundColor: record.enabled ? '#1890ff' : '#d9d9d9' }}
            icon={record.icon}
          />
          <div>
            <Text strong>{name}</Text>
            <br />
            <Text type="secondary" className="text-xs">v{record.version}</Text>
          </div>
        </Space>
      ),
    },
    {
      title: t('agentStore.description'),
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: t('agentStore.category'),
      dataIndex: 'category',
      key: 'category',
      render: (category: string) => (
        <Tag color={getCategoryColor(category)}>{getCategoryLabel(category)}</Tag>
      ),
    },
    {
      title: t('agentStore.skills'),
      dataIndex: 'skills',
      key: 'skills',
      render: (skills: AgentSkill[]) => (
        <Badge count={skills.length} showZero color="#1890ff">
          <Tag icon={<CodeOutlined />}>{skills.length} skills</Tag>
        </Badge>
      ),
    },
    {
      title: t('agentStore.status'),
      dataIndex: 'status',
      key: 'status',
      render: (status: string, record: Agent) => (
        <Space>
          <Tag color={status === 'builtin' ? 'green' : 'blue'}>
            {status === 'builtin' ? t('agentStore.builtin') : t('agentStore.installed')}
          </Tag>
          {record.enabled ? (
            <CheckCircleOutlined className="text-green-500" />
          ) : (
            <CloseCircleOutlined className="text-gray-400" />
          )}
        </Space>
      ),
    },
    {
      title: t('agentStore.enabled'),
      dataIndex: 'enabled',
      key: 'enabled',
      render: (enabled: boolean, record: Agent) => (
        <Switch
          checked={enabled}
          onChange={(checked) => handleToggleAgent(record.id, checked)}
          size="small"
        />
      ),
    },
    {
      title: t('agentStore.actions'),
      key: 'actions',
      render: (_: unknown, record: Agent) => (
        <Space>
          <Tooltip title="View Details & Skills">
            <Button
              type="link"
              size="small"
              icon={<BookOutlined />}
              onClick={() => handleViewDetail(record)}
            >
              {t('agentStore.details')}
            </Button>
          </Tooltip>
          <Tooltip title="Configure">
            <Button
              type="link"
              size="small"
              icon={<SettingOutlined />}
            >
              {t('agentStore.config')}
            </Button>
          </Tooltip>
        </Space>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <Title level={4} className="m-0">
          <ShopOutlined className="mr-2" />
          {t('agentStore.title')}
        </Title>
        <Tag color="green">{agents.filter(a => a.enabled).length} {t('agentStore.active')}</Tag>
      </div>

      <Alert
        message={t('agentStore.builtin') + " Agents"}
        description={t('agentStore.builtinMessage')}
        type="info"
        showIcon
      />

      {/* Agent List */}
      <Card>
        <Table
          dataSource={agents}
          columns={columns}
          rowKey="id"
          pagination={false}
        />
      </Card>

      {/* Agent Detail Modal */}
      <Modal
        title={
          <Space>
            {selectedAgent?.icon}
            <span>{selectedAgent?.name}</span>
            <Tag>v{selectedAgent?.version}</Tag>
          </Space>
        }
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={null}
        width={900}
      >
        {selectedAgent && (
          <Space direction="vertical" className="w-full" size="large">
            <Descriptions bordered size="small" column={2}>
              <Descriptions.Item label={t('agentStore.category')}>
                <Tag color={getCategoryColor(selectedAgent.category)}>
                  {getCategoryLabel(selectedAgent.category)}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label={t('agentStore.status')}>
                <Tag color={selectedAgent.status === 'builtin' ? 'green' : 'blue'}>
                  {selectedAgent.status === 'builtin' ? t('agentStore.builtin') : t('agentStore.installed')}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label={t('agentStore.skills')}>
                {selectedAgent.skills.length}
              </Descriptions.Item>
              <Descriptions.Item label={t('agentStore.configRequired')}>
                {selectedAgent.config_required ? t('agentStore.yes') : t('agentStore.no')}
              </Descriptions.Item>
            </Descriptions>

            <Divider className="my-4">Skills</Divider>

            <Collapse
              accordion
              items={selectedAgent.skills.map(skill => ({
                key: skill.id,
                label: (
                  <Space>
                    <ThunderboltOutlined className="text-primary-500" />
                    <Text strong>{skill.name}</Text>
                    <Text type="secondary" className="text-xs">({skill.command})</Text>
                  </Space>
                ),
                children: (
                  <Space direction="vertical" className="w-full">
                    <div>
                      <Text strong>Description: </Text>
                      <Text>{skill.description}</Text>
                    </div>
                    <div>
                      <Text strong>Command: </Text>
                      <Text code>{skill.command}</Text>
                    </div>
                    <div>
                      <Text strong>Parameters: </Text>
                      <Space wrap>
                        {skill.parameters.map(p => (
                          <Tag key={p}>{p}</Tag>
                        ))}
                      </Space>
                    </div>
                    <div>
                      <Text strong>Example:</Text>
                      <pre className="bg-gray-50 p-2 rounded text-xs mt-2 overflow-auto">
                        {skill.example}
                      </pre>
                    </div>
                  </Space>
                ),
              }))}
            />
          </Space>
        )}
      </Modal>
    </div>
  )
}
