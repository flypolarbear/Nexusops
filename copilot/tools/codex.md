# OpenAI Codex 指南

> OpenAI 代码生成模型

## 概述

OpenAI Codex 现已集成到多种产品中：
- **GitHub Copilot** - 基于 Codex 的代码补全
- **OpenAI API** - 直接调用 gpt-4 / o1 模型
- **Aider** - 终端 AI 编码工具

## 使用方式

### 1. GitHub Copilot (推荐)

Codex 能力已集成到 GitHub Copilot，参见 [github-copilot.md](./github-copilot.md)。

### 2. OpenAI API

```bash
# 设置 API Key
export OPENAI_API_KEY="your-api-key"

# 使用 curl 测试
curl https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "解释这段代码"}]
  }'
```

### 3. Aider (终端工具)

```bash
# 安装
pip install aider-chat

# 或使用 pipx
pipx install aider-chat

# 启动
aider --model gpt-4o
```

## Aider 配置

### 安装

```bash
# pip
pip install aider-chat

# pipx (推荐)
pipx install aider-chat

# Homebrew
brew install aider
```

### 基础使用

```bash
# 启动并添加文件
aider backend/app/services/agent_service.py

# 指定模型
aider --model o1

# 使用 Claude
aider --model claude-3-5-sonnet-20241022
```

### AGENTS.md 支持

Aider 读取根目录的 `AGENTS.md`：

```markdown
# AGENTS.md
## 项目说明
NexusOps - AI 原生运维平台

## 代码规范
- Python: Black + Ruff + mypy
- TypeScript: Strict mode
- 禁止: as any, @ts-ignore
```

## NexusOps 特定配置

### Aider 配置文件

```bash
# .aider.conf.yml
model: gpt-4o
map-tokens: 2048
auto-commits: false
dirty-commits: true
```

### 常用命令

```bash
# 添加文件到上下文
/add backend/app/services/agent_service.py

# 查看差异
/diff

# 撤销更改
/undo

# 清除历史
/clear

# 帮助
/help
```

## 提示词技巧

### 1. 明确文件范围

```
在 backend/app/api/routes/ 中创建 health check 端点
```

### 2. 引用现有代码

```
参考 backend/app/api/routes/auth.py 的模式，
创建 agent 管理端点
```

### 3. 请求测试

```
为 AgentService 添加单元测试，
使用 pytest 和 pytest-asyncio
```

### 4. 代码审查

```
审查 backend/app/services/agent_service.py 的错误处理
```

## 模型选择

| 模型 | 用途 | 特点 |
|------|------|------|
| `gpt-4o` | 通用编码 | 快速，成本低 |
| `o1` | 复杂推理 | 深度思考，高质量 |
| `o1-mini` | 快速推理 | 平衡速度与质量 |

```bash
# 使用 o1
aider --model o1

# 使用 gpt-4o
aider --model gpt-4o
```

## 故障排除

### API Key 问题

```bash
# 检查 key
echo $OPENAI_API_KEY

# 设置 key
export OPENAI_API_KEY="sk-..."
```

### 上下文过长

```
# 在 Aider 中
/clear    # 清除历史
/map      # 查看 token 使用

# 只添加必要文件
/add backend/app/services/agent_service.py
# 而不是
/add backend/
```

### 更改不符合预期

```
# 查看差异
/diff

# 撤销
/undo

# 更具体的提示
"只修改 AgentService 类的 generate_response 方法，
不要改动其他代码"
```

## 相关资源

- [OpenAI API 文档](https://platform.openai.com/docs)
- [Aider 文档](https://aider.chat/docs/)
- [Aider GitHub](https://github.com/paul-gauthier/aider)
- [AGENTS.md 标准](https://agents.md/)
