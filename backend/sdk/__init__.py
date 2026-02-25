"""
NexusOps Python SDK

A Python SDK for interacting with the NexusOps Agent API.
Provides both synchronous and asynchronous interfaces for
agent registration, invocation, and management.

Example:
    from nexusops_sdk import AgentClient, AgentConfig

    # Initialize client
    client = AgentClient(config=AgentConfig(
        base_url="https://nexusops.example.com",
        api_key="your-api-key"
    ))

    # List agents
    agents = client.agents.list()
    for agent in agents.agents:
        print(f"- {agent.name} ({agent.agent_id})")

    # Invoke an agent (sync)
    result = client.agents.invoke(
        agent_id="nexusops.k8s",
        action="get_pods",
        params={"namespace": "production"}
    )
    print(result.content.text)

    # Invoke an agent (async)
    async def main():
        result = await client.agents.invoke_async(
            agent_id="nexusops.k8s",
            action="get_pods",
            params={"namespace": "production"}
        )
        print(result.content.text)

    # Register a custom agent
    client.agents.register(
        agent_id="my-custom-agent",
        name="My Custom Agent",
        capabilities=["data-processing", "report-generation"],
        endpoint="https://my-agent.example.com/webhook"
    )
"""

__version__ = "1.0.0"
__author__ = "NexusOps Team"

# Main client
from .client import AgentClient, AgentsNamespace

# Models
from .models import (
    AgentConfig,
    AgentManifest,
    AgentToolDefinition,
    AgentRegistrationRequest,
    AgentRegistrationResponse,
    AgentRequestContext,
    AgentInvokeRequest,
    AgentInvokeResponse,
    AgentContent,
    AgentAction,
    RelatedResource,
    AgentError,
    AgentStatus,
    AgentListResponse,
    ErrorResponse,
)

# Exceptions
from .exceptions import (
    NexusOpsError,
    AgentNotFoundError,
    AgentTimeoutError,
    AuthenticationError,
    AuthorizationError,
    AgentNotInstalledError,
    AgentDisabledError,
    ValidationError,
    ConnectionError,
    RateLimitError,
)

__all__ = [
    # Version
    "__version__",
    # Client
    "AgentClient",
    "AgentsNamespace",
    # Models
    "AgentConfig",
    "AgentManifest",
    "AgentToolDefinition",
    "AgentRegistrationRequest",
    "AgentRegistrationResponse",
    "AgentRequestContext",
    "AgentInvokeRequest",
    "AgentInvokeResponse",
    "AgentContent",
    "AgentAction",
    "RelatedResource",
    "AgentError",
    "AgentStatus",
    "AgentListResponse",
    "ErrorResponse",
    # Exceptions
    "NexusOpsError",
    "AgentNotFoundError",
    "AgentTimeoutError",
    "AuthenticationError",
    "AuthorizationError",
    "AgentNotInstalledError",
    "AgentDisabledError",
    "ValidationError",
    "ConnectionError",
    "RateLimitError",
]
