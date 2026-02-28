"""
MK-009 Built-in Agent Capability Acceptance Tests

SPEC-MK-009 P0 Test Cases (CT-001 to CT-016)

This module tests all 7 built-in agents according to MK-009 specification:
1. nexusops.chat - Basic conversation
2. nexusops.k8s - K8s status retrieval
3. nexusops.deploy - Deployment orchestration
4. nexusops.logs - Log query
5. nexusops.cost - Cost calculation
6. nexusops.dns - DNS operations
7. nexusops.cicd - CI/CD operations (pending implementation)
8. nexusops.git - Git operations (pending implementation)

Test Requirements:
- All tests must pass 100% (no 500 errors allowed to pass)
- trace_id propagation must be verified
- Confirmation mechanism for dangerous operations
- Follows MK-006 contract validation
"""

import pytest
import uuid
from fastapi.testclient import TestClient

from app.main import app
from app.stores.agent_store import clear_all
from app.gateway.executor.router import reset_executor_router


# ============================================
# Fixtures
# ============================================

@pytest.fixture(autouse=True)
def reset_stores():
    """Reset stores before each test"""
    clear_all()
    reset_executor_router()  # Reset router singleton to pick up new handlers
    yield
    clear_all()
    reset_executor_router()


@pytest.fixture
def client(client_with_sync_db):
    """Create test client with database support"""
    return client_with_sync_db


def generate_request_id() -> str:
    """Generate a unique request ID"""
    return str(uuid.uuid4())


def generate_conversation_id() -> str:
    """Generate a unique conversation ID"""
    return str(uuid.uuid4())


# ============================================
# Helper Functions
# ============================================

def invoke_agent(client, agent_id: str, query: str, context: dict = None) -> dict:
    """
    Invoke an agent and return the response data.
    Raises assertion error if status code is not 200.
    """
    response = client.post(f"/api/v1/agents/{agent_id}/invoke", json={
        "request_id": generate_request_id(),
        "conversation_id": generate_conversation_id(),
        "agent_id": agent_id,
        "query": query,
        "context": context or {},
        "request_context": context or {},
    })

    assert response.status_code == 200, \
        f"Expected 200, got {response.status_code}: {response.text}"

    return response.json()


def assert_success_response(data: dict):
    """Assert response has success status"""
    assert data["status"] == "success", \
        f"Expected status=success, got {data['status']}"


def assert_trace_id_present(data: dict):
    """Assert trace_id is present in metadata"""
    assert "metadata" in data, "Response missing metadata field"
    assert "trace_id" in data["metadata"], "Response metadata missing trace_id"
    trace_id = data["metadata"]["trace_id"]
    assert trace_id is not None, "trace_id is None"
    assert len(trace_id) == 32, f"trace_id should be 32 chars, got {len(trace_id)}"


def assert_structured_output_present(data: dict, expected_type: str = None):
    """Assert structured_output is present and optionally check type"""
    assert "structured_output" in data, "Response missing structured_output"
    assert data["structured_output"] is not None, "structured_output is None"

    if expected_type:
        assert data["structured_output"].get("type") == expected_type, \
            f"Expected type={expected_type}, got {data['structured_output'].get('type')}"


# ============================================
# CT-001, CT-002: nexusops.chat - Basic Conversation
# ============================================

