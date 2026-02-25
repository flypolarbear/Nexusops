# NexusOps PRD 与架构方向研究报告

**研究员**: Elon (PM Agent)
**日期**: 2026-02-25
**版本**: 1.0

---

## 1. 项目定位分析

### 1.1 项目目标

**NexusOps** 是一个 **AI Native 运维与研发协作平台**，核心理念是将 DevOps/SRE 与自助研发流程中的高频、重复、易错操作，沉淀为可调用的 **Agent 能力**，并通过统一 **Gateway** 对内置与第三方 Agent 提供一致接入。

**核心价值主张**:
- 降低运维门槛：让研发同学可以自助完成部署、日志查询、CI/CD 操作
- 统一能力接入：通过 Agent Gateway 统一管理各类运维能力
- 生态扩展：支持第三方 Agent 接入，构建开放生态

### 1.2 目录结构分析

```
NexusOps/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── agents/            # 内置 Agent 实现 (chat, k8s, deploy, dns)
│   │   ├── api/               # API 路由层
│   │   │   ├── agents.py      # Agent 调用 API
│   │   │   ├── agent_market.py # Agent Market API
│   │   │   ├── projects.py    # 项目管理
│   │   │   ├── deployments.py # 部署管理
│   │   │   └── websocket.py   # WebSocket 通信
│   │   ├── gateway/           # Agent Gateway 核心层
│   │   │   ├── contract.py    # 调用契约
│   │   │   ├── errors.py      # 错误模型
│   │   │   ├── executor/      # 执行器适配层
│   │   │   ├── trace.py       # 链路追踪
│   │   │   └── validator.py   # 输入校验
│   │   ├── models/            # 数据模型
│   │   ├── services/          # 业务服务
│   │   └── stores/            # 内存存储
├── frontend/                   # React 前端
│   └── src/
│       ├── pages/             # 页面组件
│       │   ├── Dashboard.tsx
│       │   ├── Projects.tsx
│       │   ├── Deployments.tsx
│       │   ├── AgentStore.tsx
│       │   └── ...
│       ├── components/        # 通用组件
│       ├── services/          # API 服务
│       └── stores/            # Zustand 状态管理
├── docker/                     # Docker 配置
├── agentic_pact/              # 多 Agent 协作规范
│   ├── specs/                 # 需求规格
│   ├── adr/                   # 架构决策记录
│   └── state/                 # 状态文件
└── scripts/                   # 工具脚本
```

### 1.3 核心功能模块识别

| 模块 | 描述 | 状态 |
|------|------|------|
| **Dashboard** | 基础设施总览、世界地图、统计卡片 | 已实现 |
| **Projects** | 项目管理、版本管理 | 已实现 |
| **Deployments** | 部署管理、ArgoCD 集成 | 已实现 |
| **Agent Store** | Agent 市场、安装/启停管理 | 已实现 |
| **AI Assistant** | Agent 对话交互界面 | 已实现 |
| **Resources (K8sGPT)** | Kubernetes 资源管理 | 已实现 |
| **Logs** | 日志查询 | 已实现 |
| **Settings** | 系统配置 | 已实现 |

---

## 2. 技术架构评估

### 2.1 后端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| **FastAPI** | >=0.109.0 | Web 框架 |
| **SQLAlchemy** | >=2.0.0 | ORM (async) |
| **Pydantic** | >=2.5.0 | 数据校验 |
| **asyncpg** | >=0.29.0 | PostgreSQL 异步驱动 |
| **Redis** | >=5.0.0 | 缓存 |
| **python-jose** | >=3.3.0 | JWT 认证 |
| **httpx** | >=0.26.0 | HTTP 客户端 |
| **arq** | >=0.25.0 | 异步任务队列 |

**架构亮点**:
- 全异步设计，支持高并发
- 采用 ADR-001 推荐的 **FastAPI 单体内核 + 可插拔执行层** 架构
- Gateway 层职责清晰：路由、鉴权、限流、审计、统一错误处理

