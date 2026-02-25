"""
NexusOps Gateway Module

MK-006: Gateway 调用契约与错误模型
MK-007: Gateway 插件执行边界

This module provides the unified Gateway layer for Agent invocation.
"""

from app.gateway.errors import (
    ErrorCode,
    GatewayError,
    InputError,
    AuthError,
    AgentError,
    ExecError,
    SystemError,
)
from app.gateway.trace import generate_trace_id, TraceContext
from app.gateway.response import build_response, build_error_response
from app.gateway.contract import (
    InvokeRequest,
    InvokeResponse,
    ResponseContent,
    ErrorDetail,
    SuggestedAction,
    RelatedResource,
    ToolCall,
    ResponseMetadata,
)

__all__ = [
    # Errors
    "ErrorCode",
    "GatewayError",
    "InputError",
    "AuthError",
    "AgentError",
    "ExecError",
    "SystemError",
    # Trace
    "generate_trace_id",
    "TraceContext",
    # Response
    "build_response",
    "build_error_response",
    # Contract
    "InvokeRequest",
    "InvokeResponse",
    "ResponseContent",
    "ErrorDetail",
    "SuggestedAction",
    "RelatedResource",
    "ToolCall",
    "ResponseMetadata",
]
