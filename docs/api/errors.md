# 错误码表

## 格式

```
{CATEGORY}_{SUBCATEGORY}_{SPECIFIC}
```

## 分类

| 分类 | 前缀 | HTTP 状态码 |
|------|------|-------------|
| Input | `INPUT_` | 400 |
| Auth | `AUTH_` | 401, 403, 429 |
| Agent | `AGENT_` | 404, 409, 422 |
| Execution | `EXEC_` | 500, 502, 504 |
| System | `SYSTEM_` | 500, 503 |

## 完整错误码

### INPUT_* (输入错误)

| 错误码 | HTTP | 说明 | 可重试 |
|--------|------|------|--------|
| INPUT_INVALID_JSON | 400 | JSON 格式无效 | 否 |
| INPUT_SCHEMA_VIOLATION | 400 | 请求校验失败 | 否 |
| INPUT_MISSING_FIELD | 400 | 必需字段缺失 | 否 |
| INPUT_INVALID_FORMAT | 400 | 字段格式无效 | 否 |
| INPUT_QUERY_TOO_LONG | 400 | 查询超长 | 否 |
| INPUT_INVALID_AGENT_ID | 400 | agent_id 格式无效 | 否 |

### AUTH_* (认证错误)

| 错误码 | HTTP | 说明 | 可重试 |
|--------|------|------|--------|
| AUTH_TOKEN_MISSING | 401 | 缺少认证令牌 | 否 |
| AUTH_TOKEN_INVALID | 401 | 令牌无效 | 否 |
| AUTH_TOKEN_EXPIRED | 401 | 令牌过期 | 是* |
| AUTH_PERMISSION_DENIED | 403 | 权限不足 | 否 |
| AUTH_QUOTA_EXCEEDED | 429 | 超出配额 | 是 |

*需要刷新令牌后重试

### AGENT_* (Agent 错误)

| 错误码 | HTTP | 说明 | 可重试 |
|--------|------|------|--------|
| AGENT_NOT_FOUND | 404 | Agent 不存在 | 否 |
| AGENT_INACTIVE | 409 | Agent 未激活 | 否 |
| AGENT_NOT_INSTALLED | 403 | Agent 未安装 | 否 |
| AGENT_DISABLED | 403 | Agent 已禁用 | 否 |
| AGENT_BUSY | 503 | Agent 忙碌 | 是 |
| AGENT_INPUT_REJECTED | 422 | Agent 拒绝输入 | 否 |
| AGENT_OUTPUT_INVALID | 422 | Agent 输出无效 | 是 |

### EXEC_* (执行错误)

| 错误码 | HTTP | 说明 | 可重试 |
|--------|------|------|--------|
| EXEC_TIMEOUT | 504 | 执行超时 | 是 |
| EXEC_TOOL_FAILED | 500 | 工具执行失败 | 是 |
| EXEC_DOWNSTREAM_ERROR | 502 | 下游服务错误 | 是 |
| EXEC_PARTIAL_FAILURE | 500 | 部分执行失败 | 是 |
| EXEC_CIRCUIT_OPEN | 503 | 熔断器打开 | 是 |

### SYSTEM_* (系统错误)

| 错误码 | HTTP | 说明 | 可重试 |
|--------|------|------|--------|
| SYSTEM_INTERNAL_ERROR | 500 | 内部错误 | 是 |
| SYSTEM_UNAVAILABLE | 503 | 服务不可用 | 是 |
| SYSTEM_MAINTENANCE | 503 | 系统维护中 | 否 |

## 错误响应格式

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "trace_id": "a1b2c3d4e5f67890a1b2c3d4e5f67890",
  "status": "error",
  "content": {
    "text": "错误描述",
    "format": "plain"
  },
  "error": {
    "code": "ERROR_CODE",
    "message": "详细错误信息",
    "details": {
      "field": "补充上下文"
    },
    "retry_after": 5,
    "doc_url": "https://docs.nexusops.io/errors/ERROR_CODE"
  }
}
```

## Python 异常

```python
from app.gateway.errors import (
    InputError, AuthError, AgentError, ExecError, SystemError,
    agent_not_found, exec_timeout
)

# 抛出特定错误
raise agent_not_found("nexusops.unknown")

# 或使用基类
raise InputError(
    code="INPUT_MISSING_FIELD",
    message="Query is required",
    details={"field": "query"}
)
```
