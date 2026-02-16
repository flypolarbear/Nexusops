"""
NexusOps Backend - CI/CD API Router

BE-003: CI/CD 集成 API
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.services.cicd import (
    CICDProvider,
    get_cicd_provider,
    BuildInfo,
    BuildStatus,
    BuildTrigger,
)

router = APIRouter(prefix="/cicd", tags=["cicd"])


# ============================================
# Request/Response Models
# ============================================

class TriggerBuildRequest(BaseModel):
    project: str
    branch: str = "main"
    parameters: Optional[dict] = None


class BuildResponse(BaseModel):
    build_id: str
    status: str
    url: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[int] = None
    commit_sha: Optional[str] = None
    branch: Optional[str] = None
    message: Optional[str] = None

    @classmethod
    def from_build_info(cls, info: BuildInfo) -> "BuildResponse":
        return cls(
            build_id=info.build_id,
            status=info.status.value,
            url=info.url,
            started_at=info.started_at.isoformat() if info.started_at else None,
            completed_at=info.completed_at.isoformat() if info.completed_at else None,
            duration_seconds=info.duration_seconds,
            commit_sha=info.commit_sha,
            branch=info.branch,
            message=info.message,
        )


class BuildLogsResponse(BaseModel):
    build_id: str
    logs: str
    tail_lines: int


# ============================================
# Dependencies
# ============================================

def get_cicd() -> CICDProvider:
    """Get CI/CD provider instance"""
    # TODO: Get config from settings
    return get_cicd_provider("mock", {})


# ============================================
# API Endpoints
# ============================================

@router.post("/builds", response_model=BuildResponse)
async def trigger_build(
    request: TriggerBuildRequest,
    cicd: CICDProvider = Depends(get_cicd),
):
    """
    触发 CI/CD 构建

    - **project**: 项目名称 (如: my-project, owner/repo)
    - **branch**: 分支名称 (默认: main)
    - **parameters**: 构建参数 (可选)
    """
    try:
        trigger = BuildTrigger(
            project=request.project,
            branch=request.branch,
            parameters=request.parameters,
        )
        build_info = await cicd.trigger_build(trigger)
        return BuildResponse.from_build_info(build_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/builds/{build_id}", response_model=BuildResponse)
async def get_build_status(
    build_id: str,
    cicd: CICDProvider = Depends(get_cicd),
):
    """
    获取构建状态

    - **build_id**: 构建 ID
    """
    try:
        build_info = await cicd.get_build_status(build_id)
        return BuildResponse.from_build_info(build_info)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/builds/{build_id}/logs", response_model=BuildLogsResponse)
async def get_build_logs(
    build_id: str,
    tail_lines: int = Query(100, ge=1, le=1000),
    cicd: CICDProvider = Depends(get_cicd),
):
    """
    获取构建日志

    - **build_id**: 构建 ID
    - **tail_lines**: 返回的行数 (默认: 100)
    """
    try:
        logs = await cicd.get_build_logs(build_id, tail_lines)
        return BuildLogsResponse(
            build_id=build_id,
            logs=logs,
            tail_lines=tail_lines,
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/builds/{build_id}/abort", response_model=BuildResponse)
async def abort_build(
    build_id: str,
    cicd: CICDProvider = Depends(get_cicd),
):
    """
    中止构建

    - **build_id**: 构建 ID
    """
    try:
        success = await cicd.abort_build(build_id)
        if success:
            build_info = await cicd.get_build_status(build_id)
            return BuildResponse.from_build_info(build_info)
        raise HTTPException(status_code=400, detail="Failed to abort build")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project}/builds")
async def list_builds(
    project: str,
    limit: int = Query(10, ge=1, le=100),
    cicd: CICDProvider = Depends(get_cicd),
):
    """
    列出项目的构建历史

    - **project**: 项目名称
    - **limit**: 返回数量 (默认: 10)
    """
    try:
        builds = await cicd.list_builds(project, limit)
        return {
            "project": project,
            "builds": [BuildResponse.from_build_info(b) for b in builds],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
