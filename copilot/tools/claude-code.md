# Claude Code 指南

> Anthropic 官方终端 AI 编码助手

## 安装

```bash
# macOS / Linux / WSL
curl -fsSL https://claude.ai/install.sh | bash

# Homebrew (macOS/Linux)
brew install --cask claude-code

# npm (已弃用，推荐原生安装)
npm install -g @anthropic-ai/claude-code
```

## 配置

### API Key 设置

```bash
# 方式 1: 环境变量 (推荐)
export ANTHROPIC_API_KEY="your-api-key-here"

# 方式 2: 添加到 shell 配置
echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### 模型选择

```bash
# Claude Sonnet 4.6 - 最佳编码模型
export ANTHROPIC_MODEL="claude-sonnet-4-6"

# Claude Opus 4.6 - 最高质量，1M 上下文
export ANTHROPIC_MODEL="claude-opus-4-6"
```

## NexusOps 特定配置

### CLAUDE.md

项目根目录已有 `AGENTS.md`，Claude Code 会自动读取。如需 Claude 专用配置，可创建 `CLAUDE.md`：

```markdown
# NexusOps - Claude Code 配置

## 项目上下文
- 类型: AI 原生运维平台
- 后端: FastAPI + SQLAlchemy async
- 前端: React 18 + TypeScript + Zustand

## 构建命令
- 后端: `cd backend && uvicorn app.main:app --reload`
- 前端: `cd frontend && npm run dev`
- 测试: `cd backend && pytest tests/ -v`

## 代码规范
- Python: Black + Ruff + mypy strict
- TypeScript: Strict mode, @/ 路径别名
- 禁止: as any, @ts-ignore, 空 catch 块
```

### MCP 服务器 (可选)

```json
// ~/.claude/claude_desktop_config.json
{
  "mcpServers": {
    "postgres": {
      "command": "uvx",
      "args": ["mcp-server-postgres"],
      "env": {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/nexusops"
      }
    }
  }
}
```

## 常用命令

| 命令 | 说明 |
|------|------|
| `claude` | 启动交互式会话 |
| `claude "fix the auth bug"` | 直接提问 |
| `claude --help` | 查看帮助 |
| `/init` | 初始化 CLAUDE.md |
| `/compact` | 压缩对话历史 |
| `/cost` | 查看本次会话成本 |
| `/permissions` | 管理权限设置 |

## 提示词技巧

### 1. 明确上下文

```
# 好的提示
在 backend/app/api/routes/auth.py 中添加 JWT 刷新 token 端点，
遵循现有的 error-handling.md 模式

# 差的提示
添加刷新 token
```

### 2. 引用文档

```
根据 docs/api/errors.md 中的错误码规范，
为新的 agent-invocation 端点添加错误处理
```

### 3. 分步请求

```
# 第一步
分析 backend/app/services/ 目录下的服务层结构

# 第二步
基于分析结果，为 AgentService 添加缓存层
```

### 4. 验证请求

```
实现后运行 cd backend && pytest tests/ -v 验证
```

## 权限模式

```bash
# 自动接受所有读取操作
claude --allowedTools "Read(*)"

# 交互模式 (默认)
claude

# 仅建议模式 (不执行)
claude --dry-run
```

## 故障排除

### API Key 无效

```bash
# 检查 key 是否设置
echo $ANTHROPIC_API_KEY

# 验证 key 格式 (应以 sk-ant- 开头)
```

### 上下文过长

```
# 使用 /compact 压缩历史
/compact

# 或开始新会话
/exit
claude
```

### 权限被拒绝

```bash
# 检查文件权限
ls -la backend/

# 或在 Claude Code 中
/permissions
```

## 相关资源

- [官方文档](https://docs.anthropic.com/claude-code)
- [Claude Code Guide (社区)](https://github.com/Cranot/claude-code-guide)
- [MCP 服务器列表](https://github.com/modelcontextprotocol/servers)
