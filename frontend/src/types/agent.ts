/**
 * Agent 类型定义
 *
 * 基于 MCP (Model Context Protocol) 和 A2A (Agent-to-Agent) 标准
 * 参考: https://modelcontextprotocol.io/
 * 参考: https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/
 */

// ============================================
// Agent 身份与能力声明
// ============================================

/**
 * Agent 类型
 */
export type AgentType =
  | 'nexusops.chat'      // 通用聊天 Agent
  | 'nexusops.dns'       // DNS 操作 Agent
  | 'nexusops.k8s'       // K8s 操作 Agent
  | 'nexusops.ssl'       // SSL 证书 Agent
  | 'nexusops.deploy'    // 部署编排 Agent
  | 'nexusops.alert'     // 告警分析 Agent
  | 'nexusops.git'       // Git 操作 Agent
  | 'custom';            // 自定义 Agent

/**
 * Agent 身份
 */
export interface AgentIdentity {
  agent_id: string;
  agent_name: string;
  agent_version: string;
  agent_type: 'builtin' | 'third_party';
  provider: string;
}

/**
 * Agent 工具定义 (MCP Tool)
 */
export interface AgentTool {
  name: string;
  description: string;
  inputSchema: JSONSchema;
  handler?: (params: Record<string, unknown>) => Promise<AgentToolResult>;
}

/**
 * Agent 工具调用结果
 */
export interface AgentToolResult {
  success: boolean;
  data?: unknown;
  error?: string;
}

/**
 * Agent 能力声明 (Manifest)
 */
export interface AgentManifest {
  // 基本信息
  agent_id: string;
  name: string;
  version: string;
  description: string;
  author?: string;
  category: AgentCategory;

  // 能力
  capabilities: string[];

  // 输入输出 Schema
  input_schema?: JSONSchema;
  output_schema?: JSONSchema;

  // 工具
  tools?: AgentTool[];

  // 示例
  examples?: AgentExample[];

  // 端点
  endpoints?: {
    invoke?: string;
    stream?: string;
    tools?: string;
  };

  // 认证
  auth?: {
    type: 'bearer' | 'api_key' | 'oauth2' | 'none';
    header?: string;
  };

  // A2A 能力
  a2a_capabilities?: {
    can_request_from?: string[];  // 可以接收来自哪些 Agent 的请求
    can_respond_to?: string[];    // 可以响应哪些 Agent
    can_delegate_to?: string[];   // 可以委托给哪些 Agent
  };

  // 元数据
  metadata?: {
    created_at?: string;
    updated_at?: string;
    status?: 'active' | 'inactive' | 'deprecated';
    tags?: string[];
  };
}

/**
 * Agent 分类
 */
export type AgentCategory =
  | 'general'        // 通用
  | 'diagnostics'   // 诊断
  | 'deployment'    // 部署
  | 'infrastructure' // 基础设施
  | 'security'      // 安全
  | 'monitoring'    // 监控
  | 'automation';   // 自动化

/**
 * Agent 示例
 */
export interface AgentExample {
  input: Record<string, unknown>;
  output: Record<string, unknown>;
  description?: string;
}

// ============================================
// Agent 请求与响应
// ============================================

/**
 * Agent 请求 (统一请求格式)
 */
export interface AgentRequest {
  // 请求标识
  request_id: string;
  conversation_id: string;

  // Agent 标识
  agent_id: string;

  // 用户查询
  query: string;

  // 上下文
  context: AgentRequestContext;

  // 输出配置
  output_config?: AgentOutputConfig;

  // Function Calling 配置
  tools?: AgentToolDefinition[];
  tool_choice?: 'auto' | 'required' | 'none' | { type: 'function'; name: string };
}

/**
 * Agent 请求上下文
 */
export interface AgentRequestContext {
  // 用户信息
  user_id?: string;
  tenant_id?: string;

  // 资源上下文
  project_id?: string;
  version_id?: string;
  codename?: string;
  region?: string;

  // K8s 资源上下文
  resource_type?: string;
  resource_name?: string;
  namespace?: string;

  // 其他上下文
  [key: string]: unknown;
}

/**
 * Agent 输出配置
 */
export interface AgentOutputConfig {
  format: 'json' | 'markdown' | 'stream';
  schema?: string;  // JSON Schema URI
  max_tokens?: number;
  temperature?: number;
}

/**
 * Agent 工具定义 (用于 Function Calling)
 */
