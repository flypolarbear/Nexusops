# Gateway API Reference

## Overview

This document provides comprehensive API reference for the NexusOps Agent Gateway. All endpoints follow RESTful conventions and return JSON responses.

---

## Base URL

```
Production: https://api.nexusops.io
Development: http://localhost:8000
```

## Authentication

All API requests require authentication via Bearer token or API key.

```http
Authorization: Bearer <your-token>
```

Or using API key header:

```http
X-API-Key: <your-api-key>
```

## Content Type

All requests and responses use JSON:

```http
Content-Type: application/json
Accept: application/json
```

---

## Endpoints

### Invoke Agent

Invoke an agent with a query.

**Endpoint**: `POST /api/v1/agents/{agent_id}/invoke`

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_id` | string | Agent identifier (e.g., `nexusops.chat`) |

**Request Body**:

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "conversation_id": "660e8400-e29b-41d4-a716-446655440001",
  "agent_id": "nexusops.chat",
  "query": "What is the status of my deployment?",
  "context": {
    "user_id": "user-123",
    "tenant_id": "tenant-456",
    "project_id": "proj-789",
    "version_id": "v1.2.3",
    "codename": "feature-xyz",
    "region": "us-east",
    "resource_type": "deployment",
    "resource_name": "my-app",
    "namespace": "production"
  },
  "output_config": {
    "format": "markdown",
    "max_tokens": 4000
  },
  "tools": [
    {
      "name": "get_status",
      "enabled": true
    }
  ]
}
```

**Response** (200 OK):

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "trace_id": "a1b2c3d4e5f67890a1b2c3d4e5f67890",
  "status": "success",
  "content": {
    "text": "## Deployment Status\n\nYour deployment is healthy.",
    "format": "markdown"
  },
  "structured_output": {
    "status": "healthy",
    "replicas": 3
  },
  "suggested_actions": [
    {
      "id": "view-logs",
      "type": "invoke",
      "label": "View Logs",
      "params": {
        "agent_id": "nexusops.logs",
        "query": "logs my-app"
      }
    }
  ],
  "metadata": {
    "trace_id": "a1b2c3d4e5f67890a1b2c3d4e5f67890",
    "latency_ms": 250
  }
}
```

**Error Response** (404 Not Found):

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "trace_id": "a1b2c3d4e5f67890a1b2c3d4e5f67890",
  "status": "error",
  "content": {
    "text": "Agent not found: nexusops.unknown",
    "format": "plain"
  },
  "error": {
    "code": "AGENT_NOT_FOUND",
    "message": "Agent not found: nexusops.unknown",
    "details": {
      "agent_id": "nexusops.unknown"
    }
  }
}
```

---

### List Agents

List all available agents.

**Endpoint**: `GET /api/v1/agents`

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `type` | string | - | Filter by type: `builtin`, `remote` |
| `status` | string | - | Filter by status: `active`, `inactive` |
| `capability` | string | - | Filter by capability |
| `page` | integer | 1 | Page number |
| `limit` | integer | 20 | Items per page (max 100) |

**Response** (200 OK):

```json
{
  "agents": [
    {
      "agent_id": "nexusops.chat",
      "name": "Chat Agent",
      "version": "1.0.0",
      "type": "builtin",
      "status": "active",
      "capabilities": ["chat", "quick_commands"],
      "description": "General AI assistant"
    },
    {
      "agent_id": "nexusops.k8s",
      "name": "Kubernetes Agent",
      "version": "1.0.0",
      "type": "builtin",
      "status": "active",
      "capabilities": ["k8s_deploy", "k8s_scale"],
      "description": "Kubernetes operations"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 8,
    "total_pages": 1
  }
}
```

---

### Get Agent

Get details of a specific agent.

