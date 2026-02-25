"""
NexusOps Backend - Agent Store

Database-backed storage for agent data.
Supports both sync and async operations for flexibility.

Migration from in-memory to database storage:
- Agent registrations are stored in 'agents' table (via AgentRegistration model)
- Install status is stored in 'installed_agents' table
- Reviews are stored in 'agent_reviews' table
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
import json

from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import async_session, engine
from app.models.database import Base, AgentRegistration, TimestampMixin


# ============================================
# Database Models for Agent Store
# ============================================

class InstalledAgent(Base, TimestampMixin):
    """Installed Agent model - tracks installation status"""
    __tablename__ = "installed_agents"

    agent_id: Mapped[str] = mapped_column(primary_key=True)
    install_status: Mapped[str] = mapped_column(default="installed")  # installed, disabled
    installed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    installed_by: Mapped[str] = mapped_column(default="anonymous")


class AgentReview(Base):
    """Agent Review model - stores reviews for agents"""
    __tablename__ = "agent_reviews"

    id: Mapped[str] = mapped_column(primary_key=True)
    agent_id: Mapped[str] = mapped_column(index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(default="anonymous")
    rating: Mapped[float] = mapped_column(nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


# ============================================
# In-Memory Fallback (for testing/development)
# ============================================

# These are kept for backward compatibility and testing
# In production with database, these should remain empty
_agent_store: Dict[str, Dict[str, Any]] = {}
_review_store: Dict[str, list] = {}
_installed_agents: Dict[str, Dict[str, Any]] = {}

# Public aliases for backward compatibility
agent_store = _agent_store
review_store = _review_store
installed_agents = _installed_agents

# Flag to control storage mode
_USE_DATABASE = True


def set_storage_mode(use_database: bool):
    """Set storage mode (database vs in-memory)"""
    global _USE_DATABASE
    _USE_DATABASE = use_database


# ============================================
# Sync Interface (for backward compatibility)
# ============================================

def clear_all():
    """Clear all stores (useful for testing)"""
    global _agent_store, _review_store, _installed_agents
    _agent_store.clear()
    _review_store.clear()
    _installed_agents.clear()


def get_agent(agent_id: str) -> Optional[Dict[str, Any]]:
    """Get agent by ID (sync, uses in-memory fallback)"""
    return _agent_store.get(agent_id)


def save_agent(agent_id: str, data: Dict[str, Any]) -> None:
    """Save agent data (sync, uses in-memory fallback)"""
    _agent_store[agent_id] = data


def delete_agent(agent_id: str) -> bool:
    """Delete agent (sync, uses in-memory fallback)"""
    if agent_id in _agent_store:
        del _agent_store[agent_id]
        return True
    return False


def list_agents() -> List[Dict[str, Any]]:
    """List all agents (sync, uses in-memory fallback)"""
    return list(_agent_store.values())


# ============================================
# Async Interface (Database-backed)
# ============================================

async def async_get_agent(agent_id: str, db: Optional[AsyncSession] = None) -> Optional[Dict[str, Any]]:
    """
    Get agent by ID from database.

    Args:
        agent_id: Agent identifier
        db: Optional database session

    Returns:
        Agent data dict or None if not found
    """
    if db is None:
        async with async_session() as session:
            return await _async_get_agent_impl(agent_id, session)
    return await _async_get_agent_impl(agent_id, db)


async def _async_get_agent_impl(agent_id: str, db: AsyncSession) -> Optional[Dict[str, Any]]:
    """Implementation of async_get_agent"""
    result = await db.execute(
        select(AgentRegistration).where(AgentRegistration.id == agent_id)
    )
    agent = result.scalar_one_or_none()

    if agent is None:
        return None

    return _agent_model_to_dict(agent)


async def async_save_agent(agent_id: str, data: Dict[str, Any], db: Optional[AsyncSession] = None) -> None:
    """
    Save agent data to database.

    Args:
        agent_id: Agent identifier
        data: Agent data dictionary
        db: Optional database session
    """
    if db is None:
        async with async_session() as session:
            await _async_save_agent_impl(agent_id, data, session)
            await session.commit()
    else:
        await _async_save_agent_impl(agent_id, data, db)


async def _async_save_agent_impl(agent_id: str, data: Dict[str, Any], db: AsyncSession) -> None:
    """Implementation of async_save_agent"""
    # Check if agent exists
    result = await db.execute(
        select(AgentRegistration).where(AgentRegistration.id == agent_id)
    )
    existing = result.scalar_one_or_none()

    manifest = data.get("manifest", {})

    if existing:
        # Update existing
        existing.name = data.get("name", manifest.get("name", ""))
        existing.version = data.get("version", manifest.get("version", "1.0.0"))
        existing.manifest = manifest
        existing.status = data.get("status", "active")
        existing.endpoint = data.get("endpoint")
        existing.last_heartbeat = data.get("last_heartbeat")
    else:
        # Create new
        new_agent = AgentRegistration(
            id=agent_id,
            name=data.get("name", manifest.get("name", "")),
            version=data.get("version", manifest.get("version", "1.0.0")),
            manifest=manifest,
            status=data.get("status", "active"),
            endpoint=data.get("endpoint"),
            last_heartbeat=data.get("last_heartbeat"),
        )
        db.add(new_agent)


async def async_delete_agent(agent_id: str, db: Optional[AsyncSession] = None) -> bool:
    """
    Delete agent from database.

    Args:
        agent_id: Agent identifier
        db: Optional database session

    Returns:
        True if deleted, False if not found
    """
    if db is None:
        async with async_session() as session:
            result = await _async_delete_agent_impl(agent_id, session)
            await session.commit()
            return result
    return await _async_delete_agent_impl(agent_id, db)


async def _async_delete_agent_impl(agent_id: str, db: AsyncSession) -> bool:
    """Implementation of async_delete_agent"""
    result = await db.execute(
        delete(AgentRegistration).where(AgentRegistration.id == agent_id)
    )
    return result.rowcount > 0


async def async_list_agents(
    category: Optional[str] = None,
    capability: Optional[str] = None,
    tag: Optional[str] = None,
    query: Optional[str] = None,
    db: Optional[AsyncSession] = None
) -> List[Dict[str, Any]]:
    """
    List agents from database with optional filters.

    Args:
        category: Filter by category
        capability: Filter by capability
        tag: Filter by tag
        query: Search query
        db: Optional database session

    Returns:
        List of agent data dictionaries
    """
    if db is None:
        async with async_session() as session:
            return await _async_list_agents_impl(category, capability, tag, query, session)
    return await _async_list_agents_impl(category, capability, tag, query, db)


async def _async_list_agents_impl(
    category: Optional[str],
    capability: Optional[str],
    tag: Optional[str],
    query: Optional[str],
    db: AsyncSession
) -> List[Dict[str, Any]]:
    """Implementation of async_list_agents"""
    stmt = select(AgentRegistration)

    # Note: For JSONB field filtering, we need to use PostgreSQL-specific operations
    # For SQLite compatibility in tests, we'll filter in Python

    result = await db.execute(stmt)
    agents = result.scalars().all()

    # Convert to dicts
    agent_dicts = [_agent_model_to_dict(a) for a in agents]

    # Apply filters in Python for cross-database compatibility
    if category:
        agent_dicts = [a for a in agent_dicts if a.get("category") == category]

    if capability:
        agent_dicts = [a for a in agent_dicts if capability in a.get("capabilities", [])]

    if tag:
        agent_dicts = [a for a in agent_dicts if tag in a.get("tags", [])]

    if query:
        q = query.lower()
        agent_dicts = [
            a for a in agent_dicts
            if q in a.get("name", "").lower() or
               (a.get("description") and q in a.get("description", "").lower()) or
               any(q in cap.lower() for cap in a.get("capabilities", []))
        ]

    return agent_dicts


# ============================================
# Install Status Operations (Async)
# ============================================

async def async_is_agent_installed(agent_id: str, db: Optional[AsyncSession] = None) -> bool:
    """Check if agent is installed"""
    if db is None:
        async with async_session() as session:
            return await _async_is_agent_installed_impl(agent_id, session)
    return await _async_is_agent_installed_impl(agent_id, db)


async def _async_is_agent_installed_impl(agent_id: str, db: AsyncSession) -> bool:
    result = await db.execute(
        select(InstalledAgent).where(InstalledAgent.agent_id == agent_id)
    )
    return result.scalar_one_or_none() is not None


async def async_get_install_status(agent_id: str, db: Optional[AsyncSession] = None) -> str:
    """Get agent install status"""
    if db is None:
        async with async_session() as session:
            return await _async_get_install_status_impl(agent_id, session)
    return await _async_get_install_status_impl(agent_id, db)


async def _async_get_install_status_impl(agent_id: str, db: AsyncSession) -> str:
    result = await db.execute(
        select(InstalledAgent).where(InstalledAgent.agent_id == agent_id)
    )
    installed = result.scalar_one_or_none()

    if installed is None:
        return "not_installed"
    return installed.install_status


async def async_install_agent(
    agent_id: str,
    installed_by: str = "anonymous",
    db: Optional[AsyncSession] = None
) -> Dict[str, Any]:
    """Install an agent"""
    if db is None:
        async with async_session() as session:
            result = await _async_install_agent_impl(agent_id, installed_by, session)
            await session.commit()
            return result
    return await _async_install_agent_impl(agent_id, installed_by, db)


async def _async_install_agent_impl(
    agent_id: str,
    installed_by: str,
    db: AsyncSession
) -> Dict[str, Any]:
    now = datetime.utcnow()

    # Check if already installed
    result = await db.execute(
        select(InstalledAgent).where(InstalledAgent.agent_id == agent_id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.install_status = "installed"
        existing.installed_at = now
        existing.installed_by = installed_by
        return {
            "install_status": "installed",
            "installed_at": now.isoformat(),
            "installed_by": installed_by,
        }

    # Create new
    new_install = InstalledAgent(
        agent_id=agent_id,
        install_status="installed",
        installed_at=now,
        installed_by=installed_by,
    )
    db.add(new_install)

    return {
        "install_status": "installed",
        "installed_at": now.isoformat(),
        "installed_by": installed_by,
    }


async def async_uninstall_agent(agent_id: str, db: Optional[AsyncSession] = None) -> bool:
    """Uninstall an agent"""
    if db is None:
        async with async_session() as session:
            result = await _async_uninstall_agent_impl(agent_id, session)
            await session.commit()
            return result
    return await _async_uninstall_agent_impl(agent_id, db)


async def _async_uninstall_agent_impl(agent_id: str, db: AsyncSession) -> bool:
    result = await db.execute(
        delete(InstalledAgent).where(InstalledAgent.agent_id == agent_id)
    )
    return result.rowcount > 0


async def async_disable_agent(agent_id: str, db: Optional[AsyncSession] = None) -> bool:
    """Disable an installed agent"""
    if db is None:
        async with async_session() as session:
            result = await _async_disable_agent_impl(agent_id, session)
            await session.commit()
            return result
    return await _async_disable_agent_impl(agent_id, db)


async def _async_disable_agent_impl(agent_id: str, db: AsyncSession) -> bool:
    result = await db.execute(
        select(InstalledAgent).where(InstalledAgent.agent_id == agent_id)
    )
    installed = result.scalar_one_or_none()

    if installed is None:
        return False

    installed.install_status = "disabled"
    return True


async def async_enable_agent(agent_id: str, db: Optional[AsyncSession] = None) -> bool:
    """Enable a disabled agent"""
    if db is None:
        async with async_session() as session:
            result = await _async_enable_agent_impl(agent_id, session)
            await session.commit()
            return result
    return await _async_enable_agent_impl(agent_id, db)


async def _async_enable_agent_impl(agent_id: str, db: AsyncSession) -> bool:
    result = await db.execute(
        select(InstalledAgent).where(InstalledAgent.agent_id == agent_id)
    )
    installed = result.scalar_one_or_none()

    if installed is None:
        return False

    installed.install_status = "installed"
    return True


async def async_list_installed_agents(db: Optional[AsyncSession] = None) -> List[Dict[str, Any]]:
    """List all installed agents"""
    if db is None:
        async with async_session() as session:
            return await _async_list_installed_agents_impl(session)
    return await _async_list_installed_agents_impl(db)


async def _async_list_installed_agents_impl(db: AsyncSession) -> List[Dict[str, Any]]:
    result = await db.execute(select(InstalledAgent))
    installed = result.scalars().all()

    return [
        {
            "agent_id": item.agent_id,
            "install_status": item.install_status,
            "installed_at": item.installed_at.isoformat() if item.installed_at else None,
            "installed_by": item.installed_by,
        }
        for item in installed
    ]


# ============================================
# Review Operations (Async)
# ============================================

async def async_get_agent_reviews(
    agent_id: str,
    db: Optional[AsyncSession] = None
) -> List[Dict[str, Any]]:
    """Get reviews for an agent"""
    if db is None:
        async with async_session() as session:
            return await _async_get_agent_reviews_impl(agent_id, session)
    return await _async_get_agent_reviews_impl(agent_id, db)


async def _async_get_agent_reviews_impl(agent_id: str, db: AsyncSession) -> List[Dict[str, Any]]:
    result = await db.execute(
        select(AgentReview).where(AgentReview.agent_id == agent_id)
    )
    reviews = result.scalars().all()

    return [
        {
            "id": review.id,
            "agent_id": review.agent_id,
            "user_id": review.user_id,
            "rating": review.rating,
            "comment": review.comment,
            "created_at": review.created_at.isoformat() if review.created_at else None,
        }
        for review in reviews
    ]


async def async_add_review(
    agent_id: str,
    user_id: str,
    rating: float,
    comment: Optional[str] = None,
    db: Optional[AsyncSession] = None
) -> Dict[str, Any]:
    """Add a review for an agent"""
    import uuid

    if db is None:
        async with async_session() as session:
            result = await _async_add_review_impl(agent_id, user_id, rating, comment, session)
            await session.commit()
            return result
    return await _async_add_review_impl(agent_id, user_id, rating, comment, db)


async def _async_add_review_impl(
    agent_id: str,
    user_id: str,
    rating: float,
    comment: Optional[str],
    db: AsyncSession
) -> Dict[str, Any]:
    import uuid

    now = datetime.utcnow()
    review_id = str(uuid.uuid4())

    new_review = AgentReview(
        id=review_id,
        agent_id=agent_id,
        user_id=user_id,
        rating=rating,
        comment=comment,
        created_at=now,
    )
    db.add(new_review)

    return {
        "id": review_id,
        "agent_id": agent_id,
        "user_id": user_id,
        "rating": rating,
        "comment": comment,
        "created_at": now.isoformat(),
    }


# ============================================
# Legacy Sync Interface (Backward Compatibility)
# ============================================

def register_agent(agent_id: str, data: Dict[str, Any]):
    """Register or update an agent (sync, in-memory only)"""
    _agent_store[agent_id] = data


def unregister_agent(agent_id: str):
    """Unregister an agent (sync, in-memory only)"""
    if agent_id in _agent_store:
        del _agent_store[agent_id]


def is_agent_installed(agent_id: str) -> bool:
    """Check if agent is installed (sync, in-memory only)"""
    return agent_id in _installed_agents


def get_install_status(agent_id: str) -> str:
    """Get agent install status (sync, in-memory only)"""
    if agent_id not in _installed_agents:
        return "not_installed"
    return _installed_agents[agent_id].get("install_status", "not_installed")


def install_agent(agent_id: str, installed_by: str = "anonymous"):
    """Install an agent (sync, in-memory only)"""
    from datetime import datetime
    _installed_agents[agent_id] = {
        "install_status": "installed",
        "installed_at": datetime.utcnow().isoformat(),
        "installed_by": installed_by,
    }


def uninstall_agent(agent_id: str):
    """Uninstall an agent (sync, in-memory only)"""
    if agent_id in _installed_agents:
        del _installed_agents[agent_id]


def disable_agent(agent_id: str):
    """Disable an installed agent (sync, in-memory only)"""
    if agent_id in _installed_agents:
        _installed_agents[agent_id]["install_status"] = "disabled"


def enable_agent(agent_id: str):
    """Enable a disabled agent (sync, in-memory only)"""
    if agent_id in _installed_agents:
        _installed_agents[agent_id]["install_status"] = "installed"


# ============================================
# Helper Functions
# ============================================

def _agent_model_to_dict(agent: AgentRegistration) -> Dict[str, Any]:
    """Convert AgentRegistration model to dictionary"""
    manifest = agent.manifest or {}

    return {
        "id": agent.id,
        "agent_id": agent.id,  # Use id as agent_id for compatibility
        "name": agent.name,
        "version": agent.version,
        "manifest": manifest,
        "description": manifest.get("description"),
        "author": manifest.get("author"),
        "category": manifest.get("category", "general"),
        "tags": manifest.get("tags", []),
        "capabilities": manifest.get("capabilities", []),
        "tools": manifest.get("tools", []),
        "input_schema": manifest.get("input_schema"),
        "output_schema": manifest.get("output_schema"),
        "endpoints": manifest.get("endpoints"),
        "auth": manifest.get("auth"),
        "pricing": manifest.get("pricing"),
        "metadata": manifest.get("metadata"),
        "endpoint": agent.endpoint,
        "visibility": manifest.get("visibility", "public"),
        "status": agent.status,
        "rating": manifest.get("rating", 0.0),
        "downloads": manifest.get("downloads", 0),
        "created_at": agent.created_at.isoformat() if agent.created_at else "",
        "updated_at": agent.updated_at.isoformat() if agent.updated_at else "",
        "last_heartbeat": agent.last_heartbeat.isoformat() if agent.last_heartbeat else None,
    }