export interface AgentToolDefinition {
  type: 'function';
  function: {
    name: string;
    description: string;
    parameters: JSONSchema;
  };
}

/**
 * Agent 响应 (统一响应格式)
 */
export interface AgentResponse {
  // 请求标识
  request_id: string;

  // 响应状态
  status: AgentResponseStatus;

  // 主要内容
  content: AgentContent;

  // 结构化输出
  structured_output?: unknown;

  // 建议操作
  suggested_actions?: AgentAction[];

  // 工具调用结果
  tool_calls?: AgentToolCallResult[];

  // 关联资源
  related_resources?: RelatedResource[];

  // 元数据
  metadata?: AgentResponseMetadata;

  // 错误信息
  error?: AgentError;
}

/**
 * Agent 响应状态
 */
export type AgentResponseStatus = 'success' | 'error' | 'partial' | 'pending';

/**
 * Agent 内容
 */
export interface AgentContent {
  text: string;
  format: 'markdown' | 'json' | 'plain';
  data?: unknown;
}

/**
 * Agent 建议操作
 */
export interface AgentAction {
  id: string;
  type: AgentActionType;
  label: string;
  params: Record<string, unknown>;
  confirm_required?: boolean;
  danger?: boolean;
  icon?: React.ReactNode;
}

/**
 * Agent 操作类型
 */
export type AgentActionType =
  | 'deploy'
  | 'rollback'
  | 'scale'
  | 'fix'
  | 'navigate'
  | 'query'
  | 'copy'
  | 'download'
  | 'refresh';

/**
 * Agent 工具调用结果
 */
export interface AgentToolCallResult {
  tool_call_id: string;
  tool_name: string;
  status: 'success' | 'error';
  result?: unknown;
  error?: string;
}

/**
 * 关联资源
 */
export interface RelatedResource {
  type: RelatedResourceType;
  id: string;
  name: string;
  link?: string;
  status?: string;
}

/**
 * 关联资源类型
 */
export type RelatedResourceType =
  | 'version'
  | 'deployment'
  | 'pod'
  | 'service'
  | 'alert'
  | 'region'
  | 'project';

/**
 * Agent 响应元数据
 */
export interface AgentResponseMetadata {
  model?: string;
  latency_ms?: number;
  tokens_used?: {
    input: number;
    output: number;
    total: number;
  };
  agent_name?: string;
  agent_version?: string;
  [key: string]: unknown;
}

/**
 * Agent 错误
 */
export interface AgentError {
  code: AgentErrorCode;
  message: string;
  details?: Record<string, unknown>;
  retry_after?: number;
}

/**
 * Agent 错误码
 */
export enum AgentErrorCode {
  // 执行错误
  TIMEOUT = 'TIMEOUT',
  CRASH = 'CRASH',
  RESOURCE_EXHAUSTED = 'RESOURCE_EXHAUSTED',

  // 响应错误
  INVALID_JSON = 'INVALID_JSON',
  SCHEMA_VIOLATION = 'SCHEMA_VIOLATION',
  PARTIAL_RESULT = 'PARTIAL_RESULT',

  // 外部错误
  EXTERNAL_API_ERROR = 'EXTERNAL_API_ERROR',
  NETWORK_ERROR = 'NETWORK_ERROR',
  AUTHENTICATION_ERROR = 'AUTHENTICATION_ERROR',

  // 业务错误
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  NOT_FOUND = 'NOT_FOUND',
  PERMISSION_DENIED = 'PERMISSION_DENIED',

  // 系统错误
  INTERNAL_ERROR = 'INTERNAL_ERROR',
  UNKNOWN = 'UNKNOWN',
}

// ============================================
// Agent 消息 (用于聊天界面)
// ============================================

/**
 * Agent 消息
 */
export interface AgentMessage {
  id: string;
  conversation_id: string;

  // 角色
  role: 'user' | 'assistant' | 'system' | 'tool';

  // 内容
  content: string;

  // Agent 标识
  agent_id?: string;
  agent_name?: string;

  // 结构化输出
  structured_output?: {
    type: StructuredOutputType;
    data: unknown;
  };

  // 建议操作
  suggested_actions?: AgentAction[];

  // 关联资源
  related_resources?: RelatedResource[];

  // 工具调用
  tool_calls?: {
    id: string;
    name: string;
    arguments: Record<string, unknown>;
  }[];

