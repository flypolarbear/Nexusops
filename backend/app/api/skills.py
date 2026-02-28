"""
NexusOps - Skills API

API endpoints for skill management and sync from skills.sh marketplace.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.database import AgentSkill, AgentSkillBinding
from app.services.skill_sync import (
    SkillSyncService,
    SkillSyncError,
    SkillParseError,
    parse_skill_id,
)


router = APIRouter(prefix="/skills", tags=["skills"])


# ============================================
# Request/Response Models
# ============================================

class SkillSyncRequest(BaseModel):
    """Request to sync a skill from GitHub"""
    owner: str = Field(..., description="GitHub owner/organization")
    repo: str = Field(..., description="Repository name")
    skill_path: str = Field("", description="Path to skill directory (empty if at root)")
    branch: str = Field("main", description="Git branch")


class RepoSyncRequest(BaseModel):
    """Request to sync all skills from a repo"""
    owner: str = Field(..., description="GitHub owner/organization")
    repo: str = Field(..., description="Repository name")
    branch: str = Field("main", description="Git branch")


class SkillBindRequest(BaseModel):
    """Request to bind a skill to an agent"""
    skill_id: str = Field(..., description="Skill ID (owner/repo/skill-name)")
    agent_id: str = Field(..., description="Agent ID to bind to")
    priority: int = Field(0, description="Binding priority (higher = more important)")


class SkillResponse(BaseModel):
    """Response model for a single skill"""
    id: str
    name: str
    description: str
    source_repo: str
    source_url: Optional[str]
    license: Optional[str]
    compatibility: Optional[str]
    status: str
    install_count: int
    
    class Config:
        from_attributes = True


class SkillDetailResponse(SkillResponse):
    """Detailed response with full content"""
    content: str
    frontmatter: dict
    skill_metadata: Optional[dict]


class SkillBindingResponse(BaseModel):
    """Response for skill binding"""
    id: str
    agent_id: str
    skill_id: str
    enabled: bool
    priority: int


class SyncResultResponse(BaseModel):
    """Response for sync operation"""
    success: bool
    synced_count: int
    skills: List[SkillResponse]
    errors: List[str] = []


# ============================================
# Dependency
# ============================================

async def get_sync_service() -> SkillSyncService:
    """Get skill sync service with database session"""
    async with async_session() as session:
        service = SkillSyncService(session)
        try:
            yield service
        finally:
            await service.close()


# ============================================
# API Endpoints
# ============================================

@router.get("", response_model=List[SkillResponse])
async def list_skills(
    status: Optional[str] = Query(None, description="Filter by status"),
    source_repo: Optional[str] = Query(None, description="Filter by source repo"),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(async_session)
):
    """
    List all available skills.
    
    Returns skills sorted by install count (most popular first).
    """
    service = SkillSyncService(session)
    skills = await service.list_skills(status=status, source_repo=source_repo, limit=limit)
    await service.close()
    return skills


@router.get("/{skill_id:path}", response_model=SkillDetailResponse)
async def get_skill(
    skill_id: str,
    session: AsyncSession = Depends(async_session)
):
    """
    Get detailed information about a specific skill.
    
    Includes full SKILL.md content and parsed frontmatter.
    """
    from sqlalchemy import select
    
    stmt = select(AgentSkill).where(AgentSkill.id == skill_id)
    result = await session.execute(stmt)
    skill = result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill not found: {skill_id}")
    
    return skill


@router.post("/sync", response_model=SyncResultResponse)
async def sync_skill(
    request: SkillSyncRequest,
    session: AsyncSession = Depends(async_session)
):
    """
    Sync a single skill from GitHub.
    
    Fetches SKILL.md from the specified repository and creates/updates
    the skill in the local registry.
    """
    service = SkillSyncService(session)
    errors = []
    synced = []
    
    try:
        skill = await service.sync_skill(
            owner=request.owner,
            repo=request.repo,
            skill_path=request.skill_path,
            branch=request.branch
        )
        synced.append(skill)
    except (SkillSyncError, SkillParseError) as e:
        errors.append(str(e))
    
    await service.close()
    
    return SyncResultResponse(
        success=len(synced) > 0,
        synced_count=len(synced),
        skills=synced,
        errors=errors
    )


@router.post("/sync-repo", response_model=SyncResultResponse)
async def sync_repo(
    request: RepoSyncRequest,
    session: AsyncSession = Depends(async_session)
):
    """
    Sync all skills from a GitHub repository.
    
    Scans the repository for SKILL.md files and syncs all found skills.
    """
    service = SkillSyncService(session)
    errors = []
    
    try:
        skills = await service.sync_repo(
            owner=request.owner,
            repo=request.repo,
            branch=request.branch
        )
    except SkillSyncError as e:
        errors.append(str(e))
        skills = []
    
    await service.close()
    
    return SyncResultResponse(
        success=len(skills) > 0,
        synced_count=len(skills),
        skills=skills,
        errors=errors
    )


@router.post("/bind", response_model=SkillBindingResponse)
async def bind_skill(
    request: SkillBindRequest,
    session: AsyncSession = Depends(async_session)
):
    """
    Bind a skill to an agent.
    
    Associates a skill with a specific agent, making it available
    when that agent processes requests.
    """
    # Verify skill exists
    from sqlalchemy import select
    
    stmt = select(AgentSkill).where(AgentSkill.id == request.skill_id)
    result = await session.execute(stmt)
    skill = result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill not found: {request.skill_id}")
    
    service = SkillSyncService(session)
    binding = await service.bind_skill_to_agent(
        skill_id=request.skill_id,
        agent_id=request.agent_id,
        priority=request.priority
    )
    await service.close()
    
    # Update install count
    skill.install_count += 1
    await session.commit()
    
    return binding


@router.delete("/bind/{binding_id:path}", response_model=dict)
async def unbind_skill(
    binding_id: str,
    session: AsyncSession = Depends(async_session)
):
    """
    Remove a skill binding from an agent.
    """
    from sqlalchemy import select, delete
    
    stmt = select(AgentSkillBinding).where(AgentSkillBinding.id == binding_id)
    result = await session.execute(stmt)
    binding = result.scalar_one_or_none()
    
    if not binding:
        raise HTTPException(status_code=404, detail=f"Binding not found: {binding_id}")
    
    await session.execute(delete(AgentSkillBinding).where(AgentSkillBinding.id == binding_id))
    await session.commit()
    
    return {"success": True, "message": f"Binding {binding_id} removed"}


@router.get("/agent/{agent_id:path}", response_model=List[SkillResponse])
async def get_agent_skills(
    agent_id: str,
    session: AsyncSession = Depends(async_session)
):
    """
    Get all skills bound to a specific agent.
    
    Returns skills sorted by priority (highest first).
    """
    service = SkillSyncService(session)
    skills = await service.get_skills_for_agent(agent_id)
    await service.close()
    return skills


@router.delete("/{skill_id:path}", response_model=dict)
async def delete_skill(
    skill_id: str,
    session: AsyncSession = Depends(async_session)
):
    """
    Delete a skill from the registry.
    
    Also removes all bindings for this skill.
    """
    from sqlalchemy import select, delete
    
    # Check skill exists
    stmt = select(AgentSkill).where(AgentSkill.id == skill_id)
    result = await session.execute(stmt)
    skill = result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill not found: {skill_id}")
    
    # Delete bindings first
    await session.execute(delete(AgentSkillBinding).where(AgentSkillBinding.skill_id == skill_id))
    
    # Delete skill
    await session.execute(delete(AgentSkill).where(AgentSkill.id == skill_id))
    await session.commit()
    
    return {"success": True, "message": f"Skill {skill_id} deleted"}
