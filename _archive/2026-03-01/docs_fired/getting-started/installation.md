# Installation Guide

## Overview

This guide covers the installation and setup of NexusOps Agent Development Environment. Follow these steps to prepare your development environment for building and testing agents.

## Prerequisites

### System Requirements

- **Operating System**: macOS 10.15+, Ubuntu 20.04+, or Windows 10+ with WSL2
- **Python**: 3.10 or higher
- **Node.js**: 18.x or higher (for frontend development)
- **Docker**: 20.10+ (for containerized development)
- **Git**: 2.30+

### Required Tools

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.10+ | Backend runtime |
| pip | 22.0+ | Package management |
| Poetry | 1.5+ | Dependency management (recommended) |
| Node.js | 18.x | Frontend runtime |
| npm/yarn | 9.x/1.22+ | Frontend package management |
| Docker | 20.10+ | Containerization |
| Docker Compose | 2.0+ | Multi-container orchestration |

---

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/nexusops.git
cd nexusops
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install
# or with yarn
yarn install
```

### 4. Environment Configuration

Create a `.env` file in the backend directory:

```bash
# Backend/.env
DATABASE_URL=postgresql://user:password@localhost:5432/nexusops
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
DEBUG=true
LOG_LEVEL=DEBUG

# LLM Provider Configuration
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
```

Create a `.env` file in the frontend directory:

```bash
# Frontend/.env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### 5. Database Setup

```bash
# Run database migrations
cd backend
alembic upgrade head

# Seed initial data (optional)
python scripts/seed_data.py
```

### 6. Start Development Servers

Using the provided Makefile:

```bash
# From project root
make dev
```

Or manually:

```bash
# Terminal 1: Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

---

## Docker Setup (Alternative)

For a containerized development environment:

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Docker Compose Services

| Service | Port | Description |
|---------|------|-------------|
| backend | 8000 | FastAPI backend |
| frontend | 5173 | Vite dev server |
| postgres | 5432 | PostgreSQL database |
| redis | 6379 | Redis cache |

---

## Verification

### 1. Check Backend Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### 2. Check Frontend

Open `http://localhost:5173` in your browser. You should see the NexusOps dashboard.

### 3. Run Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm run test
```

---

## IDE Setup

### VS Code (Recommended)

1. Install recommended extensions:
   - Python (Microsoft)
   - Pylance
   - ESLint
   - Prettier
   - Docker

2. Workspace settings (`.vscode/settings.json`):

```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

### PyCharm

1. Open the project as a Python project
2. Set the Python interpreter to the virtual environment
3. Enable Pylint and Black integration

---

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>
```

#### 2. Database Connection Failed

- Ensure PostgreSQL is running
- Check credentials in `.env`
- Verify database exists

```bash
# Create database if not exists
createdb nexusops
```

#### 3. Python Module Not Found

```bash
# Ensure virtual environment is activated
source backend/.venv/bin/activate

# Reinstall dependencies
pip install -r backend/requirements.txt
```

#### 4. Node Modules Issues

```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

---

## Next Steps

After completing the installation:

1. Read [Quick Start Guide](./quick-start.md) to create your first agent
2. Review [Architecture Overview](./architecture-overview.md) to understand the system design
3. Explore the [API Reference](../api-reference/gateway-api.md) for detailed API documentation

---

## Getting Help

- **Documentation**: `/docs` directory
- **Issues**: GitHub Issues
- **Community**: Discord/Slack channels
- **Email**: support@nexusops.io
