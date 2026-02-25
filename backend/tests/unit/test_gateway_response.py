"""
Gateway Response Module Unit Tests

MVP-TEST-002: response.py 测试覆盖率 >= 80%

Tests:
- build_response function
- build_error_response function
- build_partial_response function
- build_pending_response function
- success_response helper
- error_response helper
"""

import pytest
from app.gateway.response import (
    build_response,
    build_error_response,
    build_partial_response,
    build_pending_response,
    success_response,
    error_response,
)
from app.gateway.contract import (
    InvokeResponse,
    ResponseContent,
    SuggestedAction,
    RelatedResource,
    ToolCall,
)
from app.gateway.errors import (
    GatewayError,
    ErrorCode,
    AgentError,
    ExecError,
    InputError,
)


class TestBuildResponse:
    """Test build_response function"""

    def test_build_response_minimal(self):
        """Build response with minimal required fields"""
        resp = build_response(
            request_id="req-123",
            trace_id="trace-456"
        )

        assert isinstance(resp, InvokeResponse)
        assert resp.request_id == "req-123"
        assert resp.trace_id == "trace-456"
        assert resp.status == "success"
        assert resp.content.text == ""
        assert resp.content.format == "markdown"

    def test_build_response_with_text(self):
        """Build response with text"""
        resp = build_response(
            request_id="req-123",
            trace_id="trace-456",
            text="Hello, world!"
        )

        assert resp.content.text == "Hello, world!"

    def test_build_response_with_format(self):
        """Build response with format"""
        resp = build_response(
            request_id="req-123",
            trace_id="trace-456",
            text='{"result": "ok"}',
            format="json"
        )

        assert resp.content.format == "json"
        assert resp.content.text == '{"result": "ok"}'

    def test_build_response_with_all_formats(self):
        """Build response with all valid formats"""
        formats = ["markdown", "json", "plain"]
        for fmt in formats:
            resp = build_response(
                request_id="req-123",
                trace_id="trace-456",
                text="Test",
                format=fmt
            )
            assert resp.content.format == fmt

    def test_build_response_with_data(self):
        """Build response with data"""
        data = {"key": "value", "count": 42}
        resp = build_response(
            request_id="req-123",
            trace_id="trace-456",
            text="Result",
            data=data
        )

        assert resp.content.data == data

    def test_build_response_with_structured_output(self):
        """Build response with structured output"""
        structured = {"type": "result", "items": [1, 2, 3]}
        resp = build_response(
            request_id="req-123",
            trace_id="trace-456",
            structured_output=structured
        )

        assert resp.structured_output == structured

    def test_build_response_with_suggested_actions(self):
        """Build response with suggested actions"""
        actions = [
            {"id": "a1", "type": "invoke", "label": "Deploy"},
            {"id": "a2", "type": "navigate", "label": "View"}
        ]
        resp = build_response(
            request_id="req-123",
            trace_id="trace-456",
            suggested_actions=actions
        )

        assert len(resp.suggested_actions) == 2
        assert isinstance(resp.suggested_actions[0], SuggestedAction)
        assert resp.suggested_actions[0].id == "a1"

    def test_build_response_with_related_resources(self):
        """Build response with related resources"""
        resources = [
            {"type": "deployment", "id": "d1", "name": "app"}
        ]
        resp = build_response(
            request_id="req-123",
            trace_id="trace-456",
            related_resources=resources
        )

        assert len(resp.related_resources) == 1
        assert isinstance(resp.related_resources[0], RelatedResource)
        assert resp.related_resources[0].type == "deployment"

    def test_build_response_with_tool_calls(self):
        """Build response with tool calls"""
        tools = [
            {"tool_id": "t1", "tool_name": "k8s", "status": "success"}
        ]
        resp = build_response(
            request_id="req-123",
            trace_id="trace-456",
            tool_calls=tools
        )

        assert len(resp.tool_calls) == 1
        assert isinstance(resp.tool_calls[0], ToolCall)
        assert resp.tool_calls[0].tool_id == "t1"

    def test_build_response_with_latency(self):
        """Build response with latency_ms"""
        resp = build_response(
            request_id="req-123",
            trace_id="trace-456",
            latency_ms=250
        )

        assert resp.metadata.latency_ms == 250

    def test_build_response_with_agent_info(self):
        """Build response with agent type and version"""
        resp = build_response(
            request_id="req-123",
            trace_id="trace-456",
            agent_type="builtin",
            agent_version="1.0.0"
        )

        assert resp.metadata.agent_type == "builtin"
        assert resp.metadata.agent_version == "1.0.0"

    def test_build_response_with_metadata(self):
        """Build response with additional metadata"""
        resp = build_response(
            request_id="req-123",
            trace_id="trace-456",
            metadata={"retry_count": 2, "cache_hit": True}
        )

        assert resp.metadata.retry_count == 2
        assert resp.metadata.cache_hit is True

    def test_build_response_with_status(self):
        """Build response with custom status"""
        for status in ["success", "error", "partial", "pending"]:
            resp = build_response(
                request_id="req-123",
                trace_id="trace-456",
                status=status
            )
            assert resp.status == status


