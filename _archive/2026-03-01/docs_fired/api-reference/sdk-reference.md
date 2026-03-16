# SDK Reference

## Overview

This document provides detailed reference for the NexusOps SDK, available in Python and TypeScript.

---

## Installation

### Python

```bash
pip install nexusops-sdk
```

### TypeScript/JavaScript

```bash
npm install @nexusops/sdk
# or
yarn add @nexusops/sdk
```

---

## Python SDK

### Client Initialization

```python
from nexusops import NexusOpsClient

# Initialize with API key
client = NexusOpsClient(
    api_key="your-api-key",
    base_url="https://api.nexusops.io"  # Optional, defaults to production
)

# Initialize with custom configuration
client = NexusOpsClient(
    api_key="your-api-key",
    base_url="https://api.nexusops.io",
    timeout=60.0,
    max_retries=3,
    retry_delay=1.0
)
```

### Invoke Agent

```python
import asyncio

async def main():
    # Basic invocation
    result = await client.invoke(
        agent_id="nexusops.chat",
        query="What is the status of my deployment?"
    )

    print(f"Status: {result.status}")
    print(f"Response: {result.content.text}")

    # With context
    result = await client.invoke(
        agent_id="nexusops.k8s",
        query="Get logs for my-app",
        context={
            "project_id": "proj-123",
            "namespace": "production"
        }
    )

    # With output configuration
    result = await client.invoke(
        agent_id="nexusops.chat",
        query="Summarize deployment",
        output_config={
            "format": "json",
            "max_tokens": 2000
        }
    )

    # Access structured output
    if result.structured_output:
        data = result.structured_output
        print(f"Structured data: {data}")

asyncio.run(main())
```

### Synchronous Client

```python
from nexusops import NexusOpsSyncClient

client = NexusOpsSyncClient(api_key="your-api-key")

# Synchronous invocation
result = client.invoke(
    agent_id="nexusops.chat",
    query="Hello"
)
```

### Error Handling

```python
from nexusops import NexusOpsClient
from nexusops.errors import (
    NexusOpsError,
    AuthenticationError,
    AgentNotFoundError,
    RateLimitError,
    TimeoutError
)

async def safe_invoke():
    client = NexusOpsClient(api_key="your-api-key")

    try:
        result = await client.invoke(
            agent_id="nexusops.chat",
            query="Hello"
        )
        return result

    except AuthenticationError as e:
        print(f"Authentication failed: {e}")
    except AgentNotFoundError as e:
        print(f"Agent not found: {e.agent_id}")
    except RateLimitError as e:
        print(f"Rate limited. Retry after {e.retry_after} seconds")
        await asyncio.sleep(e.retry_after)
        # Retry
    except TimeoutError as e:
        print(f"Request timed out: {e}")
    except NexusOpsError as e:
        print(f"API error: {e.code} - {e.message}")
```

### List Agents

```python
async def list_agents():
    # List all agents
    agents = await client.list_agents()

    for agent in agents:
        print(f"{agent.agent_id}: {agent.name}")

    # Filter by type
    builtin_agents = await client.list_agents(type="builtin")

    # Filter by capability
    deploy_agents = await client.list_agents(capability="deployment")

    # Pagination
    page1 = await client.list_agents(page=1, limit=10)
    page2 = await client.list_agents(page=2, limit=10)
```

### Get Agent Details

```python
async def get_agent():
    agent = await client.get_agent("nexusops.k8s")

    print(f"Name: {agent.name}")
    print(f"Version: {agent.version}")
    print(f"Capabilities: {agent.capabilities}")
    print(f"Tools: {[t.name for t in agent.tools]}")
```

### Get Agent Manifest

```python
async def get_manifest():
    manifest = await client.get_agent_manifest("nexusops.k8s")

    print(f"Input Schema: {manifest.input_schema}")
    print(f"Output Schema: {manifest.output_schema}")
```

### Invocation History

```python
async def get_history():
    # Get recent invocations
    history = await client.get_invocations()

    for inv in history:
        print(f"{inv.agent_id}: {inv.status} ({inv.latency_ms}ms)")

    # Filter by agent
    chat_history = await client.get_invocations(agent_id="nexusops.chat")

    # Filter by date range
    recent = await client.get_invocations(
        start_date="2026-02-01",
        end_date="2026-02-25"
    )
```

### Streaming (Beta)

```python
async def stream_response():
    async for chunk in client.stream(
        agent_id="nexusops.chat",
        query="Tell me a long story"
    ):
        print(chunk.text, end="", flush=True)
```

---

## TypeScript SDK

### Client Initialization

```typescript
import { NexusOpsClient } from '@nexusops/sdk';

// Initialize with API key
const client = new NexusOpsClient({
  apiKey: 'your-api-key',
  baseUrl: 'https://api.nexusops.io' // Optional
});

// With custom configuration
const client = new NexusOpsClient({
  apiKey: 'your-api-key',
  baseUrl: 'https://api.nexusops.io',
  timeout: 60000,
  maxRetries: 3,
  retryDelay: 1000
});
```

