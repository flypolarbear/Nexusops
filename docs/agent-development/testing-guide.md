# Testing Guide

## Overview

This guide covers testing strategies and best practices for NexusOps agents. It includes unit testing, integration testing, and contract testing approaches.

---

## Testing Pyramid

```
        +-----------------+
        |    E2E Tests    |  (Few, Slow, Expensive)
        +-----------------+
       /                   \
      /   Integration Tests \  (Some, Medium)
     +-----------------------+
    /                         \
   /      Unit Tests           \ (Many, Fast, Cheap)
  +-----------------------------+
```

| Level | Count | Speed | Purpose |
|-------|-------|-------|---------|
| Unit | Many | Fast | Test individual functions |
| Integration | Some | Medium | Test component interactions |
| E2E | Few | Slow | Test complete workflows |

---

## Test Setup

### Directory Structure

```
backend/
+-- tests/
|   +-- conftest.py           # Shared fixtures
|   +-- agents/
|   |   +-- test_chat.py
|   |   +-- test_k8s.py
|   |   +-- test_deploy.py
|   +-- gateway/
|   |   +-- test_contract.py
|   |   +-- test_errors.py
|   |   +-- test_executor.py
|   +-- integration/
|   |   +-- test_invoke_flow.py
|   +-- e2e/
|       +-- test_full_flow.py
```

### Test Configuration

```python
# tests/conftest.py

import pytest
import asyncio
from typing import Generator

from app.agents.base import BaseAgentHandler
from app.gateway.executor.base import ExecutorRequest, ExecutorContext


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def make_executor_request():
    """Factory fixture for creating ExecutorRequest."""
    def _make(
        query: str,
        agent_id: str = "nexusops.test",
        context: dict = None,
        trace_id: str = "test-trace-123",
        request_id: str = "test-request-456"
    ) -> ExecutorRequest:
        return ExecutorRequest(
            context=ExecutorContext(
                trace_id=trace_id,
                request_id=request_id,
                agent_id=agent_id
            ),
            query=query,
            request_context=context or {}
        )
    return _make


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    class MockRedis:
        def __init__(self):
            self._data = {}

        async def get(self, key):
            return self._data.get(key)

        async def set(self, key, value, ex=None):
            self._data[key] = value

        async def delete(self, key):
            self._data.pop(key, None)

    return MockRedis()
```

---

## Unit Testing

### Testing Agent Handlers

```python
# tests/agents/test_chat.py

import pytest
from app.agents.chat import ChatAgentHandler
from app.gateway.executor.base import ExecutorRequest, ExecutorContext


@pytest.fixture
def handler():
    return ChatAgentHandler()


class TestChatAgentHandler:
    """Tests for ChatAgentHandler."""

    def test_agent_id(self, handler):
        """Test agent_id property."""
        assert handler.agent_id == "nexusops.chat"

    def test_capabilities(self, handler):
        """Test capabilities property."""
        capabilities = handler.capabilities
        assert "chat" in capabilities
        assert "quick_commands" in capabilities

    @pytest.mark.asyncio
    async def test_handle_general_chat(self, handler, make_executor_request):
        """Test general chat handling."""
        request = make_executor_request(query="Hello, how are you?")
        result = await handler.handle(request)

        assert result.success
        assert "Hello" in result.content["text"]
        assert result.metadata.get("operation") == "chat"

    @pytest.mark.asyncio
    async def test_handle_deploy_command(self, handler, make_executor_request):
        """Test /deploy command handling."""
        request = make_executor_request(
            query="/deploy v1.2.3 to us-east",
            context={"codename": "v1.2.3", "region": "us-east"}
        )
        result = await handler.handle(request)

        assert result.success
        assert "Deployment" in result.content["text"]
        assert result.structured_output is not None
        assert result.structured_output["type"] == "deployment_status"

    @pytest.mark.asyncio
    async def test_handle_status_command(self, handler, make_executor_request):
        """Test /status command handling."""
        request = make_executor_request(
            query="/status v1.2.3",
            context={"codename": "v1.2.3"}
        )
        result = await handler.handle(request)

        assert result.success
        assert "v1.2.3" in result.content["text"]
        assert "Status" in result.content["text"]

    @pytest.mark.asyncio
    async def test_suggested_actions_included(self, handler, make_executor_request):
        """Test that suggested actions are included."""
        request = make_executor_request(query="/deploy v1.0.0")
        result = await handler.handle(request)

        assert len(result.suggested_actions) > 0
        assert all("id" in action for action in result.suggested_actions)
        assert all("type" in action for action in result.suggested_actions)

    def test_get_tools(self, handler):
        """Test tool definitions."""
        tools = handler.get_tools()

        assert len(tools) > 0
        assert all("name" in tool for tool in tools)
        assert all("inputSchema" in tool for tool in tools)

    def test_get_manifest(self, handler):
        """Test manifest generation."""
        manifest = handler.get_manifest()

        assert manifest["agent_id"] == "nexusops.chat"
        assert "name" in manifest
        assert "version" in manifest
        assert "capabilities" in manifest
```

