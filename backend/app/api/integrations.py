"""
Integrations Management API

Provides endpoints for managing external service integrations
(Grafana, ArgoCD, Jenkins, Git providers, etc.)
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/integrations", tags=["integrations"])

# In-memory store for demo (replace with database in production)
_integrations_store: dict = {}

# ============================================
# Models
# ============================================

class IntegrationBase(BaseModel):
    name: str
    type: str  # grafana, argocd, jenkins, gitlab, github, bitbucket
    url: str
    api_token: Optional[str] = None
    username: Optional[str] = None


class IntegrationCreate(IntegrationBase):
    pass


class IntegrationUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    api_token: Optional[str] = None
    username: Optional[str] = None


class IntegrationResponse(BaseModel):
    id: str
    name: str
    type: str
    url: str
    status: str  # connected, disconnected, error
    last_sync: Optional[str] = None
    config: dict
    created_at: str
    updated_at: str


# ============================================
# Helper Functions
# ============================================

def generate_id() -> str:
    import uuid
    return f"int-{uuid.uuid4().hex[:8]}"


def test_connection(integration_type: str, url: str, token: str = None) -> dict:
    """
    Test connection to external service.
    In production, this would actually try to connect.
    """
    # Simulate connection test
    return {
        "success": True,
        "message": f"Successfully connected to {integration_type}",
        "response_time_ms": 150
    }


# ============================================
# Endpoints
# ============================================

@router.get("", response_model=list[IntegrationResponse])
async def list_integrations():
    """List all integrations"""
    return list(_integrations_store.values())


@router.post("", response_model=IntegrationResponse)
async def create_integration(data: IntegrationCreate):
    """Create a new integration"""
    # Validate type
    valid_types = ["grafana", "argocd", "jenkins", "gitlab", "github", "bitbucket"]
    if data.type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid integration type. Must be one of: {valid_types}"
        )

    integration_id = generate_id()
    now = datetime.utcnow().isoformat()

    # Test connection
    test_result = test_connection(data.type, data.url, data.api_token)

    integration = IntegrationResponse(
        id=integration_id,
        name=data.name,
        type=data.type,
        url=data.url,
        status="connected" if test_result["success"] else "error",
        last_sync=now if test_result["success"] else None,
        config={
            "has_token": bool(data.api_token),
            "has_username": bool(data.username),
        },
        created_at=now,
        updated_at=now,
    )

    _integrations_store[integration_id] = integration
    return integration


@router.get("/{integration_id}", response_model=IntegrationResponse)
async def get_integration(integration_id: str):
    """Get integration details"""
    if integration_id not in _integrations_store:
        raise HTTPException(status_code=404, detail="Integration not found")
    return _integrations_store[integration_id]


@router.put("/{integration_id}", response_model=IntegrationResponse)
async def update_integration(integration_id: str, data: IntegrationUpdate):
    """Update an integration"""
    if integration_id not in _integrations_store:
        raise HTTPException(status_code=404, detail="Integration not found")

    existing = _integrations_store[integration_id]

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "api_token" and value:
            existing.config["has_token"] = True
        elif key == "username" and value:
            existing.config["has_username"] = True
        elif hasattr(existing, key):
            setattr(existing, key, value)

    existing.updated_at = datetime.utcnow().isoformat()
    _integrations_store[integration_id] = existing

    return existing


@router.delete("/{integration_id}")
async def delete_integration(integration_id: str):
    """Delete an integration"""
    if integration_id not in _integrations_store:
        raise HTTPException(status_code=404, detail="Integration not found")

    del _integrations_store[integration_id]
    return {"message": "Integration deleted successfully"}


@router.post("/{integration_id}/test")
async def test_integration_connection(integration_id: str):
    """Test connection to an integration"""
    if integration_id not in _integrations_store:
        raise HTTPException(status_code=404, detail="Integration not found")

    integration = _integrations_store[integration_id]
    test_result = test_connection(
        integration.type,
        integration.url,
        integration.config.get("api_token")
    )

    # Update status based on test result
    integration.status = "connected" if test_result["success"] else "error"
    integration.last_sync = datetime.utcnow().isoformat() if test_result["success"] else integration.last_sync
    _integrations_store[integration_id] = integration

    return test_result


@router.post("/{integration_id}/sync")
async def sync_integration(integration_id: str):
    """Sync data from integration"""
    if integration_id not in _integrations_store:
        raise HTTPException(status_code=404, detail="Integration not found")

    integration = _integrations_store[integration_id]

    # Simulate sync
    integration.last_sync = datetime.utcnow().isoformat()
    integration.status = "connected"
    _integrations_store[integration_id] = integration

    return {
        "success": True,
        "message": f"Synced with {integration.name}",
        "synced_at": integration.last_sync,
        "items_synced": 42  # Demo number
    }