### Invoke Agent

```typescript
// Basic invocation
const result = await client.invoke({
  agentId: 'nexusops.chat',
  query: 'What is the status of my deployment?'
});

console.log(`Status: ${result.status}`);
console.log(`Response: ${result.content.text}`);

// With context
const result = await client.invoke({
  agentId: 'nexusops.k8s',
  query: 'Get logs for my-app',
  context: {
    project_id: 'proj-123',
    namespace: 'production'
  }
});

// With output configuration
const result = await client.invoke({
  agentId: 'nexusops.chat',
  query: 'Summarize deployment',
  outputConfig: {
    format: 'json',
    maxTokens: 2000
  }
});

// Access structured output
if (result.structuredOutput) {
  console.log('Structured data:', result.structuredOutput);
}

// Access suggested actions
for (const action of result.suggestedActions) {
  console.log(`Action: ${action.label} (${action.type})`);
}
```

### Error Handling

```typescript
import {
  NexusOpsClient,
  NexusOpsError,
  AuthenticationError,
  AgentNotFoundError,
  RateLimitError,
  TimeoutError
} from '@nexusops/sdk';

async function safeInvoke() {
  const client = new NexusOpsClient({ apiKey: 'your-api-key' });

  try {
    const result = await client.invoke({
      agentId: 'nexusops.chat',
      query: 'Hello'
    });
    return result;

  } catch (error) {
    if (error instanceof AuthenticationError) {
      console.error('Authentication failed:', error.message);
    } else if (error instanceof AgentNotFoundError) {
      console.error('Agent not found:', error.agentId);
    } else if (error instanceof RateLimitError) {
      console.error(`Rate limited. Retry after ${error.retryAfter} seconds`);
      await new Promise(r => setTimeout(r, error.retryAfter * 1000));
      // Retry
    } else if (error instanceof TimeoutError) {
      console.error('Request timed out:', error.message);
    } else if (error instanceof NexusOpsError) {
      console.error(`API error: ${error.code} - ${error.message}`);
    }
  }
}
```

### List Agents

```typescript
// List all agents
const { agents, pagination } = await client.listAgents();

for (const agent of agents) {
  console.log(`${agent.agentId}: ${agent.name}`);
}

// Filter by type
const builtinAgents = await client.listAgents({ type: 'builtin' });

// Filter by capability
const deployAgents = await client.listAgents({ capability: 'deployment' });

// Pagination
const page1 = await client.listAgents({ page: 1, limit: 10 });
const page2 = await client.listAgents({ page: 2, limit: 10 });
```

### Get Agent Details

```typescript
const agent = await client.getAgent('nexusops.k8s');

console.log(`Name: ${agent.name}`);
console.log(`Version: ${agent.version}`);
console.log(`Capabilities: ${agent.capabilities.join(', ')}`);
console.log(`Tools: ${agent.tools.map(t => t.name).join(', ')}`);
```

### Invocation History

```typescript
// Get recent invocations
const { invocations, pagination } = await client.getInvocations();

for (const inv of invocations) {
  console.log(`${inv.agentId}: ${inv.status} (${inv.latencyMs}ms)`);
}

// Filter by agent
const chatHistory = await client.getInvocations({
  agentId: 'nexusops.chat'
});

// Filter by date range
const recent = await client.getInvocations({
  startDate: '2026-02-01',
  endDate: '2026-02-25'
});
```

### Streaming (Beta)

```typescript
const stream = await client.stream({
  agentId: 'nexusops.chat',
  query: 'Tell me a long story'
});

for await (const chunk of stream) {
  process.stdout.write(chunk.text);
}
```

### React Hooks

```typescript
import { useAgent, useInvoke, useAgents } from '@nexusops/sdk/react';

function MyComponent() {
  // Get agent details
  const { agent, loading, error } = useAgent('nexusops.chat');

  // List agents
  const { agents } = useAgents({ type: 'builtin' });

  // Invoke agent
  const [invoke, { result, loading: invoking }] = useInvoke();

  const handleQuery = async () => {
    const res = await invoke({
      agentId: 'nexusops.chat',
      query: 'Hello'
    });
    console.log(res.content.text);
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h1>{agent?.name}</h1>
      <button onClick={handleQuery} disabled={invoking}>
        {invoking ? 'Invoking...' : 'Invoke'}
      </button>
      {result && <div>{result.content.text}</div>}
    </div>
  );
}
```

---

## Type Definitions

### Python Types

