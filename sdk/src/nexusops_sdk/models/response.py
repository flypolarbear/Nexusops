"""
NexusOps SDK - Response Models

Response models for Agent Gateway API aligned with MK-006 Gateway Contract.
"""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class AgentContent(BaseModel):
    """Response content."""

    text: str
    format: Literal["markdown", "json", "plain"] = "markdown"
    data: Optional[Any] = None


class SuggestedAction(BaseModel):
    """Suggested action for user."""

    id: str
    type: Literal["invoke", "navigate", "copy", "external"]
    label: str
    params: Optional[Dict[str, Any]] = None
    confirm_required: bool = False
    danger: bool = False


class RelatedResource(BaseModel):
    """Related resource reference."""

    type: str
    id: str
    name: str
    link: Optional[str] = None


class AgentError(BaseModel):
    """Error detail in response."""

    code: str = Field(..., pattern=r"^[A-Z][A-Z0-9_]{2,31}$")
    message: str
    details: Optional[Dict[str, Any]] = None
    retry_after: Optional[int] = Field(None, description="Suggested retry interval in seconds")
    doc_url: Optional[str] = None


class ToolCall(BaseModel):
    """Tool call record."""

    tool_id: str
    tool_name: Optional[str] = None
    input: Optional[Dict[str, Any]] = None
    output: Optional[Any] = None
    status: Literal["success", "error", "skipped"] = "success"
    duration_ms: Optional[int] = None
    error: Optional[AgentError] = None


class TokenUsage(BaseModel):
    """Token usage info."""

    input: Optional[int] = None
    output: Optional[int] = None


class ResponseMetadata(BaseModel):
    """Response metadata."""

    trace_id: Optional[str] = None
    agent_version: Optional[str] = None
    latency_ms: Optional[int] = None
    tokens_used: Optional[TokenUsage] = None
    retry_count: Optional[int] = None
    cache_hit: Optional[bool] = None
    agent_type: Optional[str] = None
    execution_mode: Optional[str] = None


class AgentResponse(BaseModel):
    """
    Unified Invoke API Response.

    Aligned with MK-006 Gateway Contract.
    """

    request_id: str
    trace_id: Optional[str] = None
    status: Literal["success", "error", "partial", "pending"] = "success"
    content: AgentContent
    structured_output: Optional[Any] = None
    suggested_actions: List[SuggestedAction] = Field(default_factory=list)
    related_resources: List[RelatedResource] = Field(default_factory=list)
    tool_calls: Optional[List[ToolCall]] = None
    metadata: Optional[ResponseMetadata] = None
    error: Optional[AgentError] = None

    class Config:
        populate_by_name = True

    @property
    def is_success(self) -> bool:
        """Check if the response indicates success."""
        return self.status == "success"

    @property
    def is_error(self) -> bool:
        """Check if the response indicates an error."""
        return self.status == "error"

    @property
    def is_partial(self) -> bool:
        """Check if the response indicates partial success."""
        return self.status == "partial"

    @property
    def is_pending(self) -> bool:
        """Check if the response indicates pending status."""
        return self.status == "pending"

    def get_text(self) -> str:
        """Get the response text content."""
        return self.content.text if self.content else ""

    def get_structured_output(self) -> Optional[Any]:
        """Get the structured output if available."""
        return self.structured_output

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentResponse":
        """
        Create AgentResponse from dictionary.

        Handles nested model conversion automatically.
        """
        # Parse content
        content_data = data.get("content", {})
        if isinstance(content_data, dict):
            content = AgentContent(**content_data)
        else:
            content = content_data

        # Parse suggested actions
        suggested_actions = []
        for action in data.get("suggested_actions", []):
            if isinstance(action, dict):
                suggested_actions.append(SuggestedAction(**action))
            else:
                suggested_actions.append(action)

        # Parse related resources
        related_resources = []
        for resource in data.get("related_resources", []):
            if isinstance(resource, dict):
                related_resources.append(RelatedResource(**resource))
            else:
                related_resources.append(resource)

        # Parse tool calls
        tool_calls = None
        if data.get("tool_calls"):
            tool_calls = []
            for tc in data["tool_calls"]:
                if isinstance(tc, dict):
                    tool_calls.append(ToolCall(**tc))
                else:
                    tool_calls.append(tc)

        # Parse metadata
        metadata = None
        if data.get("metadata"):
            metadata_data = data["metadata"]
            if isinstance(metadata_data, dict):
                metadata = ResponseMetadata(**metadata_data)
            else:
                metadata = metadata_data

        # Parse error
        error = None
        if data.get("error"):
            error_data = data["error"]
            if isinstance(error_data, dict):
                error = AgentError(**error_data)
            else:
                error = error_data

        return cls(
            request_id=data.get("request_id", ""),
            trace_id=data.get("trace_id"),
            status=data.get("status", "success"),
            content=content,
            structured_output=data.get("structured_output"),
            suggested_actions=suggested_actions,
            related_resources=related_resources,
            tool_calls=tool_calls,
            metadata=metadata,
            error=error,
        )
