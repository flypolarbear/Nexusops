"""
NexusOps SDK - Agent Registration Utilities

Utilities for registering agents with NexusOps Gateway.
"""

from typing import Any, Callable, Dict, List, Optional, Type

from .agent import AgentBase
from ..models import AgentRequest, AgentResponse


class AgentRegistrationBuilder:
    """
    Builder for creating agent registration manifests.

    Usage:
        manifest = (AgentRegistrationBuilder("mycompany.myagent")
            .with_name("My Agent")
            .with_version("1.0.0")
            .with_description("A helpful agent")
            .with_category("general")
            .with_capabilities(["chat", "analyze"])
            .with_tool("get_status", "Get current status", {...})
            .build())
    """

    def __init__(self, agent_id: str):
        """
        Initialize the builder.

        Args:
            agent_id: Unique identifier for the agent
        """
        self._agent_id = agent_id
        self._name: str = agent_id
        self._version: str = "1.0.0"
        self._description: Optional[str] = None
        self._author: Optional[str] = None
        self._category: str = "general"
        self._tags: List[str] = []
        self._capabilities: List[str] = []
        self._tools: List[Dict[str, Any]] = []
        self._input_schema: Optional[Dict[str, Any]] = None
        self._output_schema: Optional[Dict[str, Any]] = None
        self._endpoints: Optional[Dict[str, Any]] = None
        self._auth: Optional[Dict[str, Any]] = None
        self._pricing: Optional[Dict[str, Any]] = None
        self._metadata: Optional[Dict[str, Any]] = None

    def with_name(self, name: str) -> "AgentRegistrationBuilder":
        """Set the agent name."""
        self._name = name
        return self

    def with_version(self, version: str) -> "AgentRegistrationBuilder":
        """Set the agent version."""
        self._version = version
        return self

    def with_description(self, description: str) -> "AgentRegistrationBuilder":
        """Set the agent description."""
        self._description = description
        return self

    def with_author(self, author: str) -> "AgentRegistrationBuilder":
        """Set the agent author."""
        self._author = author
        return self

    def with_category(self, category: str) -> "AgentRegistrationBuilder":
        """Set the agent category."""
        self._category = category
        return self

    def with_tags(self, tags: List[str]) -> "AgentRegistrationBuilder":
        """Set the agent tags."""
        self._tags = tags
        return self

    def add_tag(self, tag: str) -> "AgentRegistrationBuilder":
        """Add a tag to the agent."""
        self._tags.append(tag)
        return self

    def with_capabilities(self, capabilities: List[str]) -> "AgentRegistrationBuilder":
        """Set the agent capabilities."""
        self._capabilities = capabilities
        return self

    def add_capability(self, capability: str) -> "AgentRegistrationBuilder":
        """Add a capability to the agent."""
        self._capabilities.append(capability)
        return self

    def with_tool(
        self,
        name: str,
        description: str,
        input_schema: Optional[Dict[str, Any]] = None,
    ) -> "AgentRegistrationBuilder":
        """
        Add a tool definition.

        Args:
            name: Tool name
            description: Tool description
            input_schema: JSON schema for tool input

        Returns:
            self for chaining
        """
        tool = {
            "name": name,
            "description": description,
        }
        if input_schema:
            tool["inputSchema"] = input_schema
        self._tools.append(tool)
        return self

    def with_input_schema(self, schema: Dict[str, Any]) -> "AgentRegistrationBuilder":
        """Set the input JSON schema."""
        self._input_schema = schema
        return self

    def with_output_schema(self, schema: Dict[str, Any]) -> "AgentRegistrationBuilder":
        """Set the output JSON schema."""
        self._output_schema = schema
        return self

    def with_endpoints(self, endpoints: Dict[str, Any]) -> "AgentRegistrationBuilder":
        """Set the endpoints configuration."""
        self._endpoints = endpoints
        return self

    def with_auth(self, auth: Dict[str, Any]) -> "AgentRegistrationBuilder":
        """Set the authentication configuration."""
        self._auth = auth
        return self

    def with_pricing(self, pricing: Dict[str, Any]) -> "AgentRegistrationBuilder":
        """Set the pricing configuration."""
        self._pricing = pricing
        return self

    def with_metadata(self, metadata: Dict[str, Any]) -> "AgentRegistrationBuilder":
        """Set additional metadata."""
        self._metadata = metadata
        return self

    def build(self) -> Dict[str, Any]:
        """
        Build the agent manifest.

        Returns:
            Agent manifest dictionary
        """
        manifest: Dict[str, Any] = {
            "agent_id": self._agent_id,
            "name": self._name,
            "version": self._version,
            "category": self._category,
            "tags": self._tags,
            "capabilities": self._capabilities,
            "tools": self._tools,
        }

        if self._description:
            manifest["description"] = self._description
        if self._author:
            manifest["author"] = self._author
        if self._input_schema:
            manifest["input_schema"] = self._input_schema
        if self._output_schema:
            manifest["output_schema"] = self._output_schema
        if self._endpoints:
            manifest["endpoints"] = self._endpoints
        if self._auth:
            manifest["auth"] = self._auth
        if self._pricing:
            manifest["pricing"] = self._pricing
        if self._metadata:
            manifest["metadata"] = self._metadata

        return manifest