### Testing Error Handling

```python
# tests/agents/test_error_handling.py

import pytest
from app.agents.base import BaseAgentHandler
from app.gateway.executor.base import ExecutorRequest, ExecutorContext


class ValidationAgentHandler(BaseAgentHandler):
    """Test agent with validation."""

    @property
    def agent_id(self) -> str:
        return "nexusops.validation"

    @property
    def capabilities(self):
        return ["validation"]

    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        if not request.query:
            return self._error(
                code="INPUT_MISSING_FIELD",
                message="Query is required",
                details={"field": "query"}
            )

        if len(request.query) < 5:
            return self._error(
                code="INPUT_VALUE_OUT_OF_RANGE",
                message="Query too short",
                details={"min_length": 5, "actual_length": len(request.query)}
            )

        return self._success(text=f"Processed: {request.query}")


@pytest.fixture
def handler():
    return ValidationAgentHandler()


class TestErrorHandling:
    """Tests for error handling in agents."""

    @pytest.mark.asyncio
    async def test_missing_query_error(self, handler, make_executor_request):
        """Test error for missing query."""
        request = make_executor_request(query="")
        result = await handler.handle(request)

        assert not result.success
        assert result.error["code"] == "INPUT_MISSING_FIELD"
        assert "query" in result.error["details"]["field"]

    @pytest.mark.asyncio
    async def test_query_too_short_error(self, handler, make_executor_request):
        """Test error for query too short."""
        request = make_executor_request(query="Hi")
        result = await handler.handle(request)

        assert not result.success
        assert result.error["code"] == "INPUT_VALUE_OUT_OF_RANGE"
        assert result.error["details"]["min_length"] == 5

    @pytest.mark.asyncio
    async def test_success_with_valid_input(self, handler, make_executor_request):
        """Test success with valid input."""
        request = make_executor_request(query="Hello world")
        result = await handler.handle(request)

        assert result.success
        assert "Processed" in result.content["text"]
```

### Testing with Mocks

```python
# tests/agents/test_with_mocks.py

import pytest
from unittest.mock import AsyncMock, patch
from app.agents.weather import WeatherAgentHandler


@pytest.fixture
def handler():
    return WeatherAgentHandler()


class TestWeatherAgentWithMocks:
    """Tests with mocked external services."""

    @pytest.mark.asyncio
    async def test_fetch_weather_success(self, handler, make_executor_request):
        """Test successful weather fetch."""
        with patch.object(
            handler,
            '_fetch_weather',
            new_callable=AsyncMock,
            return_value={
                "location": "Tokyo",
                "condition": "Sunny",
                "temp": 25,
                "humidity": 60,
                "forecast": []
            }
        ):
            request = make_executor_request(query="weather in Tokyo")
            result = await handler.handle(request)

            assert result.success
            assert "Tokyo" in result.content["text"]
            assert result.structured_output["temp"] == 25

    @pytest.mark.asyncio
    async def test_fetch_weather_timeout(self, handler, make_executor_request):
        """Test handling of weather service timeout."""
        with patch.object(
            handler,
            '_fetch_weather',
            new_callable=AsyncMock,
            side_effect=TimeoutError("Service timeout")
        ):
            request = make_executor_request(query="weather in Tokyo")

            with pytest.raises(TimeoutError):
                await handler.handle(request)

    @pytest.mark.asyncio
    async def test_with_httpx_mock(self, handler, make_executor_request):
        """Test with mocked HTTP client."""
        import httpx

        mock_response = {
            "location": "London",
            "condition": "Rainy",
            "temp": 15,
            "humidity": 80,
            "forecast": []
        }

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = mock_client.return_value.__aenter__.return_value
            mock_instance.get = AsyncMock(
                return_value=httpx.Response(200, json=mock_response)
            )

            request = make_executor_request(query="weather in London")
            result = await handler.handle(request)

            assert result.success
```

---

## Integration Testing

### Testing Executor Flow

