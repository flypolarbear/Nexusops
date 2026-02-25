# Error Handling

## Overview

This document describes the NexusOps error handling system, including error codes, exception classes, and best practices for handling errors in agent development.

---

## Error Code Taxonomy

### Format

Error codes follow the format: `{CATEGORY}_{SUBCATEGORY}_{SPECIFIC}`

- **CATEGORY**: Top-level error category
- **SUBCATEGORY**: Specific area within category
- **SPECIFIC**: Exact error condition

### Categories

| Category | Prefix | HTTP Status Range | Description |
|----------|--------|-------------------|-------------|
| Input | `INPUT_` | 400 | Client input validation errors |
| Auth | `AUTH_` | 401, 403, 429 | Authentication and authorization errors |
| Agent | `AGENT_` | 404, 409, 422 | Agent-specific errors |
| Execution | `EXEC_` | 500, 502, 504 | Execution and downstream errors |
| System | `SYSTEM_` | 500, 503 | System-level errors |

---

## Complete Error Code Reference

### Input Validation Errors (INPUT_*)

| Code | HTTP | Message | Retryable |
|------|------|---------|-----------|
| `INPUT_INVALID_JSON` | 400 | Invalid JSON body | No |
| `INPUT_SCHEMA_VIOLATION` | 400 | Request schema validation failed | No |
| `INPUT_MISSING_FIELD` | 400 | Required field missing: {field} | No |
| `INPUT_INVALID_FORMAT` | 400 | Invalid format for field: {field} | No |
| `INPUT_VALUE_OUT_OF_RANGE` | 400 | Value out of range for field: {field} | No |
| `INPUT_QUERY_TOO_LONG` | 400 | Query exceeds maximum length | No |
| `INPUT_INVALID_AGENT_ID` | 400 | Invalid agent_id format | No |

### Authentication/Authorization Errors (AUTH_*)

| Code | HTTP | Message | Retryable |
|------|------|---------|-----------|
| `AUTH_TOKEN_MISSING` | 401 | Authorization token required | No |
| `AUTH_TOKEN_INVALID` | 401 | Invalid authorization token | No |
| `AUTH_TOKEN_EXPIRED` | 401 | Authorization token expired | Yes* |
| `AUTH_PERMISSION_DENIED` | 403 | Permission denied for this agent | No |
| `AUTH_QUOTA_EXCEEDED` | 429 | Rate limit or quota exceeded | Yes |
| `AUTH_TENANT_MISMATCH` | 403 | Tenant ID mismatch | No |

*After refreshing token

### Agent Errors (AGENT_*)

| Code | HTTP | Message | Retryable |
|------|------|---------|-----------|
| `AGENT_NOT_FOUND` | 404 | Agent not found: {agent_id} | No |
| `AGENT_INACTIVE` | 409 | Agent is not active | No |
| `AGENT_NOT_INSTALLED` | 403 | Agent is not installed | No |
| `AGENT_DISABLED` | 403 | Agent is disabled | No |
| `AGENT_VERSION_MISMATCH` | 409 | Requested version not available | No |
| `AGENT_BUSY` | 503 | Agent is temporarily unavailable | Yes |
| `AGENT_INPUT_REJECTED` | 422 | Agent rejected the input | No |
| `AGENT_OUTPUT_INVALID` | 422 | Agent returned invalid output | Yes |
| `AGENT_ENDPOINT_MISSING` | 500 | No endpoint configured for remote agent | No |

### Execution Errors (EXEC_*)

| Code | HTTP | Message | Retryable |
|------|------|---------|-----------|
| `EXEC_TIMEOUT` | 504 | Execution timed out | Yes |
| `EXEC_TOOL_FAILED` | 500 | Tool execution failed: {tool} | Yes |
| `EXEC_DOWNSTREAM_ERROR` | 502 | Downstream service error | Yes |
| `EXEC_PARTIAL_FAILURE` | 500 | Partial execution failure | Yes |
| `EXEC_RESOURCE_CONFLICT` | 409 | Resource conflict detected | Yes |
| `EXEC_CIRCUIT_OPEN` | 503 | Circuit breaker is open | Yes |
| `EXEC_INTERNAL_ERROR` | 500 | Internal execution error | Yes |

### System Errors (SYSTEM_*)

| Code | HTTP | Message | Retryable |
|------|------|---------|-----------|
| `SYSTEM_INTERNAL_ERROR` | 500 | Internal server error | Yes |
| `SYSTEM_UNAVAILABLE` | 503 | Service temporarily unavailable | Yes |
| `SYSTEM_OVERLOADED` | 503 | System is overloaded | Yes |
| `SYSTEM_MAINTENANCE` | 503 | System under maintenance | No |

---

## Error Response Format