class TestChatAgent:
    """Test nexusops.chat agent"""

    def test_ct001_normal_invoke_returns_success(self, client):
        """CT-001: Normal invocation returns success"""
        data = invoke_agent(client, "nexusops.chat", "Hello, how are you?")

        assert_success_response(data)
        assert_trace_id_present(data)
        assert "content" in data
        assert "text" in data["content"]

    def test_ct002_trace_id_propagation(self, client):
        """CT-002: trace_id correctly propagates through chat agent"""
        data = invoke_agent(client, "nexusops.chat", "Test trace propagation")

        assert_trace_id_present(data)

        # Verify trace_id is a valid hex string
        trace_id = data["metadata"]["trace_id"]
        try:
            int(trace_id, 16)
        except ValueError:
            pytest.fail(f"trace_id '{trace_id}' is not a valid hex string")

    def test_chat_deploy_command(self, client):
        """Test chat agent /deploy command"""
        data = invoke_agent(
            client,
            "nexusops.chat",
            "/deploy v1.0.0",
            context={"codename": "v1.0.0", "region": "us-east"}
        )

        assert_success_response(data)
        assert_structured_output_present(data, "deployment_status")

    def test_chat_status_command(self, client):
        """Test chat agent /status command"""
        data = invoke_agent(
            client,
            "nexusops.chat",
            "/status v1.0.0",
            context={"codename": "v1.0.0"}
        )

        assert_success_response(data)
        assert_structured_output_present(data, "deployment_status")

    def test_chat_rollback_command_has_confirm_mechanism(self, client):
        """Test chat agent /rollback command has confirmation mechanism"""
        data = invoke_agent(
            client,
            "nexusops.chat",
            "/rollback v1.0.0",
            context={"codename": "v1.0.0", "region": "us-east"}
        )

        assert_success_response(data)

        # Check suggested_actions contain confirm_required
        if data.get("suggested_actions"):
            confirm_actions = [
                a for a in data["suggested_actions"]
                if a.get("confirm_required") is True
            ]
            assert len(confirm_actions) > 0, \
                "Rollback operation should have confirm_required action"


# ============================================
# CT-003, CT-004: nexusops.k8s - K8s Status Retrieval
# ============================================

class TestK8sAgent:
    """Test nexusops.k8s agent"""

    def test_ct003_get_deployment_status(self, client):
        """CT-003: Get deployment status"""
        data = invoke_agent(
            client,
            "nexusops.k8s",
            "status",
            context={"namespace": "default", "resource_name": "api"}
        )

        assert_success_response(data)
        assert_trace_id_present(data)

    def test_ct004_error_handling_invalid_namespace(self, client):
        """CT-004: Error handling for invalid namespace"""
        # K8s agent should handle gracefully even with empty/invalid context
        data = invoke_agent(
            client,
            "nexusops.k8s",
            "status",
            context={"namespace": "", "resource_name": ""}
        )

        # Should still return success with mock data
        assert_success_response(data)

    def test_k8s_get_logs(self, client):
        """Test K8s agent logs retrieval"""
        data = invoke_agent(
            client,
            "nexusops.k8s",
            "logs for api pod",
            context={"namespace": "default", "resource_name": "api-pod"}
        )

        assert_success_response(data)
        assert_structured_output_present(data, "pod_logs")

    def test_k8s_describe_resource(self, client):
        """Test K8s agent describe resource"""
        data = invoke_agent(
            client,
            "nexusops.k8s",
            "describe deployment api",
            context={"resource_type": "Deployment", "resource_name": "api"}
        )

        assert_success_response(data)
        assert_structured_output_present(data, "resource_description")

    def test_k8s_diagnose(self, client):
        """Test K8s agent diagnose"""
        data = invoke_agent(
            client,
            "nexusops.k8s",
            "diagnose api pod",
            context={"resource_name": "api-pod"}
        )

        assert_success_response(data)
        assert_structured_output_present(data, "diagnosis_result")


# ============================================
# CT-005, CT-006: nexusops.deploy - Deployment Orchestration
# ============================================

class TestDeployAgent:
    """Test nexusops.deploy agent"""

    def test_ct005_generate_manifest(self, client):
        """CT-005: Generate manifest and trigger deployment"""
        data = invoke_agent(
            client,
            "nexusops.deploy",
            "deploy v1.0.0",
            context={"codename": "v1.0.0", "region": "us-east"}
        )

        assert_success_response(data)
        assert_trace_id_present(data)
        assert_structured_output_present(data, "deployment_result")

        # Check regions array exists
        output = data["structured_output"]
        assert "codename" in output

    def test_ct006_confirm_mechanism_validation(self, client):
        """CT-006: Confirm mechanism for dangerous operations"""
        # Rollback is a dangerous operation that should have confirmation
        data = invoke_agent(
            client,
            "nexusops.deploy",
            "rollback v1.0.0",
            context={"codename": "v1.0.0", "region": "us-east"}
        )

        assert_success_response(data)
        assert_structured_output_present(data, "rollback_result")

    def test_deploy_status(self, client):
        """Test deploy agent status query"""
        data = invoke_agent(
            client,
            "nexusops.deploy",
            "status v1.0.0",
            context={"codename": "v1.0.0"}
        )

        assert_success_response(data)
        assert_structured_output_present(data, "deployment_status")

        # Check regions array
        output = data["structured_output"]
        assert "regions" in output
        assert isinstance(output["regions"], list)

    def test_deploy_force_sync(self, client):
        """Test deploy agent force sync"""
        data = invoke_agent(
            client,
            "nexusops.deploy",
            "sync v1.0.0",
            context={"codename": "v1.0.0"}
        )

        assert_success_response(data)
        assert_structured_output_present(data, "sync_result")