class TestBuildErrorResponse:
    """Test build_error_response function"""

    def test_build_error_response_basic(self):
        """Build basic error response"""
        error = GatewayError(
            code=ErrorCode.AGENT_NOT_FOUND,
            message="Agent not found"
        )
        resp = build_error_response(
            request_id="req-123",
            trace_id="trace-456",
            error=error
        )

        assert resp.request_id == "req-123"
        assert resp.trace_id == "trace-456"
        assert resp.status == "error"
        assert resp.content.text == "Agent not found"
        assert resp.content.format == "plain"
        assert resp.error.code == "AGENT_NOT_FOUND"
        assert resp.error.message == "Agent not found"

    def test_build_error_response_with_details(self):
        """Build error response with details"""
        error = AgentError(
            code=ErrorCode.AGENT_NOT_INSTALLED,
            message="Agent not installed",
            details={"agent_id": "test.agent"}
        )
        resp = build_error_response(
            request_id="req-123",
            trace_id="trace-456",
            error=error
        )

        assert resp.error.details == {"agent_id": "test.agent"}

    def test_build_error_response_with_retry_after(self):
        """Build error response with retry_after"""
        error = ExecError(
            code=ErrorCode.EXEC_TIMEOUT,
            message="Timeout",
            retry_after=10
        )
        resp = build_error_response(
            request_id="req-123",
            trace_id="trace-456",
            error=error
        )

        assert resp.error.retry_after == 10

    def test_build_error_response_with_latency(self):
        """Build error response with latency"""
        error = GatewayError(
            code=ErrorCode.SYSTEM_INTERNAL_ERROR,
            message="Internal error"
        )
        resp = build_error_response(
            request_id="req-123",
            trace_id="trace-456",
            error=error,
            latency_ms=150
        )

        assert resp.metadata.latency_ms == 150

    def test_build_error_response_all_error_types(self):
        """Build error response with all error types"""
        errors = [
            (InputError(code=ErrorCode.INPUT_MISSING_FIELD, message="Missing"), "INPUT_MISSING_FIELD"),
            (AgentError(code=ErrorCode.AGENT_NOT_FOUND, message="Not found"), "AGENT_NOT_FOUND"),
            (ExecError(code=ErrorCode.EXEC_TIMEOUT, message="Timeout"), "EXEC_TIMEOUT"),
        ]

        for error, expected_code in errors:
            resp = build_error_response(
                request_id="req-123",
                trace_id="trace-456",
                error=error
            )
            assert resp.status == "error"
            assert resp.error.code == expected_code


class TestBuildPartialResponse:
    """Test build_partial_response function"""

    def test_build_partial_response_minimal(self):
        """Build minimal partial response"""
        resp = build_partial_response(
            request_id="req-123",
            trace_id="trace-456"
        )

        assert resp.request_id == "req-123"
        assert resp.trace_id == "trace-456"
        assert resp.status == "partial"
        assert resp.content.text == ""

    def test_build_partial_response_with_text(self):
        """Build partial response with text"""
        resp = build_partial_response(
            request_id="req-123",
            trace_id="trace-456",
            text="Partial results available"
        )

        assert resp.content.text == "Partial results available"

    def test_build_partial_response_with_results(self):
        """Build partial response with results"""
        partial_results = [
            {"item": "a", "status": "ok"},
            {"item": "b", "status": "ok"}
        ]
        failed_parts = [
            {"item": "c", "error": "timeout"}
        ]
        resp = build_partial_response(
            request_id="req-123",
            trace_id="trace-456",
            text="2 of 3 completed",
            partial_results=partial_results,
            failed_parts=failed_parts
        )

        assert resp.structured_output["type"] == "partial_result"
        assert resp.structured_output["successful"] == partial_results
        assert resp.structured_output["failed"] == failed_parts

    def test_build_partial_response_with_latency(self):
        """Build partial response with latency"""
        resp = build_partial_response(
            request_id="req-123",
            trace_id="trace-456",
            latency_ms=500
        )

        assert resp.metadata.latency_ms == 500

    def test_build_partial_response_format(self):
        """Partial response format is markdown"""
        resp = build_partial_response(
            request_id="req-123",
            trace_id="trace-456",
            text="Test"
        )

        assert resp.content.format == "markdown"


