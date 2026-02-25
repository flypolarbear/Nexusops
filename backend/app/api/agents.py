"""
NexusOps Backend - Agent API Router

Implements BE-004: Agent Gateway 基础
Implements MK-006: Gateway 调用契约
Implements MK-007: Gateway 插件执行边界
Implements MK-008: 第三方 Agent 最小闭环

Refactored to use the new Gateway layer.
Database Migration: Now uses SQLAlchemy async database storage
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional, List
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
    AgentError,
)
from app.stores.agent_store import (
    # Legacy in-memory stores (for backward compatibility with Gateway)
    agent_store as _market_store,
    installed_agents as _installed_agents,
    # New async database functions
    async_get_agent,
    async_get_install_status,
    async_list_installed_agents,
    async_list_agents,
)
from app.gateway.trace import generate_trace_id, init_trace_context, get_trace_context
from app.gateway.errors import (
    ErrorCode,
    AgentError as GatewayAgentError,
    agent_not_found,
    agent_not_installed,
    agent_disabled,
)
from app.gateway.executor.router import ExecutorRouter, get_executor_router


router = APIRouter(prefix="/agents", tags=["agents"])


# ============================================
# Install Status (synced with agent_market.py)
# ============================================

class InstallStatus(str, Enum):
    """Agent 安装状态"""
    NOT_INSTALLED = "not_installed"
    INSTALLED = "installed"
    DISABLED = "disabled"


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
        "description": "DNS 记录管理、域名生成",
        "category": "infrastructure",
        "capabilities": [
            "dns_record_create",
            "dns_record_delete",
            "dns_record_query",
            "random_domain_generate",
        ],
        "tools": [],
    },
    {
        "agent_id": "nexusops.k8s",
        "name": "Kubernetes Agent",
        "version": "1.0.0",
        "description": "Kubernetes 资源管理、部署操作",
        "category": "deployment",
        "capabilities": ["k8s_deploy", "k8s_scale", "k8s_logs", "k8s_describe"],
        "tools": [],
    },
    {
        "agent_id": "nexusops.deploy",
        "name": "Deployment Orchestrator",
        "version": "1.0.0",
        "description": "部署流程编排",
        "category": "deployment",
        "capabilities": ["deploy_create", "deploy_rollback", "deploy_status", "deploy_force_sync"],
        "tools": [],
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
# Agent Invocation (Refactored to use Gateway)
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
    Uses the new Gateway layer (MK-006/MK-007) for execution.
    """
    start_time = datetime.utcnow()
    trace_id = generate_trace_id()

    # Initialize trace context
    init_trace_context(
        request_id=request.request_id,
        trace_id=trace_id,
        agent_id=agent_id,
        conversation_id=request.conversation_id,
    )

    # Validate agent_id consistency (path vs body)
    if request.agent_id and request.agent_id != agent_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INPUT_AGENT_ID_MISMATCH",
                "message": f"Path agent_id '{agent_id}' does not match body agent_id '{request.agent_id}'",
                "trace_id": trace_id,
            }
        )

    # Step 1: Check if it's a built-in agent
    is_builtin = any(a["agent_id"] == agent_id for a in BUILTIN_AGENTS)

    # Step 2: For third-party agents, check install status from database
    if not is_builtin:
        # Check if agent exists in database
        agent = await async_get_agent(agent_id, db)

        if agent:
            # Agent is registered, check install status
            install_status = await async_get_install_status(agent_id, db)

            if install_status == InstallStatus.NOT_INSTALLED.value:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "AGENT_NOT_INSTALLED",
                        "message": f"Agent '{agent_id}' is not installed. Please install it first.",
                        "trace_id": trace_id,
                    }
                )

            if install_status == InstallStatus.DISABLED.value:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "AGENT_DISABLED",
                        "message": f"Agent '{agent_id}' is disabled. Please enable it first.",
                        "trace_id": trace_id,
                    }
                )
        else:
            # Check database for registered agents
            result = await db.execute(
                select(AgentRegistration).where(
                    AgentRegistration.id == agent_id,
                    AgentRegistration.status == "active"
                )
            )
            reg = result.scalar_one_or_none()
            if not reg:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "code": "AGENT_NOT_FOUND",
                        "message": f"Agent '{agent_id}' not found",
                        "trace_id": trace_id,
                    }
                )

    # Create invocation record
    invocation = AgentInvocation(
        id=trace_id,
        agent_id=agent_id,
        request_id=request.request_id,
        conversation_id=request.conversation_id,
        request=request.model_dump(),
        status="running",
    )
    db.add(invocation)
    await db.commit()

    try:
        # Execute via Gateway
        router = get_executor_router(use_mock_remote=True)

        # Build request context
        request_context = {}
        if request.context:
            request_context = {
                "user_id": request.context.user_id,
                "tenant_id": request.context.tenant_id,
                "project_id": request.context.project_id,
                "version_id": request.context.version_id,
                "codename": request.context.codename,
                "region": request.context.region,
                "resource_type": request.context.resource_type,
                "resource_name": request.context.resource_name,
                "namespace": request.context.namespace,
            }

        # Get installed agents list for gateway (need to convert from database)
        installed_list = await async_list_installed_agents(db)
        installed_agents_dict = {
            item["agent_id"]: item for item in installed_list
        }

        # Get agent store for gateway from database
        # We need to get all registered agents from the database
        all_agents = await async_list_agents(db=db)
        agent_store_dict = {agent["agent_id"]: agent for agent in all_agents}

        # Execute via router
        executor_result = await router.route_and_execute(
            agent_id=agent_id,
            trace_id=trace_id,
            request_id=request.request_id,
            query=request.query,
            request_context=request_context,
            output_config=request.output_config.model_dump() if request.output_config else None,
            tools=[t.model_dump() for t in request.tools] if request.tools else None,
            installed_agents=installed_agents_dict,
            agent_store=agent_store_dict,
        )

        # Convert to API response
        response = _executor_result_to_response(executor_result, request.request_id, trace_id)

        # Update invocation record
        invocation.status = response.status
        invocation.response = response.model_dump()
        invocation.latency_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        await db.commit()

        return response

    except HTTPException:
        raise
    except Exception as e:
        invocation.status = "error"
        invocation.error_code = "INTERNAL_ERROR"
        invocation.error_message = str(e)
        await db.commit()

        return AgentResponse(
            request_id=request.request_id,
            status="error",
            content=AgentContent(text="", format="plain"),
            error=AgentError(
                code="INTERNAL_ERROR",
                message=str(e),
                details={"trace_id": trace_id},
            ),
            metadata={"trace_id": trace_id},
        )


