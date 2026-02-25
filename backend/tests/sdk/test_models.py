"""
Tests for NexusOps SDK Models
"""

import pytest
from pydantic import ValidationError as PydanticValidationError

from sdk.models import (
    AgentConfig,
    AgentManifest,
    AgentToolDefinition,
    AgentRegistrationRequest,
    AgentRegistrationResponse,
    AgentRequestContext,
    AgentInvokeRequest,
    AgentInvokeResponse,
    AgentContent,
    AgentAction,
    RelatedResource,
    AgentError,
    AgentStatus,
    AgentListResponse,
    ErrorResponse,
)


class TestAgentConfig:
    """Tests for AgentConfig model."""

    def test_minimal_config(self):
        """Test minimal configuration."""
        config = AgentConfig(
            base_url="https://nexusops.example.com",
            api_key="test-key",
        )
        assert config.base_url == "https://nexusops.example.com"
        assert config.api_key == "test-key"
        assert config.timeout == 30.0
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert config.verify_ssl is True

    def test_full_config(self):
        """Test full configuration."""
        config = AgentConfig(
            base_url="https://nexusops.example.com",
            api_key="test-key",
            timeout=60.0,
            max_retries=5,
            retry_delay=2.0,
            verify_ssl=False,
        )
        assert config.timeout == 60.0
        assert config.max_retries == 5
        assert config.retry_delay == 2.0
        assert config.verify_ssl is False

    def test_invalid_timeout(self):
        """Test that negative timeout raises validation error."""
        with pytest.raises(PydanticValidationError):
            AgentConfig(
                base_url="https://nexusops.example.com",
                api_key="test-key",
                timeout=-1.0,
            )

    def test_invalid_max_retries(self):
        """Test that invalid max_retries raises validation error."""
        with pytest.raises(PydanticValidationError):
            AgentConfig(
                base_url="https://nexusops.example.com",
                api_key="test-key",
                max_retries=15,  # > 10
            )


class TestAgentManifest:
    """Tests for AgentManifest model."""

    def test_minimal_manifest(self):
        """Test minimal manifest."""
        manifest = AgentManifest(
            agent_id="test-agent",
            name="Test Agent",
            category="test",
        )
        assert manifest.agent_id == "test-agent"
        assert manifest.name == "Test Agent"
        assert manifest.version == "1.0.0"
        assert manifest.capabilities == []
        assert manifest.tools == []

    def test_full_manifest(self):
        """Test full manifest."""
        manifest = AgentManifest(
            agent_id="test-agent",
            name="Test Agent",
            version="2.0.0",
            description="A test agent",
            category="custom",
            capabilities=["chat", "process"],
            tools=[
                AgentToolDefinition(
                    name="test_tool",
                    description="A test tool",
                    inputSchema={"type": "object"},
                )
            ],
        )
        assert manifest.version == "2.0.0"
        assert manifest.description == "A test agent"
        assert len(manifest.capabilities) == 2
        assert len(manifest.tools) == 1


class TestAgentToolDefinition:
    """Tests for AgentToolDefinition model."""

    def test_minimal_tool(self):
        """Test minimal tool definition."""
        tool = AgentToolDefinition(
            name="test_tool",
            description="A test tool",
        )
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool.input_schema == {}

    def test_tool_with_input_schema(self):
        """Test tool with input schema."""
        tool = AgentToolDefinition(
            name="test_tool",
            description="A test tool",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                },
            },
        )
        assert tool.input_schema["type"] == "object"


class TestAgentRequestContext:
    """Tests for AgentRequestContext model."""

    def test_empty_context(self):
        """Test empty context."""
        context = AgentRequestContext()
        assert context.user_id is None
        assert context.tenant_id is None
        assert context.project_id is None

    def test_full_context(self):
        """Test full context."""
        context = AgentRequestContext(
            user_id="user-123",
            tenant_id="tenant-456",
            project_id="project-789",
            version_id="version-001",
            codename="v1.0.0",
            region="us-west-2",
            resource_type="deployment",
            resource_name="my-app",
            namespace="production",
        )
        assert context.user_id == "user-123"
        assert context.region == "us-west-2"
        assert context.namespace == "production"


class TestAgentInvokeRequest:
    """Tests for AgentInvokeRequest model."""

    def test_minimal_request(self):
        """Test minimal invoke request."""
        request = AgentInvokeRequest(
            agent_id="test-agent",
            query="Hello",
        )
        assert request.agent_id == "test-agent"
        assert request.query == "Hello"
        assert request.action is None
        assert request.params is None

    def test_request_with_context(self):
        """Test request with context."""
        request = AgentInvokeRequest(
            agent_id="test-agent",
            query="Deploy to production",
            context=AgentRequestContext(
                project_id="project-123",
                region="us-west-2",
            ),
        )
        assert request.context.project_id == "project-123"


