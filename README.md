# NexusOps - AI Native Operations Platform

> AI 原生运维平台，为多模态对话系统构建的统一运维 Web 平台

## 系统设计

### Agent 驱动架构

NexusOps 采用 **Agent-First** 设计理念，将运维能力抽象为可组合的智能代理。

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
└─────────────────────────────────────────────────────────────┘
                              │ HTTP/WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Gateway Core                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Middleware: Trace → Auth → Schema → RateLimit       │   │
│  └─────────────────────────────────────────────────────┘   │
│                              │                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              ExecutorRouter                          │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
              │                              │
              ▼                              ▼
┌─────────────────────────┐    ┌─────────────────────────────┐
│    BuiltinExecutor      │    │      RemoteExecutor         │
│  ┌─────────────────┐    │    │  ┌─────────────────────┐    │
│  │ Internal Agents │    │    │  │ Third-Party Agents  │    │
│  │ - chat          │    │    │  │ - HTTP/gRPC Clients │    │
│  │ - k8s           │    │    │  └─────────────────────┘    │
│  │ - deploy        │    │    └─────────────────────────────┘
│  │ - dns, logs...  │    │
│  └─────────────────┘    │
└─────────────────────────┘
```

### 核心概念

| 概念 | 说明 |
|------|------|
| **Agent** | 具备特定领域能力的智能代理（如 K8s 操作、部署管理、日志查询） |
| **Gateway** | 所有 Agent 调用的统一入口，负责认证、验证、追踪、限流 |
| **Executor** | Agent 运行器，支持内置和远程两种模式 |
| **Contract** | 统一的 `InvokeRequest` / `InvokeResponse` 格式 |

### 统一调用合约

所有 Agent 遵循统一的请求/响应格式：

```json
// Request
{
  "request_id": "uuid",
  "agent_id": "nexusops.k8s",
  "query": "列出 default 命名空间的 pods",
  "context": {"user_id": "...", "project_id": "..."}
}

