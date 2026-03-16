# GitHub Copilot 指南

> GitHub 官方 AI 编码助手

## 安装

### VS Code

1. 打开扩展市场
2. 搜索 "GitHub Copilot"
3. 点击安装
4. 使用 GitHub 账号登录

### JetBrains IDEs

1. 打开 Settings → Plugins
2. 搜索 "GitHub Copilot"
3. 安装并重启
4. 使用 GitHub 账号登录

### 命令行 (Copilot CLI)

```bash
# npm
npm install -g @github/copilot-cli

# Homebrew
brew install github-copilot-cli

# 验证安装
gh copilot --version
```

## 配置

### .github/copilot-instructions.md

GitHub Copilot 自动读取此文件：

```markdown
# .github/copilot-instructions.md

## 项目概述
NexusOps 是 AI 原生运维平台。

## 技术栈
- 后端: FastAPI + SQLAlchemy async + Pydantic v2
- 前端: React 18 + TypeScript + Zustand
- 数据库: PostgreSQL 15+ / Redis 7+

## 构建命令
- 后端启动: `cd backend && uvicorn app.main:app --reload`
- 前端启动: `cd frontend && npm run dev`
- 运行测试: `cd backend && pytest tests/ -v`

## 代码规范
- Python: Black 格式化，Ruff lint，mypy strict
- TypeScript: Strict mode，@/ 路径别名
- 禁止: `as any`，`@ts-ignore`，空 catch 块

## 错误处理
遵循 evolve/patterns/error-handling.md 中的模式
```

### 路径特定指令

```
.github/
├── copilot-instructions.md        # 全局指令
└── instructions/
    ├── backend.instructions.md    # backend/ 目录指令
    ├── frontend.instructions.md   # frontend/ 目录指令
    └── api.instructions.md        # API 相关指令
```

```markdown
<!-- .github/instructions/backend.instructions.md -->
---
applyTo: "backend/**/*.py"
---

# Backend 指令

## 命名规范
- 函数: snake_case
- 类: PascalCase

## 异步模式
- 所有数据库操作使用 async/await
- 使用 SQLAlchemy async session

## 错误处理
参考: evolve/patterns/error-handling.md
```

## NexusOps 特定配置

### 创建配置文件

```bash
mkdir -p .github/instructions
```

### 推荐结构

```
.github/
├── copilot-instructions.md           # 项目级指令
├── instructions/
│   ├── backend.instructions.md       # Python/FastAPI
│   ├── frontend.instructions.md      # React/TypeScript
│   └── database.instructions.md      # PostgreSQL/Redis
└── prompts/                          # 可复用提示词 (VS Code)
    ├── create-api.prompt.md
    └── add-tests.prompt.md
```

## 常用命令

### VS Code

| 命令 | 功能 |
|------|------|
| `Cmd/Ctrl + I` | 打开 Copilot Chat |
| `Tab` | 接受内联建议 |
| `Esc` | 拒绝建议 |
| `Alt + [` | 上一个建议 |
| `Alt + ]` | 下一个建议 |

### Copilot CLI

```bash
# 解释代码
gh copilot explain "backend/app/services/agent_service.py"

# 建议代码
gh copilot suggest "Add JWT authentication to FastAPI endpoint"

# 聊天
gh copilot chat
```

## 提示词技巧

### 1. 使用 @workspace

```
@workspace 解释 AgentService 的缓存策略
```

### 2. 引用文件

```
@backend/app/api/routes/auth.py 添加 token 刷新端点
```

### 3. 请求测试

```
为 @backend/app/services/agent_service.py 生成单元测试
```

### 4. 代码审查

```
审查这个 PR 的安全性，检查：
1. SQL 注入风险
2. 认证绕过
3. 敏感数据泄露
```

### 5. 文档生成

```
为 AgentService.generate_response() 生成 docstring
```

## 指令文件优先级

GitHub Copilot 按以下顺序读取指令：

1. **个人指令** - `~/.copilot/copilot-instructions.md`
2. **组织指令** - 组织级别设置
3. **路径特定** - `.github/instructions/*.instructions.md`
4. **仓库全局** - `.github/copilot-instructions.md`
5. **AGENTS.md** - 根目录 AGENTS.md

## Copilot Agents

GitHub Copilot 支持 coding agents：

```markdown
<!-- .github/agents/backend.agent.md -->
---
name: Backend Developer
description: FastAPI 后端开发专家
---

你是一位 FastAPI 专家，专注于：
- 异步数据库操作
- Pydantic 数据验证
- 错误处理模式
- API 设计最佳实践
```

## 故障排除

### 建议不相关

1. 检查 `copilot-instructions.md` 是否存在
2. 确保文件格式正确
3. 重新加载 VS Code 窗口

### CLI 认证失败

```bash
# 重新认证
gh auth login

# 检查状态
gh auth status
```

### 指令文件未加载

```bash
# 确认文件位置
ls -la .github/copilot-instructions.md

# 检查文件格式
cat .github/copilot-instructions.md
```

## 相关资源

- [官方文档](https://docs.github.com/en/copilot)
- [自定义指令](https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot)
- [Copilot CLI](https://docs.github.com/en/copilot/using-github-copilot/using-github-copilot-in-the-command-line)
- [Awesome Copilot](https://github.com/github/awesome-copilot)
