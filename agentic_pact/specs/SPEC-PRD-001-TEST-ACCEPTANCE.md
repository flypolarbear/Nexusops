# Spec: PRD-001-QA - Test and Acceptance Plan

## 1. Summary
本测试文档定义 NexusOps PRD-001 的统一验收标准，覆盖 Gateway、内置 Agent、第三方 Agent 接入与关键外部系统兼容。

## 2. Test Scope
1. Gateway 统一调用链路
2. Agent Registry 与安装流程
3. 内置 Agent（至少 6 类）
4. 外部系统适配（Jenkins/ArgoCD/Aliyun DNS/Cloudflare DNS）
5. 异常与稳定性场景

## 3. Test Environments
1. `dev`：快速回归与接口联调
2. `staging`：端到端与故障注入
3. `pre-prod`（可选）：上线前最终验证

## 4. Acceptance KPIs
1. 端到端成功率（正常场景）>= 95%
2. 非法输入拦截率 = 100%
3. 可追踪率（含 trace_id 的调用）= 100%
4. 首版至少 6 类内置 Agent 达到“可调用 + 可诊断 + 可回滚”
5. 第三方 Agent 最小闭环成功（注册 -> 安装 -> 调用 -> 结构化返回）

## 5. Test Matrix
### 5.1 Gateway
1. GW-T01 正常调用路由到内置 Agent
2. GW-T02 正常调用路由到第三方 Agent
3. GW-T03 无效 `agent_id` 返回标准化错误
4. GW-T04 限流触发返回明确错误码
5. GW-T05 下游超时触发重试并记录重试轨迹
6. GW-T06 下游返回非法 JSON 时被拦截并标注可诊断信息

### 5.2 Registry / Install
1. RG-T01 注册合法 Manifest 成功
2. RG-T02 注册非法 Manifest 失败并返回字段级错误
3. RG-T03 安装已注册 Agent 成功并可调用
4. RG-T04 下线 Agent 后调用被拒绝

### 5.3 Built-in Agents
1. AG-K8S-T01 资源状态查询成功
2. AG-MANI-T01 Manifest 生成输出符合 schema
3. AG-LOG-T01 日志查询返回时间窗内结果
4. AG-COST-T01 成本查询按项目维度返回
5. AG-DNS-T01 阿里云 DNS 记录创建成功（受控测试域名）
6. AG-DNS-T02 Cloudflare DNS 记录更新成功（受控测试域名）
7. AG-CICD-T01 Jenkins 触发构建并回传状态
8. AG-CICD-T02 ArgoCD 同步触发并回传状态
9. AG-GIT-T01 Git 仓库基础操作成功（只读或受控写入）

### 5.4 Reliability / Chaos
1. RL-T01 外部 API 网络抖动
2. RL-T02 第三方 Agent 返回 5xx
3. RL-T03 并发操作同一 DNS 记录冲突
4. RL-T04 调用链路中断后可恢复

## 6. Evidence Requirements
1. 每个测试用例必须输出：
- 请求样例（脱敏）
- 响应样例（脱敏）
- 日志路径或 trace_id
- 结论（Pass/Fail）与失败原因
2. 证据文件统一使用模板：
- `agentic_pact/templates/TEST_EVIDENCE_TEMPLATE.md`

## 7. Exit Criteria
1. P0/P1 用例通过率 >= 95%，且 P0 不允许失败。
2. 所有 blocker 缺陷关闭或有明确回避策略。
3. 关键链路（Jenkins/ArgoCD/DNS）具备可复现验收证据。
4. UAT 由 DevOps/SRE 与研发代表签字通过。

## 8. Known Deferrals
1. Store 评分/评论相关测试延后到二期。
2. 企业级合规项（细粒度审计导出、组织级多租户隔离）延后到后续阶段。
