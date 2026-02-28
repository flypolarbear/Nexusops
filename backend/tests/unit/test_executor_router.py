"""
Unit tests for app/gateway/executor/router.py
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.gateway.executor.router import (
    ExecutorRouter,
    get_executor_router,
    reset_executor_router,
)
from app.gateway.executor.base import ExecutorType


@pytest.fixture(autouse=True)
def reset_singleton():
    reset_executor_router()
    yield
    reset_executor_router()


@pytest.fixture
def router():
    return ExecutorRouter(use_mock_remote=True)


class TestExecutorRouterInit:
    def test_init_with_mock_remote(self):
        router = ExecutorRouter(use_mock_remote=True)
        assert router._builtin is not None
        assert router._remote is not None

    def test_init_with_real_remote(self):
        router = ExecutorRouter(use_mock_remote=False)
        assert router._builtin is not None
        assert router._remote is not None


class TestExecutorRouterAgentManagement:
    def test_list_builtin_agents(self, router):
        agents = router.list_builtin_agents()
        assert len(agents) >= 8
        assert "nexusops.chat" in agents

    def test_register_agent(self, router):
        router.register_agent("third.party.agent", {
            "type": "remote",
            "endpoint": "https://api.example.com",
        })
        
        assert "third.party.agent" in router.list_registered_agents()

    def test_unregister_agent(self, router):
        router.register_agent("test.agent", {"type": "remote"})
        router.unregister_agent("test.agent")
        
        assert "test.agent" not in router.list_registered_agents()

    def test_list_registered_agents(self, router):
        router.register_agent("agent1", {"type": "remote"})
        router.register_agent("agent2", {"type": "remote"})
        
        agents = router.list_registered_agents()
        assert "agent1" in agents
        assert "agent2" in agents


class TestExecutorRouterRouteAndExecute:
    @pytest.mark.asyncio
    async def test_route_builtin_agent(self, router):
        result = await router.route_and_execute(
            agent_id="nexusops.chat",
            trace_id="test-trace-12345678901234567890",
            request_id="test-request-001",
            query="hello",
        )
        
        assert result.success is True

    @pytest.mark.asyncio
    async def test_route_agent_not_found(self, router):
        result = await router.route_and_execute(
            agent_id="nonexistent.agent",
            trace_id="test-trace-12345678901234567890",
            request_id="test-request-001",
            query="hello",
        )
        
        assert result.success is False
        assert result.error["code"] == "AGENT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_route_remote_agent_not_installed(self, router):
        router.register_agent("third.party.agent", {
            "type": "remote",
            "endpoint": "https://api.example.com",
        })
        
        result = await router.route_and_execute(
            agent_id="third.party.agent",
            trace_id="test-trace-12345678901234567890",
            request_id="test-request-001",
            query="hello",
            installed_agents={"third.party.agent": {"install_status": "not_installed"}},
        )
        
        assert result.success is False
        assert result.error["code"] == "AGENT_NOT_INSTALLED"

    @pytest.mark.asyncio
    async def test_route_remote_agent_disabled(self, router):
        router.register_agent("third.party.agent", {
            "type": "remote",
            "endpoint": "https://api.example.com",
        })
        
        result = await router.route_and_execute(
            agent_id="third.party.agent",
            trace_id="test-trace-12345678901234567890",
            request_id="test-request-001",
            query="hello",
            installed_agents={"third.party.agent": {"install_status": "disabled"}},
        )
        
        assert result.success is False
        assert result.error["code"] == "AGENT_DISABLED"

    @pytest.mark.asyncio
    async def test_route_with_agent_store(self, router):
        agent_store = {
            "store.agent": {
                "version": "2.0.0",
                "endpoint": "https://store.example.com",
            }
        }
        
        result = await router.route_and_execute(
            agent_id="store.agent",
            trace_id="test-trace-12345678901234567890",
            request_id="test-request-001",
            query="test",
            agent_store=agent_store,
            installed_agents={"store.agent": {"install_status": "installed"}},
        )
        
        assert result.metadata.get("latency_ms") is not None

    @pytest.mark.asyncio
    async def test_route_includes_latency(self, router):
        result = await router.route_and_execute(
            agent_id="nexusops.chat",
            trace_id="test-trace-12345678901234567890",
            request_id="test-request-001",
            query="test",
        )
        
        assert "latency_ms" in result.metadata


class TestExecutorRouterResolveAgent:
    def test_resolve_builtin_agent(self, router):
        info = router._resolve_agent("nexusops.chat")
        
        assert info is not None
        assert info["type"] == "builtin"

    def test_resolve_registered_agent(self, router):
        router.register_agent("registered.agent", {
            "type": "remote",
            "endpoint": "https://api.example.com",
        })
        
        info = router._resolve_agent("registered.agent")
        
        assert info is not None
        assert info["type"] == "remote"
        assert info["endpoint"] == "https://api.example.com"

    def test_resolve_agent_from_store(self, router):
        agent_store = {
            "store.agent": {
                "version": "1.5.0",
                "endpoint": "https://store.example.com",
            }
        }
        
        info = router._resolve_agent("store.agent", agent_store=agent_store)
        
        assert info is not None
        assert info["type"] == "remote"
        assert info["version"] == "1.5.0"

    def test_resolve_agent_with_install_status(self, router):
        router.register_agent("test.agent", {"type": "remote"})
        
        info = router._resolve_agent(
            "test.agent",
            installed_agents={"test.agent": {"install_status": "installed"}}
        )
        
        assert info["install_status"] == "installed"

    def test_resolve_agent_not_found(self, router):
        info = router._resolve_agent("nonexistent.agent")
        assert info is None


class TestExecutorRouterSelectExecutor:
    def test_select_builtin_executor(self, router):
        from app.gateway.executor.builtin import BuiltinExecutor
        executor = router._select_executor(ExecutorType.BUILTIN)
        assert isinstance(executor, BuiltinExecutor)

    def test_select_remote_executor(self, router):
        from app.gateway.executor.remote import RemoteExecutor, MockRemoteExecutor
        executor = router._select_executor(ExecutorType.REMOTE)
        assert isinstance(executor, (RemoteExecutor, MockRemoteExecutor))

    def test_select_mock_executor(self, router):
        from app.gateway.executor.remote import MockRemoteExecutor
        executor = router._select_executor(ExecutorType.MOCK)
        assert isinstance(executor, MockRemoteExecutor)


class TestExecutorRouterSingleton:
    def test_get_executor_router_creates_instance(self):
        router = get_executor_router()
        assert router is not None
        assert isinstance(router, ExecutorRouter)

    def test_get_executor_router_returns_same_instance(self):
        router1 = get_executor_router()
        router2 = get_executor_router()
        assert router1 is router2

    def test_reset_executor_router(self):
        router1 = get_executor_router()
        reset_executor_router()
        router2 = get_executor_router()
        assert router1 is not router2


class TestExecutorRouterHelpers:
    def test_elapsed_ms(self, router):
        from datetime import datetime, timedelta
        
        start = datetime.utcnow() - timedelta(milliseconds=100)
        elapsed = router._elapsed_ms(start)
        
        assert elapsed >= 90
        assert elapsed < 200

    def test_add_latency(self, router):
        from app.gateway.executor.base import ExecutorResult
        from datetime import datetime, timedelta
        
        result = ExecutorResult(
            success=True,
            content={"text": "test", "format": "plain"},
            metadata={},
        )
        
        start = datetime.utcnow() - timedelta(milliseconds=50)
        updated = router._add_latency(result, start)
        
        assert "latency_ms" in updated.metadata
        assert updated.metadata["latency_ms"] >= 40


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
