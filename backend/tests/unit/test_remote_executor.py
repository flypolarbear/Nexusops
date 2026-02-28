"""
Unit tests for app/gateway/executor/remote.py
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.gateway.executor.remote import RemoteExecutor, MockRemoteExecutor
from app.gateway.executor.base import ExecutorRequest, ExecutorContext, ExecutorType


@pytest.fixture
def executor():
    return RemoteExecutor()


@pytest.fixture
def mock_context():
    return ExecutorContext(
        trace_id="test-trace-12345678901234567890",
        request_id="test-request-001",
        agent_id="third-party.agent",
        endpoint="https://api.example.com/agent",
        timeout_ms=30000,
    )


@pytest.fixture
def make_request(mock_context):
    def _make(query: str, request_context: dict = None, endpoint: str = None):
        ctx = mock_context
        if endpoint:
            ctx = ExecutorContext(
                trace_id=mock_context.trace_id,
                request_id=mock_context.request_id,
                agent_id=mock_context.agent_id,
                endpoint=endpoint,
                timeout_ms=mock_context.timeout_ms,
            )
        return ExecutorRequest(
            context=ctx,
            query=query,
            request_context=request_context or {},
        )
    return _make


class TestRemoteExecutorBasics:
    def test_executor_type(self, executor):
        assert executor.executor_type == ExecutorType.REMOTE

    def test_init_without_client(self):
        exec_ = RemoteExecutor()
        assert exec_._client is None
        assert exec_._owned_client is True

    def test_init_with_client(self):
        client = httpx.AsyncClient()
        exec_ = RemoteExecutor(http_client=client)
        assert exec_._client is client
        assert exec_._owned_client is False


    @pytest.mark.asyncio
    async def test_execute_missing_endpoint(self, executor):
        ctx = ExecutorContext(
            trace_id="test-trace-12345678901234567890",
            request_id="test-request-001",
            agent_id="test.agent",
        )
        request = ExecutorRequest(context=ctx, query="test query")
        result = await executor.execute(request)
        
        assert result.success is False
        assert result.error["code"] == "AGENT_ENDPOINT_MISSING"

    @pytest.mark.asyncio
    async def test_execute_success(self, executor, make_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "content": {"text": "Hello", "format": "markdown"},
            "structured_output": {"type": "test"},
        }
        
        with patch.object(executor, "_ensure_client") as mock_ensure:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_ensure.return_value = mock_client
            
            request = make_request("test query")
            result = await executor.execute(request)
            
            assert result.success is True
            assert result.content["text"] == "Hello"

    @pytest.mark.asyncio
    async def test_execute_with_auth(self, executor, mock_context):
        auth_context = {"api_key": "test-api-key"}
        ctx = ExecutorContext(
            trace_id=mock_context.trace_id,
            request_id=mock_context.request_id,
            agent_id=mock_context.agent_id,
            endpoint="https://api.example.com/agent",
            timeout_ms=30000,
            auth_context=auth_context,
        )
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "content": {"text": "OK", "format": "plain"},
        }
        
        with patch.object(executor, "_ensure_client") as mock_ensure:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_ensure.return_value = mock_client
            
            request = ExecutorRequest(context=ctx, query="test")
            await executor.execute(request)
            
            call_kwargs = mock_client.post.call_args
            headers = call_kwargs.kwargs["headers"]
            assert headers["Authorization"] == "Bearer test-api-key"

    @pytest.mark.asyncio
    async def test_execute_timeout(self, executor, make_request):
        with patch.object(executor, "_ensure_client") as mock_ensure:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
            mock_ensure.return_value = mock_client
            
            request = make_request("test query")
            result = await executor.execute(request)
            
            assert result.success is False
            assert result.error["code"] == "EXEC_TIMEOUT"
            assert result.error.get("retry_after") == 5

    @pytest.mark.asyncio
    async def test_execute_connection_error(self, executor, make_request):
        with patch.object(executor, "_ensure_client") as mock_ensure:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=httpx.RequestError("connection failed"))
            mock_ensure.return_value = mock_client
            
            request = make_request("test query")
            result = await executor.execute(request)
            
            assert result.success is False
            assert result.error["code"] == "EXEC_DOWNSTREAM_ERROR"

    @pytest.mark.asyncio
    async def test_execute_unexpected_error(self, executor, make_request):
        with patch.object(executor, "_ensure_client") as mock_ensure:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=RuntimeError("unexpected"))
            mock_ensure.return_value = mock_client
            
            request = make_request("test query")
            result = await executor.execute(request)
            
            assert result.success is False
            assert result.error["code"] == "EXEC_INTERNAL_ERROR"


class TestRemoteExecutorErrorResponse:
    def test_handle_error_response_with_json(self, executor, mock_context):
        response = MagicMock()
        response.status_code = 400
        response.json.return_value = {
            "error": {"code": "BAD_REQUEST", "message": "Invalid input"}
        }
        
        request = ExecutorRequest(context=mock_context, query="test")
        result = executor._handle_error_response(response, request)
        
        assert result.success is False
        assert result.error["code"] == "BAD_REQUEST"

    def test_handle_error_response_without_json(self, executor, mock_context):
        response = MagicMock()
        response.status_code = 500
        response.json.side_effect = Exception("not json")
        response.text = "Internal Server Error"
        
        request = ExecutorRequest(context=mock_context, query="test")
        result = executor._handle_error_response(response, request)
        
        assert result.success is False
        assert result.error["code"] == "HTTP_500"


class TestRemoteExecutorParseResponse:
    def test_parse_response_missing_content(self, executor, mock_context):
        data = {"status": "success"}
        request = ExecutorRequest(context=mock_context, query="test")
        
        result = executor._parse_response(data, request)
        
        assert result.success is False
        assert result.error["code"] == "AGENT_OUTPUT_INVALID"

    def test_parse_response_success(self, executor, mock_context):
        data = {
            "status": "success",
            "content": {"text": "Result", "format": "markdown"},
            "structured_output": {"type": "test"},
            "suggested_actions": [{"label": "Action"}],
        }
        request = ExecutorRequest(context=mock_context, query="test")
        
        result = executor._parse_response(data, request)
        
        assert result.success is True
        assert result.structured_output == {"type": "test"}
        assert len(result.suggested_actions) == 1

    def test_parse_response_error_status(self, executor, mock_context):
        data = {
            "status": "error",
            "content": {"text": "", "format": "plain"},
            "error": {"code": "ERR", "message": "Failed"},
        }
        request = ExecutorRequest(context=mock_context, query="test")
        
        result = executor._parse_response(data, request)
        
        assert result.success is False
        assert result.error is not None


class TestRemoteExecutorLifecycle:
    @pytest.mark.asyncio
    async def test_health_check(self, executor):
        result = await executor.health_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_close_owned_client(self):
        executor = RemoteExecutor()
        await executor._ensure_client()
        await executor.close()
        
        assert executor._client is None

    @pytest.mark.asyncio
    async def test_close_external_client(self):
        external_client = httpx.AsyncClient()
        executor = RemoteExecutor(http_client=external_client)
        await executor.close()
        
        assert executor._client == external_client


class TestMockRemoteExecutor:
    def test_executor_type(self):
        executor = MockRemoteExecutor()
        assert executor.executor_type == ExecutorType.MOCK

    @pytest.mark.asyncio
    async def test_execute_returns_mock_response(self, mock_context):
        executor = MockRemoteExecutor()
        request = ExecutorRequest(context=mock_context, query="test query")
        
        result = await executor.execute(request)
        
        assert result.success is True
        assert "third_party_response" in result.structured_output["type"]
        assert result.metadata["execution_mode"] == "mock"

    @pytest.mark.asyncio
    async def test_health_check(self):
        executor = MockRemoteExecutor()
        result = await executor.health_check()
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
