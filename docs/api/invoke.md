# 调用接口

所有 Agent 使用统一的请求/响应合约。

## InvokeRequest

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "conversation_id": "660e8400-e29b-41d4-a716-446655440001",
  "agent_id": "nexusops.chat",
  "query": "部署状态如何？",
  "context": {
    "user_id": "user-123",
    "tenant_id": "tenant-456",
    "project_id": "proj-789",
    "version_id": "v1.2.3",
    "region": "us-east",
    "namespace": "production"
  },
  "output_config": {
    "format": "markdown",
    "max_tokens": 4000
  },
  "tools": [
    {"name": "get_status", "enabled": true}
  ]
}
```

### 必需字段

| 字段 | 类型 | 说明 |
|------|------|------|
| request_id | string (UUID) | 客户端生成的唯一 ID |
| agent_id | string | Agent 标识 (格式: `namespace.name`) |
| query | string | 用户输入 (1-10000 字符) |

### 可选字段

| 字段 | 类型 | 说明 |
|------|------|------|
| conversation_id | string | 多轮对话 ID |
| context | object | 请求上下文 |
| output_config | object | 输出配置 |
| tools | array | 工具覆盖配置 |

## InvokeResponse

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "trace_id": "a1b2c3d4e5f67890a1b2c3d4e5f67890",
  "status": "success",
  "content": {
    "text": "## 部署状态\n\n当前部署正常",
    "format": "markdown",
    "data": null
  },
  "structured_output": {
    "status": "healthy",
    "replicas": 3
  },
  "suggested_actions": [
    {
      "id": "view-logs",
      "type": "invoke",
      "label": "查看日志",
      "params": {"agent_id": "nexusops.logs", "query": "logs my-app"}
    }
  ],
  "tool_calls": [
    {
      "tool_id": "tool-001",
      "tool_name": "get_status",
      "status": "success",
      "duration_ms": 150
    }
  ],
  "metadata": {
    "trace_id": "a1b2c3d4e5f67890a1b2c3d4e5f67890",
    "latency_ms": 250
  },
  "error": null
}
```

### 状态值

| 状态 | 说明 |
|------|------|
| success | 执行成功 |
| error | 执行失败 |
| partial | 部分成功 |
| pending | 异步处理中 |

### 建议操作类型

| 类型 | 说明 | params 示例 |
|------|------|-------------|
| invoke | 调用另一个 Agent | `{"agent_id": "...", "query": "..."}` |
| navigate | 导航到 URL | `{"url": "/deployments/..."}` |
| copy | 复制到剪贴板 | `{"text": "kubectl get pods"}` |
| external | 打开外部链接 | `{"url": "https://..."}` |

## Python 模型

```python
from app.gateway.contract import InvokeRequest, InvokeResponse, RequestContext

# 构建请求
request = InvokeRequest(
    request_id="550e8400-e29b-41d4-a716-446655440000",
    agent_id="nexusops.chat",
    query="Hello",
    context=RequestContext(user_id="user-123")
)

# 构建响应
response = InvokeResponse(
    request_id=request.request_id,
    trace_id="a1b2c3d4e5f67890a1b2c3d4e5f67890",
    status="success",
    content={"text": "Hello!", "format": "markdown"}
)
```
