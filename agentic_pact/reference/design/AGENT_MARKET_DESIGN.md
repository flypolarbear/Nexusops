# NexusOps Agent Market 架构设计

## 概述

NexusOps 将支持开放式 Agent 市场，允许第三方开发者创建和接入自定义 AI Agent，为 Kubernetes 和 CI/CD 提供统一的 AI 扩展能力。

## Agent 接口规范

### 1. Agent 能力声明 (Agent Manifest)

```json
{
  "agent_id": "com.nexusops.agents.k8sgpt",
  "name": "K8sGPT Diagnostic Agent",
  "version": "1.0.0",
  "description": "Kubernetes 资源诊断和修复建议",
  "author": "NexusOps Team",
  "category": "diagnostics",
  "capabilities": [
    "resource_analysis",
    "error_diagnosis",
    "fix_suggestion",
    "version_linking"
  ],
  "input_schema": {
    "type": "object",
    "properties": {
      "resource_type": { "type": "string", "enum": ["pod", "deployment", "service", "namespace"] },
      "resource_name": { "type": "string" },
      "namespace": { "type": "string" },
      "context": { "type": "object" }
    },
    "required": ["resource_type", "resource_name"]
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "status": { "type": "string", "enum": ["healthy", "warning", "critical"] },
      "insights": { "type": "array", "items": { "$ref": "#/definitions/Insight" } },
      "actions": { "type": "array", "items": { "$ref": "#/definitions/Action" } },
      "related_version": { "type": "string" }
    }
  },
  "tools": [
    {
      "name": "get_pod_logs",
      "description": "Get logs from a specific pod",
      "parameters": { "type": "object", "properties": { "pod_name": { "type": "string" } } }
    },
    {
      "name": "describe_resource",
      "description": "Get detailed resource information",
      "parameters": { "type": "object", "properties": { "resource": { "type": "string" } } }
    }
  ],
  "examples": [
    {
      "input": { "resource_type": "pod", "resource_name": "api-gateway-7d8f9", "namespace": "production" },
      "output": {
        "status": "warning",
        "insights": [
          {
            "severity": "warning",
            "message": "Memory usage at 90% of limit",
            "resource": "api-gateway-7d8f9",
            "recommendation": "Consider increasing memory limit"
          }
        ],
        "actions": [
          { "type": "scale", "params": { "replicas": 3 }, "label": "Scale deployment" }
        ],
        "related_version": "Phoenix"
      }
    }
  ],
  "endpoints": {
    "analyze": "/api/v1/agents/k8sgpt/analyze",
    "stream": "/api/v1/agents/k8sgpt/stream"
  },
  "auth": {
    "type": "bearer",
    "header": "X-Agent-Token"
  }
}
```

### 2. 统一请求格式

```typescript
interface AgentRequest {
  // 请求 ID，用于追踪
  request_id: string;

  // 会话 ID，支持多轮对话
  conversation_id: string;

  // Agent ID
  agent_id: string;

  // 用户查询
  query: string;

  // 上下文信息
  context: {
    project_id?: string;
    version_id?: string;
    region?: string;
    resource_type?: string;
    resource_name?: string;
    [key: string]: any;
  };

  // 输出控制
  output_config?: {
    format: 'json' | 'markdown' | 'stream';
    schema?: string;  // JSON Schema URI
    max_tokens?: number;
  };

  // Function Calling 配置
  tools?: AgentTool[];
  tool_choice?: 'auto' | 'required' | 'none';
}

interface AgentTool {
  name: string;
  description: string;
  parameters: JSONSchema;
}

interface AgentResponse {
  // 请求 ID（与请求匹配）
  request_id: string;

  // 响应状态
  status: 'success' | 'error' | 'partial';

  // 主要内容
  content: {
    text: string;
    format: 'markdown' | 'json';
    data?: any;  // 当 format 为 json 时
  };

  // 结构化输出（符合 output_schema）
  structured_output?: any;

  // 建议的操作
  suggested_actions?: AgentAction[];

  // 工具调用结果（Function Calling）
  tool_calls?: ToolCallResult[];

  // 关联的资源
  related_resources?: {
    type: 'version' | 'deployment' | 'alert' | 'resource';
    id: string;
    link: string;
  }[];

  // 元数据
  metadata?: {
    model?: string;
    latency_ms?: number;
    tokens_used?: number;
    [key: string]: any;
  };

  // 错误信息
  error?: {
    code: string;
    message: string;
    retry_after?: number;
  };
}
```

### 3. JSON 输出保证策略