**Endpoint**: `GET /api/v1/agents/{agent_id}`

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_id` | string | Agent identifier |

**Response** (200 OK):

```json
{
  "agent_id": "nexusops.chat",
  "name": "Chat Agent",
  "version": "1.0.0",
  "type": "builtin",
  "status": "active",
  "capabilities": ["chat", "quick_commands", "deployment_info", "status_query"],
  "description": "General AI assistant supporting quick commands",
  "tools": [
    {
      "name": "get_deployment_status",
      "description": "Get deployment status for a version",
      "inputSchema": {
        "type": "object",
        "properties": {
          "codename": {"type": "string"},
          "region": {"type": "string"}
        }
      }
    }
  ],
  "manifest": {
    "input_schema": {},
    "output_schema": {}
  }
}
```

---

### Get Agent Manifest

Get the full manifest for an agent.

**Endpoint**: `GET /api/v1/agents/{agent_id}/manifest`

**Response** (200 OK):

```json
{
  "agent_id": "nexusops.k8s",
  "name": "Kubernetes Agent",
  "version": "1.0.0",
  "description": "Kubernetes operations agent",
  "category": "k8s",
  "capabilities": ["k8s_deploy", "k8s_scale", "k8s_logs", "k8s_describe"],
  "tools": [
    {
      "name": "get_pod_logs",
      "description": "Get logs from a pod",
      "inputSchema": {
        "type": "object",
        "properties": {
          "pod_name": {"type": "string"},
          "namespace": {"type": "string", "default": "default"},
          "tail_lines": {"type": "integer", "default": 100}
        },
        "required": ["pod_name"]
      }
    }
  ],
  "input_schema": {
    "type": "object",
    "properties": {
      "query": {"type": "string"}
    }
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "content": {"type": "object"},
      "structured_output": {"type": "object"}
    }
  }
}
```

---

### Health Check

Check the health of the Gateway service.

**Endpoint**: `GET /health`

**Response** (200 OK):

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "executors": {
      "builtin": "healthy",
      "remote": "healthy"
    }
  }
}
```

---

### Get Invocation History

Get invocation history for the authenticated user.

**Endpoint**: `GET /api/v1/invocations`

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `agent_id` | string | - | Filter by agent |
| `status` | string | - | Filter by status |
| `start_date` | string | - | Start date (ISO 8601) |
| `end_date` | string | - | End date (ISO 8601) |
| `page` | integer | 1 | Page number |
| `limit` | integer | 20 | Items per page |

**Response** (200 OK):

```json
{
  "invocations": [
    {
      "invocation_id": "inv-123",
      "trace_id": "a1b2c3d4e5f67890a1b2c3d4e5f67890",
      "agent_id": "nexusops.chat",
      "status": "success",
      "query": "What is the status?",
      "latency_ms": 250,
      "created_at": "2026-02-25T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100
  }
}
```

---

### Get Invocation Details

Get details of a specific invocation.

**Endpoint**: `GET /api/v1/invocations/{invocation_id}`

**Response** (200 OK):

```json
{
  "invocation_id": "inv-123",
  "trace_id": "a1b2c3d4e5f67890a1b2c3d4e5f67890",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_id": "nexusops.chat",
  "status": "success",
  "query": "What is the status?",
  "request_context": {
    "user_id": "user-123",
    "project_id": "proj-456"
  },
  "response": {
    "content": {
      "text": "Status is healthy",
      "format": "markdown"
    }
  },
  "tool_calls": [],
  "latency_ms": 250,
  "tokens_used": {
    "input": 100,
    "output": 50
  },
  "created_at": "2026-02-25T00:00:00Z"
}
```

---

## Agent Market API

### List Available Agents (Marketplace)

**Endpoint**: `GET /api/v1/agent-market/agents`

**Query Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `category` | string | Filter by category |
| `search` | string | Search in name/description |
| `sort` | string | Sort by: `name`, `rating`, `downloads` |

**Response** (200 OK):

```json
{
  "agents": [
    {
      "agent_id": "third-party.analytics",
      "name": "Analytics Agent",
      "publisher": "Third Party Inc.",
      "version": "1.0.0",
      "category": "analytics",
      "rating": 4.5,
      "downloads": 1000,
      "description": "Data analytics and reporting",
      "installed": false
    }
  ]
}
```

---

### Install Agent

**Endpoint**: `POST /api/v1/agent-market/agents/{agent_id}/install`

**Request Body**:

```json
{
  "config": {
    "api_key": "your-api-key",
    "endpoint": "https://custom.endpoint.com"
  }
}
```

**Response** (200 OK):

```json
{
  "agent_id": "third-party.analytics",
  "status": "installed",
  "installed_at": "2026-02-25T00:00:00Z"
}
```

---

### Uninstall Agent

**Endpoint**: `DELETE /api/v1/agent-market/agents/{agent_id}/install`

**Response** (200 OK):

```json
{
  "agent_id": "third-party.analytics",
  "status": "uninstalled"
}
```

---

## Error Responses

