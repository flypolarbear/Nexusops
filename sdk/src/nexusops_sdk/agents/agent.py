"""
NexusOps SDK - Agent Base Class

Base class for creating custom agents.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..models import AgentRequest, AgentResponse, AgentContent


class AgentBase(ABC):
    """
    Abstract base class for creating custom agents.

    Subclasses must implement the `invoke` method.
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        version: str = "1.0.0",
        description: Optional[str] = None,
        category: str = "general",
        capabilities: Optional[List[str]] = None,
    ):
        """
        Initialize the agent.

        Args:
            agent_id: Unique identifier for the agent (e.g., "mycompany.myagent")
            name: Human-readable name
            version: Agent version
            description: Agent description
            category: Agent category (general, infrastructure, deployment, etc.)
            capabilities: List of capabilities this agent provides
        """
        self.agent_id = agent_id
        self.name = name
        self.version = version
        self.description = description
        self.category = category
        self.capabilities = capabilities or []

    @abstractmethod
    async def invoke(self, request: AgentRequest) -> AgentResponse:
        """
        Handle an invocation request.

        Args:
            request: The incoming request

        Returns:
            AgentResponse with the result
        """
        pass

    def get_manifest(self) -> Dict[str, Any]:
        """
        Get the agent manifest for registration.

        Returns:
            Agent manifest dictionary
        """
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "category": self.category,
            "capabilities": self.capabilities,
            "tools": self.get_tools(),
            "input_schema": self.get_input_schema(),
            "output_schema": self.get_output_schema(),
        }

    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get tool definitions for this agent.

        Override this method to define tools.

        Returns:
            List of tool definitions
        """
        return []

    def get_input_schema(self) -> Optional[Dict[str, Any]]:
        """
        Get the input JSON schema for this agent.

        Override this method to define input schema.

        Returns:
            JSON schema dictionary or None
        """
        return None

    def get_output_schema(self) -> Optional[Dict[str, Any]]:
        """
        Get the output JSON schema for this agent.

        Override this method to define output schema.

        Returns:
            JSON schema dictionary or None
        """
        return None

    # Helper methods for building responses

    @staticmethod
    def success_response(
        text: str,
        format: str = "markdown",
        structured_output: Optional[Any] = None,
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> AgentResponse:
        """
        Create a success response.

        Args:
            text: Response text
            format: Content format (markdown, json, plain)
            structured_output: Optional structured output
            request_id: Request ID to echo back
            trace_id: Trace ID to echo back

        Returns:
            AgentResponse with success status
        """
        return AgentResponse(
            request_id=request_id or "",
            trace_id=trace_id,
            status="success",
            content=AgentContent(text=text, format=format),
            structured_output=structured_output,
        )

    @staticmethod
    def error_response(
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> AgentResponse:
        """
        Create an error response.

        Args:
            code: Error code (e.g., "EXEC_INTERNAL_ERROR")
            message: Error message
            details: Optional error details
            request_id: Request ID to echo back
            trace_id: Trace ID to echo back

        Returns:
            AgentResponse with error status
        """
        from ..models.response import AgentError

        return AgentResponse(
            request_id=request_id or "",
            trace_id=trace_id,
            status="error",
            content=AgentContent(text=message, format="plain"),
            error=AgentError(
                code=code,
                message=message,
                details=details,
            ),
        )

    @staticmethod
    def partial_response(
        text: str,
        format: str = "markdown",
        structured_output: Optional[Any] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> AgentResponse:
        """
        Create a partial success response.

        Args:
            text: Response text
            format: Content format
            structured_output: Optional structured output
            error_code: Optional error code for the partial failure
            error_message: Optional error message
            request_id: Request ID to echo back
            trace_id: Trace ID to echo back

        Returns:
            AgentResponse with partial status
        """
        from ..models.response import AgentError

        error = None
        if error_code and error_message:
            error = AgentError(code=error_code, message=error_message)

        return AgentResponse(
            request_id=request_id or "",
            trace_id=trace_id,
            status="partial",
            content=AgentContent(text=text, format=format),
            structured_output=structured_output,
            error=error,
        )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} agent_id={self.agent_id} version={self.version}>"
