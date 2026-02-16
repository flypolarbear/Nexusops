"""
NexusOps Backend - Agent API Router

Implements BE-004: Agent Gateway 基础
"""

from datetime import datetime
from typing import Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.database import AgentInvocation, AgentRegistration
from app.models.schemas import (
    AgentRequest,
    AgentResponse,
    AgentContent,
    AgentRegistrationCreate,
    AgentRegistrationResponse,
    AgentManifest,
    AgentToolDefinition,
)

router = APIRouter(prefix="/agents", tags=["agents"])

# ============================================
# Built-in Agents (matching frontend BUILTIN_AGENTS)
# ============================================

BUILTIN_AGENTS: list[dict[str, Any]] = [
    {
        "agent_id": "nexusops.chat",
        "name": "AI Assistant",
        "version": "1.0.0",
        "description": "通用 AI 助手，支持快捷命令",
        "category": "general",
        "capabilities": ["chat", "quick_commands", "deployment_info", "status_query"],
        "tools": [
            {
                "name": "get_deployment_status",
                "description": "Get deployment status for a version",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "codename": {"type": "string"},
                        "region": {"type": "string"},
                    },
                },
            },
        ],
    },
    {
        "agent_id": "nexusops.dns",
        "name": "DNS Operations Agent",
        "version": "1.0.0",
        "description": "DNS 记录管理、域名生成、Cloudflare 配置",
        "category": "infrastructure",
        "capabilities": [
            "dns_record_create",
            "dns_record_delete",
            "dns_record_query",
            "random_domain_generate",
        ],
        "tools": [
            {
                "name": "create_dns_record",
                "description": "Create a DNS record",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "zone_id": {"type": "string"},
                        "record_type": {"type": "string"},
                        "name": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["zone_id", "record_type", "name", "content"],
                },
            },
            {
                "name": "generate_random_subdomain",
                "description": "Generate a random subdomain",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "base_domain": {"type": "string"},
                        "levels": {"type": "integer", "default": 4},
                    },
                    "required": ["base_domain"],
                },
            },
        ],
    },
    {
        "agent_id": "nexusops.k8s",
        "name": "Kubernetes Agent",
        "version": "1.0.0",
        "description": "Kubernetes 资源管理、部署操作",
        "category": "deployment",
        "capabilities": ["k8s_deploy", "k8s_scale", "k8s_logs", "k8s_describe"],
        "tools": [
            {
                "name": "get_pod_logs",
                "description": "Get logs from a pod",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pod_name": {"type": "string"},
                        "namespace": {"type": "string", "default": "default"},
                        "tail_lines": {"type": "integer", "default": 100},
                    },
                    "required": ["pod_name"],
                },
            },
            {
                "name": "describe_resource",
                "description": "Describe a Kubernetes resource",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "resource_type": {"type": "string"},
                        "name": {"type": "string"},
                        "namespace": {"type": "string", "default": "default"},
                    },
                    "required": ["resource_type", "name"],
                },
            },
        ],
    },
    {
        "agent_id": "nexusops.deploy",
        "name": "Deployment Orchestrator",
        "version": "1.0.0",
        "description": "部署流程编排",
        "category": "deployment",
        "capabilities": ["deploy_create", "deploy_rollback", "deploy_status", "deploy_force_sync"],
        "tools": [
            {
                "name": "create_deployment",
                "description": "Create a new deployment",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "version_id": {"type": "string"},
                        "regions": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["version_id", "regions"],
                },
            },
            {
                "name": "rollback_deployment",
                "description": "Rollback a deployment",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "version_id": {"type": "string"},
                        "region": {"type": "string"},
                    },
                    "required": ["version_id"],
                },
            },
            {
                "name": "force_sync",
                "description": "Force sync ArgoCD application",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string"},
                    },
                    "required": ["app_name"],
                },
            },
        ],
    },
]


# ============================================
# Agent List & Registration
# ============================================

@router.get("")
async def list_agents(
    db: AsyncSession = Depends(get_db),
):
    """List all available agents (built-in + registered)"""
    # Get registered agents from database
    result = await db.execute(
        select(AgentRegistration).where(AgentRegistration.status == "active")
    )
    registered = result.scalars().all()

    # Combine with built-in agents
    agents = []
    for agent_data in BUILTIN_AGENTS:
        agents.append(AgentManifest(
            agent_id=agent_data["agent_id"],
            name=agent_data["name"],
            version=agent_data["version"],
            description=agent_data.get("description"),
            category=agent_data.get("category", "general"),
            capabilities=agent_data.get("capabilities", []),
            tools=[AgentToolDefinition(**t) for t in agent_data.get("tools", [])],
        ))

    # Add registered agents
    for reg in registered:
        manifest_data = reg.manifest or {}
        agents.append(AgentManifest(
            agent_id=reg.id,
            name=reg.name,
            version=reg.version,
            description=manifest_data.get("description"),
            category=manifest_data.get("category", "custom"),
            capabilities=manifest_data.get("capabilities", []),
            tools=[AgentToolDefinition(**t) for t in manifest_data.get("tools", [])],
        ))

    return {"agents": [a.model_dump() for a in agents]}


