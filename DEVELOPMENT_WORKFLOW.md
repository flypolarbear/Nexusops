# NexusOps 项目开发流程完整指南

## 📋 项目概览

**NexusOps** - AI 原生运维平台，为多模态对话系统构建的统一运维 Web 平台

### 技术栈

| 层级 | 技术 |
|------|------|
| **后端** | FastAPI + SQLAlchemy async + Pydantic v2 |
| **前端** | React 18 + TypeScript + Zustand + Ant Design |
| **数据库** | PostgreSQL 15+ / Redis 7+ |
| **容器化** | Docker + Kubernetes |
| **Agent** | Python async + Kubernetes client |

---

## 🏗️ 架构设计

### Agent-First 架构

```
┌─────────────────────────────────────────┐
│         Frontend (React)                 │
└─────────────────────────────────────────┘
                ↓ HTTP/WebSocket
┌─────────────────────────────────────────┐
│       API Layer (FastAPI)                │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│         Gateway Core                     │
│  • Middleware: Trace → Auth → RateLimit  │
│  • ExecutorRouter                        │
└─────────────────────────────────────────┘
        ↓                       ↓
┌──────────────┐      ┌──────────────────┐
│ Builtin      │      │ Remote           │
│ Executor     │      │ Executor         │
│ • K8s        │      │ • HTTP/gRPC      │
│ • Deploy     │      │ • Third-Party    │
│ • DNS/Logs   │      │   Agents         │
└──────────────┘      └──────────────────┘
```

---

## 🚀 开发环境设置

### 1. 环境要求

- **Python**: 3.11+
- **Node.js**: 18+ (推荐 20+)
- **PostgreSQL**: 15+
- **Redis**: 7+
- **Docker**: 最新版

### 2. 快速启动

```bash
# 克隆项目
cd ~/Development/ClaudeCodeWorkspace/Projects/NexusOps

# 安装依赖
make install

# 启动 Docker 服务（数据库、Redis）
make docker-up

# 启动后端
make backend

# 启动前端（新终端）
make frontend

# 或者一次性启动所有服务
make dev
```

### 3. 数据库初始化

```bash
# 初始化数据库
make db-init

# 重置数据库
make db-reset
```

---

## 📂 项目结构

```
NexusOps/
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── main.py         # FastAPI 主入口
│   │   ├── api/            # API 路由
│   │   ├── agents/         # Agent 实现
│   │   ├── gateway/        # Gateway 核心
│   │   ├── services/       # 业务逻辑
│   │   ├── models/         # 数据模型
│   │   └── core/           # 配置和工具
│   ├── tests/              # 测试代码
│   ├── requirements.txt    # Python 依赖
│   └── Dockerfile          # Docker 配置
│
├── frontend/                # 前端代码
│   ├── src/
│   │   ├── components/     # React 组件
│   │   ├── pages/          # 页面
│   │   ├── stores/         # Zustand 状态
│   │   ├── services/       # API 调用
│   │   └── utils/          # 工具函数
│   ├── package.json        # Node 依赖
│   └── vite.config.ts      # Vite 配置
│
├── docker/                  # Docker 配置
│   └── docker-compose.middleware.yml
│
├── docs/                    # 用户文档
├── scripts/                 # 自动化脚本
├── specs/                   # 规格说明
└── Makefile                 # 构建命令
```

---

## 💻 开发流程

### 阶段 1: 需求分析

1. **创建规格文档**
   ```bash
   # 在 specs/ 目录创建新规格
   vi specs/feature-name.md
   ```

2. **定义 Agent 接口**
   - Request/Response 合约
   - 上下文参数
   - 错误处理

### 阶段 2: 后端开发

#### 2.1 API 开发

```bash
# 1. 创建 API 路由
vi backend/app/api/new_feature.py

# 2. 添加到 main.py
from app.api import new_feature
app.include_router(new_feature.router, prefix="/api/new-feature", tags=["New Feature"])
```

#### 2.2 Agent 开发

```bash
# 1. 创建 Agent
vi backend/app/agents/new_agent.py

# 2. 实现 Agent 接口
class NewAgent(BaseAgent):
    async def invoke(self, request: InvokeRequest) -> InvokeResponse:
        # 实现逻辑
        pass
```

#### 2.3 数据模型

```bash
# 1. 创建模型
vi backend/app/models/new_model.py

# 2. 使用 Pydantic v2
from pydantic import BaseModel

class NewModel(BaseModel):
    id: str
    name: str
    created_at: datetime
```

### 阶段 3: 前端开发

#### 3.1 创建组件

```bash
# 1. 创建页面组件
vi frontend/src/pages/NewFeature.tsx

# 2. 创建状态管理
vi frontend/src/stores/newFeatureStore.ts
```

#### 3.2 API 集成

```typescript
// frontend/src/services/newFeatureService.ts
import axios from 'axios';

export const newFeatureService = {
  getData: async () => {
    const response = await axios.get('/api/new-feature');
    return response.data;
  }
};
```

### 阶段 4: 测试

#### 4.1 后端测试

```bash
# 运行单元测试
cd backend
pytest tests/ -v

# 运行特定测试
pytest tests/test_new_feature.py -v

# 查看覆盖率
pytest --cov=app tests/
```