```typescript
// Agent 输出配置
interface AgentOutputConfig {
  // 方式 1: JSON Schema + Few-shot
  json_schema: {
    schema: object;
    strict: boolean;  // 严格模式
    examples: Array<{ input: any; output: any }>;
  };

  // 方式 2: Function Calling
  function_calling: {
    enabled: boolean;
    provider: 'openai' | 'anthropic' | 'azure';
    parallel_calls: boolean;
  };

  // 方式 3: 状态机约束 (outlines/guidance)
  state_machine: {
    enabled: boolean;
    library: 'outlines' | 'guidance' | 'lm-format-enforcer';
    regex?: string;  // 正则约束
  };

  // 方式 4: JSON 修复
  repair: {
    enabled: boolean;
    library: 'json-repair' | 'instructor';
    retry_count: number;
    retry_on_invalid: boolean;
  };
}

// 推荐使用 Instructor 库的示例
import Instructor from 'instructor-xxx';

const agent = new Instructor({
  mode: 'tools',  // 或 'json'
  schema: AgentOutputSchema,
  max_retries: 3,
  validation: true
});
```

## 架构设计

### 1. Agent Registry (Agent 注册中心)

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Registry                            │
├─────────────────────────────────────────────────────────────┤
│  - Agent 注册/注销                                           │
│  - 能力发现                                                  │
│  - 版本管理                                                  │
│  - 健康检查                                                  │
│  - 权限控制                                                  │
└─────────────────────────────────────────────────────────────┘
```

### 2. Agent Gateway (Agent 网关)

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Gateway                             │
├─────────────────────────────────────────────────────────────┤
│  - 请求路由                                                  │
│  - 负载均衡                                                  │
│  - 认证/授权                                                 │
│  - 限流控制                                                  │
│  - 日志/监控                                                 │
│  - 响应格式标准化                                            │
│  - JSON Schema 验证                                          │
│  - 错误处理 & 重试                                           │
└─────────────────────────────────────────────────────────────┘
```

### 3. 内置 Agent 类型

| Agent ID | 类型 | 功能 |
|----------|------|------|
| `nexusops.deploy` | 部署 | 部署流程分析、状态追踪 |
| `nexusops.k8sgpt` | 诊断 | K8s 资源诊断、修复建议 |
| `nexusops.alert` | 告警 | 告警分析、根因定位 |
| `nexusops.cicd` | CI/CD | 构建分析、流水线优化 |
| `nexusops.chat` | 通用 | 通用问答、快捷命令 |

## 前端架构调整

### 1. Agent 消息类型扩展

```typescript
// src/types/agent.ts

export type AgentType =
  | 'nexusops.chat'      // 通用聊天
  | 'nexusops.deploy'    // 部署分析
  | 'nexusops.k8sgpt'    // K8s 诊断
  | 'nexusops.alert'     // 告警分析
  | 'custom';            // 自定义 Agent

export interface AgentMessage extends Message {
  agent_id: AgentType;
  agent_name: string;

  // 结构化输出
  structured_output?: {
    type: 'deployment_status' | 'resource_analysis' | 'alert_summary' | 'version_comparison';
    data: any;
  };

  // 建议操作
  suggested_actions?: AgentAction[];

  // 关联资源
  related_resources?: RelatedResource[];
}

export interface AgentAction {
  id: string;
  type: 'deploy' | 'rollback' | 'scale' | 'fix' | 'navigate' | 'query';
  label: string;
  params: Record<string, any>;
  confirm_required?: boolean;
  danger?: boolean;
}

export interface RelatedResource {
  type: 'version' | 'deployment' | 'pod' | 'alert' | 'region';
  id: string;
  name: string;
  link?: string;
}
```

### 2. Agent 上下文提供

```typescript
// src/stores/agentContextStore.ts

import { create } from 'zustand';

interface AgentContext {
  // 当前上下文
  current_project_id: string | null;
  current_version_id: string | null;
  current_region: string | null;
  current_resource: { type: string; name: string; namespace: string } | null;

  // 上下文更新
  setProject: (id: string) => void;
  setVersion: (id: string) => void;
  setRegion: (id: string) => void;
  setResource: (resource: { type: string; name: string; namespace: string }) => void;

  // 获取完整上下文
  getFullContext: () => AgentRequestContext;
}

export const useAgentContextStore = create<AgentContext>((set, get) => ({
  current_project_id: null,
  current_version_id: null,
  current_region: null,
  current_resource: null,

  setProject: (id) => set({ current_project_id: id }),
  setVersion: (id) => set({ current_version_id: id }),
  setRegion: (id) => set({ current_region: id }),
  setResource: (resource) => set({ current_resource: resource }),

  getFullContext: () => ({
    project_id: get().current_project_id,
    version_id: get().current_version_id,
    region: get().current_region,
    resource: get().current_resource,
  }),
}));
```

### 3. Agent 响应渲染器

