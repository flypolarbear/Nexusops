# Spec: PRD-001-EXEC - NexusOps Delivery Breakdown (Dev + QA)

## 1. Summary
本文件将 `SPEC-PRD-001` 拆解为开发与测试可直接执行的任务包，目标是让团队在无额外口头澄清下即可并行推进。

## 2. Goals
1. 将 PRD 转化为可排期、可验收、可追踪的交付单元。
2. 明确每个交付单元的依赖关系、输出物与 DoD。
3. 建立“功能验收 + 稳定性验收 + 兼容性验收”统一口径。

## 3. Workstreams
### WS-1: Gateway Core
1. 统一入口与路由中间件。
2. 请求/响应标准化与错误映射。
3. 限流、重试、熔断、观测链路。

### WS-2: Built-in Agents
1. K8s 状态检索 Agent。
2. Manifest 生成 Agent。
3. Log 查询 Agent。
4. Cost 计算 Agent。
5. DNS Agent（阿里云/Cloudflare）。
6. CI/CD Agent（Jenkins/ArgoCD）。
7. Git Repo Agent。

### WS-3: Ecosystem Foundation
1. 第三方 Agent 注册、安装、调用最小闭环。
2. Agent Manifest 合约校验。
3. SDK/文档/示例 Agent 最小可用版本。

### WS-4: QA & Reliability
1. 合约测试与集成测试基线。
2. 异常注入测试（超时、非法 JSON、下游失败）。
3. 端到端 UAT 脚本。

## 4. Atomic Delivery Packages
### P0（必须先完成）
1. PKG-001 Gateway Invocation Contract
Output:
- `/invoke` 请求/响应契约实现
- 错误码规范与 trace_id
DoD:
- 合约测试全通过
- 文档化请求示例与错误示例

2. PKG-002 Agent Executor Plugin Boundary
Output:
- FastAPI 内核 + executor 接口
- 内置/第三方统一 adapter
DoD:
- 至少一个内置 Agent 和一个第三方 mock Agent 跑通同一链路

3. PKG-003 Registry + Install Flow (MVP)
Output:
- 注册/下线/版本切换 API
- 安装与启停状态
DoD:
- 第三方 Agent 完成注册 -> 安装 -> 调用 -> 返回结构化结果

### P1（首版验收）
1. PKG-004 Built-in Agent Batch A
Scope:
- K8s / Manifest / Logs
DoD:
- 3 类 Agent 均具备可调用、可追踪、可失败诊断

2. PKG-005 Built-in Agent Batch B
Scope:
- Cost / DNS / CI-CD / Git（至少完成 3 类，优先 DNS + CI-CD）
DoD:
- 累计满足“至少 6 类内置 Agent 可用闭环”

3. PKG-006 Compatibility Adapters
Scope:
- Jenkins + ArgoCD + Aliyun DNS + Cloudflare DNS
DoD:
- 每个适配器有“成功 + 失败 + 限流”三类测试样例

### P2（二期演进）
1. PKG-007 SDK & Dev Docs
2. PKG-008 Store 运营化能力（评分/评论/推荐）
3. PKG-009 细粒度权限与配额策略中心

## 5. Team Ownership Model
1. Backend Squad
- PKG-001/002/003/006 主责

2. Agent Squad
- PKG-004/005 主责

3. QA Squad
- WS-4 全项主责，参与所有 PKG 验收

4. DX/Docs Squad
- PKG-007 主责

## 6. Definition of Done (Global)
1. 功能通过：功能点按 PRD 验收项满足。
2. 契约通过：输入输出 Schema 与错误模型符合约定。
3. 可观测：关键调用有日志、trace_id、耗时、结果状态。
4. 可回滚：新能力可按 Agent/版本禁用或回切。
5. 可交接：文档、测试证据、已知风险完整。

## 7. Milestone Gates
1. Gate-A (Platform Ready)
- PKG-001/002/003 完成
- 第三方 Agent MVP 跑通

2. Gate-B (Core Capability Ready)
- 至少 6 类内置 Agent 闭环可用
- Jenkins/ArgoCD/DNS 关键链路稳定

3. Gate-C (Scale Ready)
- SDK 与文档可外部使用
- 生态接入稳定，无需核心研发逐单支持

## 8. Risk Register
1. 风险：外部 API 不稳定导致整体 SLA 下降
- 缓解：超时 + 熔断 + 部分结果返回

2. 风险：不同 Agent 返回格式不统一
- 缓解：Gateway 严格 schema 校验 + 修复重试

3. 风险：高风险动作误执行（DNS/发布）
- 缓解：受控操作白名单 + 二次确认（二期）

4. 风险：生态扩张后治理不足
- 缓解：按 ADR-002 分阶段升级权限、审计、配额
