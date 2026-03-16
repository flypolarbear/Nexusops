# Agent Lifecycle

## Overview

This document describes the complete lifecycle of a NexusOps Agent, from registration to invocation to deactivation. Understanding the lifecycle is essential for building robust, maintainable agents.

---

## Lifecycle States

```
+-------------+     register()     +-------------+
|  Uncreated  | -----------------> |  Registered |
+-------------+                    +-------------+
                                         |
                     activate()          |
                    +----------->  +-------------+
                    |              |   Active    | <------+
                    |              +-------------+        |
                    |                    |               |
                    |              deactivate()    invoke()
                    |                    |               |
                    |                    v               |
                    |              +-------------+       |
                    +------------ |  Inactive   | ------+
                                   +-------------+
                                         |
                                   unregister()
                                         |
                                         v
                                   +-------------+
                                   |  Removed    |
                                   +-------------+
```

### State Definitions

| State | Description | Invocable |
|-------|-------------|-----------|
| Uncreated | Agent code exists but not registered | No |
| Registered | Agent registered but not active | No |
| Active | Agent is active and can receive requests | Yes |
| Inactive | Agent is temporarily disabled | No |
| Removed | Agent is unregistered from the system | No |

---

## Lifecycle Phases

### 1. Registration Phase

Registration makes an agent known to the system.

#### Built-in Agent Registration

Built-in agents are registered automatically in `BuiltinExecutor`:

```python
# backend/app/gateway/executor/builtin.py

class BuiltinExecutor(BaseExecutor):
    def __init__(self):
        self._handlers: Dict[str, Callable] = {}
        self._register_builtin_handlers()

    def _register_builtin_handlers(self):
        from app.agents import (
            ChatAgentHandler,
            K8sAgentHandler,
            # ... other handlers
        )

        self._handlers = {
            "nexusops.chat": ChatAgentHandler(),
            "nexusops.k8s": K8sAgentHandler(),
            # ... other mappings
        }
```

#### Third-Party Agent Registration

Third-party agents are registered via the Agent Market API:

```python
# Register a third-party agent
POST /api/v1/agent-market/agents
{
    "agent_id": "third-party.analytics",
    "name": "Analytics Agent",
    "version": "1.0.0",
    "type": "remote",
    "endpoint": "https://analytics-agent.example.com",
    "capabilities": ["data_analysis", "reporting"],
    "auth_config": {
        "type": "api_key",
        "api_key": "secret-key"
    }
}
```

### 2. Activation Phase

Activation makes an agent available for invocations.

#### Automatic Activation

Built-in agents are activated automatically upon registration:

```python
# Built-in agents are always active after registration
# No explicit activation needed
```

#### Manual Activation

Third-party agents may require manual activation:

```python
# Activate an agent
POST /api/v1/agent-market/agents/{agent_id}/activate

# Response
{
    "agent_id": "third-party.analytics",
    "status": "active",
    "activated_at": "2026-02-25T00:00:00Z"
}
```

### 3. Invocation Phase

During invocation, the agent processes requests.

#### Invocation Flow

```
1. Request received at Gateway
   |
   v
2. ExecutorRouter resolves agent
   |
   v
3. pre_execute() hook (optional)
   | - Can short-circuit with cached result
   | - Can reject request
   v
4. execute() - Main processing
   | - Agent handler processes query
   | - Calls external services
   | - Builds result
   v
5. post_execute() hook (optional)
   | - Can modify result
   | - Can add metadata
   v
6. Response returned to client
```

#### Pre-Execute Hook

Use `pre_execute` for caching, validation, or short-circuiting:

```python
class MyAgentHandler(BaseAgentHandler):
    async def pre_execute(self, request: ExecutorRequest) -> Optional[ExecutorResult]:
        # Check cache
        cache_key = self._build_cache_key(request)
        cached = await self._cache.get(cache_key)

        if cached:
            # Return cached result, skip execute()
            return ExecutorResult(
                success=True,
                content={"text": cached, "format": "markdown"},
                metadata={"cache_hit": True}
            )

        # Continue to execute()
        return None
```