class TestBuildPendingResponse:
    """Test build_pending_response function"""

    def test_build_pending_response_minimal(self):
        """Build minimal pending response"""
        resp = build_pending_response(
            request_id="req-123",
            trace_id="trace-456"
        )

        assert resp.request_id == "req-123"
        assert resp.trace_id == "trace-456"
        assert resp.status == "pending"
        assert resp.content.text == "Request is being processed"

    def test_build_pending_response_with_custom_text(self):
        """Build pending response with custom text"""
        resp = build_pending_response(
            request_id="req-123",
            trace_id="trace-456",
            text="Your request is in the queue"
        )

        assert resp.content.text == "Your request is in the queue"

    def test_build_pending_response_with_poll_url(self):
        """Build pending response with poll URL"""
        resp = build_pending_response(
            request_id="req-123",
            trace_id="trace-456",
            poll_url="/api/v1/requests/req-123/status"
        )

        assert resp.structured_output["poll_url"] == "/api/v1/requests/req-123/status"
        assert len(resp.suggested_actions) == 1
        assert resp.suggested_actions[0].type == "navigate"
        assert resp.suggested_actions[0].label == "Check Status"

    def test_build_pending_response_without_poll_url(self):
        """Build pending response without poll URL"""
        resp = build_pending_response(
            request_id="req-123",
            trace_id="trace-456"
        )

        assert resp.structured_output["poll_url"] is None
        assert resp.suggested_actions == []

    def test_build_pending_response_with_estimated_time(self):
        """Build pending response with estimated time"""
        resp = build_pending_response(
            request_id="req-123",
            trace_id="trace-456",
            estimated_time_seconds=60
        )

        assert resp.structured_output["estimated_time_seconds"] == 60

    def test_build_pending_response_with_latency(self):
        """Build pending response with latency"""
        resp = build_pending_response(
            request_id="req-123",
            trace_id="trace-456",
            latency_ms=50
        )

        assert resp.metadata.latency_ms == 50


class TestSuccessResponse:
    """Test success_response helper"""

    def test_success_response_basic(self):
        """Build basic success response"""
        resp = success_response(
            request_id="req-123",
            trace_id="trace-456",
            text="Operation completed"
        )

        assert resp.status == "success"
        assert resp.content.text == "Operation completed"

    def test_success_response_with_kwargs(self):
        """Build success response with extra kwargs"""
        resp = success_response(
            request_id="req-123",
            trace_id="trace-456",
            text="Done",
            latency_ms=100,
            agent_type="builtin",
            suggested_actions=[{"id": "a1", "type": "navigate", "label": "View"}]
        )

        assert resp.metadata.latency_ms == 100
        assert resp.metadata.agent_type == "builtin"
        assert len(resp.suggested_actions) == 1


class TestErrorResponse:
    """Test error_response helper"""

    def test_error_response_basic(self):
        """Build basic error response"""
        resp = error_response(
            request_id="req-123",
            trace_id="trace-456",
            code=ErrorCode.AGENT_NOT_FOUND,
            message="Agent not found"
        )

        assert resp.status == "error"
        assert resp.error.code == "AGENT_NOT_FOUND"
        assert resp.error.message == "Agent not found"

    def test_error_response_with_details(self):
        """Build error response with details"""
        resp = error_response(
            request_id="req-123",
            trace_id="trace-456",
            code=ErrorCode.AGENT_NOT_FOUND,
            message="Agent not found",
            details={"agent_id": "test.agent"}
        )

        assert resp.error.details == {"agent_id": "test.agent"}

    def test_error_response_with_latency(self):
        """Build error response with latency"""
        resp = error_response(
            request_id="req-123",
            trace_id="trace-456",
            code=ErrorCode.SYSTEM_INTERNAL_ERROR,
            message="Internal error",
            latency_ms=200
        )

        assert resp.metadata.latency_ms == 200


