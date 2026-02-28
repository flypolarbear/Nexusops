# Quick Start Guide

## Overview

This guide will help you create your first NexusOps Agent in under 10 minutes. You will learn how to:

1. Create a basic agent handler
2. Register the agent with the Gateway
3. Test the agent via API
4. Add capabilities and tools

---

## Prerequisites

- Completed [Installation Guide](./installation.md)
- Backend server running on `http://localhost:8000`
- Basic understanding of Python async/await

---

## Step 1: Create Your Agent Handler

All agents extend the `BaseAgentHandler` class. Create a new file in `backend/app/agents/`:

```python
# backend/app/agents/hello.py

from typing import List, Dict, Any
from app.agents.base import BaseAgentHandler
from app.gateway.executor.base import ExecutorRequest, ExecutorResult


class HelloAgentHandler(BaseAgentHandler):
    """A simple greeting agent"""

    @property
    def agent_id(self) -> str:
        return "nexusops.hello"

    @property
    def capabilities(self) -> List[str]:
        return ["greeting", "introduction"]

    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        """Handle the request and return a greeting"""
        query = request.query
        context = request.request_context

        # Get user info from context
        user_id = context.get("user_id", "Guest")

        # Return success response
        return self._success(
            text=f"## Hello, {user_id}!\n\nYou asked: '{query}'\n\nHow can I help you today?",
            structured_output={
                "greeting": f"Hello, {user_id}!",
                "query": query
            },
            metadata={"operation": "greeting"}
        )
```

---

## Step 2: Register Your Agent

Add your agent to the `__init__.py` file:

```python
# backend/app/agents/__init__.py

from .base import BaseAgentHandler
from .chat import ChatAgentHandler
from .k8s import K8sAgentHandler
from .deploy import DeployAgentHandler
from .dns import DnsAgentHandler
from .logs import LogsAgentHandler
from .cost import CostAgentHandler
from .hello import HelloAgentHandler  # Add this line

__all__ = [
    "BaseAgentHandler",
    "ChatAgentHandler",
    "K8sAgentHandler",
    "DeployAgentHandler",
    "DnsAgentHandler",
    "LogsAgentHandler",
    "CostAgentHandler",
    "HelloAgentHandler",  # Add this line
]
```

---

## Step 3: Register with BuiltinExecutor

The `BuiltinExecutor` automatically loads handlers. Update the registration:

```python
# backend/app/gateway/executor/builtin.py

from app.agents import (
    ChatAgentHandler,
    K8sAgentHandler,
    DeployAgentHandler,
    DnsAgentHandler,
    LogsAgentHandler,
    CostAgentHandler,
    HelloAgentHandler,  # Import
)

# In _register_builtin_handlers():
self._handlers = {
    "nexusops.chat": ChatAgentHandler(),
    "nexusops.k8s": K8sAgentHandler(),
    "nexusops.deploy": DeployAgentHandler(),
    "nexusops.dns": DnsAgentHandler(),
    "nexusops.logs": LogsAgentHandler(),
    "nexusops.cost": CostAgentHandler(),
    "nexusops.hello": HelloAgentHandler(),  # Register
}
```

---

## Step 4: Test Your Agent

### Using cURL

```bash
curl -X POST http://localhost:8000/api/v1/agents/nexusops.hello/invoke \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-token" \
  -d '{
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "agent_id": "nexusops.hello",
    "query": "What can you do?",
    "context": {
      "user_id": "developer"
    }
  }'
```

### Expected Response

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "trace_id": "a1b2c3d4e5f67890a1b2c3d4e5f67890",
  "status": "success",
  "content": {
    "text": "## Hello, developer!\n\nYou asked: 'What can you do?'\n\nHow can I help you today?",
    "format": "markdown"
  },
  "structured_output": {
    "greeting": "Hello, developer!",
    "query": "What can you do?"
  },
  "suggested_actions": [],
  "related_resources": [],
  "metadata": {
    "trace_id": "a1b2c3d4e5f67890a1b2c3d4e5f67890",
    "operation": "greeting"
  }
}
```

### Using Python

```python
import httpx
import uuid

async def test_hello_agent():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/agents/nexusops.hello/invoke",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer your-token"
            },
            json={
                "request_id": str(uuid.uuid4()),
                "agent_id": "nexusops.hello",
                "query": "Hello world!",
                "context": {"user_id": "test-user"}
            }
        )
        return response.json()
```

---

## Step 5: Add Tools (Optional)

Tools define the actions your agent can perform. Override `get_tools()`:

```python
def get_tools(self) -> List[Dict[str, Any]]:
    return [
        {
            "name": "greet_user",
            "description": "Generate a personalized greeting",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "User's name"},
                    "style": {
                        "type": "string",
                        "enum": ["formal", "casual", "friendly"],
                        "default": "friendly"
                    }
                },
                "required": ["name"]
            }
        },
        {
            "name": "get_time",
            "description": "Get current time in a timezone",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "default": "UTC"
                    }
                }
            }
        }
    ]
```

---

## Step 6: Add Suggested Actions

Guide users with suggested follow-up actions:

```python
async def handle(self, request: ExecutorRequest) -> ExecutorResult:
    # ... process query ...

    return self._success(
        text=response_text,
        suggested_actions=[
            self._action(
                "learn-more",
                "invoke",
                "Learn more about this topic",
                {"agent_id": "nexusops.hello", "query": "tell me more"}
            ),
            self._action(
                "docs-link",
                "external",
                "View documentation",
                {"url": "https://docs.nexusops.io"}
            ),
        ]
    )
