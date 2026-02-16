# ADR-003: Agent 凭证管理

## 状态
已接受 (2024-02-16)

## 背景

Agent 在执行过程中需要访问外部服务的凭证，例如：
- Cloudflare API Token
- Kubernetes Service Account
- AWS/GCP 凭证
- 数据库连接字符串

这些凭证需要：
- 安全存储
- 按需注入
- 审计访问
- 定期轮换

## 选项

### 选项 A: HashiCorp Vault（推荐）
- 专业的密钥管理系统
- 支持动态凭证
- 完善的审计功能

**优点**：
- 企业级安全
- 动态凭证生成
- 详细的审计日志
- 支持凭证轮换

**缺点**：
- 需要额外的基础设施
- 运维复杂度

### 选项 B: Kubernetes Secrets
- K8s 原生密钥管理

**优点**：
- 无需额外组件
- 与 K8s 集成

**缺点**：
- 安全性较弱（默认不加密）
- 审计功能有限
- 不支持动态凭证

### 选项 C: 加密数据库
- 将加密后的凭证存储在数据库中

**优点**：
- 简单
- 无需额外组件

**缺点**：
- 密钥管理复杂
- 审计功能弱
- 不支持动态凭证

## 决策

**采用选项 A：HashiCorp Vault**，在 Phase 3.5 之前可使用 **Kubernetes Secrets 作为过渡方案**

## 详细设计

### 1. 凭证分类

```typescript
// 凭证类型
type CredentialType =
  | 'api_token'        // API Token (如 Cloudflare)
  | 'service_account'  // 服务账号 (如 K8s SA)
  | 'database'         // 数据库凭证
  | 'cloud_provider'   // 云服务商凭证
  | 'ssh_key'          // SSH 密钥
  | 'certificate';     // TLS 证书

// 凭证元数据
interface CredentialMetadata {
  id: string;
  name: string;
  type: CredentialType;
  description: string;

  // 所属
  owner_type: 'system' | 'project' | 'agent';
  owner_id: string;

  // 权限
  allowed_agents: string[];  // 哪些 Agent 可以使用
  allowed_operations: string[];  // 允许的操作

  // 生命周期
  created_at: string;
  expires_at?: string;
  last_used_at?: string;
  rotation_policy?: string;
}
```

### 2. 存储架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Vault 存储结构                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  secret/data/nexusops/                                                       │
│  ├── system/                    # 系统级凭证                                  │
│  │   ├── cloudflare             # Cloudflare API Token                       │
│  │   ├── kubernetes              # K8s Service Account                       │
│  │   └── argocd                  # ArgoCD API Token                          │
│  │                                                                           │
│  ├── projects/                  # 项目级凭证                                  │
│  │   ├── proj-001/                                                           │
│  │   │   ├── database           # 数据库连接                                  │
│  │   │   └── redis              # Redis 连接                                 │
│  │   └── proj-002/                                                           │
│  │       └── ...                                                             │
│  │                                                                           │
│  └── agents/                   # Agent 专用凭证                               │
│      ├── dns-agent/                                                          │
│      │   └── cloudflare         # DNS Agent 的 CF Token                      │
│      ├── k8s-agent/                                                          │
│      │   └── kubernetes         # K8s Agent 的 SA                            │
│      └── ...                                                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3. 凭证注入流程

```typescript
// 凭证注入配置
interface CredentialInjection {
  // 注入方式
  method: 'environment' | 'file' | 'volume';

  // 注入时机
  timing: 'container_start' | 'on_demand';

  // 凭证映射
  mappings: {
    // 环境变量名 -> Vault 路径
    [envVar: string]: {
      vault_path: string;
      vault_key: string;
    };
  };
}

// 示例：DNS Agent 的凭证注入
const DNS_AGENT_INJECTION: CredentialInjection = {
  method: 'environment',
  timing: 'container_start',
  mappings: {
    'CLOUDFLARE_API_TOKEN': {
      vault_path: 'secret/data/nexusops/agents/dns-agent/cloudflare',
      vault_key: 'api_token',
    },
    'CLOUDFLARE_ZONE_ID': {
      vault_path: 'secret/data/nexusops/agents/dns-agent/cloudflare',
      vault_key: 'zone_id',
    },
  },
};

// 凭证注入实现
async function injectCredentials(
  agentId: string,
  container: DockerContainer
): Promise<void> {
  // 1. 获取 Agent 的凭证配置
  const injection = await getCredentialInjection(agentId);

  // 2. 从 Vault 获取凭证
  const credentials: Record<string, string> = {};
  for (const [envVar, vaultConfig] of Object.entries(injection.mappings)) {
    const secret = await vaultClient.read(vaultConfig.vault_path);
    credentials[envVar] = secret.data.data[vaultConfig.vault_key];
  }

  // 3. 注入到容器
  if (injection.method === 'environment') {
    // 作为环境变量注入
    for (const [envVar, value] of Object.entries(credentials)) {
      container.addEnv(envVar, value);
    }
  } else if (injection.method === 'file') {
    // 作为文件注入
    const credentialFile = formatCredentialsFile(credentials);
    container.addVolume('/credentials', credentialFile);
  }
}
```

