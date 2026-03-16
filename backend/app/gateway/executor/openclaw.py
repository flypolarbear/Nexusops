"""
NexusOps Gateway - OpenClaw Executor

Routes agent invocations to the OpenClaw gateway (port 18789).
Falls back to BuiltinExecutor if OpenClaw is unavailable.
"""

import logging
import os
from typing import Optional

import httpx

from app.gateway.executor.base import (
    BaseExecutor,
    ExecutorType,
    ExecutorRequest,
    ExecutorResult,
)

logger = logging.getLogger(__name__)

# Map NexusOps agent IDs to OpenClaw agent IDs
_AGENT_ID_MAP = {
    "nexusops.chat": "nexusops-chat",
    "nexusops.k8s": "nexusops-k8s",
    "nexusops.deploy": "nexusops-deploy",
    "nexusops.dns": "nexusops-dns",
    "nexusops.logs": "nexusops-logs",
    "nexusops.cost": "nexusops-cost",
    "nexusops.cicd": "nexusops-cicd",
    "nexusops.git": "nexusops-git",
}


class OpenClawExecutor(BaseExecutor):
    """
    Executor that routes agent invocations to the OpenClaw gateway.

    OpenClaw gateway runs at OPENCLAW_GATEWAY_URL (default: http://localhost:18789).
    On connection failure, falls back to BuiltinExecutor automatically.
    """

    def __init__(self, gateway_url: Optional[str] = None):
        self._gateway_url = (
            gateway_url
            or os.getenv("OPENCLAW_GATEWAY_URL", "http://localhost:18789")
        ).rstrip("/")
        self._timeout = float(os.getenv("OPENCLAW_TIMEOUT", "60"))
        self._fallback: Optional[BaseExecutor] = None

    def set_fallback(self, executor: BaseExecutor) -> None:
        """Set a fallback executor used when OpenClaw is unreachable."""
        self._fallback = executor

    @property
    def executor_type(self) -> ExecutorType:
        return ExecutorType.REMOTE

    async def execute(self, request: ExecutorRequest) -> ExecutorResult:
        agent_id = request.context.agent_id
        openclaw_agent_id = _AGENT_ID_MAP.get(agent_id, agent_id.replace(".", "-"))

        # OpenResponses API (POST /v1/responses)
        payload = {
            "model": f"openclaw:{openclaw_agent_id}",
            "input": request.query,
        }

        auth_token = os.getenv("OPENCLAW_AUTH_TOKEN", "")
        headers = {"Content-Type": "application/json"}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._gateway_url}/v1/responses",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

            # Extract text from output items
            text = ""
            for item in data.get("output", []):
                for part in item.get("content", []):
                    if part.get("type") == "output_text":
                        text += part.get("text", "")

            return ExecutorResult(
                success=True,
                content={"text": text or data.get("content", ""), "format": "markdown"},
                structured_output=data.get("structured_output"),
                suggested_actions=data.get("suggested_actions", []),
                related_resources=data.get("related_resources", []),
                metadata={
                    "executor": "openclaw",
                    "openclaw_agent_id": openclaw_agent_id,
                    "openclaw_response_id": data.get("id"),
                },
            )

        except (httpx.ConnectError, httpx.TimeoutException) as e:
            logger.warning("OpenClaw unavailable at %s, falling back to builtin: %s", self._gateway_url, e)
            if self._fallback is not None:
                return await self._fallback.execute(request)
            return self._make_error_result(
                code="OPENCLAW_UNAVAILABLE",
                message=f"OpenClaw gateway not reachable at {self._gateway_url}",
                details={"agent_id": agent_id, "gateway_url": self._gateway_url},
            )

        except httpx.HTTPStatusError as e:
            return self._make_error_result(
                code="OPENCLAW_HTTP_ERROR",
                message=f"OpenClaw gateway returned {e.response.status_code}",
                details={"agent_id": agent_id, "status_code": e.response.status_code},
            )

        except Exception as e:
            return self._make_error_result(
                code="OPENCLAW_ERROR",
                message=str(e),
                details={"agent_id": agent_id, "exception": type(e).__name__},
            )

    async def health_check(self) -> bool:
        """Check if OpenClaw gateway is reachable."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self._gateway_url}/")
                return response.status_code < 500
        except Exception:
            return False