```python
# tests/integration/test_executor.py

import pytest
from app.gateway.executor.router import ExecutorRouter
from app.gateway.executor.builtin import BuiltinExecutor
from app.gateway.executor.remote import RemoteExecutor


@pytest.fixture
def router():
    return ExecutorRouter()


class TestExecutorRouter:
    """Integration tests for ExecutorRouter."""

    @pytest.mark.asyncio
    async def test_route_builtin_agent(self, router):
        """Test routing to builtin executor."""
        result = await router.route_and_execute(
            agent_id="nexusops.chat",
            trace_id="test-trace-123",
            request_id="test-request-456",
            query="Hello",
            request_context={}
        )

        assert result.success
        assert result.content["format"] == "markdown"

    @pytest.mark.asyncio
    async def test_route_unknown_agent(self, router):
        """Test routing to unknown agent."""
        result = await router.route_and_execute(
            agent_id="nexusops.unknown",
            trace_id="test-trace-123",
            request_id="test-request-456",
            query="Hello",
            request_context={}
        )

        assert not result.success
        assert result.error["code"] == "AGENT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_trace_id_propagation(self, router):
        """Test that trace_id is propagated."""
        trace_id = "a1b2c3d4e5f67890a1b2c3d4e5f67890"

        result = await router.route_and_execute(
            agent_id="nexusops.chat",
            trace_id=trace_id,
            request_id="test-request-456",
            query="Hello",
            request_context={}
        )

        # Verify trace_id in metadata
        assert result.metadata.get("trace_id") == trace_id
```

### Testing Full Invoke Flow

```python
# tests/integration/test_invoke_flow.py

import pytest
import httpx
from httpx import AsyncClient
from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


class TestInvokeFlow:
    """Integration tests for full invoke flow."""

    @pytest.mark.asyncio
    async def test_invoke_success(self, client: AsyncClient):
        """Test successful agent invocation."""
        response = await client.post(
            "/api/v1/agents/nexusops.chat/invoke",
            json={
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "agent_id": "nexusops.chat",
                "query": "Hello"
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "trace_id" in data
        assert data["trace_id"] is not None

    @pytest.mark.asyncio
    async def test_invoke_agent_not_found(self, client: AsyncClient):
        """Test invocation of non-existent agent."""
        response = await client.post(
            "/api/v1/agents/nexusops.unknown/invoke",
            json={
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "agent_id": "nexusops.unknown",
                "query": "Hello"
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 404
        data = response.json()
        assert data["status"] == "error"
        assert data["error"]["code"] == "AGENT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_invoke_validation_error(self, client: AsyncClient):
        """Test invocation with invalid request."""
        response = await client.post(
            "/api/v1/agents/nexusops.chat/invoke",
            json={
                "request_id": "invalid-uuid",
                "agent_id": "nexusops.chat",
                "query": ""
            },
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_invoke_unauthorized(self, client: AsyncClient):
        """Test invocation without auth."""
        response = await client.post(
            "/api/v1/agents/nexusops.chat/invoke",
            json={
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "agent_id": "nexusops.chat",
                "query": "Hello"
            }
        )

        assert response.status_code == 401
```

---

## Contract Testing

### JSON Schema Validation

```python
# tests/gateway/test_contract.py

import pytest
import jsonschema
from app.gateway.contract import (
    InvokeRequest,
    InvokeResponse,
    REQUEST_SCHEMA,
    RESPONSE_SCHEMA
)


class TestContractValidation:
    """Tests for contract validation."""

    def test_valid_request_schema(self):
        """Test valid request passes schema validation."""
        request = {
            "request_id": "550e8400-e29b-41d4-a716-446655440000",
            "agent_id": "nexusops.chat",
            "query": "Hello"
        }

        # Should not raise
        jsonschema.validate(request, REQUEST_SCHEMA)

    def test_invalid_request_missing_required(self):
        """Test request missing required field."""
        request = {
            "request_id": "550e8400-e29b-41d4-a716-446655440000",
            "agent_id": "nexusops.chat"
            # Missing query
        }

        with pytest.raises(jsonschema.ValidationError) as exc:
            jsonschema.validate(request, REQUEST_SCHEMA)

        assert "query" in str(exc.value)

    def test_invalid_request_agent_id_format(self):
        """Test invalid agent_id format."""
        request = {
            "request_id": "550e8400-e29b-41d4-a716-446655440000",
            "agent_id": "Invalid Agent ID!",  # Invalid format
            "query": "Hello"
        }

        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(request, REQUEST_SCHEMA)

    def test_valid_response_schema(self):
        """Test valid response passes schema validation."""
        response = {
            "request_id": "550e8400-e29b-41d4-a716-446655440000",
            "trace_id": "a1b2c3d4e5f67890a1b2c3d4e5f67890",
            "status": "success",
            "content": {
                "text": "Hello!",
                "format": "markdown"
            }
        }

        # Should not raise
        jsonschema.validate(response, RESPONSE_SCHEMA)

    def test_error_response_schema(self):
        """Test error response passes schema validation."""
        response = {
            "request_id": "550e8400-e29b-41d4-a716-446655440000",
            "trace_id": "a1b2c3d4e5f67890a1b2c3d4e5f67890",
            "status": "error",
            "content": {
                "text": "Error message",
                "format": "plain"
            },
            "error": {
                "code": "AGENT_NOT_FOUND",
                "message": "Agent not found"
            }
        }

        # Should not raise
        jsonschema.validate(response, RESPONSE_SCHEMA)
```

