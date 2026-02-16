"""
NexusOps Backend - Projects API Router

Implements BE-001: 版本管理 API
"""

from datetime import datetime
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.database import Project, Version, Deployment
from app.models.schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectDetail,
    VersionCreate,
    VersionUpdate,
    VersionResponse,
    VersionDetail,
    PaginatedResponse,
)

router = APIRouter(prefix="/projects", tags=["projects"])


# ============================================
# Projects
# ============================================

@router.get("", response_model=PaginatedResponse[ProjectResponse])
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all projects with pagination"""
    query = select(Project)

    if status:
        query = query.where(Project.status == status)

    # Get total count
    count_query = select(func.count()).select_from(Project)
    if status:
        count_query = count_query.where(Project.status == status)
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(Project.created_at.desc())

    result = await db.execute(query)
    projects = result.scalars().all()

    return PaginatedResponse(
        items=[ProjectResponse.model_validate(p) for p in projects],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new project"""
    # Check if name already exists
    existing = await db.execute(
        select(Project).where(Project.name == data.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project with this name already exists"
        )

    project = Project(
        id=f"proj-{uuid.uuid4().hex[:8]}",
        name=data.name,
        description=data.description,
        git_repo=data.git_repo,
        status="active",
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    return project


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get project details with versions"""
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.versions))
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get version count
    version_count = len(project.versions)

    return ProjectDetail(
        **{c.name: getattr(project, c.name) for c in project.__table__.columns},
        versions=[VersionResponse.model_validate(v) for v in project.versions],
        version_count=version_count,
    )


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update project"""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)

    await db.commit()
    await db.refresh(project)

    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete project"""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    await db.delete(project)
    await db.commit()


# ============================================
# Versions
# ============================================

@router.get("/{project_id}/versions", response_model=PaginatedResponse[VersionResponse])
async def list_versions(
    project_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List versions for a project"""
    # Check project exists
    project = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    if not project.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    query = select(Version).where(Version.project_id == project_id)

    if status:
        query = query.where(Version.status == status)

    # Get total count
    count_query = select(func.count()).select_from(Version).where(Version.project_id == project_id)
    if status:
        count_query = count_query.where(Version.status == status)
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(Version.created_at.desc())

    result = await db.execute(query)
    versions = result.scalars().all()

    return PaginatedResponse(
        items=[VersionResponse.model_validate(v) for v in versions],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post("/{project_id}/versions", response_model=VersionResponse, status_code=status.HTTP_201_CREATED)
async def create_version(
    project_id: str,
    data: VersionCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new version"""
    # Check project exists
    project = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    if not project.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    version = Version(
        id=f"ver-{uuid.uuid4().hex[:8]}",
        project_id=project_id,
        codename=data.codename,
        version=data.version,
        git_branch=data.git_branch,
        git_commit=data.git_commit,
        status="building",
        health="unknown",
        deployed_regions=[],
    )
    db.add(version)
    await db.commit()
    await db.refresh(version)

    return version


@router.get("/versions/{version_id}", response_model=VersionDetail)
async def get_version(
    version_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get version details with deployments"""
    result = await db.execute(
        select(Version)
        .where(Version.id == version_id)
        .options(selectinload(Version.deployments))
    )
    version = result.scalar_one_or_none()

    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    from app.models.schemas import DeploymentResponse
    return VersionDetail(
        **{c.name: getattr(version, c.name) for c in version.__table__.columns},
        deployments=[DeploymentResponse.model_validate(d) for d in version.deployments],
    )


@router.patch("/versions/{version_id}", response_model=VersionResponse)
async def update_version(
    version_id: str,
    data: VersionUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update version"""
    result = await db.execute(
        select(Version).where(Version.id == version_id)
    )
    version = result.scalar_one_or_none()

    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(version, key, value)

    await db.commit()
    await db.refresh(version)

    return version
