"""
NexusOps Backend - Pydantic Schemas

Compatible with frontend TypeScript types
"""

from datetime import datetime
from typing import Any, Generic, Literal, Optional, TypeVar

from pydantic import BaseModel, Field


# ============================================
# Common
# ============================================

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper"""
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    message: str
    details: Optional[dict[str, Any]] = None


# ============================================
# Project Schemas
# ============================================

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    git_repo: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    git_repo: Optional[str] = None
    status: Optional[str] = None


class ProjectResponse(ProjectBase):
    id: str
    status: str
    production_version_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectDetail(ProjectResponse):
    versions: list["VersionResponse"] = []
    version_count: int = 0


# ============================================
# Version Schemas
# ============================================

class VersionBase(BaseModel):
    codename: str
    version: Optional[str] = None
    git_branch: Optional[str] = None
    git_commit: Optional[str] = None


class VersionCreate(VersionBase):
    project_id: str


class VersionUpdate(BaseModel):
    codename: Optional[str] = None
    version: Optional[str] = None
    status: Optional[str] = None
    health: Optional[str] = None
    test_url: Optional[str] = None
    deployed_regions: Optional[list[str]] = None


class VersionResponse(VersionBase):
    id: str
    project_id: str
    status: str
    health: str
    test_url: Optional[str] = None
    deployed_regions: list[str] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VersionDetail(VersionResponse):
    deployments: list["DeploymentResponse"] = []


# ============================================
# Deployment Schemas
# ============================================

class DeploymentStepResponse(BaseModel):
    id: str
    step_type: str
    name: str
    status: str
    message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    details: Optional[dict[str, Any]] = None

    class Config:
        from_attributes = True


class DeploymentBase(BaseModel):
    version_id: str
    region: str
    namespace: str = "default"


class DeploymentCreate(DeploymentBase):
    pass


class DeploymentResponse(DeploymentBase):
    id: str
    status: str
    health: str
    argocd_app: Optional[str] = None
    argocd_sync_status: Optional[str] = None
    argocd_health_status: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeploymentDetail(DeploymentResponse):
    steps: list[DeploymentStepResponse] = []


# ============================================
# Agent Schemas (Compatible with frontend types)
# ============================================

class AgentIdentity(BaseModel):
    agent_id: str
    agent_name: str
    agent_version: str
    agent_type: Literal["builtin", "third_party"]
    provider: str


class AgentToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any] = Field(default_factory=dict, alias="inputSchema")

    class Config:
        populate_by_name = True


class AgentManifest(BaseModel):
    agent_id: str
    name: str
    version: str
    description: Optional[str] = None
    category: str
    capabilities: list[str] = []
    tools: list[AgentToolDefinition] = []
    input_schema: Optional[dict[str, Any]] = None
    output_schema: Optional[dict[str, Any]] = None

    class Config:
        populate_by_name = True


class AgentRequestContext(BaseModel):
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    project_id: Optional[str] = None
    version_id: Optional[str] = None
    codename: Optional[str] = None
    region: Optional[str] = None
    resource_type: Optional[str] = None
    resource_name: Optional[str] = None
    namespace: Optional[str] = None


class AgentRequest(BaseModel):
    request_id: str
    conversation_id: str
    agent_id: str
    query: str
    context: AgentRequestContext = Field(default_factory=AgentRequestContext)
    output_config: Optional[dict[str, Any]] = None
    tools: Optional[list[dict[str, Any]]] = None


class AgentAction(BaseModel):
    id: str
    type: str
    label: str
    params: dict[str, Any] = {}
    confirm_required: bool = False
    danger: bool = False


class RelatedResource(BaseModel):
    type: str
    id: str
    name: str
    link: Optional[str] = None


class AgentContent(BaseModel):
    text: str
    format: Literal["markdown", "json", "plain"] = "markdown"
    data: Optional[Any] = None


class AgentError(BaseModel):
    code: str
    message: str
    details: Optional[dict[str, Any]] = None
    retry_after: Optional[int] = None


class AgentResponse(BaseModel):
    request_id: str
    status: Literal["success", "error", "partial", "pending"]
    content: AgentContent
    structured_output: Optional[Any] = None
    suggested_actions: list[AgentAction] = []
    related_resources: list[RelatedResource] = []
    tool_calls: Optional[list[dict[str, Any]]] = None
    metadata: Optional[dict[str, Any]] = None
    error: Optional[AgentError] = None


class AgentRegistrationCreate(BaseModel):
    agent_id: str
    name: str
    version: str
    manifest: dict[str, Any]
    endpoint: Optional[str] = None


class AgentRegistrationResponse(BaseModel):
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
# Region Schemas
# ============================================

class RegionBase(BaseModel):
    name: str
    code: str
    country: str
    continent: str
    latitude: float
    longitude: float


class RegionResponse(RegionBase):
    id: str
    status: str
    k8s_cluster: Optional[str] = None
    k8s_context: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================
# User Schemas
# ============================================

class UserBase(BaseModel):
    username: str
    email: str


class UserCreate(UserBase):
    password: str
    full_name: Optional[str] = None


class UserResponse(UserBase):
    id: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginRequest(BaseModel):
    username: str
    password: str


# Update forward references
ProjectDetail.model_rebuild()
VersionDetail.model_rebuild()