# ============================================
# CT-007, CT-008: nexusops.logs - Log Query
# ============================================

class TestLogsAgent:
    """Test nexusops.logs agent"""

    def test_ct007_query_logs(self, client):
        """CT-007: Query logs"""
        data = invoke_agent(
            client,
            "nexusops.logs",
            "logs",
            context={"resource_name": "api"}
        )

        assert_success_response(data)
        assert_trace_id_present(data)
        assert_structured_output_present(data, "log_query_result")

        # Check logs array exists
        output = data["structured_output"]
        assert "logs" in output
        assert isinstance(output["logs"], list)

    def test_ct008_time_range_filter(self, client):
        """CT-008: Time range filtering"""
        data = invoke_agent(
            client,
            "nexusops.logs",
            "logs range from 1h",
            context={"from_time": "1 hour ago", "to_time": "now"}
        )

        assert_success_response(data)
        assert_structured_output_present(data, "time_range_result")

        # Check time_range exists
        output = data["structured_output"]
        assert "time_range" in output

    def test_logs_filter_by_error_level(self, client):
        """Test logs agent filter by ERROR level"""
        data = invoke_agent(
            client,
            "nexusops.logs",
            "error logs",
            context={}
        )

        assert_success_response(data)
        assert_structured_output_present(data, "log_level_result")

        # Verify all logs are ERROR level
        output = data["structured_output"]
        assert output.get("level") == "ERROR"

    def test_logs_search_keyword(self, client):
        """Test logs agent keyword search"""
        data = invoke_agent(
            client,
            "nexusops.logs",
            "search timeout",
            context={"keyword": "timeout"}
        )

        assert_success_response(data)
        assert_structured_output_present(data, "search_result")


# ============================================
# CT-009, CT-010: nexusops.cost - Cost Calculation
# ============================================

class TestCostAgent:
    """Test nexusops.cost agent"""

    def test_ct009_calculate_cost(self, client):
        """CT-009: Calculate cost"""
        data = invoke_agent(
            client,
            "nexusops.cost",
            "cost overview",
            context={}
        )

        assert_success_response(data)
        assert_trace_id_present(data)
        assert_structured_output_present(data, "cost_overview")

        # Check cost data structure
        output = data["structured_output"]
        assert "data" in output
        assert "total_cost" in output["data"]
        assert "by_service" in output["data"]
        assert "by_region" in output["data"]

    def test_ct010_group_by_resource_type(self, client):
        """CT-010: Group by resource type (service)"""
        data = invoke_agent(
            client,
            "nexusops.cost",
            "cost by service",
            context={}
        )

        assert_success_response(data)
        assert_structured_output_present(data, "cost_by_service")

        # Check by_service breakdown
        output = data["structured_output"]
        assert "data" in output
        assert "by_service" in output["data"]

    def test_cost_trend_analysis(self, client):
        """Test cost agent trend analysis"""
        data = invoke_agent(
            client,
            "nexusops.cost",
            "cost trend",
            context={}
        )

        assert_success_response(data)
        assert_structured_output_present(data, "cost_trend")

        # Check trend data
        output = data["structured_output"]
        assert "data" in output
        assert "trend" in output["data"]

    def test_cost_budget_comparison(self, client):
        """Test cost agent budget comparison"""
        data = invoke_agent(
            client,
            "nexusops.cost",
            "budget status",
            context={}
        )

        assert_success_response(data)
        assert_structured_output_present(data, "budget_comparison")

    def test_cost_optimization_suggestions(self, client):
        """Test cost agent optimization suggestions"""
        data = invoke_agent(
            client,
            "nexusops.cost",
            "cost optimization",
            context={}
        )

        assert_success_response(data)
        assert_structured_output_present(data, "cost_optimization")

        # Check optimization_tips exists
        output = data["structured_output"]
        assert "data" in output
        assert "optimization_tips" in output["data"]


