"""
NexusOps Gateway - Trace ID Handling

MK-006: Trace ID 规范

- Format: 32-bit lowercase hexadecimal string
- Generated at request entry
- Propagated through all downstream calls
"""

import uuid
import contextvars
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime


# Context variable for trace context
_trace_context: contextvars.ContextVar[Optional["TraceContext"]] = contextvars.ContextVar(
    "trace_context", default=None
)


def generate_trace_id() -> str:
    """
    Generate a 32-character lowercase hexadecimal trace ID.

    Format: {uuid.hex} (32 chars without hyphens)
    """
    return uuid.uuid4().hex


def generate_request_id() -> str:
    """Generate a standard UUID request ID"""
    return str(uuid.uuid4())


@dataclass
class TraceContext:
    """Trace context for request tracking"""

    trace_id: str
    request_id: str
    agent_id: Optional[str] = None
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.utcnow)

    # Parent/child relationships
    parent_trace_id: Optional[str] = None

    # Metadata
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.trace_id:
            self.trace_id = generate_trace_id()
        if not self.request_id:
            self.request_id = generate_request_id()

    def to_headers(self) -> dict:
        """Convert to HTTP headers"""
        headers = {
            "X-Trace-ID": self.trace_id,
            "X-Request-ID": self.request_id,
        }
        if self.conversation_id:
            headers["X-Conversation-ID"] = self.conversation_id
        return headers

    def to_log_dict(self) -> dict:
        """Convert to logging dictionary"""
        result = {
            "trace_id": self.trace_id,
            "request_id": self.request_id,
        }
        if self.agent_id:
            result["agent_id"] = self.agent_id
        if self.conversation_id:
            result["conversation_id"] = self.conversation_id
        if self.user_id:
            result["user_id"] = self.user_id
        if self.tenant_id:
            result["tenant_id"] = self.tenant_id
        return result

    @property
    def elapsed_ms(self) -> int:
        """Get elapsed time in milliseconds"""
        return int((datetime.utcnow() - self.start_time).total_seconds() * 1000)


def init_trace_context(
    request_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> TraceContext:
    """
    Initialize trace context for a request.

    Should be called at the very beginning of request processing.
    """
    context = TraceContext(
        trace_id=trace_id or generate_trace_id(),
        request_id=request_id or generate_request_id(),
        agent_id=agent_id,
        conversation_id=conversation_id,
        user_id=user_id,
        tenant_id=tenant_id,
    )
    _trace_context.set(context)
    return context


def get_trace_context() -> Optional[TraceContext]:
    """Get current trace context"""
    return _trace_context.get()


def set_trace_context(context: TraceContext) -> None:
    """Set trace context"""
    _trace_context.set(context)


def clear_trace_context() -> None:
    """Clear trace context"""
    _trace_context.set(None)


class TraceSpan:
    """Context manager for trace spans"""

    def __init__(
        self,
        operation: str,
        agent_id: Optional[str] = None,
        **metadata,
    ):
        self.operation = operation
        self.agent_id = agent_id
        self.metadata = metadata
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self._token: Optional[contextvars.Token] = None

    def __enter__(self):
        self.start_time = datetime.utcnow()

        # Get or create trace context
        ctx = get_trace_context()
        if ctx is None:
            ctx = init_trace_context(agent_id=self.agent_id)
        elif self.agent_id:
            ctx.agent_id = self.agent_id

        # Add metadata
        if self.metadata:
            ctx.metadata.update(self.metadata)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.utcnow()
        return False

    @property
    def duration_ms(self) -> int:
        """Get duration in milliseconds"""
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time).total_seconds() * 1000)
        return 0


def with_trace(operation: str, **metadata):
    """Decorator for tracing functions"""
    def decorator(func):
        import functools

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with TraceSpan(operation, **metadata):
                return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with TraceSpan(operation, **metadata):
                return func(*args, **kwargs)

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
