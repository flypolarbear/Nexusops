# NexusOps 生产环境部署指南

本文档描述 NexusOps AI 原生运维平台的生产环境部署流程。

---

## 1. 环境要求

### 1.1 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 2 核 | 4 核+ |
| 内存 | 4 GB | 8 GB+ |
| 存储 | 20 GB SSD | 50 GB+ SSD |

### 1.2 软件要求

| 软件 | 版本要求 | 说明 |
|------|----------|------|
| Python | 3.10+ | 后端运行环境 |
| Node.js | 18+ | 前端构建 |
| PostgreSQL | 15+ | 主数据库 |
| Redis | 7+ | 缓存与会话存储 |
| Docker | 24+ | 容器化部署（可选） |
| Kubernetes | 1.28+ | 生产编排（推荐） |

### 1.3 网络要求

| 端口 | 服务 | 说明 |
|------|------|------|
| 8000 | Backend API | FastAPI 服务 |
| 3000 | Frontend | React 前端 |
| 5432 | PostgreSQL | 数据库 |
| 6379 | Redis | 缓存服务 |

### 1.4 外部服务依赖

| 服务 | 用途 | 配置项 |
|------|------|--------|
| ArgoCD | GitOps 部署 | `ARGOCD_URL`, `ARGOCD_TOKEN` |
| Jenkins | CI/CD 流水线 | `JENKINS_URL`, `JENKINS_TOKEN` |
| GitHub | 代码仓库 | `GITHUB_TOKEN` |
| GLM API | AI 模型 | `GLM_API_KEY` |

---

## 2. 部署步骤

### 2.1 准备工作

```bash
# 克隆代码仓库
git clone https://github.com/your-org/nexusops.git
cd nexusops

# 切换到稳定版本
git checkout v1.0.0
```

### 2.2 部署基础设施

#### 方式一：Docker Compose（开发/测试环境）

```bash
# 启动 PostgreSQL 和 Redis
cd docker
docker-compose -f docker-compose.middleware.yml up -d

# 验证服务状态
docker-compose -f docker-compose.middleware.yml ps
```

#### 方式二：Kubernetes（生产环境）

```yaml
# k8s/postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: nexusops-postgres
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: nexusops-postgres
  template:
    metadata:
      labels:
        app: nexusops-postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: nexusops-secrets
              key: db-user
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: nexusops-secrets
              key: db-password
        - name: POSTGRES_DB
          value: nexusops
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
```

```yaml
# k8s/redis.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nexusops-redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nexusops-redis
  template:
    metadata:
      labels:
        app: nexusops-redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
```

```bash
# 创建命名空间和密钥
kubectl create namespace nexusops
kubectl create secret generic nexusops-secrets \
  --from-literal=db-user=nexusops \
  --from-literal=db-password=<YOUR_SECURE_PASSWORD> \
  -n nexusops

# 部署基础设施
kubectl apply -f k8s/postgres.yaml -n nexusops
kubectl apply -f k8s/redis.yaml -n nexusops
```

### 2.3 配置后端

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

创建生产环境配置文件 `.env`：

```bash
# .env (生产环境)
# ================================
# 应用配置
# ================================
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<生成一个安全的随机密钥>
ACCESS_TOKEN_EXPIRE_MINUTES=60

# ================================
# 数据库配置
# ================================
DATABASE_URL=postgresql+asyncpg://nexusops:<密码>@postgres:5432/nexusops

# ================================
# Redis 配置
# ================================
REDIS_URL=redis://redis:6379/0

# ================================
# CORS 配置
# ================================
CORS_ORIGINS=["https://nexusops.yourdomain.com"]

# ================================
# 外部服务
# ================================
ARGOCD_URL=https://argocd.yourdomain.com
ARGOCD_TOKEN=<ArgoCD API Token>
JENKINS_URL=https://jenkins.yourdomain.com
JENKINS_TOKEN=<Jenkins API Token>
GITHUB_TOKEN=<GitHub Personal Access Token>

# ================================
# AI 模型配置
# ================================
GLM_API_KEY=<GLM API Key>
GLM_API_URL=https://open.bigmodel.cn/api/paas/v4
```