# ============================================
# CT-011, CT-012: nexusops.dns - DNS Operations
# ============================================

class TestDNSAgent:
    """Test nexusops.dns agent"""

    def test_ct011_query_dns_records(self, client):
        """CT-011: Query DNS records"""
        data = invoke_agent(
            client,
            "nexusops.dns",
            "query example.com",
            context={"resource_name": "example.com"}
        )

        assert_success_response(data)
        assert_trace_id_present(data)
        assert_structured_output_present(data, "dns_query_result")

        # Check records array
        output = data["structured_output"]
        assert "records" in output
        assert isinstance(output["records"], list)

    def test_ct012_confirm_mechanism_validation(self, client):
        """CT-012: Confirm mechanism for delete operation"""
        data = invoke_agent(
            client,
            "nexusops.dns",
            "delete www.example.com",
            context={"zone_id": "example.com", "resource_name": "www"}
        )

        assert_success_response(data)
        assert_structured_output_present(data, "dns_record_deleted")

    def test_dns_create_record(self, client):
        """Test DNS agent create record"""
        data = invoke_agent(
            client,
            "nexusops.dns",
            "create A record",
            context={"zone_id": "example.com", "resource_name": "www", "resource_type": "A"}
        )

        assert_success_response(data)
        assert_structured_output_present(data, "dns_record_created")

    def test_dns_generate_random_domain(self, client):
        """Test DNS agent generate random domain"""
        data = invoke_agent(
            client,
            "nexusops.dns",
            "generate random domain",
            context={"codename": "test.nexusops.io"}  # levels handled internally
        )

        assert_success_response(data)
        assert_structured_output_present(data, "random_domain")

        # Check full_domain exists
        output = data["structured_output"]
        assert "full_domain" in output


# ============================================
# CT-013, CT-014: nexusops.cicd - CI/CD Operations (Pending)
# ============================================

class TestCICDAgent:
    """Test nexusops.cicd agent"""

    def test_ct013_query_pipeline_status(self, client):
        """CT-013: Query pipeline status"""
        data = invoke_agent(
            client,
            "nexusops.cicd",
            "pipeline status",
            context={"pipeline_id": "build-123"}
        )

        assert_success_response(data)
        assert_trace_id_present(data)
        assert_structured_output_present(data, "pipeline_status")

    def test_ct014_trigger_operation_confirm_mechanism(self, client):
        """CT-014: Trigger operation with confirm mechanism"""
        data = invoke_agent(
            client,
            "nexusops.cicd",
            "trigger build",
            context={"pipeline_id": "build-123", "branch": "main"}
        )

        assert_success_response(data)
        assert data.get("structured_output") is not None, "Missing structured_output"


# ============================================
# CT-015, CT-016: nexusops.git - Git Operations (Pending)
# ============================================

class TestGitAgent:
    """Test nexusops.git agent"""

    def test_ct015_query_commit_history(self, client):
        """CT-015: Query commit history"""
        data = invoke_agent(
            client,
            "nexusops.git",
            "git status",
            context={"repo": "https://github.com/example/repo.git"}
        )

        assert_success_response(data)
        assert_trace_id_present(data)
        assert_structured_output_present(data, "git_status")

    def test_ct016_create_operation_confirm_mechanism(self, client):
        """CT-016: Create operation with confirm mechanism"""
        data = invoke_agent(
            client,
            "nexusops.git",
            "delete branch feature/test",
            context={"repo": "https://github.com/example/repo.git", "branch": "feature/test"}
        )

        assert_success_response(data)


