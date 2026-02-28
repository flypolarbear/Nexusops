# OMO × Spec‑Kit Bridge Convention

本文件定义 **Spec‑Kit（模板/脚本驱动）** 与 **OMO（agent/harness 驱动）** 的
最小桥接约定，避免互相“打架”。

> 目标：让 Spec‑Kit 继续作为**规格与任务真相源**，让 OMO 作为**执行与编排引擎**。

---

## 1. 术语与职责

- **Spec‑Kit**：产出规范化制品（`spec.md`/`plan.md`/`tasks.md` 等），由模板与脚本驱动。
- **OMO**：负责任务编排、执行、验证（Sisyphus / Ralph / ulw）。

**核心职责划分**

| 领域 | 负责人 | 说明 |
|------|--------|------|
| 规格与计划 | Spec‑Kit | `specs/` 下的所有文档是唯一事实来源 |
| 执行与验证 | OMO | 读取 `tasks.md` 按任务执行并产出验证结果 |
| 变更 | Spec‑Kit | 规格、计划、任务的**修改必须通过 `/speckit.*`** |

---

## 2. 单一真相源（Source of Truth）

**Spec‑Kit 制品为唯一真相源**：

- `specs/<feature>/spec.md`
- `specs/<feature>/plan.md`
- `specs/<feature>/tasks.md`
- `specs/<feature>/research.md` / `data-model.md` / `contracts/` / `quickstart.md`

**禁止**：
- OMO 直接改写 `spec.md` / `plan.md` / `tasks.md`
- 在 ulw / ralph / Sisyphus 执行期间运行 `/speckit.specify` 或 `/speckit.plan`

---

## 3. 标准流程（Spec‑Kit → OMO）

### 3.1 Spec‑Kit 阶段（模板/脚本驱动）

1. `/speckit.constitution`（可选，但推荐）
2. `/speckit.specify` → 生成 `spec.md`
3. `/speckit.clarify`（如需澄清）
4. `/speckit.plan` → 生成 `plan.md` + `research.md` + `data-model.md` + `contracts/`
5. `/speckit.tasks` → 生成 `tasks.md`

**完成信号**：
- `specs/<feature>/tasks.md` 存在
- 所有 checklist 通过（如有）

### 3.2 OMO 阶段（agent/harness 驱动）

1. OMO 读取 `tasks.md`
2. 以任务为最小单元执行（Sisyphus 负责任务排程）
3. Ralph 负责验证与证据
4. ulw-loop 可用于长链路实现，但必须以 `tasks.md` 为输入

---

## 4. 关键桥接规则（必须遵守）

### 规则 A：只读规格
OMO 对 `specs/` 目录 **只读**，改动只能通过 `/speckit.*` 进行。

### 规则 B：阶段互斥
在 OMO 执行阶段禁止运行 `/speckit.*`（除非回到 Spec‑Kit 阶段重生成制品）。

### 规则 C：任务驱动
OMO 的执行单位必须是 `tasks.md` 中的任务；不得跳过或合并。若需变更任务，先回到
Spec‑Kit 生成新 `tasks.md`。

### 规则 D：桥接入口点
OMO 必须从 `tasks.md` 解析并构建执行图（Sisyphus graph）。不要直接从 `spec.md`
或 `plan.md` 生成任务。

---

## 5. OMO ↔ Spec‑Kit 对齐点（建议）

| Spec‑Kit 阶段 | OMO 行为 |
|--------------|----------|
| `spec.md` | 仅用于理解范围（只读） |
| `plan.md` | 仅用于结构与依赖参考 |
| `tasks.md` | 作为执行清单（唯一驱动） |
| `contracts/` | 作为 API 合约校验依据 |
| `quickstart.md` | 作为验证脚本来源 |

---

## 6. 实用桥接约定（简单可执行）

**约定 1**：执行前检查
- `tasks.md` 是否存在
- 所有 checklist 是否通过

**约定 2**：执行中记录
- 每完成一个任务，更新任务状态（由 OMO 负责）
- 验证证据写入测试输出（Ralph 负责）

**约定 3**：规格变更
- 如需调整范围 → 返回 Spec‑Kit 阶段，重跑 `/speckit.specify` 或 `/speckit.plan`

---

## 7. 常见冲突与解决方式

| 冲突 | 原因 | 解决方式 |
|------|------|----------|
| Spec‑Kit 与 OMO 同时改动任务 | 阶段未隔离 | 严格执行阶段互斥（规则 B） |
| OMO 直接修改 spec.md | 误把规格当执行输入 | 规格只读，回到 Spec‑Kit 重生成 |
| OMO 跳过 tasks.md | 执行驱动不一致 | 强制任务驱动（规则 C） |

---

## 8. 推荐执行顺序（示例）

```text
Spec‑Kit 阶段
  /speckit.specify → /speckit.plan → /speckit.tasks

OMO 阶段
  Sisyphus: 读取 tasks.md → 生成执行图
  ulw-loop: 执行任务
  Ralph: 验证 + 证据输出
```

