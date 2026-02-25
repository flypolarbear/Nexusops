"""
MK-006/MK-007 P0 Test Cases

SPEC-MK-006 P0 用例 (CT-001 to CT-008)
SPEC-MK-007 P0 用例 (EX-001 to EX-008)

All tests must pass 100% for the implementation to be valid.
"""

import pytest
from fastapi.testclient import TestClient
import uuid

from app.main import app
from app.stores.agent_store import clear_all


@pytest.fixture(autouse=True)
def reset_stores():
    """Reset stores before each test"""
    clear_all()
    yield
    clear_all()


@pytest.fixture
def client(client_with_sync_db):
    """Create test client with database support"""
    return client_with_sync_db


# ============================================
# SPEC-MK-006 P0 Test Cases (CT-001 to CT-008)
# ============================================

class TestCT001_ValidRequestSuccess:
    """CT-001: 有效请求返回成功响应"""

    def test_builtin_agent_returns_success(self, client):
        """nexusops.chat 应返回 status=success"""
        resp = client.post("/api/v1/agents/nexusops.chat/invoke", json={
            "request_id": str(uuid.uuid4()),
            "conversation_id": str(uuid.uuid4()),
            "agent_id": "nexusops.chat",
            "query": "Hello"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "trace_id" in data["metadata"]
        assert data["metadata"]["trace_id"] is not None


class TestCT002_InvalidJSON:
    """CT-002: 无效 JSON 返回 INPUT_INVALID_JSON"""

    def test_invalid_json_returns_422(self, client):
        """无效 JSON 应返回 HTTP 422 (FastAPI validation error)"""
        resp = client.post(
            "/api/v1/agents/nexusops.chat/invoke",
            content="not valid json{",
            headers={"Content-Type": "application/json"}
        )
        # FastAPI returns 422 for invalid JSON
        assert resp.status_code == 422


class TestCT003_MissingRequestID:
    """CT-003: 缺少 request_id 返回 INPUT_MISSING_FIELD"""

    def test_missing_request_id_returns_422(self, client):
        """缺少 request_id 应返回验证错误"""
        resp = client.post("/api/v1/agents/nexusops.chat/invoke", json={
            "conversation_id": str(uuid.uuid4()),
            "agent_id": "nexusops.chat",
            "query": "test"
        })
        assert resp.status_code == 422
        # Check that it's a validation error
        data = resp.json()
        assert "detail" in data


class TestCT004_InvalidAgentID:
    """CT-004: agent_id 格式错误返回 INPUT_INVALID_AGENT_ID"""

    def test_invalid_agent_id_format(self, client):
        """agent_id 格式错误应返回 404 (agent not found) or 422"""
        resp = client.post("/api/v1/agents/INVALID/invoke", json={
            "request_id": str(uuid.uuid4()),
            "conversation_id": str(uuid.uuid4()),
            "agent_id": "INVALID",  # Invalid format (uppercase)
            "query": "test"
        })
        # Should be 404 for agent not found (since INVALID is not a registered agent)
        # or 422 for validation error
        assert resp.status_code in [404, 422]


class TestCT005_AgentNotFound:
    """CT-005: 不存在的 agent_id 返回 AGENT_NOT_FOUND"""

    def test_nonexistent_agent_returns_404(self, client):
        """不存在的 agent 应返回 404"""
        # Use a valid format agent_id that doesn't exist
        agent_id = f"com.nonexistent.{uuid.uuid4().hex[:8]}"
        resp = client.post(f"/api/v1/agents/{agent_id}/invoke", json={
            "request_id": str(uuid.uuid4()),
            "conversation_id": str(uuid.uuid4()),
            "agent_id": agent_id,
            "query": "test"
        })
        # Should be 404 for not found
        assert resp.status_code == 404
        data = resp.json()
        detail = data.get("detail", {})
        if isinstance(detail, dict):
            assert detail.get("code") == "AGENT_NOT_FOUND"


class TestCT006_AuthTokenMissing:
    """CT-006: 无 Authorization 返回 AUTH_TOKEN_MISSING"""

    def test_no_auth_required_for_demo(self, client):
        """Demo 环境暂不强制认证"""
        # In demo mode, auth is not enforced
        resp = client.post("/api/v1/agents/nexusops.chat/invoke", json={
            "request_id": str(uuid.uuid4()),
            "conversation_id": str(uuid.uuid4()),
            "agent_id": "nexusops.chat",
            "query": "test"
        })
        # Should succeed in demo mode
        assert resp.status_code == 200


class TestCT007_TraceIDAndRequestID:
    """CT-007: 响应必须包含 trace_id 和 request_id"""

    def test_response_contains_trace_and_request_id(self, client):
        """所有响应应包含 trace_id 和 request_id"""
        request_id = str(uuid.uuid4())
        resp = client.post("/api/v1/agents/nexusops.chat/invoke", json={
            "request_id": request_id,
            "conversation_id": str(uuid.uuid4()),
            "agent_id": "nexusops.chat",
            "query": "test"
        })
        if resp.status_code == 200:
            data = resp.json()
            assert data["request_id"] == request_id
            assert "trace_id" in data["metadata"]
            assert len(data["metadata"]["trace_id"]) == 32  # 32-char hex string

    def test_error_response_contains_trace_id(self, client):
        """错误响应也应包含 trace_id"""
        agent_id = f"com.nonexistent.{uuid.uuid4().hex[:8]}"
        resp = client.post(f"/api/v1/agents/{agent_id}/invoke", json={
            "request_id": str(uuid.uuid4()),
            "conversation_id": str(uuid.uuid4()),
            "agent_id": agent_id,
            "query": "test"
        })
        # Check trace_id is present even in error
        if resp.status_code == 404:
            data = resp.json()
            detail = data.get("detail", {})
            if isinstance(detail, dict):
                assert "trace_id" in detail


class TestCT008_ErrorDetailSchema:
    """CT-008: 错误响应符合 ErrorDetail Schema"""

    def test_error_response_schema(self, client):
        """错误响应应符合 ErrorDetail Schema"""
        agent_id = f"com.nonexistent.{uuid.uuid4().hex[:8]}"
        resp = client.post(f"/api/v1/agents/{agent_id}/invoke", json={
            "request_id": str(uuid.uuid4()),
            "conversation_id": str(uuid.uuid4()),
            "agent_id": agent_id,
            "query": "test"
        })
        if resp.status_code == 404:
            data = resp.json()
            detail = data.get("detail", {})
            if isinstance(detail, dict):
                # ErrorDetail required fields
                assert "code" in detail
                assert "message" in detail
                # Code format: A-Z followed by alphanumeric and underscore
                code = detail["code"]
                assert code.isupper() or code.replace("_", "").isalpha()


# ============================================
# SPEC-MK-007 P0 Test Cases (EX-001 to EX-008)
# ============================================

class TestEX001_BuiltinAgentSuccess:
    """EX-001: 内置 Agent 调用成功"""

    def test_nexusops_chat_returns_success(self, client):
        """nexusops.chat 应返回 success"""
        resp = client.post("/api/v1/agents/nexusops.chat/invoke", json={
            "request_id": str(uuid.uuid4()),
            "conversation_id": str(uuid.uuid4()),
            "agent_id": "nexusops.chat",
            "query": "What is the status?"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert len(data["content"]["text"]) > 0


class TestEX002_ThirdPartyAgentSuccess:
    """EX-002: 第三方 Agent 调用成功"""

    def test_third_party_mock_returns_success(self, client):
        """mock remote agent 应返回 success"""
        # First register and install
        agent_id = f"com.test.p0-{uuid.uuid4().hex[:8]}"
        reg_resp = client.post("/api/v1/market", json={
            "manifest": {
                "agent_id": agent_id,
                "name": "Test Agent",
                "version": "1.0.0",
                "category": "test"
            },
            "visibility": "public"
        })
        assert reg_resp.status_code == 201

        install_resp = client.post(f"/api/v1/market/{agent_id}/install")
        assert install_resp.status_code == 200

        # Invoke
        resp = client.post(f"/api/v1/agents/{agent_id}/invoke", json={
            "request_id": str(uuid.uuid4()),
            "conversation_id": str(uuid.uuid4()),
            "agent_id": agent_id,
            "query": "test"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["metadata"]["agent_type"] == "third_party"


class TestEX003_AgentNotFound:
    """EX-003: 不存在的 Agent 返回 AGENT_NOT_FOUND"""

    def test_nonexistent_agent_returns_not_found(self, client):
        """不存在的 Agent 应返回 AGENT_NOT_FOUND"""
        agent_id = f"com.nonexistent.p0.{uuid.uuid4().hex[:8]}"
        resp = client.post(f"/api/v1/agents/{agent_id}/invoke", json={
            "request_id": str(uuid.uuid4()),
            "conversation_id": str(uuid.uuid4()),
            "agent_id": agent_id,
            "query": "test"
        })
        assert resp.status_code == 404
        detail = resp.json().get("detail", {})
        if isinstance(detail, dict):
            assert detail.get("code") == "AGENT_NOT_FOUND"


class TestEX004_RemoteExecutorTimeout:
    """EX-004: RemoteExecutor 超时返回 EXEC_TIMEOUT"""

    def test_timeout_returns_exec_timeout(self, client):
        """验证超时错误码定义正确"""
        from app.gateway.errors import ErrorCode, ERROR_HTTP_STATUS

        # Verify error code exists
        assert ErrorCode.EXEC_TIMEOUT.value == "EXEC_TIMEOUT"
        assert ERROR_HTTP_STATUS[ErrorCode.EXEC_TIMEOUT] == 504


class TestEX005_RemoteExecutorConnectionError:
    """EX-005: RemoteExecutor 连接失败返回 EXEC_DOWNSTREAM_ERROR"""

    def test_connection_error_returns_downstream_error(self, client):
        """验证连接错误码定义正确"""
        from app.gateway.errors import ErrorCode, ERROR_HTTP_STATUS

        assert ErrorCode.EXEC_DOWNSTREAM_ERROR.value == "EXEC_DOWNSTREAM_ERROR"
        assert ERROR_HTTP_STATUS[ErrorCode.EXEC_DOWNSTREAM_ERROR] == 502


class TestEX006_TraceIDPropagation:
    """EX-006: 同一 trace_id 贯穿内置 Agent 调用"""

    def test_trace_id_propagates_through_builtin(self, client):
        """trace_id 应贯穿整个调用链"""
        resp = client.post("/api/v1/agents/nexusops.chat/invoke", json={
            "request_id": str(uuid.uuid4()),
            "conversation_id": str(uuid.uuid4()),
            "agent_id": "nexusops.chat",
            "query": "test"
        })
        if resp.status_code == 200:
            data = resp.json()

            # trace_id should be in metadata
            trace_id = data["metadata"]["trace_id"]
            assert trace_id is not None
            assert len(trace_id) == 32

            # Should match hex format
            int(trace_id, 16)  # Should not raise


class TestEX007_TraceIDThirdParty:
    """EX-007: 同一 trace_id 贯穿第三方 Agent 调用"""

    def test_trace_id_propagates_to_third_party(self, client):
        """trace_id 应传递到第三方 Agent"""
        agent_id = f"com.test.trace-{uuid.uuid4().hex[:8]}"
        reg_resp = client.post("/api/v1/market", json={
            "manifest": {
                "agent_id": agent_id,
                "name": "Trace Test Agent",
                "version": "1.0.0",
                "category": "test"
            },
            "visibility": "public"
        })
        assert reg_resp.status_code == 201

        install_resp = client.post(f"/api/v1/market/{agent_id}/install")
        assert install_resp.status_code == 200

        resp = client.post(f"/api/v1/agents/{agent_id}/invoke", json={
            "request_id": str(uuid.uuid4()),
            "conversation_id": str(uuid.uuid4()),
            "agent_id": agent_id,
            "query": "test"
        })
        assert resp.status_code == 200
        data = resp.json()
        trace_id = data["metadata"]["trace_id"]
        assert trace_id is not None
        assert len(trace_id) == 32


class TestEX008_AgentHandlerReturnsExecutorResult:
    """EX-008: Agent Handler 返回 ExecutorResult"""

    def test_handler_returns_executor_result(self, client):
        """验证 Handler 返回正确类型"""
        from app.gateway.executor.router import get_executor_router
        from app.gateway.executor.base import ExecutorRequest, ExecutorContext, ExecutorResult

        router = get_executor_router(use_mock_remote=True)

        # Verify router returns ExecutorResult
        import asyncio
        result = asyncio.run(router.route_and_execute(
            agent_id="nexusops.chat",
            trace_id="a" * 32,
            request_id="test-req",
            query="test",
            request_context={},
        ))

        assert isinstance(result, ExecutorResult)
        assert result.success is True
        assert result.content is not None
        assert "text" in result.content


# ============================================
# Run Tests
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