```python
from nexusops.types import (
    InvokeRequest,
    InvokeResponse,
    Agent,
    AgentManifest,
    ToolDefinition,
    ResponseContent,
    SuggestedAction,
    RelatedResource,
    ErrorDetail,
)

# InvokeRequest
request = InvokeRequest(
    request_id="uuid",
    agent_id="nexusops.chat",
    query="Hello",
    context={"user_id": "user-123"},
    output_config={"format": "markdown"}
)

# InvokeResponse
response = InvokeResponse(
    request_id="uuid",
    trace_id="trace-123",
    status="success",
    content=ResponseContent(text="Hello!", format="markdown"),
    structured_output={"key": "value"},
    suggested_actions=[
        SuggestedAction(id="1", type="invoke", label="Next")
    ]
)
```

### TypeScript Types

```typescript
import type {
  InvokeRequest,
  InvokeResponse,
  Agent,
  AgentManifest,
  ToolDefinition,
  ResponseContent,
  SuggestedAction,
  RelatedResource,
  ErrorDetail,
  InvokeOptions,
  ListAgentsOptions,
  GetInvocationsOptions
} from '@nexusops/sdk';

// InvokeRequest
interface InvokeRequest {
  requestId: string;
  agentId: string;
  query: string;
  context?: Record<string, any>;
  outputConfig?: OutputConfig;
  tools?: ToolOverride[];
}

// InvokeResponse
interface InvokeResponse {
  requestId: string;
  traceId: string;
  status: 'success' | 'error' | 'partial' | 'pending';
  content: ResponseContent;
  structuredOutput?: any;
  suggestedActions: SuggestedAction[];
  relatedResources: RelatedResource[];
  toolCalls?: ToolCall[];
  metadata?: ResponseMetadata;
  error?: ErrorDetail;
}

// Agent
interface Agent {
  agentId: string;
  name: string;
  version: string;
  type: 'builtin' | 'remote';
  status: 'active' | 'inactive';
  capabilities: string[];
  description: string;
  tools: ToolDefinition[];
}

// SuggestedAction
interface SuggestedAction {
  id: string;
  type: 'invoke' | 'navigate' | 'copy' | 'external';
  label: string;
  params?: Record<string, any>;
  confirmRequired?: boolean;
  danger?: boolean;
}
```

---

## Configuration Options

### Client Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `apiKey` | string | Required | API key for authentication |
| `baseUrl` | string | `https://api.nexusops.io` | API base URL |
| `timeout` | number | 30000 | Request timeout in ms |
| `maxRetries` | number | 3 | Max retry attempts |
| `retryDelay` | number | 1000 | Base retry delay in ms |
| `headers` | object | {} | Additional headers |

### Invoke Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `timeout` | number | Client default | Override timeout |
| `retryOnRateLimit` | boolean | true | Auto-retry on rate limit |
| `stream` | boolean | false | Enable streaming |

---

## Middleware

### Python Middleware

```python
from nexusops import NexusOpsClient
from nexusops.middleware import LoggingMiddleware, RetryMiddleware

client = NexusOpsClient(
    api_key="your-api-key",
    middleware=[
        LoggingMiddleware(logger=my_logger),
        RetryMiddleware(max_retries=5)
    ]
)
```

### Custom Middleware

```python
from nexusops.middleware import Middleware

class TimingMiddleware(Middleware):
    async def before_request(self, request):
        request.context['start_time'] = time.time()
        return request

    async def after_response(self, response):
        duration = time.time() - response.context['start_time']
        print(f"Request took {duration:.2f}s")
        return response

client = NexusOpsClient(
    api_key="your-api-key",
    middleware=[TimingMiddleware()]
)
```

---

## Best Practices

### 1. Reuse Client Instance

```python
# Good: Reuse client
client = NexusOpsClient(api_key="your-api-key")

async def handle_request(query):
    return await client.invoke("nexusops.chat", query)

# Bad: Create new client each time
async def handle_request(query):
    client = NexusOpsClient(api_key="your-api-key")  # Don't do this
    return await client.invoke("nexusops.chat", query)
```

### 2. Handle Errors Gracefully

```python
async def safe_invoke(agent_id: str, query: str):
    try:
        return await client.invoke(agent_id, query)
    except RateLimitError as e:
        await asyncio.sleep(e.retry_after)
        return await client.invoke(agent_id, query)
    except NexusOpsError as e:
        logger.error(f"Invoke failed: {e}")
        return None
```

### 3. Use Context Managers

```python
async with NexusOpsClient(api_key="your-api-key") as client:
    result = await client.invoke("nexusops.chat", "Hello")
```

### 4. Configure Timeouts Appropriately

```python
# Long-running operations
result = await client.invoke(
    "nexusops.k8s",
    "deploy to production",
    timeout=120000  # 2 minutes
)
```

---

## Next Steps

- [Gateway API](./gateway-api.md) - Full API reference
- [Webhook Spec](./webhook-spec.md) - Webhook integration
- [Best Practices](../best-practices/performance.md) - Performance tips
