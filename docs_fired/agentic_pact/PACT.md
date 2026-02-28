# Agentic Engineering Pact

> **快速入门**: 请先阅读 [README.md](./README.md)

本公约定义多智能体协作的核心规则。工具无关，保持精简。

---

## 1. 核心角色

| 角色 | 职责 | 产出 |
|------|------|------|
| **协调者** | 任务分派、冲突解决、质量门禁 | 汇总报告、验收报告 |
| **规格师** | 编写规格、定义验收标准 | SPEC 文件 |
| **实现者** | 编码实现、自测验证 | 代码、测试 |
| **验证者** | 独立验证、记录证据 | 证据文件 |
| **审查者** | 代码审查、风险评估 | Review 意见 |

---

## 2. 必需制品

| 制品 | 位置 | 用途 |
|------|------|------|
| **Spec** | `specs/SPEC-*.md` | 功能规格和验收标准 |
| **Task List** | `state/task_list.json` | 任务列表和进度 |
| **Lock Registry** | `state/lock_registry.json` | 防止并发冲突 |
| **Evidence** | `evidence/PRD-XXX/` | 完成证据 |
| **ADR** | `adr/ADR-*.md` | 架构决策记录 |

---

## 3. 协作流程

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ 1.领取  │ → │ 2.锁定  │ → │ 3.实现  │ → │ 4.验证  │ → │ 5.提交  │
│ 任务    │    │ 登记    │    │ 编码    │    │ 证据    │    │ 归档    │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
      │              │              │              │              │
      ▼              ▼              ▼              ▼              ▼
 task_list.json  lock_registry   你的编辑器   evidence/    更新状态
```

---

## 4. 锁规则

1. **唯一性**: 一个任务同时只能有一个活跃锁
2. **必需字段**: task_id, owner, timestamp, status
3. **默认 TTL**: 24 小时
4. **强制接管**: 需书面说明原因

**锁状态**:
- `active` - 进行中
- `released` - 已释放
- `expired` - 已过期（可被接管）

---

## 5. 完成定义 (DoD)

任务完成 = 以下全部满足:

- [ ] 实现符合规格
- [ ] 测试通过
- [ ] 证据已记录到 `evidence/`
- [ ] `task_list.json` 状态更新
- [ ] 会话已总结
- [ ] 锁已释放

---

## 6. 会话连续性

**会话开始**: 在 `state/session_log.md` 添加会话头

```markdown
## Session: YYYY-MM-DD-XX
- Owner: 名字
- Purpose: 目的
- Status: Active

## Context
- 关键上下文
```

**会话结束**: 添加总结和下一步

```markdown
## Summary
- 完成了什么

## Next Steps
- 下一步做什么
```

---

## 7. 异常处理

### Hotfix 流程

允许跳过规格，但必须:

1. 事后补写 SPEC 文件
2. 在 task_list.json 记录
3. 在 session_log.md 说明原因

### 任务阻塞

1. 在 task_list.json 标记 `blocked`
2. 说明阻塞原因
3. 寻求帮助或切换任务

---

## 8. Git 提交规范

**提交时机**:
- 单个任务完成并验证后
- 重大架构决策确定后
- 里程碑完成后

**提交格式**:
```
<type>(<scope>): <description> [<task-id>]

type: feat|fix|refactor|docs|test|chore
```

**禁止**: 累积多个任务后一次性提交

---

## 9. 质量门禁

代码合并前必须通过:

- [ ] 单元测试通过
- [ ] 代码审查通过
- [ ] 证据文件完整
- [ ] 无未解决的阻塞问题

---

## 10. 模板索引

| 模板 | 用途 |
|------|------|
| `templates/SPEC_TEMPLATE.md` | 功能规格 |
| `templates/TASK_LIST_TEMPLATE.json` | 任务列表 |
| `templates/TEST_EVIDENCE_TEMPLATE.md` | 测试证据 |
| `templates/ADR_TEMPLATE.md` | 架构决策 |
| `templates/SESSION_LOG_TEMPLATE.md` | 会话记录 |

---

## 11. 工具适配

### OpenCode / Claude Code
- 自动读取 `AGENTS.md` 和 `README.md`
- 直接用自然语言指令操作

### Cursor
- 在 `.cursorrules` 引用本公约
- 使用 Chat 进行任务协作

### 其他工具
- 手动维护 `state/` 目录文件
- 遵循文件格式规范

---

## 12. 冲突解决

规则优先级（从高到低）:

1. 本文件 (PACT.md)
2. 具体规格 (specs/SPEC-*.md)
3. 架构决策 (adr/ADR-*.md)
4. 历史会话 (state/session_log.md)

---

## 附录 A: 目录结构

```
agentic_pact/
├── README.md              # 快速入门（从这里开始）
├── PACT.md               # 本文件 - 核心公约
├── state/                # 运行时状态
│   ├── task_list.json
│   ├── lock_registry.json
│   └── session_log.md
├── specs/                # 功能规格
├── templates/            # 文件模板
├── evidence/             # 完成证据
└── adr/                  # 架构决策
```

---

## 附录 B: EXO 团队模式 (高级)

对于支持多 Agent 并行的工具（如 OpenCode），可采用 EXO 团队模式：

```
                    ┌─────────────────────────────────────┐
                    │         Coordinator                  │
                    │  - 总控协调、质量门禁、最终汇总       │
                    └─────────────────┬───────────────────┘
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            │                         │                         │
            ▼                         ▼                         ▼
    ┌───────────────┐         ┌───────────────┐         ┌───────────────┐
    │    Architect   │         │   Developer   │         │      QA       │
    │               │         │               │         │               │
    │ - PRD/Spec    │         │ - 实现方案    │         │ - 测试策略    │
    │ - 架构方向    │         │ - 代码质量    │         │ - E2E测试     │
    │ - 里程碑规划  │         │ - 技术债务    │         │ - 质量门禁    │
    └───────────────┘         └───────────────┘         └───────────────┘
```

**并行工作原则**:
- 复杂任务（>3步）使用并行模式
- 单文件修改、快速修复使用单 Agent
- Coordinator 负责聚合输出、解决冲突
