"""
NexusOps SDK - Trace Utilities Tests

Tests for trace ID generation and context management.
"""

import pytest

from nexusops_sdk.utils.trace import (
    generate_trace_id,
    generate_request_id,
    TraceContext,
    TraceSpan,
    init_trace_context,
    get_trace_context,
    set_trace_context,
    clear_trace_context,
)


class TestTraceIdGeneration:
    """Tests for trace ID generation."""

    def test_generate_trace_id(self):
        """Test trace ID generation."""
        trace_id = generate_trace_id()

        assert isinstance(trace_id, str)
        assert len(trace_id) == 32
        assert trace_id.islower()
        assert all(c in "0123456789abcdef" for c in trace_id)

    def test_generate_trace_id_unique(self):
        """Test trace IDs are unique."""
        ids = {generate_trace_id() for _ in range(100)}
        assert len(ids) == 100

    def test_generate_request_id(self):
        """Test request ID generation."""
        request_id = generate_request_id()

        assert isinstance(request_id, str)
        assert len(request_id) == 36  # UUID with hyphens
        assert request_id.count("-") == 4

    def test_generate_request_id_unique(self):
        """Test request IDs are unique."""
        ids = {generate_request_id() for _ in range(100)}
        assert len(ids) == 100


class TestTraceContext:
    """Tests for TraceContext."""

    def test_create_trace_context(self):
        """Test creating trace context."""
        ctx = TraceContext(
            trace_id="1234567890abcdef1234567890abcdef",
            request_id="req-123",
        )

        assert ctx.trace_id == "1234567890abcdef1234567890abcdef"
        assert ctx.request_id == "req-123"

    def test_trace_context_auto_generate(self):
        """Test trace context auto-generates IDs."""
        ctx = TraceContext(trace_id="", request_id="")

        # Empty strings should be replaced
        assert ctx.trace_id  # Should have generated one
        assert ctx.request_id

    def test_to_headers(self):
        """Test converting context to headers."""
        ctx = TraceContext(
            trace_id="1234567890abcdef1234567890abcdef",
            request_id="req-123",
            conversation_id="conv-456",
        )

        headers = ctx.to_headers()

        assert headers["X-Trace-ID"] == "1234567890abcdef1234567890abcdef"
        assert headers["X-Request-ID"] == "req-123"
        assert headers["X-Conversation-ID"] == "conv-456"

    def test_to_log_dict(self):
        """Test converting context to log dict."""
        ctx = TraceContext(
            trace_id="1234567890abcdef1234567890abcdef",
            request_id="req-123",
            agent_id="test.agent",
            user_id="user-123",
        )

        log_dict = ctx.to_log_dict()

        assert log_dict["trace_id"] == "1234567890abcdef1234567890abcdef"
        assert log_dict["request_id"] == "req-123"
        assert log_dict["agent_id"] == "test.agent"
        assert log_dict["user_id"] == "user-123"

    def test_elapsed_ms(self):
        """Test elapsed time calculation."""
        import time
        from datetime import datetime, timedelta

        ctx = TraceContext(
            trace_id="test",
            request_id="test",
        )

        # Should be very small right after creation
        elapsed = ctx.elapsed_ms
        assert elapsed >= 0
        assert elapsed < 1000  # Should be less than 1 second

    def test_from_headers(self):
        """Test creating context from headers."""
        headers = {
            "X-Trace-ID": "1234567890abcdef1234567890abcdef",
            "X-Request-ID": "req-123",
            "X-Conversation-ID": "conv-456",
        }

        ctx = TraceContext.from_headers(headers)

        assert ctx.trace_id == "1234567890abcdef1234567890abcdef"
        assert ctx.request_id == "req-123"
        assert ctx.conversation_id == "conv-456"


class TestTraceContextManagement:
    """Tests for trace context management."""

    def test_init_trace_context(self):
        """Test initializing trace context."""
        clear_trace_context()

        ctx = init_trace_context(
            request_id="req-123",
            trace_id="1234567890abcdef1234567890abcdef",
            agent_id="test.agent",
        )

        assert ctx.request_id == "req-123"
        assert ctx.trace_id == "1234567890abcdef1234567890abcdef"
        assert ctx.agent_id == "test.agent"

        # Should be retrievable
        retrieved = get_trace_context()
        assert retrieved is not None
        assert retrieved.request_id == "req-123"

        clear_trace_context()

    def test_set_and_get_trace_context(self):
        """Test setting and getting trace context."""
        clear_trace_context()

        ctx = TraceContext(
            trace_id="test-trace",
            request_id="test-request",
        )

        set_trace_context(ctx)
        retrieved = get_trace_context()

        assert retrieved is not None
        assert retrieved.trace_id == "test-trace"

        clear_trace_context()

    def test_clear_trace_context(self):
        """Test clearing trace context."""
        ctx = TraceContext(trace_id="test", request_id="test")
        set_trace_context(ctx)

        clear_trace_context()
        assert get_trace_context() is None


class TestTraceSpan:
    """Tests for TraceSpan context manager."""

    def test_trace_span_basic(self):
        """Test basic trace span usage."""
        with TraceSpan("test_operation") as span:
            assert span.start_time is not None
            assert span.end_time is None

        assert span.end_time is not None
        assert span.duration_ms >= 0

    def test_trace_span_with_agent_id(self):
        """Test trace span with agent ID."""
        clear_trace_context()

        with TraceSpan("test_operation", agent_id="test.agent") as span:
            ctx = get_trace_context()
            assert ctx is not None
            assert ctx.agent_id == "test.agent"

        clear_trace_context()

    def test_trace_span_with_metadata(self):
        """Test trace span with metadata."""
        clear_trace_context()

        with TraceSpan("test_operation", custom_key="custom_value") as span:
            ctx = get_trace_context()
            assert ctx is not None
            assert ctx.metadata.get("custom_key") == "custom_value"

        clear_trace_context()

    def test_trace_span_duration(self):
        """Test trace span duration calculation."""
        import time

        with TraceSpan("test_operation") as span:
            time.sleep(0.01)  # 10ms

        assert span.duration_ms >= 10


class TestWithTraceDecorator:
    """Tests for with_trace decorator."""

    @pytest.mark.asyncio
    async def test_with_trace_async(self):
        """Test with_trace decorator on async function."""
        from nexusops_sdk.utils.trace import with_trace

        clear_trace_context()

        @with_trace("async_operation", custom="metadata")
        async def async_func():
            ctx = get_trace_context()
            assert ctx is not None
            return "result"

        result = await async_func()
        assert result == "result"

        clear_trace_context()

    def test_with_trace_sync(self):
        """Test with_trace decorator on sync function."""
        from nexusops_sdk.utils.trace import with_trace

        clear_trace_context()

        @with_trace("sync_operation")
        def sync_func():
            ctx = get_trace_context()
            assert ctx is not None
            return "result"

        result = sync_func()
        assert result == "result"

        clear_trace_context()
