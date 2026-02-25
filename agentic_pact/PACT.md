# Agentic Engineering Pact (Draft)

This pact defines how multiple agent CLIs collaborate without conflicts, context loss, or partial delivery.
It is tool-agnostic and intentionally small enough to be adopted quickly.

## 1. Roles
- Orchestrator: owns intake, priority, and conflict resolution.
- Initializer: writes specs, defines acceptance, and breaks work into atomic tasks.
- Implementer: builds exactly one atomic task at a time.
- Verifier: independently validates the work and evidence.
- Reviewer: performs code and risk review before merge.

## 2. Required Artifacts
- Spec: a written specification for each feature.
- Task List: atomic tasks with test steps and pass/fail status.
- Lock Registry: single source of truth for active work.
- Session Log: current session header and end summary.
- ADR: architecture decisions when behavior changes.
- Test Evidence: screenshots or logs for verification.

## 3. Collaboration Flow
1. Intake: Orchestrator collects requirements and clarifies scope.
2. Spec: Initializer writes the spec and acceptance criteria.
3. Breakdown: Initializer creates atomic tasks and test steps.
4. Assign: Orchestrator assigns a single task per Implementer.
5. Implement: Implementer takes a lock, codes, and self-verifies.
6. Verify: Verifier validates end-to-end and records evidence.
7. Review: Reviewer checks quality and risk.
8. Closeout: update Task List, Session Log, release lock, commit.

## 4. Lock Rules
- Exactly one active lock per task.
- A lock must include owner, timestamp, and status.
- Default lock TTL is 24 hours.
- A lock can be taken over only with a written reason.

## 5. Definition of Done (DoD)
A task is complete only when:
- The implementation matches the spec.
- Tests and required checks are done.
- Evidence is recorded.
- The task is marked pass in Task List.
- The session is summarized.
- The lock is released.

## 6. Session Continuity
- Each session start must add a Session Header.
- Each session end must add a Session Summary and next steps.

## 7. Exceptions
- Hotfix is allowed only if logged and followed by a spec and task entry.

## 8. Templates
Templates are provided in `agentic_pact/templates/`.
State files are expected in `agentic_pact/state/`.

Default state files:
- `agentic_pact/state/task_list.json`
- `agentic_pact/state/lock_registry.json`
- `agentic_pact/state/session_log.md`
- `agentic_pact/state/progress_log.md`
- `agentic_pact/state/project_status.md`

## 9. EXO Team: Parallel Agent Workflow

EXO 是一个多智能体并行协作团队，采用 **Spec/PRD 驱动 + 并行研发 + 自动化测试 + 持续汇总** 的模式。

### 9.1 Team Structure

```
                    ┌─────────────────────────────────────┐
                    │         GLM (Executive Lead)        │
                    │  - 总控协调、质量门禁、最终汇总      │
                    └─────────────────┬───────────────────┘
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            │                         │                         │
            ▼                         ▼                         ▼
    ┌───────────────┐         ┌───────────────┐         ┌───────────────┐
    │     Elon      │         │     Ryan      │         │   Cynthia     │
    │  PM/Architect │         │  Full-Stack   │         │  QA/Testing   │
    │               │         │  Developer    │         │               │
    │ - PRD/Spec    │         │ - 实现方案    │         │ - 测试策略    │
    │ - 架构方向    │         │ - 代码质量    │         │ - E2E测试     │
    │ - 里程碑规划  │         │ - 技术债务    │         │ - 质量门禁    │
    └───────────────┘         └───────────────┘         └───────────────┘
```

### 9.2 Role Definitions

| Role | 身份 | 职责 | 产出 |
|------|------|------|------|
| **GLM** | Executive Lead | 总控协调、跨角色冲突解决、质量门禁、最终汇总 | 每日/里程碑汇总、验收报告 |
| **Elon** | PM + Architect | 需求澄清、PRD/Spec、架构方向、里程碑拆分 | PRD、架构文档、迭代计划 |
| **Ryan** | Full-Stack Dev | 实现方案、代码质量、接口契约、安全权限 | 代码提交、模块设计、运行手册 |
| **Cynthia** | QA Engineer | 测试用例、自动化测试、调试诊断、质量门禁 | 测试计划、Playwright工程、缺陷报告 |