```tsx
// src/components/AgentResponseRenderer.tsx

import { AgentMessage, AgentAction, RelatedResource } from '../types/agent';

interface Props {
  message: AgentMessage;
  onActionClick?: (action: AgentAction) => void;
  onResourceClick?: (resource: RelatedResource) => void;
}

export function AgentResponseRenderer({ message, onActionClick, onResourceClick }: Props) {
  return (
    <div className="agent-response">
      {/* Markdown 内容 */}
      <div className="prose">
        <ReactMarkdown>{message.content}</ReactMarkdown>
      </div>

      {/* 结构化输出（按类型渲染） */}
      {message.structured_output && (
        <StructuredOutputRenderer output={message.structured_output} />
      )}

      {/* 建议操作 */}
      {message.suggested_actions && message.suggested_actions.length > 0 && (
        <div className="suggested-actions">
          {message.suggested_actions.map(action => (
            <Button
              key={action.id}
              type={action.danger ? 'primary' : 'default'}
              danger={action.danger}
              onClick={() => onActionClick?.(action)}
            >
              {action.label}
            </Button>
          ))}
        </div>
      )}

      {/* 关联资源 */}
      {message.related_resources && message.related_resources.length > 0 && (
        <div className="related-resources">
          <Text type="secondary">Related:</Text>
          {message.related_resources.map(resource => (
            <Tag
              key={resource.id}
              clickable
              onClick={() => onResourceClick?.(resource)}
            >
              {resource.name}
            </Tag>
          ))}
        </div>
      )}

      {/* Agent 标识 */}
      <div className="agent-info">
        <Tag color="purple">{message.agent_name}</Tag>
      </div>
    </div>
  );
}
```

## 扩展点预留

### 1. 现有功能改造为 Agent

| 现有功能 | 改造为 Agent | 优先级 |
|----------|--------------|--------|
| AI Assistant | `nexusops.chat` | P0 |
| K8sGPT 诊断 | `nexusops.k8sgpt` | P0 |
| 部署链分析 | `nexusops.deploy` | P1 |
| 告警分析 | `nexusops.alert` | P2 |

### 2. 接口预留

```typescript
// 后端 API 路由预留
// /api/v1/agents
// /api/v1/agents/:agent_id/invoke
// /api/v1/agents/:agent_id/stream
// /api/v1/agents/:agent_id/tools
// /api/v1/agent-registry
```

### 3. 数据库表设计预留

```sql
-- Agent 注册表
CREATE TABLE agents (
  id VARCHAR(255) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  version VARCHAR(50) NOT NULL,
  manifest JSONB NOT NULL,
  status VARCHAR(20) DEFAULT 'active',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Agent 调用日志
CREATE TABLE agent_invocations (
  id UUID PRIMARY KEY,
  agent_id VARCHAR(255) REFERENCES agents(id),
  request_id VARCHAR(255),
  conversation_id VARCHAR(255),
  request JSONB,
  response JSONB,
  status VARCHAR(20),
  latency_ms INTEGER,
  tokens_used INTEGER,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Agent 工具权限
CREATE TABLE agent_tool_permissions (
  id UUID PRIMARY KEY,
  agent_id VARCHAR(255) REFERENCES agents(id),
  tool_name VARCHAR(255),
  permission_level VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW()
);
```

## 开发路线图

### Phase 3.5: Agent 基础架构（新增）

1. **Agent 类型定义**
   - 定义 AgentMessage, AgentAction 等类型
   - 创建 AgentContextStore
   - 预留 Agent 相关接口

2. **Agent 响应渲染器**
   - 创建 AgentResponseRenderer 组件
   - 支持结构化输出渲染
   - 支持操作按钮和资源链接

3. **现有功能 Agent 化**
   - 重构 AIAssistantDrawer 支持多 Agent
   - 重构 K8sGPT 分析为独立 Agent
   - 添加 Agent 选择器

### Phase 5: Agent Market (未来)

1. Agent 注册中心
2. Agent 网关
3. Agent Store UI
4. 第三方 Agent 接入文档
5. Agent 开发 SDK（多语言）

## 技术选型建议

### JSON 输出保证

1. **首选方案**: Instructor
   - 支持 `mode='tools'` 和 `mode='json'`
   - 自动重试机制
   - Pydantic 模型验证
   - 多 LLM 提供商支持

2. **备选方案**:
   - outlines (状态机)
   - guidance (微软)
   - json-repair (轻量级修复)

### 多语言 SDK

```
/agent-sdks
├── python/          # NexusOps Agent SDK for Python
├── nodejs/          # NexusOps Agent SDK for Node.js
├── go/              # NexusOps Agent SDK for Go
└── java/            # NexusOps Agent SDK for Java
```

## 总结

当前 Phase 2 已完成，建议：

1. **Phase 3 (后端集成)** 时预留 Agent 相关接口
2. **Phase 3.5 (新增)** 实现 Agent 基础架构
3. **Phase 4 (优化)** 时支持 Agent 流式响应
4. **Phase 5 (未来)** 实现 Agent Market 完整功能
