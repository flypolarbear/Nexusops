# Gateway API

## 基础信息

```
Base URL: http://localhost:8000
Content-Type: application/json
```

## 认证

```http
Authorization: Bearer <token>
# 或
X-API-Key: <api-key>
```

## 端点

### 调用 Agent

```http
POST /api/v1/agents/{agent_id}/invoke
```

**请求体**:
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_id": "nexusops.chat",
  "query": "部署状态如何？",
  "context": {
    "user_id": "user-123",
    "project_id": "proj-789"
  }
}
```

**响应**:
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "trace_id": "a1b2c3d4e5f67890a1b2c3d4e5f67890",
  "status": "success",
  "content": {
    "text": "## 部署状态\n\n当前部署正常...",
    "format": "markdown"
  }
}
```

### 列出 Agents

```http
GET /api/v1/agents
```

**查询参数**:
| 参数 | 说明 |
|------|------|
| type | builtin / remote |
| status | active / inactive |
| capability | 按能力过滤 |

### 获取 Agent 详情

```http
GET /api/v1/agents/{agent_id}
```

### 健康检查

```http
GET /health
```

**响应**:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

## SDK 示例

### Python

```python
import httpx
import uuid

async def invoke_agent(agent_id: str, query: str, token: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"http://localhost:8000/api/v1/agents/{agent_id}/invoke",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "request_id": str(uuid.uuid4()),
                "agent_id": agent_id,
                "query": query
            }
        )
        return response.json()
```

### TypeScript

```typescript
import axios from 'axios';

async function invokeAgent(agentId: string, query: string, token: string) {
  const response = await axios.post(
    `http://localhost:8000/api/v1/agents/${agentId}/invoke`,
    {
      request_id: crypto.randomUUID(),
      agent_id: agentId,
      query
    },
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return response.data;
}
```

## 限流

响应头包含限流信息:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1708838400
```
