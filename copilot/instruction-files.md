# 指令文件格式对照

> 各 AI 编码工具支持的指令文件位置与格式

## 概述

AI 编码工具通过读取指令文件来理解项目上下文。不同工具支持不同的文件位置和格式。

---

## AGENTS.md - 跨工具标准

**AGENTS.md** 已成为 AI 编码工具的事实标准：

- 网站: https://agents.md/
- 支持 15+ 工具: OpenCode, Cursor, VS Code Copilot, Claude Code, Codex, Gemini, Windsurf, Devin 等

### 位置

```
<项目根目录>/AGENTS.md
```

### 格式

```markdown
# 项目名称

## 项目概述
简要描述项目用途

## 技术栈
- 后端: ...
- 前端: ...

## 构建命令
- 启动: ...
- 测试: ...

## 代码规范
- 规则 1
- 规则 2

## 目录结构
说明主要目录用途
```

---

## 工具对照表

| 工具 | 主指令文件 | 备用文件 | 格式 |
|------|-----------|---------|------|
| **OpenCode** | `AGENTS.md` | - | Markdown |
| **Claude Code** | `CLAUDE.md` | `AGENTS.md` | Markdown |
| **Cursor** | `.cursor/rules/*.md` | `AGENTS.md` | Markdown |
| **GitHub Copilot** | `.github/copilot-instructions.md` | `AGENTS.md` | Markdown |
| **Codex / Aider** | `AGENTS.md` | `CODEX.md` | Markdown |
| **Gemini** | `GEMINI.md` | `AGENTS.md` | Markdown |

---

## 详细配置

### GitHub Copilot

```
项目根目录/
├── .github/
│   ├── copilot-instructions.md        # 全局指令
│   └── instructions/
│       ├── backend.instructions.md    # 路径特定
│       └── frontend.instructions.md
└── AGENTS.md                          # 备用
```

路径特定指令需要 YAML front matter：

```markdown
---
applyTo: "backend/**/*.py"
---

# Backend 指令
...
```

### Cursor

```
项目根目录/
├── .cursor/
│   └── rules/
│       ├── core.md
│       ├── backend.md
│       └── frontend.md
└── AGENTS.md
```

规则文件按文件类型自动激活。

### Claude Code

```
项目根目录/
├── CLAUDE.md                          # 主指令
├── AGENTS.md                          # 备用
└── .claude/
    └── settings.local.json            # 本地设置
```

### OpenCode

```
项目根目录/
├── AGENTS.md                          # 主指令
├── opencode.json                      # 配置
└── .opencode/
    ├── agents/
    ├── commands/
    └── skills/
```

---

## 优先级规则

### GitHub Copilot

1. 个人指令 (`~/.copilot/copilot-instructions.md`)
2. 路径特定 (`.github/instructions/*.instructions.md`)
3. 仓库全局 (`.github/copilot-instructions.md`)
4. AGENTS.md

### Cursor

1. `.cursor/rules/*.md` (项目级)
2. AGENTS.md
3. 用户全局设置

### Claude Code

1. 命令行参数
2. `.claude/settings.local.json`
3. `CLAUDE.md`
4. `AGENTS.md`
5. 全局配置 (`~/.claude/`)

---

## 保持同步策略

### 策略 1: AGENTS.md 为唯一来源

```
AGENTS.md ← 所有工具读取此文件
```

**优点**: 简单，无重复
**缺点**: 无法工具特定配置

### 策略 2: AGENTS.md + 工具特定文件

```
AGENTS.md ← 通用规则
├── .github/copilot-instructions.md ← Copilot 特定
├── .cursor/rules/ ← Cursor 特定
└── CLAUDE.md ← Claude 特定
```

**优点**: 各工具优化
**缺点**: 需要同步维护

### 策略 3: 符号链接 (不推荐)

```bash
# 创建符号链接
ln -s AGENTS.md CLAUDE.md
ln -s AGENTS.md .github/copilot-instructions.md
```

**优点**: 自动同步
**缺点**: 部分工具不支持

---

## 推荐配置

### 最小配置

只需 `AGENTS.md`：

```markdown
# NexusOps

## 技术栈
- FastAPI + SQLAlchemy async
- React 18 + TypeScript

## 构建
- 后端: cd backend && uvicorn app.main:app --reload
- 前端: cd frontend && npm run dev

## 规范
- 禁止 as any, @ts-ignore
- 所有 I/O 使用 async/await
```

### 完整配置

```
NexusOps/
├── AGENTS.md                          # 通用指令
├── .github/
│   └── copilot-instructions.md        # Copilot (可引用 AGENTS.md)
├── .cursor/
│   └── rules/
│       └── core.md                    # Cursor (可引用 AGENTS.md)
└── CLAUDE.md                          # Claude (可引用 AGENTS.md)
```

各工具文件内容：

```markdown
# 项目指令

参见 [AGENTS.md](../AGENTS.md) 获取完整项目说明。

## 工具特定配置
(可选的工具特定规则)
```

---

## 验证配置

### GitHub Copilot

```bash
# 检查文件
cat .github/copilot-instructions.md

# 在 VS Code Copilot Chat 中
@workspace 你知道项目的构建命令吗？
```

### Cursor

```bash
# 检查规则
ls -la .cursor/rules/

# 在 Cursor Chat 中
你知道项目的代码规范吗？
```

### Claude Code / OpenCode

```bash
# 检查 AGENTS.md
cat AGENTS.md

# 在工具中验证
/init  # 重新初始化
```
