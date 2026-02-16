/**
 * Agent 响应渲染器
 *
 * 用于渲染 Agent 返回的结构化响应，包括：
 * - Markdown 内容
 * - 结构化输出（表格、状态、资源）
 * - 建议操作按钮
 * - 关联资源链接
 */

import React from 'react';
import {
  Card,
  Button,
  Space,
  Tag,
  Typography,
  Table,
  Descriptions,
  Alert,
  Tooltip,
  Divider,
  Badge,
  Statistic,
  Row,
  Col,
} from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  SyncOutlined,
  LoadingOutlined,
  ExclamationCircleOutlined,
  RocketOutlined,
  GlobalOutlined,
  WarningOutlined,
  DockerOutlined,
  AppstoreOutlined,
  ApiOutlined,
  FolderOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type {
  AgentAction,
  RelatedResource,
  AgentMessage,
} from '../types/agent';

const { Text, Paragraph } = Typography;

// ============================================
// Props 定义
// ============================================

interface AgentResponseRendererProps {
  // 消息内容
  message: AgentMessage;

  // 加载状态
  loading?: boolean;

  // 操作回调
  onActionClick?: (action: AgentAction) => void;
  onResourceClick?: (resource: RelatedResource) => void;

  // 样式
  className?: string;
}

// ============================================
// 主组件
// ============================================

export function AgentResponseRenderer({
  message,
  loading,
  onActionClick,
  onResourceClick,
  className,
}: AgentResponseRendererProps) {
  return (
    <div className={`agent-response space-y-4 ${className || ''}`}>
      {/* Agent 标识 */}
      {message.agent_id && (
        <div className="flex items-center gap-2 mb-2">
          <Tag color="purple">{message.agent_name || message.agent_id}</Tag>
          {message.metadata?.agent_version && (
            <Text type="secondary" className="text-xs">
              v{message.metadata.agent_version}
            </Text>
          )}
        </div>
      )}

      {/* Markdown 内容 */}
      {message.content && (
        <div className="prose prose-sm max-w-none dark:prose-invert">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
        </div>
      )}

      {/* 结构化输出 */}
      {message.structured_output && (
        <StructuredOutputRenderer
          type={message.structured_output.type}
          data={message.structured_output.data}
        />
      )}

      {/* 建议操作 */}
      {message.suggested_actions && message.suggested_actions.length > 0 && (
        <div className="suggested-actions">
          <Divider orientation="left" className="text-sm text-gray-400">
            Suggested Actions
          </Divider>
          <Space wrap>
            {message.suggested_actions.map((action) => (
              <ActionButton
                key={action.id}
                action={action}
                onClick={() => onActionClick?.(action)}
              />
            ))}
          </Space>
        </div>
      )}

      {/* 关联资源 */}
      {message.related_resources && message.related_resources.length > 0 && (
        <div className="related-resources mt-4">
          <Text type="secondary" className="text-xs block mb-2">Related Resources:</Text>
          <Space wrap>
            {message.related_resources.map((resource, index) => (
              <ResourceTag
                key={`${resource.type}-${resource.id}-${index}`}
                resource={resource}
                onClick={() => onResourceClick?.(resource)}
              />
            ))}
          </Space>
        </div>
      )}

      {/* 元数据 */}
      {message.metadata && (
        <ResponseMetadata metadata={message.metadata} />
      )}

      {/* 加载状态 */}
      {loading && (
        <div className="flex items-center gap-2 text-gray-400">
          <LoadingOutlined spin />
          <Text type="secondary">Thinking...</Text>
        </div>
      )}
    </div>
  );
}

// ============================================
// 结构化输出渲染器
// ============================================

interface StructuredOutputRendererProps {
  type: string;
  data: unknown;
}

