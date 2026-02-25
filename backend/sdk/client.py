"""
NexusOps SDK - Client

Main client classes for interacting with the NexusOps Agent API.
Supports both synchronous and asynchronous operations.
"""

import asyncio
import json
import uuid
from typing import Any, Dict, List, Optional, Union

import httpx
from pydantic import ValidationError as PydanticValidationError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from .models import (
    AgentConfig,
    AgentManifest,
    AgentInvokeRequest,
    AgentInvokeResponse,
    AgentRegistrationRequest,
    AgentRegistrationResponse,
    AgentStatus,
    AgentListResponse,
    AgentRequestContext,
    ErrorResponse,
)
from .exceptions import (
    NexusOpsError,
    AgentNotFoundError,
    AgentTimeoutError,
    AuthenticationError,
    AuthorizationError,
    AgentNotInstalledError,
    AgentDisabledError,
    ValidationError,
    ConnectionError as NexusOpsConnectionError,
    RateLimitError,
)


class AgentsNamespace:
    """
    Namespace for agent-related operations.

    Provides methods to register, invoke, and manage agents.
    Supports both synchronous and asynchronous patterns.
    """

    def __init__(self, client: "AgentClient"):
        self._client = client

    # ============================================
    # Registration
    # ============================================

    def register(
        self,
        agent_id: str,
        name: str,
        capabilities: List[str],
        endpoint: Optional[str] = None,
        version: str = "1.0.0",
        description: Optional[str] = None,
        category: str = "custom",
        tools: Optional[List[Dict[str, Any]]] = None,
        input_schema: Optional[Dict[str, Any]] = None,
        output_schema: Optional[Dict[str, Any]] = None,
    ) -> AgentRegistrationResponse:
        """
        Register a new agent (synchronous).

        Args:
            agent_id: Unique identifier for the agent
            name: Display name for the agent
            capabilities: List of agent capabilities
            endpoint: Webhook endpoint for the agent
            version: Agent version
            description: Agent description
            category: Agent category
            tools: List of tool definitions
            input_schema: JSON Schema for input validation
            output_schema: JSON Schema for output validation

        Returns:
            AgentRegistrationResponse with registration details

        Raises:
            ValidationError: If parameters are invalid
            AuthenticationError: If authentication fails
            NexusOpsError: For other errors
        """
        request = AgentRegistrationRequest(
            agent_id=agent_id,
            name=name,
            version=version,
            description=description,
            category=category,
            capabilities=capabilities,
            tools=tools or [],
            endpoint=endpoint,
            input_schema=input_schema,
            output_schema=output_schema,
        )

        # Build manifest for the API
        manifest = {
            "description": description,
            "category": category,
            "capabilities": capabilities,
            "tools": [t.model_dump(by_alias=True) for t in request.tools],
            "input_schema": input_schema,
            "output_schema": output_schema,
        }

        payload = {
            "agent_id": agent_id,
            "name": name,
            "version": version,
            "manifest": manifest,
            "endpoint": endpoint,
        }

        response = self._client._request(
            method="POST",
            path="/api/agents",
            json=payload,
        )

        return AgentRegistrationResponse(**response)

    async def register_async(
        self,
        agent_id: str,
        name: str,
        capabilities: List[str],
        endpoint: Optional[str] = None,
        version: str = "1.0.0",
        description: Optional[str] = None,
        category: str = "custom",
        tools: Optional[List[Dict[str, Any]]] = None,
        input_schema: Optional[Dict[str, Any]] = None,
        output_schema: Optional[Dict[str, Any]] = None,
    ) -> AgentRegistrationResponse:
        """
        Register a new agent (asynchronous).

        See register() for parameter details.
        """
        request = AgentRegistrationRequest(
            agent_id=agent_id,
            name=name,
            version=version,
            description=description,
            category=category,
            capabilities=capabilities,
            tools=tools or [],
            endpoint=endpoint,
            input_schema=input_schema,
            output_schema=output_schema,
        )

        manifest = {
            "description": description,
            "category": category,
            "capabilities": capabilities,
            "tools": [t.model_dump(by_alias=True) for t in request.tools],
            "input_schema": input_schema,
            "output_schema": output_schema,
        }

        payload = {
            "agent_id": agent_id,
            "name": name,
            "version": version,
            "manifest": manifest,
            "endpoint": endpoint,
        }

        response = await self._client._request_async(
            method="POST",
            path="/api/agents",
            json=payload,
        )

        return AgentRegistrationResponse(**response)

    # ============================================
    # Invocation
    # ============================================

    def invoke(
        self,
        agent_id: str,
        query: Optional[str] = None,
        action: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        context: Optional[AgentRequestContext] = None,
        conversation_id: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> AgentInvokeResponse:
        """
        Invoke an agent (synchronous).

        Args:
            agent_id: ID of the agent to invoke
            query: Natural language query for the agent
            action: Specific action to perform (alternative to query)
            params: Parameters for the action
            context: Request context (user, project, etc.)
            conversation_id: Conversation ID for continuity
            timeout: Override default timeout for this request

        Returns:
            AgentInvokeResponse with the agent's response

        Raises:
            AgentNotFoundError: If the agent doesn't exist
            AgentTimeoutError: If the request times out
            AgentNotInstalledError: If the agent is not installed
            AgentDisabledError: If the agent is disabled
            AuthenticationError: If authentication fails
            NexusOpsError: For other errors

        Example:
            result = client.agents.invoke(
                agent_id="nexusops.k8s",
                action="get_pods",
                params={"namespace": "production"}
            )
            print(result.content.text)
        """
        # Build query string
        if action:
            query_str = f"{action}"
            if params:
                param_str = " ".join(f"{k}={v}" for k, v in params.items())
                query_str = f"{action} {param_str}"
        else:
            query_str = query or ""

        request_id = str(uuid.uuid4())
        conv_id = conversation_id or str(uuid.uuid4())

        payload = {
            "request_id": request_id,
            "conversation_id": conv_id,
            "agent_id": agent_id,
            "query": query_str,
        }

        if context:
            payload["context"] = context.model_dump()

        try:
            response = self._client._request(
                method="POST",
                path=f"/api/agents/{agent_id}/invoke",
                json=payload,
                timeout=timeout,
            )
        except AgentTimeoutError:
            raise
        except NexusOpsError:
            raise

        result = AgentInvokeResponse(**response)
        return result

    async def invoke_async(
        self,
        agent_id: str,
        query: Optional[str] = None,
        action: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        context: Optional[AgentRequestContext] = None,
        conversation_id: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> AgentInvokeResponse:
        """
        Invoke an agent (asynchronous).

        See invoke() for parameter details.

        Example:
            result = await client.agents.invoke_async(
                agent_id="nexusops.k8s",
                action="get_pods",
                params={"namespace": "production"}
            )
            print(result.content.text)
        """
        if action:
            query_str = f"{action}"
            if params:
                param_str = " ".join(f"{k}={v}" for k, v in params.items())
                query_str = f"{action} {param_str}"
        else:
            query_str = query or ""

        request_id = str(uuid.uuid4())
        conv_id = conversation_id or str(uuid.uuid4())

        payload = {
            "request_id": request_id,
            "conversation_id": conv_id,
            "agent_id": agent_id,
            "query": query_str,
        }

        if context:
            payload["context"] = context.model_dump()

        response = await self._client._request_async(
            method="POST",
            path=f"/api/agents/{agent_id}/invoke",
            json=payload,
            timeout=timeout,
        )

        result = AgentInvokeResponse(**response)
        return result

    # ============================================
    # Discovery
    # ============================================

    def list(self) -> AgentListResponse:
        """
        List all available agents (synchronous).

        Returns:
            AgentListResponse with list of agents
        """
        response = self._client._request(
            method="GET",
            path="/api/agents",
        )
        return AgentListResponse(
            agents=[AgentManifest(**a) for a in response.get("agents", [])],
            total=len(response.get("agents", [])),
        )

    async def list_async(self) -> AgentListResponse:
        """
        List all available agents (asynchronous).

        Returns:
            AgentListResponse with list of agents
        """
        response = await self._client._request_async(
            method="GET",
            path="/api/agents",
        )
        return AgentListResponse(
            agents=[AgentManifest(**a) for a in response.get("agents", [])],
            total=len(response.get("agents", [])),
        )

    def get(self, agent_id: str) -> AgentManifest:
        """
        Get details of a specific agent (synchronous).

        Args:
            agent_id: ID of the agent

        Returns:
            AgentManifest with agent details

        Raises:
            AgentNotFoundError: If the agent doesn't exist
        """
        response = self._client._request(
            method="GET",
            path=f"/api/agents/{agent_id}",
        )
        return AgentManifest(**response)

    async def get_async(self, agent_id: str) -> AgentManifest:
        """
        Get details of a specific agent (asynchronous).

        Args:
            agent_id: ID of the agent

        Returns:
            AgentManifest with agent details

        Raises:
            AgentNotFoundError: If the agent doesn't exist
        """
        response = await self._client._request_async(
            method="GET",
            path=f"/api/agents/{agent_id}",
        )
        return AgentManifest(**response)

    def get_tools(self, agent_id: str) -> List[Dict[str, Any]]:
        """
        Get tools available for an agent (synchronous).

        Args:
            agent_id: ID of the agent

        Returns:
            List of tool definitions
        """
        response = self._client._request(
            method="GET",
            path=f"/api/agents/{agent_id}/tools",
        )
        return response.get("tools", [])

    async def get_tools_async(self, agent_id: str) -> List[Dict[str, Any]]:
        """
        Get tools available for an agent (asynchronous).

        Args:
            agent_id: ID of the agent

        Returns:
            List of tool definitions
        """
        response = await self._client._request_async(
            method="GET",
            path=f"/api/agents/{agent_id}/tools",
        )
        return response.get("tools", [])


class AgentClient:
    """
    Main client for interacting with the NexusOps Agent API.

    Provides both synchronous and asynchronous interfaces for
    agent registration, invocation, and management.

    Example:
        from nexusops_sdk import AgentClient, AgentConfig

        # Initialize client
        client = AgentClient(config=AgentConfig(
            base_url="https://nexusops.example.com",
            api_key="your-api-key"
        ))

        # Register an agent
        await client.agents.register(
            agent_id="my-custom-agent",
            name="My Custom Agent",
            capabilities=["data-processing", "report-generation"],
            endpoint="https://my-agent.example.com/webhook"
        )

        # Invoke an agent
        result = client.agents.invoke(
            agent_id="nexusops.k8s",
            action="get_pods",
            params={"namespace": "production"}
        )
    """

    def __init__(self, config: AgentConfig):
        """
        Initialize the AgentClient.

        Args:
            config: Configuration containing base_url, api_key, and options
        """
        self.config = config
        self._sync_client: Optional[httpx.Client] = None
        self._async_client: Optional[httpx.AsyncClient] = None

        # Create namespaces
        self.agents = AgentsNamespace(self)

    def _get_headers(self) -> Dict[str, str]:
        """Get default headers for requests."""
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "NexusOps-Python-SDK/1.0.0",
        }

    def _get_sync_client(self) -> httpx.Client:
        """Get or create the synchronous HTTP client."""
        if self._sync_client is None:
            self._sync_client = httpx.Client(
                base_url=self.config.base_url,
                headers=self._get_headers(),
                timeout=httpx.Timeout(self.config.timeout),
                verify=self.config.verify_ssl,
            )
        return self._sync_client

    def _get_async_client(self) -> httpx.AsyncClient:
        """Get or create the asynchronous HTTP client."""
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                base_url=self.config.base_url,
                headers=self._get_headers(),
                timeout=httpx.Timeout(self.config.timeout),
                verify=self.config.verify_ssl,
            )
        return self._async_client

    def _build_url(self, path: str) -> str:
        """Build full URL from path."""
        return f"{self.config.base_url.rstrip('/')}{path}"

    def _handle_error_response(self, response: httpx.Response) -> None:
        """Handle error responses and raise appropriate exceptions."""
        try:
            error_data = response.json()
            error_code = error_data.get("code", "UNKNOWN_ERROR")
            error_message = error_data.get("message", response.text)
            error_details = error_data.get("details", {})
            retry_after = error_data.get("retry_after")
        except (json.JSONDecodeError, ValueError):
            error_code = "UNKNOWN_ERROR"
            error_message = response.text
            error_details = {}
            retry_after = None

        # Extract detail from HTTPException format
        if "detail" in error_data:
            detail = error_data["detail"]
            if isinstance(detail, dict):
                error_code = detail.get("code", error_code)
                error_message = detail.get("message", error_message)
                error_details = detail.get("details", error_details)

        # Map status codes to exceptions
        if response.status_code == 401:
            raise AuthenticationError(
                message=error_message,
                details=error_details,
            )
        elif response.status_code == 403:
            if error_code == "AGENT_NOT_INSTALLED":
                agent_id = error_details.get("agent_id", "unknown")
                raise AgentNotInstalledError(
                    agent_id=agent_id,
                    message=error_message,
                    details=error_details,
                )
            elif error_code == "AGENT_DISABLED":
                agent_id = error_details.get("agent_id", "unknown")
                raise AgentDisabledError(
                    agent_id=agent_id,
                    message=error_message,
                    details=error_details,
                )
            else:
                raise AuthorizationError(
                    message=error_message,
                    details=error_details,
                )
        elif response.status_code == 404:
            if "agent" in error_message.lower() or error_code == "AGENT_NOT_FOUND":
                raise AgentNotFoundError(
                    agent_id=error_details.get("agent_id", "unknown"),
                    message=error_message,
                    details=error_details,
                )
            else:
                raise NexusOpsError(
                    message=error_message,
                    code=error_code,
                    details=error_details,
                )
        elif response.status_code == 422:
            raise ValidationError(
                message=error_message,
                details=error_details,
            )
        elif response.status_code == 429:
            raise RateLimitError(
                message=error_message,
                retry_after=retry_after or int(response.headers.get("Retry-After", 60)),
                details=error_details,
            )
        elif response.status_code >= 500:
            raise NexusOpsError(
                message=error_message,
                code=error_code,
                details=error_details,
            )
        else:
            raise NexusOpsError(
                message=error_message,
                code=error_code,
                details=error_details,
            )

    @retry(
        retry=retry_if_exception_type(NexusOpsConnectionError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def _request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Make a synchronous HTTP request with retry logic.

        Args:
            method: HTTP method
            path: API path
            json: JSON body
            timeout: Request timeout override

        Returns:
            Response JSON data

        Raises:
            NexusOpsError: For API errors
            AgentTimeoutError: For timeout errors
        """
        client = self._get_sync_client()

        try:
            timeout_config = httpx.Timeout(timeout or self.config.timeout)
            response = client.request(
                method=method,
                url=path,
                json=json,
                timeout=timeout_config,
            )
        except httpx.TimeoutException as e:
            raise AgentTimeoutError(
                agent_id=json.get("agent_id", "unknown") if json else "unknown",
                timeout_seconds=timeout or self.config.timeout,
                message=str(e),
            )
        except httpx.ConnectError as e:
            raise NexusOpsConnectionError(
                base_url=self.config.base_url,
                message=f"Failed to connect to {self.config.base_url}: {e}",
            )
        except httpx.RequestError as e:
            raise NexusOpsConnectionError(
                base_url=self.config.base_url,
                message=f"Request failed: {e}",
            )

        if response.status_code >= 400:
            self._handle_error_response(response)

        return response.json()

    @retry(
        retry=retry_if_exception_type(NexusOpsConnectionError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _request_async(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Make an asynchronous HTTP request with retry logic.

        Args:
            method: HTTP method
            path: API path
            json: JSON body
            timeout: Request timeout override

        Returns:
            Response JSON data

        Raises:
            NexusOpsError: For API errors
            AgentTimeoutError: For timeout errors
        """
        client = self._get_async_client()

        try:
            timeout_config = httpx.Timeout(timeout or self.config.timeout)
            response = await client.request(
                method=method,
                url=path,
                json=json,
                timeout=timeout_config,
            )
        except httpx.TimeoutException as e:
            raise AgentTimeoutError(
                agent_id=json.get("agent_id", "unknown") if json else "unknown",
                timeout_seconds=timeout or self.config.timeout,
                message=str(e),
            )
        except httpx.ConnectError as e:
            raise NexusOpsConnectionError(
                base_url=self.config.base_url,
                message=f"Failed to connect to {self.config.base_url}: {e}",
            )
        except httpx.RequestError as e:
            raise NexusOpsConnectionError(
                base_url=self.config.base_url,
                message=f"Request failed: {e}",
            )

        if response.status_code >= 400:
            self._handle_error_response(response)

        return response.json()

    def close(self) -> None:
        """Close the client and release resources."""
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None

    async def close_async(self) -> None:
        """Close the async client and release resources."""
        if self._async_client:
            await self._async_client.aclose()
            self._async_client = None

    def __enter__(self) -> "AgentClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    async def __aenter__(self) -> "AgentClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close_async()
