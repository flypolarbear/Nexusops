# Plan: agentic_pact → copilot 转换

> Created: 2026-03-02
> Goal: 将 agentic_pact/ 重命名为 copilot/，重新定位为 AI 编码工具使用指南

## Research Summary

### 当前 agentic_pact/ 状态
- 仅包含 `index.md` (30 行)
- 内容：多 Agent 协作规范（任务锁定、证据提交）
- 实际用途有限

### 目标定位
copilot/ 目录将指导用户使用不同 AI 编码工具上手 NexusOps 项目：
- Claude Code (Anthropic)
- OpenCode (Open Source)
- Cursor (Anysphere)
- GitHub Copilot (Microsoft/GitHub)
- Codex (OpenAI)

### 行业标准发现

| 工具 | 主指令文件 | 备用文件 |
|------|-----------|---------|
| GitHub Copilot | `.github/copilot-instructions.md` | `AGENTS.md` |
| Claude Code | `CLAUDE.md` | `AGENTS.md` |
| Cursor | `.cursor/rules/` | `AGENTS.md` |
| OpenCode | `AGENTS.md` | - |
| Codex | `AGENTS.md` | `CODEX.md` |

**AGENTS.md 已成为跨工具标准** (https://agents.md/)

---

## Tasks

### Phase 1: 目录重构

- [x] 1.1 创建 `copilot/` 目录
- [x] 1.2 创建 `copilot/tools/` 子目录
- [x] 1.3 归档 `agentic_pact/` 到 `_archive/2026-03-02/`

### Phase 2: 创建工具指南

- [x] 2.1 创建 `copilot/tools/claude-code.md` - Claude Code 设置指南
- [x] 2.2 创建 `copilot/tools/opencode.md` - OpenCode 设置指南
- [x] 2.3 创建 `copilot/tools/cursor.md` - Cursor 设置指南
- [x] 2.4 创建 `copilot/tools/github-copilot.md` - GitHub Copilot 设置指南
- [x] 2.5 创建 `copilot/tools/codex.md` - OpenAI Codex 设置指南

### Phase 3: 创建通用指南

- [x] 3.1 创建 `copilot/index.md` - 总览与快速开始
- [x] 3.2 创建 `copilot/instruction-files.md` - 指令文件格式对照表
- [x] 3.3 创建 `copilot/best-practices.md` - AI 编码最佳实践
- [x] 3.4 创建 `copilot/faq.md` - 常见问题

### Phase 4: 更新引用

- [x] 4.1 更新 `AGENTS.md` 中的 agentic_pact 引用
- [x] 4.2 更新 `README.md` 中的链接
- [x] 4.3 更新 `docs/index.md` 中的引用
- [x] 4.4 更新 `.specify/memory/constitution.md` 中的引用
---

## Directory Structure (目标)

```
copilot/
├── index.md                    # 总览与快速开始
├── tools/
│   ├── claude-code.md          # Claude Code 设置与技巧
│   ├── opencode.md             # OpenCode 设置与技巧
│   ├── cursor.md               # Cursor 设置与技巧
│   ├── github-copilot.md       # GitHub Copilot 设置与技巧
│   └── codex.md                # OpenAI Codex 设置与技巧
├── instruction-files.md        # 指令文件格式对照
├── best-practices.md           # AI 编码最佳实践
└── faq.md                      # 常见问题
```

---

## Content Guidelines

### 每个工具指南应包含：
1. **安装与配置** - 如何安装和设置
2. **NexusOps 特定配置** - 项目相关的设置
3. **常用命令** - 日常使用的关键命令
4. **提示词技巧** - 针对此项目的有效提示词
5. **故障排除** - 常见问题与解决方案

### instruction-files.md 应包含：
- 各工具支持的指令文件位置
- 文件格式与优先级
- 如何保持多个文件同步
- 推荐的同步策略

### best-practices.md 应包含：
- 如何编写有效的提示词
- 上下文管理技巧
- 代码审查最佳实践
- 安全与隐私注意事项

---

## Naming Convention

遵循已有规范：
- 小写 + 连字符分隔
- 无前缀
- 简洁明了
