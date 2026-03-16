# NexusOps - AI Agent Entry Point

> 🤖 OpenCode / Claude Code / Cursor 入口文件

## Quick Context

| 项目 | 值 |
|------|-----|
| 类型 | AI 原生运维平台 |
| 后端 | FastAPI + SQLAlchemy async + Pydantic v2 |
| 前端 | React 18 + TypeScript + Zustand |
| 数据库 | PostgreSQL 15+ / Redis 7+ |

---

## Development Guidelines

遵循项目开发规范：
- **API-First Design** - 所有功能暴露 REST/WebSocket API
- **Async-First Architecture** - 全异步架构
- **Type Safety** - 严格类型检查
- **Test Coverage** - 70%+ 测试覆盖率

---

## Build Commands

```bash
# 后端
cd backend && uvicorn app.main:app --reload --port 8000
cd backend && pytest tests/ -v

# 前端
cd frontend && npm run dev
cd frontend && npm run build

# Docker
cd docker && docker-compose -f docker-compose.middleware.yml up -d
```

---

## Key References

| 内容 | 位置 |
|------|------|
| 用户文档 | [docs/](./docs/index.md) |
| 演进知识库 | [evolve/](./evolve/index.md) |
| AI 工具指南 | [copilot/](./copilot/index.md) |
| 开发流程 | [DEVELOPMENT_WORKFLOW.md](./DEVELOPMENT_WORKFLOW.md) |
---

## Code Style

### Backend (Python)
- Line length: 100 chars
- Formatter: Black
- Linter: Ruff + mypy strict
- Naming: `snake_case` for functions, `PascalCase` for classes

### Frontend (TypeScript)
- Strict mode enabled
- Path alias: `@/` for `src/`
- Naming: `PascalCase` for components, `camelCase` for functions

### Critical Rules
1. **Never** suppress type errors (`as any`, `@ts-ignore`)
2. **Always** use async/await for I/O
3. **Never** use empty catch blocks

---

## Testing & Verification (强制)

> ⚠️ 所有需求开发完成后必须执行

### 验证工具
- **Playwright**: E2E 自动化测试
- **Chrome DevTools**: 性能与功能验证
- **截图工具**: 实际效果存证

### 验证流程
1. 执行自动化测试套件
2. 确保测试覆盖度 ≥ 90%
3. 对关键功能进行截图验证
4. 归档测试证据至 `test-evidence/`
5. 记录测试结果和审计信息

### 证据要求
- 截图必须包含时间戳
- 测试日志必须完整保留
- 所有证据必须可追溯

---

## OpenClaw Integration

NexusOps agents run through [OpenClaw](https://docs.openclaw.ai/) — a self-hosted AI agent gateway.

| 组件 | 说明 |
|------|------|
| `openclaw/openclaw.json` | OpenClaw agent 配置（8个 NexusOps agents） |
| `openclaw/workspace/` | Agent workspace（AGENTS.md, SOUL.md, skills/） |
| `openclaw/workspace/skills/` | 每个 agent 的 SKILL.md 技能文件 |

### 启动 OpenClaw

```bash
# 随中间件一起启动
cd docker && docker-compose -f docker-compose.middleware.yml up -d

# 或单独启动
docker run -it --rm \
  -p 18789:18789 \
  -v ~/.openclaw:/home/node/.openclaw \
  -v $(pwd)/openclaw/workspace:/home/node/.openclaw/nexusops/workspace \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  ghcr.io/openclaw/openclaw:latest
```

### 启用 OpenClaw 路由

```bash
# 设置环境变量，后端将通过 OpenClaw 执行所有 agents
export OPENCLAW_GATEWAY_URL=http://localhost:18789
cd backend && uvicorn app.main:app --reload --port 8000
```

不设置 `OPENCLAW_GATEWAY_URL` 时，后端回退到内置 Python agent handlers。

---

## Project Structure

```
NexusOps/
├── AGENTS.md              # 本文件
├── openclaw/              # OpenClaw 配置与 workspace
│   ├── openclaw.json      # Agent 定义
│   └── workspace/         # Agent workspace + skills
├── docs/                  # 用户文档
├── evolve/                # 演进知识库
├── copilot/               # AI 工具指南
├── backend/               # FastAPI 后端
└── frontend/              # React 前端
```

---

## Active Work

任务状态：[copilot/](./copilot/index.md) 查看工具指南

---

## Knowledge Base

演进知识库：[evolve/](./evolve/index.md)

适用场景：
- 完成功能模块后总结模式
- 解决复杂 bug 后记录教训
- 做出重要技术决策后归档 ADR

## Active Technologies
- Python 3.11+ + FastAPI 0.100+, SQLAlchemy 2.0+ (async), Pydantic 2.0+, httpx
- PostgreSQL 15+ / Redis 7+
- OpenClaw (ghcr.io/openclaw/openclaw) — AI agent gateway on port 18789

## Recent Changes
- 001-skill-bridge-mvp: Integrated OpenClaw as agent execution backend
  - Added `openclaw/` workspace with 8 agent SKILL.md files
  - Added `OpenClawExecutor` in `backend/app/gateway/executor/openclaw.py`
  - `ExecutorRouter` routes through OpenClaw when `OPENCLAW_GATEWAY_URL` is set
  - Added OpenClaw service to `docker/docker-compose.middleware.yml`
