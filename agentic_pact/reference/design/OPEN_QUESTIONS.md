# Agent 设计未明确问题分析

> 进度规则：该文档仅保留未解决问题。已做出决定的事项请记录为 `agentic_pact/adr/ADR-*.md` 并从此处移除。

## 🔴 关键问题（需立即明确）

### 1. Agent 执行环境

**问题**: Agent 在哪里执行？

| 选项 | 优点 | 缺点 | 需要明确 |
|------|------|------|----------|
| **A. 服务端执行** | 安全可控、可访问内网资源 | 需要后端基础设施 | ✅ 推荐 |
| B. 客户端执行 | 减轻服务端压力 | 安全风险、无法访问内网 | ❌ 不推荐 |
| C. 混合模式 | 灵活 | 复杂度高 | ⚠️ 可选 |

**需要明确**:
- [ ] Agent 是否需要沙箱隔离？
- [ ] Agent 的资源限制（CPU、内存、超时时间）？
- [ ] Agent 的执行日志如何存储和审计？

---

### 2. Agent 认证与授权

**问题**: 如何验证 Agent 身份和权限？

**当前设计中未明确**:
```
┌─────────────────────────────────────────────────────────────┐
│  Agent A ──────► Agent B                                    │
│                                                              │
│  ❓ A 如何证明自己是合法 Agent？                               │
│  ❓ B 如何验证 A 有权限调用自己？                               │
│  ❓ 用户授权如何传递？                                         │
└─────────────────────────────────────────────────────────────┘
```

**需要明确**:
- [ ] Agent 身份认证方式（API Key / mTLS / OAuth2？）
- [ ] Agent 间调用的信任链如何建立？
- [ ] 用户授权的粒度（按项目 / 按操作 / 按资源）？
- [ ] 敏感操作（如 DNS 配置）是否需要二次确认？

**建议方案**:
```yaml
# Agent 授权模型
auth_model:
  # 方式 1: 基于 Token
  token_based:
    issuer: "nexusops-agent-registry"
    validation: "RS256 JWT"

  # 方式 2: 基于 mTLS
  mtls:
    ca: "nexusops-ca"
    cert_rotation: "24h"

  # 方式 3: 基于 OAuth2
  oauth2:
    flow: "client_credentials"
    scope: "agent:invoke"
```

---

### 3. Agent 工具执行安全

**问题**: Agent 调用外部工具（如 Cloudflare API）时，凭证如何管理？

**未明确问题**:
- [ ] 敏感凭证（Cloudflare API Token）存储在哪里？
- [ ] 凭证如何安全传递给 Agent？
- [ ] 凭证的使用如何审计？

**建议方案**:
```yaml
# 凭证管理
credential_management:
  storage: "vault"  # HashiCorp Vault / AWS Secrets Manager
  injection: "env_at_runtime"  # 运行时注入
  audit: "all_access_logged"
  rotation: "auto_90_days"
```

---

### 4. Agent 状态管理

**问题**: 有状态的 Agent 如何管理状态？

**场景**:
- DNS Agent 创建了一个域名，需要记录这个状态
- 后续操作需要知道这个域名的存在

**未明确**:
- [ ] Agent 状态存储在哪里？
- [ ] 多次调用如何共享状态？
- [ ] 状态如何与 NexusOps 资源关联？

**建议方案**:
```typescript
// Agent 状态存储
interface AgentState {
  agent_id: string;
  conversation_id: string;
  state_type: 'provisioned_resources' | 'user_preferences' | 'workflow_context';
  data: {
    resource_type: string;
    resource_id: string;
    metadata: Record<string, any>;
  };
  created_at: string;
  expires_at?: string;  // 可选的过期时间
}

// 状态存储 API
POST /api/v1/agents/{agent_id}/state
GET /api/v1/agents/{agent_id}/state/{key}
DELETE /api/v1/agents/{agent_id}/state/{key}
```

---

## 🟡 重要问题（需尽快明确）

### 5. Agent 版本兼容性

**问题**: 不同版本的 Agent 如何共存？

**场景**:
- 用户安装了 `dns-agent@1.0.0`
- 后来升级到 `dns-agent@2.0.0`
- 2.0.0 的接口可能与 1.0.0 不兼容

**需要明确**:
- [ ] Agent 的语义化版本规范
- [ ] 大版本不兼容时的迁移策略
- [ ] 是否支持多版本共存？

---

### 6. Agent 错误处理

**问题**: Agent 调用失败时如何处理？

**未明确的错误场景**:
| 场景 | 当前处理 | 需要明确 |
|------|----------|----------|
| Agent 超时 | ❌ 未定义 | 超时时间？重试策略？ |
| Agent 崩溃 | ❌ 未定义 | 如何恢复？ |
| Agent 返回无效 JSON | ✅ 有重试机制 | 重试几次？降级策略？ |
| 外部 API 失败 | ❌ 未定义 | 如何通知用户？ |

**建议方案**:
```yaml
# 错误处理策略
error_handling:
  timeout: 30s
  retry:
    max_attempts: 3
    backoff: "exponential"
    base_delay: 1s
  fallback:
    enabled: true
    action: "return_partial_result"  # 或 "raise_error"
  notification:
    channels: ["ui", "email", "slack"]
    severity_levels: ["warning", "error", "critical"]
```

---

### 7. Agent 并发控制

**问题**: 多个 Agent 同时操作同一资源时如何处理？

**场景**:
```
Agent A: 配置 DNS 域名 test.example.com
Agent B: 同时配置同一域名
```

**需要明确**:
- [ ] 是否需要分布式锁？
- [ ] 冲突解决策略（最后写入胜出 / 报错 / 合并）？
- [ ] 是否支持乐观锁（基于版本号）？

---

### 8. Agent 成本与计费

**问题**: Agent 的资源消耗如何计量和计费？

**需要明确**:
- [ ] Agent 调用次数如何计量？
- [ ] LLM Token 消耗如何追踪？
- [ ] 第三方 API 调用费用谁承担？

---

## 🟢 次要问题（可后续明确）

### 9. Agent 调试与开发体验

**未明确**:
- [ ] 如何本地开发和测试 Agent？
- [ ] 如何模拟 Agent 间调用？
- [ ] 日志和追踪如何集成？

---

### 10. Agent 更新机制

**未明确**:
- [ ] Agent 如何更新？
- [ ] 更新时是否中断服务？
- [ ] 如何回滚到旧版本？

---

## 📋 决策记录模板

对于每个未明确问题，建议使用以下模板记录决策：

```markdown
## ADR-XXX: [问题标题]

### 背景
[为什么需要做这个决策]

### 选项
1. 选项 A: [描述] - 优点 / 缺点
2. 选项 B: [描述] - 优点 / 缺点
3. 选项 C: [描述] - 优点 / 缺点

### 决策
[选择的选项]

### 理由
[为什么选择这个选项]

### 后果
[选择带来的影响]
```

---

## 🎯 建议优先级

| 优先级 | 问题 | 建议 |
|--------|------|------|
| **P0** | Agent 执行环境 | 立即明确，采用服务端执行 |
| **P0** | 认证与授权 | 立即明确，采用 JWT + RBAC |
| **P0** | 凭证管理 | 立即明确，采用 Vault 方案 |
| **P1** | 状态管理 | Phase 3.5 明确 |
| **P1** | 错误处理 | Phase 3.5 明确 |
| **P2** | 版本兼容性 | Phase 4 明确 |
| **P2** | 并发控制 | Phase 4 明确 |
| **P3** | 成本计费 | Phase 5 明确 |
| **P3** | 调试开发 | Phase 5 明确 |
