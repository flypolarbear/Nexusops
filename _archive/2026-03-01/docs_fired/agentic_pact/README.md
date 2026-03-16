# VibeCoding 工作流规范

> **目标**: 让使用不同 AI 编码工具（OpenCode、Claude Code、Cursor、Windsurf 等）的团队成员都能快速理解并参与项目协作。

---

## 快速入门 (30秒)

```
┌─────────────────────────────────────────────────────────────────┐
│                     VibeCoding 工作流                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   1. 领任务 → 2. 写代码 → 3. 提证据 → 4. 更新状态               │
│       ↓              ↓              ↓              ↓            │
│   lock_registry   你的编辑器   evidence/     task_list.json     │
│                                                                 │
│   核心原则: 一次只做一个任务，做完再领下一个                      │
└─────────────────────────────────────────────────────────────────┘
```

**开始前必读**:
1. 查看 `state/task_list.json` 找到待办任务
2. 在 `state/lock_registry.json` 登记你要做的任务
3. 完成后在 `evidence/` 目录提交证据

---

## 目录结构

```
agentic_pact/
├── README.md              # 👈 你在这里
├── PACT.md               # 详细公约（进阶阅读）
│
├── state/                # 📋 运行时状态（必须实时更新）
│   ├── task_list.json    # 任务列表 + 进度
│   ├── lock_registry.json # 任务锁定（防止冲突）
│   ├── session_log.md    # 会话记录
│   └── progress_log.md   # 进度日志
│
├── specs/                # 📄 功能规格（做什么）
│   └── SPEC-*.md         # 每个功能一个规格文件
│
├── templates/            # 📝 模板（复制使用）
│   ├── SPEC_TEMPLATE.md
│   ├── TASK_LIST_TEMPLATE.json
│   ├── TEST_EVIDENCE_TEMPLATE.md
│   └── ADR_TEMPLATE.md
│
├── evidence/             # ✅ 验收证据（做完提交）
│   └── PRD-XXX/          # 按 PRD 分组
│       └── MK-XXX-*.md   # 任务完成证据
│
├── adr/                  # 🏗️ 架构决策记录
│   └── ADR-*.md
│
└── reference/            # 📚 参考资料
    ├── workflow/         # 工作流设计
    └── design/           # 架构设计
```

---

## 核心工作流

### Step 1: 领取任务

```bash
# 1. 查看可用任务
cat agentic_pact/state/task_list.json | grep '"status": "pending"'

# 2. 在 lock_registry.json 登记锁定
# 格式:
{
  "locks": [
    {
      "task_id": "MK-001",
      "owner": "你的名字/工具名",
      "timestamp": "2026-02-27T10:00:00Z",
      "status": "active",
      "note": "简要说明你要做什么"
    }
  ]
}
```

### Step 2: 执行任务

1. **阅读规格**: 找到对应的 `specs/SPEC-*.md` 文件
2. **编写代码**: 使用你喜欢的工具（OpenCode/Claude Code/Cursor）
3. **本地验证**: 运行测试、构建确保通过

### Step 3: 提交证据

```bash
# 在 evidence/PRD-XXX/ 目录创建证据文件
# 文件名格式: {TASK_ID}-{描述}.md

# 证据文件内容:
# - 做了什么
# - 如何验证（测试命令、截图路径）
# - 结果（通过/失败）
```

### Step 4: 更新状态

```json
// task_list.json 更新任务状态
{
  "id": "MK-001",
  "status": "completed",  // 或 "in_progress"
  "completed_at": "2026-02-27"
}

// lock_registry.json 释放锁
{
  "task_id": "MK-001",
  "status": "released",
  "note": "完成原因"
}
```

---

## 不同工具适配指南

### OpenCode / Claude Code 用户

```markdown
# 系统会自动读取 AGENTS.md 和本文件
# 直接告诉 AI:
"请帮我完成 MK-001 任务，规格在 specs/SPEC-MK-001.md"

# 完成后:
"请在 evidence/PRD-001/ 创建 MK-001-完成证据.md"
```

### Cursor 用户

```markdown
# 在 .cursorrules 或 Chat 中指定:
"遵循 agentic_pact/README.md 的工作流规范"

# 领取任务时:
"我要做 MK-001，请帮我更新 lock_registry.json"

# 完成时:
"请帮我更新 task_list.json 并创建证据文件"
```

