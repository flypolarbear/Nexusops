"""
NexusOps SDK - Client Tests

Tests for AgentClient functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from nexusops_sdk import AgentClient
from nexusops_sdk.exceptions import (
    NexusOpsError,
    AgentError,
    AuthError,
    ErrorCode,
)
from nexusops_sdk.models import (
    AgentResponse,
    AgentStatus,
    InstallStatus,
    AgentInstallStatus,
)


class TestAgentClient:
    """Tests for AgentClient."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return AgentClient(
            base_url="http://localhost:8000",
            api_key="test-api-key",
            tenant_id="test-tenant",
        )

    def test_client_initialization(self, client):
        """Test client initializes correctly."""
        assert client.base_url == "http://localhost:8000"
        assert client.api_key == "test-api-key"
        assert client.tenant_id == "test-tenant"
        assert "X-API-Key" in client._default_headers
        assert client._default_headers["X-API-Key"] == "test-api-key"

    def test_client_with_token(self):
        """Test client with bearer token."""
        client = AgentClient(
            base_url="http://localhost:8000",
            token="bearer-token",
        )
        assert "Authorization" in client._default_headers
        assert client._default_headers["Authorization"] == "Bearer bearer-token"

    @pytest.mark.asyncio
    async def test_invoke_agent_success(self, client):
        """Test successful agent invocation."""
        mock_response = {
            "request_id": "test-request-id",
            "trace_id": "test-trace-id",
            "status": "success",
            "content": {
                "text": "Hello! How can I help?",
                "format": "markdown"
            },
            "suggested_actions": [],
            "related_resources": [],
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            response = await client.invoke_agent(
                agent_id="nexusops.chat",
                query="Hello!",
            )

            assert isinstance(response, AgentResponse)
            assert response.status == "success"
            assert response.content.text == "Hello! How can I help?"
            assert response.is_success

    @pytest.mark.asyncio
    async def test_invoke_agent_with_context(self, client):
        """Test agent invocation with context."""
        mock_response = {
            "request_id": "test-request-id",
            "trace_id": "test-trace-id",
            "status": "success",
            "content": {"text": "OK", "format": "markdown"},
            "suggested_actions": [],
            "related_resources": [],
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            response = await client.invoke_agent(
                agent_id="nexusops.k8s",
                query="Get pod status",
                context={"user_id": "user-123", "project_id": "proj-456"},
            )

            # Verify context was passed
            call_args = mock_request.call_args
            assert call_args is not None
            json_body = call_args.kwargs.get("json") or call_args.args[2]
            assert json_body["context"]["user_id"] == "user-123"
            assert json_body["context"]["project_id"] == "proj-456"

    @pytest.mark.asyncio
    async def test_invoke_agent_error(self, client):
        """Test agent invocation error handling."""
        error_response = {
            "request_id": "test-request-id",
            "trace_id": "test-trace-id",
            "error": {
                "code": "AGENT_NOT_FOUND",
                "message": "Agent not found: invalid.agent",
            }
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = NexusOpsError.from_response(error_response)

            with pytest.raises(NexusOpsError) as exc_info:
                await client.invoke_agent(
                    agent_id="invalid.agent",
                    query="Hello!",
                )

            assert exc_info.value.code == ErrorCode.AGENT_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_agent_status(self, client):
        """Test getting agent status."""
        mock_response = {
            "agent_id": "nexusops.chat",
            "name": "AI Assistant",
            "version": "1.0.0",
            "install_status": "installed",
            "agent_status": "active",
            "installed_at": "2026-02-25T10:00:00Z",
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            status = await client.get_agent_status("nexusops.chat")

            assert isinstance(status, AgentInstallStatus)
            assert status.agent_id == "nexusops.chat"
            assert status.install_status == InstallStatus.INSTALLED
            assert status.agent_status == AgentStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_register_agent(self, client):
        """Test agent registration."""
        mock_response = {
            "agent_id": "test.agent",
            "name": "Test Agent",
            "version": "1.0.0",
            "status": "active",
            "created_at": "2026-02-25T10:00:00Z",
            "updated_at": "2026-02-25T10:00:00Z",
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await client.register_agent(
                agent_id="test.agent",
                name="Test Agent",
                version="1.0.0",
                description="A test agent",
                capabilities=["chat", "analyze"],
            )

            assert result["agent_id"] == "test.agent"
            assert result["name"] == "Test Agent"

    @pytest.mark.asyncio
    async def test_install_agent(self, client):
        """Test agent installation."""
        mock_response = {
            "agent_id": "test.agent",
            "name": "Test Agent",
            "version": "1.0.0",
            "install_status": "installed",
            "message": "Agent installed successfully",
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await client.install_agent("test.agent")

            assert result["install_status"] == "installed"

    @pytest.mark.asyncio
    async def test_list_agents(self, client):
        """Test listing agents."""
        mock_response = {
            "items": [
                {"agent_id": "agent1", "name": "Agent 1"},
                {"agent_id": "agent2", "name": "Agent 2"},
            ],
            "total": 2,
            "page": 1,
            "page_size": 20,
            "total_pages": 1,
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await client.list_agents(query="test", page=1)

            assert result["total"] == 2
            assert len(result["items"]) == 2


class TestAgentResponse:
    """Tests for AgentResponse model."""

    def test_is_success(self):
        """Test is_success property."""
        response = AgentResponse(
            request_id="test",
            status="success",
            content={"text": "OK", "format": "markdown"},
        )
        assert response.is_success
        assert not response.is_error
        assert not response.is_partial

    def test_is_error(self):
        """Test is_error property."""
        response = AgentResponse(
            request_id="test",
            status="error",
            content={"text": "Error", "format": "plain"},
            error={"code": "ERROR", "message": "Something went wrong"},
        )
        assert response.is_error
        assert not response.is_success

    def test_from_dict(self):
        """Test creating response from dict."""
        data = {
            "request_id": "req-123",
            "trace_id": "trace-456",
            "status": "success",
            "content": {
                "text": "Hello",
                "format": "markdown",
            },
            "suggested_actions": [
                {"id": "1", "type": "invoke", "label": "Action 1"}
            ],
        }

        response = AgentResponse.from_dict(data)
        assert response.request_id == "req-123"
        assert response.trace_id == "trace-456"
        assert response.is_success
        assert len(response.suggested_actions) == 1


class TestExceptions:
    """Tests for exception classes."""

    def test_error_from_response(self):
        """Test creating exception from API response."""
        data = {
            "request_id": "req-123",
            "trace_id": "trace-456",
            "error": {
                "code": "AGENT_NOT_FOUND",
                "message": "Agent not found",
                "details": {"agent_id": "invalid.agent"},
            }
        }

        error = NexusOpsError.from_response(data)
        assert error.code == ErrorCode.AGENT_NOT_FOUND
        assert error.message == "Agent not found"
        assert error.trace_id == "trace-456"
        assert isinstance(error, AgentError)

    def test_error_is_retryable(self):
        """Test is_retryable property."""
        error = NexusOpsError(
            code=ErrorCode.EXEC_TIMEOUT,
            message="Timeout",
        )
        assert error.is_retryable

        error2 = NexusOpsError(
            code=ErrorCode.AGENT_NOT_FOUND,
            message="Not found",
        )
        assert not error2.is_retryable

    def test_error_http_status(self):
        """Test http_status property."""
        error = NexusOpsError(
            code=ErrorCode.AUTH_TOKEN_MISSING,
            message="Missing token",
        )
        assert error.http_status == 401

        error2 = NexusOpsError(
            code=ErrorCode.AGENT_NOT_FOUND,
            message="Not found",
        )
        assert error2.http_status == 404
