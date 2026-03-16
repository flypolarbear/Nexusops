# 错误分类体系决策

## 状态

已采纳

## 背景

需要标准化的错误处理方式，便于客户端处理和问题追踪。

## 决策

采用**分层错误码体系**：`{CATEGORY}_{SUBCATEGORY}_{SPECIFIC}`

## 错误分类

| 类别 | 前缀 | HTTP 状态码 | 说明 |
|------|------|-------------|------|
| Input | INPUT_ | 400 | 客户端输入错误 |
| Auth | AUTH_ | 401/403/429 | 认证授权错误 |
| Agent | AGENT_ | 404/409/422 | Agent 相关错误 |
| Exec | EXEC_ | 500/502/504 | 执行层错误 |
| System | SYSTEM_ | 500/503 | 系统级错误 |

## 常用错误码

### Input (400)
- `INPUT_INVALID_JSON` - 无效 JSON
- `INPUT_SCHEMA_VIOLATION` - Schema 校验失败
- `INPUT_MISSING_FIELD` - 缺少必需字段

### Auth (401/403/429)
- `AUTH_TOKEN_MISSING` - 缺少认证 Token
- `AUTH_TOKEN_INVALID` - 无效 Token
- `AUTH_PERMISSION_DENIED` - 权限不足
- `AUTH_QUOTA_EXCEEDED` - 限流

### Agent (404/409/422)
- `AGENT_NOT_FOUND` - Agent 不存在
- `AGENT_INACTIVE` - Agent 未激活
- `AGENT_INPUT_REJECTED` - Agent 拒绝输入

### Exec (500/502/504)
- `EXEC_TIMEOUT` - 执行超时
- `EXEC_DOWNSTREAM_ERROR` - 下游服务错误
- `EXEC_CIRCUIT_OPEN` - 熔断器打开

### System (500/503)
- `SYSTEM_INTERNAL_ERROR` - 内部错误
- `SYSTEM_UNAVAILABLE` - 服务不可用

## 错误响应格式

```json
{
  "code": "ERROR_CODE",
  "message": "人类可读的错误描述",
  "details": {"field": "额外上下文"},
  "retry_after": 5,
  "doc_url": "https://docs.nexusops.io/errors/ERROR_CODE"
}
```

## 可重试错误

以下错误可以安全重试：
- `AUTH_TOKEN_EXPIRED`
- `AUTH_QUOTA_EXCEEDED`
- `AGENT_BUSY`
- `EXEC_*` 系列
- `SYSTEM_*` 系列（除 `SYSTEM_MAINTENANCE`）

## 影响

- 客户端可以统一处理错误
- 便于监控和告警分类
- 支持自动化重试策略
