# NexusOps - AI Native Operations Platform

AI 原生运维平台，为多模态对话系统构建的统一运维 Web 平台。

## 项目结构

```
NexusOps/
├── AGENTS.md                      # OpenCode entry point
├── CLAUDE.md                      # Claude Code entry point
├── Makefile
├── README.md
├── _archive/                      # Legacy/archived artifacts (read-only)
├── backend/                       # FastAPI backend
├── docker/                        # Docker Compose and scripts
│   ├── docker-compose.middleware.yml
│   └── scripts/
│       └── init-db.sql
├── agentic_pact/                  # Canonical multi-agent workflow (current)
│   ├── PACT.md
│   ├── templates/
│   ├── state/
│   ├── specs/
│   ├── adr/
│   ├── reference/
│   └── evidence/
├── frontend/                      # React frontend
├── init.sh
├── logs/
├── scripts/
└── test_results/
```

## 快速开始

### 前置要求

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+ (或使用 Docker)

### 1. 启动基础设施

```bash
cd docker
docker-compose -f docker-compose.middleware.yml up -d postgres redis
```

### 2. 初始化数据库

数据库会在启动时执行 `docker/scripts/init-db.sql`（如果存在）。如需手动执行：

```bash
psql -h localhost -U nexusops -d nexusops -f docker/scripts/init-db.sql
```

### 3. 启动后端

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

### 5. 访问应用

- 前端: http://localhost:3000
- API: http://localhost:8000

## 环境变量

### 后端

```bash
# 数据库
DB_HOST=localhost
DB_PORT=5432
DB_USER=nexusops
DB_PASSWORD=nexusops
DB_DATABASE=nexusops

# 认证
JWT_SECRET=your-secret-key
OIDC_ISSUER=https://keycloak.example.com/realms/nexusops

# 外部服务
GRAFANA_URL=http://localhost:3000
ARGOCD_URL=https://argocd.example.com
JENKINS_URL=https://jenkins.example.com
HARBOR_URL=https://harbor.example.com
OPENCLAW_URL=ws://openclaw.example.com/ws
```

### 前端

```bash
VITE_API_URL=/api/v1
VITE_WS_URL=ws://localhost:8000/ws
```

## API 端点

| 端点 | 描述 |
|------|------|
| `GET /api/v1/overview` | 获取总览数据 |
| `GET /api/v1/resources` | 获取资源列表 |
| `GET /api/v1/deployments` | 获取部署列表 |
| `GET /api/v1/alerts` | 获取告警列表 |
| `GET /api/v1/tickets` | 获取工单列表 |
| `POST /api/v1/tickets` | 创建工单 |
| `GET /api/v1/ai/query` | AI 查询 |
| `WS /ws` | WebSocket 连接 |

## 技术栈

### 后端
- **框架**: FastAPI
- **ORM**: SQLAlchemy (async)
- **数据校验**: Pydantic v2
- **WebSocket**: FastAPI WebSocket
- **配置**: Pydantic Settings

### 前端
- **框架**: React 18 + TypeScript
- **构建**: Vite
- **UI**: Ant Design + Tailwind CSS
- **状态管理**: Zustand
- **数据获取**: TanStack Query
- **图表**: Recharts

### 基础设施
- **数据库**: PostgreSQL
- **缓存**: Redis
- **监控**: Prometheus + Grafana
- **CI/CD**: Jenkins
- **部署**: ArgoCD + Kubernetes
- **镜像仓库**: Harbor

## 开发指南

### 添加新的 API 端点

1. 在 `backend/app/models/schemas.py` 添加数据模型
2. 在 `backend/app/services/` 添加业务逻辑 (如需要)
3. 在 `backend/app/api/` 添加路由并在 `backend/app/main.py` 注册
4. 在 `frontend/src/services/` 添加 API 调用
5. 在 `frontend/src/pages/` 添加页面组件

### 添加新的外部集成

1. 在 `backend/app/services/` 创建新的集成模块
2. 实现客户端接口
3. 在 `backend/app/core/config.py` 添加配置
4. 在对应服务或 API 路由中使用

## 许可证

MIT
