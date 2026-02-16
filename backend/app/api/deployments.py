"""
NexusOps Backend - Deployments API Router

Implements BE-002: ArgoCD 集成
"""

from datetime import datetime
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.database import Deployment, DeploymentStep, Version
from app.models.schemas import (
    DeploymentCreate,
    DeploymentResponse,
    DeploymentDetail,
    DeploymentStepResponse,
    PaginatedResponse,
)

router = APIRouter(prefix="/deployments", tags=["deployments"])


# ============================================
# Deployments
# ============================================

@router.get("", response_model=PaginatedResponse[DeploymentResponse])
async def list_deployments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    version_id: Optional[str] = None,
    region: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List deployments with filters"""
    query = select(Deployment)

    if version_id:
        query = query.where(Deployment.version_id == version_id)
    if region:
        query = query.where(Deployment.region == region)
    if status:
        query = query.where(Deployment.status == status)

    # Get total count
    count_query = select(func.count()).select_from(Deployment)
    if version_id:
        count_query = count_query.where(Deployment.version_id == version_id)
    if region:
        count_query = count_query.where(Deployment.region == region)
    if status:
        count_query = count_query.where(Deployment.status == status)
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(Deployment.created_at.desc())

    result = await db.execute(query)
    deployments = result.scalars().all()

    return PaginatedResponse(
        items=[DeploymentResponse.model_validate(d) for d in deployments],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=DeploymentResponse, status_code=status.HTTP_201_CREATED)
async def create_deployment(
    data: DeploymentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new deployment"""
    # Check version exists
    version = await db.execute(
        select(Version).where(Version.id == data.version_id)
    )
    if not version.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Version not found")

    deployment = Deployment(
        id=f"dep-{uuid.uuid4().hex[:8]}",
        version_id=data.version_id,
        region=data.region,
        namespace=data.namespace,
        status="pending",
        health="unknown",
        argocd_app=f"{data.version_id}-{data.region}",
    )
    db.add(deployment)
    await db.commit()
    await db.refresh(deployment)

    # Create deployment steps (CI/CD → ArgoCD → Health Check chain)
    steps = [
        DeploymentStep(
            id=f"step-{uuid.uuid4().hex[:8]}",
            deployment_id=deployment.id,
            step_type="ci_build",
            name="CI/CD Build",
            status="pending",
        ),
        DeploymentStep(
            id=f"step-{uuid.uuid4().hex[:8]}",
            deployment_id=deployment.id,
            step_type="argocd_sync",
            name="ArgoCD Sync",
            status="pending",
        ),
        DeploymentStep(
            id=f"step-{uuid.uuid4().hex[:8]}",
            deployment_id=deployment.id,
            step_type="health_check",
            name="Health Check",
            status="pending",
        ),
    ]
    for step in steps:
        db.add(step)
    await db.commit()

    return deployment


@router.get("/{deployment_id}", response_model=DeploymentDetail)
async def get_deployment(
    deployment_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get deployment details with steps"""
    result = await db.execute(
        select(Deployment)
        .where(Deployment.id == deployment_id)
        .options(selectinload(Deployment.steps))
    )
    deployment = result.scalar_one_or_none()

    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")

    return DeploymentDetail(
        **{c.name: getattr(deployment, c.name) for c in deployment.__table__.columns},
        steps=[DeploymentStepResponse.model_validate(s) for s in deployment.steps],
    )


@router.post("/{deployment_id}/sync", response_model=DeploymentResponse)
async def trigger_sync(
    deployment_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Trigger ArgoCD sync for deployment"""
    result = await db.execute(
        select(Deployment).where(Deployment.id == deployment_id)
    )
    deployment = result.scalar_one_or_none()

    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")

    # Update status
    deployment.status = "syncing"
    deployment.argocd_sync_status = "Syncing"

    # Update ArgoCD sync step
    step_result = await db.execute(
        select(DeploymentStep).where(
            DeploymentStep.deployment_id == deployment_id,
            DeploymentStep.step_type == "argocd_sync"
        )
    )
    sync_step = step_result.scalar_one_or_none()
    if sync_step:
        sync_step.status = "running"
        sync_step.started_at = datetime.utcnow()

    await db.commit()
    await db.refresh(deployment)

    return deployment


@router.post("/{deployment_id}/rollback", response_model=DeploymentResponse)
async def trigger_rollback(
    deployment_id: str,
    revision: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """Trigger rollback for deployment"""
    result = await db.execute(
        select(Deployment).where(Deployment.id == deployment_id)
    )
    deployment = result.scalar_one_or_none()

    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")

    # Update status
    deployment.status = "rolling_back"

    await db.commit()
    await db.refresh(deployment)

    return deployment


# ============================================
# Deployment Steps
# ============================================

@router.get("/{deployment_id}/steps")
async def get_deployment_steps(
    deployment_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get deployment steps (CI/CD chain)"""
    result = await db.execute(
        select(DeploymentStep)
        .where(DeploymentStep.deployment_id == deployment_id)
        .order_by(DeploymentStep.created_at)
    )
    steps = result.scalars().all()

    return {"steps": [DeploymentStepResponse.model_validate(s) for s in steps]}
