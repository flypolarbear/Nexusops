"""
NexusOps SDK - Exceptions

Custom exception classes for the NexusOps Python SDK.
"""

from typing import Optional, Dict, Any


class NexusOpsError(Exception):
    """
    Base exception for all NexusOps SDK errors.

    All SDK-specific exceptions inherit from this class.
    """

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code or "UNKNOWN_ERROR"
        self.details = details or {}
        self.retry_after = retry_after

    def __str__(self) -> str:
        parts = [f"[{self.code}] {self.message}"]
        if self.details:
            parts.append(f"Details: {self.details}")
        if self.retry_after:
            parts.append(f"Retry after: {self.retry_after}s")
        return " | ".join(parts)


class AgentNotFoundError(NexusOpsError):
    """
    Raised when the requested agent does not exist.

    This can happen when:
    - The agent_id is incorrect
    - The agent has been unregistered
    - The agent is not available in the current scope
    """

    def __init__(
        self,
        agent_id: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message or f"Agent '{agent_id}' not found",
            code="AGENT_NOT_FOUND",
            details={"agent_id": agent_id, **(details or {})},
        )
        self.agent_id = agent_id


class AgentTimeoutError(NexusOpsError):
    """
    Raised when an agent invocation times out.

    This can happen when:
    - The agent takes too long to respond
    - Network connectivity issues
    - The agent is overloaded
    """

    def __init__(
        self,
        agent_id: str,
        timeout_seconds: float,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message or f"Agent '{agent_id}' invocation timed out after {timeout_seconds}s",
            code="AGENT_TIMEOUT",
            details={
                "agent_id": agent_id,
                "timeout_seconds": timeout_seconds,
                **(details or {}),
            },
        )
        self.agent_id = agent_id
        self.timeout_seconds = timeout_seconds


class AuthenticationError(NexusOpsError):
    """
    Raised when authentication fails.

    This can happen when:
    - Invalid API key
    - Expired token
    - Missing credentials
    """

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message or "Authentication failed. Please check your API key or credentials.",
            code="AUTHENTICATION_ERROR",
            details=details or {},
        )


class AuthorizationError(NexusOpsError):
    """
    Raised when authorization fails.

    This can happen when:
    - Insufficient permissions
    - Access denied to resource
    - Scope mismatch
    """

    def __init__(
        self,
        message: Optional[str] = None,
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        if resource:
            details["resource"] = resource
        super().__init__(
            message or "Authorization failed. Insufficient permissions.",
            code="AUTHORIZATION_ERROR",
            details=details,
        )


class AgentNotInstalledError(NexusOpsError):
    """
    Raised when trying to invoke an agent that is not installed.

    This applies to third-party agents that need to be installed
    before they can be invoked.
    """

    def __init__(
        self,
        agent_id: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message or f"Agent '{agent_id}' is not installed. Please install it first.",
            code="AGENT_NOT_INSTALLED",
            details={"agent_id": agent_id, **(details or {})},
        )
        self.agent_id = agent_id


class AgentDisabledError(NexusOpsError):
    """
    Raised when trying to invoke a disabled agent.

    The agent must be enabled before it can be invoked.
    """

    def __init__(
        self,
        agent_id: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message or f"Agent '{agent_id}' is disabled. Please enable it first.",
            code="AGENT_DISABLED",
            details={"agent_id": agent_id, **(details or {})},
        )
        self.agent_id = agent_id


class ValidationError(NexusOpsError):
    """
    Raised when request validation fails.

    This can happen when:
    - Invalid parameters
    - Missing required fields
    - Schema mismatch
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        if field:
            details["field"] = field
        super().__init__(
            message,
            code="VALIDATION_ERROR",
            details=details,
        )


class ConnectionError(NexusOpsError):
    """
    Raised when connection to the NexusOps server fails.

    This can happen when:
    - Server is unreachable
    - Network issues
    - DNS resolution failure
    """

    def __init__(
        self,
        message: Optional[str] = None,
        base_url: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        if base_url:
            details["base_url"] = base_url
        super().__init__(
            message or "Failed to connect to NexusOps server.",
            code="CONNECTION_ERROR",
            details=details,
        )


class RateLimitError(NexusOpsError):
    """
    Raised when rate limit is exceeded.

    Contains retry_after information for when to retry the request.
    """

    def __init__(
        self,
        message: Optional[str] = None,
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message or "Rate limit exceeded. Please retry later.",
            code="RATE_LIMIT_EXCEEDED",
            details=details or {},
            retry_after=retry_after,
        )