---

## 9. 变更与维护

如桥接约定调整，需要：
1. 更新本文件
2. 同步到 `AGENTS.md`
3. 如有新钩子/约定，确保 Spec‑Kit 与 OMO 双方一致

---

## 10. Agent Mapping（全局调度规则）

定义 Spec‑Kit 各阶段到 OMO 专业 Agent 的分派规则。Sisyphus 在执行时自动查询此映射表。

### 10.1 Spec‑Kit 阶段 → Agent 映射

| 命令 | 阶段 | 子任务 | 主责 Agent | 辅助 Agent | 触发条件 |
|------|------|--------|-----------|-----------|----------|
| `/speckit.specify` | 全部 | 需求分析 | Sisyphus | - | 总是 |
| `/speckit.specify` | 澄清 | 歧义消除 | metis | - | 有 [NEEDS CLARIFICATION] |
| `/speckit.clarify` | 全部 | 需求澄清 | metis | - | 总是 |
| `/speckit.plan` | Phase 0 | 技术研究 | librarian | - | NEEDS CLARIFICATION 存在 |
| `/speckit.plan` | Phase 1 | 架构设计 | oracle | - | 复杂系统/多模块 |
| `/speckit.plan` | Phase 1 | 任务规划 | prometheus | - | 复杂任务分解 |
| `/speckit.plan` | Phase 1 | 计划审查 | momus | - | 总是（质量门） |
| `/speckit.plan` | Phase 1 | 文档撰写 | writing | - | 总是 |
| `/speckit.tasks` | 全部 | 任务分解 | Sisyphus | - | 总是（自己） |
| `/speckit.tasks` | 审查 | 一致性分析 | momus | - | 可选 |
| `/speckit.implement` | 执行 | 前端实现 | visual-engineering | - | 有 UI 任务 |
| `/speckit.implement` | 执行 | 复杂逻辑 | ultrabrain | - | 有算法/复杂逻辑 |
| `/speckit.implement` | 执行 | 快速修复 | quick | - | 单文件/简单修改 |
| `/speckit.implement` | 执行 | 代码审查 | oracle | momus | 完成后审查 |
| `/spec` (魔法命令) | 全流程 | 一键工作流 | Sisyphus | 所有专业 agent | 总是 |

### 10.2 Agent 职责说明

| Agent | 职责 | 适用场景 |
|-------|------|----------|
| **Sisyphus** | 编排与调度 | 主控 agent，负责整体流程编排 |
| **prometheus** | 任务规划师 | 从需求创建结构化计划、依赖编排 |
| **metis** | 预规划分析师 | 分析请求、识别歧义、发现 AI 失败点 |
| **oracle** | 高级技术顾问 | 复杂架构决策、调试、代码审查（只读） |
| **momus** | 计划审查员 | 计划审查、一致性检查、质量把关 |
| **librarian** | 外部资源研究员 | 外部文档查询、最佳实践查找 |
| **writing** | 文档撰写 | 生成各类文档材料 |
| **visual-engineering** | 前端工程 | UI/UX、样式、动画 |
| **ultrabrain** | 复杂逻辑 | 高难度逻辑任务 |
| **quick** | 快速任务 | 单文件修改、简单修复 |
| **explore** | 代码探索 | 代码库模式发现、结构理解 |

### 10.3 调度协议

**Sisyphus 执行流程：**

```
1. 识别当前阶段（命令 + 子任务）
2. 查询 Agent Mapping 表
3. 确定主责 Agent
4. 分派任务：
   task(subagent_type="{agent}", prompt="...上下文...")
5. 等待结果
6. 如需审查（momus），自动触发审查流程
7. 继续下一阶段
```

**审查流程（momus）：**

```
主责 Agent 完成 → 自动分派 momus → 
  momus 通过 → 继续
  momus 不通过 → 回主责 Agent 修正
```

### 10.4 调度脚本

Sisyphus 可调用 `.specify/scripts/bash/agent-dispatch.sh` 获取推荐 Agent：

```bash
# 用法
./agent-dispatch.sh <command> <phase> [activity]

# 示例
./agent-dispatch.sh speckit.plan research      # → librarian
./agent-dispatch.sh speckit.plan architecture  # → oracle
./agent-dispatch.sh speckit.plan review        # → momus
./agent-dispatch.sh speckit.implement frontend # → visual-engineering
```

### 10.5 命令级 handoffs（方案 A）

对于简单场景，命令文件中已配置 `handoffs`，Sisyphus 优先使用 handoffs。

复杂场景（多阶段、需审查）时，Sisyphus 查询本节的 Agent Mapping。

**优先级：**
1. 命令级 `handoffs`（简单场景）
2. 全局 Agent Mapping（复杂场景）
3. 默认：Sisyphus 自己处理

如桥接约定调整，需要：
1. 更新本文件
2. 同步到 `AGENTS.md`
3. 如有新钩子/约定，确保 Spec‑Kit 与 OMO 双方一致
