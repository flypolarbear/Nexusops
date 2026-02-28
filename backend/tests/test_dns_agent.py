"""
DNS Agent Unit Tests

Test cases for nexusops.dns agent handler.
"""

import pytest

from app.agents.dns import DNSAgentHandler
from app.gateway.executor.base import ExecutorRequest, ExecutorContext


@pytest.fixture
def agent():
    """Create DNSAgentHandler instance"""
    return DNSAgentHandler()


@pytest.fixture
def context():
    """Create ExecutorContext for testing"""
    return ExecutorContext(
        trace_id="test-trace-12345678901234567890",
        request_id="test-request-003",
        agent_id="nexusops.dns",
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


class TestDNSAgentBasics:
    """Basic agent property tests"""

    def test_agent_id(self, agent):
        """Agent ID should be nexusops.dns"""
        assert agent.agent_id == "nexusops.dns"

    def test_capabilities(self, agent):
        """Agent should have all required capabilities"""
        expected_capabilities = [
            "dns_record_create",
            "dns_record_delete",
            "dns_record_query",
            "random_domain_generate",
        ]
        assert set(agent.capabilities) == set(expected_capabilities)

    def test_get_tools(self, agent):
        """Should return tool definitions"""
        tools = agent.get_tools()
        tool_names = [t["name"] for t in tools]
        expected_tools = [
            "create_dns_record",
            "generate_random_subdomain",
        ]
        assert set(tool_names) == set(expected_tools)


class TestCreateRecord:
    """Tests for DNS record creation"""

    @pytest.mark.asyncio
    async def test_create_returns_success(self, agent, make_request):
        """Create record should return success"""
        request = make_request("create dns record", {
            "zone_id": "example.com",
            "resource_name": "www",
            "resource_type": "A",
        })
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_create_has_structured_output(self, agent, make_request):
        """Create record should return structured output"""
        request = make_request("add dns record", {
            "zone_id": "nexusops.io",
            "resource_name": "api",
            "resource_type": "CNAME",
        })
        result = await agent.handle(request)
        assert result.structured_output is not None
        assert result.structured_output["type"] == "dns_record_created"
        assert result.structured_output["zone"] == "nexusops.io"
        assert result.structured_output["record_name"] == "api"
        assert result.structured_output["status"] == "created"


class TestDeleteRecord:
    """Tests for DNS record deletion"""

    @pytest.mark.asyncio
    async def test_delete_returns_success(self, agent, make_request):
        """Delete record should return success"""
        request = make_request("delete dns record", {
            "zone_id": "example.com",
            "resource_name": "old-record",
        })
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_delete_has_structured_output(self, agent, make_request):
        """Delete record should return structured output"""
        request = make_request("remove dns record", {
            "zone_id": "nexusops.io",
            "resource_name": "stale",
        })
        result = await agent.handle(request)
        assert result.structured_output["type"] == "dns_record_deleted"
        assert result.structured_output["status"] == "deleted"


class TestQueryRecord:
    """Tests for DNS record query"""

    @pytest.mark.asyncio
    async def test_query_returns_success(self, agent, make_request):
        """Query record should return success"""
        request = make_request("query example.com", {
            "resource_name": "example.com",
        })
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_query_has_records(self, agent, make_request):
        """Query should return DNS records"""
        request = make_request("lookup nexusops.io", {
            "resource_name": "nexusops.io",
        })
        result = await agent.handle(request)
        assert result.structured_output["type"] == "dns_query_result"
        records = result.structured_output["records"]
        assert len(records) >= 1
        # Check record structure
        for record in records:
            assert "type" in record
            assert "name" in record
            assert "value" in record
            assert "ttl" in record


class TestGenerateDomain:
    """Tests for random domain generation"""

    @pytest.mark.asyncio
    async def test_generate_returns_success(self, agent, make_request):
        """Generate domain should return success"""
        request = make_request("generate random domain", {
            "codename": "test.nexusops.io",
            "namespace": 4,
        })
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_generate_has_structured_output(self, agent, make_request):
        """Generate domain should return structured output"""
        request = make_request("random domain", {
            "codename": "dev.nexusops.io",
            "namespace": 3,
        })
        result = await agent.handle(request)
        assert result.structured_output["type"] == "random_domain"
        assert result.structured_output["base_domain"] == "dev.nexusops.io"
        assert result.structured_output["full_domain"].endswith(".dev.nexusops.io")

    @pytest.mark.asyncio
    async def test_generate_has_suggested_actions(self, agent, make_request):
        """Generate should return suggested actions"""
        request = make_request("generate domain", {
            "codename": "test.nexusops.io",
        })
        result = await agent.handle(request)
        assert len(result.suggested_actions) >= 1


class TestDNSStatus:
    """Tests for DNS status"""

    @pytest.mark.asyncio
    async def test_status_returns_success(self, agent, make_request):
        """Status query should return success"""
        request = make_request("dns status", {})
        result = await agent.handle(request)
        assert result.success is True


# Run tests directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