生成安全密钥：

```bash
# 生成 SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2.4 构建前端

```bash
cd frontend

# 安装依赖
npm ci

# 创建生产环境配置
cat > .env.production << EOF
VITE_API_URL=/api/v1
VITE_WS_URL=wss://nexusops.yourdomain.com/ws
EOF

# 构建生产版本
npm run build

# 构建产物位于 dist/ 目录
```

### 2.5 部署后端服务

#### 方式一：Systemd 服务

```bash
# /etc/systemd/system/nexusops-backend.service
[Unit]
Description=NexusOps Backend API
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=nexusops
Group=nexusops
WorkingDirectory=/opt/nexusops/backend
Environment="PATH=/opt/nexusops/backend/.venv/bin"
ExecStart=/opt/nexusops/backend/.venv/bin/uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --proxy-headers
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable nexusops-backend
sudo systemctl start nexusops-backend
sudo systemctl status nexusops-backend
```

#### 方式二：Kubernetes Deployment

```yaml
# k8s/backend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nexusops-backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nexusops-backend
  template:
    metadata:
      labels:
        app: nexusops-backend
    spec:
      containers:
      - name: backend
        image: your-registry/nexusops-backend:v1.0.0
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: nexusops-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: nexusops-backend
spec:
  selector:
    app: nexusops-backend
  ports:
  - port: 8000
    targetPort: 8000
```

### 2.6 部署前端服务

#### Nginx 配置

```nginx
# /etc/nginx/sites-available/nexusops
server {
    listen 80;
    server_name nexusops.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name nexusops.yourdomain.com;

    # SSL 配置
    ssl_certificate /etc/letsencrypt/live/nexusops.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/nexusops.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;

    # 前端静态文件
    root /opt/nexusops/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket 代理
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }

    # Gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;
    gzip_min_length 1000;
}
```

```bash
# 启用站点
sudo ln -s /etc/nginx/sites-available/nexusops /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 3. 配置说明

### 3.1 环境变量详解

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `ENVIRONMENT` | 是 | development | 运行环境: development/staging/production |
| `DEBUG` | 否 | true | 调试模式，生产环境必须为 false |
| `SECRET_KEY` | 是 | - | JWT 签名密钥，至少 32 字符 |
| `DATABASE_URL` | 是 | - | PostgreSQL 连接字符串 |
| `REDIS_URL` | 是 | - | Redis 连接字符串 |
| `CORS_ORIGINS` | 否 | localhost | 允许的前端域名列表 |
| `ARGOCD_URL` | 否 | - | ArgoCD 服务地址 |
| `ARGOCD_TOKEN` | 否 | - | ArgoCD API Token |
| `JENKINS_URL` | 否 | - | Jenkins 服务地址 |
| `JENKINS_TOKEN` | 否 | - | Jenkins API Token |
| `GITHUB_TOKEN` | 否 | - | GitHub Personal Access Token |
| `GLM_API_KEY` | 否 | - | GLM API 密钥 |

### 3.2 数据库初始化

首次部署需要初始化数据库：

```bash
# 使用 Docker Compose
cd docker
PGPASSWORD=nexusops psql -h localhost -U nexusops -d nexusops -f scripts/init-db.sql

# 或使用 Kubernetes
kubectl exec -it nexusops-postgres-0 -n nexusops -- \
  psql -U nexusops -d nexusops -f /docker-entrypoint-initdb.d/init.sql
```

### 3.3 Agent 配置

NexusOps 支持多种内置 Agent：

| Agent ID | 功能 | 依赖 |
|----------|------|------|
| `nexusops.chat` | 通用对话 | GLM API |
| `nexusops.k8s` | Kubernetes 操作 | Kubeconfig |
| `nexusops.git` | Git 操作 | GitHub Token |
| `nexusops.cicd` | CI/CD 操作 | Jenkins/ArgoCD |
| `nexusops.deploy` | 部署操作 | ArgoCD |
| `nexusops.cost` | 成本分析 | - |
| `nexusops.logs` | 日志分析 | - |
| `nexusops.dns` | DNS 管理 | Cloudflare Token |

