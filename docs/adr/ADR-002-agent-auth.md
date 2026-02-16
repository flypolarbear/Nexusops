# ADR-002: Agent 认证与授权

## 状态
已接受 (2024-02-16)

## 背景

Agent 需要一个安全的认证和授权机制：
- 验证 Agent 身份
- 控制 Agent 间调用的权限
- 传递用户授权上下文
- 支持敏感操作的二次确认

## 选项

### 选项 A: JWT + RBAC（推荐）
- 使用 RS256 签名的 JWT 作为 Agent 身份凭证
- 使用 RBAC 模型控制权限
- 支持细粒度的权限控制

**优点**：
- 无状态，易扩展
- 标准化，生态完善
- 支持细粒度权限

**缺点**：
- Token 撤销复杂（需要黑名单）

### 选项 B: mTLS
- 双向 TLS 认证
- 基于证书的身份验证

**优点**：
- 安全性高
- 无需管理 Token

**缺点**：
- 证书管理复杂
- 不适合细粒度授权

### 选项 C: API Key
- 简单的 API Key 认证

**优点**：
- 简单易用

**缺点**：
- 安全性较低
- 不支持细粒度授权

## 决策

**采用选项 A：JWT + RBAC**

## 详细设计

### 1. Agent 身份模型

```typescript
// Agent 身份
interface AgentIdentity {
  agent_id: string;          // 唯一标识，如 com.nexusops.agents.dns
  agent_name: string;
  agent_version: string;
  agent_type: 'builtin' | 'third_party';
  provider: string;          // 提供者

  // 能力声明
  capabilities: string[];    // ['dns:read', 'dns:write', 'cloudflare:configure']

  // 元数据
  metadata: {
    created_at: string;
    updated_at: string;
    status: 'active' | 'inactive' | 'suspended';
  };
}

// Agent JWT Claims
interface AgentJWTClaims {
  // 标准 Claims
  iss: 'nexusops-agent-registry';
  sub: string;              // Agent ID
  aud: 'nexusops-agents';
  exp: number;
  iat: number;
  jti: string;              // JWT ID

  // 自定义 Claims
  agent_id: string;
  agent_type: 'builtin' | 'third_party';
  capabilities: string[];
  permissions: string[];
}
```

### 2. 权限模型

```typescript
// 权限定义
type Permission =
  // DNS 相关
  | 'dns:read'
  | 'dns:write'
  | 'dns:delete'

  // K8s 相关
  | 'k8s:read'
  | 'k8s:deploy'
  | 'k8s:scale'
  | 'k8s:delete'

  // 部署相关
  | 'deploy:create'
  | 'deploy:rollback'
  | 'deploy:force_sync'

  // 系统相关
  | 'system:read'
  | 'system:admin';

// 角色定义
interface Role {
  name: string;
  permissions: Permission[];
}

// 预定义角色
const BUILTIN_ROLES: Role[] = [
  {
    name: 'agent.reader',
    permissions: [
      'dns:read',
      'k8s:read',
      'deploy:create',  // 只能创建，不能删除
      'system:read',
    ],
  },
  {
    name: 'agent.operator',
    permissions: [
      'dns:read',
      'dns:write',
      'k8s:read',
      'k8s:deploy',
      'k8s:scale',
      'deploy:create',
      'deploy:rollback',
      'deploy:force_sync',
      'system:read',
    ],
  },
  {
    name: 'agent.admin',
    permissions: [
      'dns:read',
      'dns:write',
      'dns:delete',
      'k8s:read',
      'k8s:deploy',
      'k8s:scale',
      'k8s:delete',
      'deploy:create',
      'deploy:rollback',
      'deploy:force_sync',
      'system:read',
      'system:admin',
    ],
  },
];
```

### 3. Agent 间调用授权

