# 安装指南

## 系统要求

| 依赖 | 版本 |
|------|------|
| Python | 3.10+ |
| Node.js | 18.x+ |
| Docker | 20.10+ |
| PostgreSQL | 15+ |
| Redis | 7+ |

## 快速安装

### 1. 克隆项目

```bash
git clone https://github.com/your-org/nexusops.git
cd nexusops
```

### 2. 后端配置

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 环境变量

创建 `backend/.env`:

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/nexusops
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
DEBUG=true

# LLM Provider
OPENAI_API_KEY=sk-xxx
```

创建 `frontend/.env`:

```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### 4. 前端配置

```bash
cd frontend
npm install
```

### 5. 启动服务

```bash
# 使用 Makefile
make dev

# 或手动启动
# 终端1: 后端
cd backend && uvicorn app.main:app --reload --port 8000

# 终端2: 前端
cd frontend && npm run dev
```

## Docker 部署

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

## 验证安装

```bash
# 检查后端健康状态
curl http://localhost:8000/health

# 运行测试
cd backend && pytest tests/ -v
```

## 常见问题

### 端口占用

```bash
lsof -i :8000
kill -9 <PID>
```

### 数据库连接失败

确保 PostgreSQL 运行中，检查 `.env` 中的连接字符串。

### 依赖问题

```bash
# 重新安装
rm -rf node_modules package-lock.json
npm install
```