### 2.2 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| **React** | 18.2.0 | UI 框架 |
| **TypeScript** | 5.3.0 | 类型系统 |
| **Vite** | 5.0.0 | 构建工具 |
| **Ant Design** | 5.12.0 | UI 组件库 |
| **Tailwind CSS** | 3.4.0 | 样式框架 |
| **Zustand** | 4.4.0 | 状态管理 |
| **TanStack Query** | 5.17.0 | 数据获取 |
| **Recharts** | 2.10.0 | 图表库 |
| **i18next** | 25.8.12 | 国际化 |

**架构亮点**:
- 现代化 React 生态
- 轻量级状态管理 (Zustand)
- 内置国际化支持

### 2.3 数据库设计

**PostgreSQL 模型**:

| 表名 | 用途 |
|------|------|
| `projects` | 项目信息 |
| `versions` | 版本管理 |
| `deployments` | 部署记录 |
| `deployment_steps` | 部署步骤追踪 |
| `agent_states` | Agent 状态持久化 |
| `agent_invocations` | Agent 调用日志 |
| `agent_registrations` | Agent 注册信息 |
| `users` | 用户信息 |
| `regions` | 部署区域 |

**设计特点**:
- 支持 Agent 状态持久化 (ADR-004)
- 完整的调用审计链路
- 部署步骤追踪 (CI/CD -> ArgoCD -> Health Check)

### 2.4 Agent 系统架构

```
                    ┌─────────────────────────────────────┐
                    │           FastAPI Main              │
                    └─────────────────┬───────────────────┘
                                      │
                    ┌─────────────────▼───────────────────┐
                    │         Agent Gateway Layer         │
                    │  ┌──────────┐ ┌──────────┐ ┌──────┐ │
                    │  │  Router  │ │  Auth    │ │Trace │ │
                    │  │          │ │  Check   │ │      │ │
                    │  └────┬─────┘ └──────────┘ └──────┘ │
                    │       │                             │
                    │  ┌────▼─────┐ ┌──────────┐ ┌──────┐ │
                    │  │ Validator│ │  Errors  │ │ Rate │ │
                    │  │          │ │  Model   │ │Limit │ │
                    │  └──────────┘ └──────────┘ └──────┘ │
                    └─────────────────┬───────────────────┘
                                      │
                    ┌─────────────────▼───────────────────┐
                    │         Executor Router             │
                    │  ┌──────────────┐ ┌───────────────┐ │
                    │  │    Builtin   │ │    Remote     │ │
                    │  │   Executor   │ │   Executor    │ │
                    │  └──────┬───────┘ └───────┬───────┘ │
                    └─────────┼─────────────────┼─────────┘
                              │                 │
        ┌─────────────────────┼─────────────────┼─────────────────────┐
        │                     │                 │                     │
        ▼                     ▼                 ▼                     ▼
   ┌─────────┐          ┌─────────┐       ┌─────────┐          ┌─────────┐
   │  Chat   │          │   K8s   │       │  DNS    │          │  Third  │
   │  Agent  │          │  Agent  │       │  Agent  │          │  Party  │
   └─────────┘          └─────────┘       └─────────┘          │ Agents  │
                                                                └─────────┘
```

**内置 Agent 清单**:

| Agent ID | 名称 | 能力 |
|----------|------|------|
| `nexusops.chat` | AI Assistant | 通用对话、快捷命令、状态查询 |
| `nexusops.k8s` | Kubernetes Agent | K8s 部署、扩缩容、日志、资源描述 |
| `nexusops.deploy` | Deployment Orchestrator | 部署创建、回滚、状态、强制同步 |
| `nexusops.dns` | DNS Operations Agent | DNS 记录管理、域名生成 |

---

## 3. 产品需求梳理

### 3.1 已实现功能

**Phase 1-3 (已完成)**:
- [x] 基础设施监控 Dashboard
- [x] 项目与版本管理
- [x] 部署管理 (ArgoCD 集成)
- [x] CI/CD 集成 (Jenkins)
- [x] WebSocket 实时通信
- [x] 用户认证框架

**Phase 3.5 (已完成)**:
- [x] Agent Gateway 基础架构
- [x] 内置 Agent Handler 基类
- [x] 4 个内置 Agent 实现
- [x] Agent 注册与调用 API