// Response
{
  "request_id": "uuid",
  "trace_id": "32位hex",
  "status": "success",
  "content": {"text": "...", "format": "markdown"},
  "structured_output": {"pods": [...]},
  "suggested_actions": []
}
```

---

## 目录结构

```
NexusOps/
├── AGENTS.md                  # AI Agent 入口 (OpenCode/Claude Code/Cursor)
├── README.md                  # 本文件
│
├── docs/                      # 用户文档
│   ├── index.md               # 文档导航
│   ├── start/                 # 快速开始
│   │   ├── install.md         # 安装指南
│   │   ├── quickstart.md      # 10分钟上手
│   │   └── concepts.md        # 核心概念
│   ├── api/                   # API 参考
│   │   ├── gateway.md         # Gateway API
│   │   ├── invoke.md          # 调用接口
│   │   └── errors.md          # 错误码表
│   └── guides/                # 开发指南
│       ├── agent-dev.md       # Agent 开发
│       ├── contract.md        # 请求响应合约
│       ├── lifecycle.md       # Agent 生命周期
│       └── testing.md         # 测试指南
│
├── evolve/                    # 演进知识库
│   ├── index.md               # 知识库导航
│   ├── patterns/              # 验证模式
│   │   ├── async-patterns.md  # 异步处理模式
│   │   ├── caching.md         # 缓存策略
│   │   ├── connection-pool.md # 连接池模式
│   │   ├── error-handling.md  # 错误处理模式
│   │   ├── rate-limiting.md   # 限流熔断
│   │   └── security.md        # 安全实践
│   ├── anti-patterns/         # 反模式
│   │   └── avoid.md           # 常见错误
│   └── decisions/             # 技术决策
│       ├── monolith-gateway.md
│       ├── unified-contract.md
│       └── error-taxonomy.md
│
├── copilot/                   # AI 编码工具指南
│   ├── index.md               # 总览与快速开始
│   ├── tools/                 # 工具指南
│   │   ├── claude-code.md     # Claude Code
│   │   ├── opencode.md        # OpenCode
│   │   ├── cursor.md          # Cursor
│   │   ├── github-copilot.md  # GitHub Copilot
│   │   └── codex.md           # OpenAI Codex
│   ├── instruction-files.md   # 指令文件格式
│   ├── best-practices.md      # AI 编码最佳实践
│   └── faq.md                 # 常见问题
│
├── .specify/                  # Spec-Kit 配置
│   ├── memory/
│   │   └── constitution.md    # 项目宪法 (最高优先级)
│   ├── templates/             # 规格模板
│   └── scripts/               # 辅助脚本
│
├── backend/                   # FastAPI 后端
│   ├── app/
│   │   ├── api/               # API 路由
│   │   ├── gateway/           # Gateway 核心
│   │   ├── agents/            # 内置 Agent 实现
│   │   ├── services/          # 业务逻辑
│   │   ├── models/            # 数据模型
│   │   ├── llm/               # LLM 集成
│   │   └── core/              # 配置与基础设施
│   ├── sdk/                   # Agent SDK
│   └── tests/                 # 测试
│
├── frontend/                  # React 前端
│   ├── src/
│   │   ├── components/        # UI 组件
│   │   ├── pages/             # 页面
│   │   ├── stores/            # Zustand 状态
│   │   ├── services/          # API 服务
│   │   └── hooks/             # 自定义 Hooks
│   └── public/                # 静态资源
│
├── docker/                    # Docker Compose
│   └── scripts/               # 启动脚本
│
├── scripts/                   # 工具脚本
├── tests/                     # E2E 测试
└── _archive/                  # 归档文件
```

---

## 文档导航

| 文档 | 说明 |
|------|------|
| [docs/](./docs/index.md) | 用户文档、API 参考、开发指南 |
| [evolve/](./evolve/index.md) | 演进知识库、验证模式、技术决策 |
| [copilot/](./copilot/index.md) | AI 编码工具使用指南 |
| [AGENTS.md](./AGENTS.md) | AI Agent 入口点 |
| [DEVELOPMENT_WORKFLOW.md](./DEVELOPMENT_WORKFLOW.md) | 开发流程指南 |

---

## 快速开始

### 1. 启动基础设施

```bash
cd docker
docker-compose -f docker-compose.middleware.yml up -d postgres redis
```

### 2. 启动后端

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 3. 启动前端

```bash
cd frontend
npm install && npm run dev
```

### 4. 访问应用

- 前端: http://localhost:3000
- API: http://localhost:8000
- API 文档: http://localhost:8000/docs

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI + SQLAlchemy async + Pydantic v2 |
| 前端 | React 18 + TypeScript + Zustand |
| 数据库 | PostgreSQL 15+ / Redis 7+ |
| 部署 | Docker + Kubernetes + ArgoCD |
| 监控 | Prometheus + Grafana |

---

## 内置 Agents

| Agent ID | 能力 |
|----------|------|
| `nexusops.chat` | 通用对话、快捷命令 |
| `nexusops.k8s` | Kubernetes 资源操作 |
| `nexusops.deploy` | 部署管理与状态查询 |
| `nexusops.dns` | DNS 记录管理 |
| `nexusops.logs` | 日志聚合与查询 |
| `nexusops.cost` | 成本分析与优化 |

---

## AI 辅助开发

本项目支持多种 AI 编码工具：

| 工具 | 入口文件 | 指南 |
|------|----------|------|
| OpenCode | `AGENTS.md` | [copilot/tools/opencode.md](./copilot/tools/opencode.md) |
| Claude Code | `AGENTS.md` / `CLAUDE.md` | [copilot/tools/claude-code.md](./copilot/tools/claude-code.md) |
| Cursor | `.cursor/rules/` | [copilot/tools/cursor.md](./copilot/tools/cursor.md) |
| GitHub Copilot | `.github/copilot-instructions.md` | [copilot/tools/github-copilot.md](./copilot/tools/github-copilot.md) |

详见 [copilot/](./copilot/index.md) 获取完整指南。

---

## 许可证

MIT
