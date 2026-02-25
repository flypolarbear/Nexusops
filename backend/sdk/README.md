# NexusOps Python SDK

A Python SDK for interacting with the NexusOps Agent API. Provides both synchronous and asynchronous interfaces for agent registration, invocation, and management.

## Installation

```bash
pip install nexusops-sdk
```

Or with poetry:

```bash
poetry add nexusops-sdk
```

## Requirements

- Python 3.10+
- httpx
- pydantic
- tenacity

## Quick Start

### Initialize the Client

```python
from nexusops_sdk import AgentClient, AgentConfig

# Initialize with configuration
client = AgentClient(config=AgentConfig(
    base_url="https://nexusops.example.com",
    api_key="your-api-key",
    timeout=30.0,
    max_retries=3,
))
```

### Using Context Manager

```python
from nexusops_sdk import AgentClient, AgentConfig

# Synchronous context manager
with AgentClient(config=AgentConfig(
    base_url="https://nexusops.example.com",
    api_key="your-api-key",
)) as client:
    agents = client.agents.list()
    print(f"Found {agents.total} agents")

# Asynchronous context manager
async with AgentClient(config=AgentConfig(
    base_url="https://nexusops.example.com",
    api_key="your-api-key",
)) as client:
    agents = await client.agents.list_async()
    print(f"Found {agents.total} agents")
```

## Agent Discovery

### List All Agents

```python
# Synchronous
agents = client.agents.list()
for agent in agents.agents:
    print(f"- {agent.name} ({agent.agent_id})")
    print(f"  Capabilities: {agent.capabilities}")

# Asynchronous
agents = await client.agents.list_async()
```

### Get Agent Details

```python
# Synchronous
agent = client.agents.get("nexusops.k8s")
print(f"Name: {agent.name}")
print(f"Version: {agent.version}")
print(f"Capabilities: {agent.capabilities}")

# Asynchronous
agent = await client.agents.get_async("nexusops.k8s")
```

### Get Agent Tools

```python
tools = client.agents.get_tools("nexusops.chat")
for tool in tools:
    print(f"- {tool['name']}: {tool['description']}")
```

## Agent Invocation

### Synchronous Invocation

```python
# Simple query
result = client.agents.invoke(
    agent_id="nexusops.chat",
    query="What is the status of production deployment?"
)
print(result.content.text)

# Action-based invocation
result = client.agents.invoke(
    agent_id="nexusops.k8s",
    action="get_pods",
    params={"namespace": "production"}
)
print(result.content.text)

# With context
from nexusops_sdk import AgentRequestContext

result = client.agents.invoke(
    agent_id="nexusops.deploy",
    query="Deploy version 1.2.3 to us-west-2",
    context=AgentRequestContext(
        user_id="user-123",
        project_id="project-456",
        region="us-west-2",
    )
)
```

### Asynchronous Invocation

```python
import asyncio
from nexusops_sdk import AgentClient, AgentConfig

async def main():
    async with AgentClient(config=AgentConfig(
        base_url="https://nexusops.example.com",
        api_key="your-api-key",
    )) as client:
        result = await client.agents.invoke_async(
            agent_id="nexusops.k8s",
            action="get_pods",
            params={"namespace": "production"}
        )
        print(result.content.text)

asyncio.run(main())
```

### Handling Responses

```python
result = client.agents.invoke(
    agent_id="nexusops.k8s",
    action="get_pods",
    params={"namespace": "production"}
)

# Check status
if result.status == "success":
    print(f"Text: {result.content.text}")
    print(f"Format: {result.content.format}")

    # Structured output (if available)
    if result.structured_output:
        print(f"Data: {result.structured_output}")

    # Suggested actions
    for action in result.suggested_actions:
        print(f"Action: {action.label}")
        if action.confirm_required:
            print("  Requires confirmation!")

    # Related resources
    for resource in result.related_resources:
        print(f"Resource: {resource.name} ({resource.type})")

elif result.status == "error":
    print(f"Error: {result.error.code} - {result.error.message}")
```

## Agent Registration

### Register a Custom Agent

