"""
Integrations Management API

Provides endpoints for managing external service integrations
(Grafana, ArgoCD, Jenkins, Git providers, etc.)
"""

import os
import asyncio
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl
from fastapi import APIRouter, HTTPException
import httpx

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


class ConnectionTestResult(BaseModel):
    success: bool
    message: str
    response_time_ms: Optional[int] = None
    version: Optional[str] = None
    error: Optional[str] = None


# ============================================
# Helper Functions
# ============================================

def generate_id() -> str:
    import uuid
    return f"int-{uuid.uuid4().hex[:8]}"


async def test_argocd_connection(url: str, token: str = None) -> ConnectionTestResult:
    """Test ArgoCD connection"""
    import time
    start = time.time()

    # Remove trailing slash
    url = url.rstrip('/')

    # Try different health endpoints
    endpoints = [
        "/healthz",
        "/api/healthz",
        "/api/v1/session/userinfo",
    ]

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient(timeout=10, verify=False) as client:
        for endpoint in endpoints:
            try:
                response = await client.get(f"{url}{endpoint}", headers=headers)
                if response.status_code == 200:
                    latency = int((time.time() - start) * 1000)
                    return ConnectionTestResult(
                        success=True,
                        message="Successfully connected to ArgoCD",
                        response_time_ms=latency,
                        version="unknown"
                    )
            except Exception as e:
                continue

    return ConnectionTestResult(
        success=False,
        message="Failed to connect to ArgoCD server",
        error="Connection refused or timeout"
    )


async def test_k8s_connection() -> ConnectionTestResult:
    """Test Kubernetes connection using kubectl"""
    import time
    start = time.time()

    try:
        # Try to get cluster info
        proc = await asyncio.create_subprocess_exec(
            'kubectl', 'cluster-info',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)

        latency = int((time.time() - start) * 1000)

        if proc.returncode == 0:
            return ConnectionTestResult(
                success=True,
                message="Successfully connected to Kubernetes cluster",
                response_time_ms=latency
            )
        else:
            return ConnectionTestResult(
                success=False,
                message="Kubernetes cluster not accessible",
                error=stderr.decode() if stderr else "Unknown error"
            )
    except FileNotFoundError:
        return ConnectionTestResult(
            success=False,
            message="kubectl not found",
            error="Please install kubectl and configure kubeconfig"
        )
    except asyncio.TimeoutError:
        return ConnectionTestResult(
            success=False,
            message="Kubernetes connection timeout",
            error="Cluster did not respond in time"
        )
    except Exception as e:
        return ConnectionTestResult(
            success=False,
            message="Kubernetes connection failed",
            error=str(e)
        )


async def test_cloudflare_connection(api_token: str) -> ConnectionTestResult:
    """Test Cloudflare API connection"""
    import time
    start = time.time()

    if not api_token:
        return ConnectionTestResult(
            success=False,
            message="Cloudflare API token not configured",
            error="Please provide an API token"
        )

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                "https://api.cloudflare.com/client/v4/user/tokens/verify",
                headers={
                    "Authorization": f"Bearer {api_token}",
                    "Content-Type": "application/json"
                }
            )

            latency = int((time.time() - start) * 1000)

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return ConnectionTestResult(
                        success=True,
                        message="Successfully connected to Cloudflare API",
                        response_time_ms=latency
                    )

            return ConnectionTestResult(
                success=False,
                message="Cloudflare API authentication failed",
                error=f"Status: {response.status_code}"
            )
    except Exception as e:
        return ConnectionTestResult(
            success=False,
            message="Cloudflare connection failed",
            error=str(e)
        )


async def test_jenkins_connection(url: str, username: str, api_token: str) -> ConnectionTestResult:
    """Test Jenkins connection"""
    import time
    start = time.time()

    url = url.rstrip('/')

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{url}/api/json",
                auth=(username, api_token) if username and api_token else None
            )

            latency = int((time.time() - start) * 1000)

            if response.status_code == 200:
                return ConnectionTestResult(
                    success=True,
                    message="Successfully connected to Jenkins",
                    response_time_ms=latency
                )
            elif response.status_code == 401:
                return ConnectionTestResult(
                    success=False,
                    message="Jenkins authentication failed",
                    error="Invalid credentials"
                )
            else:
                return ConnectionTestResult(
                    success=False,
                    message="Jenkins connection failed",
                    error=f"Status: {response.status_code}"
                )
    except Exception as e:
        return ConnectionTestResult(
            success=False,
            message="Jenkins connection failed",
            error=str(e)
        )


