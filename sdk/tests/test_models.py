"""
NexusOps SDK - Models Tests

Tests for request and response models.
"""

import pytest

from nexusops_sdk.models import (
    AgentRequest,
    AgentRequestContext,
    AgentResponse,
    AgentContent,
    AgentError,
    SuggestedAction,
    RelatedResource,
    OutputConfig,
    ToolOverride,
    Agent,
    AgentManifest,
    AgentStatus,
    InstallStatus,
)


class TestAgentRequest:
    """Tests for AgentRequest model."""

    def test_create_basic_request(self):
        """Test creating a basic request."""
        request = AgentRequest(
            agent_id="nexusops.chat",
            query="Hello!",
        )

        assert request.agent_id == "nexusops.chat"
        assert request.query == "Hello!"
        assert request.request_id  # Auto-generated
        assert request.context is not None

    def test_create_request_with_context(self):
        """Test creating request with context."""
        context = AgentRequestContext(
            user_id="user-123",
            tenant_id="tenant-456",
            project_id="project-789",
        )

        request = AgentRequest(
            agent_id="nexusops.chat",
            query="Hello!",
            context=context,
        )

        assert request.context.user_id == "user-123"
        assert request.context.tenant_id == "tenant-456"

    def test_create_request_factory_method(self):
        """Test using create factory method."""
        request = AgentRequest.create(
            agent_id="nexusops.k8s",
            query="Get pods",
            user_id="user-123",
            project_id="project-456",
        )

        assert request.agent_id == "nexusops.k8s"
        assert request.context.user_id == "user-123"
        assert request.context.project_id == "project-456"

    def test_request_with_output_config(self):
        """Test request with output configuration."""
        output_config = OutputConfig(
            format="json",
            max_tokens=1000,
        )

        request = AgentRequest(
            agent_id="nexusops.chat",
            query="Hello!",
            output_config=output_config,
        )

        assert request.output_config.format == "json"
        assert request.output_config.max_tokens == 1000

    def test_request_with_tools(self):
        """Test request with tool overrides."""
        tools = [
            ToolOverride(name="get_status", enabled=True),
            ToolOverride(name="deploy", enabled=False),
        ]

        request = AgentRequest(
            agent_id="nexusops.chat",
            query="Check status",
            tools=tools,
        )

        assert len(request.tools) == 2
        assert request.tools[0].name == "get_status"

    def test_agent_id_validation(self):
        """Test agent_id format validation."""
        # Valid IDs
        valid_ids = [
            "nexusops.chat",
            "mycompany.my-agent",
            "a.b-c.d",
            "abc",
        ]

        for agent_id in valid_ids:
            request = AgentRequest(agent_id=agent_id, query="test")
            assert request.agent_id == agent_id

        # Invalid ID should raise
        with pytest.raises(Exception):  # Pydantic ValidationError
            AgentRequest(agent_id="Invalid", query="test")

    def test_query_length_validation(self):
        """Test query length validation."""
        # Max 10000 characters
        long_query = "x" * 10000
        request = AgentRequest(agent_id="test.agent", query=long_query)
        assert len(request.query) == 10000

        # Over limit should raise
        with pytest.raises(Exception):  # Pydantic ValidationError
            AgentRequest(agent_id="test.agent", query="x" * 10001)