```python
# Synchronous
registration = client.agents.register(
    agent_id="my-custom-agent",
    name="My Custom Agent",
    capabilities=["data-processing", "report-generation"],
    endpoint="https://my-agent.example.com/webhook",
    version="1.0.0",
    description="A custom agent for data processing",
    category="custom",
)

print(f"Registered: {registration.agent_id}")
print(f"Status: {registration.status}")

# Asynchronous
registration = await client.agents.register_async(
    agent_id="my-custom-agent",
    name="My Custom Agent",
    capabilities=["data-processing", "report-generation"],
    endpoint="https://my-agent.example.com/webhook",
)
```

### Register with Tools

```python
tools = [
    {
        "name": "process_data",
        "description": "Process data files",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "format": {"type": "string", "enum": ["csv", "json"]},
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "generate_report",
        "description": "Generate a report from processed data",
        "inputSchema": {
            "type": "object",
            "properties": {
                "template": {"type": "string"},
                "output_format": {"type": "string", "enum": ["pdf", "html"]},
            },
        },
    },
]

client.agents.register(
    agent_id="data-processor",
    name="Data Processor Agent",
    capabilities=["data-processing", "report-generation"],
    tools=tools,
    endpoint="https://data-processor.example.com/webhook",
)
```

## Error Handling

```python
from nexusops_sdk import (
    AgentClient,
    AgentConfig,
    NexusOpsError,
    AgentNotFoundError,
    AgentTimeoutError,
    AuthenticationError,
    AgentNotInstalledError,
    AgentDisabledError,
    RateLimitError,
)

try:
    result = client.agents.invoke(
        agent_id="non-existent-agent",
        query="Hello"
    )
except AgentNotFoundError as e:
    print(f"Agent not found: {e.agent_id}")
except AgentNotInstalledError as e:
    print(f"Agent not installed: {e.agent_id}")
    # Prompt user to install the agent
except AgentDisabledError as e:
    print(f"Agent is disabled: {e.agent_id}")
    # Prompt user to enable the agent
except AgentTimeoutError as e:
    print(f"Request timed out after {e.timeout_seconds}s")
    # Retry with longer timeout or queue for later
except AuthenticationError as e:
    print(f"Authentication failed: {e.message}")
    # Check API key
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
    # Wait and retry
except NexusOpsError as e:
    print(f"API error: [{e.code}] {e.message}")
```

## Configuration Options

```python
from nexusops_sdk import AgentConfig

config = AgentConfig(
    base_url="https://nexusops.example.com",  # Required: NexusOps server URL
    api_key="your-api-key",                   # Required: API key for authentication
    timeout=30.0,                             # Optional: Request timeout (default: 30s)
    max_retries=3,                            # Optional: Max retry attempts (default: 3)
    retry_delay=1.0,                          # Optional: Base delay between retries (default: 1s)
    verify_ssl=True,                          # Optional: Verify SSL certificates (default: True)
)

client = AgentClient(config=config)
```

## API Reference

### AgentClient

Main client class for interacting with the NexusOps API.

| Method | Description |
|--------|-------------|
| `agents` | Namespace for agent operations |
| `close()` | Close the client and release resources |
| `close_async()` | Close the async client |

### AgentsNamespace

Namespace for agent-related operations.

| Method | Sync | Async | Description |
|--------|------|-------|-------------|
| `register()` | Yes | Yes | Register a new agent |
| `invoke()` | Yes | Yes | Invoke an agent |
| `list()` | Yes | Yes | List all available agents |
| `get()` | Yes | Yes | Get agent details |
| `get_tools()` | Yes | Yes | Get agent tools |

### Models

| Model | Description |
|-------|-------------|
| `AgentConfig` | Client configuration |
| `AgentManifest` | Agent metadata and capabilities |
| `AgentInvokeRequest` | Request to invoke an agent |
| `AgentInvokeResponse` | Response from agent invocation |
| `AgentRequestContext` | Context for agent requests |
| `AgentRegistrationRequest` | Request to register an agent |
| `AgentRegistrationResponse` | Response from agent registration |

### Exceptions

| Exception | Description |
|-----------|-------------|
| `NexusOpsError` | Base exception for all SDK errors |
| `AgentNotFoundError` | Agent does not exist |
| `AgentTimeoutError` | Request timed out |
| `AuthenticationError` | Authentication failed |
| `AuthorizationError` | Authorization failed |
| `AgentNotInstalledError` | Agent not installed |
| `AgentDisabledError` | Agent is disabled |
| `ValidationError` | Invalid parameters |
| `ConnectionError` | Connection failed |
| `RateLimitError` | Rate limit exceeded |

## License

MIT License