### 3.4 SSL/TLS 配置

使用 Let's Encrypt 获取免费证书：

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d nexusops.yourdomain.com

# 自动续期
sudo certbot renew --dry-run
```

---

## 4. 故障排查

### 4.1 常见问题

#### 后端无法连接数据库

```bash
# 检查数据库状态
docker-compose -f docker/docker-compose.middleware.yml ps postgres

# 检查连接
PGPASSWORD=nexusops psql -h localhost -U nexusops -d nexusops -c "SELECT 1"

# 查看日志
docker-compose -f docker/docker-compose.middleware.yml logs postgres
```

#### 前端 502 错误

```bash
# 检查后端服务状态
sudo systemctl status nexusops-backend

# 检查端口
netstat -tlnp | grep 8000

# 查看 Nginx 日志
sudo tail -f /var/log/nginx/error.log
```

#### WebSocket 连接失败

```bash
# 检查 Nginx WebSocket 配置
sudo nginx -t

# 检查后端日志
journalctl -u nexusops-backend -f
```

#### Agent 调用失败

```bash
# 检查 Agent 注册状态
curl http://localhost:8000/api/v1/market

# 检查 GLM API 连接
curl -H "Authorization: Bearer $GLM_API_KEY" \
  https://open.bigmodel.cn/api/paas/v4/models
```

### 4.2 日志位置

| 服务 | 日志位置 |
|------|----------|
| 后端 | `journalctl -u nexusops-backend` |
| Nginx | `/var/log/nginx/` |
| PostgreSQL | `docker logs nexusops-postgres` |
| Redis | `docker logs nexusops-redis` |

### 4.3 健康检查

```bash
# 后端健康检查
curl http://localhost:8000/health

# 数据库健康检查
curl http://localhost:8000/api/v1/health/db

# 完整系统检查
curl http://localhost:8000/api/v1/health
```

### 4.4 性能调优

#### 后端

```bash
# 增加 Worker 数量（根据 CPU 核心数）
uvicorn app.main:app --workers 4

# 或在 Gunicorn 中使用 Uvicorn worker
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

#### PostgreSQL

```sql
-- 调整连接池
ALTER SYSTEM SET max_connections = 200;

-- 调整共享缓冲区
ALTER SYSTEM SET shared_buffers = '256MB';
```

#### Redis

```bash
# 调整最大内存
redis-cli CONFIG SET maxmemory 256mb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

---

## 5. 备份与恢复

### 5.1 数据库备份

```bash
# 手动备份
PGPASSWORD=nexusops pg_dump -h localhost -U nexusops nexusops > backup_$(date +%Y%m%d).sql

# 定时备份（crontab）
0 2 * * * PGPASSWORD=nexusops pg_dump -h localhost -U nexusops nexusops > /backup/nexusops_$(date +\%Y\%m\%d).sql
```

### 5.2 数据库恢复

```bash
# 恢复数据库
PGPASSWORD=nexusops psql -h localhost -U nexusops nexusops < backup_20260225.sql
```

---

## 6. 升级指南

### 6.1 标准升级流程

```bash
# 1. 备份数据库
make db-backup

# 2. 拉取新版本
git fetch --tags
git checkout v1.1.0

# 3. 更新后端依赖
cd backend && pip install -r requirements.txt

# 4. 运行数据库迁移（如有）
alembic upgrade head

# 5. 重新构建前端
cd ../frontend && npm ci && npm run build

# 6. 重启服务
sudo systemctl restart nexusops-backend
```

### 6.2 滚动升级（Kubernetes）

```bash
# 更新镜像版本
kubectl set image deployment/nexusops-backend \
  backend=your-registry/nexusops-backend:v1.1.0 \
  -n nexusops

# 监控升级状态
kubectl rollout status deployment/nexusops-backend -n nexusops

# 回滚（如需要）
kubectl rollout undo deployment/nexusops-backend -n nexusops
```

---

## 7. 联系支持

- **文档**: https://docs.nexusops.io
- **问题反馈**: https://github.com/your-org/nexusops/issues
- **邮件支持**: support@nexusops.io
