"""
NexusOps SDK - Exceptions

Standardized error codes and exceptions aligned with MK-006 Gateway Contract.

Error Code Format: {CATEGORY}_{SUBCATEGORY}_{SPECIFIC}
Categories: INPUT, AUTH, AGENT, EXEC, SYSTEM
"""

from enum import Enum
from typing import Any, Dict, Optional


class ErrorCode(str, Enum):
    """Standardized error codes from Gateway."""

    # Input Validation Errors (INPUT_*) - HTTP 400
    INPUT_INVALID_JSON = "INPUT_INVALID_JSON"
    INPUT_SCHEMA_VIOLATION = "INPUT_SCHEMA_VIOLATION"
    INPUT_MISSING_FIELD = "INPUT_MISSING_FIELD"
    INPUT_INVALID_FORMAT = "INPUT_INVALID_FORMAT"
    INPUT_VALUE_OUT_OF_RANGE = "INPUT_VALUE_OUT_OF_RANGE"
    INPUT_QUERY_TOO_LONG = "INPUT_QUERY_TOO_LONG"
    INPUT_INVALID_AGENT_ID = "INPUT_INVALID_AGENT_ID"

    # Auth Errors (AUTH_*) - HTTP 401/403
    AUTH_TOKEN_MISSING = "AUTH_TOKEN_MISSING"
    AUTH_TOKEN_INVALID = "AUTH_TOKEN_INVALID"
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    AUTH_PERMISSION_DENIED = "AUTH_PERMISSION_DENIED"
    AUTH_QUOTA_EXCEEDED = "AUTH_QUOTA_EXCEEDED"
    AUTH_TENANT_MISMATCH = "AUTH_TENANT_MISMATCH"

    # Agent Errors (AGENT_*) - HTTP 404/409/422
    AGENT_NOT_FOUND = "AGENT_NOT_FOUND"
    AGENT_INACTIVE = "AGENT_INACTIVE"
    AGENT_NOT_INSTALLED = "AGENT_NOT_INSTALLED"
    AGENT_DISABLED = "AGENT_DISABLED"
    AGENT_VERSION_MISMATCH = "AGENT_VERSION_MISMATCH"
    AGENT_BUSY = "AGENT_BUSY"
    AGENT_INPUT_REJECTED = "AGENT_INPUT_REJECTED"
    AGENT_OUTPUT_INVALID = "AGENT_OUTPUT_INVALID"
    AGENT_ENDPOINT_MISSING = "AGENT_ENDPOINT_MISSING"

    # Execution Errors (EXEC_*) - HTTP 500/502/504
    EXEC_TIMEOUT = "EXEC_TIMEOUT"
    EXEC_TOOL_FAILED = "EXEC_TOOL_FAILED"
    EXEC_DOWNSTREAM_ERROR = "EXEC_DOWNSTREAM_ERROR"
    EXEC_PARTIAL_FAILURE = "EXEC_PARTIAL_FAILURE"
    EXEC_RESOURCE_CONFLICT = "EXEC_RESOURCE_CONFLICT"
    EXEC_CIRCUIT_OPEN = "EXEC_CIRCUIT_OPEN"
    EXEC_INTERNAL_ERROR = "EXEC_INTERNAL_ERROR"

    # System Errors (SYSTEM_*) - HTTP 500/503
    SYSTEM_INTERNAL_ERROR = "SYSTEM_INTERNAL_ERROR"
    SYSTEM_UNAVAILABLE = "SYSTEM_UNAVAILABLE"
    SYSTEM_OVERLOADED = "SYSTEM_OVERLOADED"
    SYSTEM_MAINTENANCE = "SYSTEM_MAINTENANCE"


