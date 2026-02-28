"""
Chat Agent Unit Tests

Test cases for nexusops.chat agent handler.
"""

import pytest

from app.agents.chat import ChatAgentHandler
from app.gateway.executor.base import ExecutorRequest, ExecutorContext


@pytest.fixture
def agent():
    """Create ChatAgentHandler instance"""
    return ChatAgentHandler()


@pytest.fixture
def context():
    """Create ExecutorContext for testing"""
    return ExecutorContext(
        trace_id="test-trace-12345678901234567890",
        request_id="test-request-001",
        agent_id="nexusops.chat",
    )


@pytest.fixture
def make_request(context):
    """Factory to create ExecutorRequest"""
    def _make(query: str, request_context: dict = None):
        return ExecutorRequest(
            context=context,
            query=query,
            request_context=request_context or {},
        )
    return _make


class TestChatAgentBasics:
    """Basic agent property tests"""

    def test_agent_id(self, agent):
        """Agent ID should be nexusops.chat"""
        assert agent.agent_id == "nexusops.chat"

    def test_capabilities(self, agent):
        """Agent should have all required capabilities"""
        expected_capabilities = [
            "chat",
            "quick_commands",
            "deployment_info",
            "status_query",
            "llm_integration",
        ]
        assert set(agent.capabilities) == set(expected_capabilities)

    def test_get_tools(self, agent):
        """Should return tool definitions"""
        tools = agent.get_tools()
        assert isinstance(tools, list)
        tool_names = [t["name"] for t in tools]
        assert "get_deployment_status" in tool_names


class TestChatAgentCommands:
    """Tests for chat agent quick commands"""

    @pytest.mark.asyncio
    async def test_deploy_command(self, agent, make_request):
        """/deploy command should return deployment status"""
        request = make_request("/deploy phoenix")
        result = await agent.handle(request)
        assert result.success is True
        assert "Deployment" in result.content["text"]

    @pytest.mark.asyncio
    async def test_status_command(self, agent, make_request):
        """/status command should return version status"""
        request = make_request("/status phoenix")
        result = await agent.handle(request)
        assert result.success is True
        assert "Status" in result.content["text"]

    @pytest.mark.asyncio
    async def test_rollback_command(self, agent, make_request):
        """/rollback command should return rollback info"""
        request = make_request("/rollback phoenix")
        result = await agent.handle(request)
        assert result.success is True
        assert "Rollback" in result.content["text"]
        # Check for danger action
        has_danger_action = any(
            a.get("danger", False) for a in result.suggested_actions
        )
        assert has_danger_action, "Rollback should have dangerous action"

    @pytest.mark.asyncio
    async def test_logs_command(self, agent, make_request):
        """/logs command should return logs"""
        request = make_request("/logs api-server")
        result = await agent.handle(request)
        assert result.success is True
        assert "Logs" in result.content["text"]


class TestChatAgentGeneral:
    """Tests for general chat handling"""

    @pytest.mark.asyncio
    async def test_general_query_returns_success(self, agent, make_request):
        """General query should return success"""
        request = make_request("hello, what can you do?")
        result = await agent.handle(request)
        assert result.success is True
        assert result.content["text"] is not None