#### Post-Execute Hook

Use `post_execute` for logging, transformation, or enrichment:

```python
class MyAgentHandler(BaseAgentHandler):
    async def post_execute(
        self,
        request: ExecutorRequest,
        result: ExecutorResult
    ) -> ExecutorResult:
        # Log execution
        await self._log_execution(request, result)

        # Add metadata
        result.metadata["processed_at"] = datetime.utcnow().isoformat()

        # Cache successful results
        if result.success:
            cache_key = self._build_cache_key(request)
            await self._cache.set(cache_key, result.content["text"], ttl=300)

        return result
```

### 4. Deactivation Phase

Deactivation temporarily disables an agent without removing it.

```python
# Deactivate an agent
POST /api/v1/agent-market/agents/{agent_id}/deactivate

# Response
{
    "agent_id": "third-party.analytics",
    "status": "inactive",
    "deactivated_at": "2026-02-25T00:00:00Z"
}
```

Deactivated agents return `AGENT_INACTIVE` error:

```json
{
    "status": "error",
    "error": {
        "code": "AGENT_INACTIVE",
        "message": "Agent is not active",
        "details": {
            "agent_id": "third-party.analytics",
            "status": "inactive"
        }
    }
}
```

### 5. Unregistration Phase

Unregistration permanently removes an agent from the system.

```python
# Unregister an agent
DELETE /api/v1/agent-market/agents/{agent_id}

# Response
{
    "agent_id": "third-party.analytics",
    "status": "removed",
    "removed_at": "2026-02-25T00:00:00Z"
}
```

---

## Agent Handler Interface

### Base Class

All agents must inherit from `BaseAgentHandler`:

```python
from app.agents.base import BaseAgentHandler
from app.gateway.executor.base import ExecutorRequest, ExecutorResult

class MyAgentHandler(BaseAgentHandler):
    @property
    def agent_id(self) -> str:
        """Unique agent identifier"""
        return "nexusops.myagent"

    @property
    def capabilities(self) -> List[str]:
        """List of agent capabilities"""
        return ["capability1", "capability2"]

    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        """Main request handler"""
        # Process request and return result
        pass
```

### Required Properties

| Property | Type | Description |
|----------|------|-------------|
| `agent_id` | `str` | Unique identifier (format: `nexusops.{category}`) |
| `capabilities` | `List[str]` | List of capability identifiers |

### Required Methods

| Method | Description |
|--------|-------------|
| `handle(request)` | Process request and return result |

### Optional Methods

| Method | Description |
|--------|-------------|
| `get_tools()` | Return tool definitions |
| `get_manifest()` | Return full agent manifest |

---

## Context Management

### RequestContext

The `RequestContext` provides information about the request environment:

```python
class RequestContext(BaseModel):
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    project_id: Optional[str] = None
    version_id: Optional[str] = None
    codename: Optional[str] = None
    region: Optional[str] = None
    resource_type: Optional[str] = None
    resource_name: Optional[str] = None
    namespace: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None
```

### Accessing Context

```python
async def handle(self, request: ExecutorRequest) -> ExecutorResult:
    context = request.request_context

    user_id = context.get("user_id")
    project_id = context.get("project_id")
    region = context.get("region", "us-east")  # Default value

    # Use context for authorization, filtering, etc.
    if not self._check_permission(user_id, project_id):
        return self._error(
            code="AUTH_PERMISSION_DENIED",
            message="User does not have permission"
        )
```

---

## State Management

### Stateless Agents (Recommended)

Most agents should be stateless, processing each request independently:

```python
class StatelessAgent(BaseAgentHandler):
    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        # Process without relying on previous state
        result = await self._process(request.query)
        return self._success(text=result)
```

### Stateful Agents

