# OpenCode 指南

> 开源终端 AI 编码助手

## 安装

```bash
# 官方脚本 (推荐)
curl -fsSL https://opencode.ai/install | bash

# npm
npm install -g opencode-ai

# Homebrew (macOS/Linux)
brew install anomalyco/tap/opencode

# Arch Linux
sudo pacman -S opencode           # Stable
paru -S opencode-bin              # Latest from AUR

# Windows - Chocolatey
choco install opencode

# Windows - Scoop
scoop install opencode

# Docker
docker run -it --rm ghcr.io/anomalyco/opencode
```

## 配置

### 配置文件位置

OpenCode 使用 JSON/JSONC 配置文件，按优先级加载：

| 优先级 | 位置 | 作用域 |
|--------|------|--------|
| 1 | `OPENCODE_CONFIG_CONTENT` env | 运行时覆盖 |
| 2 | `.opencode/` 目录 | 项目级 agents/commands/plugins |
| 3 | `opencode.json` (项目根) | 项目设置 |
| 4 | `OPENCODE_CONFIG` env | 自定义配置 |
| 5 | `~/.config/opencode/opencode.json` | 用户全局 |
| 6 | `.well-known/opencode` | 组织默认 |

### 基础配置

```jsonc
// opencode.json 或 ~/.config/opencode/opencode.json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "anthropic/claude-sonnet-4-5",
  "autoupdate": true,
  "server": {
    "port": 4096
  }
}
```

### 支持的模型

```jsonc
{
  // Anthropic
  "model": "anthropic/claude-sonnet-4-5",
  "model": "anthropic/claude-opus-4",

  // OpenAI
  "model": "openai/gpt-4o",
  "model": "openai/o1",

  // Google
  "model": "google/gemini-2.0-flash",

  // 本地模型
  "model": "ollama/llama3.2"
}
```

## NexusOps 特定配置

### AGENTS.md

OpenCode 自动读取项目根目录的 `AGENTS.md`。NexusOps 已有此文件，无需额外配置。

### 项目配置示例

```jsonc
// opencode.json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "anthropic/claude-sonnet-4-5",
  "autoupdate": true,
  "permissions": {
    "allow": [
      "Bash(cd backend && pytest *)",
      "Bash(cd frontend && npm run *)"
    ],
    "deny": [
      "Read(.env)",
      "Read(.env.*)"
    ]
  }
}
```

### 初始化 AGENTS.md

```bash
# 在 OpenCode 中运行
/init

# 这会扫描项目并生成/更新 AGENTS.md
```

## 常用命令

| 命令 | 说明 |
|------|------|
| `opencode` | 启动交互式会话 |
| `opencode "explain auth.py"` | 直接提问 |
| `opencode --help` | 查看帮助 |
| `/init` | 初始化/更新 AGENTS.md |
| `/compact` | 压缩对话历史 |
| `/clear` | 清空当前会话 |
| `/model` | 切换模型 |
| `/config` | 查看配置 |

## 提示词技巧

### 1. 利用 AGENTS.md

OpenCode 会自动读取 AGENTS.md，确保项目信息完整：

```markdown
# AGENTS.md 已包含
- 项目结构
- 构建命令
- 代码规范
```

### 2. 指定工作目录

```
在 backend/app/services/ 目录下，为 AgentService 添加缓存
```

### 3. 引用现有模式

```
参考 evolve/patterns/error-handling.md，
为新的 API 端点添加错误处理
```

### 4. 请求验证

```
实现后运行 pytest tests/services/test_agent.py 验证
```

## 目录结构

OpenCode 支持项目级扩展：

```
.opencode/
├── agents/           # 自定义 agents
├── commands/         # 自定义命令
├── modes/            # 自定义模式
├── plugins/          # 插件
├── skills/           # 技能
└── tools/            # 工具
```

### 自定义命令示例

```markdown
<!-- .opencode/commands/test.md -->
运行项目测试：
1. cd backend
2. pytest tests/ -v --cov=app
```

## 故障排除

### 模型不可用

```bash
# 检查 API key
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY

# 在 OpenCode 中切换模型
/model
```

### 配置不生效

```bash
# 检查配置加载顺序
/config

# 验证 JSON 语法
cat opencode.json | jq .
```

### AGENTS.md 未被读取

```bash
# 确保文件在项目根目录
ls -la AGENTS.md

# 重新初始化
/init
```

## OpenClaw 集成

NexusOps 使用 [OpenClaw](https://docs.openclaw.ai/) 作为 AI agent 网关。OpenClaw 与 OpenCode 是互补的：

| 工具 | 角色 |
|------|------|
| OpenCode | 终端 AI 编码助手（开发时使用） |
| OpenClaw | 自托管 agent 网关（运行时 agent 执行） |

OpenClaw 配置位于 `openclaw/` 目录：
- `openclaw/openclaw.json` — agent 定义
- `openclaw/workspace/skills/` — 每个 agent 的 SKILL.md

```bash
# 启动 OpenClaw（随中间件）
cd docker && docker-compose -f docker-compose.middleware.yml up -d

# 让后端通过 OpenClaw 执行 agents
export OPENCLAW_GATEWAY_URL=http://localhost:18789
```

## 相关资源

- [官方文档](https://opencode.ai/docs/)
- [GitHub 仓库](https://github.com/anomalyco/opencode)
- [配置参考](https://opencode.ai/docs/config/)
- [规则系统](https://opencode.ai/docs/rules/)
- [OpenClaw 文档](https://docs.openclaw.ai/)