```

---

## Step 7: Handle Errors Gracefully

Use the `_error()` helper for error responses:

```python
async def handle(self, request: ExecutorRequest) -> ExecutorResult:
    query = request.query

    # Validate input
    if not query or len(query.strip()) == 0:
        return self._error(
            code="INPUT_MISSING_FIELD",
            message="Query cannot be empty",
            details={"field": "query"}
        )

    # Handle unsupported operations
    if "unsupported" in query.lower():
        return self._error(
            code="AGENT_INPUT_REJECTED",
            message="This operation is not supported",
            details={"reason": "Feature not implemented"}
        )

    # ... normal processing ...
```

---

## Complete Example

Here is a complete agent with all features:

```python
# backend/app/agents/weather.py

from typing import List, Dict, Any
from app.agents.base import BaseAgentHandler
from app.gateway.executor.base import ExecutorRequest, ExecutorResult


class WeatherAgentHandler(BaseAgentHandler):
    """Weather information agent"""

    @property
    def agent_id(self) -> str:
        return "nexusops.weather"

    @property
    def capabilities(self) -> List[str]:
        return ["weather_query", "forecast", "alerts"]

    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        query = request.query.lower()
        context = request.request_context

        # Parse location from query
        location = self._extract_location(query)
        if not location:
            return self._error(
                code="INPUT_MISSING_FIELD",
                message="Please specify a location",
                details={"example": "weather in San Francisco"}
            )

        # Get weather data (mock implementation)
        weather_data = await self._fetch_weather(location)

        return self._success(
            text=f"""## Weather in {location}

**Condition:** {weather_data['condition']}
**Temperature:** {weather_data['temp']}C
**Humidity:** {weather_data['humidity']}%

### 3-Day Forecast
{self._format_forecast(weather_data['forecast'])}
""",
            structured_output=weather_data,
            suggested_actions=[
                self._action(
                    "detailed-forecast",
                    "invoke",
                    "View detailed forecast",
                    {"agent_id": "nexusops.weather", "query": f"detailed forecast {location}"}
                ),
            ],
            related_resources=[
                self._resource("location", location, location, f"https://weather.com/{location}")
            ],
            metadata={"location": location, "operation": "weather_query"}
        )

    def _extract_location(self, query: str) -> str:
        """Extract location from query"""
        # Simple extraction logic
        words = query.split()
        for i, word in enumerate(words):
            if word in ["in", "at", "for"] and i + 1 < len(words):
                return words[i + 1]
        return None

    async def _fetch_weather(self, location: str) -> Dict[str, Any]:
        """Fetch weather data (mock)"""
        return {
            "location": location,
            "condition": "Partly Cloudy",
            "temp": 22,
            "humidity": 65,
            "forecast": [
                {"day": "Today", "high": 24, "low": 18},
                {"day": "Tomorrow", "high": 26, "low": 19},
                {"day": "Wednesday", "high": 23, "low": 17},
            ]
        }

    def _format_forecast(self, forecast: List[Dict]) -> str:
        """Format forecast as markdown table"""
        rows = [f"| {f['day']} | {f['high']}C | {f['low']}C |" for f in forecast]
        return "| Day | High | Low |\n|-----|------|-----|\n" + "\n".join(rows)

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "get_weather",
                "description": "Get current weather for a location",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"},
                        "units": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                    },
                    "required": ["location"]
                }
            }
        ]
```

---

## Testing Your Agent

Create unit tests for your agent:

```python
# backend/tests/agents/test_weather.py

import pytest
from app.agents.weather import WeatherAgentHandler
from app.gateway.executor.base import ExecutorRequest, ExecutorContext


@pytest.fixture
def handler():
    return WeatherAgentHandler()


@pytest.fixture
def make_request():
    def _make(query: str, context: dict = None):
        return ExecutorRequest(
            context=ExecutorContext(
                trace_id="test-trace",
                request_id="test-request",
                agent_id="nexusops.weather"
            ),
            query=query,
            request_context=context or {}
        )
    return _make


@pytest.mark.asyncio
async def test_weather_query_success(handler, make_request):
    request = make_request("weather in Tokyo")
    result = await handler.handle(request)

    assert result.success
    assert "Tokyo" in result.content["text"]
    assert result.structured_output["location"] == "Tokyo"


@pytest.mark.asyncio
async def test_weather_missing_location(handler, make_request):
    request = make_request("what's the weather")
    result = await handler.handle(request)

    assert not result.success
    assert result.error["code"] == "INPUT_MISSING_FIELD"


def test_agent_metadata(handler):
    assert handler.agent_id == "nexusops.weather"
    assert "weather_query" in handler.capabilities
    assert len(handler.get_tools()) > 0
```

Run tests:

```bash
pytest backend/tests/agents/test_weather.py -v
```

---

## Next Steps

- Read [Agent Lifecycle](../agent-development/agent-lifecycle.md) for detailed lifecycle management
- Learn about [Contract Specification](../agent-development/contract-specification.md)
- Explore [Error Handling](../agent-development/error-handling.md) best practices
- Review [Testing Guide](../agent-development/testing-guide.md) for comprehensive testing

---

## FAQ

### Q: How do I access external APIs in my agent?

Use `httpx` for async HTTP calls:

```python
import httpx

async def _fetch_data(self, url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10.0)
        return response.json()
```

### Q: How do I store state between requests?

Use the `conversation_id` to correlate requests and store state in Redis or the database:

```python
from app.stores import get_redis

async def handle(self, request: ExecutorRequest) -> ExecutorResult:
    redis = get_redis()
    conversation_id = request.context.conversation_id

    # Get previous state
    state = await redis.get(f"conv:{conversation_id}")

    # ... process ...

    # Save state
    await redis.set(f"conv:{conversation_id}", new_state, ex=3600)
```

### Q: How do I implement streaming responses?

Streaming is not yet supported in the current version. It is planned for a future release (see SPEC-MK-006 Non-Goals).
