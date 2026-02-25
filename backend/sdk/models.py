"""
NexusOps SDK - Models

Pydantic models for request and response data structures.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ============================================
# Configuration
# ============================================

class AgentConfig(BaseModel):
    """Configuration for the AgentClient."""

    base_url: str = Field(
        ...,
        description="Base URL of the NexusOps server",
        examples=["https://nexusops.example.com", "http://localhost:8000"],
    )
    api_key: str = Field(
        ...,
        description="API key for authentication",
    )
    timeout: float = Field(
        default=30.0,
        description="Default timeout for requests in seconds",
        gt=0,
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts",
        ge=0,
        le=10,
    )
    retry_delay: float = Field(
        default=1.0,
        description="Base delay between retries in seconds",
        ge=0,
    )
    verify_ssl: bool = Field(
        default=True,
        description="Whether to verify SSL certificates",
    )


# ============================================
# Agent Manifest
# ============================================

class AgentToolDefinition(BaseModel):
    """Definition of an agent tool."""

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    input_schema: Dict[str, Any] = Field(
        default_factory=dict,
        alias="inputSchema",
        description="JSON Schema for tool input",
    )

    class Config:
        populate_by_name = True


class AgentManifest(BaseModel):
    """Agent manifest containing metadata and capabilities."""

    agent_id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Agent display name")
    version: str = Field(default="1.0.0", description="Agent version")
    description: Optional[str] = Field(default=None, description="Agent description")
    category: str = Field(default="general", description="Agent category")
    capabilities: List[str] = Field(
        default_factory=list,
        description="List of agent capabilities",
    )
    tools: List[AgentToolDefinition] = Field(
        default_factory=list,
        description="List of available tools",
    )
    input_schema: Optional[Dict[str, Any]] = Field(
        default=None,
        description="JSON Schema for agent input",
    )
    output_schema: Optional[Dict[str, Any]] = Field(
        default=None,
        description="JSON Schema for agent output",
    )

    class Config:
        populate_by_name = True


# ============================================
# Agent Registration
# ============================================

class AgentRegistrationRequest(BaseModel):
    """Request to register a new agent."""

    agent_id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Agent display name")
    version: str = Field(default="1.0.0", description="Agent version")
    description: Optional[str] = Field(default=None, description="Agent description")
    category: str = Field(default="custom", description="Agent category")
    capabilities: List[str] = Field(
        default_factory=list,
        description="List of agent capabilities",
    )
    tools: List[AgentToolDefinition] = Field(
        default_factory=list,
        description="List of available tools",
    )
    endpoint: Optional[str] = Field(
        default=None,
        description="Webhook endpoint for the agent",
    )
    input_schema: Optional[Dict[str, Any]] = Field(
        default=None,
        description="JSON Schema for agent input",
    )
    output_schema: Optional[Dict[str, Any]] = Field(
        default=None,
        description="JSON Schema for agent output",
    )


class AgentRegistrationResponse(BaseModel):
    """Response after agent registration."""

    agent_id: str
    name: str
    version: str
    status: str
    endpoint: Optional[str] = None
    last_heartbeat: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================
# Agent Invocation
# ============================================

class AgentRequestContext(BaseModel):
    """Context information for agent requests."""

    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    project_id: Optional[str] = None
    version_id: Optional[str] = None
    codename: Optional[str] = None
    region: Optional[str] = None
    resource_type: Optional[str] = None
    resource_name: Optional[str] = None
    namespace: Optional[str] = None


class AgentInvokeRequest(BaseModel):
    """Request to invoke an agent."""

    agent_id: str = Field(..., description="Agent to invoke")
    query: str = Field(..., description="Query or command for the agent")
    action: Optional[str] = Field(
        default=None,
        description="Specific action to perform",
    )
    params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Parameters for the action",
    )
    context: Optional[AgentRequestContext] = Field(
        default=None,
        description="Request context",
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="Conversation ID for continuity",
    )
    output_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Output configuration",
    )
    tools: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Tools to make available",
    )


class AgentContent(BaseModel):
    """Content returned by an agent."""

    text: str = Field(default="", description="Text content")
    format: Literal["markdown", "json", "plain"] = Field(
        default="markdown",
        description="Content format",
    )
    data: Optional[Any] = Field(
        default=None,
        description="Structured data",
    )


class AgentAction(BaseModel):
    """Suggested action from an agent."""

    id: str
    type: str
    label: str
    params: Dict[str, Any] = Field(default_factory=dict)
    confirm_required: bool = Field(default=False)
    danger: bool = Field(default=False)


class RelatedResource(BaseModel):
    """Resource related to an agent response."""

    type: str
    id: str
    name: str
    link: Optional[str] = None


class AgentError(BaseModel):
    """Error information from an agent response."""

    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    retry_after: Optional[int] = None


class AgentInvokeResponse(BaseModel):
    """Response from an agent invocation."""

    request_id: str
    status: Literal["success", "error", "partial", "pending"]
    content: AgentContent
    structured_output: Optional[Any] = None
    suggested_actions: List[AgentAction] = Field(default_factory=list)
    related_resources: List[RelatedResource] = Field(default_factory=list)
    tool_calls: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[AgentError] = None
    trace_id: Optional[str] = Field(
        default=None,
        description="Trace ID for debugging",
    )


# ============================================
# Agent Status
# ============================================

class AgentStatus(BaseModel):
    """Status of an agent."""

    agent_id: str
    name: str
    status: Literal["active", "inactive", "disabled", "error"]
    version: str
    last_heartbeat: Optional[datetime] = None
    uptime_seconds: Optional[float] = None
    total_invocations: int = Field(default=0)
    successful_invocations: int = Field(default=0)
    failed_invocations: int = Field(default=0)
    average_latency_ms: Optional[float] = None


# ============================================
# Agent List
# ============================================

class AgentListResponse(BaseModel):
    """Response containing a list of agents."""

    agents: List[AgentManifest]
    total: int
    page: Optional[int] = None
    page_size: Optional[int] = None


# ============================================
# Error Models
# ============================================

class ErrorResponse(BaseModel):
    """Standard error response from the API."""

    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = None