### 9.3 Parallel Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         GLM: Task Dispatch                          │
│  1. 分析用户目标 → 拆分并行任务包                                    │
│  2. 设定每个任务的 DoD (验收标准 + 证据要求)                          │
└─────────────────────────────────────────────────────────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          │                         │                         │
          ▼                         ▼                         ▼
    ┌───────────┐             ┌───────────┐             ┌───────────┐
    │   Elon    │             │   Ryan    │             │  Cynthia  │
    │ 独立上下文 │             │ 独立上下文 │             │ 独立上下文 │
    │           │             │           │             │           │
    │ PRD研究   │             │ 代码分析  │             │ 测试评估  │
    │ 架构评估  │             │ 质量审计  │             │ 风险识别  │
    │ 规划制定  │             │ 方案设计  │             │ 策略建议  │
    └─────┬─────┘             └─────┬─────┘             └─────┬─────┘
          │                         │                         │
          └─────────────────────────┼─────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       GLM: Aggregation                              │
│  1. 聚合成员输出 → 解决冲突 → 形成统一决策                           │
│  2. 更新置顶文档 (research.md)                                       │
│  3. 发起 Release Readiness Review (如到达里程碑)                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.4 Output Files

| Agent | 输出文件 | 内容 |
|-------|---------|------|
| Elon | `exo_research/elon_findings.md` | PRD、架构、里程碑规划 |
| Ryan | `exo_research/ryan_findings.md` | 代码质量、实现方案、技术债务 |
| Cynthia | `exo_research/cynthia_findings.md` | 测试策略、E2E规划、质量门禁 |
| **GLM** | `research.md` | 汇总报告、决策、行动项 |

### 9.5 "先检索再行动" 规则

当出现以下情况，必须先检索 (网页 + GitHub):
- 新概念/新工具/不确定的最佳实践
- 关键安全/权限/合规问题
- 影响架构与长期维护的选型

**检索后仍不确定**: 在置顶文档写清问题点、已检索证据、备选方案、需要用户确认的点。

### 9.6 tmuxSplitPanes 监控

使用 tmux 分屏实时监控各 Agent 工作状态:

```
┌────────────────────────────────────────────────────────────────────┐
│                        GLM: Coordinator                            │
│  任务分派 | 冲突解决 | 质量门禁 | 最终汇总                           │
├─────────────────────┬─────────────────────┬────────────────────────┤
│        Elon         │        Ryan         │       Cynthia          │
│   PM/Architect      │   Full-Stack Dev    │   QA/Testing           │
│                     │                     │                        │
│  [PRD 进度]         │  [实现进度]         │  [测试进度]            │
│  [架构状态]         │  [代码质量]         │  [E2E 状态]            │
│  [里程碑]           │  [技术债务]         │  [质量门禁]            │
└─────────────────────┴─────────────────────┴────────────────────────┘
```

### 9.7 启动命令

```bash
# 启动 EXO 团队并行研究
# GLM 自动分派任务给 Elon/Ryan/Cynthia，然后汇总到 research.md
```

---

## 10. Operational Rules

### 10.1 Git Push at Stable Nodes
每个稳定任务节点必须进行 `git push`:
- **稳定节点定义**: 单个原子任务完成、测试通过、证据记录后
- **Push 时机**:
  - 单个 task 完成并验证通过后
  - 重大架构决策 (ADR) 确定后
  - 里程碑 (MK-xxx) 完成后
  - 每日结束前 (EOD)
- **Commit 格式**: `feat|fix|refactor|docs|test(scope): description [task-id]`
- **禁止**: 累积多个 task 后一次性 push

### 10.2 Always Enable Agent Team
始终启用 Agent Team 并行工作:
- **默认模式**: 所有复杂任务 (>3 steps) 使用 EXO Team 并行
- **单 Agent 仅用于**: 简单查询、单文件修改、快速修复
- **并行启动**: GLM 同时分派任务给 Elon/Ryan/Cynthia
- **汇总节点**: GLM 负责聚合输出、解决冲突、更新置顶文档

## 11. Recommended Usage
- Copy templates into active state files and keep them updated.
- Do not modify multiple tasks in one change set.
- All UI changes require visual evidence.
- Use EXO Team workflow for complex research and implementation tasks.
