# Contract Specification

## Overview

This document defines the NexusOps Agent Gateway contract (MK-006). All agents must conform to this specification for consistent request handling and response formatting.

---

## Request Schema

### InvokeRequest

The standard request format for all agent invocations.

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
    "namespace": "production",
    "extra": {}
  },
  "output_config": {
    "format": "markdown",
    "max_tokens": 4000,
    "structured_output_schema": {}
  },
  "tools": [
    {
      "name": "get_deployment_status",
      "enabled": true,
      "params": {}
    }
  ]
}
```

### Field Specifications

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `request_id` | string (UUID) | Yes | Client-generated unique request ID |
| `conversation_id` | string (UUID) | No | Session ID for multi-turn conversations |
| `agent_id` | string | Yes | Target agent ID (pattern: `^[a-z][a-z0-9._-]{2,63}$`) |
| `query` | string | Yes | User input (1-10000 characters) |
| `context` | object | No | Request context with user/project info |
| `output_config` | object | No | Output formatting configuration |
| `tools` | array | No | Tool override configurations |

### RequestContext Fields

| Field | Type | Description |
|-------|------|-------------|
| `user_id` | string | Authenticated user ID |
| `tenant_id` | string | Tenant/organization ID |
| `project_id` | string | Project ID |
| `version_id` | string | Application version ID |
| `codename` | string | Release codename |
| `region` | string | Target region |
| `resource_type` | string | Kubernetes resource type |
| `resource_name` | string | Resource name |
| `namespace` | string | Kubernetes namespace |
| `extra` | object | Additional custom context |

### OutputConfig Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `format` | enum | `"markdown"` | Output format: `markdown`, `json`, `plain` |
| `max_tokens` | integer | - | Maximum response tokens (1-32000) |
| `structured_output_schema` | object | - | JSON Schema for structured output |

### ToolOverride Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Tool name |
| `enabled` | boolean | No | Enable/disable tool (default: true) |
| `params` | object | No | Tool-specific parameters |

---

## Response Schema

### InvokeResponse

The standard response format for all agent invocations.

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "trace_id": "a1b2c3d4e5f67890a1b2c3d4e5f67890",
  "status": "success",
  "content": {
    "text": "## Deployment Status\n\nYour deployment is healthy.",
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
      "label": "View Logs",
      "params": {
        "agent_id": "nexusops.logs",
        "query": "logs my-app"
      },
      "confirm_required": false,
      "danger": false
    }
  ],
  "related_resources": [
    {
      "type": "deployment",
      "id": "my-app",
      "name": "my-app",
      "link": "https://console.example.com/deployments/my-app"
    }
  ],
  "tool_calls": [
    {
      "tool_id": "tool-001",
      "tool_name": "get_deployment_status",
      "input": {"name": "my-app"},
      "output": {"status": "healthy"},
      "status": "success",
      "duration_ms": 150
    }
  ],
  "metadata": {
    "trace_id": "a1b2c3d4e5f67890a1b2c3d4e5f67890",
    "agent_version": "1.0.0",
    "latency_ms": 250,
    "tokens_used": {
      "input": 100,
      "output": 50
    },
    "retry_count": 0,
    "cache_hit": false
  },
  "error": null
}
```

### Field Specifications

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `request_id` | string | Yes | Echo of request ID |
| `trace_id` | string | Yes | Server-generated 32-char hex trace ID |
| `status` | enum | Yes | `success`, `error`, `partial`, `pending` |
| `content` | object | Yes | Response content |
| `structured_output` | any | No | Structured output data |
| `suggested_actions` | array | No | Follow-up action suggestions |
| `related_resources` | array | No | Related resource references |
| `tool_calls` | array | No | Tool call records |
| `metadata` | object | No | Response metadata |
| `error` | object | No | Error details (if status is error) |

### ResponseContent Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Response text |
| `format` | enum | Yes | `markdown`, `json`, `plain` |
| `data` | any | No | Additional data |

### SuggestedAction Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique action ID |
| `type` | enum | Yes | `invoke`, `navigate`, `copy`, `external` |
| `label` | string | Yes | Display label |
| `params` | object | No | Action parameters |
| `confirm_required` | boolean | No | Requires confirmation (default: false) |
| `danger` | boolean | No | Destructive action warning (default: false) |

### Action Types

| Type | Description | Params Example |
|------|-------------|----------------|
| `invoke` | Invoke another agent | `{"agent_id": "nexusops.k8s", "query": "scale my-app"}` |
| `navigate` | Navigate to URL | `{"url": "/deployments/my-app"}` |
| `copy` | Copy text to clipboard | `{"text": "kubectl get pods"}` |
| `external` | Open external URL | `{"url": "https://docs.example.com"}` |

### RelatedResource Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Resource type |
| `id` | string | Yes | Resource ID |
| `name` | string | Yes | Display name |
| `link` | string | No | Resource URL |

### ToolCall Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tool_id` | string | Yes | Unique tool call ID |
| `tool_name` | string | No | Tool name |
| `input` | object | No | Tool input |
| `output` | any | No | Tool output |
| `status` | enum | Yes | `success`, `error`, `skipped` |
| `duration_ms` | integer | No | Execution duration |
| `error` | object | No | Error details |

### ResponseMetadata Fields

| Field | Type | Description |
|-------|------|-------------|
| `trace_id` | string | Trace ID |
| `agent_version` | string | Agent version |
| `latency_ms` | integer | Total latency |
| `tokens_used` | object | Token usage (`input`, `output`) |
| `retry_count` | integer | Number of retries |
| `cache_hit` | boolean | Result from cache |

---

## HTTP Headers

### Request Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes | Bearer token or API key |
| `Content-Type` | Yes | `application/json` |
| `X-Request-ID` | No | Client request ID |
| `X-Tenant-ID` | No | Tenant ID for multi-tenant |

