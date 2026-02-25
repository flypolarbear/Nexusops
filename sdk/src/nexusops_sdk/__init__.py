"""
NexusOps Python SDK

A Python SDK for interacting with NexusOps Agent Gateway.

Usage:
    from nexusops_sdk import AgentClient

    client = AgentClient(base_url="http://localhost:8000", api_key="your-api-key")

    # Register an agent
    agent = await client.register_agent(
        agent_id="my-agent",
        name="My Agent",
        version="1.0.0",
        manifest={...}
    )

    # Invoke an agent
    response = await client.invoke_agent(
        agent_id="nexusops.chat",
        query="Hello!"
    )

    # Get agent status
    status = await client.get_agent_status("my-agent")
"""

__version__ = "0.1.0"

from .client import AgentClient
from .exceptions import (
    NexusOpsError,
    InputError,
    AuthError,
    AgentError,
    ExecError,
    SystemError,
    ErrorCode,
)
from .models import (
    Agent,
    AgentManifest,
    AgentRequest,
    AgentResponse,
    AgentStatus,
    InstallStatus,
)
from .agents import AgentBase, register_agent_decorator

__all__ = [
    # Client
    "AgentClient",
    # Models
    "Agent",
    "AgentManifest",
    "AgentRequest",
    "AgentResponse",
    "AgentStatus",
    "InstallStatus",
    # Agents
    "AgentBase",
    "register_agent_decorator",
    # Exceptions
    "NexusOpsError",
    "InputError",
    "AuthError",
    "AgentError",
    "ExecError",
    "SystemError",
    "ErrorCode",
]