  // 元数据
  metadata?: AgentResponseMetadata;

  // 时间戳
  created_at: string;
}

/**
 * 结构化输出类型
 */
export type StructuredOutputType =
  | 'deployment_status'
  | 'resource_analysis'
  | 'alert_summary'
  | 'version_comparison'
  | 'dns_record'
  | 'k8s_resource'
  | 'error_diagnosis';

// ============================================
// Agent 上下文 (Store)
// ============================================

/**
 * Agent 上下文状态
 */
export interface AgentContextState {
  // 当前上下文
  current_project_id: string | null;
  current_version_id: string | null;
  current_codename: string | null;
  current_region: string | null;
  current_resource: AgentResourceContext | null;

  // 用户上下文
  user_id: string | null;
  tenant_id: string | null;

  // 会话上下文
  conversation_id: string | null;

  // Actions
  setProject: (id: string) => void;
  setVersion: (id: string, codename?: string) => void;
  setRegion: (id: string) => void;
  setResource: (resource: AgentResourceContext) => void;
  setUserId: (id: string) => void;
  setTenantId: (id: string) => void;
  setConversationId: (id: string) => void;
  clearContext: () => void;

  // 获取完整上下文
  getFullContext: () => AgentRequestContext;
}

/**
 * Agent 资源上下文
 */
export interface AgentResourceContext {
  type: string;
  name: string;
  namespace?: string;
  cluster?: string;
}

// ============================================
// Agent 工具层
// ============================================

/**
 * Agent 工具权限
 */
export interface AgentToolPermission {
  tool_name: string;
  permission_level: 'read' | 'write' | 'admin';
  conditions?: Record<string, unknown>;
}

/**
 * Agent 工具执行上下文
 */
export interface AgentToolExecutionContext {
  agent_id: string;
  user_id?: string;
  tenant_id?: string;
  project_id?: string;
  request_id: string;
  conversation_id: string;
}

// ============================================
// JSON Schema 类型
// ============================================

/**
 * JSON Schema (简化版)
 */
export interface JSONSchema {
  type: string | string[];
  properties?: Record<string, JSONSchema>;
  required?: string[];
  items?: JSONSchema;
  enum?: (string | number | boolean)[];
  description?: string;
  default?: unknown;
  minimum?: number;
  maximum?: number;
  minLength?: number;
  maxLength?: number;
  pattern?: string;
  format?: string;
  $ref?: string;
  additionalProperties?: boolean | JSONSchema;
  anyOf?: JSONSchema[];
  allOf?: JSONSchema[];
  oneOf?: JSONSchema[];
  [key: string]: unknown;
}

// ============================================
// Agent 注册表
// ============================================

/**
 * Agent 注册信息
 */
export interface AgentRegistration {
  manifest: AgentManifest;
  status: AgentRegistrationStatus;
  registered_at: string;
  last_heartbeat?: string;
  endpoint?: string;
}

/**
 * Agent 注册状态
 */
export type AgentRegistrationStatus =
  | 'active'
  | 'inactive'
  | 'error'
  | 'deprecated';

// ============================================
// 预定义的内置 Agent
// ============================================

/**
 * 内置 Agent 定义
 */
