# Spec: PRD-001 - NexusOps Core Product and Agent Ecosystem

## 1. Summary
NexusOps 是一个 AI Native 的运维与研发协作平台，核心目标是把 DevOps/SRE 与自助研发流程中的高频、重复、易错操作，沉淀为可调用的 Agent 能力，并通过统一 Gateway 对内置与第三方 Agent 提供一致接入。

本 PRD 覆盖完整 NexusOps 核心产品，不仅是 Agent Market/Gateway。首期重点是“平台能力稳定 + 通用接入逻辑稳定”，而不是先做重运营化商店功能。

## 2. Goals
1. 建立统一 Agent Gateway，支持内置 Agent 与第三方 Agent 的一致调用、鉴权、路由、观测。
2. 打通核心运维/研发场景的内置 Agent 能力闭环（查询、生成、执行、回写状态）。
3. 兼容现有系统（Jenkins、ArgoCD、Git、云服务、DNS 平台）并通过 Agent 适配层完成统一抽象。
4. 建立可扩展生态基础，允许后续第三方 Agent 安装、调用、版本演进。

## 3. Non-Goals
1. 首期不追求完整商业化能力（计费结算、复杂套餐、分账体系）。
2. 首期不做重运营社区能力（评分/评论/内容运营体系）。
3. 首期不强制高等级合规认证（在用户规模有限阶段采用“够用且可升级”的安全基线）。

## 4. User Stories
1. 作为 DevOps/SRE，我希望通过 Agent 快速定位 K8s 资源状态和异常原因，减少人工排障时间。
2. 作为研发同学，我希望通过自助入口完成 manifest 生成、日志检索、CI/CD 触发与状态查询，不依赖平台团队手工支持。
3. 作为平台工程师，我希望统一管理 Agent 接入协议和调用链路，避免每个功能各自实现。
4. 作为生态开发者，我希望按标准 Manifest 接入第三方 Agent，并在平台中被发现与调用。

## 5. Functional Requirements
### 5.1 平台与网关
1. 提供统一调用入口（同步 + 可扩展流式），支持请求标准化与响应标准化。
2. 提供 Agent Registry 基础能力：注册、下线、版本、健康状态。
3. 提供能力路由：按 `agent_id` 与版本规则转发到内置执行器或第三方执行端点。
4. 提供限流与熔断基础能力（按 Agent、按调用方）。
5. 提供结构化错误模型与重试策略（可配置最大重试次数与退避策略）。

### 5.2 内置 Agent 能力范围（首期打磨重点）
1. Kubernetes 信息状态检索（资源状态、事件、基础诊断）。
2. Manifest 文件生成与建议修复。
3. 日志查询与上下文关联（服务、环境、时间窗口）。
4. 云服务 Projects/Services 成本计算（先支持核心云账户视角）。
5. DNS 解析配置操作（首批适配阿里云与 Cloudflare）。
6. CI/CD 对接（Jenkins 与 ArgoCD 的触发、状态查询、结果回传）。
7. Git 仓库管理相关操作（只开放可控范围内动作）。

### 5.3 Agent Store（首期降优先级）
1. 首期仅提供“可发现 + 可安装 + 可调用验证”的最小闭环。
2. 评分/评论系统延后到二期。
3. 健康检查在首期提供基础状态，不做复杂运营面板。

## 6. Non-Functional Requirements
1. 稳定性优先于功能广度：Gateway 必须可观测、可回放、可定位问题。
2. 接口一致性：内置 Agent 与第三方 Agent 使用同一请求/响应契约。
3. 可演进：认证、隔离、审计、配额模型需可平滑升级，不返工核心调用路径。
4. 兼容性：以“通过 Agent 兼容既有系统”为原则，避免一次性替换存量系统。

## 7. Data Model / API Changes
1. Agent Manifest：
   - 基础身份：`agent_id`、`version`、`owner`、`category`
   - 契约声明：`input_schema`、`output_schema`
   - 运行与依赖：`endpoints`、`required_integrations`
2. Invoke API（统一）：
   - 入参：`request_id`、`agent_id`、`query`、`context`、`auth_context`
   - 出参：`status`、`content`、`structured_output`、`error`、`metadata`
3. Registry API：
   - 注册/更新/下线
   - 获取 Agent 详情与版本列表
   - 健康状态查询

## 8. UI/UX Notes
1. 首页/控制台强调“内置能力即开即用 + 第三方能力可接入”双主线。
2. Agent Store 首期采用工具化视图：搜索、安装、启停、调用测试。
3. 内置 Agent 需要提供可追踪的执行结果与下一步建议动作。

## 9. Edge Cases
1. 第三方 Agent 返回非法结构：Gateway 应统一报错并可按策略重试。
2. 外部系统超时/失败：返回部分结果并明确失败子步骤。
3. 同一资源并发操作冲突（如 DNS）：需要资源级互斥策略或串行队列。
4. 版本不兼容：支持并存版本与显式默认版本策略。

## 10. Acceptance Criteria
### 10.1 首版验收（MVP）
1. 至少 6 类内置 Agent 能力可稳定调用（K8s/Manifest/Logs/Cost/DNS/CI-CD/Git 中任选不少于 6 类完成可用闭环）。
2. 第三方 Agent 能完成一次“注册 -> 安装 -> 调用 -> 返回结构化结果”的端到端流程。
3. Jenkins 与 ArgoCD 集成链路可用，关键调用有可追踪日志。
4. 阿里云和 Cloudflare 的 DNS 操作能力可在受控范围执行并返回结果。
5. Gateway 在异常场景（超时、非法 JSON、下游错误）可给出可诊断错误信息。

### 10.2 二期验收（Ecosystem）
1. 稳定通用接入逻辑定型（文档、SDK、示例齐备）。
2. Store 补齐评级/评论等运营能力（若业务确认需要）。
3. 提供更细粒度配额/审计/策略中心能力。

## 11. Test Plan
1. 合约测试：对每个 Agent 的输入/输出 Schema 做自动校验。
2. 集成测试：Jenkins、ArgoCD、Aliyun DNS、Cloudflare DNS 的关键路径测试。
3. 混沌/异常测试：超时、网络抖动、外部 API 失败、非法响应。
4. 回归测试：内置 Agent 升级不得破坏统一调用契约。
5. UAT：由 DevOps/SRE 与研发代表完成场景化验收脚本。

## 12. Rollback Plan
1. Gateway 层保留按 Agent 与版本的快速禁用开关。
2. 新 Agent 灰度发布，异常时可回切到上一稳定版本。
3. 对高风险动作（DNS/CI-CD 触发）保留“只读模式/演练模式”降级能力。

## 13. Product Strategy Decisions (from 2026-02-24 alignment)
1. PRD 范围：覆盖整个 NexusOps 核心产品，不仅 Agent Market/Gateway。
2. 主用户：DevOps/SRE 与自助研发；同时开放第三方 Agent 生态。
3. 成功标准：首期重内置能力稳定与通用接入稳定，生态扩张在二期放量。
4. 时间约束：无硬截止日期，以兼容既有系统和稳定性为导向。
5. Store 优先级：前期降低，二期重点强化生态与接入逻辑。
