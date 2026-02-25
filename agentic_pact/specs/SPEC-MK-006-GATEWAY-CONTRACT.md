# Spec: MK-006 - Gateway 调用契约与错误模型

## 1. Summary

定义 NexusOps Agent Gateway 的统一调用契约，包括请求/响应结构、错误码体系、trace_id 规范和 JSON Schema 校验机制。本规范适用于内置 Agent 与第三方 Agent 的一致接入。

## 2. Goals

1. 建立统一的 Invoke API 请求/响应契约，内置与第三方 Agent 共用。
2. 定义标准化错误码体系，覆盖输入校验、执行、下游、系统四类错误。
3. 确保每次调用都有 trace_id，支持全链路追踪。
4. 提供 JSON Schema 校验能力，拦截非法输入并返回可诊断信息。

## 3. Non-Goals

1. 不定义具体 Agent 的业务逻辑。
2. 不定义计费、配额细节（ADR-002 阶段 2）。
3. 不定义流式响应（SSE/WebSocket）契约（后续迭代）。

---

## 4. API 契约（Interface Contract）

### 4.1 Invoke API

**Endpoint:** `POST /api/v1/agents/{agent_id}/invoke`

#### 4.1.1 Request Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["request_id", "agent_id", "query"],
  "properties": {
    "request_id": {
      "type": "string",
      "format": "uuid",
      "description": "客户端生成的请求唯一标识"
    },
    "agent_id": {
      "type": "string",
      "pattern": "^[a-z][a-z0-9._-]{2,63}$",
      "description": "目标 Agent 标识"
    },
    "conversation_id": {
      "type": "string",
      "format": "uuid",
      "description": "会话标识，用于多轮对话关联"
    },
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 10000,
      "description": "用户输入"
    },
    "context": {
      "$ref": "#/$defs/RequestContext"
    },
    "output_config": {
      "$ref": "#/$defs/OutputConfig"
    },
    "tools": {
      "type": "array",
      "items": { "$ref": "#/$defs/ToolOverride" },
      "description": "可选的工具覆盖配置"
    }
  },
  "$defs": {
    "RequestContext": {
      "type": "object",
      "properties": {
        "user_id": { "type": "string" },
        "tenant_id": { "type": "string" },
        "project_id": { "type": "string" },
        "version_id": { "type": "string" },
        "codename": { "type": "string" },
        "region": { "type": "string" },
        "resource_type": { "type": "string" },
        "resource_name": { "type": "string" },
        "namespace": { "type": "string" },
        "extra": { "type": "object" }
      }
    },
    "OutputConfig": {
      "type": "object",
      "properties": {
        "format": { "enum": ["markdown", "json", "plain"], "default": "markdown" },
        "max_tokens": { "type": "integer", "minimum": 1, "maximum": 32000 },
        "structured_output_schema": { "type": "object" }
      }
    },
    "ToolOverride": {
      "type": "object",
      "required": ["name"],
      "properties": {
        "name": { "type": "string" },
        "enabled": { "type": "boolean", "default": true },
        "params": { "type": "object" }
      }
    }
  }
}
```

#### 4.1.2 Response Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["request_id", "trace_id", "status", "content"],
  "properties": {
    "request_id": {
      "type": "string",
      "format": "uuid",
      "description": "回显请求 ID"
    },
    "trace_id": {
      "type": "string",
      "pattern": "^[a-f0-9]{32}$",
      "description": "服务端生成的 32 位十六进制 trace ID"
    },
    "status": {
      "enum": ["success", "partial", "error"],
      "description": "执行状态"
    },
    "content": {
      "$ref": "#/$defs/ResponseContent"
    },
    "structured_output": {
      "type": ["object", "array", "null"],
      "description": "结构化输出数据"
    },
    "suggested_actions": {
      "type": "array",
      "items": { "$ref": "#/$defs/SuggestedAction" }
    },
    "related_resources": {
      "type": "array",
      "items": { "$ref": "#/$defs/RelatedResource" }
    },
    "tool_calls": {
      "type": "array",
      "items": { "$ref": "#/$defs/ToolCall" }
    },
    "metadata": {
      "$ref": "#/$defs/ResponseMetadata"
    },
    "error": {
      "$ref": "#/$defs/ErrorDetail"
    }
  },
  "$defs": {
    "ResponseContent": {
      "type": "object",
      "required": ["text", "format"],
      "properties": {
        "text": { "type": "string" },
        "format": { "enum": ["markdown", "json", "plain"] },
        "data": {}
      }
    },
    "SuggestedAction": {
      "type": "object",
      "required": ["id", "type", "label"],
      "properties": {
        "id": { "type": "string" },
        "type": { "enum": ["invoke", "navigate", "copy", "external"] },
        "label": { "type": "string" },
        "params": { "type": "object" },
        "confirm_required": { "type": "boolean", "default": false },
        "danger": { "type": "boolean", "default": false }
      }
    },
    "RelatedResource": {
      "type": "object",
      "required": ["type", "id", "name"],
      "properties": {
        "type": { "type": "string" },
        "id": { "type": "string" },
        "name": { "type": "string" },
        "link": { "type": "string", "format": "uri" }
      }
    },
    "ToolCall": {
      "type": "object",
      "required": ["tool_id", "status"],
      "properties": {
        "tool_id": { "type": "string" },
        "tool_name": { "type": "string" },
        "input": { "type": "object" },
        "output": {},
        "status": { "enum": ["success", "error", "skipped"] },
        "duration_ms": { "type": "integer" },
        "error": { "$ref": "#/$defs/ErrorDetail" }
      }
    },
    "ResponseMetadata": {
      "type": "object",
      "properties": {
        "agent_version": { "type": "string" },
        "latency_ms": { "type": "integer" },
        "tokens_used": {
          "type": "object",
          "properties": {
            "input": { "type": "integer" },
            "output": { "type": "integer" }
          }
        },
        "retry_count": { "type": "integer" },
        "cache_hit": { "type": "boolean" }
      }
    },
    "ErrorDetail": {
      "type": "object",
      "required": ["code", "message"],
      "properties": {
        "code": { "type": "string", "pattern": "^[A-Z][A-Z0-9_]{2,31}$" },
        "message": { "type": "string" },
        "details": { "type": "object" },
        "retry_after": { "type": "integer", "description": "建议重试间隔（秒）" },
        "doc_url": { "type": "string", "format": "uri" }
      }
    }
  }
}
```