**Phase 4 (已完成)**:
- [x] Gateway 调用契约 (MK-006)
- [x] Gateway 插件执行边界 (MK-007)
- [x] 第三方 Agent 最小闭环 (MK-008)

### 3.2 待开发功能

**Phase 5 (进行中)**:

| 任务 | 描述 | 优先级 |
|------|------|--------|
| MK-002 | Agent Gateway (路由、鉴权、限流、日志/监控) | P0 |
| MK-004 | Agent SDK (Python, Node.js, Go, Java) | P1 |
| MK-005 | Agent 开发者文档 | P1 |
| MK-009 | 内置 Agent 能力批次验收 (至少 6 类) | P0 |
| MK-010 | 外部系统兼容适配稳定性测试 | P0 |
| MK-011 | PRD-001 统一验收与测试证据归档 | P0 |

**二期规划**:
- [ ] Store 运营化能力 (评分/评论/推荐)
- [ ] 细粒度权限与配额策略中心
- [ ] 高级审计能力

### 3.3 MVP 核心功能清单

根据 PRD-001 验收标准，MVP 必须满足:

1. **至少 6 类内置 Agent 能力可稳定调用**
   - 当前: 4 类已实现 (Chat, K8s, Deploy, DNS)
   - 待补充: 2 类 (Logs Agent, Cost Agent 或 Git Agent)

2. **第三方 Agent 端到端流程**
   - 注册 -> 安装 -> 调用 -> 返回结构化结果
   - 当前状态: 基础流程已实现

3. **外部系统集成**
   - Jenkins: 已实现基础集成
   - ArgoCD: 已实现基础集成
   - DNS (阿里云/Cloudflare): 待实现

4. **Gateway 异常处理**
   - 超时处理: 已实现
   - 非法 JSON: 已实现
   - 下游错误: 已实现

---

## 4. 技术选型建议

### 4.1 当前架构优点

| 方面 | 优点 |
|------|------|
| **技术栈** | 现代化、社区活跃、文档完善 |
| **架构模式** | 遵循 ADR-001，渐进式演进，避免过度设计 |
| **异步设计** | 全栈异步，支持高并发 |
| **模块化** | Gateway 与 Executor 分离，职责清晰 |
| **可观测性** | 内置 trace_id 链路追踪 |
| **国际化** | 前端内置 i18n 支持 |

### 4.2 潜在技术债务

| 债务 | 风险 | 建议 |
|------|------|------|
| **内存存储** | Agent Store 使用内存 Dict，重启丢失 | 迁移到 Redis 或数据库 |
| **认证简化** | 当前 JWT 为演示模式，无真实 OIDC | 对接 Keycloak 或 Auth0 |
| **测试覆盖** | 测试文件较少 | 补充单元测试和集成测试 |
| **数据库迁移** | 未使用 Alembic | 建立 migration 流程 |
| **API 版本** | 版本 `/api/v1` 硬编码 | 配置化管理 |
| **限流实现** | 配置存在但未实现 | 实现基于 Redis 的限流 |

### 4.3 改进建议

**短期 (1-2 周)**:
1. 补充 Logs Agent 和 Cost Agent，满足 MVP 6 类 Agent 要求
2. 实现 Redis 限流中间件
3. 添加数据库 migration 脚本

**中期 (1 个月)**:
1. 完善 Agent SDK (Python 优先)
2. 对接真实 OIDC 认证
3. 补充集成测试

**长期 (季度)**:
1. 实现 Store 运营化能力
2. 构建细粒度权限系统
3. 考虑 Gateway 独立部署

---

## 5. 里程碑规划

### 5.1 MVP 阶段目标 (当前 -> Gate-B)

**时间窗口**: 2-3 周

**交付物**:
- [ ] 6 类内置 Agent 全部可用
- [ ] DNS Agent 对接阿里云/Cloudflare
- [ ] Jenkins/ArgoCD 关键链路稳定
- [ ] 第三方 Agent MVP 跑通
- [ ] 基础限流实现

**验收标准**:
- 合约测试 100% 通过
- 集成测试覆盖关键路径
- UAT 脚本可执行

### 5.2 Beta 阶段目标 (Gate-B -> Gate-C)

**目标时间窗口**: 1-2 月

**核心交付物**:

#### 5.2.1 Agent SDK (Python 优先)

**功能范围**:
- Agent 注册: 支持 SDK 方式注册新 Agent 到 Gateway
- Agent 调用: 支持同步/异步调用已注册 Agent
- 状态管理: 支持 Agent 状态查询和更新
- 错误处理: 统一异常类型和错误恢复机制

**技术要求**:
- 包含完整类型定义 (Type hints + Pydantic models)
- 支持 Python 3.9+
- 提供 sync/async 两种 API
- 内置重试和超时机制

**示例代码**:
```python
from nexusops_sdk import AgentClient, AgentConfig

# 初始化客户端
client = AgentClient(config=AgentConfig(
    base_url="https://nexusops.example.com",
    api_key="your-api-key"
))

# 注册 Agent
await client.agents.register(
    agent_id="my-custom-agent",
    name="My Custom Agent",
    capabilities=["data-processing", "report-generation"],
    endpoint="https://my-agent.example.com/webhook"
)

# 调用 Agent
result = await client.agents.invoke(
    agent_id="nexusops.k8s",
    action="get_pods",
    params={"namespace": "production"}
)
```

#### 5.2.2 开发者文档

**文档结构**:
```
docs/
├── getting-started/
│   ├── installation.md
│   ├── quick-start.md
│   └── architecture-overview.md
├── agent-development/
│   ├── agent-lifecycle.md
│   ├── contract-specification.md
│   ├── error-handling.md
│   └── testing-guide.md
├── api-reference/
│   ├── gateway-api.md
│   ├── sdk-reference.md
│   └── webhook-spec.md
└── best-practices/
    ├── security.md
    ├── performance.md
    └── troubleshooting.md
```

**交付标准**:
- [ ] 所有 API 有 OpenAPI 规范
- [ ] 每个概念有代码示例
- [ ] 提供可运行的 Demo 项目

#### 5.2.3 监控告警集成

**Prometheus Metrics**:
| 指标名 | 类型 | 描述 |
|--------|------|------|
| `nexusops_agent_invocations_total` | Counter | Agent 调用总数 |
| `nexusops_agent_invocation_duration_seconds` | Histogram | 调用延迟分布 |
| `nexusops_agent_errors_total` | Counter | 错误总数 (按 agent_id, error_type) |
| `nexusops_agent_active_sessions` | Gauge | 活跃会话数 |
| `nexusops_gateway_requests_total` | Counter | Gateway 请求总数 |
| `nexusops_gateway_rate_limit_hits` | Counter | 限流命中次数 |

**告警规则**:
```yaml
groups:
  - name: nexusops-agent-alerts
    rules:
      - alert: AgentHighErrorRate
        expr: |
          rate(nexusops_agent_errors_total[5m])
          / rate(nexusops_agent_invocations_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Agent {{ $labels.agent_id }} error rate > 5%"

      - alert: AgentSlowResponse
        expr: |
          histogram_quantile(0.95,
            rate(nexusops_agent_invocation_duration_seconds_bucket[5m])
          ) > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Agent {{ $labels.agent_id }} P95 latency > 2s"
```

**Dashboard 模板**:
- Agent Overview Dashboard: 调用量、延迟、错误率总览
- Agent Detail Dashboard: 单个 Agent 深度分析
- Gateway Health Dashboard: Gateway 整体健康状态

#### 5.2.4 性能优化

**目标指标**:
| 指标 | 目标值 | 当前值 | 优化方案 |
|------|--------|--------|----------|
| Agent 调用延迟 (P95) | < 2s | TBD | 连接池、缓存、异步优化 |
| 并发处理能力 | 100+ RPM | TBD | 并发控制、资源隔离 |
| 内存使用 (Gateway) | < 512MB | TBD | 内存泄漏检测、对象池 |
| CPU 使用率 (空闲) | < 5% | TBD | 事件驱动优化 |

**优化措施**:
1. **连接池管理**: httpx 连接复用，减少握手开销
2. **结果缓存**: 对幂等查询类操作实现短时缓存
3. **并发控制**: 基于信号量的并发限制，防止资源耗尽
4. **异步优化**: 全链路异步，避免阻塞调用

