# AI Copilot 使用指南

> 帮助你使用各种 AI 编码工具上手 NexusOps 项目

## 快速开始

### 1. 选择你的工具

| 工具 | 类型 | 推荐场景 |
|------|------|----------|
| [Claude Code](./tools/claude-code.md) | 终端 | 深度代码理解、复杂重构 |
| [OpenCode](./tools/opencode.md) | 终端 | 开源方案、多模型支持 |
| [Cursor](./tools/cursor.md) | IDE | 日常开发、多文件编辑 |
| [GitHub Copilot](./tools/github-copilot.md) | IDE/云端 | VS Code 用户、团队协作 |
| [Codex](./tools/codex.md) | API/终端 | 自定义集成 |

### 2. 核心指令文件

NexusOps 使用 **AGENTS.md** 作为跨工具标准指令文件：

```
NexusOps/
├── AGENTS.md          # 主指令文件 (所有工具通用)
├── docs/              # 用户文档
├── evolve/            # 演进知识库
└── copilot/           # 本目录
```

### 3. 项目关键信息

```yaml
项目类型: AI 原生运维平台
后端: FastAPI + SQLAlchemy async + Pydantic v2
前端: React 18 + TypeScript + Zustand
数据库: PostgreSQL 15+ / Redis 7+

构建命令:
  后端: cd backend && uvicorn app.main:app --reload
  前端: cd frontend && npm run dev
  测试: cd backend && pytest tests/ -v

代码规范:
  - Python: Black + Ruff + mypy strict
  - TypeScript: Strict mode, @/ 路径别名
  - 禁止: as any, @ts-ignore, 空 catch 块
```

---

## 工具指南

### 终端工具

- **[Claude Code](./tools/claude-code.md)** - Anthropic 官方终端助手
  - 深度代码理解
  - MCP 服务器集成
  - 最佳编码质量

- **[OpenCode](./tools/opencode.md)** - 开源终端助手
  - 多模型支持 (Claude/GPT/Gemini/Ollama)
  - 可扩展架构
  - 社区驱动

- **[Codex (Aider)](./tools/codex.md)** - OpenAI 终端工具
  - GPT-4o / o1 支持
  - Git 集成
  - 简洁交互

### IDE 集成

- **[Cursor](./tools/cursor.md)** - AI 原生编辑器
  - 规则系统 (.cursor/rules/)
  - Composer 多文件编辑
  - 代码库索引

- **[GitHub Copilot](./tools/github-copilot.md)** - GitHub 官方助手
  - VS Code / JetBrains 集成
  - copilot-instructions.md 支持
  - Copilot CLI

---

## 通用资源

| 文档 | 说明 |
|------|------|
| [指令文件格式](./instruction-files.md) | 各工具指令文件对照表 |
| [最佳实践](./best-practices.md) | AI 编码通用技巧 |
| [常见问题](./faq.md) | 故障排除与 FAQ |

---

## 一键配置

### 创建工具特定配置

```bash
# GitHub Copilot
mkdir -p .github
cat > .github/copilot-instructions.md << 'EOF'
# NexusOps - GitHub Copilot 指令

## 项目
AI 原生运维平台

## 技术栈
- 后端: FastAPI + SQLAlchemy async
- 前端: React 18 + TypeScript + Zustand

## 规范
- 禁止 as any, @ts-ignore
- 所有 I/O 使用 async/await
EOF

# Cursor
mkdir -p .cursor/rules
cat > .cursor/rules/core.md << 'EOF'
# NexusOps 核心规则

## 技术栈
- 后端: FastAPI + SQLAlchemy async + Pydantic v2
- 前端: React 18 + TypeScript + Zustand

## 严格规则
1. 禁止 as any, @ts-ignore
2. 禁止空 catch 块
3. 所有 I/O 使用 async/await
EOF

# Claude Code (可选，AGENTS.md 已足够)
cat > CLAUDE.md << 'EOF'
# NexusOps - Claude Code 配置

参见 AGENTS.md 获取完整项目说明。
EOF
```

---

## 推荐工作流

### 1. 日常开发
```
Cursor → 编写代码 → GitHub Copilot → 补全建议
```

### 2. 复杂重构
```
Claude Code → 理解代码 → 规划重构 → 执行
```

### 3. 调试问题
```
OpenCode → 分析日志 → 定位问题 → 修复
```

### 4. 快速原型
```
GitHub Copilot Chat → 描述需求 → 生成代码 → 验证
```

---

## 获取帮助

- 查看 [FAQ](./faq.md) 解决常见问题
- 参考 [最佳实践](./best-practices.md) 提升效率
- 阅读 [指令文件格式](./instruction-files.md) 理解配置
