"""
Cost Agent Unit Tests

Test cases for nexusops.cost agent handler.
"""

import pytest
import asyncio

from app.agents.cost import CostAgentHandler
from app.gateway.executor.base import ExecutorRequest, ExecutorContext, ExecutorResult


@pytest.fixture
def agent():
    """Create CostAgentHandler instance"""
    return CostAgentHandler()


@pytest.fixture
def context():
    """Create ExecutorContext for testing"""
    return ExecutorContext(
        trace_id="test-trace-12345678901234567890",
        request_id="test-request-001",
        agent_id="nexusops.cost",
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


class TestCostAgentBasics:
    """Basic agent property tests"""

    def test_agent_id(self, agent):
        """Agent ID should be nexusops.cost"""
        assert agent.agent_id == "nexusops.cost"

    def test_capabilities(self, agent):
        """Agent should have all required capabilities"""
        expected_capabilities = [
            "cost_query",
            "cost_by_service",
            "cost_by_region",
            "cost_trend_analysis",
            "budget_comparison",
            "budget_alert",
            "cost_optimization",
            "resource_utilization",
        ]
        assert set(agent.capabilities) == set(expected_capabilities)

    def test_manifest(self, agent):
        """Manifest should contain correct metadata"""
        manifest = agent.get_manifest()
        assert manifest["agent_id"] == "nexusops.cost"
        assert manifest["name"] == "Cost Agent"
        assert manifest["version"] == "1.0.0"
        assert manifest["category"] == "cost"
        assert len(manifest["tools"]) == 7

    def test_get_tools(self, agent):
        """Should return 7 tool definitions"""
        tools = agent.get_tools()
        tool_names = [t["name"] for t in tools]
        expected_tools = [
            "get_cost_overview",
            "get_cost_by_service",
            "get_cost_by_region",
            "get_cost_trend",
            "get_budget_status",
            "get_optimization_suggestions",
            "get_resource_utilization",
        ]
        assert set(tool_names) == set(expected_tools)


class TestGeneralCostQuery:
    """Tests for general cost query handling"""

    @pytest.mark.asyncio
    async def test_general_query_returns_success(self, agent, make_request):
        """General cost query should return success"""
        request = make_request("show me costs")
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_general_query_has_structured_output(self, agent, make_request):
        """General cost query should return structured output"""
        request = make_request("show me costs")
        result = await agent.handle(request)
        assert result.structured_output is not None
        assert result.structured_output["type"] == "cost_overview"

    @pytest.mark.asyncio
    async def test_general_query_has_cost_data(self, agent, make_request):
        """General cost query should include by_service and by_region"""
        request = make_request("show me costs")
        result = await agent.handle(request)
        data = result.structured_output["data"]
        assert "total_cost" in data
        assert "budget" in data
        assert "by_service" in data
        assert "by_region" in data
        assert data["total_cost"] > 0

    @pytest.mark.asyncio
    async def test_general_query_has_suggested_actions(self, agent, make_request):
        """General cost query should return suggested actions"""
        request = make_request("show me costs")
        result = await agent.handle(request)
        assert len(result.suggested_actions) == 3
        action_labels = [a["label"] for a in result.suggested_actions]
        assert "View Cost Trend" in action_labels
        assert "Get Optimization Tips" in action_labels


class TestCostByService:
    """Tests for cost by service handling"""

    @pytest.mark.asyncio
    async def test_service_query_returns_success(self, agent, make_request):
        """Service query should return success"""
        request = make_request("cost by service")
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_service_query_has_service_breakdown(self, agent, make_request):
        """Service query should return breakdown by service"""
        request = make_request("cost by service breakdown")
        result = await agent.handle(request)
        data = result.structured_output["data"]
        assert "by_service" in data
        assert "EC2" in data["by_service"]
        assert "RDS" in data["by_service"]

    @pytest.mark.asyncio
    async def test_service_query_includes_change_percentage(self, agent, make_request):
        """Service query should include month-over-month change"""
        request = make_request("cost by service")
        result = await agent.handle(request)
        data = result.structured_output["data"]["by_service"]
        # Each service should have cost and change
        for service, info in data.items():
            assert "cost" in info
            assert "change" in info


class TestCostByRegion:
    """Tests for cost by region handling"""

    @pytest.mark.asyncio
    async def test_region_query_returns_success(self, agent, make_request):
        """Region query should return success"""
        request = make_request("cost by region")
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_region_query_has_region_breakdown(self, agent, make_request):
        """Region query should return breakdown by region"""
        request = make_request("cost by region breakdown")
        result = await agent.handle(request)
        data = result.structured_output["data"]
        assert "by_region" in data
        assert "us-east-1" in data["by_region"]


class TestTrendAnalysis:
    """Tests for cost trend analysis"""

    @pytest.mark.asyncio
    async def test_trend_query_returns_success(self, agent, make_request):
        """Trend query should return success"""
        request = make_request("cost trend analysis")
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_trend_query_has_trend_data(self, agent, make_request):
        """Trend query should return trend data points"""
        request = make_request("cost trend analysis")
        result = await agent.handle(request)
        data = result.structured_output["data"]
        assert "trend" in data
        assert len(data["trend"]) == 30  # 30 days of data

    @pytest.mark.asyncio
    async def test_trend_query_has_averages(self, agent, make_request):
        """Trend query should return weekly and monthly averages"""
        request = make_request("cost trend analysis")
        result = await agent.handle(request)
        data = result.structured_output["data"]
        assert "weekly_average" in data
        assert "monthly_average" in data
        assert "projected_monthly" in data

    @pytest.mark.asyncio
    async def test_trend_data_has_date_and_cost(self, agent, make_request):
        """Each trend data point should have date and cost"""
        request = make_request("cost trend analysis")
        result = await agent.handle(request)
        trend = result.structured_output["data"]["trend"]
        for point in trend:
            assert "date" in point
            assert "cost" in point


class TestBudgetComparison:
    """Tests for budget comparison"""

    @pytest.mark.asyncio
    async def test_budget_query_returns_success(self, agent, make_request):
        """Budget query should return success"""
        request = make_request("budget comparison")
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_budget_query_has_budget_data(self, agent, make_request):
        """Budget query should return budget comparison data"""
        request = make_request("budget comparison")
        result = await agent.handle(request)
        data = result.structured_output["data"]
        assert "budget" in data
        assert "current_spend" in data
        assert "remaining" in data
        assert "projected_spend" in data
        assert "alert_level" in data

    @pytest.mark.asyncio
    async def test_budget_query_has_valid_alert_level(self, agent, make_request):
        """Budget query should return valid alert level"""
        request = make_request("budget comparison")
        result = await agent.handle(request)
        alert_level = result.structured_output["data"]["alert_level"]
        assert alert_level in ["normal", "warning", "critical"]


class TestCostOptimization:
    """Tests for cost optimization suggestions"""

    @pytest.mark.asyncio
    async def test_optimization_query_returns_success(self, agent, make_request):
        """Optimization query should return success"""
        request = make_request("cost optimization suggestions")
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_optimization_has_tips(self, agent, make_request):
        """Optimization query should return optimization tips"""
        request = make_request("cost optimization suggestions")
        result = await agent.handle(request)
        tips = result.structured_output["data"]["optimization_tips"]
        assert len(tips) >= 3

    @pytest.mark.asyncio
    async def test_optimization_tips_have_required_fields(self, agent, make_request):
        """Each optimization tip should have required fields"""
        request = make_request("cost optimization suggestions")
        result = await agent.handle(request)
        tips = result.structured_output["data"]["optimization_tips"]
        for tip in tips:
            assert "title" in tip
            assert "description" in tip
            assert "potential_savings" in tip
            assert "priority" in tip
            assert "resources" in tip

    @pytest.mark.asyncio
    async def test_optimization_has_total_savings(self, agent, make_request):
        """Optimization should include total potential savings"""
        request = make_request("cost optimization suggestions")
        result = await agent.handle(request)
        data = result.structured_output["data"]
        assert "total_potential_savings" in data
        assert data["total_potential_savings"] > 0

    @pytest.mark.asyncio
    async def test_optimization_has_suggested_actions(self, agent, make_request):
        """Optimization query should return suggested actions"""
        request = make_request("cost optimization suggestions")
        result = await agent.handle(request)
        assert len(result.suggested_actions) >= 2
        # Check that actions have confirm_required for dangerous operations
        delete_action = next(
            (a for a in result.suggested_actions if "delete" in a["id"].lower()),
            None
        )
        if delete_action:
            assert delete_action.get("confirm_required") is True


class TestResourceUtilization:
    """Tests for resource utilization analysis"""

    @pytest.mark.asyncio
    async def test_utilization_query_returns_success(self, agent, make_request):
        """Utilization query should return success"""
        request = make_request("resource utilization analysis")
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_utilization_has_resource_types(self, agent, make_request):
        """Utilization should include all resource types"""
        request = make_request("resource utilization analysis")
        result = await agent.handle(request)
        data = result.structured_output["data"]
        assert "EC2" in data
        assert "RDS" in data
        assert "Lambda" in data
        assert "S3" in data

    @pytest.mark.asyncio
    async def test_ec2_utilization_has_required_fields(self, agent, make_request):
        """EC2 utilization should include required fields"""
        request = make_request("resource utilization analysis")
        result = await agent.handle(request)
        ec2_data = result.structured_output["data"]["EC2"]
        assert "total_instances" in ec2_data
        assert "avg_cpu" in ec2_data
        assert "underutilized" in ec2_data


class TestChineseQueries:
    """Tests for Chinese language queries"""

    @pytest.mark.asyncio
    async def test_chinese_trend_query(self, agent, make_request):
        """Chinese trend query should work"""
        request = make_request("cost trend analysis")
        result = await agent.handle(request)
        assert result.success is True
        assert result.structured_output["type"] == "cost_trend"

    @pytest.mark.asyncio
    async def test_chinese_optimization_query(self, agent, make_request):
        """Chinese optimization query should work"""
        request = make_request("cost optimization suggestions")
        result = await agent.handle(request)
        assert result.success is True
        assert result.structured_output["type"] == "cost_optimization"


# Run tests directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