def register_agent_decorator(
    agent_id: str,
    name: str,
    version: str = "1.0.0",
    description: Optional[str] = None,
    category: str = "general",
    capabilities: Optional[List[str]] = None,
):
    """
    Decorator for registering a function as an agent.

    Usage:
        @register_agent_decorator(
            agent_id="mycompany.myagent",
            name="My Agent",
            description="A helpful agent"
        )
        async def my_agent_handler(request: AgentRequest) -> AgentResponse:
            return AgentResponse(...)

    Args:
        agent_id: Unique identifier for the agent
        name: Human-readable name
        version: Agent version
        description: Agent description
        category: Agent category
        capabilities: List of capabilities

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> "FunctionAgent":
        return FunctionAgent(
            agent_id=agent_id,
            name=name,
            version=version,
            description=description,
            category=category,
            capabilities=capabilities,
            handler=func,
        )

    return decorator


class FunctionAgent(AgentBase):
    """
    Agent that wraps a simple async function.

    Created by the register_agent_decorator.
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        version: str = "1.0.0",
        description: Optional[str] = None,
        category: str = "general",
        capabilities: Optional[List[str]] = None,
        handler: Optional[Callable] = None,
    ):
        """
        Initialize the function agent.

        Args:
            agent_id: Unique identifier
            name: Human-readable name
            version: Agent version
            description: Agent description
            category: Agent category
            capabilities: List of capabilities
            handler: Async function to handle requests
        """
        super().__init__(
            agent_id=agent_id,
            name=name,
            version=version,
            description=description,
            category=category,
            capabilities=capabilities,
        )
        self._handler = handler

    def set_handler(self, handler: Callable) -> None:
        """Set the handler function."""
        self._handler = handler

    async def invoke(self, request: AgentRequest) -> AgentResponse:
        """Handle the request using the configured handler."""
        if self._handler is None:
            return self.error_response(
                code="EXEC_INTERNAL_ERROR",
                message="No handler configured for this agent",
                request_id=request.request_id,
            )

        try:
            result = self._handler(request)
            # Handle both sync and async handlers
            import asyncio
            if asyncio.iscoroutine(result):
                result = await result

            if isinstance(result, AgentResponse):
                return result

            # If handler returns dict, try to create response
            if isinstance(result, dict):
                return AgentResponse.from_dict(result)

            # If handler returns string, create success response
            if isinstance(result, str):
                return self.success_response(
                    text=result,
                    request_id=request.request_id,
                )

            return self.error_response(
                code="AGENT_OUTPUT_INVALID",
                message=f"Handler returned unexpected type: {type(result)}",
                request_id=request.request_id,
            )

        except Exception as e:
            return self.error_response(
                code="EXEC_INTERNAL_ERROR",
                message=str(e),
                request_id=request.request_id,
            )
