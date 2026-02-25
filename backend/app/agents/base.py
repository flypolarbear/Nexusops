"""
NexusOps Agents - Base Handler

MK-007: Agent 处理器基类

All built-in agents must inherit from this class.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from app.gateway.executor.base import ExecutorRequest, ExecutorResult


class BaseAgentHandler(ABC):
    """
    Base class for agent handlers.

    All built-in agents should inherit from this class and implement
    the required abstract methods.
    """

    @property
    @abstractmethod
    def agent_id(self) -> str:
        """
        Agent identifier.

        Format: nexusops.{category}
        Example: nexusops.chat, nexusops.k8s, nexusops.dns
        """
        pass

    @property
    @abstractmethod
    def capabilities(self) -> List[str]:
        """
        List of agent capabilities.

        Used for capability discovery and filtering.
        """
        pass

    @abstractmethod
    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        """
        Handle the request.

        Args:
            request: The execution request containing query and context

        Returns:
            ExecutorResult with success/failure status and content
        """
        pass

    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get tool definitions for this agent.

        Override to provide tool definitions for the agent manifest.
        """
        return []

    def get_manifest(self) -> Dict[str, Any]:
        """
        Get the agent manifest.

        Returns the full manifest for agent registration.
        """
        return {
            "agent_id": self.agent_id,
            "name": self._get_name(),
            "version": self._get_version(),
            "description": self._get_description(),
            "category": self._get_category(),
            "capabilities": self.capabilities,
            "tools": self.get_tools(),
        }

    def _get_name(self) -> str:
        """Get agent display name"""
        return self.agent_id.replace("nexusops.", "").title() + " Agent"

    def _get_version(self) -> str:
        """Get agent version"""
        return "1.0.0"

    def _get_description(self) -> str:
        """Get agent description"""
        return f"Built-in {self.agent_id} agent"

    def _get_category(self) -> str:
        """Get agent category"""
        return self.agent_id.split(".")[-1] if "." in self.agent_id else "general"

    # Helper methods for creating results

    def _success(
        self,
        text: str,
        format: str = "markdown",
        structured_output: Optional[Any] = None,
        suggested_actions: Optional[List[Dict[str, Any]]] = None,
        related_resources: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutorResult:
        """Create a success result"""
        return ExecutorResult(
            success=True,
            content={"text": text, "format": format},
            structured_output=structured_output,
            suggested_actions=suggested_actions or [],
            related_resources=related_resources or [],
            metadata=metadata or {},
        )

    def _error(
        self,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> ExecutorResult:
        """Create an error result"""
        return ExecutorResult(
            success=False,
            content={"text": message, "format": "plain"},
            error={
                "code": code,
                "message": message,
                "details": details,
            },
        )

    def _action(
        self,
        action_id: str,
        action_type: str,
        label: str,
        params: Optional[Dict[str, Any]] = None,
        confirm_required: bool = False,
        danger: bool = False,
    ) -> Dict[str, Any]:
        """Create a suggested action"""
        return {
            "id": action_id,
            "type": action_type,
            "label": label,
            "params": params or {},
            "confirm_required": confirm_required,
            "danger": danger,
        }

    def _resource(
        self,
        resource_type: str,
        resource_id: str,
        name: str,
        link: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a related resource"""
        return {
            "type": resource_type,
            "id": resource_id,
            "name": name,
            "link": link,
        }