### Structure

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "trace_id": "a1b2c3d4e5f67890a1b2c3d4e5f67890",
  "status": "error",
  "content": {
    "text": "Human-readable error message",
    "format": "plain"
  },
  "error": {
    "code": "ERROR_CODE_HERE",
    "message": "Detailed error message",
    "details": {
      "field": "value",
      "additional": "context"
    },
    "retry_after": 5,
    "doc_url": "https://docs.nexusops.io/errors/ERROR_CODE_HERE"
  },
  "metadata": {
    "trace_id": "a1b2c3d4e5f67890a1b2c3d4e5f67890",
    "latency_ms": 12
  }
}
```

### ErrorDetail Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | string | Yes | Error code (pattern: `^[A-Z][A-Z0-9_]{2,31}$`) |
| `message` | string | Yes | Human-readable error message |
| `details` | object | No | Additional context |
| `retry_after` | integer | No | Suggested retry interval in seconds |
| `doc_url` | string | No | Link to documentation |

---

## Python Exception Classes

### Class Hierarchy

```
GatewayError (base)
├── InputError
├── AuthError
├── AgentError
├── ExecError
└── SystemError
```

### Using Exceptions

```python
from app.gateway.errors import (
    GatewayError,
    InputError,
    AuthError,
    AgentError,
    ExecError,
    SystemError,
    ErrorCode,
    agent_not_found,
    agent_not_installed,
    agent_disabled,
    exec_timeout,
    exec_downstream_error,
    input_schema_violation,
    input_missing_field,
)

# Raise specific errors
raise InputError(
    code=ErrorCode.INPUT_MISSING_FIELD,
    message="Required field missing: query",
    details={"field": "query"}
)

# Use helper functions
raise agent_not_found("nexusops.unknown")
raise agent_not_installed("third-party.analytics")
raise exec_timeout(30000, endpoint="https://api.example.com")
```

### Exception Properties

```python
error = AgentError(
    code=ErrorCode.AGENT_NOT_FOUND,
    message="Agent not found",
    details={"agent_id": "unknown"}
)

error.code          # ErrorCode.AGENT_NOT_FOUND
error.message       # "Agent not found"
error.details       # {"agent_id": "unknown"}
error.http_status   # 404 (auto-mapped)
error.is_retryable  # False (auto-determined)
```

---

## Handling Errors in Agents

### Using Helper Methods

```python
class MyAgentHandler(BaseAgentHandler):
    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        query = request.query

        # Validate input
        if not query:
            return self._error(
                code="INPUT_MISSING_FIELD",
                message="Query cannot be empty",
                details={"field": "query"}
            )

        # Check permissions
        if not self._check_permission(request.request_context):
            return self._error(
                code="AUTH_PERMISSION_DENIED",
                message="You don't have permission to perform this action",
                details={"required_role": "admin"}
            )

        # Process request
        try:
            result = await self._process(query)
            return self._success(text=result)
        except ExternalServiceError as e:
            return self._error(
                code="EXEC_DOWNSTREAM_ERROR",
                message=f"External service error: {e}",
                details={"service": "external-api"},
                retry_after=10
            )
```

### Error Details Best Practices

```python
# Good: Include helpful context
return self._error(
    code="INPUT_SCHEMA_VIOLATION",
    message="Invalid date format",
    details={
        "field": "date",
        "expected_format": "YYYY-MM-DD",
        "actual_value": "25/02/2026",
        "example": "2026-02-25"
    }
)

# Good: Include available options
return self._error(
    code="AGENT_NOT_FOUND",
    message="Agent not found: nexusops.unknown",
    details={
        "agent_id": "nexusops.unknown",
        "available_agents": [
            "nexusops.chat",
            "nexusops.k8s",
            "nexusops.deploy"
        ]
    }
)

# Good: Include retry guidance
return self._error(
    code="EXEC_TIMEOUT",
    message="Request timed out after 30 seconds",
    details={
        "timeout_ms": 30000,
        "suggestion": "Try reducing the scope of your query"
    },
    retry_after=5
)
```

---

## HTTP Status Code Mapping

### Automatic Mapping

```python
# gateway/errors.py

ERROR_HTTP_STATUS: Dict[ErrorCode, int] = {
    # Input - 400
    ErrorCode.INPUT_INVALID_JSON: 400,
    ErrorCode.INPUT_SCHEMA_VIOLATION: 400,
    # ...
    # Auth - 401/403
    ErrorCode.AUTH_TOKEN_MISSING: 401,
    ErrorCode.AUTH_PERMISSION_DENIED: 403,
    # ...
    # Agent - 404/409/422
    ErrorCode.AGENT_NOT_FOUND: 404,
    ErrorCode.AGENT_BUSY: 503,
    # ...
    # Exec - 500/502/504
    ErrorCode.EXEC_TIMEOUT: 504,
    ErrorCode.EXEC_DOWNSTREAM_ERROR: 502,
    # ...
}
```

### Custom HTTP Status

```python
# In FastAPI exception handler
@app.exception_handler(GatewayError)
async def gateway_error_handler(request: Request, exc: GatewayError):
    return JSONResponse(
        status_code=exc.http_status,
        content={
            "status": "error",
            "error": exc.to_error_detail().to_dict()
        }
    )
