"""
NexusOps Gateway - Response Builder

MK-006: 响应构建器

Provides utilities for building standardized responses.
"""

from typing import Optional, List, Any, Dict, Literal
from datetime import datetime

from app.gateway.contract import (
    InvokeResponse,
    ResponseContent,
    ResponseMetadata,
    SuggestedAction,
    RelatedResource,
    ToolCall,
    ErrorDetail,
)
from app.gateway.errors import GatewayError, ErrorCode


def build_response(
    request_id: str,
    trace_id: str,
    status: Literal["success", "error", "partial", "pending"] = "success",
    text: str = "",
    format: Literal["markdown", "json", "plain"] = "markdown",
    data: Optional[Any] = None,
    structured_output: Optional[Any] = None,
    suggested_actions: Optional[List[Dict[str, Any]]] = None,
    related_resources: Optional[List[Dict[str, Any]]] = None,
    tool_calls: Optional[List[Dict[str, Any]]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    latency_ms: Optional[int] = None,
    agent_type: Optional[str] = None,
    agent_version: Optional[str] = None,
) -> InvokeResponse:
    """
    Build a standardized success response.

    All responses should be built through this function to ensure consistency.
    """
    response_metadata = ResponseMetadata(
        trace_id=trace_id,
        latency_ms=latency_ms,
        agent_type=agent_type,
        agent_version=agent_version,
    )

    if metadata:
        for key, value in metadata.items():
            if hasattr(response_metadata, key):
                setattr(response_metadata, key, value)
            else:
                if response_metadata.model_extra is None:
                    response_metadata.model_extra = {}
                response_metadata.model_extra[key] = value

    return InvokeResponse(
        request_id=request_id,
        trace_id=trace_id,
        status=status,
        content=ResponseContent(
            text=text,
            format=format,
            data=data,
        ),
        structured_output=structured_output,
        suggested_actions=[
            SuggestedAction(**a) for a in (suggested_actions or [])
        ],
        related_resources=[
            RelatedResource(**r) for r in (related_resources or [])
        ],
        tool_calls=[
            ToolCall(**t) for t in (tool_calls or [])
        ] if tool_calls else None,
        metadata=response_metadata,
    )


def build_error_response(
    request_id: str,
    trace_id: str,
    error: GatewayError,
    latency_ms: Optional[int] = None,
) -> InvokeResponse:
    """
    Build a standardized error response.

    All error responses should be built through this function.
    """
    return InvokeResponse(
        request_id=request_id,
        trace_id=trace_id,
        status="error",
        content=ResponseContent(
            text=error.message,
            format="plain",
        ),
        metadata=ResponseMetadata(
            trace_id=trace_id,
            latency_ms=latency_ms,
        ),
        error=ErrorDetail(
            code=error.code.value,
            message=error.message,
            details=error.details,
            retry_after=error.retry_after,
        ),
    )


def build_partial_response(
    request_id: str,
    trace_id: str,
    text: str = "",
    partial_results: Optional[List[Dict[str, Any]]] = None,
    failed_parts: Optional[List[Dict[str, Any]]] = None,
    latency_ms: Optional[int] = None,
) -> InvokeResponse:
    """
    Build a partial success response.

    Used when some operations succeeded but others failed.
    """
    structured_output = {
        "type": "partial_result",
        "successful": partial_results or [],
        "failed": failed_parts or [],
    }

    return InvokeResponse(
        request_id=request_id,
        trace_id=trace_id,
        status="partial",
        content=ResponseContent(
            text=text,
            format="markdown",
        ),
        structured_output=structured_output,
        metadata=ResponseMetadata(
            trace_id=trace_id,
            latency_ms=latency_ms,
        ),
    )


def build_pending_response(
    request_id: str,
    trace_id: str,
    text: str = "Request is being processed",
    poll_url: Optional[str] = None,
    estimated_time_seconds: Optional[int] = None,
    latency_ms: Optional[int] = None,
) -> InvokeResponse:
    """
    Build a pending response for async operations.

    Used when the operation is still in progress.
    """
    structured_output = {
        "type": "pending",
        "poll_url": poll_url,
        "estimated_time_seconds": estimated_time_seconds,
    }

    suggested_actions = []
    if poll_url:
        suggested_actions.append({
            "id": "poll-status",
            "type": "navigate",
            "label": "Check Status",
            "params": {"url": poll_url},
        })

    return InvokeResponse(
        request_id=request_id,
        trace_id=trace_id,
        status="pending",
        content=ResponseContent(
            text=text,
            format="markdown",
        ),
        structured_output=structured_output,
        suggested_actions=[
            SuggestedAction(**a) for a in suggested_actions
        ],
        metadata=ResponseMetadata(
            trace_id=trace_id,
            latency_ms=latency_ms,
        ),
    )


# Helper for quick responses

def success_response(
    request_id: str,
    trace_id: str,
    text: str,
    **kwargs,
) -> InvokeResponse:
    """Quick success response builder"""
    return build_response(
        request_id=request_id,
        trace_id=trace_id,
        status="success",
        text=text,
        **kwargs,
    )


def error_response(
    request_id: str,
    trace_id: str,
    code: ErrorCode,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    latency_ms: Optional[int] = None,
) -> InvokeResponse:
    """Quick error response builder"""
    from app.gateway.errors import GatewayError
    error = GatewayError(code, message, details)
    return build_error_response(
        request_id=request_id,
        trace_id=trace_id,
        error=error,
        latency_ms=latency_ms,
    )
