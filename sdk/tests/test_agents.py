"""
NexusOps SDK - Agents Tests

Tests for Agent base class and registration utilities.
"""

import pytest

from nexusops_sdk.agents import AgentBase, register_agent_decorator, AgentRegistrationBuilder
from nexusops_sdk.models import AgentRequest, AgentResponse, AgentContent


class SimpleTestAgent(AgentBase):
    """Simple test agent implementation."""

    def __init__(self):
        super().__init__(
            agent_id="test.simple",
            name="Simple Test Agent",
            version="1.0.0",
            description="A simple test agent",
            category="test",
            capabilities=["echo", "reverse"],
        )

    async def invoke(self, request: AgentRequest) -> AgentResponse:
        """Echo the query back."""
        return self.success_response(
            text=f"Echo: {request.query}",
            request_id=request.request_id,
        )


class TestAgentBase:
    """Tests for AgentBase class."""

    @pytest.fixture
    def agent(self):
        """Create a test agent."""
        return SimpleTestAgent()

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.agent_id == "test.simple"
        assert agent.name == "Simple Test Agent"
        assert agent.version == "1.0.0"
        assert agent.category == "test"
        assert "echo" in agent.capabilities

    def test_get_manifest(self, agent):
        """Test getting agent manifest."""
        manifest = agent.get_manifest()

        assert manifest["agent_id"] == "test.simple"
        assert manifest["name"] == "Simple Test Agent"
        assert manifest["version"] == "1.0.0"
        assert manifest["category"] == "test"
        assert manifest["capabilities"] == ["echo", "reverse"]

    @pytest.mark.asyncio
    async def test_invoke(self, agent):
        """Test agent invocation."""
        request = AgentRequest(
            request_id="test-123",
            agent_id="test.simple",
            query="Hello World",
        )

        response = await agent.invoke(request)

        assert isinstance(response, AgentResponse)
        assert response.status == "success"
        assert "Hello World" in response.content.text
        assert response.is_success

    def test_success_response_helper(self, agent):
        """Test success_response helper method."""
        response = AgentBase.success_response(
            text="Success message",
            format="markdown",
            request_id="req-123",
            trace_id="trace-456",
        )

        assert response.status == "success"
        assert response.content.text == "Success message"
        assert response.request_id == "req-123"
        assert response.trace_id == "trace-456"

    def test_error_response_helper(self, agent):
        """Test error_response helper method."""
        response = AgentBase.error_response(
            code="EXEC_INTERNAL_ERROR",
            message="Something went wrong",
            details={"reason": "test error"},
            request_id="req-123",
        )

        assert response.status == "error"
        assert response.error.code == "EXEC_INTERNAL_ERROR"
        assert response.error.message == "Something went wrong"
        assert response.error.details == {"reason": "test error"}

    def test_partial_response_helper(self, agent):
        """Test partial_response helper method."""
        response = AgentBase.partial_response(
            text="Partial result",
            error_code="EXEC_PARTIAL_FAILURE",
            error_message="Some steps failed",
            request_id="req-123",
        )

        assert response.status == "partial"
        assert response.content.text == "Partial result"
        assert response.error.code == "EXEC_PARTIAL_FAILURE"


class TestRegistrationBuilder:
    """Tests for AgentRegistrationBuilder."""

    def test_build_basic_manifest(self):
        """Test building basic manifest."""
        manifest = (
            AgentRegistrationBuilder("test.agent")
            .with_name("Test Agent")
            .with_version("1.0.0")
            .build()
        )

        assert manifest["agent_id"] == "test.agent"
        assert manifest["name"] == "Test Agent"
        assert manifest["version"] == "1.0.0"

    def test_build_full_manifest(self):
        """Test building full manifest with all options."""
        manifest = (
            AgentRegistrationBuilder("test.full")
            .with_name("Full Agent")
            .with_version("2.0.0")
            .with_description("A fully configured agent")
            .with_author("Test Author")
            .with_category("infrastructure")
            .add_tag("kubernetes")
            .add_tag("deployment")
            .add_capability("deploy")
            .add_capability("rollback")
            .with_tool(
                name="deploy",
                description="Deploy application",
                input_schema={"type": "object"},
            )
            .with_input_schema({"type": "object"})
            .with_output_schema({"type": "object"})
            .build()
        )

        assert manifest["agent_id"] == "test.full"
        assert manifest["name"] == "Full Agent"
        assert manifest["version"] == "2.0.0"
        assert manifest["description"] == "A fully configured agent"
        assert manifest["author"] == "Test Author"
        assert manifest["category"] == "infrastructure"
        assert "kubernetes" in manifest["tags"]
        assert "deploy" in manifest["capabilities"]
        assert len(manifest["tools"]) == 1
        assert manifest["tools"][0]["name"] == "deploy"

    def test_build_with_pricing(self):
        """Test building manifest with pricing."""
        manifest = (
            AgentRegistrationBuilder("test.paid")
            .with_name("Paid Agent")
            .with_pricing({
                "model": "per_request",
                "price": 0.01,
            })
            .build()
        )

        assert "pricing" in manifest
        assert manifest["pricing"]["model"] == "per_request"


class TestRegisterAgentDecorator:
    """Tests for register_agent_decorator."""

    @pytest.mark.asyncio
    async def test_decorator_creates_function_agent(self):
        """Test decorator creates a FunctionAgent."""
        @register_agent_decorator(
            agent_id="test.decorated",
            name="Decorated Agent",
            description="Created via decorator",
        )
        async def my_handler(request: AgentRequest) -> AgentResponse:
            return AgentResponse(
                request_id=request.request_id,
                status="success",
                content=AgentContent(text=f"Handled: {request.query}", format="markdown"),
            )

        assert hasattr(my_handler, "agent_id")
        assert my_handler.agent_id == "test.decorated"
        assert my_handler.name == "Decorated Agent"

        # Test invocation
        request = AgentRequest(
            request_id="req-123",
            agent_id="test.decorated",
            query="Test query",
        )

        response = await my_handler.invoke(request)
        assert response.status == "success"
        assert "Test query" in response.content.text

    @pytest.mark.asyncio
    async def test_decorator_with_sync_handler(self):
        """Test decorator with sync handler."""
        @register_agent_decorator(
            agent_id="test.sync",
            name="Sync Agent",
        )
        def sync_handler(request: AgentRequest) -> str:
            return f"Sync response: {request.query}"

        request = AgentRequest(
            request_id="req-123",
            agent_id="test.sync",
            query="Hello",
        )

        response = await sync_handler.invoke(request)
        assert response.status == "success"
        assert "Hello" in response.content.text

    @pytest.mark.asyncio
    async def test_decorator_error_handling(self):
        """Test decorator handles exceptions."""
        @register_agent_decorator(
            agent_id="test.error",
            name="Error Agent",
        )
        async def error_handler(request: AgentRequest):
            raise ValueError("Test error")

        request = AgentRequest(
            request_id="req-123",
            agent_id="test.error",
            query="Test",
        )

        response = await error_handler.invoke(request)
        assert response.status == "error"
        assert "Test error" in response.error.message


class TestAgentRepr:
    """Tests for agent string representation."""

    def test_agent_repr(self):
        """Test agent __repr__ method."""
        agent = SimpleTestAgent()
        repr_str = repr(agent)

        assert "SimpleTestAgent" in repr_str
        assert "test.simple" in repr_str
        assert "1.0.0" in repr_str