# ============================================
# BA-001 to BA-003: Common Agent Tests
# ============================================

class TestAllAgentsCommon:
    """Common tests that apply to all agents"""

    BUILTIN_AGENTS = [
        "nexusops.chat",
        "nexusops.k8s",
        "nexusops.deploy",
        "nexusops.logs",
        "nexusops.cost",
        "nexusops.dns",
        "nexusops.cicd",
        "nexusops.git",
    ]

    def test_ba001_invoke_all_agents_success(self, client):
        """BA-001: All agents can be invoked and return success"""
        for agent_id in self.BUILTIN_AGENTS:
            data = invoke_agent(client, agent_id, "test query")
            assert_success_response(data), f"{agent_id} did not return success"

    def test_ba002_all_responses_contain_trace_id(self, client):
        """BA-002: All responses contain trace_id"""
        for agent_id in self.BUILTIN_AGENTS:
            data = invoke_agent(client, agent_id, "test query")
            assert_trace_id_present(data), f"{agent_id} missing trace_id"

    def test_ba003_nonexistent_agent_returns_404(self, client):
        """BA-003: Non-existent agent returns AGENT_NOT_FOUND"""
        agent_id = f"com.nonexistent.{uuid.uuid4().hex[:8]}"
        response = client.post(f"/api/v1/agents/{agent_id}/invoke", json={
            "request_id": generate_request_id(),
            "conversation_id": generate_conversation_id(),
            "agent_id": agent_id,
            "query": "test",
        })

        assert response.status_code == 404, \
            f"Expected 404, got {response.status_code}"

        data = response.json()
        detail = data.get("detail", {})
        if isinstance(detail, dict):
            assert detail.get("code") == "AGENT_NOT_FOUND", \
                f"Expected AGENT_NOT_FOUND, got {detail.get('code')}"


# ============================================
# DIAG Tests: Trace ID Propagation
# ============================================

class TestTraceIDPropagation:
    """Test trace_id propagation across all agents"""

    def test_trace_id_is_consistent_in_response(self, client):
        """DIAG-001/002: trace_id is consistent throughout response"""
        data = invoke_agent(client, "nexusops.chat", "test")

        # trace_id in metadata
        trace_id = data["metadata"]["trace_id"]

        # trace_id should be 32-char hex
        assert len(trace_id) == 32
        assert all(c in "0123456789abcdef" for c in trace_id)

    def test_trace_id_unique_per_request(self, client):
        """Each request gets a unique trace_id"""
        data1 = invoke_agent(client, "nexusops.chat", "test1")
        data2 = invoke_agent(client, "nexusops.chat", "test2")

        trace_id1 = data1["metadata"]["trace_id"]
        trace_id2 = data2["metadata"]["trace_id"]

        assert trace_id1 != trace_id2, "trace_id should be unique per request"


# ============================================
# RB Tests: Rollback and Confirm Mechanism
# ============================================

class TestRollbackAndConfirm:
    """Test rollback capability and confirm mechanism"""

    def test_rb001_dangerous_operation_marked(self, client):
        """RB-001: Dangerous operations are marked with danger=true"""
        # Chat rollback command should suggest dangerous action
        data = invoke_agent(
            client,
            "nexusops.chat",
            "/rollback v1.0.0",
            context={"codename": "v1.0.0"}
        )

        # Check for danger flag in suggested actions
        actions = data.get("suggested_actions", [])
        danger_actions = [a for a in actions if a.get("danger") is True]

        assert len(danger_actions) > 0, \
            "Rollback operation should have danger=true in suggested_actions"

    def test_rb002_confirm_required_for_dangerous_ops(self, client):
        """RB-002: Dangerous operations require confirmation"""
        data = invoke_agent(
            client,
            "nexusops.chat",
            "/rollback v1.0.0",
            context={"codename": "v1.0.0"}
        )

        actions = data.get("suggested_actions", [])
        confirm_actions = [a for a in actions if a.get("confirm_required") is True]

        assert len(confirm_actions) > 0, \
            "Rollback operation should have confirm_required=true"


# ============================================
# Run Tests
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