function StructuredOutputRenderer({ type, data }: StructuredOutputRendererProps) {
  switch (type) {
    case 'deployment_status':
      return <DeploymentStatusRenderer data={data as DeploymentStatusData} />;
    case 'resource_analysis':
      return <ResourceAnalysisRenderer data={data as ResourceAnalysisData} />;
    case 'alert_summary':
      return <AlertSummaryRenderer data={data as AlertSummaryData} />;
    case 'version_comparison':
      return <VersionComparisonRenderer data={data as VersionComparisonData} />;
    case 'dns_record':
      return <DnsRecordRenderer data={data as DnsRecordData} />;
    case 'k8s_resource':
      return <K8sResourceRenderer data={data as K8sResourceData} />;
    case 'error_diagnosis':
      return <ErrorDiagnosisRenderer data={data as ErrorDiagnosisData} />;
    default:
      return (
        <Card size="small" className="bg-gray-50">
          <pre className="text-xs overflow-auto">
            {JSON.stringify(data, null, 2)}
          </pre>
        </Card>
      );
  }
}

// ============================================
// 部署状态渲染器
// ============================================

interface DeploymentStatusData {
  version?: string;
  codename?: string;
  regions?: Array<{
    name: string;
    status: 'healthy' | 'warning' | 'critical';
    replicas?: {
      ready: number;
      total: number;
    };
    last_deployed?: string;
  }>;
}

function DeploymentStatusRenderer({ data }: { data: DeploymentStatusData }) {
  if (!data) return null;

  return (
    <Card size="small" title="Deployment Status" className="mt-2">
      {data.codename && (
        <div className="mb-3">
          <Tag color="purple">{data.codename}</Tag>
          {data.version && <Text type="secondary" className="ml-2">{data.version}</Text>}
        </div>
      )}

      {data.regions && (
        <Table
          size="small"
          dataSource={data.regions}
          rowKey="name"
          pagination={false}
          columns={[
            {
              title: 'Region',
              dataIndex: 'name',
              key: 'name',
              render: (name: string) => (
                <span className="flex items-center gap-1">
                  <GlobalOutlined />
                  {name}
                </span>
              ),
            },
            {
              title: 'Status',
              dataIndex: 'status',
              key: 'status',
              render: (status: string) => <StatusBadge status={status} />,
            },
            {
              title: 'Replicas',
              dataIndex: 'replicas',
              key: 'replicas',
              render: (replicas: { ready: number; total: number }) =>
                replicas ? `${replicas.ready}/${replicas.total}` : '-',
            },
            {
              title: 'Last Deployed',
              dataIndex: 'last_deployed',
              key: 'last_deployed',
              render: (time: string) => time || '-',
            },
          ]}
        />
      )}
    </Card>
  );
}

// ============================================
// 资源分析渲染器
// ============================================

interface ResourceAnalysisData {
  resource_type?: string;
  resource_name?: string;
  namespace?: string;
  status?: string;
  issues?: Array<{
    severity: 'low' | 'medium' | 'high' | 'critical';
    message: string;
    recommendation?: string;
  }>;
  metrics?: Record<string, { value: number | string; unit?: string }>;
}

function ResourceAnalysisRenderer({ data }: { data: ResourceAnalysisData }) {
  if (!data) return null;

  return (
    <Card size="small" title="Resource Analysis" className="mt-2">
      <Descriptions size="small" column={2} bordered>
        <Descriptions.Item label="Resource">
          {data.resource_name}
        </Descriptions.Item>
        <Descriptions.Item label="Type">
          <Tag>{data.resource_type}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Namespace">
          {data.namespace || 'default'}
        </Descriptions.Item>
        <Descriptions.Item label="Status">
          {data.status && <StatusBadge status={data.status} />}
        </Descriptions.Item>
      </Descriptions>

      {data.issues && data.issues.length > 0 && (
        <div className="mt-3">
          <Text strong className="block mb-2">Issues Found</Text>
          {data.issues.map((issue, index) => (
            <Alert
              key={index}
              message={issue.message}
              description={issue.recommendation}
              type={
                issue.severity === 'critical' ? 'error' :
                issue.severity === 'high' ? 'error' :
                issue.severity === 'medium' ? 'warning' : 'info'
              }
              showIcon
              className="mb-2"
            />
          ))}
        </div>
      )}

      {data.metrics && (
        <div className="mt-3">
          <Text strong className="block mb-2">Metrics</Text>
          <Row gutter={16}>
            {Object.entries(data.metrics).map(([key, metric]) => (
              <Col key={key} span={6}>
                <Statistic
                  title={key}
                  value={metric.value}
                  suffix={metric.unit}
                />
              </Col>
            ))}
          </Row>
        </div>
      )}
    </Card>
  );
}

