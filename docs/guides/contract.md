# 请求响应合约

## InvokeRequest Schema

### 必需字段

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| request_id | string | UUID 格式 | 客户端生成 |
| agent_id | string | `^[a-z][a-z0-9._-]{2,63}$` | Agent 标识 |
| query | string | 1-10000 字符 | 用户输入 |

### 可选字段

| 字段 | 类型 | 说明 |
|------|------|------|
| conversation_id | string | 多轮对话 ID |
| context | object | 请求上下文 |
| output_config | object | 输出配置 |
| tools | array | 工具覆盖 |

### Context 字段

```json
{
  "user_id": "string",
  "tenant_id": "string",
  "project_id": "string",
  "version_id": "string",
  "codename": "string",
  "region": "string",
  "resource_type": "string",
  "resource_name": "string",
  "namespace": "string",
  "extra": {}
}
```

### OutputConfig

```json
{
  "format": "markdown | json | plain",
  "max_tokens": 4000,
  "structured_output_schema": {}
}
```

## InvokeResponse Schema

### 必需字段

| 字段 | 类型 | 说明 |
|------|------|------|
| request_id | string | 请求 ID 回显 |
| trace_id | string | 32 位 hex | 服务端生成 |
| status | enum | success / error / partial / pending |
| content | object | 响应内容 |

### Content 结构

```json
{
  "text": "响应文本",
  "format": "markdown | json | plain",
  "data": null
}
```

### 可选字段

| 字段 | 类型 | 说明 |
|------|------|------|
| structured_output | any | 结构化输出 |
| suggested_actions | array | 建议操作 |
| related_resources | array | 相关资源 |
| tool_calls | array | 工具调用记录 |
| metadata | object | 元数据 |
| error | object | 错误详情 |

### SuggestedAction

```json
{
  "id": "action-id",
  "type": "invoke | navigate | copy | external",
  "label": "显示标签",
  "params": {},
  "confirm_required": false,
  "danger": false
}
```

### ToolCall

```json
{
  "tool_id": "tool-001",
  "tool_name": "get_status",
  "input": {},
  "output": {},
  "status": "success | error | skipped",
  "duration_ms": 150
}
```

### ErrorDetail

```json
{
  "code": "ERROR_CODE",
  "message": "错误描述",
  "details": {},
  "retry_after": 5,
  "doc_url": "https://..."
}
```

## 向后兼容

### 添加字段

只添加可选字段，不破坏兼容性:
```json
{
  "new_optional_field": "value"
}
```

### 版本控制

破坏性变更使用新版本:
```
/api/v1/agents/{id}/invoke  → 当前
/api/v2/agents/{id}/invoke  → 新版本
```