class TestAgentInvokeResponse:
    """Tests for AgentInvokeResponse model."""

    def test_success_response(self):
        """Test success response."""
        response = AgentInvokeResponse(
            request_id="req-123",
            status="success",
            content=AgentContent(text="Hello, world!"),
        )
        assert response.request_id == "req-123"
        assert response.status == "success"
        assert response.content.text == "Hello, world!"
        assert response.error is None

    def test_error_response(self):
        """Test error response."""
        response = AgentInvokeResponse(
            request_id="req-123",
            status="error",
            content=AgentContent(text=""),
            error=AgentError(
                code="INTERNAL_ERROR",
                message="Something went wrong",
            ),
        )
        assert response.status == "error"
        assert response.error.code == "INTERNAL_ERROR"
        assert response.error.message == "Something went wrong"

    def test_response_with_actions(self):
        """Test response with suggested actions."""
        response = AgentInvokeResponse(
            request_id="req-123",
            status="success",
            content=AgentContent(text="Done"),
            suggested_actions=[
                AgentAction(
                    id="action-1",
                    type="invoke",
                    label="Deploy",
                    params={"version": "1.0.0"},
                )
            ],
        )
        assert len(response.suggested_actions) == 1
        assert response.suggested_actions[0].label == "Deploy"


class TestAgentContent:
    """Tests for AgentContent model."""

    def test_default_content(self):
        """Test default content."""
        content = AgentContent(text="Hello")
        assert content.text == "Hello"
        assert content.format == "markdown"
        assert content.data is None

    def test_json_content(self):
        """Test JSON content."""
        content = AgentContent(
            text='{"status": "ok"}',
            format="json",
            data={"status": "ok"},
        )
        assert content.format == "json"
        assert content.data == {"status": "ok"}


class TestAgentAction:
    """Tests for AgentAction model."""

    def test_basic_action(self):
        """Test basic action."""
        action = AgentAction(
            id="action-1",
            type="invoke",
            label="Deploy",
        )
        assert action.id == "action-1"
        assert action.type == "invoke"
        assert action.label == "Deploy"
        assert action.confirm_required is False
        assert action.danger is False

    def test_dangerous_action(self):
        """Test dangerous action."""
        action = AgentAction(
            id="action-1",
            type="delete",
            label="Delete Resource",
            confirm_required=True,
            danger=True,
        )
        assert action.confirm_required is True
        assert action.danger is True


class TestAgentError:
    """Tests for AgentError model."""

    def test_basic_error(self):
        """Test basic error."""
        error = AgentError(
            code="NOT_FOUND",
            message="Resource not found",
        )
        assert error.code == "NOT_FOUND"
        assert error.message == "Resource not found"
        assert error.details is None
        assert error.retry_after is None

    def test_error_with_retry(self):
        """Test error with retry_after."""
        error = AgentError(
            code="RATE_LIMITED",
            message="Too many requests",
            retry_after=60,
        )
        assert error.retry_after == 60


class TestAgentListResponse:
    """Tests for AgentListResponse model."""

    def test_empty_list(self):
        """Test empty agent list."""
        response = AgentListResponse(agents=[], total=0)
        assert response.agents == []
        assert response.total == 0

    def test_agent_list(self):
        """Test agent list with items."""
        response = AgentListResponse(
            agents=[
                AgentManifest(
                    agent_id="agent-1",
                    name="Agent 1",
                    category="test",
                ),
                AgentManifest(
                    agent_id="agent-2",
                    name="Agent 2",
                    category="test",
                ),
            ],
            total=2,
        )
        assert len(response.agents) == 2
        assert response.total == 2


class TestErrorResponse:
    """Tests for ErrorResponse model."""

    def test_basic_error(self):
        """Test basic error response."""
        error = ErrorResponse(
            code="VALIDATION_ERROR",
            message="Invalid input",
        )
        assert error.code == "VALIDATION_ERROR"
        assert error.message == "Invalid input"

    def test_error_with_details(self):
        """Test error with details."""
        error = ErrorResponse(
            code="VALIDATION_ERROR",
            message="Invalid input",
            details={"field": "agent_id"},
            trace_id="trace-123",
        )
        assert error.details == {"field": "agent_id"}
        assert error.trace_id == "trace-123"
