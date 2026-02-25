# NexusOps Python SDK

A Python SDK for interacting with the NexusOps Agent Gateway.

## Installation

```bash
pip install nexusops-sdk
```

## Quick Start

### Initialize the Client

```python
from nexusops_sdk import AgentClient

# With API key
client = AgentClient(
    base_url="http://localhost:8000",
    api_key="your-api-key"
)

# Or with Bearer token
client = AgentClient(
    base_url="http://localhost:8000",
    token="your-bearer-token"
)
```

### Invoke an Agent

```python
import asyncio
from nexusops_sdk import AgentClient

async def main():
    async with AgentClient(base_url="http://localhost:8000", api_key="...") as client:
        # Simple invocation
        response = await client.invoke_agent(
            agent_id="nexusops.chat",
            query="Hello, how can you help?"
        )

        print(f"Status: {response.status}")
        print(f"Response: {response.content.text}")

        # With context
        response = await client.invoke_agent(
            agent_id="nexusops.k8s",
            query="Get pod status for my-app",
            context={
                "user_id": "user-123",
                "project_id": "project-456",
                "namespace": "production"
            }
        )

asyncio.run(main())
```

### Sync Usage

```python
from nexusops_sdk import AgentClient

with AgentClient(base_url="http://localhost:8000", api_key="...") as client:
    response = client.invoke_agent_sync(
        agent_id="nexusops.chat",
        query="Hello!"
    )
    print(response.content.text)
```

### Register an Agent

```python
from nexusops_sdk import AgentClient

async def register_my_agent():
    async with AgentClient(base_url="...", api_key="...") as client:
        result = await client.register_agent(
            agent_id="mycompany.myagent",
            name="My Custom Agent",
            version="1.0.0",
            description="A custom agent for specific tasks",
            category="custom",
            capabilities=["analyze", "report"],
            endpoint="https://my-agent.example.com/invoke"
        )
        print(f"Registered: {result['agent_id']}")
```

### Install and Enable Agents

```python
from nexusops_sdk import AgentClient

async def manage_agents():
    async with AgentClient(base_url="...", api_key="...") as client:
        # Install an agent
        await client.install_agent("third.party.agent")

        # Get status
        status = await client.get_agent_status("third.party.agent")
        print(f"Install status: {status.install_status}")

        # Disable if needed
        await client.disable_agent("third.party.agent")

        # Re-enable
        await client.enable_agent("third.party.agent")

        # Uninstall
        await client.uninstall_agent("third.party.agent")
```

## Creating Custom Agents

### Using AgentBase Class

```python
from nexusops_sdk.agents import AgentBase
from nexusops_sdk.models import AgentRequest, AgentResponse

class MyCustomAgent(AgentBase):
    def __init__(self):
        super().__init__(
            agent_id="mycompany.custom",
            name="My Custom Agent",
            version="1.0.0",
            description="Does custom things",
            category="custom",
            capabilities=["custom_capability"]
        )

    async def invoke(self, request: AgentRequest) -> AgentResponse:
        # Your custom logic here
        result = process_query(request.query)

        return self.success_response(
            text=result,
            request_id=request.request_id
        )

    def get_tools(self):
        return [
            {
                "name": "custom_tool",
                "description": "A custom tool",
                "inputSchema": {"type": "object"}
            }
        ]
```

### Using Decorator

```python
from nexusops_sdk.agents import register_agent_decorator
from nexusops_sdk.models import AgentRequest, AgentResponse

@register_agent_decorator(
    agent_id="mycompany.simple",
    name="Simple Agent",
    description="A simple handler"
)
async def simple_handler(request: AgentRequest) -> AgentResponse:
    return AgentResponse(
        request_id=request.request_id,
        status="success",
        content={"text": f"Echo: {request.query}", "format": "markdown"}
    )
```

### Using Registration Builder

