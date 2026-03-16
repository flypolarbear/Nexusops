# 核心概念

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
└─────────────────────────────────────────────────────────────┘
                              │ HTTP/WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Gateway Core                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Middleware: Trace → Auth → Schema → RateLimit       │   │
│  └─────────────────────────────────────────────────────┘   │
│                              │                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              ExecutorRouter                          │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
              │                              │
              ▼                              ▼
┌─────────────────────────┐    ┌─────────────────────────────┐
│    BuiltinExecutor      │    │      RemoteExecutor         │
│  ┌─────────────────┐    │    │  ┌─────────────────────┐    │
│  │ Internal Agents │    │    │  │ Third-Party Agents  │    │
│  │ - chat          │    │    │  │ - HTTP/gRPC Clients │    │
│  │ - k8s           │    │    │  └─────────────────────┘    │
│  │ - deploy        │    │    └─────────────────────────────┘
│  │ - dns, logs...  │    │
│  └─────────────────┘    │
└─────────────────────────┘
```

## 核心组件

### Agent

具备特定领域能力的智能代理。

| 类型 | 说明 |
|------|------|
| Built-in | 平台内置，直接可用 |
| Third-party | 外部开发，通过 Market 安装 |

### Gateway

所有 Agent 调用的统一入口:
- 认证授权
- 请求验证
- Trace ID 生成与传播
- 响应格式化

### Executor

负责运行 Agent:
- **BuiltinExecutor**: 运行内置 Agent
- **RemoteExecutor**: 调用第三方 Agent 端点

### Contract

统一的请求/响应格式，所有 Agent 必须遵守。

## 请求处理流程

```
1. 客户端请求
      ↓
2. API 层解析
      ↓
3. 中间件链处理 (Trace → Auth → Schema)
      ↓
4. Gateway 构建 ExecutorRequest
      ↓
5. ExecutorRouter 路由到对应 Executor
      ↓
6. Agent Handler 处理请求
      ↓
7. 构建 InvokeResponse 返回
```

## 状态流转

```
Uncreated → Registered → Active ↔ Inactive → Removed
                         │
                         └─→ 可接收调用
```

| 状态 | 可调用 | 说明 |
|------|--------|------|
| Active | ✓ | 正常运行 |
| Inactive | ✗ | 临时禁用 |
| Registered | ✗ | 已注册未激活 |
| Removed | ✗ | 已注销 |

## 数据模型

### InvokeRequest

```json
{
  "request_id": "uuid",
  "agent_id": "nexusops.chat",
  "query": "用户输入",
  "context": {"user_id": "...", "project_id": "..."}
}
```

### InvokeResponse

```json
{
  "request_id": "uuid",
  "trace_id": "32位hex",
  "status": "success|error|partial",
  "content": {"text": "...", "format": "markdown"},
  "structured_output": {},
  "suggested_actions": [],
  "error": null
}
```