**验收标准**:
- [ ] SDK 可独立安装使用 (`pip install nexusops-sdk`)
- [ ] 外部开发者可自主接入 Agent (文档引导)
- [ ] 关键指标可观测 (latency, error_rate, throughput)
- [ ] 性能基准测试通过 (P95 < 2s, 100+ RPM)

### 5.3 GA 阶段目标 (Gate-C+)

**目标时间窗口**: 季度级别

**交付物**:
- [ ] Store 运营化 (评分/评论)
- [ ] 细粒度权限与配额
- [ ] 多租户支持
- [ ] SLA 保障

**验收标准**:
- 生态接入无需核心研发支持
- 达到企业级可用标准

---

## 5.4 里程碑验收检查点 (Gate Review Checklist)

### Gate-A (项目启动) - 已完成

- [x] 技术选型确定
- [x] 架构设计评审通过
- [x] 开发环境搭建完成
- [x] 基础框架搭建

### Gate-B (MVP 完成) - 进行中

**功能验收**:
- [ ] 6 类内置 Agent 全部可用并通过测试
- [ ] 第三方 Agent 注册/调用流程完整
- [ ] DNS Agent 对接真实 API (阿里云/Cloudflare)
- [ ] Jenkins/ArgoCD 集成链路稳定

**质量验收**:
- [ ] 合约测试 100% 通过
- [ ] 集成测试覆盖关键路径 (>80%)
- [ ] UAT 脚本可执行
- [ ] 无 P0/P1 缺陷

**文档验收**:
- [ ] API 文档 (OpenAPI) 完整
- [ ] 部署文档可执行
- [ ] 架构决策记录 (ADR) 更新

### Gate-C (Beta 完成)

**功能验收**:
- [ ] SDK 可独立安装使用
- [ ] 开发者文档完整且可执行
- [ ] 监控指标采集正常
- [ ] 告警规则生效

**性能验收**:
- [ ] Agent 调用 P95 延迟 < 2s
- [ ] 支持 100+ RPM 并发
- [ ] 压力测试通过 (无资源泄漏)

**生态验收**:
- [ ] 至少 1 个外部开发者成功接入
- [ ] Demo 项目可运行
- [ ] 反馈机制建立

### Gate-D (GA 发布)

**功能验收**:
- [ ] Store 运营化功能完整
- [ ] 细粒度权限系统上线
- [ ] 多租户隔离验证通过

**运维验收**:
- [ ] SLA 指标定义并监控
- [ ] 灾备方案验证通过
- [ ] 安全审计通过

**生态验收**:
- [ ] 至少 3 个第三方 Agent 上架
- [ ] 开发者社区活跃
- [ ] 企业客户 PoC 通过

---

## 6. 结论与建议

### 6.1 项目健康度评估

| 维度 | 评分 | 说明 |
|------|------|------|
| **架构设计** | A | 遵循 ADR，渐进式演进，职责清晰 |
| **代码质量** | B+ | 结构清晰，但测试覆盖不足 |
| **功能完成度** | B | 核心功能已实现，MVP 差 2 类 Agent |
| **文档完善度** | B- | PRD/ADR 完善，但 API 文档和开发者指南缺失 |
| **可维护性** | B+ | 模块化设计良好，但有技术债务 |

### 6.2 关键行动项

1. **P0 (本周)**:
   - 补充 Logs Agent 和 Cost Agent 实现
   - 实现 DNS Agent 真实调用
   - 添加基础限流

2. **P1 (下周)**:
   - 补充集成测试
   - 实现 Redis 持久化存储
   - 完善 API 文档

3. **P2 (月内)**:
   - 发布 Python SDK
   - 对接真实 OIDC
   - 建立 migration 流程

### 6.3 风险提示

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 外部 API 不稳定 | 中 | 高 | 超时+熔断+部分结果返回 |
| Agent 返回格式不统一 | 中 | 中 | Gateway 严格 Schema 校验 |
| 高风险操作误执行 | 低 | 高 | 操作白名单+二次确认 |
| 生态扩张后治理不足 | 中 | 中 | 分阶段升级权限/审计/配额 |

---

**报告完成**
**下一步**: 与团队对齐优先级，开始 MVP 收尾工作
