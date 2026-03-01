# Feature Specification: Spec-Kit × OMO 工作流整理与文档化

**Feature Branch**: `005-spec-kit-omo-workflow`  
**Created**: 2026-03-02  
**Status**: Draft  
**Input**: User description: "帮我创建一个计划搞清晰整理当前的 spec-kit opencode omo 的工作流"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 开发者快速上手工作流 (Priority: P1)

作为一名刚加入项目的开发者（或 AI Agent），我想在 10 分钟内理解 Spec-Kit → OMO 的完整工作流程，
知道每个阶段该用哪个命令、产出哪些制品、以及由谁负责执行。

**Why this priority**: 这是最基础的需求。没有清晰的工作流文档，新成员（包括 AI Agent）都无法正确地开始工作，所有后续流程都依赖于此。

**Independent Test**: 给一名从未接触本项目的人（或 AI Agent）提供整理后的文档，让他们独立完成从 `/speckit.specify` 到 OMO 执行触发的完整流程，验证是否成功，无需额外询问。

**Acceptance Scenarios**:

1. **Given** 一名新开发者/Agent 拿到整理后的工作流文档，**When** 按照文档执行 `/speckit.specify → /speckit.plan → /speckit.tasks`，**Then** 能在不查阅其他文档的情况下生成全套制品
2. **Given** 开发者完成 Spec-Kit 阶段，**When** 切换到 OMO 执行阶段，**Then** 能清楚地知道触发入口、输入来源（`tasks.md`）、及执行模式（ulw-loop/Ralph/Sisyphus）
3. **Given** 开发者遇到"是否应该在 OMO 执行中修改 spec？"的疑问，**When** 查阅工作流文档，**Then** 在 30 秒内找到明确答案（规则 B：阶段互斥）

---

### User Story 2 - AI Agent 自动调度正确的专业 Agent (Priority: P2)

作为 Sisyphus（主控 Agent），在 Spec-Kit 各阶段执行时，我需要知道每个子任务应该分派给哪个专业 Agent（prometheus、oracle、metis、momus 等），以保证工作流的质量与一致性。

**Why this priority**: Agent 分派规则直接影响执行质量。如果 Sisyphus 不清楚何时调用 momus 做质量审查、何时调用 oracle 做架构决策，会导致制品质量不稳定。

**Independent Test**: 在 `/speckit.plan` 执行时，Sisyphus 能根据整理后的 Agent Mapping 准确分派各子任务到对应 Agent，不依赖人工干预。

**Acceptance Scenarios**:

1. **Given** Sisyphus 执行 `/speckit.plan` 的研究阶段，**When** 遇到技术选型问题，**Then** 自动分派给 `librarian` Agent 而非自己处理
2. **Given** Sisyphus 完成计划草稿，**When** 需要质量把关，**Then** 自动触发 `momus` 审查，且审查不通过时自动回主责 Agent 修正
3. **Given** Sisyphus 查阅 Agent Mapping，**When** 遇到前端实现任务，**Then** 分派给 `visual-engineering` 而非通用执行

---

### User Story 3 - 规格变更时保持制品一致性 (Priority: P3)

作为项目维护者，当需求在 OMO 执行中途发生变更时，我需要一个明确的流程返回 Spec-Kit 阶段更新规格，而不是直接修改执行中的任务，确保 `spec.md`、`plan.md`、`tasks.md` 三者始终保持一致。

**Why this priority**: 工作流中最常见的问题是"边执行边改规格"，这会导致制品不一致，引发不可追踪的执行错误。

**Independent Test**: 模拟中途变更场景，验证开发者能按照文档走"变更流程"（停止 OMO → 回 Spec-Kit 重生成 → 重启 OMO），而非直接改 `tasks.md`。

**Acceptance Scenarios**:

1. **Given** OMO 执行进行到一半，**When** 发现需求有误需要变更，**Then** 文档明确指出需要"停止 OMO → 返回 Spec-Kit → 重跑 `/speckit.specify` 或 `/speckit.plan`"
2. **Given** 开发者想直接修改 `tasks.md` 跳过 Spec-Kit，**When** 查阅工作流规则，**Then** 文档明确标注该行为违反规则 C（任务驱动）并说明后果

---

### Edge Cases

- 当 `tasks.md` 不存在时，OMO 尝试启动执行会发生什么？（应有明确的前置检查约定）
- 当 Spec-Kit 某个命令中途失败（如 `/speckit.plan` 未完成），如何恢复状态？
- 当多个 Agent 同时读取同一 Spec-Kit 制品时，如何保证一致性？

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 文档系统必须提供端到端的工作流说明，覆盖 Spec-Kit 的 5 个阶段命令及其产出制品
- **FR-002**: 文档系统必须明确说明 Spec-Kit 制品是唯一事实来源，OMO 对 `specs/` 目录只读，任何改动只能通过 `/speckit.*` 命令进行
- **FR-003**: 文档系统必须提供完整的 Agent Mapping 表，列出每个 Spec-Kit 命令/阶段对应的主责 Agent、辅助 Agent 及触发条件
- **FR-004**: 文档系统必须包含 4 条关键桥接规则（只读规格、阶段互斥、任务驱动、桥接入口点）及每条规则的违规反例
- **FR-005**: 文档系统必须提供标准执行顺序示例（Spec-Kit 阶段 → OMO 阶段的完整流程说明）
- **FR-006**: 文档系统必须说明规格变更的正确流程：OMO 执行中途如何回退到 Spec-Kit 重生成制品
- **FR-007**: `AGENTS.md` 必须包含工作流快速参考（Agent Mapping 表和 `/spec` 魔法命令说明），确保 AI Agent 在启动时即可获取关键调度信息

### Key Entities

- **Spec-Kit 命令**：每个命令的触发时机、产出制品、责任 Agent——命令间的先后依赖关系
- **OMO 执行模式**：Sisyphus（编排）、ulw-loop（长链路执行）、Ralph（验证+证据）
- **制品层级**：spec.md（需求）→ plan.md（设计）→ tasks.md（执行单元）→ 验证证据
- **Agent 角色**：prometheus、oracle、metis、momus、librarian、writing、visual-engineering、ultrabrain——职责边界与调度触发条件

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 新成员（或 AI Agent）能在 10 分钟内独立完成从 `/speckit.specify` 到 OMO 执行触发的完整流程，无需额外询问
- **SC-002**: Agent 分派错误率为零——所有 Spec-Kit 命令执行时，Sisyphus 均能正确分派专业 Agent，无需人工干预纠正
- **SC-003**: 工作流执行中不再出现 tasks.md 与 spec.md 内容脱节的问题，制品一致性 100%
- **SC-004**: 工作流文档覆盖所有桥接规则，开发者遇到任何决策点时都能找到明确指引

---

## Assumptions

- 现有的 `OMO_SPEC.md` 和 `AGENTS.md` 是主要整理对象，而非从零创建
- 文档的主要受众是 AI Agent（Sisyphus 及专业子 Agent），其次是人类开发者
- `/spec` 魔法命令已通过 `.opencode/command/spec.md` 实现，本 feature 只需确保文档中有清晰说明
- `agent-dispatch.sh` 脚本已存在并经过验证，本 feature 的重点是文档一致性，而非脚本功能扩展