class TestResponseConsistency:
    """Test response consistency across builders"""

    def test_all_responses_have_request_id_and_trace_id(self):
        """All responses should have request_id and trace_id"""
        request_id = "req-123"
        trace_id = "trace-456"

        # Success response
        resp1 = build_response(request_id, trace_id)
        assert resp1.request_id == request_id
        assert resp1.trace_id == trace_id

        # Error response
        error = GatewayError(code=ErrorCode.SYSTEM_INTERNAL_ERROR, message="Error")
        resp2 = build_error_response(request_id, trace_id, error)
        assert resp2.request_id == request_id
        assert resp2.trace_id == trace_id

        # Partial response
        resp3 = build_partial_response(request_id, trace_id)
        assert resp3.request_id == request_id
        assert resp3.trace_id == trace_id

        # Pending response
        resp4 = build_pending_response(request_id, trace_id)
        assert resp4.request_id == request_id
        assert resp4.trace_id == trace_id

    def test_all_responses_are_invoke_response_type(self):
        """All responses should be InvokeResponse type"""
        request_id = "req-123"
        trace_id = "trace-456"

        resp1 = build_response(request_id, trace_id)
        resp2 = build_error_response(
            request_id, trace_id,
            GatewayError(code=ErrorCode.SYSTEM_INTERNAL_ERROR, message="Error")
        )
        resp3 = build_partial_response(request_id, trace_id)
        resp4 = build_pending_response(request_id, trace_id)

        assert isinstance(resp1, InvokeResponse)
        assert isinstance(resp2, InvokeResponse)
        assert isinstance(resp3, InvokeResponse)
        assert isinstance(resp4, InvokeResponse)

    def test_status_values_are_consistent(self):
        """Status values should be consistent"""
        request_id = "req-123"
        trace_id = "trace-456"

        resp1 = build_response(request_id, trace_id, status="success")
        resp2 = build_error_response(
            request_id, trace_id,
            GatewayError(code=ErrorCode.SYSTEM_INTERNAL_ERROR, message="Error")
        )
        resp3 = build_partial_response(request_id, trace_id)
        resp4 = build_pending_response(request_id, trace_id)

        assert resp1.status == "success"
        assert resp2.status == "error"
        assert resp3.status == "partial"
        assert resp4.status == "pending"


class TestResponseMetadata:
    """Test response metadata handling"""

    def test_metadata_trace_id_included(self):
        """Metadata should include trace_id"""
        resp = build_response(
            request_id="req-123",
            trace_id="trace-456"
        )

        assert resp.metadata is not None
        assert resp.metadata.trace_id == "trace-456"

    def test_metadata_latency_optional(self):
        """Latency is optional in metadata"""
        resp1 = build_response(
            request_id="req-123",
            trace_id="trace-456"
        )
        assert resp1.metadata.latency_ms is None

        resp2 = build_response(
            request_id="req-123",
            trace_id="trace-456",
            latency_ms=100
        )
        assert resp2.metadata.latency_ms == 100

    def test_error_response_metadata(self):
        """Error response metadata"""
        error = ExecError(
            code=ErrorCode.EXEC_TIMEOUT,
            message="Timeout"
        )
        resp = build_error_response(
            request_id="req-123",
            trace_id="trace-456",
            error=error,
            latency_ms=500
        )

        assert resp.metadata.trace_id == "trace-456"
        assert resp.metadata.latency_ms == 500


class TestResponseEdgeCases:
    """Test edge cases in response building"""

    def test_empty_text(self):
        """Empty text should work"""
        resp = build_response(
            request_id="req-123",
            trace_id="trace-456",
            text=""
        )
        assert resp.content.text == ""

    def test_empty_suggested_actions(self):
        """Empty suggested actions should work"""
        resp = build_response(
            request_id="req-123",
            trace_id="trace-456",
            suggested_actions=[]
        )
        assert resp.suggested_actions == []

    def test_none_values(self):
        """None values should work for optional fields"""
        resp = build_response(
            request_id="req-123",
            trace_id="trace-456",
            text="Test",
            data=None,
            structured_output=None,
            tool_calls=None
        )
        assert resp.content.data is None
        assert resp.structured_output is None
        assert resp.tool_calls is None

    def test_special_characters_in_text(self):
        """Special characters in text should work"""
        special_text = "Hello <world> & 'friends' \"!@#$%^*()\""
        resp = build_response(
            request_id="req-123",
            trace_id="trace-456",
            text=special_text
        )
        assert resp.content.text == special_text

    def test_unicode_in_text(self):
        """Unicode in text should work"""
        unicode_text = "你好世界 🌍 Hello мир"
        resp = build_response(
            request_id="req-123",
            trace_id="trace-456",
            text=unicode_text
        )
        assert resp.content.text == unicode_text

    def test_large_data_object(self):
        """Large data object should work"""
        large_data = {"items": list(range(1000))}
        resp = build_response(
            request_id="req-123",
            trace_id="trace-456",
            data=large_data
        )
        assert resp.content.data == large_data
