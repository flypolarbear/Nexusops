# Architect + Dev 双 Agent 协作 Runbook

## 1. 目标
使用两个 Agent 并行推进 PRD-001：
1. `architect`（高级模型）负责设计、评审、风险决策。
2. `dev`（低成本模型）负责实现、测试、提交证据。

## 2. 固定分工
### architect 负责
1. 领取并拆解任务（SPEC/ADR/接口契约）。
2. 定义 DoD、测试口径、风险边界。
3. 审查 dev 产出，给出 pass/rework 结论。

### dev 负责
1. 按 SPEC 实现代码与测试。
2. 提交变更摘要与自测结果。
3. 归档 evidence，并回传 architect 审查。

## 3. 执行节奏（一个任务循环）
1. Architect 领锁：
   - 更新 `agentic_pact/state/lock_registry.json` 为 `active`
2. Architect 产出设计输入：
   - 更新 `agentic_pact/specs/SPEC-*.md`
   - 必要时新增 `agentic_pact/adr/ADR-*.md`
3. Dev 开发：
   - 依据 SPEC 实现
   - 补测试并执行
4. Dev 交付：
   - 更新 `agentic_pact/state/progress_log.md`
   - 提交 evidence（`agentic_pact/evidence/PRD-001/`）
5. Architect 审查：
   - 结论写入 `agentic_pact/state/session_log.md`（pass/rework）
6. 任务关闭：
   - 更新 `task_list.json` 状态
   - 释放 lock（`released`）

## 4. 当前任务分配建议（PRD-001）
### Architect 主导
1. `MK-006` Gateway 契约与错误模型（先出接口与错误码）
2. `MK-007` Executor 插件边界（先出模块图与接口）
3. `MK-011` 最终验收标准与签收规则

### Dev 主导
1. `MK-008` 第三方 Agent 最小闭环实现
2. `MK-009` 内置 Agent 能力批次实现与自测
3. `MK-010` 兼容性联调与稳定性测试

## 5. 交接模板
### Architect -> Dev
1. 任务 ID：
2. 目标：
3. 非目标：
4. 接口契约（请求/响应/错误码）：
5. 测试必过项：
6. 回滚策略：

### Dev -> Architect
1. 任务 ID：
2. 变更文件：
3. 测试结果（命令 + 结论）：
4. 风险与已知问题：
5. evidence 路径：

## 6. 质量闸门
1. 无 SPEC 不开发。
2. 无测试结果不提审。
3. 无 evidence 不标记完成。
4. Architect 未签收不释放任务。

## 7. 建议日节奏（无硬截止场景）
1. 上午：Architect 产出/修订 SPEC，Dev 实现前一任务。
2. 下午：Dev 提审，Architect 评审并给下一轮输入。
3. 日终：更新 `progress_log.md` 与 `session_log.md`，清锁或续锁。
