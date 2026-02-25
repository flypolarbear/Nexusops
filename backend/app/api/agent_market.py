"""
NexusOps Backend - Agent Market API

MK-001: Agent 注册中心
- Agent 注册/注销
- 能力发现与搜索
- 版本管理
- 健康检查

MK-008: 第三方 Agent 最小闭环
- 安装/卸载状态管理
- 启停控制

Database Migration: Now uses SQLAlchemy async database storage
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.database import AgentRegistration
from app.stores.agent_store import (
    # Legacy in-memory stores (kept for backward compatibility)
    agent_store as _agent_store,
    review_store as _review_store,
    installed_agents as _installed_agents,
    # New async database functions
    async_get_agent,
    async_save_agent,
    async_delete_agent,
    async_list_agents,
    async_is_agent_installed,
    async_get_install_status,
    async_install_agent,
    async_uninstall_agent,
    async_disable_agent,
    async_enable_agent,
    async_list_installed_agents,
    async_get_agent_reviews,
    async_add_review,
)

router = APIRouter(prefix="/market", tags=["agent-market"])


# ============================================
# Install Status Enum
# ============================================

class InstallStatus(str, Enum):
    """Agent 安装状态"""
    NOT_INSTALLED = "not_installed"
    INSTALLED = "installed"
    DISABLED = "disabled"


class AgentStatus(str, Enum):
    """Agent 运行状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


# ============================================
# Request/Response Models
# ============================================

class AgentManifest(BaseModel):
    """Agent Manifest"""
    agent_id: str
    name: str
    version: str
    description: Optional[str] = None
    author: Optional[str] = None
    category: str = "general"
    tags: list[str] = []
    capabilities: list[str] = []
    tools: list[dict] = []
    input_schema: Optional[dict] = None
    output_schema: Optional[dict] = None
    endpoints: Optional[dict] = None
    auth: Optional[dict] = None
    pricing: Optional[dict] = None
    metadata: Optional[dict] = None


class AgentRegisterRequest(BaseModel):
    """Agent 注册请求"""
    manifest: AgentManifest
    endpoint: Optional[str] = None
    auth_token: Optional[str] = None
    visibility: str = "public"  # public, private, organization


class AgentResponse(BaseModel):
    """Agent 响应"""
    agent_id: str
    name: str
    version: str
    description: Optional[str] = None
    author: Optional[str] = None
    category: str
    tags: list[str]
    capabilities: list[str]
    tools_count: int
    visibility: str
    status: str
    endpoint: Optional[str] = None
    rating: float = 0.0
    downloads: int = 0
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class AgentDetailResponse(AgentResponse):
    """Agent 详情响应"""
    tools: list[dict]
    input_schema: Optional[dict] = None
    output_schema: Optional[dict] = None
    endpoints: Optional[dict] = None
    auth: Optional[dict] = None
    pricing: Optional[dict] = None
    metadata: Optional[dict] = None


class AgentSearchRequest(BaseModel):
    """Agent 搜索请求"""
    query: Optional[str] = None
    category: Optional[str] = None
    capability: Optional[str] = None
    tags: Optional[list[str]] = None
    min_rating: Optional[float] = None
    sort_by: str = "popularity"  # popularity, rating, newest
    page: int = 1
    page_size: int = 20