#### 4.2 前端测试

```bash
# 运行前端测试
cd frontend
npm run test
```

#### 4.3 集成测试

```bash
# 运行所有测试
make test
```

---

## 🧪 测试流程

### 测试层级

| 测试类型 | 工具 | 覆盖率要求 |
|---------|------|-----------|
| **单元测试** | pytest / Vitest | 70%+ |
| **集成测试** | pytest + httpx | 关键路径 |
| **契约测试** | 自定义 | Agent 接口 |
| **E2E 测试** | Playwright | 核心功能 |

### 测试命令

```bash
# 后端测试
make test-backend

# 前端测试
make test-frontend

# 所有测试
make test

# 测试监控（持续运行）
make test-monitor
```

---

## 🚢 部署流程

### 1. 构建产物

```bash
# 构建后端
make build-backend

# 构建前端
make build-frontend

# 构建所有
make build
```

### 2. Docker 部署

```bash
# 构建镜像
docker build -t nexusops-backend:latest backend/
docker build -t nexusops-frontend:latest frontend/

# 运行容器
docker-compose up -d
```

### 3. Kubernetes 部署

```bash
# 应用配置
kubectl apply -f k8s/

# ArgoCD 同步
argocd app sync nexusops
```

---

## 🤖 自动化工具

### 1. Agent 团队

```bash
# 架构师 Agent（Claude Opus）
make architect

# 开发者 Agent（GLM-5）
make developer

# 测试监控 Agent
make test-monitor
```

### 2. 代码质量

```bash
# 后端 Lint
make lint-backend

# 前端 Lint
make lint-frontend

# 所有 Lint
make lint
```

### 3. 数据库管理

```bash
# 初始化数据库
make db-init

# 重置数据库
make db-reset

# 查看日志
make docker-logs
```

---

## 📋 开发规范

### 宪法（Constitution）

项目遵循严格的开发宪法：

#### I. API-First Design
- ✅ 所有功能必须暴露 REST 或 WebSocket API
- ✅ 完整的 OpenAPI 规范
- ✅ 契约优先于实现

#### II. Async-First Architecture
- ✅ 所有 I/O 操作使用 async/await
- ✅ FastAPI async 处理器
- ✅ SQLAlchemy async 会话

#### III. Type Safety (NON-NEGOTIABLE)
- ✅ Pydantic v2 用于所有数据模型
- ✅ TypeScript 严格模式
- ✅ 零 `any` 类型，零 `@ts-ignore`

#### IV. Contract-Based Agent Interface
- ✅ 统一的 Request/Response 格式
- ✅ 所有 Agent 遵循相同契约

#### V. Test Coverage
- ✅ 单元测试覆盖所有服务
- ✅ 集成测试覆盖外部集成
- ✅ 70% 最低覆盖率

#### VI. Component-Based Frontend
- ✅ React 函数组件 + Hooks
- ✅ Zustand 全局状态管理
- ✅ Ant Design + Tailwind CSS

#### VII. Infrastructure as Code
- ✅ Docker Compose 本地开发
- ✅ Kubernetes 生产部署
- ✅ ArgoCD GitOps

---

## 🔄 日常开发工作流

### 典型的一天

```bash
# 1. 拉取最新代码
git pull origin master

# 2. 启动开发环境
make dev

# 3. 创建新分支
git checkout -b feature/new-feature

# 4. 开发...

# 5. 运行测试
make test

# 6. 提交代码
git add .
git commit -m "feat: add new feature"
git push origin feature/new-feature

# 7. 创建 Pull Request
gh pr create --title "Add new feature" --body "Description"
```

---

## 🛠️ 常用命令速查

### 开发命令

| 命令 | 说明 |
|------|------|
| `make dev` | 启动完整开发环境 |
| `make backend` | 仅启动后端 |
| `make frontend` | 仅启动前端 |
| `make install` | 安装所有依赖 |
| `make test` | 运行所有测试 |
| `make lint` | 运行代码检查 |
| `make build` | 构建所有服务 |

### Docker 命令

| 命令 | 说明 |
|------|------|
| `make docker-up` | 启动 Docker 服务 |
| `make docker-down` | 停止 Docker 服务 |
| `make docker-logs` | 查看 Docker 日志 |

### 数据库命令

| 命令 | 说明 |
|------|------|
| `make db-init` | 初始化数据库 |
| `make db-reset` | 重置数据库 |

---

## 📚 参考文档

- **用户文档**: `docs/`
- **架构文档**: `docs/architecture.md`
- **API 文档**: `http://localhost:8000/docs`
- **宪法**: `.specify/memory/constitution.md`
- **Agent 入口**: `CLAUDE.md`

---

## 🎯 下一步行动

### 新开发者

1. ✅ 阅读本文档
2. ✅ 设置开发环境
3. ✅ 阅读 `docs/architecture.md`
4. ✅ 查看 `CLAUDE.md` 了解开发规范
5. ✅ 运行 `make dev` 启动项目

### 开始开发

1. 选择一个 feature 或 bug
2. 创建分支
3. 编写代码 + 测试
4. 提交 PR
5. Code Review
6. 合并到 master

---

**文档版本**: 1.0
**更新时间**: 2026-03-14
**维护者**: NexusOps Team