export const BUILTIN_AGENTS: AgentManifest[] = [
  {
    agent_id: 'nexusops.chat',
    name: 'AI Assistant',
    version: '1.0.0',
    description: '通用 AI 助手，支持快捷命令',
    category: 'general',
    capabilities: [
      'chat',
      'quick_commands',
      'deployment_info',
      'status_query',
    ],
    tools: [
      {
        name: 'get_deployment_status',
        description: 'Get deployment status for a version',
        inputSchema: {
          type: 'object',
          properties: {
            codename: { type: 'string', description: 'Version codename' },
            region: { type: 'string', description: 'Target region' },
          },
          required: ['codename'],
        },
      },
      {
        name: 'get_version_info',
        description: 'Get version information',
        inputSchema: {
          type: 'object',
          properties: {
            codename: { type: 'string', description: 'Version codename' },
          },
          required: ['codename'],
        },
      },
    ],
    a2a_capabilities: {
      can_request_from: ['*'],
      can_delegate_to: [
        'nexusops.deploy',
        'nexusops.dns',
        'nexusops.k8s',
        'nexusops.alert',
      ],
    },
  },
  {
    agent_id: 'nexusops.dns',
    name: 'DNS Operations Agent',
    version: '1.0.0',
    description: 'DNS 记录管理、域名生成、Cloudflare 配置',
    category: 'infrastructure',
    capabilities: [
      'dns_record_create',
      'dns_record_delete',
      'dns_record_update',
      'dns_record_query',
      'random_domain_generate',
      'cloudflare_configure',
    ],
    tools: [
      {
        name: 'create_dns_record',
        description: 'Create a DNS record',
        inputSchema: {
          type: 'object',
          properties: {
            zone_id: { type: 'string' },
            record_type: { type: 'string', enum: ['A', 'AAAA', 'CNAME', 'MX', 'TXT', 'NS'] },
            name: { type: 'string' },
            content: { type: 'string' },
            ttl: { type: 'integer', default: 3600 },
            proxied: { type: 'boolean', default: false },
          },
          required: ['zone_id', 'record_type', 'name', 'content'],
        },
      },
      {
        name: 'generate_random_subdomain',
        description: 'Generate a random subdomain name',
        inputSchema: {
          type: 'object',
          properties: {
            base_domain: { type: 'string' },
            levels: { type: 'integer', default: 4 },
            style: { type: 'string', enum: ['random', 'readable', 'uuid'], default: 'readable' },
          },
          required: ['base_domain'],
        },
      },
      {
        name: 'configure_cloudflare',
        description: 'Configure Cloudflare DNS',
        inputSchema: {
          type: 'object',
          properties: {
            zone_name: { type: 'string' },
            subdomain: { type: 'string' },
            target_ip: { type: 'string' },
            ssl_enabled: { type: 'boolean', default: true },
          },
          required: ['zone_name', 'subdomain', 'target_ip'],
        },
      },
    ],
    a2a_capabilities: {
      can_request_from: ['nexusops.chat', 'nexusops.deploy'],
      can_delegate_to: ['nexusops.ssl'],
    },
  },
  {
    agent_id: 'nexusops.k8s',
    name: 'Kubernetes Agent',
    version: '1.0.0',
    description: 'Kubernetes 资源管理、部署操作',
    category: 'deployment',
    capabilities: [
      'k8s_deploy',
      'k8s_scale',
      'k8s_rollback',
      'k8s_logs',
      'k8s_describe',
    ],
    tools: [
      {
        name: 'deploy_manifest',
        description: 'Deploy a Kubernetes manifest',
        inputSchema: {
          type: 'object',
          properties: {
            manifest: { type: 'object' },
            namespace: { type: 'string', default: 'default' },
            dry_run: { type: 'boolean', default: false },
          },
          required: ['manifest'],
        },
      },
      {
        name: 'scale_deployment',
        description: 'Scale a deployment',
        inputSchema: {
          type: 'object',
          properties: {
            name: { type: 'string' },
            namespace: { type: 'string', default: 'default' },
            replicas: { type: 'integer' },
          },
          required: ['name', 'replicas'],
        },
      },
      {
        name: 'get_pod_logs',
        description: 'Get logs from a pod',
        inputSchema: {
          type: 'object',
          properties: {
            pod_name: { type: 'string' },
            namespace: { type: 'string', default: 'default' },
            tail_lines: { type: 'integer', default: 100 },
            container: { type: 'string' },
          },
          required: ['pod_name'],
        },
      },
      {
        name: 'describe_resource',
        description: 'Describe a Kubernetes resource',
        inputSchema: {
          type: 'object',
          properties: {
            resource_type: { type: 'string' },
            name: { type: 'string' },
            namespace: { type: 'string', default: 'default' },
          },
          required: ['resource_type', 'name'],
        },
      },
    ],
    a2a_capabilities: {
      can_request_from: ['nexusops.chat', 'nexusops.deploy'],
      can_delegate_to: [],
    },
  },
  {
    agent_id: 'nexusops.deploy',
    name: 'Deployment Orchestrator',
    version: '1.0.0',
    description: '部署流程编排，协调多 Agent 完成部署任务',
    category: 'deployment',
    capabilities: [
      'deploy_create',
      'deploy_rollback',
      'deploy_status',
      'deploy_force_sync',
      'multi_region_deploy',
    ],
    tools: [
      {
        name: 'create_deployment',
        description: 'Create a new deployment',
        inputSchema: {
          type: 'object',
          properties: {
            version_id: { type: 'string' },
            regions: { type: 'array', items: { type: 'string' } },
            strategy: { type: 'string', enum: ['rolling', 'blue-green', 'canary'] },
          },
          required: ['version_id', 'regions'],
        },
      },
      {
        name: 'rollback_deployment',
        description: 'Rollback a deployment',
        inputSchema: {
          type: 'object',
          properties: {
            version_id: { type: 'string' },
            region: { type: 'string' },
            revision: { type: 'integer' },
          },
          required: ['version_id'],
        },
      },
      {
        name: 'force_sync',
        description: 'Force sync an ArgoCD application',
        inputSchema: {
          type: 'object',
          properties: {
            app_name: { type: 'string' },
            dry_run: { type: 'boolean', default: false },
          },
          required: ['app_name'],
        },
      },
    ],
    a2a_capabilities: {
      can_request_from: ['nexusops.chat', 'nexusops.alert'],
      can_delegate_to: ['nexusops.dns', 'nexusops.k8s', 'nexusops.ssl'],
    },
  },
  {
    agent_id: 'nexusops.alert',
    name: 'Alert Analysis Agent',
    version: '1.0.0',
    description: '告警分析、根因定位、修复建议',
    category: 'monitoring',
    capabilities: [
      'alert_analyze',
      'root_cause_find',
      'fix_suggest',
      'trend_analysis',
    ],
    tools: [
      {
        name: 'analyze_alert',
        description: 'Analyze an alert',
        inputSchema: {
          type: 'object',
          properties: {
            alert_id: { type: 'string' },
            include_history: { type: 'boolean', default: true },
          },
          required: ['alert_id'],
        },
      },
      {
        name: 'find_root_cause',
        description: 'Find root cause of an issue',
        inputSchema: {
          type: 'object',
          properties: {
            alert_id: { type: 'string' },
            context: { type: 'object' },
          },
          required: ['alert_id'],
        },
      },
    ],
    a2a_capabilities: {
      can_request_from: ['nexusops.chat'],
      can_delegate_to: ['nexusops.k8s', 'nexusops.deploy'],
    },
  },
  {
    agent_id: 'nexusops.git',
    name: 'Git Operations Agent',
    version: '1.0.0',
    description: 'Git 仓库操作、分支管理、PR 创建',
    category: 'automation',
    capabilities: [
      'git_branch_create',
      'git_pr_create',
      'git_commit_info',
      'git_compare',
    ],
    tools: [
      {
        name: 'create_branch',
        description: 'Create a Git branch',
        inputSchema: {
          type: 'object',
          properties: {
            repo: { type: 'string' },
            branch_name: { type: 'string' },
            base_branch: { type: 'string', default: 'main' },
          },
          required: ['repo', 'branch_name'],
        },
      },
      {
        name: 'create_pull_request',
        description: 'Create a pull request',
        inputSchema: {
          type: 'object',
          properties: {
            repo: { type: 'string' },
            title: { type: 'string' },
            body: { type: 'string' },
            head_branch: { type: 'string' },
            base_branch: { type: 'string', default: 'main' },
          },
          required: ['repo', 'title', 'head_branch'],
        },
      },
    ],
    a2a_capabilities: {
      can_request_from: ['nexusops.chat', 'nexusops.deploy'],
      can_delegate_to: [],
    },
  },
];

// ============================================
// 工具函数
// ============================================

/**
 * 获取内置 Agent
 */
export function getBuiltinAgent(agentId: string): AgentManifest | undefined {
  return BUILTIN_AGENTS.find(a => a.agent_id === agentId);
}

/**
 * 获取所有内置 Agent
 */
export function getAllBuiltinAgents(): AgentManifest[] {
  return BUILTIN_AGENTS;
}

/**
 * 检查 Agent 是否支持某能力
 */
export function hasCapability(manifest: AgentManifest, capability: string): boolean {
  return manifest.capabilities.includes(capability);
}

/**
 * 检查 Agent 是否可以调用另一个 Agent
 */
export function canDelegateTo(fromAgent: AgentManifest, toAgentId: string): boolean {
  const a2a = fromAgent.a2a_capabilities;
  if (!a2a?.can_delegate_to) return false;
  return a2a.can_delegate_to.includes(toAgentId) || a2a.can_delegate_to.includes('*');
}

/**
 * 生成请求 ID
 */
export function generateRequestId(): string {
  return `req-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * 生成会话 ID
 */
export function generateConversationId(): string {
  return `conv-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}
