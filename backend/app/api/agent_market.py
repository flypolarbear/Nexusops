"""
NexusOps Backend - Agent Market API

MK-001: Agent 注册中心
- Agent 注册/注销
- 能力发现与搜索
- 版本管理
- 健康检查
"""

from datetime import datetime
from typing import Any, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.database import AgentRegistration

router = APIRouter(prefix="/market", tags=["agent-market"])


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


# ============================================
# In-Memory Store (for demo)
# ============================================

# In production, use database
_agent_store: dict[str, dict] = {}
_review_store: dict[str, list[dict]] = {}


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
):
    """
    列出所有公开的 Agent

    - **query**: 搜索关键词
    - **category**: 分类过滤
    - **capability**: 能力过滤
    - **tag**: 标签过滤
    - **sort_by**: 排序方式 (popularity, rating, newest)
    """
    agents = list(_agent_store.values())

    # 过滤
    if query:
        q = query.lower()
        agents = [
            a for a in agents
            if q in a["name"].lower() or
               (a.get("description") and q in a["description"].lower()) or
               any(q in cap.lower() for cap in a.get("capabilities", []))
        ]

    if category:
        agents = [a for a in agents if a.get("category") == category]

    if capability:
        agents = [a for a in agents if capability in a.get("capabilities", [])]

    if tag:
        agents = [a for a in agents if tag in a.get("tags", [])]

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
):
    """
    注册新的 Agent

    - **manifest**: Agent 元数据
    - **endpoint**: Agent 服务端点
    - **visibility**: 可见性 (public, private, organization)
    """
    agent_id = request.manifest.agent_id

    # 检查是否已存在
    if agent_id in _agent_store:
        # 更新
        existing = _agent_store[agent_id]
        existing["manifest"] = request.manifest.model_dump()
        existing["endpoint"] = request.endpoint
        existing["visibility"] = request.visibility
        existing["updated_at"] = datetime.utcnow().isoformat()
        existing["status"] = "active"
        return _to_detail_response(existing)

    # 创建新 Agent
    now = datetime.utcnow().isoformat()
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

    _agent_store[agent_id] = agent
    return _to_detail_response(agent)


@router.get("/{agent_id}", response_model=AgentDetailResponse)
async def get_agent(agent_id: str):
    """
    获取 Agent 详情
    """
    if agent_id not in _agent_store:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent = _agent_store[agent_id]

    # 增加下载/查看计数
    agent["downloads"] = agent.get("downloads", 0) + 1

    return _to_detail_response(agent)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_agent(agent_id: str):
    """
    注销 Agent
    """
    if agent_id not in _agent_store:
        raise HTTPException(status_code=404, detail="Agent not found")

    del _agent_store[agent_id]
    return None


@router.post("/{agent_id}/heartbeat")
async def agent_heartbeat(agent_id: str):
    """
    Agent 心跳

    Agent 应定期发送心跳以表明自己仍在运行
    """
    if agent_id not in _agent_store:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent = _agent_store[agent_id]
    agent["last_heartbeat"] = datetime.utcnow().isoformat()
    agent["status"] = "active"

    return {"status": "ok"}


@router.get("/{agent_id}/reviews")
async def get_agent_reviews(
    agent_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
):
    """
    获取 Agent 评价
    """
    if agent_id not in _agent_store:
        raise HTTPException(status_code=404, detail="Agent not found")

    reviews = _review_store.get(agent_id, [])

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
):
    """
    提交 Agent 评价
    """
    if agent_id not in _agent_store:
        raise HTTPException(status_code=404, detail="Agent not found")

    if agent_id not in _review_store:
        _review_store[agent_id] = []

    review = {
        "id": str(uuid.uuid4()),
        "agent_id": agent_id,
        "user_id": "anonymous",  # TODO: get from auth
        "rating": request.rating,
        "comment": request.comment,
        "created_at": datetime.utcnow().isoformat(),
    }

    _review_store[agent_id].append(review)

    # 更新 Agent 平均评分
    reviews = _review_store[agent_id]
    avg_rating = sum(r["rating"] for r in reviews) / len(reviews)
    _agent_store[agent_id]["rating"] = round(avg_rating, 1)

    return review


@router.get("/categories")
async def list_categories():
    """
    列出所有 Agent 分类
    """
    categories = {}

    for agent in _agent_store.values():
        cat = agent.get("category", "general")
        if cat not in categories:
            categories[cat] = {"name": cat, "count": 0}
        categories[cat]["count"] += 1

    return {
        "categories": list(categories.values())
    }


@router.get("/capabilities")
async def list_capabilities():
    """
    列出所有 Agent 能力
    """
    capabilities = {}

    for agent in _agent_store.values():
        for cap in agent.get("capabilities", []):
            if cap not in capabilities:
                capabilities[cap] = {"name": cap, "count": 0}
            capabilities[cap]["count"] += 1

    return {
        "capabilities": list(capabilities.values())
    }


# ============================================
# Helper Functions
# ============================================

def _to_response(agent: dict) -> AgentResponse:
    """转换为响应模型"""
    manifest = agent.get("manifest", {})
    return AgentResponse(
        agent_id=agent["agent_id"],
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
