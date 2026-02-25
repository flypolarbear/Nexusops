"""
NexusOps SDK - Models

Request and response models aligned with MK-006 Gateway Contract.
"""

from .request import (
    AgentRequest,
    AgentRequestContext,
    OutputConfig,
    ToolOverride,
)
from .response import (
    AgentResponse,
    AgentContent,
    AgentError,
    SuggestedAction,
    RelatedResource,
    ToolCall,
    ResponseMetadata,
    TokenUsage,
)

# Import Agent model
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Agent running status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class InstallStatus(str, Enum):
    """Agent installation status."""
    NOT_INSTALLED = "not_installed"
    INSTALLED = "installed"
    DISABLED = "disabled"


class AgentToolDefinition(BaseModel):
    """Agent tool definition."""
    name: str
    description: str
    input_schema: Dict[str, Any] = Field(default_factory=dict, alias="inputSchema")

    class Config:
        populate_by_name = True


class AgentManifest(BaseModel):
    """Agent manifest for registration."""
    agent_id: str
    name: str
    version: str
    description: Optional[str] = None
    author: Optional[str] = None
    category: str = "general"
    tags: List[str] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)
    tools: List[Dict[str, Any]] = Field(default_factory=list)
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    endpoints: Optional[Dict[str, Any]] = None
    auth: Optional[Dict[str, Any]] = None
    pricing: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class Agent(BaseModel):
    """Agent model with full details."""
    agent_id: str
    name: str
    version: str
    description: Optional[str] = None
    author: Optional[str] = None
    category: str = "general"
    tags: List[str] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)
    tools: List[AgentToolDefinition] = Field(default_factory=list)
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    status: AgentStatus = AgentStatus.ACTIVE
    install_status: InstallStatus = InstallStatus.NOT_INSTALLED
    visibility: str = "public"
    endpoint: Optional[str] = None
    rating: float = 0.0
    downloads: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        populate_by_name = True


class AgentInstallStatus(BaseModel):
    """Agent installation status response."""
    agent_id: str
    name: str
    version: str
    install_status: InstallStatus
    agent_status: AgentStatus
    installed_at: Optional[str] = None
    last_heartbeat: Optional[str] = None


__all__ = [
    # Request models
    "AgentRequest",
    "AgentRequestContext",
    "OutputConfig",
    "ToolOverride",
    # Response models
    "AgentResponse",
    "AgentContent",
    "AgentError",
    "SuggestedAction",
    "RelatedResource",
    "ToolCall",
    "ResponseMetadata",
    "TokenUsage",
    # Agent models
    "Agent",
    "AgentManifest",
    "AgentToolDefinition",
    "AgentStatus",
    "InstallStatus",
    "AgentInstallStatus",
]