### 4.2 HTTP Headers

#### Request Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes | Bearer token 或 API Key |
| `X-Request-ID` | No | 客户端 request_id（与 body 中一致） |
| `X-Tenant-ID` | No | 租户标识（多租户场景） |
| `Content-Type` | Yes | `application/json` |
| `Accept` | No | `application/json` |

#### Response Headers

| Header | Description |
|--------|-------------|
| `X-Request-ID` | 回显请求 ID |
| `X-Trace-ID` | 服务端 trace ID |
| `X-RateLimit-Limit` | 速率限制上限 |
| `X-RateLimit-Remaining` | 剩余配额 |
| `X-RateLimit-Reset` | 配额重置时间戳 |

---

## 5. 错误码表（Error Code Table）

### 5.1 错误码命名规范

格式：`{CATEGORY}_{SUBCATEGORY}_{SPECIFIC}`

- **CATEGORY**: 错误大类（4 类）
- **SUBCATEGORY**: 错误子类
- **SPECIFIC**: 具体错误

### 5.2 完整错误码表

#### 5.2.1 输入校验错误（INPUT_*）- HTTP 400

| Code | Message | Description | Retry |
|------|---------|-------------|-------|
| `INPUT_INVALID_JSON` | Invalid JSON body | 请求体非法 JSON | No |
| `INPUT_SCHEMA_VIOLATION` | Request schema validation failed | JSON Schema 校验失败 | No |
| `INPUT_MISSING_FIELD` | Required field missing: {field} | 缺少必填字段 | No |
| `INPUT_INVALID_FORMAT` | Invalid format for field: {field} | 字段格式错误 | No |
| `INPUT_VALUE_OUT_OF_RANGE` | Value out of range for field: {field} | 字段值超出范围 | No |
| `INPUT_QUERY_TOO_LONG` | Query exceeds maximum length | 查询内容过长 | No |
| `INPUT_INVALID_AGENT_ID` | Invalid agent_id format | Agent ID 格式错误 | No |

#### 5.2.2 认证授权错误（AUTH_*）- HTTP 401/403

| Code | Message | Description | Retry |
|------|---------|-------------|-------|
| `AUTH_TOKEN_MISSING` | Authorization token required | 未提供认证信息 | No |
| `AUTH_TOKEN_INVALID` | Invalid authorization token | Token 无效 | No |
| `AUTH_TOKEN_EXPIRED` | Authorization token expired | Token 过期 | No* |
| `AUTH_PERMISSION_DENIED` | Permission denied for this agent | 无权访问该 Agent | No |
| `AUTH_QUOTA_EXCEEDED` | Rate limit or quota exceeded | 超出配额或速率限制 | Yes |
| `AUTH_TENANT_MISMATCH` | Tenant ID mismatch | 租户不匹配 | No |

