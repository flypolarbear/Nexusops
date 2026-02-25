"""
Tests for NexusOps SDK Client
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from sdk.client import AgentClient, AgentsNamespace
from sdk.models import AgentConfig, AgentManifest, AgentRequestContext
from sdk.exceptions import (
    NexusOpsError,
    AgentNotFoundError,
    AgentTimeoutError,
    AuthenticationError,
    AgentNotInstalledError,
    AgentDisabledError,
    RateLimitError,
    ConnectionError as NexusOpsConnectionError,
)


@pytest.fixture
def config():
    """Create a test configuration."""
    return AgentConfig(
        base_url="https://nexusops.example.com",
        api_key="test-api-key",
        timeout=10.0,
        max_retries=2,
    )


@pytest.fixture
def client(config):
    """Create a test client."""
    with AgentClient(config=config) as client:
        yield client


class TestAgentConfig:
    """Tests for AgentConfig."""

    def test_config_creation(self):
        """Test configuration creation."""
        config = AgentConfig(
            base_url="https://test.example.com",
            api_key="secret-key",
        )
        assert config.base_url == "https://test.example.com"
        assert config.api_key == "secret-key"
        assert config.timeout == 30.0

    def test_config_validation(self):
        """Test configuration validation - missing required fields."""
        with pytest.raises(Exception):
            AgentConfig()  # Missing required fields

    def test_config_invalid_timeout(self):
        """Test that negative timeout is rejected."""
        with pytest.raises(Exception):
            AgentConfig(
                base_url="https://test.example.com",
                api_key="key",
                timeout=-1.0,
            )


class TestAgentClient:
    """Tests for AgentClient."""

    def test_client_initialization(self, config):
        """Test client initialization."""
        client = AgentClient(config=config)
        assert client.config == config
        assert client.agents is not None
        assert isinstance(client.agents, AgentsNamespace)
        client.close()

    def test_context_manager(self, config):
        """Test context manager usage."""
        with AgentClient(config=config) as client:
            assert client._sync_client is None  # Lazy initialization
        # Client should be closed after context exit

    def test_headers(self, config):
        """Test default headers."""
        with AgentClient(config=config) as client:
            headers = client._get_headers()
            assert headers["Authorization"] == "Bearer test-api-key"
            assert headers["Content-Type"] == "application/json"
            assert "NexusOps-Python-SDK" in headers["User-Agent"]


class TestAgentsNamespace:
    """Tests for AgentsNamespace."""

    def test_list_agents(self, client):
        """Test listing agents."""
        mock_response = {
            "agents": [
                {
                    "agent_id": "nexusops.chat",
                    "name": "Chat Agent",
                    "version": "1.0.0",
                    "category": "general",
                    "capabilities": ["chat"],
                    "tools": [],
                },
                {
                    "agent_id": "nexusops.k8s",
                    "name": "K8s Agent",
                    "version": "1.0.0",
                    "category": "deployment",
                    "capabilities": ["k8s_deploy"],
                    "tools": [],
                },
            ]
        }

        with patch.object(client, "_request", return_value=mock_response):
            result = client.agents.list()

            assert result.total == 2
            assert len(result.agents) == 2
            assert result.agents[0].agent_id == "nexusops.chat"
            assert result.agents[1].agent_id == "nexusops.k8s"

    @pytest.mark.asyncio
    async def test_list_agents_async(self, config):
        """Test listing agents asynchronously."""
        mock_response = {
            "agents": [
                {
                    "agent_id": "nexusops.chat",
                    "name": "Chat Agent",
                    "version": "1.0.0",
                    "category": "general",
                    "capabilities": ["chat"],
                    "tools": [],
                }
            ]
        }

        async with AgentClient(config=config) as client:
            with patch.object(client, "_request_async", new_callable=AsyncMock, return_value=mock_response):
                result = await client.agents.list_async()

                assert result.total == 1
                assert result.agents[0].agent_id == "nexusops.chat"

    def test_get_agent(self, client):
        """Test getting a specific agent."""
        mock_response = {
            "agent_id": "nexusops.k8s",
            "name": "Kubernetes Agent",
            "version": "1.0.0",
            "description": "K8s operations",
            "category": "deployment",
            "capabilities": ["k8s_deploy", "k8s_scale"],
            "tools": [],
        }

        with patch.object(client, "_request", return_value=mock_response):
            result = client.agents.get("nexusops.k8s")

            assert result.agent_id == "nexusops.k8s"
            assert result.name == "Kubernetes Agent"
            assert "k8s_deploy" in result.capabilities

    def test_get_agent_not_found(self, client):
        """Test getting a non-existent agent."""
        with patch.object(client, "_request") as mock_request:
            mock_request.side_effect = AgentNotFoundError(
                agent_id="non-existent",
                message="Agent not found",
            )

            with pytest.raises(AgentNotFoundError) as exc_info:
                client.agents.get("non-existent")

            assert exc_info.value.agent_id == "non-existent"

    def test_invoke_agent_with_query(self, client):
        """Test invoking an agent with a query."""
        mock_response = {
            "request_id": "req-123",
            "status": "success",
            "content": {"text": "Hello!", "format": "markdown"},
            "suggested_actions": [],
            "related_resources": [],
        }

        with patch.object(client, "_request", return_value=mock_response):
            result = client.agents.invoke(
                agent_id="nexusops.chat",
                query="Hello",
            )

            assert result.status == "success"
            assert result.content.text == "Hello!"

    def test_invoke_agent_with_action(self, client):
        """Test invoking an agent with an action."""
        mock_response = {
            "request_id": "req-456",
            "status": "success",
            "content": {"text": "Pods listed", "format": "markdown"},
            "suggested_actions": [],
            "related_resources": [],
        }

        with patch.object(client, "_request", return_value=mock_response) as mock_req:
            result = client.agents.invoke(
                agent_id="nexusops.k8s",
                action="get_pods",
                params={"namespace": "production"},
            )

            # Verify the query was built correctly
            call_args = mock_req.call_args
            payload = call_args.kwargs["json"]
            assert "get_pods" in payload["query"]
            assert "namespace=production" in payload["query"]

            assert result.status == "success"

    @pytest.mark.asyncio
    async def test_invoke_agent_async(self, config):
        """Test invoking an agent asynchronously."""
        mock_response = {
            "request_id": "req-789",
            "status": "success",
            "content": {"text": "Async response", "format": "markdown"},
            "suggested_actions": [],
            "related_resources": [],
        }

        async with AgentClient(config=config) as client:
            with patch.object(client, "_request_async", new_callable=AsyncMock, return_value=mock_response):
                result = await client.agents.invoke_async(
                    agent_id="nexusops.chat",
                    query="Hello async",
                )

                assert result.status == "success"
                assert result.content.text == "Async response"

    def test_invoke_agent_with_context(self, client):
        """Test invoking an agent with context."""
        mock_response = {
            "request_id": "req-ctx",
            "status": "success",
            "content": {"text": "Context processed", "format": "markdown"},
            "suggested_actions": [],
            "related_resources": [],
        }

        with patch.object(client, "_request", return_value=mock_response) as mock_req:
            result = client.agents.invoke(
                agent_id="nexusops.deploy",
                query="Deploy to production",
                context=AgentRequestContext(
                    user_id="user-123",
                    project_id="project-456",
                    region="us-west-2",
                ),
            )

            call_args = mock_req.call_args
            payload = call_args.kwargs["json"]
            assert payload["context"]["user_id"] == "user-123"
            assert payload["context"]["region"] == "us-west-2"

    def test_invoke_agent_timeout(self, client):
        """Test agent invocation timeout."""
        with patch.object(client, "_request") as mock_request:
            mock_request.side_effect = AgentTimeoutError(
                agent_id="nexusops.slow",
                timeout_seconds=10.0,
            )

            with pytest.raises(AgentTimeoutError) as exc_info:
                client.agents.invoke(
                    agent_id="nexusops.slow",
                    query="This will timeout",
                )

            assert exc_info.value.agent_id == "nexusops.slow"
            assert exc_info.value.timeout_seconds == 10.0

    def test_register_agent(self, client):
        """Test registering an agent."""
        mock_response = {
            "agent_id": "my-custom-agent",
            "name": "My Custom Agent",
            "version": "1.0.0",
            "status": "active",
            "endpoint": "https://my-agent.example.com/webhook",
            "created_at": "2024-01-01T00:00:00Z",
        }

        with patch.object(client, "_request", return_value=mock_response) as mock_req:
            result = client.agents.register(
                agent_id="my-custom-agent",
                name="My Custom Agent",
                capabilities=["data-processing"],
                endpoint="https://my-agent.example.com/webhook",
            )

            assert result.agent_id == "my-custom-agent"
            assert result.status == "active"

            # Verify request payload
            call_args = mock_req.call_args
            payload = call_args.kwargs["json"]
            assert payload["agent_id"] == "my-custom-agent"
            assert payload["name"] == "My Custom Agent"

    @pytest.mark.asyncio
    async def test_register_agent_async(self, config):
        """Test registering an agent asynchronously."""
        mock_response = {
            "agent_id": "async-agent",
            "name": "Async Agent",
            "version": "1.0.0",
            "status": "active",
            "created_at": "2024-01-01T00:00:00Z",
        }

        async with AgentClient(config=config) as client:
            with patch.object(client, "_request_async", new_callable=AsyncMock, return_value=mock_response):
                result = await client.agents.register_async(
                    agent_id="async-agent",
                    name="Async Agent",
                    capabilities=["async-ops"],
                )

                assert result.agent_id == "async-agent"


class TestClientErrorHandling:
    """Tests for client error handling."""

    def test_authentication_error(self, client):
        """Test authentication error handling."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "code": "AUTH_ERROR",
            "message": "Invalid API key",
        }

        with patch.object(client._get_sync_client(), "request", return_value=mock_response):
            with pytest.raises(AuthenticationError) as exc_info:
                client._request("GET", "/api/agents")

            assert "Invalid API key" in str(exc_info.value)

    def test_agent_not_found_error(self, client):
        """Test agent not found error handling."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 404
        mock_response.json.return_value = {
            "detail": {
                "code": "AGENT_NOT_FOUND",
                "message": "Agent not found",
                "details": {"agent_id": "unknown-agent"},
            }
        }

        with patch.object(client._get_sync_client(), "request", return_value=mock_response):
            with pytest.raises(AgentNotFoundError):
                client._request("GET", "/api/agents/unknown-agent")

    def test_agent_not_installed_error(self, client):
        """Test agent not installed error handling."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 403
        mock_response.json.return_value = {
            "detail": {
                "code": "AGENT_NOT_INSTALLED",
                "message": "Agent not installed",
            }
        }

        with patch.object(client._get_sync_client(), "request", return_value=mock_response):
            with pytest.raises(AgentNotInstalledError):
                client._request("POST", "/api/agents/third-party/invoke", json={"agent_id": "third-party"})

    def test_agent_disabled_error(self, client):
        """Test agent disabled error handling."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 403
        mock_response.json.return_value = {
            "detail": {
                "code": "AGENT_DISABLED",
                "message": "Agent is disabled",
            }
        }

        with patch.object(client._get_sync_client(), "request", return_value=mock_response):
            with pytest.raises(AgentDisabledError):
                client._request("POST", "/api/agents/disabled-agent/invoke", json={"agent_id": "disabled-agent"})

    def test_rate_limit_error(self, client):
        """Test rate limit error handling."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_response.json.return_value = {
            "code": "RATE_LIMIT_EXCEEDED",
            "message": "Too many requests",
            "retry_after": 60,
        }

        with patch.object(client._get_sync_client(), "request", return_value=mock_response):
            with pytest.raises(RateLimitError) as exc_info:
                client._request("GET", "/api/agents")

            assert exc_info.value.retry_after == 60

    def test_timeout_error(self, client):
        """Test timeout error handling."""
        with patch.object(client._get_sync_client(), "request") as mock_request:
            mock_request.side_effect = httpx.TimeoutException("Request timed out")

            with pytest.raises(AgentTimeoutError):
                client._request("GET", "/api/agents", json={"agent_id": "test"})

    def test_connection_error(self, client):
        """Test connection error handling."""
        # The retry decorator will retry 3 times before giving up
        # We mock the underlying httpx client to always fail
        with patch.object(client._get_sync_client(), "request") as mock_request:
            # Always raise connection error
            mock_request.side_effect = httpx.ConnectError("Connection failed")

            # This will raise NexusOpsConnectionError after retries are exhausted
            # Note: The retry decorator is configured to retry on NexusOpsConnectionError,
            # but the first call raises httpx.ConnectError which gets converted to NexusOpsConnectionError
            # The retry then kicks in and retries 3 times total before giving up
            with pytest.raises(NexusOpsConnectionError):
                client._request("GET", "/api/agents", json={"test": "data"})


class TestClientRetry:
    """Tests for client retry logic."""

    def test_retry_on_connection_error(self, client):
        """Test that connection errors trigger retry."""
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.ConnectError("Connection failed")
            return MagicMock(
                status_code=200,
                json=lambda: {"agents": []}
            )

        with patch.object(client._get_sync_client(), "request", side_effect=side_effect):
            result = client._request("GET", "/api/agents")

            assert call_count == 3  # Initial + 2 retries
            assert result == {"agents": []}