```

---

## Retryable Errors

### Definition

```python
RETRYABLE_ERRORS: set[ErrorCode] = {
    ErrorCode.AUTH_TOKEN_EXPIRED,
    ErrorCode.AUTH_QUOTA_EXCEEDED,
    ErrorCode.AGENT_BUSY,
    ErrorCode.AGENT_OUTPUT_INVALID,
    ErrorCode.EXEC_TIMEOUT,
    ErrorCode.EXEC_TOOL_FAILED,
    ErrorCode.EXEC_DOWNSTREAM_ERROR,
    ErrorCode.EXEC_PARTIAL_FAILURE,
    ErrorCode.EXEC_RESOURCE_CONFLICT,
    ErrorCode.EXEC_CIRCUIT_OPEN,
    ErrorCode.SYSTEM_INTERNAL_ERROR,
    ErrorCode.SYSTEM_UNAVAILABLE,
    ErrorCode.SYSTEM_OVERLOADED,
}
```

### Client Retry Logic

```python
import httpx
import asyncio

async def invoke_with_retry(
    agent_id: str,
    query: str,
    max_retries: int = 3
) -> dict:
    async with httpx.AsyncClient() as client:
        for attempt in range(max_retries):
            response = await client.post(
                f"{API_URL}/api/v1/agents/{agent_id}/invoke",
                json={"request_id": str(uuid.uuid4()), "agent_id": agent_id, "query": query}
            )

            data = response.json()

            if data["status"] == "success":
                return data

            error = data.get("error", {})
            retry_after = error.get("retry_after", 5)

            # Check if error is retryable
            if error.get("code") in RETRYABLE_ERROR_CODES:
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_after)
                    continue

            # Non-retryable error or max retries
            raise AgentError(error["code"], error["message"])
```

---

## Error Logging

### Structured Logging

```python
import structlog

logger = structlog.get_logger()

async def handle(self, request: ExecutorRequest) -> ExecutorResult:
    log = logger.bind(
        trace_id=request.context.trace_id,
        request_id=request.context.request_id,
        agent_id=self.agent_id
    )

    try:
        result = await self._process(request)
        log.info("request_completed", latency_ms=result.metadata.get("latency_ms"))
        return result
    except Exception as e:
        log.error(
            "request_failed",
            error_code="EXEC_INTERNAL_ERROR",
            error_message=str(e),
            exc_info=True
        )
        return self._error(
            code="EXEC_INTERNAL_ERROR",
            message=str(e)
        )
```

### Error Context

Always include trace_id in error logs for debugging:

```python
{
    "timestamp": "2026-02-25T00:00:00.000Z",
    "level": "ERROR",
    "trace_id": "a1b2c3d4e5f67890a1b2c3d4e5f67890",
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "agent_id": "nexusops.k8s",
    "event": "request_failed",
    "error_code": "EXEC_TIMEOUT",
    "error_message": "Execution timed out after 30000ms"
}
```

---

## Circuit Breaker Pattern

### Implementation

```python
from datetime import datetime, timedelta
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 30
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None

    async def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise ExecError(
                    code=ErrorCode.EXEC_CIRCUIT_OPEN,
                    message="Circuit breaker is open",
                    retry_after=self._remaining_recovery_time()
                )

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        if not self.last_failure_time:
            return True
        return datetime.utcnow() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)

    def _on_success(self):
        self.failures = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        self.failures += 1
        self.last_failure_time = datetime.utcnow()
        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
```

---

## Best Practices

### 1. Use Specific Error Codes

```python
# Bad
return self._error(code="ERROR", message="Something went wrong")

# Good
return self._error(
    code="INPUT_SCHEMA_VIOLATION",
    message="Invalid date format in query",
    details={"field": "date", "expected": "YYYY-MM-DD"}
)
```

### 2. Include Actionable Details

```python
# Bad
return self._error(
    code="AGENT_NOT_FOUND",
    message="Agent not found"
)

# Good
return self._error(
    code="AGENT_NOT_FOUND",
    message="Agent not found: third-party.analytics",
    details={
        "agent_id": "third-party.analytics",
        "suggestion": "Check if the agent is installed",
        "available_agents": ["nexusops.chat", "nexusops.k8s"]
    },
    doc_url="https://docs.nexusops.io/agents/installation"
)
```

### 3. Set Retry After for Transient Errors

```python
# For rate limiting
return self._error(
    code="AUTH_QUOTA_EXCEEDED",
    message="Rate limit exceeded",
    details={"limit": 100, "window": "1m"},
    retry_after=60
)

# For timeouts
return self._error(
    code="EXEC_TIMEOUT",
    message="Request timed out",
    details={"timeout_ms": 30000},
    retry_after=5
)
```

### 4. Log Errors with Context

```python
except Exception as e:
    logger.error(
        "agent_error",
        agent_id=self.agent_id,
        trace_id=request.context.trace_id,
        error_type=type(e).__name__,
        error_message=str(e),
        exc_info=True
    )
    return self._error(...)
```

---

## Next Steps

- [Testing Guide](./testing-guide.md) - Test error handling
- [Gateway API](../api-reference/gateway-api.md) - API error responses
- [Troubleshooting](../best-practices/troubleshooting.md) - Debug errors
