# Invoke API Contract

**Feature**: 001-agent-market-gateway
**Date**: 2026-03-01
**Version**: 1.0.0

## Overview

The Invoke API provides a unified interface for invoking both built-in and third-party agents. All agents use the same request/response contract.

---

## Base URL

```
POST /api/v1/invoke
```

---

## Request Schema

```json
{
  "request_id": "string (required) - Client-generated unique request ID",
  "conversation_id": "string (optional) - Session ID for multi-turn conversations",
  "agent_id": "string (required) - Target agent ID, pattern: ^[a-z][a-z0-9._-]{2,63}$",
  "query": "string (required, 1-10000 chars) - User input",
  "context": {
    "user_id": "string (optional)",
    "tenant_id": "string (optional)",
    "project_id": "string (optional)",
    "version_id": "string (optional)",
    "codename": "string (optional)",
    "region": "string (optional)",
    "resource_type": "string (optional)",
    "resource_name": "string (optional)",
    "namespace": "string (optional)",
    "extra": "object (optional) - Additional context"
  },
  "output_config": {
    "format": "string (default: markdown) - markdown, json, or plain",
    "max_tokens": "integer (optional, 1-32000)",
    "structured_output_schema": "object (optional) - JSON schema for structured output"
  },
  "tools": [
    {
      "name": "string (required) - Tool name",
      "enabled": "boolean (default: true)",
      "params": "object (optional) - Tool parameters"
    }
  ]
}
```

### Example Request

```json
{
  "request_id": "req-abc123",
  "agent_id": "nexusops.k8s",
  "query": "Get pod status for my-app in production namespace",
  "context": {
    "namespace": "production",
    "project_id": "proj-001"
  }
}
```

---

## Response Schema

```json
{
  "request_id": "string - Echoed from request",
  "trace_id": "string - Distributed trace ID for debugging",
  "status": "string - success, error, partial, or pending",
  "content": {
    "text": "string - Response text",
    "format": "string - markdown, json, or plain",
    "data": "any (optional) - Structured data"
  },
  "structured_output": "any (optional) - Structured output matching schema",
  "suggested_actions": [
    {
      "id": "string - Action identifier",
      "type": "string - invoke, navigate, copy, or external",
      "label": "string - Button text",
      "params": "object (optional) - Action parameters",
      "confirm_required": "boolean (default: false)",
      "danger": "boolean (default: false) - Destructive action warning"
    }
  ],
  "related_resources": [
    {
      "type": "string - Resource type",
      "id": "string - Resource identifier",
      "name": "string - Resource name",
      "link": "string (optional) - Link to resource"
    }
  ],
  "tool_calls": [
    {
      "tool_id": "string",
      "tool_name": "string (optional)",
      "input": "object (optional)",
      "output": "any (optional)",
      "status": "string - success, error, or skipped",
      "duration_ms": "integer (optional)",
      "error": "ErrorDetail (optional)"
    }
  ],
  "metadata": {
    "trace_id": "string",
    "agent_version": "string (optional)",
    "latency_ms": "integer (optional)",
    "tokens_used": {
      "input": "integer (optional)",
      "output": "integer (optional)"
    },
    "retry_count": "integer (optional)",
    "cache_hit": "boolean (optional)",
    "agent_type": "string (optional) - builtin, remote, mock",
    "execution_mode": "string (optional)"
  },
  "error": {
    "code": "string - Error code pattern: ^[A-Z][A-Z0-9_]{2,31}$",
    "message": "string - Human-readable error message",
    "details": "object (optional) - Additional error details",
    "retry_after": "integer (optional) - Seconds to wait before retry",
    "doc_url": "string (optional) - Link to error documentation"
  }
}
```

### Example Success Response

```json
{
  "request_id": "req-abc123",
  "trace_id": "trace-xyz789",
  "status": "success",
  "content": {
    "text": "## Pod Status: my-app\n\n| Pod | Status | Ready | Restarts |\n|-----|--------|-------|----------|\n| my-app-7d8f9c-x2k4m | Running | 1/1 | 0 |",
    "format": "markdown"
  },
  "suggested_actions": [
    {
      "id": "view-logs",
      "type": "invoke",
      "label": "View Logs",
      "params": {
        "agent_id": "nexusops.logs",
        "query": "logs for my-app-7d8f9c-x2k4m"
      }
    }
  ],
  "metadata": {
    "trace_id": "trace-xyz789",
    "agent_version": "1.2.0",
    "latency_ms": 342
  }
}
```

### Example Error Response

```json
{
  "request_id": "req-abc123",
  "trace_id": "trace-xyz789",
  "status": "error",
  "content": {
    "text": "Failed to get pod status",
    "format": "plain"
  },
  "error": {
    "code": "AGENT_UNAVAILABLE",
    "message": "Agent nexusops.k8s is currently unavailable",
    "details": {
      "agent_id": "nexusops.k8s",
      "last_heartbeat": "2026-03-01T02:00:00Z"
    },
    "retry_after": 30
  }
}
```

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_REQUEST` | 400 | Request validation failed |
| `AGENT_NOT_FOUND` | 404 | Agent ID does not exist |
| `AGENT_UNAVAILABLE` | 503 | Agent is not responding |
| `AGENT_NOT_INSTALLED` | 400 | Agent not installed for this user |
| `RATE_LIMIT_EXCEEDED` | 429 | Rate limit exceeded |
| `CIRCUIT_OPEN` | 503 | Circuit breaker is open |
| `TIMEOUT` | 504 | Agent invocation timed out |
| `INTERNAL_ERROR` | 500 | Internal server error |

---

## Streaming (WebSocket)

For streaming responses, connect to `/ws` and send:

```json
{
  "type": "invoke",
  "request_id": "stream-001",
  "agent_id": "nexusops.logs",
  "query": "Stream logs for my-app",
  "streaming": true
}
```

### Stream Chunk Format

```json
{
  "type": "chunk",
  "request_id": "stream-001",
  "trace_id": "trace-abc",
  "sequence": 1,
  "content": {
    "text": "partial response...",
    "format": "markdown"
  },
  "done": false
}
```

### Stream Completion

```json
{
  "type": "complete",
  "request_id": "stream-001",
  "trace_id": "trace-abc",
  "status": "success",
  "metadata": {
    "latency_ms": 1234,
    "chunks_sent": 10
  }
}
```

---

## Rate Limiting

- Default: 60 requests per minute per agent per caller
- Burst: 10 requests
- Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

---

## Versioning

The contract is versioned. Include `Accept-Version: 1` header to specify version. Current version: 1.0.0
