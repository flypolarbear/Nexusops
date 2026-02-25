"""
NexusOps SDK - Request Models

Request models for Agent Gateway API aligned with MK-006 Gateway Contract.
"""

import uuid
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class AgentRequestContext(BaseModel):
    """Request context with user/project/environment info."""

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
    """Output configuration for agent response."""

    format: Literal["markdown", "json", "plain"] = "markdown"
    max_tokens: Optional[int] = Field(None, ge=1, le=32000)
    structured_output_schema: Optional[Dict[str, Any]] = None


class ToolOverride(BaseModel):
    """Tool override configuration."""

    name: str
    enabled: bool = True
    params: Optional[Dict[str, Any]] = None


class AgentRequest(BaseModel):
    """
    Unified Invoke API Request.

    Aligned with MK-006 Gateway Contract.
    """

    request_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Client-generated unique request ID"
    )
    conversation_id: Optional[str] = Field(
        None,
        description="Session ID for multi-turn conversations"
    )
    agent_id: str = Field(
        ...,
        pattern=r"^[a-z][a-z0-9._-]{2,63}$",
        description="Target Agent ID"
    )
    query: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="User input"
    )
    context: AgentRequestContext = Field(
        default_factory=AgentRequestContext,
        description="Request context"
    )
    output_config: Optional[OutputConfig] = None
    tools: Optional[List[ToolOverride]] = None

    class Config:
        populate_by_name = True

    @classmethod
    def create(
        cls,
        agent_id: str,
        query: str,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        project_id: Optional[str] = None,
        **kwargs,
    ) -> "AgentRequest":
        """
        Convenience method to create a request.

        Args:
            agent_id: Target Agent ID
            query: User input/query
            conversation_id: Optional conversation ID for multi-turn
            user_id: Optional user ID
            tenant_id: Optional tenant ID
            project_id: Optional project ID
            **kwargs: Additional context fields

        Returns:
            AgentRequest instance
        """
        context = AgentRequestContext(
            user_id=user_id,
            tenant_id=tenant_id,
            project_id=project_id,
            **{k: v for k, v in kwargs.items() if hasattr(AgentRequestContext.__fields__, k)}
        )

        return cls(
            agent_id=agent_id,
            query=query,
            conversation_id=conversation_id,
            context=context,
        )