# HTTP Status Code Mapping
ERROR_HTTP_STATUS: Dict[ErrorCode, int] = {
    # Input - 400
    ErrorCode.INPUT_INVALID_JSON: 400,
    ErrorCode.INPUT_SCHEMA_VIOLATION: 400,
    ErrorCode.INPUT_MISSING_FIELD: 400,
    ErrorCode.INPUT_INVALID_FORMAT: 400,
    ErrorCode.INPUT_VALUE_OUT_OF_RANGE: 400,
    ErrorCode.INPUT_QUERY_TOO_LONG: 400,
    ErrorCode.INPUT_INVALID_AGENT_ID: 400,
    # Auth - 401/403
    ErrorCode.AUTH_TOKEN_MISSING: 401,
    ErrorCode.AUTH_TOKEN_INVALID: 401,
    ErrorCode.AUTH_TOKEN_EXPIRED: 401,
    ErrorCode.AUTH_PERMISSION_DENIED: 403,
    ErrorCode.AUTH_QUOTA_EXCEEDED: 429,
    ErrorCode.AUTH_TENANT_MISMATCH: 403,
    # Agent - 404/409/422
    ErrorCode.AGENT_NOT_FOUND: 404,
    ErrorCode.AGENT_INACTIVE: 409,
    ErrorCode.AGENT_NOT_INSTALLED: 403,
    ErrorCode.AGENT_DISABLED: 403,
    ErrorCode.AGENT_VERSION_MISMATCH: 409,
    ErrorCode.AGENT_BUSY: 503,
    ErrorCode.AGENT_INPUT_REJECTED: 422,
    ErrorCode.AGENT_OUTPUT_INVALID: 422,
    ErrorCode.AGENT_ENDPOINT_MISSING: 500,
    # Exec - 500/502/504
    ErrorCode.EXEC_TIMEOUT: 504,
    ErrorCode.EXEC_TOOL_FAILED: 500,
    ErrorCode.EXEC_DOWNSTREAM_ERROR: 502,
    ErrorCode.EXEC_PARTIAL_FAILURE: 500,
    ErrorCode.EXEC_RESOURCE_CONFLICT: 409,
    ErrorCode.EXEC_CIRCUIT_OPEN: 503,
    ErrorCode.EXEC_INTERNAL_ERROR: 500,
    # System - 500/503
    ErrorCode.SYSTEM_INTERNAL_ERROR: 500,
    ErrorCode.SYSTEM_UNAVAILABLE: 503,
    ErrorCode.SYSTEM_OVERLOADED: 503,
    ErrorCode.SYSTEM_MAINTENANCE: 503,
}

# Retryable errors
RETRYABLE_ERRORS: set[ErrorCode] = {
    ErrorCode.AUTH_TOKEN_EXPIRED,
    ErrorCode.AUTH_QUOTA_EXCEEDED,
    ErrorCode.AGENT_BUSY,
    ErrorCode.AGENT_OUTPUT_INVALID,
    ErrorCode.EXEC_TIMEOUT,
    ErrorCode.EXEC_TOOL_FAILED,
    ErrorCode.EXEC_DOWNSTREAM_ERROR,
    ErrorCode.EXEC_PARTIAL_FAILURE,
    ErrorCode.EXEC_RESOURCE_CONFLICT,
    ErrorCode.EXEC_CIRCUIT_OPEN,
    ErrorCode.SYSTEM_INTERNAL_ERROR,
    ErrorCode.SYSTEM_UNAVAILABLE,
    ErrorCode.SYSTEM_OVERLOADED,
}