#### 5.2.3 Agent 错误（AGENT_*）- HTTP 404/409/422

| Code | Message | Description | Retry |
|------|---------|-------------|-------|
| `AGENT_NOT_FOUND` | Agent not found: {agent_id} | Agent 不存在 | No |
| `AGENT_INACTIVE` | Agent is not active | Agent 已下线 | No |
| `AGENT_VERSION_MISMATCH` | Requested version not available | 版本不匹配 | No |
| `AGENT_BUSY` | Agent is temporarily unavailable | Agent 忙碌 | Yes |
| `AGENT_INPUT_REJECTED` | Agent rejected the input | Agent 拒绝输入 | No |
| `AGENT_OUTPUT_INVALID` | Agent returned invalid output | Agent 输出非法 | Yes |

#### 5.2.4 执行错误（EXEC_*）- HTTP 500/502/504

| Code | Message | Description | Retry |
|------|---------|-------------|-------|
| `EXEC_TIMEOUT` | Execution timed out | 执行超时 | Yes |
| `EXEC_TOOL_FAILED` | Tool execution failed: {tool} | 工具执行失败 | Yes |
| `EXEC_DOWNSTREAM_ERROR` | Downstream service error | 下游服务错误 | Yes |
| `EXEC_PARTIAL_FAILURE` | Partial execution failure | 部分执行失败 | Yes |
| `EXEC_RESOURCE_CONFLICT` | Resource conflict detected | 资源冲突 | Yes |
| `EXEC_CIRCUIT_OPEN` | Circuit breaker is open | 熔断器打开 | Yes |

#### 5.2.5 系统错误（SYSTEM_*）- HTTP 500/503

| Code | Message | Description | Retry |
|------|---------|-------------|-------|
| `SYSTEM_INTERNAL_ERROR` | Internal server error | 内部错误 | Yes |
| `SYSTEM_UNAVAILABLE` | Service temporarily unavailable | 服务不可用 | Yes |
| `SYSTEM_OVERLOADED` | System is overloaded | 系统过载 | Yes |
| `SYSTEM_MAINTENANCE` | System under maintenance | 维护中 | No |

### 5.3 错误响应示例

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "trace_id": "a1b2c3d4e5f67890a1b2c3d4e5f67890",
  "status": "error",
  "content": {
    "text": "Agent not found: invalid.agent",
    "format": "plain"
  },
  "error": {
    "code": "AGENT_NOT_FOUND",
    "message": "Agent not found: invalid.agent",
    "details": {
      "agent_id": "invalid.agent",
      "available_agents": ["nexusops.chat", "nexusops.k8s", "nexusops.deploy"]
    },
    "doc_url": "https://docs.nexusops.io/errors/AGENT_NOT_FOUND"
  },
  "metadata": {
    "latency_ms": 12
  }
}
```

---

## 6. Trace ID 规范

### 6.1 生成规则

- **格式**: 32 位小写十六进制字符串
- **生成**: 服务端在收到请求时立即生成
- **传播**: 所有下游调用必须携带同一 trace_id
- **存储**: 记录到 invocation 日志和数据库

### 6.2 关联规则

```
trace_id (服务端生成)
├── request_id (客户端生成)
├── conversation_id (会话关联)
├── invocation_id (数据库记录 ID)
└── tool_call_ids[] (工具调用 ID)
```

### 6.3 日志格式

```json
{
  "timestamp": "2026-02-24T16:00:00.000Z",
  "level": "INFO",
  "trace_id": "a1b2c3d4e5f67890a1b2c3d4e5f67890",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_id": "nexusops.k8s",
  "event": "invoke_start",
  "context": {
    "user_id": "user-123",
    "project_id": "proj-456"
  }
}
```

---

## 7. JSON Schema 校验机制

### 7.1 校验层级

1. **Gateway 入口校验**: 请求结构校验
2. **Agent 输入校验**: 按 Agent 定义的 input_schema 校验
3. **Agent 输出校验**: 按 Agent 定义的 output_schema 校验

### 7.2 校验失败处理

```python
# 伪代码
def validate_and_respond(request, schema):
    errors = validate_json_schema(request, schema)
    if errors:
        return {
            "status": "error",
            "error": {
                "code": "INPUT_SCHEMA_VIOLATION",
                "message": "Request schema validation failed",
                "details": {
                    "validation_errors": [
                        {
                            "path": error.path,
                            "message": error.message,
                            "expected": error.expected,
                            "actual": error.actual
                        }
                        for error in errors
                    ]
                }
            }
        }