### Common Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `INPUT_INVALID_JSON` | Invalid JSON in request body |
| 400 | `INPUT_SCHEMA_VIOLATION` | Request validation failed |
| 400 | `INPUT_MISSING_FIELD` | Required field missing |
| 401 | `AUTH_TOKEN_MISSING` | No authentication provided |
| 401 | `AUTH_TOKEN_INVALID` | Invalid token |
| 403 | `AUTH_PERMISSION_DENIED` | Permission denied |
| 404 | `AGENT_NOT_FOUND` | Agent not found |
| 429 | `AUTH_QUOTA_EXCEEDED` | Rate limit exceeded |
| 500 | `SYSTEM_INTERNAL_ERROR` | Internal server error |
| 503 | `SYSTEM_UNAVAILABLE` | Service unavailable |

### Error Response Format

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "trace_id": "a1b2c3d4e5f67890a1b2c3d4e5f67890",
  "status": "error",
  "content": {
    "text": "Error message",
    "format": "plain"
  },
  "error": {
    "code": "ERROR_CODE",
    "message": "Detailed error message",
    "details": {
      "field": "additional context"
    },
    "retry_after": 5,
    "doc_url": "https://docs.nexusops.io/errors/ERROR_CODE"
  }
}
```

---

## Rate Limiting

### Headers

All responses include rate limit headers:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1708838400
```

### Limits

| Tier | Requests/min | Requests/day |
|------|-------------|--------------|
| Free | 60 | 1,000 |
| Pro | 600 | 50,000 |
| Enterprise | Custom | Custom |

---

## SDK Examples

### Python

```python
import httpx
import uuid

class NexusOpsClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)

    async def invoke(
        self,
        agent_id: str,
        query: str,
        context: dict = None
    ) -> dict:
        response = await self.client.post(
            f"{self.base_url}/api/v1/agents/{agent_id}/invoke",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "request_id": str(uuid.uuid4()),
                "agent_id": agent_id,
                "query": query,
                "context": context or {}
            }
        )
        response.raise_for_status()
        return response.json()

    async def list_agents(self, **params) -> dict:
        response = await self.client.get(
            f"{self.base_url}/api/v1/agents",
            headers={"Authorization": f"Bearer {self.api_key}"},
            params=params
        )
        response.raise_for_status()
        return response.json()

# Usage
async def main():
    client = NexusOpsClient("https://api.nexusops.io", "your-api-key")

    result = await client.invoke(
        agent_id="nexusops.chat",
        query="What is the status of my deployment?",
        context={"project_id": "proj-123"}
    )

    print(result["content"]["text"])
```

### JavaScript/TypeScript

```typescript
import axios from 'axios';

interface InvokeRequest {
  request_id: string;
  agent_id: string;
  query: string;
  context?: Record<string, any>;
}

interface InvokeResponse {
  request_id: string;
  trace_id: string;
  status: 'success' | 'error' | 'partial';
  content: {
    text: string;
    format: string;
  };
  error?: {
    code: string;
    message: string;
  };
}

class NexusOpsClient {
  private client = axios.create({
    baseURL: this.baseUrl,
    headers: {
      'Authorization': `Bearer ${this.apiKey}`,
      'Content-Type': 'application/json'
    }
  });

  constructor(
    private baseUrl: string,
    private apiKey: string
  ) {}

  async invoke(
    agentId: string,
    query: string,
    context?: Record<string, any>
  ): Promise<InvokeResponse> {
    const response = await this.client.post<InvokeResponse>(
      `/api/v1/agents/${agentId}/invoke`,
      {
        request_id: crypto.randomUUID(),
        agent_id: agentId,
        query,
        context
      }
    );
    return response.data;
  }

  async listAgents(params?: {
    type?: string;
    status?: string;
    page?: number;
    limit?: number;
  }): Promise<any> {
    const response = await this.client.get('/api/v1/agents', { params });
    return response.data;
  }
}

// Usage
const client = new NexusOpsClient('https://api.nexusops.io', 'your-api-key');

const result = await client.invoke(
  'nexusops.chat',
  'What is the status?',
  { project_id: 'proj-123' }
);

console.log(result.content.text);
```

---

## OpenAPI Specification

The full OpenAPI specification is available at:

```
GET /openapi.json
GET /docs (Swagger UI)
GET /redoc (ReDoc UI)
```

---

## Next Steps

- [SDK Reference](./sdk-reference.md) - Detailed SDK documentation
- [Webhook Spec](./webhook-spec.md) - Webhook integration
- [Error Handling](../agent-development/error-handling.md) - Error handling guide
