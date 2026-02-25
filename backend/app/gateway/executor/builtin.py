"""
NexusOps Gateway - Builtin Executor

MK-007: 内置 Agent 执行器

Executes built-in agents within the same process.
"""

from typing import Callable, Dict, Optional, Any
import asyncio

from app.gateway.executor.base import (
    BaseExecutor,
    ExecutorType,
    ExecutorRequest,
    ExecutorResult,
)


class BaseAgentHandler:
    """
    Base class for agent handlers.

    All built-in agents should inherit from this class.
    """

    @property
    def agent_id(self) -> str:
        """Agent identifier"""
        raise NotImplementedError

    @property
    def capabilities(self) -> list[str]:
        """List of agent capabilities"""
        return []

    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        """Handle the request"""
        raise NotImplementedError

    def get_tools(self) -> list[dict]:
        """Get tool definitions"""
        return []


class BuiltinExecutor(BaseExecutor):
    """
    Built-in agent executor.

    Executes agents registered within the same process.
    """

    def __init__(self):
        self._handlers: Dict[str, BaseAgentHandler] = {}
        self._register_builtin_handlers()

    @property
    def executor_type(self) -> ExecutorType:
        return ExecutorType.BUILTIN

    def _register_builtin_handlers(self):
        """Register all built-in agent handlers"""
        try:
            from app.agents import (
                ChatAgentHandler,
                K8sAgentHandler,
                DeployAgentHandler,
                DNSAgentHandler,
                LogsAgentHandler,
                CostAgentHandler,
                CICDAgentHandler,
                GitAgentHandler,
            )

            handlers = [
                ChatAgentHandler(),
                K8sAgentHandler(),
                DeployAgentHandler(),
                DNSAgentHandler(),
                LogsAgentHandler(),
                CostAgentHandler(),
                CICDAgentHandler(),
                GitAgentHandler(),
            ]

            for handler in handlers:
                self._handlers[handler.agent_id] = handler

        except ImportError:
            # Fall back to mock handlers if agents module not available
            self._register_mock_handlers()

    def _register_mock_handlers(self):
        """Register mock handlers for development"""
        self._handlers = {
            "nexusops.chat": MockChatHandler(),
            "nexusops.k8s": MockK8sHandler(),
            "nexusops.deploy": MockDeployHandler(),
            "nexusops.dns": MockDNSHandler(),
            "nexusops.logs": MockLogsHandler(),
            "nexusops.cost": MockCostHandler(),
            "nexusops.cicd": MockCICDHandler(),
            "nexusops.git": MockGitHandler(),
        }

    def register_handler(self, agent_id: str, handler: BaseAgentHandler):
        """Dynamically register a handler"""
        self._handlers[agent_id] = handler

    def unregister_handler(self, agent_id: str):
        """Unregister a handler"""
        self._handlers.pop(agent_id, None)

    async def execute(self, request: ExecutorRequest) -> ExecutorResult:
        """Execute a built-in agent"""
        agent_id = request.context.agent_id

        if agent_id not in self._handlers:
            return self._make_error_result(
                code="AGENT_NOT_FOUND",
                message=f"Built-in agent not found: {agent_id}",
                details={"agent_id": agent_id, "type": "builtin"},
            )

        handler = self._handlers[agent_id]

        try:
            result = await handler.handle(request)
            return result

        except Exception as e:
            return self._make_error_result(
                code="EXEC_INTERNAL_ERROR",
                message=str(e),
                details={
                    "agent_id": agent_id,
                    "exception": type(e).__name__,
                },
            )

    async def health_check(self) -> bool:
        """Check executor health"""
        return True

    def list_agents(self) -> list[str]:
        """List all registered built-in agents"""
        return list(self._handlers.keys())

    def has_agent(self, agent_id: str) -> bool:
        """Check if agent is registered"""
        return agent_id in self._handlers

    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent information"""
        if agent_id not in self._handlers:
            return None

        handler = self._handlers[agent_id]
        return {
            "agent_id": handler.agent_id,
            "capabilities": handler.capabilities,
            "tools": handler.get_tools(),
            "type": "builtin",
        }


# Mock handlers for development

class MockChatHandler(BaseAgentHandler):
    """Mock chat agent handler"""

    @property
    def agent_id(self) -> str:
        return "nexusops.chat"

    @property
    def capabilities(self) -> list[str]:
        return ["chat", "quick_commands", "deployment_info", "status_query"]

    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        await asyncio.sleep(0.3)  # Simulate processing

        query = request.query.lower()

        if query.startswith("/deploy"):
            return ExecutorResult(
                success=True,
                content={
                    "text": f"## 🚀 Deployment Triggered\n\n**Version:** {request.request_context.get('codename', 'unknown')}\n\nDeployment has been initiated.",
                    "format": "markdown",
                },
                structured_output={
                    "type": "deployment_status",
                    "status": "triggered",
                },
                metadata={"operation": "deploy"},
            )

        return ExecutorResult(
            success=True,
            content={
                "text": f"I received your message: {request.query}",
                "format": "markdown",
            },
            metadata={"operation": "chat"},
        )

    def get_tools(self) -> list[dict]:
        return [
            {
                "name": "get_deployment_status",
                "description": "Get deployment status for a version",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "codename": {"type": "string"},
                        "region": {"type": "string"},
                    },
                },
            },
        ]


class MockK8sHandler(BaseAgentHandler):
    """Mock K8s agent handler"""

    @property
    def agent_id(self) -> str:
        return "nexusops.k8s"

    @property
    def capabilities(self) -> list[str]:
        return ["k8s_deploy", "k8s_scale", "k8s_logs", "k8s_describe"]

    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        await asyncio.sleep(0.3)

        return ExecutorResult(
            success=True,
            content={
                "text": f"## K8s Resource Analysis\n\nAnalyzing resource in namespace **{request.request_context.get('namespace', 'default')}**\n\nStatus: Running\nHealth: Healthy",
                "format": "markdown",
            },
            metadata={"operation": "k8s_query"},
        )


class MockDeployHandler(BaseAgentHandler):
    """Mock deploy agent handler"""

    @property
    def agent_id(self) -> str:
        return "nexusops.deploy"

    @property
    def capabilities(self) -> list[str]:
        return ["deploy_create", "deploy_rollback", "deploy_status", "deploy_force_sync"]

    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        await asyncio.sleep(0.3)

        return ExecutorResult(
            success=True,
            content={
                "text": f"## Deployment Orchestration\n\nProcessing deployment request for **{request.request_context.get('codename', 'unknown')}**\n\n✅ CI/CD Build - Completed\n✅ ArgoCD Sync - Completed\n✅ Health Check - Passed",
                "format": "markdown",
            },
            metadata={"operation": "deploy"},
        )


class MockDNSHandler(BaseAgentHandler):
    """Mock DNS agent handler"""

    @property
    def agent_id(self) -> str:
        return "nexusops.dns"

    @property
    def capabilities(self) -> list[str]:
        return ["dns_record_create", "dns_record_delete", "dns_record_query", "random_domain_generate"]

    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        await asyncio.sleep(0.3)

        return ExecutorResult(
            success=True,
            content={
                "text": f"## DNS Operations\n\nDNS operation completed successfully.",
                "format": "markdown",
            },
            metadata={"operation": "dns"},
        )


class MockLogsHandler(BaseAgentHandler):
    """Mock logs agent handler"""

    @property
    def agent_id(self) -> str:
        return "nexusops.logs"

    @property
    def capabilities(self) -> list[str]:
        return ["query_logs", "search_errors", "tail_logs", "filter_by_level", "filter_by_service"]

    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        await asyncio.sleep(0.3)

        return ExecutorResult(
            success=True,
            content={
                "text": "## Log Query Results\n\nFound **25** log entries.",
                "format": "markdown",
            },
            metadata={"operation": "logs_query"},
        )


class MockCostHandler(BaseAgentHandler):
    """Mock cost agent handler"""

    @property
    def agent_id(self) -> str:
        return "nexusops.cost"

    @property
    def capabilities(self) -> list[str]:
        return ["cost_query", "cost_by_service", "cost_by_region", "cost_trend_analysis", "budget_comparison"]

    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        await asyncio.sleep(0.3)

        return ExecutorResult(
            success=True,
            content={
                "text": "## Cost Overview\n\n**Total Cost:** $12,500.00\n**Budget:** $15,000.00",
                "format": "markdown",
            },
            metadata={"operation": "cost_query"},
        )


class MockCICDHandler(BaseAgentHandler):
    """Mock CI/CD agent handler"""

    @property
    def agent_id(self) -> str:
        return "nexusops.cicd"

    @property
    def capabilities(self) -> list[str]:
        return ["pipeline_trigger", "pipeline_status", "pipeline_cancel", "build_logs", "pipeline_list", "jenkins_trigger", "argocd_sync"]

    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        await asyncio.sleep(0.3)

        return ExecutorResult(
            success=True,
            content={
                "text": "## CI/CD Pipeline\n\nPipeline triggered successfully.",
                "format": "markdown",
            },
            metadata={"operation": "cicd"},
        )


class MockGitHandler(BaseAgentHandler):
    """Mock git agent handler"""

    @property
    def agent_id(self) -> str:
        return "nexusops.git"

    @property
    def capabilities(self) -> list[str]:
        return ["git_status", "git_branch", "git_tag", "git_pr", "git_diff", "git_commit", "create_branch", "delete_branch", "create_pull_request"]

    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        await asyncio.sleep(0.3)

        return ExecutorResult(
            success=True,
            content={
                "text": "## Git Operations\n\nRepository status retrieved successfully.",
                "format": "markdown",
            },
            metadata={"operation": "git"},
        )
