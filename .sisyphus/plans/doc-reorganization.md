# Plan: NexusOps 文档重组

> Created: 2026-03-01
> Goal: 重组文档架构，建立 docs/（用户文档）+ evolve/（演进知识库）+ 精简 AGENTS.md

## Principles

1. **新命名规范**: 全小写 + 连字符分隔，无前缀（SPEC-*, ADR-*）
2. **内容压缩**: 提取核心信息，删除冗余
3. **职责分离**: docs/ 面向用户，evolve/ 面向开发演进
4. **保留状态**: agentic_pact/state/ 保持运行时数据

---

## Tasks

### Phase 1: 创建目录骨架

- [x] 1.1 创建 docs/ 子目录 (start/, api/, guides/)
- [x] 1.2 创建 evolve/ 子目录 (patterns/, anti-patterns/, decisions/)
- [x] 1.3 创建 _archive/2026-03-01/ 归档目录

### Phase 2: 创建 docs/ 用户文档

- [x] 2.1 创建 docs/index.md - 文档导航首页
- [x] 2.2 创建 docs/start/install.md - 安装指南
- [x] 2.3 创建 docs/start/quickstart.md - 快速上手
- [x] 2.4 创建 docs/start/concepts.md - 核心概念与架构
- [x] 2.5 创建 docs/api/gateway.md - Gateway API 参考
- [x] 2.6 创建 docs/api/invoke.md - 调用接口合约
- [x] 2.7 创建 docs/api/errors.md - 错误码表
- [x] 2.8 创建 docs/guides/agent-dev.md - Agent 开发指南
- [x] 2.9 创建 docs/guides/contract.md - 请求响应合约
- [x] 2.10 创建 docs/guides/lifecycle.md - Agent 生命周期
- [x] 2.11 创建 docs/guides/testing.md - 测试指南

### Phase 3: 创建 evolve/ 演进知识库

- [x] 3.1 创建 evolve/index.md - 知识库导航
- [x] 3.2 创建 evolve/patterns/async-patterns.md - 异步处理模式
- [x] 3.3 创建 evolve/patterns/caching.md - 缓存策略模式
- [x] 3.4 创建 evolve/patterns/connection-pool.md - 连接池模式
- [x] 3.5 创建 evolve/patterns/error-handling.md - 错误处理模式
- [x] 3.6 创建 evolve/patterns/rate-limiting.md - 限流熔断模式
- [x] 3.7 创建 evolve/patterns/security.md - 安全实践模式
- [x] 3.8 创建 evolve/anti-patterns/avoid.md - 常见反模式
- [x] 3.9 创建 evolve/decisions/monolith-gateway.md - 架构决策
- [x] 3.10 创建 evolve/decisions/unified-contract.md - 合约决策
- [x] 3.11 创建 evolve/decisions/error-taxonomy.md - 错误分类决策

### Phase 4: 更新 AGENTS.md

- [x] 4.1 重写 AGENTS.md 为简洁索引格式

### Phase 5: 精简 agentic_pact/

- [x] 5.1 创建 agentic_pact/index.md - 协作说明
- [x] 5.2 精简 agentic_pact/pact.md（重命名自 PACT.md）
- [x] 5.3 重命名 session_log.md → sessions.md

### Phase 6: 归档与清理

- [x] 6.1 移动 docs_fired/ 到 _archive/2026-03-01/
- [x] 6.2 移动 agentic_pact/adr/ 到 evolve/decisions/（已提取）
- [x] 6.3 删除 agentic_pact/templates/（已废弃）
- [x] 6.4 更新 README.md 添加文档入口链接

---

## File Mapping Reference

| 源文件 | 目标文件 |
|--------|----------|
| docs_fired/getting-started/installation.md | docs/start/install.md |
| docs_fired/getting-started/quick-start.md | docs/start/quickstart.md |
| docs_fired/getting-started/architecture-overview.md | docs/start/concepts.md |
| docs_fired/api-reference/gateway-api.md | docs/api/gateway.md |
| docs_fired/agent-development/contract-specification.md | docs/api/invoke.md + docs/guides/contract.md |
| docs_fired/agent-development/error-handling.md | docs/api/errors.md |
| docs_fired/agent-development/agent-specification.md | docs/guides/agent-dev.md |
| docs_fired/agent-development/agent-lifecycle.md | docs/guides/lifecycle.md |
| docs_fired/agent-development/testing-guide.md | docs/guides/testing.md |
| docs_fired/best-practices/performance.md | evolve/patterns/async-patterns.md + caching.md + connection-pool.md + rate-limiting.md |
| docs_fired/best-practices/security.md | evolve/patterns/security.md |
| docs_fired/agentic_pact/adr/ADR-001-*.md | evolve/decisions/monolith-gateway.md |
| docs_fired/agentic_pact/adr/ADR-003-*.md | evolve/decisions/error-taxonomy.md |
