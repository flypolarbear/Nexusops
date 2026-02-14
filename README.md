# NexusOps - AI Native Operations Platform

AI 原生运维平台，为多模态对话系统构建的统一运维 Web 平台。

## 项目结构

```
NexusOps/
├── backend/                    # Go 后端服务
│   ├── cmd/                    # 服务入口
│   │   ├── api-gateway/        # API 网关服务
│   │   └── chat-gateway/       # Chat Gateway (WebSocket)
│   ├── internal/               # 内部模块
│   │   ├── auth/               # 认证模块
│   │   ├── chat/               # 聊天模块
│   │   ├── config/             # 配置
│   │   ├── middleware/         # 中间件
│   │   ├── models/             # 数据模型
│   │   └── ...
│   ├── pkg/                    # 外部集成
│   │   ├── k8s/                # Kubernetes 客户端
│   │   ├── grafana/            # Grafana API
│   │   ├── argocd/             # ArgoCD API
│   │   ├── jenkins/            # Jenkins API
│   │   ├── harbor/             # Harbor API
│   │   └── openclaw/           # Openclaw 集成
│   └── deployments/
│       └── docker/             # Docker Compose 配置
│           ├── docker-compose.yaml
│           ├── init-db.sql     # 数据库初始化
│           └── prometheus.yml
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── components/         # UI 组件
│   │   ├── pages/              # 页面
│   │   ├── hooks/              # 自定义 Hooks
│   │   ├── services/           # API 服务
│   │   ├── stores/             # Zustand 状态管理
│   │   ├── types/              # TypeScript 类型
│   │   └── styles/             # 样式
│   ├── package.json
│   └── vite.config.ts
└── docs/                       # 文档
```

## 快速开始

### 前置要求

- Go 1.22+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+ (或使用 Docker)

### 1. 启动基础设施

```bash
cd backend/deployments/docker
docker-compose up -d postgres redis grafana prometheus
```

### 2. 初始化数据库

数据库会自动执行 `init-db.sql`，或手动执行：

```bash
psql -h localhost -U nexusops -d nexusops -f backend/deployments/docker/init-db.sql
```

### 3. 启动后端

```bash
cd backend
go mod tidy
go run ./cmd/api-gateway
# 另一个终端
go run ./cmd/chat-gateway
```

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

### 5. 访问应用

- 前端: http://localhost:3000
- API Gateway: http://localhost:8080
- Chat Gateway: http://localhost:8081
- Grafana: http://localhost:3001 (admin/admin)
- Prometheus: http://localhost:9090

## 环境变量

### 后端

```bash
# 数据库
DB_HOST=localhost
DB_PORT=5432
DB_USER=nexusops
DB_PASSWORD=nexusops_dev
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
VITE_WS_URL=ws://localhost:8081
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
- **框架**: Gin
- **ORM**: pgx (PostgreSQL driver)
- **WebSocket**: gorilla/websocket
- **配置**: Viper
- **认证**: JWT, OAuth2

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

1. 在 `backend/internal/models/` 添加数据模型
2. 在 `backend/internal/handlers/` 添加处理器
3. 在 `backend/cmd/api-gateway/main.go` 注册路由
4. 在 `frontend/src/services/api.ts` 添加 API 调用
5. 在 `frontend/src/pages/` 添加页面组件

### 添加新的外部集成

1. 在 `backend/pkg/` 创建新的集成包
2. 实现客户端接口
3. 在 `backend/internal/config/config.go` 添加配置
4. 在聚合服务中使用

## 许可证

MIT