### 4. 访问审计

```typescript
// 审计日志
interface CredentialAccessLog {
  id: string;
  timestamp: string;

  // 访问者
  accessor: {
    type: 'agent' | 'user' | 'system';
    id: string;
    name: string;
  };

  // 凭证信息
  credential: {
    id: string;
    name: string;
    type: CredentialType;
  };

  // 访问详情
  access: {
    action: 'read' | 'write' | 'delete';
    granted: boolean;
    reason?: string;  // 如果拒绝，说明原因
  };

  // 上下文
  context: {
    request_id: string;
    conversation_id?: string;
    ip_address?: string;
    user_agent?: string;
  };
}

// 审计查询
async function queryCredentialAuditLogs(params: {
  credential_id?: string;
  accessor_id?: string;
  action?: 'read' | 'write' | 'delete';
  start_time?: Date;
  end_time?: Date;
}): Promise<CredentialAccessLog[]> {
  // 实现审计日志查询
}
```

### 5. 凭证轮换

```typescript
// 轮换策略
interface RotationPolicy {
  id: string;
  name: string;

  // 轮换周期
  rotation_period: number;  // 天

  // 轮换触发条件
  triggers: {
    on_compromise: boolean;      // 泄露时触发
    on_expiration: boolean;      // 过期时触发
    on_schedule: boolean;        // 定时触发
  };

  // 轮换操作
  actions: {
    generate_new: boolean;       // 生成新凭证
    revoke_old: boolean;         // 撤销旧凭证
    notify_owners: boolean;      // 通知所有者
    update_services: string[];   // 自动更新的服务
  };
}

// 轮换流程
async function rotateCredential(credentialId: string): Promise<void> {
  // 1. 获取凭证信息
  const credential = await getCredential(credentialId);
  const policy = credential.rotation_policy;

  // 2. 生成新凭证
  if (policy.actions.generate_new) {
    const newCredential = await generateNewCredential(credential.type);
    await storeNewCredential(credentialId, newCredential);
  }

  // 3. 撤销旧凭证
  if (policy.actions.revoke_old) {
    await revokeOldCredential(credential);
  }

  // 4. 通知所有者
  if (policy.actions.notify_owners) {
    await notifyCredentialOwners(credential, 'rotated');
  }

  // 5. 更新服务
  for (const service of policy.actions.update_services) {
    await updateServiceCredential(service, credentialId);
  }

  // 6. 记录审计日志
  await logCredentialRotation(credentialId);
}
```

### 6. 过渡方案：Kubernetes Secrets

```yaml
# Phase 3.5 之前的过渡方案
apiVersion: v1
kind: Secret
metadata:
  name: nexusops-agent-credentials
  namespace: nexusops
type: Opaque
data:
  # Base64 编码的凭证
  cloudflare-api-token: <base64-encoded-token>
  cloudflare-zone-id: <base64-encoded-zone-id>

---
# Agent Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dns-agent
  namespace: nexusops
spec:
  template:
    spec:
      containers:
        - name: agent
          env:
            - name: CLOUDFLARE_API_TOKEN
              valueFrom:
                secretKeyRef:
                  name: nexusops-agent-credentials
                  key: cloudflare-api-token
            - name: CLOUDFLARE_ZONE_ID
              valueFrom:
                secretKeyRef:
                  name: nexusops-agent-credentials
                  key: cloudflare-zone-id
```

## 后果

### 正面
- 企业级安全
- 详细的审计追踪
- 自动凭证轮换

### 负面
- 需要维护 Vault 基础设施
- 增加系统复杂度

### 风险
- Vault 不可用导致 Agent 无法工作（通过缓存缓解）

## 实现

1. **Phase 3.5**: 使用 Kubernetes Secrets 作为过渡
2. **Phase 4**: 部署 HashiCorp Vault
3. **Phase 4**: 迁移凭证到 Vault
4. **Phase 5**: 实现自动轮换
