"""
Logs Agent Unit Tests

Test cases for nexusops.logs agent handler.
"""

import pytest

from app.agents.logs import LogsAgentHandler
from app.gateway.executor.base import ExecutorRequest, ExecutorContext


@pytest.fixture
def agent():
    """Create LogsAgentHandler instance"""
    return LogsAgentHandler()


@pytest.fixture
def context():
    """Create ExecutorContext for testing"""
    return ExecutorContext(
        trace_id="test-trace-12345678901234567890",
        request_id="test-request-004",
        agent_id="nexusops.logs",
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


class TestLogsAgentBasics:
    """Basic agent property tests"""

    def test_agent_id(self, agent):
        """Agent ID should be nexusops.logs"""
        assert agent.agent_id == "nexusops.logs"

    def test_capabilities(self, agent):
        """Agent should have all required capabilities"""
        expected_capabilities = [
            "query_logs",
            "search_errors",
            "tail_logs",
            "filter_by_level",
            "filter_by_service",
            "search_keywords",
            "time_range",
        ]
        assert set(agent.capabilities) == set(expected_capabilities)

    def test_get_tools(self, agent):
        """Should return tool definitions"""
        tools = agent.get_tools()
        tool_names = [t["name"] for t in tools]
        expected_tools = [
            "query_logs",
            "search_logs",
            "get_log_stats",
        ]
        assert set(tool_names) == set(expected_tools)


class TestGeneralLogQuery:
    """Tests for general log query handling"""

    @pytest.mark.asyncio
    async def test_general_query_returns_success(self, agent, make_request):
        """General log query should return success"""
        request = make_request("show me logs")
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_general_query_has_structured_output(self, agent, make_request):
        """General log query should return structured output"""
        request = make_request("show me logs")
        result = await agent.handle(request)
        assert result.structured_output is not None
        assert result.structured_output["type"] == "log_query_result"

    @pytest.mark.asyncio
    async def test_general_query_has_logs(self, agent, make_request):
        """General log query should include logs"""
        request = make_request("show me logs")
        result = await agent.handle(request)
        data = result.structured_output
        assert "logs" in data
        assert "total_count" in data
        assert data["total_count"] > 0

    @pytest.mark.asyncio
    async def test_general_query_has_suggested_actions(self, agent, make_request):
        """General log query should return suggested actions"""
        request = make_request("show me logs")
        result = await agent.handle(request)
        assert len(result.suggested_actions) >= 1


class TestLogLevelFilter:
    """Tests for log level filtering"""

    @pytest.mark.asyncio
    async def test_error_query_returns_success(self, agent, make_request):
        """Error query should return success"""
        request = make_request("error logs")
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_error_query_has_error_logs(self, agent, make_request):
        """Error query should return error level logs"""
        request = make_request("error logs")
        result = await agent.handle(request)
        assert result.structured_output["type"] == "log_level_result"
        assert result.structured_output["level"] == "ERROR"
        logs = result.structured_output["logs"]
        for log in logs:
            assert log["level"] == "ERROR"

    @pytest.mark.asyncio
    async def test_warn_query_returns_warn_logs(self, agent, make_request):
        """Warn query should return warn level logs"""
        request = make_request("warning logs")
        result = await agent.handle(request)
        assert result.structured_output["level"] == "WARN"
        logs = result.structured_output["logs"]
        for log in logs:
            assert log["level"] == "WARN"


class TestServiceFilter:
    """Tests for service filtering"""

    @pytest.mark.asyncio
    async def test_service_query_returns_success(self, agent, make_request):
        """Service query should return success"""
        request = make_request("logs service=api", {"resource_name": "api"})
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_service_query_has_service_logs(self, agent, make_request):
        """Service query should return logs for specific service"""
        request = make_request("logs service=worker", {"resource_name": "worker"})
        result = await agent.handle(request)
        assert result.structured_output["type"] == "service_logs_result"
        assert result.structured_output["service"] == "worker"


class TestKeywordSearch:
    """Tests for keyword search"""

    @pytest.mark.asyncio
    async def test_search_returns_success(self, agent, make_request):
        """Search query should return success"""
        request = make_request("search timeout", {"keyword": "timeout"})
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_search_has_keyword(self, agent, make_request):
        """Search should include keyword in output"""
        request = make_request("search connection", {"keyword": "connection"})
        result = await agent.handle(request)
        assert result.structured_output["type"] == "search_result"
        assert result.structured_output["keyword"] == "connection"


class TestRecentLogs:
    """Tests for recent/tail logs"""

    @pytest.mark.asyncio
    async def test_recent_returns_success(self, agent, make_request):
        """Recent logs query should return success"""
        request = make_request("recent logs")
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_recent_has_time_range(self, agent, make_request):
        """Recent logs should include time range"""
        request = make_request("tail logs")
        result = await agent.handle(request)
        assert result.structured_output["type"] == "recent_logs_result"
        assert "time_range" in result.structured_output
        assert "start" in result.structured_output["time_range"]
        assert "end" in result.structured_output["time_range"]


class TestTimeRangeQuery:
    """Tests for time range queries"""

    @pytest.mark.asyncio
    async def test_time_range_returns_success(self, agent, make_request):
        """Time range query should return success"""
        request = make_request("logs from 1 hour ago")
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_time_range_has_time_info(self, agent, make_request):
        """Time range query should include time info"""
        request = make_request("logs range")
        result = await agent.handle(request)
        assert result.structured_output["type"] == "time_range_result"
        assert "time_range" in result.structured_output


# Run tests directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
