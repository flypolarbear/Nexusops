"""
NexusOps Backend - Database Models

Based on ADR-003 (凭证管理), ADR-004 (状态管理)
"""

from datetime import datetime
from typing import Optional, Any
from uuid import uuid4

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Boolean,
    Index,
    TypeDecorator,
)
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB, UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class JSONB(TypeDecorator):
    """
    Platform-independent JSONB type.

    Uses PostgreSQL's JSONB type when available,
    falls back to JSON for other databases like SQLite.
    """
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_JSONB())
        else:
            return dialect.type_descriptor(JSON())


class UUID(TypeDecorator):
    """
    Platform-independent UUID type.

    Uses PostgreSQL's UUID type when available,
    falls back to String for other databases like SQLite.
    """
    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=False))
        else:
            return dialect.type_descriptor(String(36))


class Base(DeclarativeBase):
    """SQLAlchemy declarative base"""
    pass


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


# ============================================
# Project & Version Models
# ============================================

class Project(Base, TimestampMixin):
    """Project model"""
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    git_repo: Mapped[Optional[str]] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), default="active")

    # Relationships
    versions: Mapped[list["Version"]] = relationship(back_populates="project", cascade="all, delete-orphan")

    # Metadata
    production_version_id: Mapped[Optional[str]] = mapped_column(String(50))
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB)


class Version(Base, TimestampMixin):
    """Version model"""
    __tablename__ = "versions"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(50), ForeignKey("projects.id"), nullable=False)

    # Version info
    codename: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(50))
    git_branch: Mapped[Optional[str]] = mapped_column(String(255))
    git_commit: Mapped[Optional[str]] = mapped_column(String(50))

    # Status
    status: Mapped[str] = mapped_column(String(20), default="building")
    health: Mapped[str] = mapped_column(String(20), default="unknown")

    # Deployment info
    test_url: Mapped[Optional[str]] = mapped_column(String(255))
    deployed_regions: Mapped[list] = mapped_column(JSONB, default=list)

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="versions")
    deployments: Mapped[list["Deployment"]] = relationship(back_populates="version", cascade="all, delete-orphan")
    states: Mapped[list["AgentState"]] = relationship(back_populates="version", cascade="all, delete-orphan")


# ============================================
# Deployment Models
# ============================================

class Deployment(Base, TimestampMixin):
    """Deployment model"""
    __tablename__ = "deployments"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    version_id: Mapped[str] = mapped_column(String(50), ForeignKey("versions.id"), nullable=False)

    # Deployment info
    region: Mapped[str] = mapped_column(String(50), nullable=False)
    namespace: Mapped[str] = mapped_column(String(100), default="default")

    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending")
    health: Mapped[str] = mapped_column(String(20), default="unknown")

    # ArgoCD info
    argocd_app: Mapped[Optional[str]] = mapped_column(String(255))
    argocd_sync_status: Mapped[Optional[str]] = mapped_column(String(50))
    argocd_health_status: Mapped[Optional[str]] = mapped_column(String(50))

    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    version: Mapped["Version"] = relationship(back_populates="deployments")
    steps: Mapped[list["DeploymentStep"]] = relationship(back_populates="deployment", cascade="all, delete-orphan")


class DeploymentStep(Base):
    """Deployment step model - tracks CI/CD → ArgoCD → Health Check chain"""
    __tablename__ = "deployment_steps"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    deployment_id: Mapped[str] = mapped_column(String(50), ForeignKey("deployments.id"), nullable=False)

    # Step info
    step_type: Mapped[str] = mapped_column(String(50), nullable=False)  # ci_build, argocd_sync, health_check
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending")
    message: Mapped[Optional[str]] = mapped_column(Text)

    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Details
    details: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Relationships
    deployment: Mapped["Deployment"] = relationship(back_populates="steps")


# ============================================
# Agent Models (Based on ADR-004)
# ============================================

class AgentState(Base):
    """Agent state model - for persisting agent state"""
    __tablename__ = "agent_states"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))

    # Agent identification
    agent_id: Mapped[str] = mapped_column(String(255), nullable=False)
    agent_version: Mapped[Optional[str]] = mapped_column(String(50))

    # Context
    conversation_id: Mapped[str] = mapped_column(String(255), nullable=False)
    request_id: Mapped[Optional[str]] = mapped_column(String(255))

    # State type
    state_type: Mapped[str] = mapped_column(String(50), nullable=False)
    state_key: Mapped[str] = mapped_column(String(255), nullable=False)
    state_value: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Related resource
    related_resource_type: Mapped[Optional[str]] = mapped_column(String(50))
    related_resource_id: Mapped[Optional[str]] = mapped_column(String(255))
    version_id: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey("versions.id"))

    # Lifecycle
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    version: Mapped[Optional["Version"]] = relationship(back_populates="states")

    # Indexes
    __table_args__ = (
        Index("ix_agent_states_agent_conv_key", "agent_id", "conversation_id", "state_key", unique=True),
        Index("ix_agent_states_expires", "expires_at"),
    )


class AgentInvocation(Base):
    """Agent invocation log - for tracking and auditing"""
    __tablename__ = "agent_invocations"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))

    # Agent info
    agent_id: Mapped[str] = mapped_column(String(255), nullable=False)

    # Request/Response
    request_id: Mapped[str] = mapped_column(String(255), nullable=False)
    conversation_id: Mapped[Optional[str]] = mapped_column(String(255))
    request: Mapped[dict] = mapped_column(JSONB)
    response: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Metrics
    status: Mapped[str] = mapped_column(String(20), default="pending")
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer)

    # Error info
    error_code: Mapped[Optional[str]] = mapped_column(String(50))
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index("ix_agent_invocations_agent", "agent_id"),
        Index("ix_agent_invocations_created", "created_at"),
    )


class AgentRegistration(Base, TimestampMixin):
    """Agent registration - for Agent Registry"""
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)  # e.g., com.nexusops.agents.dns
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)

    # Manifest
    manifest: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="active")

    # Endpoint
    endpoint: Mapped[Optional[str]] = mapped_column(String(255))
    last_heartbeat: Mapped[Optional[datetime]] = mapped_column(DateTime)


# ============================================
# User Models
# ============================================

class User(Base, TimestampMixin):
    """User model"""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Profile
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Roles
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    # Tenant
    tenant_id: Mapped[Optional[str]] = mapped_column(String(50))


# ============================================
# Region Models
# ============================================

class Region(Base, TimestampMixin):
    """Deployment region model"""
    __tablename__ = "regions"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # e.g., us-east

    # Location
    country: Mapped[str] = mapped_column(String(100))
    continent: Mapped[str] = mapped_column(String(50))

    # Status
    status: Mapped[str] = mapped_column(String(20), default="active")

    # Cluster info
    k8s_cluster: Mapped[Optional[str]] = mapped_column(String(255))
    k8s_context: Mapped[Optional[str]] = mapped_column(String(255))

    # Coordinates (for WorldMap)
    latitude: Mapped[float] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)