def _executor_result_to_response(
    result: Any,
    request_id: str,
    trace_id: str,
) -> AgentResponse:
    """Convert ExecutorResult to AgentResponse"""
    status = "success" if result.success else "error"

    content = AgentContent(
        text=result.content.get("text", ""),
        format=result.content.get("format", "markdown"),
        data=result.content.get("data"),
    )

    suggested_actions = []
    for action in (result.suggested_actions or []):
        suggested_actions.append({
            "id": action.get("id", ""),
            "type": action.get("type", "invoke"),
            "label": action.get("label", ""),
            "params": action.get("params", {}),
            "confirm_required": action.get("confirm_required", False),
            "danger": action.get("danger", False),
        })

    related_resources = []
    for resource in (result.related_resources or []):
        related_resources.append({
            "type": resource.get("type", ""),
            "id": resource.get("id", ""),
            "name": resource.get("name", ""),
            "link": resource.get("link"),
        })

    error = None
    if result.error:
        error = AgentError(
            code=result.error.get("code", "UNKNOWN_ERROR"),
            message=result.error.get("message", "Unknown error"),
            details=result.error.get("details"),
            retry_after=result.error.get("retry_after"),
        )

    metadata = {
        **(result.metadata or {}),
        "trace_id": trace_id,
    }

    return AgentResponse(
        request_id=request_id,
        status=status,
        content=content,
        structured_output=result.structured_output,
        suggested_actions=suggested_actions,
        related_resources=related_resources,
        tool_calls=result.tool_calls,
        metadata=metadata,
        error=error,
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
