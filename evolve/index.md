# 演进知识库

开发过程中积累的经验和模式，## 验证模式

经过实践验证的最佳实践：

| 模式 | 说明 |
|------|------|
| [异步处理](./patterns/async-patterns.md) | async/await,最佳实践 |
| [缓存策略](./patterns/caching.md) | 匉应缓存与 Redis |
| [连接池](./patterns/connection-pool.md) | HTTP 连接复用 |
| [错误处理](./patterns/error-handling.md) | 统一错误模型 |
| [限流熔断](./patterns/rate-limiting.md) | 保护下游服务 |
| [安全实践](./patterns/security.md) | 认证、授权、数据保护 |
| [Skill-Tool 分层](./patterns/skill-tool-separation.md) | 平台知识与 Agent 能力分离 |
| [Bridge 适配器](./patterns/bridge-adapter.md) | 外部系统连接与执行 |

## 反模式警示

- [常见错误](./anti-patterns/avoid.md) - 开发中要避免的问题

| 决策 | 说明 |
|------|------|
| [单体网关架构](./decisions/monolith-gateway.md) | FastAPI 单体 + 可插拔执行层 |
| [统一合约设计](./decisions/unified-contract.md) | 所有 Agent 使用相同请求/响应格式 |
| [错误分类体系](./decisions/error-taxonomy.md) | 分层错误码设计 |
| [Skill Bridge 架构](./decisions/skill-bridge-architecture.md) | Skill 注入 + Bridge 适配器 |

## 如何贡献

1. 在开发中发现新模式时，添加到 `patterns/`
2. 遇到坑时，记录到 `anti-patterns/`
3. 做出重要技术决策时，添加到 `decisions/`