// ============================================
// 告警摘要渲染器
// ============================================

interface AlertSummaryData {
  total_alerts?: number;
  by_severity?: Record<string, number>;
  alerts?: Array<{
    id: string;
    name: string;
    severity: string;
    status: string;
    started_at?: string;
  }>;
}

function AlertSummaryRenderer({ data }: { data: AlertSummaryData }) {
  if (!data) return null;

  return (
    <Card size="small" title="Alert Summary" className="mt-2">
      <Row gutter={16} className="mb-3">
        <Col span={6}>
          <Statistic title="Total" value={data.total_alerts || 0} />
        </Col>
        <Col span={6}>
          <Statistic
            title="Critical"
            value={data.by_severity?.critical || 0}
            valueStyle={{ color: '#cf1322' }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="Warning"
            value={data.by_severity?.warning || 0}
            valueStyle={{ color: '#fa8c16' }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="Info"
            value={data.by_severity?.info || 0}
            valueStyle={{ color: '#1890ff' }}
          />
        </Col>
      </Row>

      {data.alerts && data.alerts.length > 0 && (
        <Table
          size="small"
          dataSource={data.alerts}
          rowKey="id"
          pagination={false}
          columns={[
            { title: 'Alert', dataIndex: 'name', key: 'name' },
            {
              title: 'Severity',
              dataIndex: 'severity',
              key: 'severity',
              render: (severity: string) => (
                <Tag
                  color={
                    severity === 'critical' ? 'red' :
                    severity === 'warning' ? 'orange' : 'blue'
                  }
                >
                  {severity}
                </Tag>
              ),
            },
            {
              title: 'Status',
              dataIndex: 'status',
              key: 'status',
            },
            {
              title: 'Started',
              dataIndex: 'started_at',
              key: 'started_at',
            },
          ]}
        />
      )}
    </Card>
  );
}

// ============================================
// 版本对比渲染器
// ============================================

interface VersionComparisonData {
  version1?: { name: string; codename: string };
  version2?: { name: string; codename: string };
  differences?: Array<{
    aspect: string;
    v1_value: string;
    v2_value: string;
  }>;
  recommendation?: string;
}

function VersionComparisonRenderer({ data }: { data: VersionComparisonData }) {
  if (!data) return null;

  return (
    <Card size="small" title="Version Comparison" className="mt-2">
      <Table
        size="small"
        dataSource={data.differences || []}
        rowKey="aspect"
        pagination={false}
        columns={[
          { title: 'Aspect', dataIndex: 'aspect', key: 'aspect' },
          {
            title: data.version1?.codename || 'Version 1',
            dataIndex: 'v1_value',
            key: 'v1_value',
          },
          {
            title: data.version2?.codename || 'Version 2',
            dataIndex: 'v2_value',
            key: 'v2_value',
          },
        ]}
      />

      {data.recommendation && (
        <Alert
          message="Recommendation"
          description={data.recommendation}
          type="info"
          showIcon
          className="mt-3"
        />
      )}
    </Card>
  );
}

// ============================================
// DNS 记录渲染器
// ============================================

interface DnsRecordData {
  records?: Array<{
    type: string;
    name: string;
    content: string;
    ttl: number;
    proxied?: boolean;
    status?: string;
  }>;
  zone?: string;
}

function DnsRecordRenderer({ data }: { data: DnsRecordData }) {
  if (!data) return null;

  return (
    <Card size="small" title="DNS Records" className="mt-2">
      {data.zone && (
        <Text type="secondary" className="block mb-2">Zone: {data.zone}</Text>
      )}

      <Table
        size="small"
        dataSource={data.records || []}
        rowKey="name"
        pagination={false}
        columns={[
          { title: 'Type', dataIndex: 'type', key: 'type', width: 80 },
          { title: 'Name', dataIndex: 'name', key: 'name' },
          { title: 'Content', dataIndex: 'content', key: 'content' },
          { title: 'TTL', dataIndex: 'ttl', key: 'ttl', width: 80 },
          {
            title: 'Proxied',
            dataIndex: 'proxied',
            key: 'proxied',
            width: 80,
            render: (proxied: boolean) =>
              proxied ? <Tag color="orange">Yes</Tag> : <Tag>No</Tag>,
          },
        ]}
      />
    </Card>
  );
}

// ============================================
// K8s 资源渲染器
// ============================================

interface K8sResourceData {
  kind?: string;
  name?: string;
  namespace?: string;
  status?: string;
  pods?: Array<{
    name: string;
    status: string;
    ready: boolean;
    restarts: number;
  }>;
  events?: Array<{
    type: string;
    message: string;
    count: number;
  }>;
}

function K8sResourceRenderer({ data }: { data: K8sResourceData }) {
  if (!data) return null;

  return (
    <Card size="small" title={`K8s Resource: ${data.kind}/${data.name}`} className="mt-2">
      <Descriptions size="small" column={2} bordered>
        <Descriptions.Item label="Name">{data.name}</Descriptions.Item>
        <Descriptions.Item label="Namespace">{data.namespace}</Descriptions.Item>
        <Descriptions.Item label="Kind">{data.kind}</Descriptions.Item>
        <Descriptions.Item label="Status">
          {data.status && <StatusBadge status={data.status} />}
        </Descriptions.Item>
      </Descriptions>

      {data.pods && (
        <div className="mt-3">
          <Text strong className="block mb-2">Pods</Text>
          <Table
            size="small"
            dataSource={data.pods}
            rowKey="name"
            pagination={false}
            columns={[
              { title: 'Name', dataIndex: 'name', key: 'name' },
              {
                title: 'Status',
                dataIndex: 'status',
                key: 'status',
                render: (status: string) => <StatusBadge status={status} />,
              },
              {
                title: 'Ready',
                dataIndex: 'ready',
                key: 'ready',
                render: (ready: boolean) =>
                  ready ? <CheckCircleOutlined className="text-green-500" /> : <CloseCircleOutlined className="text-red-500" />,
              },
              { title: 'Restarts', dataIndex: 'restarts', key: 'restarts' },
            ]}
          />
        </div>
      )}
    </Card>
  );
}

// ============================================
// 错误诊断渲染器
// ============================================

interface ErrorDiagnosisData {
  error_type?: string;
  error_message?: string;
  root_cause?: string;
  affected_resources?: string[];
  fix_steps?: string[];
}

function ErrorDiagnosisRenderer({ data }: { data: ErrorDiagnosisData }) {
  if (!data) return null;

  return (
    <Card size="small" title="Error Diagnosis" className="mt-2">
      <Alert
        message={data.error_type || 'Error'}
        description={data.error_message}
        type="error"
        showIcon
        className="mb-3"
      />

      {data.root_cause && (
        <div className="mb-3">
          <Text strong>Root Cause:</Text>
          <Paragraph>{data.root_cause}</Paragraph>
        </div>
      )}

      {data.fix_steps && data.fix_steps.length > 0 && (
        <div>
          <Text strong className="block mb-2">Fix Steps:</Text>
          <ol className="list-decimal list-inside space-y-1">
            {data.fix_steps.map((step, index) => (
              <li key={index}>{step}</li>
            ))}
          </ol>
        </div>
      )}
    </Card>
  );
}

// ============================================
// 辅助组件
// ============================================

function StatusBadge({ status }: { status: string }) {
  const statusConfig: Record<string, { color: string; icon: React.ReactNode }> = {
    healthy: { color: 'green', icon: <CheckCircleOutlined /> },
    success: { color: 'green', icon: <CheckCircleOutlined /> },
    running: { color: 'blue', icon: <SyncOutlined spin /> },
    warning: { color: 'orange', icon: <ExclamationCircleOutlined /> },
    critical: { color: 'red', icon: <CloseCircleOutlined /> },
    error: { color: 'red', icon: <CloseCircleOutlined /> },
    degraded: { color: 'orange', icon: <ExclamationCircleOutlined /> },
    progressing: { color: 'blue', icon: <LoadingOutlined /> },
    pending: { color: 'default', icon: <ClockCircleOutlined /> },
  };

  const config = statusConfig[status.toLowerCase()] || { color: 'default', icon: null };

  return (
    <Tag color={config.color} icon={config.icon}>
      {status.toUpperCase()}
    </Tag>
  );
}

function ActionButton({ action, onClick }: { action: AgentAction; onClick: () => void }) {
  const buttonType = action.danger ? 'primary' : 'default';
  const buttonDanger = action.danger;

  return (
    <Tooltip title={action.confirm_required ? 'Requires confirmation' : undefined}>
      <Button
        type={buttonType}
        danger={buttonDanger}
        size="small"
        icon={action.icon}
        onClick={onClick}
      >
        {action.label}
        {action.confirm_required && <ExclamationCircleOutlined className="ml-1" />}
      </Button>
    </Tooltip>
  );
}

function ResourceTag({ resource, onClick }: { resource: RelatedResource; onClick?: () => void }) {
  const typeConfig: Record<string, { color: string; icon: React.ReactNode }> = {
    version: { color: 'purple', icon: <RocketOutlined /> },
    deployment: { color: 'blue', icon: <DockerOutlined /> },
    pod: { color: 'cyan', icon: <AppstoreOutlined /> },
    service: { color: 'geekblue', icon: <ApiOutlined /> },
    alert: { color: 'orange', icon: <WarningOutlined /> },
    region: { color: 'green', icon: <GlobalOutlined /> },
    project: { color: 'magenta', icon: <FolderOutlined /> },
  };

  const config = typeConfig[resource.type] || { color: 'default', icon: null };

  return (
    <Tag
      color={config.color}
      icon={config.icon}
      className="cursor-pointer"
      onClick={onClick}
    >
      {resource.name}
      {resource.status && (
        <Badge
          status={
            resource.status === 'healthy' ? 'success' :
            resource.status === 'warning' ? 'warning' :
            resource.status === 'critical' ? 'error' : 'default'
          }
          className="ml-1"
        />
      )}
    </Tag>
  );
}

function ResponseMetadata({ metadata }: { metadata: Record<string, unknown> }) {
  const latencyMs = typeof metadata.latency_ms === 'number' ? metadata.latency_ms : null;
  const tokensUsed = metadata.tokens_used as { input?: number; output?: number } | undefined;
  const model = typeof metadata.model === 'string' ? metadata.model : null;

  return (
    <div className="text-xs text-gray-400 mt-2 flex items-center gap-3">
      {latencyMs !== null && (
        <span>Latency: {latencyMs}ms</span>
      )}
      {tokensUsed && (
        <span>
          Tokens: {(tokensUsed.input || 0) + (tokensUsed.output || 0)}
        </span>
      )}
      {model && (
        <span>Model: {model}</span>
      )}
    </div>
  );
}

export default AgentResponseRenderer;
