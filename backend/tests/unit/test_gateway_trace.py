"""
Unit tests for app/gateway/trace.py

Tests for trace ID generation, context management, and span tracking.
"""

import pytest
import asyncio
from datetime import datetime

from app.gateway.trace import (
    generate_trace_id,
    generate_request_id,
    TraceContext,
    init_trace_context,
    get_trace_context,
    set_trace_context,
    clear_trace_context,
    TraceSpan,
    with_trace,
)


class TestTraceIdGeneration:
    """Tests for trace ID generation"""

    def test_generate_trace_id_format(self):
        """Test trace ID is 32-char hex string"""
        trace_id = generate_trace_id()
        assert len(trace_id) == 32
        assert all(c in '0123456789abcdef' for c in trace_id)

    def test_generate_trace_id_unique(self):
        """Test trace IDs are unique"""
        ids = {generate_trace_id() for _ in range(100)}
        assert len(ids) == 100

    def test_generate_request_id_format(self):
        """Test request ID is UUID format"""
        request_id = generate_request_id()
        # UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        assert len(request_id) == 36
        assert request_id.count('-') == 4

    def test_generate_request_id_unique(self):
        """Test request IDs are unique"""
        ids = {generate_request_id() for _ in range(100)}
        assert len(ids) == 100


class TestTraceContext:
    """Tests for TraceContext dataclass"""

    def test_create_with_all_fields(self):
        """Test creating TraceContext with all fields"""
        ctx = TraceContext(
            trace_id="12345678901234567890123456789012",
            request_id="req-123",
            agent_id="test-agent",
            conversation_id="conv-123",
            user_id="user-123",
            tenant_id="tenant-123",
        )
        
        assert ctx.trace_id == "12345678901234567890123456789012"
        assert ctx.request_id == "req-123"
        assert ctx.agent_id == "test-agent"
        assert ctx.conversation_id == "conv-123"
        assert ctx.user_id == "user-123"
        assert ctx.tenant_id == "tenant-123"

    def test_auto_generate_ids(self):
        """Test auto-generating trace_id and request_id"""
        ctx = TraceContext(trace_id="", request_id="")
        assert len(ctx.trace_id) == 32
        assert len(ctx.request_id) == 36

    def test_to_headers_basic(self):
        """Test converting to HTTP headers"""
        ctx = TraceContext(
            trace_id="12345678901234567890123456789012",
            request_id="req-123",
        )
        
        headers = ctx.to_headers()
        
        assert headers["X-Trace-ID"] == "12345678901234567890123456789012"
        assert headers["X-Request-ID"] == "req-123"
        assert "X-Conversation-ID" not in headers

    def test_to_headers_with_conversation(self):
        """Test headers include conversation ID when set"""
        ctx = TraceContext(
            trace_id="12345678901234567890123456789012",
            request_id="req-123",
            conversation_id="conv-456",
        )
        
        headers = ctx.to_headers()
        
        assert headers["X-Conversation-ID"] == "conv-456"

    def test_to_log_dict_basic(self):
        """Test converting to logging dict"""
        ctx = TraceContext(
            trace_id="12345678901234567890123456789012",
            request_id="req-123",
        )
        
        log_dict = ctx.to_log_dict()
        
        assert log_dict["trace_id"] == "12345678901234567890123456789012"
        assert log_dict["request_id"] == "req-123"
        assert "agent_id" not in log_dict

    def test_to_log_dict_with_all_fields(self):
        """Test logging dict includes optional fields when set"""
        ctx = TraceContext(
            trace_id="12345678901234567890123456789012",
            request_id="req-123",
            agent_id="agent-1",
            conversation_id="conv-1",
            user_id="user-1",
            tenant_id="tenant-1",
        )
        
        log_dict = ctx.to_log_dict()
        
        assert log_dict["agent_id"] == "agent-1"
        assert log_dict["conversation_id"] == "conv-1"
        assert log_dict["user_id"] == "user-1"
        assert log_dict["tenant_id"] == "tenant-1"

    def test_elapsed_ms(self):
        """Test elapsed time calculation"""
        ctx = TraceContext(
            trace_id="12345678901234567890123456789012",
            request_id="req-123",
        )
        
        # Should be very small since just created
        elapsed = ctx.elapsed_ms
        assert elapsed >= 0
        assert elapsed < 1000  # Less than 1 second