### Response Builder Tests

```python
# tests/gateway/test_response.py

import pytest
from app.gateway.response import ResponseBuilder
from app.gateway.errors import ErrorCode, AgentError


class TestResponseBuilder:
    """Tests for response builder."""

    def test_build_success_response(self):
        """Test building success response."""
        builder = ResponseBuilder(
            request_id="550e8400-e29b-41d4-a716-446655440000",
            trace_id="a1b2c3d4e5f67890a1b2c3d4e5f67890"
        )

        response = builder.success(
            text="Hello!",
            format="markdown"
        ).build()

        assert response["status"] == "success"
        assert response["content"]["text"] == "Hello!"
        assert response["trace_id"] == "a1b2c3d4e5f67890a1b2c3d4e5f67890"

    def test_build_error_response(self):
        """Test building error response."""
        builder = ResponseBuilder(
            request_id="550e8400-e29b-41d4-a716-446655440000",
            trace_id="a1b2c3d4e5f67890a1b2c3d4e5f67890"
        )

        error = AgentError(
            code=ErrorCode.AGENT_NOT_FOUND,
            message="Agent not found: test"
        )

        response = builder.error(error).build()

        assert response["status"] == "error"
        assert response["error"]["code"] == "AGENT_NOT_FOUND"
```

---

## Test Coverage

### Running Tests with Coverage

```bash
# Run all tests with coverage
pytest --cov=app --cov-report=html --cov-report=term

# Run specific test file
pytest tests/agents/test_chat.py --cov=app.agents.chat

# Run with verbose output
pytest -v --cov=app --cov-report=term-missing
```

### Coverage Configuration

```ini
# pytest.ini

[pytest]
testpaths = tests
asyncio_mode = auto
addopts = --cov=app --cov-report=term-missing --cov-fail-under=80

[coverage:run]
source = app
omit =
    app/main.py
    app/__init__.py
    */tests/*

[coverage:report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if TYPE_CHECKING:
```

---

## Test Acceptance Criteria

### P0 Tests (Must Pass)

| ID | Test | Description |
|----|------|-------------|
| CT-001 | `test_valid_request_response` | Valid request returns success |
| CT-002 | `test_invalid_json` | Invalid JSON returns INPUT_INVALID_JSON |
| CT-003 | `test_missing_request_id` | Missing request_id returns INPUT_MISSING_FIELD |
| CT-004 | `test_invalid_agent_id` | Invalid agent_id returns INPUT_INVALID_AGENT_ID |
| CT-005 | `test_agent_not_found` | Unknown agent returns AGENT_NOT_FOUND |
| CT-006 | `test_unauthorized` | No auth returns AUTH_TOKEN_MISSING |
| CT-007 | `test_trace_id_present` | All responses have trace_id |
| CT-008 | `test_error_schema` | Error responses match ErrorDetail schema |

### P1 Tests (Should Pass)

| ID | Test | Description |
|----|------|-------------|
| CT-101 | `test_query_too_long` | Long query returns INPUT_QUERY_TOO_LONG |
| CT-102 | `test_schema_validation_errors` | Schema violations return field-level errors |
| CT-103 | `test_timeout` | Timeout returns EXEC_TIMEOUT |
| CT-104 | `test_invalid_output` | Invalid output returns AGENT_OUTPUT_INVALID |
| CT-105 | `test_rate_limit` | Rate limit returns AUTH_QUOTA_EXCEEDED |

---

## Best Practices

### 1. Use Fixtures for Common Setup

```python
@pytest.fixture
def handler():
    return MyAgentHandler()

@pytest.fixture
def make_request():
    def _make(query, **kwargs):
        return ExecutorRequest(...)
    return _make
```

### 2. Test Edge Cases

```python
@pytest.mark.parametrize("query,expected", [
    ("normal query", True),
    ("", False),
    ("a" * 10001, False),
    (None, False),
])
async def test_query_validation(query, expected):
    ...
```

### 3. Mock External Services

```python
with patch('httpx.AsyncClient') as mock_client:
    mock_client.return_value.get = AsyncMock(return_value=mock_response)
    ...
```

### 4. Use Async Test Markers

```python
@pytest.mark.asyncio
async def test_async_operation():
    result = await handler.handle(request)
    ...
```

---

## Next Steps

- [Error Handling](./error-handling.md) - Handle errors properly
- [Troubleshooting](../best-practices/troubleshooting.md) - Debug test failures
- [Best Practices](../best-practices/performance.md) - Performance testing
