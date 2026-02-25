"""
NexusOps Gateway - Remote Executor

MK-007: 第三方 Agent 执行器

Executes remote agents via HTTP endpoints.
"""

import httpx
from typing import Optional, Dict, Any

from app.gateway.executor.base import (
    BaseExecutor,
    ExecutorType,
    ExecutorRequest,
    ExecutorResult,
)


class RemoteExecutor(BaseExecutor):
    """
    Remote agent executor.

    Executes third-party agents via HTTP calls.
    """

    def __init__(self, http_client: Optional[httpx.AsyncClient] = None):
        self._client = http_client
        self._owned_client = http_client is None

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure HTTP client is initialized"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    @property
    def executor_type(self) -> ExecutorType:
        return ExecutorType.REMOTE

    async def execute(self, request: ExecutorRequest) -> ExecutorResult:
        """Execute a remote agent"""
        endpoint = request.context.endpoint

        if not endpoint:
            return self._make_error_result(
                code="AGENT_ENDPOINT_MISSING",
                message="No endpoint configured for remote agent",
                details={"agent_id": request.context.agent_id},
            )

        # Build remote request
        remote_request = {
            "request_id": request.context.request_id,
            "trace_id": request.context.trace_id,
            "agent_id": request.context.agent_id,
            "query": request.query,
            "context": request.request_context,
            "output_config": request.output_config,
            "tools": request.tools,
        }

        headers = {
            "Content-Type": "application/json",
            "X-Trace-ID": request.context.trace_id,
            "X-Request-ID": request.context.request_id,
        }

        # Add auth if available
        if request.context.auth_context:
            if "api_key" in request.context.auth_context:
                headers["Authorization"] = f"Bearer {request.context.auth_context['api_key']}"

        try:
            client = await self._ensure_client()
            timeout_seconds = request.context.timeout_ms / 1000

            response = await client.post(
                f"{endpoint}/invoke",
                json=remote_request,
                headers=headers,
                timeout=timeout_seconds,
            )

            if response.status_code >= 400:
                return self._handle_error_response(response, request)

            data = response.json()
            return self._parse_response(data, request)

        except httpx.TimeoutException:
            return self._make_error_result(
                code="EXEC_TIMEOUT",
                message=f"Remote agent timeout after {request.context.timeout_ms}ms",
                details={"endpoint": endpoint},
                retry_after=5,
            )

        except httpx.RequestError as e:
            return self._make_error_result(
                code="EXEC_DOWNSTREAM_ERROR",
                message=f"Connection error: {str(e)}",
                details={"endpoint": endpoint, "error": str(e)},
                retry_after=10,
            )

        except Exception as e:
            return self._make_error_result(
                code="EXEC_INTERNAL_ERROR",
                message=f"Unexpected error: {str(e)}",
                details={"endpoint": endpoint, "error": str(e)},
            )

    def _handle_error_response(
        self,
        response: httpx.Response,
        request: ExecutorRequest,
    ) -> ExecutorResult:
        """Handle HTTP error response"""
        try:
            data = response.json()
            error = data.get("error", {})
        except Exception:
            error = {
                "code": f"HTTP_{response.status_code}",
                "message": response.text[:500] if response.text else "Unknown error",
            }

        return ExecutorResult(
            success=False,
            content={"text": error.get("message", "Remote agent error"), "format": "plain"},
            error={
                "code": error.get("code", "EXEC_DOWNSTREAM_ERROR"),
                "message": error.get("message", "Remote agent error"),
                "details": {
                    "http_status": response.status_code,
                    "endpoint": request.context.endpoint,
                    "original_error": error,
                },
            },
        )

    def _parse_response(self, data: dict, request: ExecutorRequest) -> ExecutorResult:
        """Parse remote agent response"""
        # Validate response format
        if "content" not in data:
            return self._make_error_result(
                code="AGENT_OUTPUT_INVALID",
                message="Remote agent returned invalid response: missing content",
                details={"missing_field": "content"},
            )

        status = data.get("status", "success")

        return ExecutorResult(
            success=(status == "success"),
            content=data["content"],
            structured_output=data.get("structured_output"),
            suggested_actions=data.get("suggested_actions", []),
            related_resources=data.get("related_resources", []),
            tool_calls=data.get("tool_calls"),
            metadata={
                **data.get("metadata", {}),
                "endpoint": request.context.endpoint,
                "agent_type": "remote",
            },
            error=data.get("error") if status == "error" else None,
        )

    async def health_check(self) -> bool:
        """Check executor health"""
        # In production, check connection pool status
        return True

    async def close(self):
        """Close HTTP client"""
        if self._owned_client and self._client:
            await self._client.aclose()
            self._client = None


class MockRemoteExecutor(BaseExecutor):
    """
    Mock remote executor for testing.

    Returns mock responses without making actual HTTP calls.
    """

    @property
    def executor_type(self) -> ExecutorType:
        return ExecutorType.MOCK

    async def execute(self, request: ExecutorRequest) -> ExecutorResult:
        """Execute with mock response"""
        import asyncio

        # Simulate processing delay
        await asyncio.sleep(0.3)

        return ExecutorResult(
            success=True,
            content={
                "text": f"## Third-party Agent Response\n\n**Agent:** {request.context.agent_id}\n**Trace ID:** {request.context.trace_id}\n\nYour request has been processed by this third-party agent.",
                "format": "markdown",
            },
            structured_output={
                "type": "third_party_response",
                "agent_id": request.context.agent_id,
                "query": request.query,
                "processed": True,
            },
            metadata={
                "trace_id": request.context.trace_id,
                "agent_type": "third_party",
                "execution_mode": "mock",
            },
        )

    async def health_check(self) -> bool:
        return True
