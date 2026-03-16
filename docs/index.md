# NexusOps 文档

面向 Agent 开发者和平台用户的完整指南。

## 快速开始

| 文档 | 说明 |
|------|------|
| [安装指南](./start/install.md) | 环境配置与安装 |
| [10分钟上手](./start/quickstart.md) | 创建你的第一个 Agent |
| [核心概念](./start/concepts.md) | 理解系统架构 |

## API 参考

| 文档 | 说明 |
|------|------|
| [Gateway API](./api/gateway.md) | REST 端点与调用示例 |
| [调用接口](./api/invoke.md) | 请求/响应合约规范 |
| [错误码表](./api/errors.md) | 完整错误码参考 |

## 开发指南

| 文档 | 说明 |
|------|------|
| [Agent 开发](./guides/agent-dev.md) | 开发规范与最佳实践 |
| [请求响应合约](./guides/contract.md) | InvokeRequest/InvokeResponse |
| [生命周期](./guides/lifecycle.md) | 注册、激活、调用、下线 |
| [测试指南](./guides/testing.md) | 单元/集成/合约测试 |

## 内置 Agents

| Agent ID | 能力 |
|----------|------|
| `nexusops.chat` | 通用对话、快捷命令 |
| `nexusops.k8s` | Kubernetes 资源操作 |
| `nexusops.deploy` | 部署管理与状态查询 |
| `nexusops.dns` | DNS 记录管理 |
| `nexusops.logs` | 日志聚合与查询 |
| `nexusops.cost` | 成本分析与优化 |

## 技术栈

- **后端**: FastAPI + SQLAlchemy async + Pydantic v2
- **前端**: React 18 + TypeScript + Zustand
- **数据库**: PostgreSQL 15+ / Redis 7+

## 架构文档

| 文档 | 说明 |
|------|------|
| [Agent 调用架构](./architecture/agent-invocation.md) | 内置 Agent 调用流程详解 |
