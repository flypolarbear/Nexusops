"""
CI/CD Agent Unit Tests

Test cases for nexusops.cicd agent handler.
"""

import pytest
import asyncio

from app.agents.cicd import CICDAgentHandler
from app.gateway.executor.base import ExecutorRequest, ExecutorContext, ExecutorResult


@pytest.fixture
def agent():
    """Create CICDAgentHandler instance"""
    return CICDAgentHandler()


@pytest.fixture
def context():
    """Create ExecutorContext for testing"""
    return ExecutorContext(
        trace_id="test-trace-12345678901234567890",
        request_id="test-request-001",
        agent_id="nexusops.cicd",
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


class TestCICDAgentBasics:
    """Basic agent property tests"""

    def test_agent_id(self, agent):
        """Agent ID should be nexusops.cicd"""
        assert agent.agent_id == "nexusops.cicd"

    def test_capabilities(self, agent):
        """Agent should have all required capabilities"""
        expected_capabilities = [
            "pipeline_trigger",
            "pipeline_status",
            "pipeline_cancel",
            "build_logs",
            "pipeline_list",
            "jenkins_trigger",
            "argocd_sync",
        ]
        assert set(agent.capabilities) == set(expected_capabilities)

    def test_manifest(self, agent):
        """Manifest should contain correct metadata"""
        manifest = agent.get_manifest()
        assert manifest["agent_id"] == "nexusops.cicd"
        assert manifest["name"] == "Cicd Agent"
        assert manifest["version"] == "1.0.0"
        assert manifest["category"] == "cicd"
        assert len(manifest["tools"]) == 6

    def test_get_tools(self, agent):
        """Should return 6 tool definitions"""
        tools = agent.get_tools()
        tool_names = [t["name"] for t in tools]
        expected_tools = [
            "trigger_jenkins_build",
            "trigger_argocd_sync",
            "get_pipeline_status",
            "cancel_pipeline",
            "get_build_logs",
            "list_pipelines",
        ]
        assert set(tool_names) == set(expected_tools)


class TestTriggerPipeline:
    """Tests for pipeline trigger functionality"""

    @pytest.mark.asyncio
    async def test_trigger_pipeline_returns_success(self, agent, make_request):
        """Trigger pipeline should return success"""
        request = make_request("trigger pipeline")
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_trigger_pipeline_has_structured_output(self, agent, make_request):
        """Trigger pipeline should return structured output"""
        # Use "trigger" keyword explicitly (not "build" which routes to jenkins)
        request = make_request("trigger pipeline frontend-app")
        result = await agent.handle(request)
        assert result.structured_output is not None
        assert result.structured_output["type"] == "pipeline_triggered"

    @pytest.mark.asyncio
    async def test_trigger_pipeline_has_build_id(self, agent, make_request):
        """Trigger pipeline should return build_id"""
        request = make_request("trigger pipeline frontend-build")
        result = await agent.handle(request)
        assert "build_id" in result.structured_output
        assert result.structured_output["build_id"].startswith("build-")

    @pytest.mark.asyncio
    async def test_trigger_pipeline_has_suggested_actions(self, agent, make_request):
        """Trigger pipeline should return suggested actions"""
        request = make_request("trigger pipeline")
        result = await agent.handle(request)
        assert len(result.suggested_actions) >= 2


class TestJenkinsBuild:
    """Tests for Jenkins build functionality"""

    @pytest.mark.asyncio
    async def test_trigger_jenkins_returns_success(self, agent, make_request):
        """Trigger Jenkins build should return success"""
        request = make_request("trigger jenkins build")
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_trigger_jenkins_has_structured_output(self, agent, make_request):
        """Trigger Jenkins build should return structured output"""
        request = make_request("trigger jenkins build frontend")
        result = await agent.handle(request)
        assert result.structured_output is not None
        assert result.structured_output["type"] == "jenkins_build_triggered"

    @pytest.mark.asyncio
    async def test_trigger_jenkins_has_jenkins_url(self, agent, make_request):
        """Trigger Jenkins build should include Jenkins URL"""
        request = make_request("trigger jenkins build")
        result = await agent.handle(request)
        assert "jenkins_url" in result.structured_output


class TestArgoCDSync:
    """Tests for ArgoCD sync functionality"""

    @pytest.mark.asyncio
    async def test_argocd_sync_returns_success(self, agent, make_request):
        """ArgoCD sync should return success"""
        request = make_request("argocd sync production")
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_argocd_sync_has_structured_output(self, agent, make_request):
        """ArgoCD sync should return structured output"""
        request = make_request("argocd sync")
        result = await agent.handle(request)
        assert result.structured_output is not None
        assert result.structured_output["type"] == "argocd_sync_triggered"

    @pytest.mark.asyncio
    async def test_argocd_sync_has_sync_id(self, agent, make_request):
        """ArgoCD sync should return sync_id"""
        request = make_request("argocd sync")
        result = await agent.handle(request)
        assert "sync_id" in result.structured_output


class TestPipelineStatus:
    """Tests for pipeline status query"""

    @pytest.mark.asyncio
    async def test_status_query_returns_success(self, agent, make_request):
        """Status query should return success"""
        request = make_request("status pipeline-123")
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_status_query_has_structured_output(self, agent, make_request):
        """Status query should return structured output"""
        request = make_request("check status build-123")
        result = await agent.handle(request)
        assert result.structured_output is not None
        assert result.structured_output["type"] == "pipeline_status"

    @pytest.mark.asyncio
    async def test_status_query_has_stages(self, agent, make_request):
        """Status query should return stages"""
        request = make_request("status pipeline-123")
        result = await agent.handle(request)
        assert "stages" in result.structured_output
        assert len(result.structured_output["stages"]) >= 3


class TestCancelPipeline:
    """Tests for pipeline cancellation"""

    @pytest.mark.asyncio
    async def test_cancel_pipeline_returns_success(self, agent, make_request):
        """Cancel pipeline should return success"""
        request = make_request("cancel pipeline-123")
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_cancel_pipeline_has_structured_output(self, agent, make_request):
        """Cancel pipeline should return structured output"""
        # Use explicit cancel keyword without "build" to avoid jenkins route
        request = make_request("cancel pipeline-123")
        result = await agent.handle(request)
        assert result.structured_output is not None
        assert result.structured_output["type"] == "pipeline_cancelled"
        assert result.structured_output["status"] == "cancelled"


class TestBuildLogs:
    """Tests for build logs"""

    @pytest.mark.asyncio
    async def test_logs_query_returns_success(self, agent, make_request):
        """Logs query should return success"""
        request = make_request("logs build-123")
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_logs_query_has_structured_output(self, agent, make_request):
        """Logs query should return structured output"""
        request = make_request("get build logs build-123")
        result = await agent.handle(request)
        assert result.structured_output is not None
        assert result.structured_output["type"] == "build_logs"

    @pytest.mark.asyncio
    async def test_logs_query_has_logs_array(self, agent, make_request):
        """Logs query should return logs array"""
        request = make_request("logs build-123")
        result = await agent.handle(request)
        assert "logs" in result.structured_output
        assert len(result.structured_output["logs"]) > 0


class TestListPipelines:
    """Tests for listing pipelines"""

    @pytest.mark.asyncio
    async def test_list_pipelines_returns_success(self, agent, make_request):
        """List pipelines should return success"""
        request = make_request("list all pipelines")
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_list_pipelines_has_structured_output(self, agent, make_request):
        """List pipelines should return structured output"""
        request = make_request("show pipelines")
        result = await agent.handle(request)
        assert result.structured_output is not None
        assert result.structured_output["type"] == "pipeline_list"

    @pytest.mark.asyncio
    async def test_list_pipelines_has_pipelines_array(self, agent, make_request):
        """List pipelines should return pipelines array"""
        request = make_request("list pipelines")
        result = await agent.handle(request)
        assert "pipelines" in result.structured_output
        assert len(result.structured_output["pipelines"]) > 0


class TestGeneralQuery:
    """Tests for general CI/CD queries"""

    @pytest.mark.asyncio
    async def test_general_query_returns_success(self, agent, make_request):
        """General query should return success"""
        request = make_request("show me cicd info")
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_general_query_has_overview_type(self, agent, make_request):
        """General query should return overview type"""
        request = make_request("cicd overview")
        result = await agent.handle(request)
        assert result.structured_output is not None
        assert result.structured_output["type"] == "cicd_overview"


# Run tests directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