async def test_grafana_connection(url: str, api_token: str) -> ConnectionTestResult:
    """Test Grafana connection"""
    import time
    start = time.time()

    url = url.rstrip('/')

    headers = {}
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{url}/api/health", headers=headers)

            latency = int((time.time() - start) * 1000)

            if response.status_code == 200:
                data = response.json()
                return ConnectionTestResult(
                    success=True,
                    message="Successfully connected to Grafana",
                    response_time_ms=latency,
                    version=data.get("version", "unknown")
                )
            else:
                return ConnectionTestResult(
                    success=False,
                    message="Grafana connection failed",
                    error=f"Status: {response.status_code}"
                )
    except Exception as e:
        return ConnectionTestResult(
            success=False,
            message="Grafana connection failed",
            error=str(e)
        )


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

    integration = IntegrationResponse(
        id=integration_id,
        name=data.name,
        type=data.type,
        url=data.url,
        status="not_tested",
        last_sync=None,
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


@router.post("/{integration_id}/test", response_model=ConnectionTestResult)
async def test_integration_connection(integration_id: str):
    """Test connection to an integration"""
    if integration_id not in _integrations_store:
        raise HTTPException(status_code=404, detail="Integration not found")

    integration = _integrations_store[integration_id]

    # Run real connection test based on type
    if integration.type == "argocd":
        result = await test_argocd_connection(
            integration.url,
            integration.config.get("api_token")
        )
    elif integration.type == "jenkins":
        result = await test_jenkins_connection(
            integration.url,
            integration.config.get("username"),
            integration.config.get("api_token")
        )
    elif integration.type == "grafana":
        result = await test_grafana_connection(
            integration.url,
            integration.config.get("api_token")
        )
    else:
        # Generic mock for other types
        result = ConnectionTestResult(
            success=True,
            message=f"Connection to {integration.type} verified (simulated)"
        )

    # Update status based on test result
    integration.status = "connected" if result.success else "error"
    if result.success:
        integration.last_sync = datetime.utcnow().isoformat()
    _integrations_store[integration_id] = integration

    return result


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


# ============================================
# Type-based endpoints (for frontend convenience)
# ============================================

@router.get("/type/{integration_type}")
async def get_integration_by_type(integration_type: str):
    """Get integration by type (e.g., argocd, grafana, jenkins)"""
    # Check environment variables for configured integrations
    config = _get_config_from_env(integration_type)

    # Check store for saved config
    for integration in _integrations_store.values():
        if integration.type == integration_type:
            return integration

    # Return env-based config or default
    return config


@router.post("/type/{integration_type}/test", response_model=ConnectionTestResult)
async def test_integration_by_type(integration_type: str):
    """Test connection by integration type"""

    # First check store for saved config
    saved_config = None
    for integration in _integrations_store.values():
        if integration.type == integration_type:
            saved_config = integration
            break

    # Get config from env or saved
    if saved_config:
        url = saved_config.url
        api_token = saved_config.config.get("api_token")
        username = saved_config.config.get("username")
    else:
        env_config = _get_config_from_env(integration_type)
        url = env_config.get("url", "")
        api_token = env_config.get("api_token")
        username = env_config.get("username")

    # Run appropriate test
    if integration_type == "argocd":
        return await test_argocd_connection(url, api_token)
    elif integration_type == "jenkins":
        return await test_jenkins_connection(url, username, api_token)
    elif integration_type == "grafana":
        return await test_grafana_connection(url, api_token)
    elif integration_type == "kubernetes" or integration_type == "k8s":
        return await test_k8s_connection()
    elif integration_type == "cloudflare":
        return await test_cloudflare_connection(api_token)
    else:
        return ConnectionTestResult(
            success=False,
            message=f"Unknown integration type: {integration_type}",
            error="Unsupported integration"
        )


def _get_config_from_env(integration_type: str) -> dict:
    """Get integration config from environment variables"""
    if integration_type == "argocd":
        return {
            "id": "argocd-env",
            "name": "ArgoCD",
            "type": "argocd",
            "url": os.getenv("ARGOCD_URL", "https://127.0.0.1:8080"),
            "status": "configured" if os.getenv("ARGOCD_TOKEN") else "not_configured",
            "config": {
                "has_token": bool(os.getenv("ARGOCD_TOKEN")),
            }
        }
    elif integration_type == "jenkins":
        return {
            "id": "jenkins-env",
            "name": "Jenkins",
            "type": "jenkins",
            "url": os.getenv("JENKINS_URL", ""),
            "status": "configured" if os.getenv("JENKINS_URL") else "not_configured",
            "config": {
                "has_token": bool(os.getenv("JENKINS_TOKEN")),
                "has_username": bool(os.getenv("JENKINS_USERNAME")),
            }
        }
    elif integration_type == "grafana":
        return {
            "id": "grafana-env",
            "name": "Grafana",
            "type": "grafana",
            "url": os.getenv("GRAFANA_URL", ""),
            "status": "configured" if os.getenv("GRAFANA_API_KEY") else "not_configured",
            "config": {
                "has_token": bool(os.getenv("GRAFANA_API_KEY")),
            }
        }
    elif integration_type == "kubernetes" or integration_type == "k8s":
        return {
            "id": "kubernetes-env",
            "name": "Kubernetes",
            "type": "kubernetes",
            "url": "kubeconfig",
            "status": "configured",  # Will be verified by test
            "config": {}
        }
    elif integration_type == "cloudflare":
        return {
            "id": "cloudflare-env",
            "name": "Cloudflare",
            "type": "cloudflare",
            "url": "https://api.cloudflare.com",
            "status": "configured" if os.getenv("CLOUDFLARE_API_TOKEN") else "not_configured",
            "config": {
                "has_token": bool(os.getenv("CLOUDFLARE_API_TOKEN")),
            }
        }
    else:
        return {
            "id": f"{integration_type}-env",
            "name": integration_type.title(),
            "type": integration_type,
            "url": "",
            "status": "not_configured",
            "config": {}
        }
