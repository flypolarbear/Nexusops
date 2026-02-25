"""
NexusOps Gateway - Request/Response Contract

MK-006: 统一 Invoke API 契约

Defines the unified request/response structure for all Agent invocations.
"""

from typing import Optional, List, Any, Dict, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================
# Request Models
# ============================================

class RequestContext(BaseModel):
    """Request context with user/project/environment info"""
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    project_id: Optional[str] = None
    version_id: Optional[str] = None
    codename: Optional[str] = None
    region: Optional[str] = None
    resource_type: Optional[str] = None
    resource_name: Optional[str] = None
    namespace: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None


class OutputConfig(BaseModel):
    """Output configuration"""
    format: Literal["markdown", "json", "plain"] = "markdown"
    max_tokens: Optional[int] = Field(None, ge=1, le=32000)
    structured_output_schema: Optional[Dict[str, Any]] = None


class ToolOverride(BaseModel):
    """Tool override configuration"""
    name: str
    enabled: bool = True
    params: Optional[Dict[str, Any]] = None


class InvokeRequest(BaseModel):
    """Unified Invoke API Request"""
    request_id: str = Field(..., description="Client-generated unique request ID")
    conversation_id: Optional[str] = Field(None, description="Session ID for multi-turn conversations")
    agent_id: str = Field(..., pattern=r"^[a-z][a-z0-9._-]{2,63}$", description="Target Agent ID")
    query: str = Field(..., min_length=1, max_length=10000, description="User input")
    context: RequestContext = Field(default_factory=RequestContext)
    output_config: Optional[OutputConfig] = None
    tools: Optional[List[ToolOverride]] = None


# ============================================
# Response Models
# ============================================

class ResponseContent(BaseModel):
    """Response content"""
    text: str
    format: Literal["markdown", "json", "plain"] = "markdown"
    data: Optional[Any] = None


class SuggestedAction(BaseModel):
    """Suggested action for user"""
    id: str
    type: Literal["invoke", "navigate", "copy", "external"]
    label: str
    params: Optional[Dict[str, Any]] = None
    confirm_required: bool = False
    danger: bool = False


class RelatedResource(BaseModel):
    """Related resource reference"""
    type: str
    id: str
    name: str
    link: Optional[str] = None


class ToolCall(BaseModel):
    """Tool call record"""
    tool_id: str
    tool_name: Optional[str] = None
    input: Optional[Dict[str, Any]] = None
    output: Optional[Any] = None
    status: Literal["success", "error", "skipped"] = "success"
    duration_ms: Optional[int] = None
    error: Optional["ErrorDetail"] = None


class TokenUsage(BaseModel):
    """Token usage info"""
    input: Optional[int] = None
    output: Optional[int] = None


class ResponseMetadata(BaseModel):
    """Response metadata"""
    trace_id: Optional[str] = None
    agent_version: Optional[str] = None
    latency_ms: Optional[int] = None
    tokens_used: Optional[TokenUsage] = None
    retry_count: Optional[int] = None
    cache_hit: Optional[bool] = None
    agent_type: Optional[str] = None
    execution_mode: Optional[str] = None


class ErrorDetail(BaseModel):
    """Error detail"""
    code: str = Field(..., pattern=r"^[A-Z][A-Z0-9_]{2,31}$")
    message: str
    details: Optional[Dict[str, Any]] = None
    retry_after: Optional[int] = Field(None, description="Suggested retry interval in seconds")
    doc_url: Optional[str] = None


class InvokeResponse(BaseModel):
    """Unified Invoke API Response"""
    request_id: str
    trace_id: Optional[str] = None
    status: Literal["success", "error", "partial", "pending"] = "success"
    content: ResponseContent
    structured_output: Optional[Any] = None
    suggested_actions: List[SuggestedAction] = Field(default_factory=list)
    related_resources: List[RelatedResource] = Field(default_factory=list)
    tool_calls: Optional[List[ToolCall]] = None
    metadata: Optional[ResponseMetadata] = None
    error: Optional[ErrorDetail] = None

    class Config:
        populate_by_name = True


# ============================================
# Internal Models (for executor layer)
# ============================================

class ExecutorContext(BaseModel):
    """Execution context for executor"""
    trace_id: str
    request_id: str
    agent_id: str
    agent_version: str = "1.0.0"
    agent_type: Literal["builtin", "remote", "mock"] = "builtin"
    endpoint: Optional[str] = None
    timeout_ms: int = 30000
    retry_config: Optional[Dict[str, Any]] = None
    auth_context: Optional[Dict[str, Any]] = None


class ExecutorRequest(BaseModel):
    """Execution request for executor"""
    context: ExecutorContext
    query: str
    request_context: Dict[str, Any] = Field(default_factory=dict)
    output_config: Optional[Dict[str, Any]] = None
    tools: Optional[List[Dict[str, Any]]] = None


class ExecutorResult(BaseModel):
    """Execution result from executor"""
    success: bool
    content: Dict[str, Any]
    structured_output: Optional[Any] = None
    suggested_actions: List[Dict[str, Any]] = Field(default_factory=list)
    related_resources: List[Dict[str, Any]] = Field(default_factory=list)
    tool_calls: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[Dict[str, Any]] = None

    def to_invoke_response(self, request_id: str, trace_id: str) -> InvokeResponse:
        """Convert to InvokeResponse"""
        status = "success" if self.success else "error"

        return InvokeResponse(
            request_id=request_id,
            trace_id=trace_id,
            status=status,
            content=ResponseContent(**self.content),
            structured_output=self.structured_output,
            suggested_actions=[
                SuggestedAction(**a) for a in self.suggested_actions
            ],
            related_resources=[
                RelatedResource(**r) for r in self.related_resources
            ],
            tool_calls=[
                ToolCall(**t) for t in (self.tool_calls or [])
            ],
            metadata=ResponseMetadata(
                trace_id=trace_id,
                **self.metadata
            ),
            error=ErrorDetail(**self.error) if self.error else None,
        )