class TestTraceContextFunctions:
    """Tests for trace context management functions"""

    def setup_method(self):
        """Clear context before each test"""
        clear_trace_context()

    def teardown_method(self):
        """Clear context after each test"""
        clear_trace_context()

    def test_init_trace_context(self):
        """Test initializing trace context"""
        ctx = init_trace_context()
        
        assert ctx is not None
        assert len(ctx.trace_id) == 32
        assert len(ctx.request_id) == 36

    def test_init_trace_context_with_ids(self):
        """Test initializing with provided IDs"""
        ctx = init_trace_context(
            trace_id="12345678901234567890123456789012",
            request_id="req-456",
            agent_id="test-agent",
        )
        
        assert ctx.trace_id == "12345678901234567890123456789012"
        assert ctx.request_id == "req-456"
        assert ctx.agent_id == "test-agent"

    def test_get_trace_context(self):
        """Test getting current trace context"""
        ctx = init_trace_context(agent_id="my-agent")
        retrieved = get_trace_context()
        
        assert retrieved is ctx
        assert retrieved.agent_id == "my-agent"

    def test_get_trace_context_none(self):
        """Test getting context when none set"""
        clear_trace_context()
        assert get_trace_context() is None

    def test_set_trace_context(self):
        """Test setting trace context"""
        ctx = TraceContext(
            trace_id="12345678901234567890123456789012",
            request_id="req-789",
        )
        
        set_trace_context(ctx)
        retrieved = get_trace_context()
        
        assert retrieved.trace_id == "12345678901234567890123456789012"

    def test_clear_trace_context(self):
        """Test clearing trace context"""
        init_trace_context()
        clear_trace_context()
        
        assert get_trace_context() is None


class TestTraceSpan:
    """Tests for TraceSpan context manager"""

    def setup_method(self):
        """Clear context before each test"""
        clear_trace_context()

    def teardown_method(self):
        """Clear context after each test"""
        clear_trace_context()

    def test_span_creates_context(self):
        """Test span creates context if none exists"""
        with TraceSpan("test-operation") as span:
            ctx = get_trace_context()
            assert ctx is not None
            assert span.operation == "test-operation"

    def test_span_uses_existing_context(self):
        """Test span uses existing context"""
        ctx = init_trace_context(agent_id="existing-agent")
        
        with TraceSpan("test-operation") as span:
            current = get_trace_context()
            assert current is ctx

    def test_span_updates_agent_id(self):
        """Test span can update agent ID"""
        init_trace_context(agent_id="original")
        
        with TraceSpan("test-op", agent_id="new-agent"):
            ctx = get_trace_context()
            assert ctx.agent_id == "new-agent"

    def test_span_adds_metadata(self):
        """Test span adds metadata to context"""
        init_trace_context()
        
        with TraceSpan("test-op", custom_key="custom_value"):
            ctx = get_trace_context()
            assert ctx.metadata.get("custom_key") == "custom_value"

    def test_span_records_timing(self):
        """Test span records start and end times"""
        with TraceSpan("test-operation") as span:
            assert span.start_time is not None
            assert span.end_time is None
        
        assert span.end_time is not None

    def test_span_duration_ms(self):
        """Test span calculates duration"""
        with TraceSpan("test-operation") as span:
            pass
        
        duration = span.duration_ms
        assert duration >= 0

    def test_span_duration_before_end(self):
        """Test duration is 0 before span ends"""
        span = TraceSpan("test-operation")
        span.start_time = datetime.utcnow()
        # Don't set end_time
        
        assert span.duration_ms == 0


class TestWithTraceDecorator:
    """Tests for with_trace decorator"""

    def setup_method(self):
        """Clear context before each test"""
        clear_trace_context()

    def teardown_method(self):
        """Clear context after each test"""
        clear_trace_context()

    def test_decorator_sync_function(self):
        """Test decorator on sync function"""
        @with_trace("sync-operation")
        def sync_func():
            ctx = get_trace_context()
            return ctx is not None
        
        result = sync_func()
        assert result is True

    @pytest.mark.asyncio
    async def test_decorator_async_function(self):
        """Test decorator on async function"""
        @with_trace("async-operation")
        async def async_func():
            ctx = get_trace_context()
            return ctx is not None
        
        result = await async_func()
        assert result is True

    def test_decorator_preserves_return_value(self):
        """Test decorator preserves return value"""
        @with_trace("test-operation")
        def return_value():
            return "test-result"
        
        assert return_value() == "test-result"

    def test_decorator_with_metadata(self):
        """Test decorator with metadata"""
        @with_trace("test-operation", custom="value")
        def func_with_metadata():
            ctx = get_trace_context()
            return ctx.metadata.get("custom")
        
        result = func_with_metadata()
        assert result == "value"

    @pytest.mark.asyncio
    async def test_decorator_async_preserves_return(self):
        """Test decorator preserves async return value"""
        @with_trace("async-op")
        async def async_return():
            return "async-result"
        
        result = await async_return()
        assert result == "async-result"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
