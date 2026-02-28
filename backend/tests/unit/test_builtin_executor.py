"""
Unit tests for app/gateway/executor/builtin.py
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.gateway.executor.builtin import (
    BaseAgentHandler,
    BuiltinExecutor,
    MockChatHandler,
    MockK8sHandler,
    MockDeployHandler,
    MockDNSHandler,
    MockLogsHandler,
    MockCostHandler,
    MockCICDHandler,
    MockGitHandler,
)
from app.gateway.executor.base import ExecutorRequest, ExecutorContext, ExecutorType


@pytest.fixture
def executor():
    return BuiltinExecutor()


@pytest.fixture
def mock_context():
    return ExecutorContext(
        trace_id="test-trace-12345678901234567890",
        request_id="test-request-001",
        agent_id="nexusops.chat",
    )


@pytest.fixture
def make_request(mock_context):
    def _make(query: str, agent_id: str = None):
        ctx = mock_context
        if agent_id:
            ctx = ExecutorContext(
                trace_id=mock_context.trace_id,
                request_id=mock_context.request_id,
                agent_id=agent_id,
            )
        return ExecutorRequest(context=ctx, query=query, request_context={})
    return _make


class TestBaseAgentHandler:
    def test_agent_id_not_implemented(self):
        handler = BaseAgentHandler()
        with pytest.raises(NotImplementedError):
            _ = handler.agent_id

    def test_capabilities_default_empty(self):
        class TestHandler(BaseAgentHandler):
            @property
            def agent_id(self):
                return "test.agent"
        
        handler = TestHandler()
        assert handler.capabilities == []

    def test_handle_not_implemented(self):
        class TestHandler(BaseAgentHandler):
            @property
            def agent_id(self):
                return "test.agent"
        
        handler = TestHandler()
        with pytest.raises(NotImplementedError):
            import asyncio
            asyncio.run(handler.handle(None))

    def test_get_tools_default_empty(self):
        class TestHandler(BaseAgentHandler):
            @property
            def agent_id(self):
                return "test.agent"
        
        handler = TestHandler()
        assert handler.get_tools() == []


class TestBuiltinExecutorBasics:
    def test_executor_type(self, executor):
        assert executor.executor_type == ExecutorType.BUILTIN

    def test_list_agents(self, executor):
        agents = executor.list_agents()
        assert len(agents) >= 8
        assert "nexusops.chat" in agents
        assert "nexusops.k8s" in agents

    def test_has_agent_true(self, executor):
        assert executor.has_agent("nexusops.chat") is True

    def test_has_agent_false(self, executor):
        assert executor.has_agent("nonexistent.agent") is False

    def test_get_agent_info(self, executor):
        info = executor.get_agent_info("nexusops.chat")
        assert info is not None
        assert info["agent_id"] == "nexusops.chat"
        assert info["type"] == "builtin"
        assert "capabilities" in info
        assert "tools" in info

    def test_get_agent_info_not_found(self, executor):
        info = executor.get_agent_info("nonexistent.agent")
        assert info is None


class TestBuiltinExecutorRegistration:
    def test_register_handler(self, executor):
        class CustomHandler(BaseAgentHandler):
            @property
            def agent_id(self):
                return "custom.agent"
            
            async def handle(self, request):
                pass
        
        handler = CustomHandler()
        executor.register_handler("custom.agent", handler)
        
        assert executor.has_agent("custom.agent") is True
        assert "custom.agent" in executor.list_agents()

    def test_unregister_handler(self, executor):
        executor.unregister_handler("nexusops.chat")
        
        assert executor.has_agent("nexusops.chat") is False

    def test_unregister_nonexistent_handler(self, executor):
        executor.unregister_handler("nonexistent.agent")


class TestBuiltinExecutorExecute:
    @pytest.mark.asyncio
    async def test_execute_agent_not_found(self, executor, make_request):
        request = make_request("test query", agent_id="nonexistent.agent")
        result = await executor.execute(request)
        
        assert result.success is False
        assert result.error["code"] == "AGENT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_execute_success(self, executor, make_request):
        request = make_request("hello", agent_id="nexusops.chat")
        result = await executor.execute(request)
        
        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_handler_exception(self, executor, make_request):
        class FailingHandler(BaseAgentHandler):
            @property
            def agent_id(self):
                return "failing.agent"
            
            async def handle(self, request):
                raise RuntimeError("Handler failed")
        
        executor.register_handler("failing.agent", FailingHandler())
        request = make_request("test", agent_id="failing.agent")
        result = await executor.execute(request)
        
        assert result.success is False
        assert result.error["code"] == "EXEC_INTERNAL_ERROR"
        assert "RuntimeError" in result.error["details"]["exception"]


class TestBuiltinExecutorHealth:
    @pytest.mark.asyncio
    async def test_health_check(self, executor):
        result = await executor.health_check()
        assert result is True


class TestMockChatHandler:
    def test_agent_id(self):
        handler = MockChatHandler()
        assert handler.agent_id == "nexusops.chat"

    def test_capabilities(self):
        handler = MockChatHandler()
        assert "chat" in handler.capabilities
        assert "quick_commands" in handler.capabilities

    @pytest.mark.asyncio
    async def test_handle_chat(self, mock_context):
        handler = MockChatHandler()
        request = ExecutorRequest(context=mock_context, query="hello world")
        
        result = await handler.handle(request)
        
        assert result.success is True
        assert "hello world" in result.content["text"]

    @pytest.mark.asyncio
    async def test_handle_deploy_command(self, mock_context):
        handler = MockChatHandler()
        request = ExecutorRequest(
            context=mock_context,
            query="/deploy phoenix",
            request_context={"codename": "phoenix"}
        )
        
        result = await handler.handle(request)
        
        assert result.success is True
        assert result.structured_output["type"] == "deployment_status"

    def test_get_tools(self):
        handler = MockChatHandler()
        tools = handler.get_tools()
        assert len(tools) >= 1
        assert tools[0]["name"] == "get_deployment_status"


class TestMockK8sHandler:
    def test_agent_id(self):
        handler = MockK8sHandler()
        assert handler.agent_id == "nexusops.k8s"

    def test_capabilities(self):
        handler = MockK8sHandler()
        assert "k8s_deploy" in handler.capabilities

    @pytest.mark.asyncio
    async def test_handle(self, mock_context):
        handler = MockK8sHandler()
        request = ExecutorRequest(context=mock_context, query="get pods")
        
        result = await handler.handle(request)
        
        assert result.success is True
        assert "K8s Resource" in result.content["text"]


class TestMockDeployHandler:
    def test_agent_id(self):
        handler = MockDeployHandler()
        assert handler.agent_id == "nexusops.deploy"

    def test_capabilities(self):
        handler = MockDeployHandler()
        assert "deploy_create" in handler.capabilities
        assert "deploy_rollback" in handler.capabilities

    @pytest.mark.asyncio
    async def test_handle(self, mock_context):
        handler = MockDeployHandler()
        request = ExecutorRequest(
            context=mock_context,
            query="deploy",
            request_context={"codename": "phoenix"}
        )
        
        result = await handler.handle(request)
        
        assert result.success is True


class TestMockDNSHandler:
    def test_agent_id(self):
        handler = MockDNSHandler()
        assert handler.agent_id == "nexusops.dns"

    @pytest.mark.asyncio
    async def test_handle(self, mock_context):
        handler = MockDNSHandler()
        request = ExecutorRequest(context=mock_context, query="query dns")
        
        result = await handler.handle(request)
        
        assert result.success is True


class TestMockLogsHandler:
    def test_agent_id(self):
        handler = MockLogsHandler()
        assert handler.agent_id == "nexusops.logs"

    @pytest.mark.asyncio
    async def test_handle(self, mock_context):
        handler = MockLogsHandler()
        request = ExecutorRequest(context=mock_context, query="show logs")
        
        result = await handler.handle(request)
        
        assert result.success is True
        assert "Log Query" in result.content["text"]


class TestMockCostHandler:
    def test_agent_id(self):
        handler = MockCostHandler()
        assert handler.agent_id == "nexusops.cost"

    @pytest.mark.asyncio
    async def test_handle(self, mock_context):
        handler = MockCostHandler()
        request = ExecutorRequest(context=mock_context, query="show costs")
        
        result = await handler.handle(request)
        
        assert result.success is True
        assert "Cost" in result.content["text"]


class TestMockCICDHandler:
    def test_agent_id(self):
        handler = MockCICDHandler()
        assert handler.agent_id == "nexusops.cicd"

    @pytest.mark.asyncio
    async def test_handle(self, mock_context):
        handler = MockCICDHandler()
        request = ExecutorRequest(context=mock_context, query="list pipelines")
        
        result = await handler.handle(request)
        
        assert result.success is True


class TestMockGitHandler:
    def test_agent_id(self):
        handler = MockGitHandler()
        assert handler.agent_id == "nexusops.git"

    @pytest.mark.asyncio
    async def test_handle(self, mock_context):
        handler = MockGitHandler()
        request = ExecutorRequest(context=mock_context, query="git status")
        
        result = await handler.handle(request)
        
        assert result.success is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