```typescript
// Agent 间调用请求
interface AgentToAgentRequest {
  // 调用方身份
  caller: {
    agent_id: string;
    jwt: string;            // 调用方的 JWT
  };

  // 被调用方
  callee: {
    agent_id: string;
  };

  // 调用内容
  request: {
    action: string;         // 如 'create_dns_record'
    params: Record<string, any>;
  };

  // 用户上下文（传递用户授权）
  user_context?: {
    user_id: string;
    session_id: string;
    permissions: Permission[];  // 用户授予的权限
  };
}

// 授权检查流程
async function authorizeAgentCall(request: AgentToAgentRequest): Promise<boolean> {
  // 1. 验证调用方 JWT
  const callerClaims = await verifyJWT(request.caller.jwt);
  if (!callerClaims) return false;

  // 2. 检查调用方是否有权调用此 Agent
  const calleeAgent = await getAgent(request.callee.agent_id);
  const canCall = calleeAgent.allowed_callers.includes(callerClaims.agent_id);
  if (!canCall) return false;

  // 3. 检查操作权限
  const requiredPermission = getRequiredPermission(request.request.action);
  const hasPermission = callerClaims.permissions.includes(requiredPermission);
  if (!hasPermission) return false;

  // 4. 检查用户授权（如果涉及用户资源）
  if (request.user_context) {
    const userHasPermission = request.user_context.permissions.includes(requiredPermission);
    if (!userHasPermission) return false;
  }

  return true;
}
```

### 4. 敏感操作二次确认

```typescript
// 需要二次确认的操作
const SENSITIVE_OPERATIONS = {
  'dns:delete': {
    confirm_message: '确定要删除此 DNS 记录吗？',
    timeout: 60,  // 确认有效期（秒）
  },
  'k8s:delete': {
    confirm_message: '确定要删除此 K8s 资源吗？此操作不可撤销。',
    timeout: 60,
  },
  'deploy:rollback': {
    confirm_message: '确定要回滚到此版本吗？',
    timeout: 120,
  },
  'cloudflare:configure': {
    confirm_message: '即将修改 Cloudflare 配置，是否继续？',
    timeout: 60,
  },
};

// 敏感操作确认 Token
interface Confirmation {
  confirmation_id: string;
  operation: string;
  params: Record<string, any>;
  user_id: string;
  expires_at: string;
  used: boolean;
}

// 确认流程
async function handleSensitiveOperation(
  operation: string,
  params: Record<string, any>,
  userId: string
): Promise<{ needs_confirmation: boolean; confirmation_id?: string }> {
  const sensitiveOp = SENSITIVE_OPERATIONS[operation];
  if (!sensitiveOp) {
    // 非敏感操作，直接执行
    return { needs_confirmation: false };
  }

  // 生成确认 Token
  const confirmation: Confirmation = {
    confirmation_id: generateUUID(),
    operation,
    params,
    user_id: userId,
    expires_at: new Date(Date.now() + sensitiveOp.timeout * 1000).toISOString(),
    used: false,
  };

  await storeConfirmation(confirmation);

  return {
    needs_confirmation: true,
    confirmation_id: confirmation.confirmation_id,
  };
}
```

### 5. Token 生命周期

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Token 生命周期                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. 注册阶段                                                                  │
│  ┌─────────┐    ┌─────────────┐    ┌─────────────┐                          │
│  │ Agent   │───▶│ Registry    │───▶│ 颁发初始 JWT │                          │
│  │ 注册    │    │ 验证身份     │    │ (有效期 24h) │                          │
│  └─────────┘    └─────────────┘    └─────────────┘                          │
│                                                                              │
│  2. 运行阶段                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                      │
│  │ 使用 JWT    │───▶│ Token 即将  │───▶│ 自动刷新    │                      │
│  │ 调用其他    │    │ 过期 (1h内) │    │ 新 JWT      │                      │
│  │ Agent      │    └─────────────┘    └─────────────┘                      │
│  └─────────────┘                                                           │
│                                                                              │
│  3. 撤销阶段                                                                  │
│  ┌─────────────┐    ┌─────────────┐                                         │
│  │ Agent 被禁用│───▶│ JWT 加入    │                                         │
│  │ 或删除      │    │ 黑名单      │                                         │
│  └─────────────┘    └─────────────┘                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 后果

### 正面
- 标准化、安全的认证机制
- 支持细粒度权限控制
- 敏感操作有保护

### 负面
- JWT 黑名单管理复杂度
- 需要维护权限配置

## 实现

1. **Phase 3.5**: 实现 JWT 颁发和验证
2. **Phase 3.5**: 实现 RBAC 权限检查
3. **Phase 4**: 实现敏感操作二次确认
4. **Phase 4**: 实现 JWT 黑名单
