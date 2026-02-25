"""
NexusOps SDK - Agent Client

Main client for interacting with NexusOps Agent Gateway.

Usage:
    from nexusops_sdk import AgentClient

    # Sync usage
    client = AgentClient(base_url="http://localhost:8000", api_key="your-api-key")

    # Async usage
    async with AgentClient(base_url="...", api_key="...") as client:
        response = await client.invoke_agent("nexusops.chat", "Hello!")

Aligned with MK-006 Gateway Contract.
"""

import json
import uuid
from typing import Any, Dict, List, Optional, Union

import httpx

from .models import (
    Agent,
    AgentManifest,
    AgentRequest,
    AgentRequestContext,
    AgentResponse,
    AgentStatus,
    AgentInstallStatus,
    InstallStatus,
)
from .models.request import OutputConfig, ToolOverride
from .exceptions import (
    NexusOpsError,
    ErrorCode,
)
from .utils.trace import (
    generate_trace_id,
    generate_request_id,
    init_trace_context,
    get_trace_context,
    TraceContext,
)


class AgentClient:
    """
    Main client for interacting with NexusOps Agent Gateway.

    Supports both sync and async operations.
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        token: Optional[str] = None,
        tenant_id: Optional[str] = None,
        timeout: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the Agent Client.

        Args:
            base_url: Base URL of NexusOps API (e.g., "http://localhost:8000")
            api_key: API key for authentication (X-API-Key header)
            token: Bearer token for authentication (Authorization header)
            tenant_id: Optional tenant ID for multi-tenant scenarios
            timeout: Request timeout in seconds
            headers: Additional headers to include in all requests
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.token = token
        self.tenant_id = tenant_id
        self.timeout = timeout
        self._extra_headers = headers or {}

        # Build default headers
        self._default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **self._extra_headers,
        }

        if self.api_key:
            self._default_headers["X-API-Key"] = self.api_key
        if self.token:
            self._default_headers["Authorization"] = f"Bearer {self.token}"
        if self.tenant_id:
            self._default_headers["X-Tenant-ID"] = self.tenant_id

        # HTTP client (lazy initialization)
        self._async_client: Optional[httpx.AsyncClient] = None
        self._sync_client: Optional[httpx.Client] = None

    def _get_async_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=self._default_headers,
            )
        return self._async_client

    def _get_sync_client(self) -> httpx.Client:
        """Get or create sync HTTP client."""
        if self._sync_client is None:
            self._sync_client = httpx.Client(
                timeout=self.timeout,
                headers=self._default_headers,
            )
        return self._sync_client

    async def close(self) -> None:
        """Close HTTP clients."""
        if self._async_client:
            await self._async_client.aclose()
            self._async_client = None
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None

    async def __aenter__(self) -> "AgentClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    def __enter__(self) -> "AgentClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None

    # ========================================
    # Agent Registration
    # ========================================

    async def register_agent(
        self,
        agent_id: str,
        name: str,
        version: str = "1.0.0",
        manifest: Optional[Union[AgentManifest, Dict[str, Any]]] = None,
        endpoint: Optional[str] = None,
        visibility: str = "public",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Register a new agent with the gateway.

        Args:
            agent_id: Unique agent identifier
            name: Human-readable agent name
            version: Agent version
            manifest: Agent manifest (AgentManifest or dict)
            endpoint: Agent service endpoint
            visibility: Visibility setting (public, private, organization)
            **kwargs: Additional manifest fields

        Returns:
            Registered agent details

        Raises:
            AuthError: If authentication fails
            InputError: If input validation fails
            NexusOpsError: For other errors
        """
        # Build manifest
        if manifest is None:
            manifest_dict = {
                "agent_id": agent_id,
                "name": name,
                "version": version,
                **kwargs,
            }
        elif isinstance(manifest, AgentManifest):
            manifest_dict = manifest.model_dump()
        else:
            manifest_dict = manifest

        payload = {
            "manifest": manifest_dict,
            "endpoint": endpoint,
            "visibility": visibility,
        }

        response = await self._request("POST", "/api/v1/market", json=payload)
        return response

    def register_agent_sync(
        self,
        agent_id: str,
        name: str,
        version: str = "1.0.0",
        manifest: Optional[Union[AgentManifest, Dict[str, Any]]] = None,
        endpoint: Optional[str] = None,
        visibility: str = "public",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Synchronous version of register_agent.
        """
        # Build manifest
        if manifest is None:
            manifest_dict = {
                "agent_id": agent_id,
                "name": name,
                "version": version,
                **kwargs,
            }
        elif isinstance(manifest, AgentManifest):
            manifest_dict = manifest.model_dump()
        else:
            manifest_dict = manifest

        payload = {
            "manifest": manifest_dict,
            "endpoint": endpoint,
            "visibility": visibility,
        }

        response = self._request_sync("POST", "/api/v1/market", json=payload)
        return response

    # ========================================
    # Agent Invocation
    # ========================================

    async def invoke_agent(
        self,
        agent_id: str,
        query: str,
        conversation_id: Optional[str] = None,
        context: Optional[Union[AgentRequestContext, Dict[str, Any]]] = None,
        output_config: Optional[Union[OutputConfig, Dict[str, Any]]] = None,
        tools: Optional[List[Union[ToolOverride, Dict[str, Any]]]] = None,
        request_id: Optional[str] = None,
    ) -> AgentResponse:
        """
        Invoke an agent with a query.

        Args:
            agent_id: Target agent ID
            query: User input/query
            conversation_id: Optional conversation ID for multi-turn
            context: Optional request context
            output_config: Optional output configuration
            tools: Optional tool overrides
            request_id: Optional request ID (generated if not provided)

        Returns:
            AgentResponse with the result

        Raises:
            AgentError: If agent is not found or not installed
            AuthError: If authentication fails
            ExecError: If execution fails
            NexusOpsError: For other errors
        """
        # Generate request ID if not provided
        if request_id is None:
            request_id = generate_request_id()

        # Build context
        if context is None:
            context_dict = {}
        elif isinstance(context, AgentRequestContext):
            context_dict = context.model_dump()
        else:
            context_dict = context

        # Build output config
        output_config_dict = None
        if output_config:
            if isinstance(output_config, OutputConfig):
                output_config_dict = output_config.model_dump()
            else:
                output_config_dict = output_config

        # Build tools
        tools_list = None
        if tools:
            tools_list = [
                t.model_dump() if isinstance(t, ToolOverride) else t
                for t in tools
            ]

        # Build request payload
        payload = {
            "request_id": request_id,
            "agent_id": agent_id,
            "query": query,
            "context": context_dict,
        }

        if conversation_id:
            payload["conversation_id"] = conversation_id
        if output_config_dict:
            payload["output_config"] = output_config_dict
        if tools_list:
            payload["tools"] = tools_list

        # Initialize trace context
        init_trace_context(request_id=request_id, agent_id=agent_id)

        # Make request
        response_data = await self._request(
            "POST",
            f"/api/v1/agents/{agent_id}/invoke",
            json=payload,
        )

        return AgentResponse.from_dict(response_data)

    def invoke_agent_sync(
        self,
        agent_id: str,
        query: str,
        conversation_id: Optional[str] = None,
        context: Optional[Union[AgentRequestContext, Dict[str, Any]]] = None,
        output_config: Optional[Union[OutputConfig, Dict[str, Any]]] = None,
        tools: Optional[List[Union[ToolOverride, Dict[str, Any]]]] = None,
        request_id: Optional[str] = None,
    ) -> AgentResponse:
        """
        Synchronous version of invoke_agent.
        """
        # Generate request ID if not provided
        if request_id is None:
            request_id = generate_request_id()

        # Build context
        if context is None:
            context_dict = {}
        elif isinstance(context, AgentRequestContext):
            context_dict = context.model_dump()
        else:
            context_dict = context

        # Build output config
        output_config_dict = None
        if output_config:
            if isinstance(output_config, OutputConfig):
                output_config_dict = output_config.model_dump()
            else:
                output_config_dict = output_config

        # Build tools
        tools_list = None
        if tools:
            tools_list = [
                t.model_dump() if isinstance(t, ToolOverride) else t
                for t in tools
            ]

        # Build request payload
        payload = {
            "request_id": request_id,
            "agent_id": agent_id,
            "query": query,
            "context": context_dict,
        }

        if conversation_id:
            payload["conversation_id"] = conversation_id
        if output_config_dict:
            payload["output_config"] = output_config_dict
        if tools_list:
            payload["tools"] = tools_list

        # Initialize trace context
        init_trace_context(request_id=request_id, agent_id=agent_id)

        # Make request
        response_data = self._request_sync(
            "POST",
            f"/api/v1/agents/{agent_id}/invoke",
            json=payload,
        )

        return AgentResponse.from_dict(response_data)

    # ========================================
    # Agent Status
    # ========================================

    async def get_agent_status(
        self,
        agent_id: str,
    ) -> AgentInstallStatus:
        """
        Get agent installation and running status.

        Args:
            agent_id: Agent ID to check

        Returns:
            AgentInstallStatus with current status

        Raises:
            AgentError: If agent is not found
            AuthError: If authentication fails
        """
        response = await self._request(
            "GET",
            f"/api/v1/market/{agent_id}/install-status",
        )

        return AgentInstallStatus(
            agent_id=response.get("agent_id", agent_id),
            name=response.get("name", ""),
            version=response.get("version", ""),
            install_status=InstallStatus(response.get("install_status", "not_installed")),
            agent_status=AgentStatus(response.get("agent_status", "inactive")),
            installed_at=response.get("installed_at"),
            last_heartbeat=response.get("last_heartbeat"),
        )

    def get_agent_status_sync(
        self,
        agent_id: str,
    ) -> AgentInstallStatus:
        """
        Synchronous version of get_agent_status.
        """
        response = self._request_sync(
            "GET",
            f"/api/v1/market/{agent_id}/install-status",
        )

        return AgentInstallStatus(
            agent_id=response.get("agent_id", agent_id),
            name=response.get("name", ""),
            version=response.get("version", ""),
            install_status=InstallStatus(response.get("install_status", "not_installed")),
            agent_status=AgentStatus(response.get("agent_status", "inactive")),
            installed_at=response.get("installed_at"),
            last_heartbeat=response.get("last_heartbeat"),
        )

    async def get_agent(self, agent_id: str) -> Agent:
        """
        Get agent details.

        Args:
            agent_id: Agent ID to retrieve

        Returns:
            Agent with full details
        """
        response = await self._request(
            "GET",
            f"/api/v1/market/{agent_id}",
        )

        return Agent(
            agent_id=response.get("agent_id", agent_id),
            name=response.get("name", ""),
            version=response.get("version", ""),
            description=response.get("description"),
            author=response.get("author"),
            category=response.get("category", "general"),
            tags=response.get("tags", []),
            capabilities=response.get("capabilities", []),
            status=AgentStatus(response.get("status", "active")),
            visibility=response.get("visibility", "public"),
            endpoint=response.get("endpoint"),
            rating=response.get("rating", 0.0),
            downloads=response.get("downloads", 0),
            created_at=response.get("created_at"),
            updated_at=response.get("updated_at"),
        )

    def get_agent_sync(self, agent_id: str) -> Agent:
        """
        Synchronous version of get_agent.
        """
        response = self._request_sync(
            "GET",
            f"/api/v1/market/{agent_id}",
        )

        return Agent(
            agent_id=response.get("agent_id", agent_id),
            name=response.get("name", ""),
            version=response.get("version", ""),
            description=response.get("description"),
            author=response.get("author"),
            category=response.get("category", "general"),
            tags=response.get("tags", []),
            capabilities=response.get("capabilities", []),
            status=AgentStatus(response.get("status", "active")),
            visibility=response.get("visibility", "public"),
            endpoint=response.get("endpoint"),
            rating=response.get("rating", 0.0),
            downloads=response.get("downloads", 0),
            created_at=response.get("created_at"),
            updated_at=response.get("updated_at"),
        )

    # ========================================
    # Agent Install/Uninstall
    # ========================================

    async def install_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Install an agent from the market.

        Args:
            agent_id: Agent ID to install

        Returns:
            Installation result
        """
        return await self._request(
            "POST",
            f"/api/v1/market/{agent_id}/install",
        )

    def install_agent_sync(self, agent_id: str) -> Dict[str, Any]:
        """
        Synchronous version of install_agent.
        """
        return self._request_sync(
            "POST",
            f"/api/v1/market/{agent_id}/install",
        )

    async def uninstall_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Uninstall an agent.

        Args:
            agent_id: Agent ID to uninstall

        Returns:
            Uninstallation result
        """
        return await self._request(
            "POST",
            f"/api/v1/market/{agent_id}/uninstall",
        )

    def uninstall_agent_sync(self, agent_id: str) -> Dict[str, Any]:
        """
        Synchronous version of uninstall_agent.
        """
        return self._request_sync(
            "POST",
            f"/api/v1/market/{agent_id}/uninstall",
        )

    async def enable_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Enable a disabled agent.

        Args:
            agent_id: Agent ID to enable

        Returns:
            Enable result
        """
        return await self._request(
            "POST",
            f"/api/v1/market/{agent_id}/enable",
        )

    def enable_agent_sync(self, agent_id: str) -> Dict[str, Any]:
        """
        Synchronous version of enable_agent.
        """
        return self._request_sync(
            "POST",
            f"/api/v1/market/{agent_id}/enable",
        )

    async def disable_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Disable an installed agent.

        Args:
            agent_id: Agent ID to disable

        Returns:
            Disable result
        """
        return await self._request(
            "POST",
            f"/api/v1/market/{agent_id}/disable",
        )

    def disable_agent_sync(self, agent_id: str) -> Dict[str, Any]:
        """
        Synchronous version of disable_agent.
        """
        return self._request_sync(
            "POST",
            f"/api/v1/market/{agent_id}/disable",
        )

    # ========================================
    # List Agents
    # ========================================

    async def list_agents(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        capability: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        List available agents.

        Args:
            query: Search query
            category: Filter by category
            capability: Filter by capability
            page: Page number
            page_size: Items per page

        Returns:
            Paginated list of agents
        """
        params = {
            "page": page,
            "page_size": page_size,
        }
        if query:
            params["query"] = query
        if category:
            params["category"] = category
        if capability:
            params["capability"] = capability

        return await self._request("GET", "/api/v1/market", params=params)

    def list_agents_sync(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        capability: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        Synchronous version of list_agents.
        """
        params = {
            "page": page,
            "page_size": page_size,
        }
        if query:
            params["query"] = query
        if category:
            params["category"] = category
        if capability:
            params["capability"] = capability

        return self._request_sync("GET", "/api/v1/market", params=params)

    # ========================================
    # HTTP Request Helpers
    # ========================================

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make an async HTTP request.

        Args:
            method: HTTP method
            path: API path
            params: Query parameters
            json: JSON body

        Returns:
            Response data

        Raises:
            NexusOpsError: On API error
        """
        url = f"{self.base_url}{path}"
        client = self._get_async_client()

        # Get trace context for headers
        trace_ctx = get_trace_context()
        headers = {}
        if trace_ctx:
            headers.update(trace_ctx.to_headers())

        try:
            response = await client.request(
                method,
                url,
                params=params,
                json=json,
                headers=headers if headers else None,
            )

            return self._handle_response(response)

        except httpx.TimeoutException as e:
            raise NexusOpsError(
                code=ErrorCode.EXEC_TIMEOUT,
                message=f"Request timed out: {e}",
            )
        except httpx.RequestError as e:
            raise NexusOpsError(
                code=ErrorCode.SYSTEM_UNAVAILABLE,
                message=f"Request failed: {e}",
            )

    def _request_sync(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make a sync HTTP request.
        """
        url = f"{self.base_url}{path}"
        client = self._get_sync_client()

        # Get trace context for headers
        trace_ctx = get_trace_context()
        headers = {}
        if trace_ctx:
            headers.update(trace_ctx.to_headers())

        try:
            response = client.request(
                method,
                url,
                params=params,
                json=json,
                headers=headers if headers else None,
            )

            return self._handle_response(response)

        except httpx.TimeoutException as e:
            raise NexusOpsError(
                code=ErrorCode.EXEC_TIMEOUT,
                message=f"Request timed out: {e}",
            )
        except httpx.RequestError as e:
            raise NexusOpsError(
                code=ErrorCode.SYSTEM_UNAVAILABLE,
                message=f"Request failed: {e}",
            )

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """
        Handle HTTP response and extract data or raise errors.

        Args:
            response: HTTP response

        Returns:
            Response data

        Raises:
            NexusOpsError: On non-2xx response
        """
        # Extract trace info from headers
        trace_id = response.headers.get("X-Trace-ID")
        request_id = response.headers.get("X-Request-ID")

        if 200 <= response.status_code < 300:
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"data": response.text}

        # Handle error response
        try:
            error_data = response.json()
        except json.JSONDecodeError:
            error_data = {
                "error": {
                    "code": "SYSTEM_INTERNAL_ERROR",
                    "message": response.text or "Unknown error",
                }
            }

        # Add trace info
        if trace_id:
            error_data["trace_id"] = trace_id
        if request_id:
            error_data["request_id"] = request_id

        # Raise appropriate exception
        raise NexusOpsError.from_response(error_data)