### Windsurf / 其他 IDE 用户

```markdown
# 手动操作:
1. 读取 specs/SPEC-*.md 了解任务
2. 手动更新 state/lock_registry.json
3. 编写代码
4. 手动创建 evidence/ 文件
5. 手动更新 state/task_list.json
```

---

## 核心规则

### 🔒 锁规则 (Lock Rules)

1. **一次一个锁**: 每个任务只能有一个活跃锁
2. **必须登记**: 开始前必须在 `lock_registry.json` 登记
3. **默认 TTL**: 24 小时，超时可被接管
4. **强制接管**: 需要写明原因

### ✅ 完成定义 (Definition of Done)

任务完成 = 以下全部满足:

- [ ] 代码实现符合规格
- [ ] 测试通过
- [ ] 证据文件已提交到 `evidence/`
- [ ] `task_list.json` 状态已更新
- [ ] 锁已释放

### 🚫 禁止事项

- 不要同时锁定多个任务
- 不要跳过证据提交
- 不要直接修改 `specs/` 中的已定稿规格
- 不要在锁超时前接管他人任务

---

## 文件模板速查

### 任务列表 (task_list.json)

```json
{
  "project": "项目名",
  "updated_at": "2026-02-27",
  "tasks": [
    {
      "id": "MK-001",
      "title": "任务标题",
      "status": "pending",
      "priority": "P0",
      "owner": "",
      "acceptance_criteria": ["验收标准1", "验收标准2"]
    }
  ]
}
```

### 证据文件 (evidence/*.md)

```markdown
# Test Evidence: MK-001

## 环境
- Date: 2026-02-27
- Commit: abc123

## 验证步骤
1. 运行 `pytest tests/unit/test_xxx.py`
2. 检查输出

## 结果
- [x] 测试通过
- [x] 覆盖率 >= 80%

## 截图/日志
- 路径: test_results/mk-001/
```

### 架构决策 (adr/*.md)

```markdown
# ADR-001: 决策标题

## Status
Accepted

## Context
背景和问题

## Decision
做出的决定

## Consequences
影响和后果
```

---

## 常见场景

### 场景 1: 开始新任务

```bash
1. git pull  # 确保最新
2. 查看 state/task_list.json 选择任务
3. 更新 state/lock_registry.json 锁定
4. 阅读 specs/SPEC-*.md 了解规格
5. 开始编码
```

### 场景 2: 任务完成

```bash
1. 运行测试确保通过
2. 创建 evidence/PRD-XXX/MK-XXX-evidence.md
3. 更新 state/task_list.json (status: completed)
4. 更新 state/lock_registry.json (status: released)
5. git add . && git commit -m "feat: 完成 MK-XXX"
```

### 场景 3: 任务阻塞

```bash
1. 在 evidence/ 创建阻塞说明文件
2. 更新 task_list.json 添加 blocked 状态
3. 在 lock_registry.json 说明阻塞原因
4. 寻求帮助或切换其他任务
```

### 场景 4: 紧急修复 (Hotfix)

```bash
1. 直接修复（可以先不写规格）
2. 事后补写 specs/SPEC-HOTFIX-XXX.md
3. 更新 task_list.json 添加 hotfix 记录
4. 在 session_log.md 记录原因
```

---

## 进阶阅读

- `PACT.md` - 完整的协作公约
- `adr/ADR-*.md` - 架构决策记录
---

## 快速参考卡片

```
┌────────────────────────────────────────────────────────────┐
│                    VibeCoding 速查表                        │
├────────────────────────────────────────────────────────────┤
│ 📋 任务列表    state/task_list.json                        │
│ 🔒 锁登记      state/lock_registry.json                    │
│ 📄 规格文件    specs/SPEC-*.md                             │
│ ✅ 证据目录    evidence/PRD-XXX/                            │
│ 📝 模板        templates/                                   │
├────────────────────────────────────────────────────────────┤
│ 工作流: 领任务 → 锁定 → 编码 → 证据 → 释放                  │
│ 原则: 一次一个任务，证据驱动，状态同步                       │
└────────────────────────────────────────────────────────────┘
```
