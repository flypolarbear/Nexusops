"""
NexusOps Backend - Overview API

Dashboard statistics and overview data.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(tags=["overview"])


class OverviewStats(BaseModel):
    """Overview statistics response"""
    services: dict
    clusters: dict
    alerts: dict
    deployments: dict
    resources: dict


@router.get("/overview", response_model=OverviewStats)
async def get_overview():
    """
    Get infrastructure overview statistics.

    Returns aggregate stats for the dashboard.
    """
    # TODO: Replace with real data from database/monitoring systems
    return OverviewStats(
        services={
            "total": 24,
            "healthy": 22,
            "warning": 1,
            "critical": 1,
        },
        clusters={
            "total": 10,
            "healthy": 8,
            "warning": 1,
            "critical": 1,
        },
        alerts={
            "total": 3,
            "critical": 1,
            "warning": 1,
            "info": 1,
        },
        deployments={
            "total": 15,
            "success": 12,
            "running": 2,
            "failed": 1,
        },
        resources={
            "cpu_cores_used": 4200,
            "cpu_cores_total": 6500,
            "memory_tb_used": 12.5,
            "memory_tb_total": 16,
            "storage_tb_used": 4.5,
            "storage_tb_total": 10,
            "network_gbps_used": 32,
            "network_gbps_total": 100,
        }
    )
