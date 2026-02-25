# Troubleshooting Guide

## Overview

This guide helps you diagnose and resolve common issues when developing and deploying NexusOps agents.

---

## Common Issues

### 1. Agent Not Found

**Symptom**: `AGENT_NOT_FOUND` error when invoking agent.

**Possible Causes**:
- Agent not registered
- Typo in agent_id
- Agent deactivated

**Solutions**:

```bash
# List available agents
curl -H "Authorization: Bearer $TOKEN" \
  https://api.nexusops.io/api/v1/agents

# Check agent status
curl -H "Authorization: Bearer $TOKEN" \
  https://api.nexusops.io/api/v1/agents/nexusops.chat
```

```python
# Verify agent registration
from app.gateway.executor.builtin import BuiltinExecutor

executor = BuiltinExecutor()
registered_agents = executor.list_agents()
print("Registered agents:", registered_agents)
```

### 2. Authentication Errors

**Symptom**: `AUTH_TOKEN_MISSING`, `AUTH_TOKEN_INVALID`, or `AUTH_TOKEN_EXPIRED`.

**Solutions**:

```python
# Check token validity
import jwt

try:
    decoded = jwt.decode(token, options={"verify_signature": False})
    print(f"Token expires at: {decoded.get('exp')}")
except jwt.ExpiredSignatureError:
    print("Token expired")
except jwt.InvalidTokenError as e:
    print(f"Invalid token: {e}")
```

```bash
# Refresh token
curl -X POST https://api.nexusops.io/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "your-refresh-token"}'
```

### 3. Timeout Errors

**Symptom**: `EXEC_TIMEOUT` error.

**Possible Causes**:
- Slow external service
- Large data processing
- Network issues

**Solutions**:

```python
# Increase timeout
async def handle(self, request: ExecutorRequest) -> ExecutorResult:
    try:
        result = await asyncio.wait_for(
            self._process(request),
            timeout=60.0  # Increase timeout
        )
        return result
    except asyncio.TimeoutError:
        return self._error(
            code="EXEC_TIMEOUT",
            message="Request timed out",
            retry_after=10
        )

# Optimize slow operations
async def _process(self, request: ExecutorRequest):
    # Use concurrent processing
    results = await asyncio.gather(
        self._fetch_data(),
        self._process_query(),
        self._check_cache()
    )
    return self._combine(results)
```

### 4. Rate Limiting

**Symptom**: `AUTH_QUOTA_EXCEEDED` error.

**Solutions**:

```python
# Implement exponential backoff
async def invoke_with_backoff(agent_id: str, query: str, max_retries: int = 5):
    for attempt in range(max_retries):
        try:
            return await client.invoke(agent_id, query)
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise

            # Exponential backoff
            delay = min(e.retry_after, 2 ** attempt)
            await asyncio.sleep(delay)
```

### 5. Schema Validation Errors

**Symptom**: `INPUT_SCHEMA_VIOLATION` error.

**Solutions**:

```python
# Validate request before processing
from jsonschema import validate, ValidationError

def validate_request(request: dict, schema: dict) -> list:
    try:
        validate(request, schema)
        return []
    except ValidationError as e:
        return [{
            "path": list(e.path),
            "message": e.message,
            "validator": e.validator
        }]

# In handler
async def handle(self, request: ExecutorRequest) -> ExecutorResult:
    errors = validate_request(request.model_dump(), self.get_input_schema())
    if errors:
        return self._error(
            code="INPUT_SCHEMA_VIOLATION",
            message="Request validation failed",
            details={"validation_errors": errors}
        )
```

---

## Debugging Techniques

### Enable Debug Logging

```python
import logging

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# For specific modules
logging.getLogger("app.gateway").setLevel(logging.DEBUG)
logging.getLogger("httpx").setLevel(logging.DEBUG)
```

### Trace Request Flow

```python
import structlog

logger = structlog.get_logger()

class TracingHandler(BaseAgentHandler):
    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        log = logger.bind(
            trace_id=request.context.trace_id,
            request_id=request.context.request_id,
            agent_id=self.agent_id
        )

        log.info("handle_start", query=request.query)

        try:
            result = await self._process(request)
            log.info("handle_success", success=result.success)
            return result
        except Exception as e:
            log.error("handle_error", error=str(e), exc_info=True)
            raise
```

### Inspect Context

```python
async def handle(self, request: ExecutorRequest) -> ExecutorResult:
    # Log full context for debugging
    import json
    print("Request Context:")
    print(json.dumps(request.request_context, indent=2, default=str))

    print(f"Trace ID: {request.context.trace_id}")
    print(f"Request ID: {request.context.request_id}")
    print(f"Agent ID: {request.context.agent_id}")
    print(f"Query: {request.query}")

    # ... rest of handler
```

---

## Performance Issues

### Slow Response Times

**Diagnosis**:

```python
import time

async def handle(self, request: ExecutorRequest) -> ExecutorResult:
    timings = {}

    # Track each step
    start = time.time()
    data = await self._fetch_data()
    timings["fetch_data"] = time.time() - start

    start = time.time()
    processed = await self._process(data)
    timings["process"] = time.time() - start

    start = time.time()
    formatted = self._format(processed)
    timings["format"] = time.time() - start

    print(f"Timings: {timings}")

    return self._success(text=formatted)
```

**Solutions**:

1. **Add caching**:
```python
@lru_cache(maxsize=100)
def expensive_computation(key: str) -> str:
    # ...
```

2. **Use concurrent processing**:
```python
results = await asyncio.gather(*tasks)
```

3. **Optimize queries**:
```python
# Use indexes, limit results, select only needed columns
```

### Memory Issues