For multi-turn conversations, use external state storage:

```python
class StatefulAgent(BaseAgentHandler):
    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        conversation_id = request.context.conversation_id

        # Get previous state
        state = await self._get_state(conversation_id)

        # Process with context
        result = await self._process(request.query, state)

        # Save updated state
        await self._save_state(conversation_id, result.state)

        return self._success(text=result.text)

    async def _get_state(self, conversation_id: str) -> dict:
        # Get from Redis
        redis = get_redis()
        data = await redis.get(f"agent:state:{conversation_id}")
        return json.loads(data) if data else {}

    async def _save_state(self, conversation_id: str, state: dict):
        # Save to Redis with TTL
        redis = get_redis()
        await redis.set(
            f"agent:state:{conversation_id}",
            json.dumps(state),
            ex=3600  # 1 hour TTL
        )
```

---

## Health Checking

### Executor Health Check

Executors implement `health_check()` for monitoring:

```python
class BuiltinExecutor(BaseExecutor):
    async def health_check(self) -> bool:
        # Check if all handlers are healthy
        for agent_id, handler in self._handlers.items():
            if hasattr(handler, 'health_check'):
                if not await handler.health_check():
                    return False
        return True
```

### Agent Health Check

Agents can implement custom health checks:

```python
class MyAgentHandler(BaseAgentHandler):
    async def health_check(self) -> bool:
        # Check external dependencies
        try:
            await self._check_database_connection()
            await self._check_api_connection()
            return True
        except Exception:
            return False
```

---

## Versioning

### Agent Versioning

Agents can be versioned for backward compatibility:

```python
class MyAgentHandler(BaseAgentHandler):
    def _get_version(self) -> str:
        return "2.0.0"

    def get_manifest(self) -> Dict[str, Any]:
        manifest = super().get_manifest()
        manifest["version"] = self._get_version()
        manifest["compatibility"] = ["1.0.0", "1.5.0", "2.0.0"]
        return manifest
```

### Version-Specific Handling

```python
async def handle(self, request: ExecutorRequest) -> ExecutorResult:
    requested_version = request.context.agent_version

    if requested_version.startswith("1."):
        return await self._handle_v1(request)
    else:
        return await self._handle_v2(request)
```

---

## Graceful Shutdown

### Handling Shutdown Signals

Agents should handle shutdown gracefully:

```python
class MyAgentHandler(BaseAgentHandler):
    def __init__(self):
        self._shutdown = False
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        import signal

        def handle_shutdown(signum, frame):
            self._shutdown = True

        signal.signal(signal.SIGTERM, handle_shutdown)
        signal.signal(signal.SIGINT, handle_shutdown)

    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        if self._shutdown:
            return self._error(
                code="AGENT_BUSY",
                message="Agent is shutting down"
            )

        # Normal processing
        return await self._process(request)
```

---

## Best Practices

### 1. Idempotency

Design agents to handle duplicate requests safely:

```python
async def handle(self, request: ExecutorRequest) -> ExecutorResult:
    # Use request_id for idempotency
    request_id = request.context.request_id

    # Check if already processed
    existing = await self._get_result(request_id)
    if existing:
        return existing

    # Process and store
    result = await self._process(request)
    await self._store_result(request_id, result)

    return result
```

### 2. Timeout Handling

Always set timeouts for external calls:

```python
async def _call_external_api(self, url: str) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)
        return response.json()
```

### 3. Resource Cleanup

Clean up resources after processing:

```python
async def handle(self, request: ExecutorRequest) -> ExecutorResult:
    conn = None
    try:
        conn = await self._get_connection()
        result = await self._process(conn, request)
        return result
    finally:
        if conn:
            await conn.close()
```

---

## Next Steps

- [Contract Specification](./contract-specification.md) - Learn about request/response contracts
- [Error Handling](./error-handling.md) - Handle errors gracefully
- [Testing Guide](./testing-guide.md) - Test your agents thoroughly