class TestAgentResponse:
    """Tests for AgentResponse model."""

    def test_create_success_response(self):
        """Test creating a success response."""
        response = AgentResponse(
            request_id="req-123",
            status="success",
            content=AgentContent(text="Hello!", format="markdown"),
        )

        assert response.request_id == "req-123"
        assert response.status == "success"
        assert response.content.text == "Hello!"
        assert response.is_success

    def test_create_error_response(self):
        """Test creating an error response."""
        response = AgentResponse(
            request_id="req-123",
            status="error",
            content=AgentContent(text="Error", format="plain"),
            error=AgentError(
                code="AGENT_NOT_FOUND",
                message="Agent not found",
            ),
        )

        assert response.is_error
        assert response.error.code == "AGENT_NOT_FOUND"

    def test_response_with_structured_output(self):
        """Test response with structured output."""
        structured = {"result": "data", "count": 42}

        response = AgentResponse(
            request_id="req-123",
            status="success",
            content=AgentContent(text="Result", format="markdown"),
            structured_output=structured,
        )

        assert response.structured_output == structured

    def test_response_with_suggested_actions(self):
        """Test response with suggested actions."""
        actions = [
            SuggestedAction(
                id="1",
                type="invoke",
                label="Deploy",
                params={"target": "production"},
            ),
            SuggestedAction(
                id="2",
                type="navigate",
                label="View Logs",
            ),
        ]

        response = AgentResponse(
            request_id="req-123",
            status="success",
            content=AgentContent(text="Done", format="markdown"),
            suggested_actions=actions,
        )

        assert len(response.suggested_actions) == 2
        assert response.suggested_actions[0].label == "Deploy"

    def test_response_with_related_resources(self):
        """Test response with related resources."""
        resources = [
            RelatedResource(
                type="deployment",
                id="deploy-123",
                name="my-app",
                link="/deployments/deploy-123",
            ),
        ]

        response = AgentResponse(
            request_id="req-123",
            status="success",
            content=AgentContent(text="Done", format="markdown"),
            related_resources=resources,
        )

        assert len(response.related_resources) == 1

    def test_from_dict(self):
        """Test creating response from dictionary."""
        data = {
            "request_id": "req-123",
            "trace_id": "trace-456",
            "status": "partial",
            "content": {
                "text": "Partial result",
                "format": "markdown",
            },
            "structured_output": {"key": "value"},
            "suggested_actions": [
                {"id": "1", "type": "invoke", "label": "Retry"}
            ],
            "metadata": {
                "latency_ms": 100,
            },
        }

        response = AgentResponse.from_dict(data)

        assert response.request_id == "req-123"
        assert response.trace_id == "trace-456"
        assert response.status == "partial"
        assert response.is_partial
        assert response.structured_output == {"key": "value"}
        assert len(response.suggested_actions) == 1


class TestAgentModel:
    """Tests for Agent model."""

    def test_create_agent(self):
        """Test creating an agent."""
        agent = Agent(
            agent_id="test.agent",
            name="Test Agent",
            version="1.0.0",
            description="A test agent",
            category="general",
            capabilities=["chat", "analyze"],
        )

        assert agent.agent_id == "test.agent"
        assert agent.name == "Test Agent"
        assert agent.status == AgentStatus.ACTIVE
        assert agent.install_status == InstallStatus.NOT_INSTALLED

    def test_agent_manifest(self):
        """Test agent manifest model."""
        manifest = AgentManifest(
            agent_id="test.agent",
            name="Test Agent",
            version="1.0.0",
            capabilities=["chat"],
            tools=[{"name": "tool1", "description": "Tool 1"}],
        )

        assert manifest.agent_id == "test.agent"
        assert len(manifest.capabilities) == 1


class TestOutputConfig:
    """Tests for OutputConfig model."""

    def test_default_config(self):
        """Test default output configuration."""
        config = OutputConfig()
        assert config.format == "markdown"

    def test_custom_config(self):
        """Test custom output configuration."""
        config = OutputConfig(
            format="json",
            max_tokens=5000,
            structured_output_schema={"type": "object"},
        )

        assert config.format == "json"
        assert config.max_tokens == 5000

    def test_max_tokens_validation(self):
        """Test max_tokens validation."""
        # Valid range: 1-32000
        config = OutputConfig(max_tokens=1)
        assert config.max_tokens == 1

        config = OutputConfig(max_tokens=32000)
        assert config.max_tokens == 32000

        with pytest.raises(Exception):
            OutputConfig(max_tokens=0)

        with pytest.raises(Exception):
            OutputConfig(max_tokens=32001)