```

### 7.3 宽松模式 vs 严格模式

| 模式 | 适用场景 | 行为 |
|------|---------|------|
| 严格模式 | 生产环境 | 校验失败立即返回错误 |
| 宽松模式 | 开发环境 | 校验失败记录警告，继续执行 |

---

## 8. 模块边界

```
┌─────────────────────────────────────────────────────────────┐
│                     API Layer (FastAPI)                      │
├─────────────────────────────────────────────────────────────┤
│  /api/v1/agents/{agent_id}/invoke                           │
│  - Request parsing                                          │
│  - Header extraction                                        │
│  - Response formatting                                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Middleware Chain                          │
├─────────────────────────────────────────────────────────────┤
│  1. TraceMiddleware      → 生成 trace_id                    │
│  2. AuthMiddleware       → 认证校验                         │
│  3. SchemaMiddleware     → JSON Schema 校验                 │
│  4. RateLimitMiddleware  → 限流检查                         │
│  5. AuditMiddleware      → 审计日志                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Gateway Core                              │
├─────────────────────────────────────────────────────────────┤
│  gateway/                                                   │
│  ├── contract.py         → 契约定义（本 Spec 核心）          │
│  ├── errors.py           → 错误码与异常类                    │
│  ├── validator.py        → JSON Schema 校验器                │
│  ├── trace.py            → Trace ID 生成与传播               │
│  └── response.py         → 响应构建器                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Executor Layer (MK-007)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. 测试必过项（Test Acceptance Criteria）

### 9.1 P0 用例（必须 100% 通过）

| ID | 用例 | 验证点 |
|----|------|--------|
| CT-001 | 有效请求返回成功响应 | status=success, 有 trace_id |
| CT-002 | 无效 JSON 返回 INPUT_INVALID_JSON | HTTP 400, error.code 正确 |
| CT-003 | 缺少 request_id 返回 INPUT_MISSING_FIELD | HTTP 400, details.field="request_id" |
| CT-004 | agent_id 格式错误返回 INPUT_INVALID_AGENT_ID | HTTP 400 |
| CT-005 | 不存在的 agent_id 返回 AGENT_NOT_FOUND | HTTP 404 |
| CT-006 | 无 Authorization 返回 AUTH_TOKEN_MISSING | HTTP 401 |
| CT-007 | 响应必须包含 trace_id 和 request_id | 所有响应校验 |
| CT-008 | 错误响应符合 ErrorDetail Schema | Schema 校验 |

### 9.2 P1 用例（通过率 >= 95%）

| ID | 用例 | 验证点 |
|----|------|--------|
| CT-101 | 超长 query 返回 INPUT_QUERY_TOO_LONG | query > 10000 字符 |
| CT-102 | Schema 违规返回字段级错误详情 | details.validation_errors |
| CT-103 | 下游超时返回 EXEC_TIMEOUT | 模拟超时 |
| CT-104 | 下游非法 JSON 返回 AGENT_OUTPUT_INVALID | 模拟非法响应 |
| CT-105 | 限流触发返回 AUTH_QUOTA_EXCEEDED | 模拟限流 |
| CT-106 | 同一 trace_id 贯穿整个调用链 | 日志检查 |
| CT-107 | metadata.latency_ms 正确记录 | 耗时校验 |
| CT-108 | 部分失败返回 status=partial | 模拟部分失败 |

### 9.3 契约回归测试

- 每次 CI/CD 构建必须运行契约测试
- 任何契约变更必须更新 Schema 版本
- 向后兼容性检查：新字段必须 optional

---

## 10. 实施约束

1. 所有错误码必须在 `gateway/errors.py` 中集中定义
2. 所有响应必须通过 `gateway/response.py` 的 `build_response()` 构建
3. 禁止在业务代码中直接构造错误响应
4. trace_id 必须在请求进入 Gateway 第一行代码时生成

---

## 11. Rollback Plan

1. 契约版本化：通过 URL 路径版本（`/api/v1/`）支持多版本共存
2. 错误码向后兼容：新增错误码不得删除或修改已有错误码语义
3. 降级开关：可通过配置关闭 Schema 校验进入宽松模式