class AgentSearchResponse(BaseModel):
    """Agent 搜索响应"""
    items: list[AgentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AgentReview(BaseModel):
    """Agent 评价"""
    id: str
    agent_id: str
    user_id: str
    rating: float  # 1.0 - 5.0
    comment: Optional[str] = None
    created_at: str


class AgentReviewRequest(BaseModel):
    """Agent 评价请求"""
    rating: float = Field(..., ge=1.0, le=5.0)
    comment: Optional[str] = None


class AgentInstallResponse(BaseModel):
    """Agent 安装响应"""
    agent_id: str
    name: str
    version: str
    install_status: InstallStatus
    installed_at: Optional[str] = None
    message: str


class AgentInstallStatusResponse(BaseModel):
    """Agent 安装状态响应"""
    agent_id: str
    name: str
    version: str
    install_status: InstallStatus
    agent_status: AgentStatus
    installed_at: Optional[str] = None
    last_heartbeat: Optional[str] = None


# ============================================
# API Endpoints
# ============================================

@router.get("", response_model=AgentSearchResponse)
async def list_agents(
    query: Optional[str] = None,
    category: Optional[str] = None,
    capability: Optional[str] = None,
    tag: Optional[str] = None,
    sort_by: str = "popularity",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    列出所有公开的 Agent

    - **query**: 搜索关键词
    - **category**: 分类过滤
    - **capability**: 能力过滤
    - **tag**: 标签过滤
    - **sort_by**: 排序方式 (popularity, rating, newest)
    """
    # Use database-backed storage
    agents = await async_list_agents(
        category=category,
        capability=capability,
        tag=tag,
        query=query,
        db=db,
    )

    # 排序
    if sort_by == "popularity":
        agents.sort(key=lambda a: a.get("downloads", 0), reverse=True)
    elif sort_by == "rating":
        agents.sort(key=lambda a: a.get("rating", 0), reverse=True)
    elif sort_by == "newest":
        agents.sort(key=lambda a: a.get("created_at", ""), reverse=True)

    # 分页
    total = len(agents)
    start = (page - 1) * page_size
    end = start + page_size
    items = agents[start:end]

    return AgentSearchResponse(
        items=[_to_response(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=AgentDetailResponse, status_code=status.HTTP_201_CREATED)
async def register_agent(
    request: AgentRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    注册新的 Agent

    - **manifest**: Agent 元数据
    - **endpoint**: Agent 服务端点
    - **visibility**: 可见性 (public, private, organization)
    """
    agent_id = request.manifest.agent_id
    now = datetime.utcnow().isoformat()

    # Check if agent exists
    existing = await async_get_agent(agent_id, db)

    if existing:
        # Update existing
        existing["manifest"] = request.manifest.model_dump()
        existing["endpoint"] = request.endpoint
        existing["visibility"] = request.visibility
        existing["updated_at"] = now
        existing["status"] = "active"
        existing["name"] = request.manifest.name
        existing["version"] = request.manifest.version
        existing["description"] = request.manifest.description
        existing["author"] = request.manifest.author
        existing["category"] = request.manifest.category
        existing["tags"] = request.manifest.tags
        existing["capabilities"] = request.manifest.capabilities
        existing["tools"] = request.manifest.tools
        existing["input_schema"] = request.manifest.input_schema
        existing["output_schema"] = request.manifest.output_schema
        existing["endpoints"] = request.manifest.endpoints
        existing["auth"] = request.manifest.auth
        existing["pricing"] = request.manifest.pricing
        existing["metadata"] = request.manifest.metadata

        await async_save_agent(agent_id, existing, db)
        await db.commit()
        return _to_detail_response(existing)

    # Create new Agent
    agent = {
        "id": str(uuid.uuid4()),
        "agent_id": agent_id,
        "manifest": request.manifest.model_dump(),
        "name": request.manifest.name,
        "version": request.manifest.version,
        "description": request.manifest.description,
        "author": request.manifest.author,
        "category": request.manifest.category,
        "tags": request.manifest.tags,
        "capabilities": request.manifest.capabilities,
        "tools": request.manifest.tools,
        "input_schema": request.manifest.input_schema,
        "output_schema": request.manifest.output_schema,
        "endpoints": request.manifest.endpoints,
        "auth": request.manifest.auth,
        "pricing": request.manifest.pricing,
        "metadata": request.manifest.metadata,
        "endpoint": request.endpoint,
        "visibility": request.visibility,
        "status": "active",
        "rating": 0.0,
        "downloads": 0,
        "created_at": now,
        "updated_at": now,
    }

    await async_save_agent(agent_id, agent, db)
    await db.commit()
    return _to_detail_response(agent)


# ============================================
# Static Routes (must be before /{agent_id})
# ============================================

@router.get("/categories")
async def list_categories(
    db: AsyncSession = Depends(get_db),
):
    """
    列出所有 Agent 分类
    """
    agents = await async_list_agents(db=db)
    categories = {}

    for agent in agents:
        cat = agent.get("category", "general")
        if cat not in categories:
            categories[cat] = {"name": cat, "count": 0}
        categories[cat]["count"] += 1

    return {
        "categories": list(categories.values())
    }


@router.get("/capabilities")
async def list_capabilities(
    db: AsyncSession = Depends(get_db),
):
    """
    列出所有 Agent 能力
    """
    agents = await async_list_agents(db=db)
    capabilities = {}

    for agent in agents:
        for cap in agent.get("capabilities", []):
            if cap not in capabilities:
                capabilities[cap] = {"name": cap, "count": 0}
            capabilities[cap]["count"] += 1

    return {
        "capabilities": list(capabilities.values())
    }


# ============================================
# MK-008: Install/Uninstall APIs
# ============================================

@router.get("/installed", response_model=list[AgentInstallStatusResponse])
async def list_installed_agents(
    db: AsyncSession = Depends(get_db),
):
    """
    列出所有已安装的 Agent

    返回安装状态为 installed 或 disabled 的 Agent 列表
    """
    installed = []
    installed_list = await async_list_installed_agents(db)

    for install_info in installed_list:
        agent_id = install_info["agent_id"]
        agent = await async_get_agent(agent_id, db)

        if agent:
            installed.append(AgentInstallStatusResponse(
                agent_id=agent_id,
                name=agent.get("name", ""),
                version=agent.get("version", ""),
                install_status=InstallStatus(install_info.get("install_status", "installed")),
                agent_status=AgentStatus(agent.get("status", "active")),
                installed_at=install_info.get("installed_at"),
                last_heartbeat=agent.get("last_heartbeat"),
            ))

    return installed


# ============================================
# Dynamic Routes (with {agent_id})
# ============================================

@router.get("/{agent_id}", response_model=AgentDetailResponse)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    获取 Agent 详情
    """
    agent = await async_get_agent(agent_id, db)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # 增加下载/查看计数
    agent["downloads"] = agent.get("downloads", 0) + 1
    await async_save_agent(agent_id, agent, db)
    await db.commit()

    return _to_detail_response(agent)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    注销 Agent
    """
    agent = await async_get_agent(agent_id, db)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    await async_delete_agent(agent_id, db)
    await db.commit()
    return None


@router.post("/{agent_id}/heartbeat")
async def agent_heartbeat(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Agent 心跳

    Agent 应定期发送心跳以表明自己仍在运行
    """
    agent = await async_get_agent(agent_id, db)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent["last_heartbeat"] = datetime.utcnow().isoformat()
    agent["status"] = "active"

    await async_save_agent(agent_id, agent, db)
    await db.commit()

    return {"status": "ok"}


@router.get("/{agent_id}/reviews")
async def get_agent_reviews(
    agent_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """
    获取 Agent 评价
    """
    agent = await async_get_agent(agent_id, db)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    reviews = await async_get_agent_reviews(agent_id, db)

    start = (page - 1) * page_size
    end = start + page_size

    return {
        "items": reviews[start:end],
        "total": len(reviews),
        "page": page,
        "page_size": page_size,
    }


@router.post("/{agent_id}/reviews", status_code=status.HTTP_201_CREATED)
async def submit_review(
    agent_id: str,
    request: AgentReviewRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    提交 Agent 评价
    """
    agent = await async_get_agent(agent_id, db)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    review = await async_add_review(
        agent_id=agent_id,
        user_id="anonymous",  # TODO: get from auth
        rating=request.rating,
        comment=request.comment,
        db=db,
    )

    # Update agent average rating
    reviews = await async_get_agent_reviews(agent_id, db)
    if reviews:
        avg_rating = sum(r["rating"] for r in reviews) / len(reviews)
        agent["rating"] = round(avg_rating, 1)
        await async_save_agent(agent_id, agent, db)

    await db.commit()
    return review


# ============================================
# Helper Functions
# ============================================

def _to_response(agent: dict) -> AgentResponse:
    """转换为响应模型"""
    manifest = agent.get("manifest", {})
    return AgentResponse(
        agent_id=agent.get("agent_id", agent.get("id", "")),
        name=agent.get("name", manifest.get("name", "")),
        version=agent.get("version", manifest.get("version", "")),
        description=agent.get("description"),
        author=agent.get("author"),
        category=agent.get("category", "general"),
        tags=agent.get("tags", []),
        capabilities=agent.get("capabilities", []),
        tools_count=len(agent.get("tools", [])),
        visibility=agent.get("visibility", "public"),
        status=agent.get("status", "active"),
        endpoint=agent.get("endpoint"),
        rating=agent.get("rating", 0.0),
        downloads=agent.get("downloads", 0),
        created_at=agent.get("created_at", ""),
        updated_at=agent.get("updated_at", ""),
    )


def _to_detail_response(agent: dict) -> AgentDetailResponse:
    """转换为详情响应模型"""
    base = _to_response(agent)
    return AgentDetailResponse(
        **base.model_dump(),
        tools=agent.get("tools", []),
        input_schema=agent.get("input_schema"),
        output_schema=agent.get("output_schema"),
        endpoints=agent.get("endpoints"),
        auth=agent.get("auth"),
        pricing=agent.get("pricing"),
        metadata=agent.get("metadata"),
    )


# ============================================
# MK-008: Install/Uninstall API Endpoints
# ============================================

@router.post("/{agent_id}/install", response_model=AgentInstallResponse)
async def api_install_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    安装 Agent

    将已注册的 Agent 安装到可用列表中，使其可以被调用
    """
    agent = await async_get_agent(agent_id, db)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found in registry"
        )

    # Check if already installed
    install_status = await async_get_install_status(agent_id, db)

    if install_status == InstallStatus.INSTALLED.value:
        installed_list = await async_list_installed_agents(db)
        install_info = next((i for i in installed_list if i["agent_id"] == agent_id), {})
        return AgentInstallResponse(
            agent_id=agent_id,
            name=agent.get("name", ""),
            version=agent.get("version", ""),
            install_status=InstallStatus.INSTALLED,
            installed_at=install_info.get("installed_at"),
            message="Agent is already installed"
        )

    # Perform installation
    install_info = await async_install_agent(agent_id, "anonymous", db)
    await db.commit()

    return AgentInstallResponse(
        agent_id=agent_id,
        name=agent.get("name", ""),
        version=agent.get("version", ""),
        install_status=InstallStatus.INSTALLED,
        installed_at=install_info.get("installed_at"),
        message="Agent installed successfully"
    )


@router.post("/{agent_id}/uninstall", response_model=AgentInstallResponse)
async def api_uninstall_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    卸载 Agent

    从可用列表中移除 Agent，调用将被拒绝
    """
    agent = await async_get_agent(agent_id, db)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found in registry"
        )

    install_status = await async_get_install_status(agent_id, db)

    if install_status == InstallStatus.NOT_INSTALLED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent '{agent_id}' is not installed"
        )

    await async_uninstall_agent(agent_id, db)
    await db.commit()

    return AgentInstallResponse(
        agent_id=agent_id,
        name=agent.get("name", ""),
        version=agent.get("version", ""),
        install_status=InstallStatus.NOT_INSTALLED,
        installed_at=None,
        message="Agent uninstalled successfully"
    )


@router.post("/{agent_id}/enable", response_model=AgentInstallResponse)
async def api_enable_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    启用已安装的 Agent

    将 disabled 状态的 Agent 重新启用
    """
    agent = await async_get_agent(agent_id, db)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found in registry"
        )

    install_status = await async_get_install_status(agent_id, db)

    if install_status == InstallStatus.NOT_INSTALLED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent '{agent_id}' is not installed. Install it first."
        )

    await async_enable_agent(agent_id, db)
    await db.commit()

    installed_list = await async_list_installed_agents(db)
    install_info = next((i for i in installed_list if i["agent_id"] == agent_id), {})

    return AgentInstallResponse(
        agent_id=agent_id,
        name=agent.get("name", ""),
        version=agent.get("version", ""),
        install_status=InstallStatus.INSTALLED,
        installed_at=install_info.get("installed_at"),
        message="Agent enabled successfully"
    )


@router.post("/{agent_id}/disable", response_model=AgentInstallResponse)
async def api_disable_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    禁用已安装的 Agent

    暂时禁用 Agent，调用将被拒绝，但保留安装信息
    """
    agent = await async_get_agent(agent_id, db)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found in registry"
        )

    install_status = await async_get_install_status(agent_id, db)

    if install_status == InstallStatus.NOT_INSTALLED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent '{agent_id}' is not installed. Install it first."
        )

    await async_disable_agent(agent_id, db)
    await db.commit()

    installed_list = await async_list_installed_agents(db)
    install_info = next((i for i in installed_list if i["agent_id"] == agent_id), {})

    return AgentInstallResponse(
        agent_id=agent_id,
        name=agent.get("name", ""),
        version=agent.get("version", ""),
        install_status=InstallStatus.DISABLED,
        installed_at=install_info.get("installed_at"),
        message="Agent disabled successfully"
    )


@router.get("/{agent_id}/install-status", response_model=AgentInstallStatusResponse)
async def api_get_install_status(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    获取 Agent 安装状态
    """
    agent = await async_get_agent(agent_id, db)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found in registry"
        )

    install_status_str = await async_get_install_status(agent_id, db)

    installed_list = await async_list_installed_agents(db)
    install_info = next((i for i in installed_list if i["agent_id"] == agent_id), {})

    return AgentInstallStatusResponse(
        agent_id=agent_id,
        name=agent.get("name", ""),
        version=agent.get("version", ""),
        install_status=InstallStatus(install_status_str),
        agent_status=AgentStatus(agent.get("status", "active")),
        installed_at=install_info.get("installed_at"),
        last_heartbeat=agent.get("last_heartbeat"),
    )