### Response Headers

| Header | Description |
|--------|-------------|
| `X-Request-ID` | Echo of request ID |
| `X-Trace-ID` | Server trace ID |
| `X-RateLimit-Limit` | Rate limit ceiling |
| `X-RateLimit-Remaining` | Remaining quota |
| `X-RateLimit-Reset` | Quota reset timestamp |

---

## Python Models

### Using Pydantic Models

```python
from app.gateway.contract import (
    InvokeRequest,
    InvokeResponse,
    RequestContext,
    OutputConfig,
    ResponseContent,
    SuggestedAction,
    RelatedResource,
    ErrorDetail,
)

# Build a request
request = InvokeRequest(
    request_id="550e8400-e29b-41d4-a716-446655440000",
    agent_id="nexusops.chat",
    query="Hello",
    context=RequestContext(user_id="user-123"),
)

# Build a response
response = InvokeResponse(
    request_id=request.request_id,
    trace_id="a1b2c3d4e5f67890a1b2c3d4e5f67890",
    status="success",
    content=ResponseContent(
        text="Hello! How can I help?",
        format="markdown"
    ),
    suggested_actions=[
        SuggestedAction(
            id="learn-more",
            type="invoke",
            label="Learn More",
            params={"agent_id": "nexusops.chat", "query": "help"}
        )
    ]
)
```

### ExecutorResult

For internal use, agents return `ExecutorResult`:

```python
from app.gateway.executor.base import ExecutorResult

result = ExecutorResult(
    success=True,
    content={"text": "Hello!", "format": "markdown"},
    structured_output={"greeting": "Hello!"},
    suggested_actions=[
        {"id": "help", "type": "invoke", "label": "Get Help"}
    ],
    related_resources=[],
    metadata={"operation": "greeting"}
)
```

Convert to `InvokeResponse`:

```python
response = result.to_invoke_response(
    request_id=request.request_id,
    trace_id=trace_id
)
```

---

## JSON Schema Validation

### Request Validation

The Gateway validates requests against JSON Schema:

```python
# gateway/validator.py

REQUEST_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["request_id", "agent_id", "query"],
    "properties": {
        "request_id": {
            "type": "string",
            "format": "uuid"
        },
        "agent_id": {
            "type": "string",
            "pattern": "^[a-z][a-z0-9._-]{2,63}$"
        },
        "query": {
            "type": "string",
            "minLength": 1,
            "maxLength": 10000
        }
        # ... other fields
    }
}

def validate_request(request: dict) -> list:
    """Validate request against schema. Returns list of errors."""
    errors = []
    try:
        jsonschema.validate(request, REQUEST_SCHEMA)
    except jsonschema.ValidationError as e:
        errors.append({
            "path": list(e.path),
            "message": e.message,
            "expected": e.schema.get("expected"),
            "actual": e.instance
        })
    return errors
```

### Agent-Specific Schema

Agents can define their own input schema:

```python
class MyAgentHandler(BaseAgentHandler):
    def get_input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "minLength": 10,
                    "description": "Detailed query required"
                }
            }
        }
```

---

## Response Building

### Using Helper Methods

```python
class MyAgentHandler(BaseAgentHandler):
    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        # Success response
        return self._success(
            text="## Operation Complete\n\nSuccess!",
            structured_output={"result": "success"},
            suggested_actions=[
                self._action("next", "invoke", "Next Step", {"query": "next"})
            ],
            related_resources=[
                self._resource("deployment", "my-app", "My App")
            ],
            metadata={"operation": "complete"}
        )

        # Error response
        return self._error(
            code="INPUT_MISSING_FIELD",
            message="Required field missing",
            details={"field": "query"}
        )
```

### Building Actions

```python
# Invoke action
action = self._action(
    "deploy",
    "invoke",
    "Deploy Application",
    params={"agent_id": "nexusops.deploy", "query": "deploy my-app"},
    confirm_required=True
)

# Navigate action
action = self._action(
    "view-dashboard",
    "navigate",
    "View Dashboard",
    params={"url": "/dashboard"}
)

# External link
action = self._action(
    "docs",
    "external",
    "View Documentation",
    params={"url": "https://docs.example.com"}
)

# Dangerous action
action = self._action(
    "delete",
    "invoke",
    "Delete Resource",
    params={"agent_id": "nexusops.k8s", "query": "delete pod my-pod"},
    confirm_required=True,
    danger=True
)
```

---

## Backward Compatibility

### Adding Fields

New optional fields can be added without breaking compatibility:

```json
{
  "new_optional_field": "value"  // OK - optional
}
```

### Required Fields

Never add required fields to existing schemas. Instead:

```json
{
  "new_field": {
    "type": "string",
    "default": "default_value"  // Provide default
  }
}
```

### Versioning

Use API versioning for breaking changes:

```
/api/v1/agents/{agent_id}/invoke  -> Current
/api/v2/agents/{agent_id}/invoke  -> New version
```

---

## Examples

### Minimal Request

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_id": "nexusops.chat",
  "query": "Hello"
}
```

### Minimal Success Response

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "trace_id": "a1b2c3d4e5f67890a1b2c3d4e5f67890",
  "status": "success",
  "content": {
    "text": "Hello! How can I help?",
    "format": "markdown"
  }
}
```

### Error Response

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
      "agent_id": "invalid.agent"
    },
    "doc_url": "https://docs.nexusops.io/errors/AGENT_NOT_FOUND"
  }
}
```

---

## Next Steps

- [Error Handling](./error-handling.md) - Learn about error codes and handling
- [Gateway API](../api-reference/gateway-api.md) - Full API reference
- [Testing Guide](./testing-guide.md) - Test contract compliance
