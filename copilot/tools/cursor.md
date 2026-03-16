# Cursor 指南

> AI 原生代码编辑器

## 安装

```bash
# macOS
brew install --cask cursor

# Windows
winget install Cursor.Cursor

# Linux
# 下载: https://cursor.sh/downloads
```

## 配置

### .cursor/rules/ 目录

Cursor 使用 `.cursor/rules/` 目录存放规则文件：

```
.cursor/
└── rules/
    ├── core.md           # 核心规则
    ├── backend.md        # 后端规则
    ├── frontend.md       # 前端规则
    ├── testing.md        # 测试规则
    └── security.md       # 安全规则
```

### 规则文件示例

```markdown
<!-- .cursor/rules/core.md -->
# NexusOps 核心规则

## 项目概述
AI 原生运维平台，为多模态对话系统构建统一运维 Web 平台。

## 技术栈
- 后端: FastAPI + SQLAlchemy async + Pydantic v2
- 前端: React 18 + TypeScript + Zustand
- 数据库: PostgreSQL 15+ / Redis 7+

## 严格规则
1. 禁止使用 `as any` 或 `@ts-ignore`
2. 禁止空 catch 块
3. 所有 I/O 必须使用 async/await
4. 遵循 Black + Ruff 格式化规范
```

```markdown
<!-- .cursor/rules/backend.md -->
# 后端规则

## 目录结构
- `app/api/routes/` - API 路由
- `app/services/` - 业务逻辑
- `app/models/` - 数据模型
- `app/schemas/` - Pydantic schemas

## 命名规范
- 函数: snake_case
- 类: PascalCase
- 常量: UPPER_SNAKE_CASE

## 错误处理
参考: evolve/patterns/error-handling.md
```

## NexusOps 特定配置

### 创建规则目录

```bash
mkdir -p .cursor/rules
```

### 推荐规则文件

```
.cursor/rules/
├── core.md           # 项目核心信息
├── backend.md        # Python/FastAPI 规范
├── frontend.md       # TypeScript/React 规范
└── database.md       # PostgreSQL/Redis 规范
```

### 索引设置

在 Cursor 设置中启用代码库索引：

1. `Cmd/Ctrl + Shift + P` → "Cursor Settings"
2. 找到 "Codebase Indexing"
3. 确保以下目录被索引：
   - `docs/`
   - `evolve/`
   - `AGENTS.md`

## 常用快捷键

| 快捷键 | 功能 |
|--------|------|
| `Cmd/Ctrl + K` | 内联编辑 |
| `Cmd/Ctrl + L` | 打开 Chat |
| `Cmd/Ctrl + I` | Composer 模式 |
| `Cmd/Ctrl + Shift + P` | 命令面板 |
| `Tab` | 接受建议 |

## 提示词技巧

### 1. 使用 @ 符号引用

```
@backend/app/services/agent_service.py 添加缓存，
参考 @evolve/patterns/caching.md 的策略
```

### 2. 指定文件范围

```
在 @backend/app/api/routes/ 目录下创建新的 health 端点
```

### 3. 请求多个选项

```
为 AgentService 设计缓存方案，给我 3 个选项：
1. Redis 缓存
2. 内存缓存
3. 混合方案
```

### 4. 代码审查请求

```
审查 @backend/app/api/routes/auth.py 的安全性，
检查 JWT 实现是否符合 evolve/patterns/security.md
```

## Composer 模式

Composer 是 Cursor 的多文件编辑模式：

```
Cmd/Ctrl + I → 打开 Composer

示例提示：
"重构 AgentService，将缓存逻辑提取到独立的 CacheService，
更新所有引用，确保测试通过"
```

### Composer 最佳实践

1. **明确范围** - 指定要修改的文件
2. **分步请求** - 大改动分成小步骤
3. **验证结果** - 每步后运行测试

## 规则优先级

Cursor 按以下顺序读取规则：

1. `.cursor/rules/*.md` (项目级)
2. `AGENTS.md` (项目级)
3. 用户全局设置

## 故障排除

### 规则不生效

```bash
# 检查规则文件位置
ls -la .cursor/rules/

# 确保是 .md 格式
file .cursor/rules/*.md
```

### 索引问题

1. Cursor Settings → Codebase Indexing
2. 点击 "Reindex Codebase"
3. 等待索引完成

### 建议质量差

1. 检查规则文件是否完整
2. 确保相关文档被索引
3. 使用更具体的提示词

## 相关资源

- [官方文档](https://docs.cursor.sh/)
- [Cursor Rules 指南](https://docs.cursor.sh/context/rules)
- [Awesome CursorRules](https://github.com/PatrickJS/awesome-cursorrules)
- [Composer 文档](https://docs.cursor.sh/composer)