class NexusOpsError(Exception):
    """Base exception for all NexusOps SDK errors."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None,
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.retry_after = retry_after
        self.trace_id = trace_id
        self.request_id = request_id
        super().__init__(message)

    @property
    def http_status(self) -> int:
        """Get HTTP status code for this error."""
        return ERROR_HTTP_STATUS.get(self.code, 500)

    @property
    def is_retryable(self) -> bool:
        """Check if this error is retryable."""
        return self.code in RETRYABLE_ERRORS

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "code": self.code.value,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        if self.retry_after is not None:
            result["retry_after"] = self.retry_after
        if self.trace_id:
            result["trace_id"] = self.trace_id
        if self.request_id:
            result["request_id"] = self.request_id
        return result

    @classmethod
    def from_response(cls, data: Dict[str, Any]) -> "NexusOpsError":
        """Create exception from API response."""
        error_data = data.get("error", data)
        code_str = error_data.get("code", "SYSTEM_INTERNAL_ERROR")

        try:
            code = ErrorCode(code_str)
        except ValueError:
            code = ErrorCode.SYSTEM_INTERNAL_ERROR

        # Determine the appropriate exception class
        error_class = _get_error_class(code)

        return error_class(
            code=code,
            message=error_data.get("message", "Unknown error"),
            details=error_data.get("details"),
            retry_after=error_data.get("retry_after"),
            trace_id=data.get("trace_id"),
            request_id=data.get("request_id"),
        )


class InputError(NexusOpsError):
    """Input validation error."""

    def __init__(
        self,
        code: ErrorCode = ErrorCode.INPUT_SCHEMA_VIOLATION,
        message: str = "Input validation failed",
        details: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        super().__init__(code, message, details, **kwargs)


class AuthError(NexusOpsError):
    """Authentication/authorization error."""

    def __init__(
        self,
        code: ErrorCode = ErrorCode.AUTH_TOKEN_MISSING,
        message: str = "Authentication required",
        details: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        super().__init__(code, message, details, **kwargs)


class AgentError(NexusOpsError):
    """Agent-related error."""

    def __init__(
        self,
        code: ErrorCode = ErrorCode.AGENT_NOT_FOUND,
        message: str = "Agent error",
        details: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        super().__init__(code, message, details, **kwargs)


class ExecError(NexusOpsError):
    """Execution error."""

    def __init__(
        self,
        code: ErrorCode = ErrorCode.EXEC_INTERNAL_ERROR,
        message: str = "Execution error",
        details: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(code, message, details, retry_after, **kwargs)


class SystemError(NexusOpsError):
    """System error."""

    def __init__(
        self,
        code: ErrorCode = ErrorCode.SYSTEM_INTERNAL_ERROR,
        message: str = "Internal server error",
        details: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(code, message, details, retry_after, **kwargs)


def _get_error_class(code: ErrorCode) -> type[NexusOpsError]:
    """Get the appropriate exception class for an error code."""
    if code.value.startswith("INPUT_"):
        return InputError
    elif code.value.startswith("AUTH_"):
        return AuthError
    elif code.value.startswith("AGENT_"):
        return AgentError
    elif code.value.startswith("EXEC_"):
        return ExecError
    elif code.value.startswith("SYSTEM_"):
        return SystemError
    return NexusOpsError


# Helper functions for creating common errors

def agent_not_found(agent_id: str, trace_id: Optional[str] = None) -> AgentError:
    """Create agent not found error."""
    return AgentError(
        code=ErrorCode.AGENT_NOT_FOUND,
        message=f"Agent not found: {agent_id}",
        details={"agent_id": agent_id},
        trace_id=trace_id,
    )


def agent_not_installed(agent_id: str, trace_id: Optional[str] = None) -> AgentError:
    """Create agent not installed error."""
    return AgentError(
        code=ErrorCode.AGENT_NOT_INSTALLED,
        message=f"Agent '{agent_id}' is not installed. Please install it first.",
        details={"agent_id": agent_id},
        trace_id=trace_id,
    )


def agent_disabled(agent_id: str, trace_id: Optional[str] = None) -> AgentError:
    """Create agent disabled error."""
    return AgentError(
        code=ErrorCode.AGENT_DISABLED,
        message=f"Agent '{agent_id}' is disabled. Please enable it first.",
        details={"agent_id": agent_id},
        trace_id=trace_id,
    )


def exec_timeout(timeout_ms: int, endpoint: Optional[str] = None, trace_id: Optional[str] = None) -> ExecError:
    """Create execution timeout error."""
    details = {"timeout_ms": timeout_ms}
    if endpoint:
        details["endpoint"] = endpoint
    return ExecError(
        code=ErrorCode.EXEC_TIMEOUT,
        message=f"Execution timed out after {timeout_ms}ms",
        details=details,
        retry_after=5,
        trace_id=trace_id,
    )


def input_schema_violation(errors: list, trace_id: Optional[str] = None) -> InputError:
    """Create schema validation error."""
    return InputError(
        code=ErrorCode.INPUT_SCHEMA_VIOLATION,
        message="Request schema validation failed",
        details={"validation_errors": errors},
        trace_id=trace_id,
    )


def input_missing_field(field: str, trace_id: Optional[str] = None) -> InputError:
    """Create missing field error."""
    return InputError(
        code=ErrorCode.INPUT_MISSING_FIELD,
        message=f"Required field missing: {field}",
        details={"field": field},
        trace_id=trace_id,
    )