```python
from nexusops_sdk.agents import AgentRegistrationBuilder

manifest = (
    AgentRegistrationBuilder("mycompany.builder")
    .with_name("Builder Agent")
    .with_version("1.0.0")
    .with_description("Built with builder pattern")
    .with_category("infrastructure")
    .add_capability("deploy")
    .add_capability("rollback")
    .with_tool(
        name="deploy",
        description="Deploy application",
        input_schema={"type": "object", "properties": {"target": {"type": "string"}}}
    )
    .build()
)
```

## Error Handling

```python
from nexusops_sdk import AgentClient
from nexusops_sdk.exceptions import (
    NexusOpsError,
    AgentError,
    AuthError,
    ErrorCode
)

async def safe_invoke():
    async with AgentClient(base_url="...", api_key="...") as client:
        try:
            response = await client.invoke_agent("agent.id", "query")
        except AgentError as e:
            if e.code == ErrorCode.AGENT_NOT_FOUND:
                print("Agent not found")
            elif e.code == ErrorCode.AGENT_NOT_INSTALLED:
                print("Agent not installed")
            else:
                print(f"Agent error: {e.message}")
        except AuthError as e:
            print(f"Authentication failed: {e.message}")
        except NexusOpsError as e:
            print(f"Error: {e.code} - {e.message}")
            if e.is_retryable:
                print("This error can be retried")
```

## Response Model

```python
response = await client.invoke_agent("agent.id", "query")

# Status check
response.is_success    # True if status == "success"
response.is_error      # True if status == "error"
response.is_partial    # True if status == "partial"

# Content
response.content.text     # Response text
response.content.format   # "markdown", "json", or "plain"

# Structured output (if available)
data = response.structured_output

# Suggested actions
for action in response.suggested_actions:
    print(f"{action.label}: {action.type}")

# Related resources
for resource in response.related_resources:
    print(f"{resource.name} ({resource.type})")

# Metadata
if response.metadata:
    print(f"Latency: {response.metadata.latency_ms}ms")
    print(f"Trace ID: {response.metadata.trace_id}")

# Error (if any)
if response.error:
    print(f"Error: {response.error.code} - {response.error.message}")
```

## Trace ID Support

```python
from nexusops_sdk.utils.trace import (
    generate_trace_id,
    init_trace_context,
    get_trace_context
)

# Auto-managed by client
response = await client.invoke_agent("agent.id", "query")
print(f"Trace ID: {response.trace_id}")

# Manual context management
init_trace_context(
    request_id="my-request-id",
    agent_id="agent.id"
)

ctx = get_trace_context()
print(f"Trace ID: {ctx.trace_id}")
```

## API Reference

### AgentClient

| Method | Description |
|--------|-------------|
| `register_agent()` | Register a new agent |
| `invoke_agent()` | Invoke an agent (async) |
| `invoke_agent_sync()` | Invoke an agent (sync) |
| `get_agent_status()` | Get agent install status |
| `get_agent()` | Get agent details |
| `install_agent()` | Install an agent |
| `uninstall_agent()` | Uninstall an agent |
| `enable_agent()` | Enable a disabled agent |
| `disable_agent()` | Disable an installed agent |
| `list_agents()` | List available agents |

### Error Codes

| Category | Codes |
|----------|-------|
| Input | `INPUT_INVALID_JSON`, `INPUT_SCHEMA_VIOLATION`, `INPUT_MISSING_FIELD`, ... |
| Auth | `AUTH_TOKEN_MISSING`, `AUTH_TOKEN_INVALID`, `AUTH_PERMISSION_DENIED`, ... |
| Agent | `AGENT_NOT_FOUND`, `AGENT_NOT_INSTALLED`, `AGENT_DISABLED`, ... |
| Exec | `EXEC_TIMEOUT`, `EXEC_DOWNSTREAM_ERROR`, `EXEC_CIRCUIT_OPEN`, ... |
| System | `SYSTEM_INTERNAL_ERROR`, `SYSTEM_UNAVAILABLE`, ... |

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy .

# Linting
ruff check .
```

## License

MIT License
