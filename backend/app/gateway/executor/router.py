"""
NexusOps Gateway - Executor Router

MK-007: Executor 路由器

Routes agent invocations to the appropriate executor.
"""

import os
from typing import Dict, Optional, Any
from datetime import datetime

from app.gateway.executor.base import (
    BaseExecutor,
    ExecutorType,
    ExecutorContext,
    ExecutorRequest,
    ExecutorResult,
)
from app.gateway.executor.builtin import BuiltinExecutor
from app.gateway.executor.remote import RemoteExecutor, MockRemoteExecutor
from app.gateway.executor.openclaw import OpenClawExecutor


class ExecutorRouter:
    """
    Executor router.

    Routes agent invocations to the appropriate executor based on agent type.
    When OPENCLAW_GATEWAY_URL is set, built-in agents are routed through
    OpenClaw. BuiltinExecutor is kept as fallback.
    """

    def __init__(self, use_mock_remote: bool = False):
        """
        Initialize the router.

        Args:
            use_mock_remote: If True, use MockRemoteExecutor for remote agents.
                           Useful for development and testing.
        """
        self._builtin = BuiltinExecutor()

        if use_mock_remote:
            self._remote: BaseExecutor = MockRemoteExecutor()
        else:
            self._remote = RemoteExecutor()

        # OpenClaw executor — active when OPENCLAW_GATEWAY_URL is set
        openclaw_url = os.getenv("OPENCLAW_GATEWAY_URL")
        self._openclaw: Optional[OpenClawExecutor] = None
        if openclaw_url:
            self._openclaw = OpenClawExecutor(gateway_url=openclaw_url)
            self._openclaw.set_fallback(self._builtin)

        # Agent registry: agent_id -> registration info
        self._agent_registry: Dict[str, dict] = {}

    async def route_and_execute(
        self,
        agent_id: str,
        trace_id: str,
        request_id: str,
        query: str,
        request_context: Optional[dict] = None,
        output_config: Optional[dict] = None,
        tools: Optional[list] = None,
        installed_agents: Optional[Dict[str, dict]] = None,
        agent_store: Optional[Dict[str, dict]] = None,
    ) -> ExecutorResult:
        """
        Route and execute an agent invocation.

        This is the main entry point for agent execution.

        Args:
            agent_id: Target agent ID
            trace_id: Trace ID for tracking
            request_id: Request ID
            query: User query
            request_context: Request context (project, version, etc.)
            output_config: Output configuration
            tools: Tool overrides
            installed_agents: Dict of installed agents from store
            agent_store: Dict of registered agents from store

        Returns:
            ExecutorResult from the agent execution
        """
        start_time = datetime.utcnow()

        # 1. Resolve agent info
        agent_info = self._resolve_agent(
            agent_id,
            installed_agents=installed_agents,
            agent_store=agent_store,
        )

        if not agent_info:
            return ExecutorResult(
                success=False,
                content={"text": f"Agent not found: {agent_id}", "format": "plain"},
                error={
                    "code": "AGENT_NOT_FOUND",
                    "message": f"Agent not found: {agent_id}",
                    "details": {"agent_id": agent_id},
                },
                metadata={
                    "trace_id": trace_id,
                    "latency_ms": self._elapsed_ms(start_time),
                },
            )

        # 2. Check install status for third-party agents
        agent_type = agent_info.get("type", "builtin")
        if agent_type == "remote":
            install_status = agent_info.get("install_status", "not_installed")
            if install_status == "not_installed":
                return ExecutorResult(
                    success=False,
                    content={"text": f"Agent '{agent_id}' is not installed", "format": "plain"},
                    error={
                        "code": "AGENT_NOT_INSTALLED",
                        "message": f"Agent '{agent_id}' is not installed. Please install it first.",
                        "details": {"agent_id": agent_id},
                    },
                    metadata={
                        "trace_id": trace_id,
                        "latency_ms": self._elapsed_ms(start_time),
                    },
                )
            elif install_status == "disabled":
                return ExecutorResult(
                    success=False,
                    content={"text": f"Agent '{agent_id}' is disabled", "format": "plain"},
                    error={
                        "code": "AGENT_DISABLED",
                        "message": f"Agent '{agent_id}' is disabled. Please enable it first.",
                        "details": {"agent_id": agent_id},
                    },
                    metadata={
                        "trace_id": trace_id,
                        "latency_ms": self._elapsed_ms(start_time),
                    },
                )

        # 3. Build execution context
        context = ExecutorContext(
            trace_id=trace_id,
            request_id=request_id,
            agent_id=agent_id,
            agent_version=agent_info.get("version", "1.0.0"),
            agent_type=ExecutorType(agent_type),
            endpoint=agent_info.get("endpoint"),
            timeout_ms=agent_info.get("timeout_ms", 30000),
            auth_context=agent_info.get("auth"),
        )

        request = ExecutorRequest(
            context=context,
            query=query,
            request_context=request_context or {},
            output_config=output_config,
            tools=tools,
        )

        # 4. Select and execute
        executor = self._select_executor(context.agent_type)

        # Pre-execute hook
        pre_result = await executor.pre_execute(request)
        if pre_result:
            return self._add_latency(pre_result, start_time)

        # Execute
        result = await executor.execute(request)

        # Post-execute hook
        result = await executor.post_execute(request, result)

        return self._add_latency(result, start_time)

    def _resolve_agent(
        self,
        agent_id: str,
        installed_agents: Optional[Dict[str, dict]] = None,
        agent_store: Optional[Dict[str, dict]] = None,
    ) -> Optional[dict]:
        """Resolve agent registration info"""

        # 1. Check built-in agents
        if self._builtin.has_agent(agent_id):
            return {
                "agent_id": agent_id,
                "type": "builtin",
                "version": "1.0.0",
            }

        # 2. Check registered third-party agents
        if agent_id in self._agent_registry:
            info = self._agent_registry[agent_id].copy()
            # Add install status if available
            if installed_agents and agent_id in installed_agents:
                info["install_status"] = installed_agents[agent_id].get("install_status", "installed")
            return info

        # 3. Check agent store (from MK-008)
        if agent_store and agent_id in agent_store:
            agent_data = agent_store[agent_id]
            info = {
                "agent_id": agent_id,
                "type": "remote",
                "version": agent_data.get("version", "1.0.0"),
                "endpoint": agent_data.get("endpoint"),
            }
            # Add install status if available
            if installed_agents and agent_id in installed_agents:
                info["install_status"] = installed_agents[agent_id].get("install_status", "installed")
            return info

        return None

    def _select_executor(self, agent_type: ExecutorType) -> BaseExecutor:
        """Select executor based on agent type.

        When OpenClaw is configured, built-in agents are routed through it.
        Falls back to BuiltinExecutor if OpenClaw is not available.
        """
        if agent_type == ExecutorType.BUILTIN:
            if self._openclaw is not None:
                return self._openclaw
            return self._builtin
        elif agent_type in (ExecutorType.REMOTE, ExecutorType.MOCK):
            return self._remote
        else:
            raise ValueError(f"Unknown executor type: {agent_type}")

    def register_agent(self, agent_id: str, info: dict):
        """Register a third-party agent"""
        self._agent_registry[agent_id] = info

    def unregister_agent(self, agent_id: str):
        """Unregister an agent"""
        self._agent_registry.pop(agent_id, None)

    def list_builtin_agents(self) -> list[str]:
        """List all built-in agents"""
        return self._builtin.list_agents()

    def list_registered_agents(self) -> list[str]:
        """List all registered third-party agents"""
        return list(self._agent_registry.keys())
    def get_all_tools(self) -> list[dict]:
        """Get tools from all available agents"""
        tools = []

        # 1. Built-in agents
        for agent_id in self._builtin.list_agents():
            # Skip chat agent itself to avoid recursion/redundancy if it had tools
            if agent_id == "nexusops.chat":
                continue

            info = self._builtin.get_agent_info(agent_id)
            if info and info.get("tools"):
                # Deep copy to avoid modifying original
                import copy
                agent_tools = copy.deepcopy(info["tools"])
                # Inject agent_id for routing
                for tool in agent_tools:
                    tool["x-nexusops-agent-id"] = agent_id
                tools.extend(agent_tools)

        # 2. Registered remote agents
        for agent_id, info in self._agent_registry.items():
            if info.get("tools"):
                import copy
                agent_tools = copy.deepcopy(info["tools"])
                # Inject agent_id for routing
                for tool in agent_tools:
                    tool["x-nexusops-agent-id"] = agent_id
                tools.extend(agent_tools)

        return tools

    def _elapsed_ms(self, start_time: datetime) -> int:
        """Calculate elapsed time in milliseconds"""
        return int((datetime.utcnow() - start_time).total_seconds() * 1000)
    def _add_latency(self, result: ExecutorResult, start_time: datetime) -> ExecutorResult:
        """Add latency to result metadata"""
        result.metadata["latency_ms"] = self._elapsed_ms(start_time)
        return result


# Singleton instance for convenience
_router_instance: Optional[ExecutorRouter] = None


def get_executor_router(use_mock_remote: bool = False) -> ExecutorRouter:
    """Get or create the executor router singleton"""
    global _router_instance
    if _router_instance is None:
        _router_instance = ExecutorRouter(use_mock_remote=use_mock_remote)
    return _router_instance


def reset_executor_router():
    """Reset the executor router singleton (for testing)"""
    global _router_instance
    _router_instance = None
