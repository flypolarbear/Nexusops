"""
Deploy Agent Unit Tests

Test cases for nexusops.deploy agent handler.
"""

import pytest

from app.agents.deploy import DeployAgentHandler
from app.gateway.executor.base import ExecutorRequest, ExecutorContext


@pytest.fixture
def agent():
    """Create DeployAgentHandler instance"""
    return DeployAgentHandler()


@pytest.fixture
def context():
    """Create ExecutorContext for testing"""
    return ExecutorContext(
        trace_id="test-trace-12345678901234567890",
        request_id="test-request-002",
        agent_id="nexusops.deploy",
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


class TestDeployAgentBasics:
    """Basic agent property tests"""

    def test_agent_id(self, agent):
        """Agent ID should be nexusops.deploy"""
        assert agent.agent_id == "nexusops.deploy"

    def test_capabilities(self, agent):
        """Agent should have all required capabilities"""
        expected_capabilities = [
            "deploy_create",
            "deploy_rollback",
            "deploy_status",
            "deploy_force_sync",
        ]
        assert set(agent.capabilities) == set(expected_capabilities)

    def test_get_tools(self, agent):
        """Should return tool definitions"""
        tools = agent.get_tools()
        tool_names = [t["name"] for t in tools]
        expected_tools = [
            "create_deployment",
            "rollback_deployment",
            "force_sync",
        ]
        assert set(tool_names) == set(expected_tools)


class TestDeployOperations:
    """Tests for deploy operations"""

    @pytest.mark.asyncio
    async def test_deploy_create_returns_success(self, agent, make_request):
        """Deploy create should return success"""
        request = make_request("deploy phoenix", {"codename": "phoenix"})
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_deploy_create_has_structured_output(self, agent, make_request):
        """Deploy create should return structured output"""
        request = make_request("deploy phoenix", {"codename": "phoenix"})
        result = await agent.handle(request)
        assert result.structured_output is not None
        assert result.structured_output["type"] == "deployment_result"
        assert result.structured_output["codename"] == "phoenix"
        assert result.structured_output["status"] == "success"

    @pytest.mark.asyncio
    async def test_deploy_create_has_services(self, agent, make_request):
        """Deploy create should include services"""
        request = make_request("deploy phoenix", {"codename": "phoenix"})
        result = await agent.handle(request)
        services = result.structured_output["services"]
        assert len(services) == 3
        service_names = [s["name"] for s in services]
        assert "api" in service_names
        assert "worker" in service_names
        assert "web" in service_names


class TestRollbackOperations:
    """Tests for rollback operations"""

    @pytest.mark.asyncio
    async def test_rollback_returns_success(self, agent, make_request):
        """Rollback should return success"""
        request = make_request("rollback phoenix", {"codename": "phoenix"})
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_rollback_has_structured_output(self, agent, make_request):
        """Rollback should return structured output"""
        request = make_request("rollback phoenix", {"codename": "phoenix", "region": "us-east"})
        result = await agent.handle(request)
        assert result.structured_output is not None
        assert result.structured_output["type"] == "rollback_result"
        assert result.structured_output["codename"] == "phoenix"
        assert result.structured_output["region"] == "us-east"


class TestStatusOperations:
    """Tests for status operations"""

    @pytest.mark.asyncio
    async def test_status_returns_success(self, agent, make_request):
        """Status query should return success"""
        request = make_request("status phoenix", {"codename": "phoenix"})
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_status_has_regions(self, agent, make_request):
        """Status should include regional deployment info"""
        request = make_request("status phoenix", {"codename": "phoenix"})
        result = await agent.handle(request)
        assert result.structured_output["type"] == "deployment_status"
        regions = result.structured_output["regions"]
        assert len(regions) == 3


class TestSyncOperations:
    """Tests for sync operations"""

    @pytest.mark.asyncio
    async def test_sync_returns_success(self, agent, make_request):
        """Sync should return success"""
        request = make_request("sync phoenix", {"codename": "phoenix"})
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_sync_has_structured_output(self, agent, make_request):
        """Sync should return structured output"""
        request = make_request("sync phoenix", {"codename": "phoenix"})
        result = await agent.handle(request)
        assert result.structured_output["type"] == "sync_result"
        assert result.structured_output["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_sync_has_suggested_actions(self, agent, make_request):
        """Sync should return suggested actions"""
        request = make_request("sync phoenix", {"codename": "phoenix"})
        result = await agent.handle(request)
        assert len(result.suggested_actions) >= 1


# Run tests directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