**Diagnosis**:

```python
import tracemalloc

tracemalloc.start()

# ... code ...

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics("lineno")

for stat in top_stats[:10]:
    print(stat)
```

**Solutions**:

1. **Use generators** for large datasets
2. **Clear caches** periodically
3. **Release resources** explicitly

---

## Network Issues

### Connection Errors

**Symptom**: `EXEC_DOWNSTREAM_ERROR` or connection refused.

**Diagnosis**:

```bash
# Check connectivity
curl -v https://api.example.com/health

# Check DNS
nslookup api.example.com

# Check ports
netstat -an | grep 443
```

**Solutions**:

```python
# Implement retry with circuit breaker
async def fetch_with_retry(url: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            return await client.get(url)
        except httpx.ConnectError as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)
```

### SSL/TLS Issues

**Symptom**: SSL certificate errors.

**Solutions**:

```python
# For development only - never in production!
import ssl
import httpx

# Create unverified context (development only!)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

client = httpx.AsyncClient(verify=ssl_context)
```

---

## Database Issues

### Connection Pool Exhaustion

**Symptom**: Timeout waiting for database connection.

**Solutions**:

```python
# Increase pool size
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True
)

# Ensure connections are released
async def get_data():
    async with AsyncSession(engine) as session:
        # Session is automatically closed
        result = await session.execute(query)
        return result.scalars().all()
```

### Slow Queries

**Diagnosis**:

```python
# Enable query logging
import logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
```

**Solutions**:

1. Add indexes
2. Use `explain analyze`
3. Limit result sets
4. Use connection pooling

---

## Error Analysis

### Parse Error Details

```python
def analyze_error(response: dict) -> str:
    error = response.get("error", {})
    code = error.get("code", "UNKNOWN")
    message = error.get("message", "Unknown error")
    details = error.get("details", {})
    retry_after = error.get("retry_after")

    analysis = f"Error Code: {code}\n"
    analysis += f"Message: {message}\n"

    if details:
        analysis += f"Details: {json.dumps(details, indent=2)}\n"

    if retry_after:
        analysis += f"Retry after: {retry_after} seconds\n"

    # Suggest resolution
    suggestions = {
        "AGENT_NOT_FOUND": "Check if the agent is registered and active",
        "AUTH_TOKEN_EXPIRED": "Refresh your authentication token",
        "AUTH_QUOTA_EXCEEDED": "Wait before retrying or upgrade your plan",
        "EXEC_TIMEOUT": "Optimize your query or increase timeout",
    }

    if code in suggestions:
        analysis += f"Suggestion: {suggestions[code]}\n"

    return analysis
```

### Check Trace Logs

```bash
# Search logs by trace_id
grep "a1b2c3d4e5f67890a1b2c3d4e5f67890" /var/log/nexusops/*.log

# Or using structured logging
cat logs.json | jq 'select(.trace_id == "a1b2c3d4e5f67890a1b2c3d4e5f67890")'
```

---

## Health Checks

### Agent Health Check

```python
async def health_check(self) -> dict:
    """Comprehensive health check."""
    checks = {}

    # Check database
    try:
        await self._check_database()
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {e}"

    # Check cache
    try:
        await self._check_cache()
        checks["cache"] = "healthy"
    except Exception as e:
        checks["cache"] = f"unhealthy: {e}"

    # Check external APIs
    try:
        await self._check_external_api()
        checks["external_api"] = "healthy"
    except Exception as e:
        checks["external_api"] = f"unhealthy: {e}"

    overall = all(v == "healthy" for v in checks.values())

    return {
        "status": "healthy" if overall else "unhealthy",
        "checks": checks
    }
```

### System Health Check

```bash
# Check all components
curl https://api.nexusops.io/health

# Response
{
  "status": "healthy",
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

## Support Resources

### Log Collection

```bash
# Collect relevant logs
tar -czf nexusops-logs-$(date +%Y%m%d).tar.gz \
  /var/log/nexusops/*.log \
  --transform 's,^,nexusops-logs/,'
```

### Diagnostic Information

```python
def collect_diagnostics() -> dict:
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "python_version": sys.version,
        "platform": platform.platform(),
        "environment": {
            "NEXUSOPS_VERSION": os.environ.get("NEXUSOPS_VERSION"),
            "ENVIRONMENT": os.environ.get("ENVIRONMENT"),
        },
        "config": {
            "log_level": LOG_LEVEL,
            "debug_mode": DEBUG_MODE,
        }
    }
```

### Getting Help

1. **Documentation**: Check `/docs` directory
2. **Search Issues**: GitHub Issues
3. **Community**: Discord/Slack
4. **Support Email**: support@nexusops.io

When contacting support, provide:
- Trace ID
- Error code and message
- Timestamp
- Steps to reproduce

---

## FAQ

### Q: Why is my agent returning partial results?

A: Check for `EXEC_PARTIAL_FAILURE` status. This indicates some operations succeeded while others failed. Review `tool_calls` in the response for details.

### Q: How do I debug webhook delivery failures?

A: Check the webhook delivery logs in the dashboard. Verify your endpoint returns 200 within 10 seconds and the signature is correctly verified.

### Q: Why are my requests being rate limited?

A: Check the `X-RateLimit-Remaining` header. If it's near 0, you've exceeded your quota. Consider upgrading or implementing request batching.

### Q: How do I test agent locally?

A: Use the test fixtures and mock external services. See [Testing Guide](../agent-development/testing-guide.md).

---

## Next Steps

- [Error Handling](../agent-development/error-handling.md) - Error handling guide
- [Performance Best Practices](./performance.md) - Optimize performance
- [Security Best Practices](./security.md) - Security guidelines