@router.post("", response_model=AgentRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register_agent(
    data: AgentRegistrationCreate,
    db: AsyncSession = Depends(get_db),
):
    """Register a new agent"""
    # Check if already exists
    result = await db.execute(
        select(AgentRegistration).where(AgentRegistration.id == data.agent_id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Update existing
        existing.name = data.name
        existing.version = data.version
        existing.manifest = data.manifest
        existing.endpoint = data.endpoint
        existing.status = "active"
        existing.last_heartbeat = datetime.utcnow()
        await db.commit()
        await db.refresh(existing)
        return existing

    # Create new
    agent = AgentRegistration(
        id=data.agent_id,
        name=data.name,
        version=data.version,
        manifest=data.manifest,
        endpoint=data.endpoint,
        status="active",
        last_heartbeat=datetime.utcnow(),
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


@router.get("/{agent_id}")
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get agent details"""
    # Check built-in agents first
    for agent_data in BUILTIN_AGENTS:
        if agent_data["agent_id"] == agent_id:
            return AgentManifest(
                agent_id=agent_data["agent_id"],
                name=agent_data["name"],
                version=agent_data["version"],
                description=agent_data.get("description"),
                category=agent_data.get("category", "general"),
                capabilities=agent_data.get("capabilities", []),
                tools=[AgentToolDefinition(**t) for t in agent_data.get("tools", [])],
            )

    # Check registered agents
    result = await db.execute(
        select(AgentRegistration).where(AgentRegistration.id == agent_id)
    )
    reg = result.scalar_one_or_none()

    if not reg:
        raise HTTPException(status_code=404, detail="Agent not found")

    manifest_data = reg.manifest or {}
    return AgentManifest(
        agent_id=reg.id,
        name=reg.name,
        version=reg.version,
        description=manifest_data.get("description"),
        category=manifest_data.get("category", "custom"),
        capabilities=manifest_data.get("capabilities", []),
        tools=[AgentToolDefinition(**t) for t in manifest_data.get("tools", [])],
    )


# ============================================
# Agent Invocation
# ============================================

@router.post("/{agent_id}/invoke", response_model=AgentResponse)
async def invoke_agent(
    agent_id: str,
    request: AgentRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Invoke an agent

    This is the main entry point for agent execution.
    Implements ADR-001 (execution environment), ADR-002 (auth), ADR-005 (error handling)
    """
    start_time = datetime.utcnow()

    # Validate agent exists
    agent_found = False
    agent_manifest = None

    for agent_data in BUILTIN_AGENTS:
        if agent_data["agent_id"] == agent_id:
            agent_found = True
            agent_manifest = agent_data
            break

    if not agent_found:
        result = await db.execute(
            select(AgentRegistration).where(
                AgentRegistration.id == agent_id,
                AgentRegistration.status == "active"
            )
        )
        reg = result.scalar_one_or_none()
        if reg:
            agent_found = True
            agent_manifest = reg.manifest

    if not agent_found:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Create invocation record
    invocation = AgentInvocation(
        id=str(uuid.uuid4()),
        agent_id=agent_id,
        request_id=request.request_id,
        conversation_id=request.conversation_id,
        request=request.model_dump(),
        status="running",
    )
    db.add(invocation)
    await db.commit()

    try:
        # Execute agent (mock implementation)
        response = await execute_agent_mock(agent_id, request, agent_manifest)

        # Update invocation record
        invocation.status = response.status
        invocation.response = response.model_dump()
        invocation.latency_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        await db.commit()

        return response

    except Exception as e:
        invocation.status = "error"
        invocation.error_code = "INTERNAL_ERROR"
        invocation.error_message = str(e)
        await db.commit()

        return AgentResponse(
            request_id=request.request_id,
            status="error",
            content=AgentContent(text="", format="plain"),
            error={
                "code": "INTERNAL_ERROR",
                "message": str(e),
            },
        )


async def execute_agent_mock(
    agent_id: str,
    request: AgentRequest,
    manifest: dict,
) -> AgentResponse:
    """
    Mock agent execution

    In production, this would:
    1. Validate request against input_schema
    2. Execute tools if needed
    3. Call LLM with context
    4. Validate response against output_schema
    5. Return structured response
    """
    # Simulate processing delay
    import asyncio
    await asyncio.sleep(0.5 + len(request.query) * 0.001)

    # Generate mock response based on agent type and query
    query = request.query.lower()

    if agent_id == "nexusops.chat":
        if query.startswith("/deploy"):
            return AgentResponse(
                request_id=request.request_id,
                status="success",
                content=AgentContent(
                    text=f"""## 🚀 Deployment Triggered

**Version:** {request.context.codename or 'unknown'}
**Target Region:** {request.context.region or 'us-east'}

The deployment has been initiated. I'll notify you when it completes.

### Deployment Steps
1. ✅ CI/CD Build - Completed
2. 🔄 ArgoCD Sync - In Progress
3. ⏳ Health Check - Pending

Estimated time: 2-3 minutes
""",
                    format="markdown",
                ),
                structured_output={
                    "type": "deployment_status",
                    "data": {
                        "codename": request.context.codename,
                        "regions": [{"name": request.context.region, "status": "progressing"}],
                    },
                },
                suggested_actions=[
                    {
                        "id": "view-progress",
                        "type": "navigate",
                        "label": "View Progress",
                        "params": {"url": "/deployments"},
                    },
                ],
            )

        elif query.startswith("/status"):
            return AgentResponse(
                request_id=request.request_id,
                status="success",
                content=AgentContent(
                    text=f"""## 📊 Version Status: {request.context.codename or 'unknown'}

The version is deployed and healthy across all regions.

### Regional Status
| Region | Status | Health | Replicas |
|--------|--------|--------|----------|
| US East | ✅ Synced | 🟢 Healthy | 3/3 |
| EU West | ✅ Synced | 🟢 Healthy | 2/2 |

**Last deployed:** 2 hours ago
""",
                    format="markdown",
                ),
                structured_output={
                    "type": "deployment_status",
                    "data": {
                        "codename": request.context.codename,
                        "regions": [
                            {"name": "US East", "status": "healthy", "replicas": {"ready": 3, "total": 3}},
                            {"name": "EU West", "status": "healthy", "replicas": {"ready": 2, "total": 2}},
                        ],
                    },
                },
            )

        else:
            return AgentResponse(
                request_id=request.request_id,
                status="success",
                content=AgentContent(
                    text=f"""I understand you're asking: "{request.query}"

Based on the current system state, here's what I found:

- All services are operational
- No critical incidents in the last 24 hours
- Resource utilization is within expected ranges

Is there anything specific you'd like me to help with?
""",
                    format="markdown",
                ),
            )

    elif agent_id == "nexusops.k8s":
        return AgentResponse(
            request_id=request.request_id,
            status="success",
            content=AgentContent(
                text=f"""## K8s Resource Analysis

Analyzing resource: **{request.context.resource_name or 'unknown'}** in namespace **{request.context.namespace or 'default'}**

### Resource Status
- **Type:** {request.context.resource_type or 'Pod'}
- **Status:** Running
- **Health:** Healthy

### Metrics
- CPU: 250m / 500m (50%)
- Memory: 384Mi / 512Mi (75%)

### No issues detected
""",
                format="markdown",
            ),
        )

    elif agent_id == "nexusops.deploy":
        return AgentResponse(
            request_id=request.request_id,
            status="success",
            content=AgentContent(
                text=f"""## Deployment Orchestration

Processing deployment request for **{request.context.codename or 'unknown'}**

### Deployment Chain
1. ✅ **CI/CD Build** - Completed (2m 30s)
2. ✅ **ArgoCD Sync** - Completed (45s)
3. ✅ **Health Check** - Passed (30s)

### Result
Deployment successful! All services are running.
""",
                format="markdown",
            ),
        )

    # Default response
    return AgentResponse(
        request_id=request.request_id,
        status="success",
        content=AgentContent(
            text=f"Agent {agent_id} received your request: {request.query}",
            format="markdown",
        ),
    )


# ============================================
# Agent Tools
# ============================================

@router.get("/{agent_id}/tools")
async def get_agent_tools(
    agent_id: str,
):
    """Get tools available for an agent"""
    for agent_data in BUILTIN_AGENTS:
        if agent_data["agent_id"] == agent_id:
            return {"tools": agent_data.get("tools", [])}

    return {"tools": []}
