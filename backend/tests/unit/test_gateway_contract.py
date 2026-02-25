"""
Gateway Contract Module Unit Tests

MVP-TEST-002: contract.py 测试覆盖率 >= 80%

Tests:
- RequestContext model
- OutputConfig model
- ToolOverride model
- InvokeRequest model
- ResponseContent model
- SuggestedAction model
- RelatedResource model
- ToolCall model
- TokenUsage model
- ResponseMetadata model
- ErrorDetail model
- InvokeResponse model
- ExecutorContext model
- ExecutorRequest model
- ExecutorResult model
- ExecutorResult.to_invoke_response()
"""

import pytest
from pydantic import ValidationError as PydanticValidationError
from app.gateway.contract import (
    RequestContext,
    OutputConfig,
    ToolOverride,
    InvokeRequest,
    ResponseContent,
    SuggestedAction,
    RelatedResource,
    ToolCall,
    TokenUsage,
    ResponseMetadata,
    ErrorDetail,
    InvokeResponse,
    ExecutorContext,
    ExecutorRequest,
    ExecutorResult,
)


class TestRequestContext:
    """Test RequestContext model"""

    def test_empty_request_context(self):
        """Create empty RequestContext"""
        ctx = RequestContext()
        assert ctx.user_id is None
        assert ctx.tenant_id is None
        assert ctx.project_id is None
        assert ctx.version_id is None
        assert ctx.extra is None

    def test_request_context_with_all_fields(self):
        """Create RequestContext with all fields"""
        ctx = RequestContext(
            user_id="user-123",
            tenant_id="tenant-456",
            project_id="project-789",
            version_id="version-001",
            codename="v1.0.0",
            region="us-east-1",
            resource_type="deployment",
            resource_name="my-app",
            namespace="default",
            extra={"custom": "value"}
        )
        assert ctx.user_id == "user-123"
        assert ctx.tenant_id == "tenant-456"
        assert ctx.project_id == "project-789"
        assert ctx.version_id == "version-001"
        assert ctx.codename == "v1.0.0"
        assert ctx.region == "us-east-1"
        assert ctx.resource_type == "deployment"
        assert ctx.resource_name == "my-app"
        assert ctx.namespace == "default"
        assert ctx.extra == {"custom": "value"}

    def test_request_context_partial(self):
        """Create RequestContext with partial fields"""
        ctx = RequestContext(user_id="user-123", project_id="project-789")
        assert ctx.user_id == "user-123"
        assert ctx.project_id == "project-789"
        assert ctx.tenant_id is None


class TestOutputConfig:
    """Test OutputConfig model"""

    def test_default_output_config(self):
        """Create OutputConfig with defaults"""
        config = OutputConfig()
        assert config.format == "markdown"
        assert config.max_tokens is None
        assert config.structured_output_schema is None

    def test_output_config_json_format(self):
        """Create OutputConfig with JSON format"""
        config = OutputConfig(format="json")
        assert config.format == "json"

    def test_output_config_plain_format(self):
        """Create OutputConfig with plain format"""
        config = OutputConfig(format="plain")
        assert config.format == "plain"

    def test_output_config_with_max_tokens(self):
        """Create OutputConfig with max_tokens"""
        config = OutputConfig(max_tokens=1000)
        assert config.max_tokens == 1000

    def test_output_config_max_tokens_min_value(self):
        """OutputConfig max_tokens must be >= 1"""
        config = OutputConfig(max_tokens=1)
        assert config.max_tokens == 1

    def test_output_config_max_tokens_max_value(self):
        """OutputConfig max_tokens must be <= 32000"""
        config = OutputConfig(max_tokens=32000)
        assert config.max_tokens == 32000

    def test_output_config_max_tokens_below_min_invalid(self):
        """OutputConfig max_tokens < 1 should fail"""
        with pytest.raises(PydanticValidationError):
            OutputConfig(max_tokens=0)

    def test_output_config_max_tokens_above_max_invalid(self):
        """OutputConfig max_tokens > 32000 should fail"""
        with pytest.raises(PydanticValidationError):
            OutputConfig(max_tokens=32001)

    def test_output_config_with_structured_schema(self):
        """Create OutputConfig with structured_output_schema"""
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        config = OutputConfig(structured_output_schema=schema)
        assert config.structured_output_schema == schema


class TestToolOverride:
    """Test ToolOverride model"""

    def test_tool_override_required_name(self):
        """ToolOverride requires name"""
        tool = ToolOverride(name="kubernetes")
        assert tool.name == "kubernetes"
        assert tool.enabled is True
        assert tool.params is None

    def test_tool_override_disabled(self):
        """ToolOverride can be disabled"""
        tool = ToolOverride(name="kubernetes", enabled=False)
        assert tool.enabled is False

    def test_tool_override_with_params(self):
        """ToolOverride with params"""
        tool = ToolOverride(
            name="kubernetes",
            params={"namespace": "production"}
        )
        assert tool.params == {"namespace": "production"}


class TestInvokeRequest:
    """Test InvokeRequest model"""

    def test_invoke_request_required_fields(self):
        """InvokeRequest with required fields only"""
        req = InvokeRequest(
            request_id="req-123",
            agent_id="nexusops.chat",
            query="Hello"
        )
        assert req.request_id == "req-123"
        assert req.agent_id == "nexusops.chat"
        assert req.query == "Hello"
        assert req.conversation_id is None
        assert isinstance(req.context, RequestContext)
        assert req.output_config is None
        assert req.tools is None

    def test_invoke_request_with_all_fields(self):
        """InvokeRequest with all fields"""
        req = InvokeRequest(
            request_id="req-123",
            conversation_id="conv-456",
            agent_id="nexusops.chat",
            query="What is the status?",
            context=RequestContext(user_id="user-123"),
            output_config=OutputConfig(format="json"),
            tools=[ToolOverride(name="kubernetes")]
        )
        assert req.request_id == "req-123"
        assert req.conversation_id == "conv-456"
        assert req.agent_id == "nexusops.chat"
        assert req.query == "What is the status?"
        assert req.context.user_id == "user-123"
        assert req.output_config.format == "json"
        assert len(req.tools) == 1

    def test_invoke_request_agent_id_pattern_valid(self):
        """Valid agent_id patterns"""
        valid_ids = [
            "nexusops.chat",
            "com.example.agent",
            "a.bc",
            "test-agent",
            "test_agent",
            "agent123",
        ]
        for agent_id in valid_ids:
            req = InvokeRequest(
                request_id="req-123",
                agent_id=agent_id,
                query="test"
            )
            assert req.agent_id == agent_id

    def test_invoke_request_agent_id_pattern_invalid(self):
        """Invalid agent_id patterns"""
        invalid_ids = [
            "1agent",  # starts with number
            "A",       # uppercase
            "a",       # too short (needs 3+ chars)
            "ab",      # too short
            "agent with space",  # has space
        ]
        for agent_id in invalid_ids:
            with pytest.raises(PydanticValidationError):
                InvokeRequest(
                    request_id="req-123",
                    agent_id=agent_id,
                    query="test"
                )

    def test_invoke_request_query_min_length(self):
        """InvokeRequest query min length is 1"""
        with pytest.raises(PydanticValidationError):
            InvokeRequest(
                request_id="req-123",
                agent_id="test.agent",
                query=""
            )

    def test_invoke_request_query_max_length(self):
        """InvokeRequest query max length is 10000"""
        req = InvokeRequest(
            request_id="req-123",
            agent_id="test.agent",
            query="x" * 10000
        )
        assert len(req.query) == 10000

    def test_invoke_request_query_exceeds_max_length(self):
        """InvokeRequest query > 10000 should fail"""
        with pytest.raises(PydanticValidationError):
            InvokeRequest(
                request_id="req-123",
                agent_id="test.agent",
                query="x" * 10001
            )


class TestResponseContent:
    """Test ResponseContent model"""

    def test_response_content_required_text(self):
        """ResponseContent requires text"""
        content = ResponseContent(text="Hello")
        assert content.text == "Hello"
        assert content.format == "markdown"
        assert content.data is None

    def test_response_content_with_format(self):
        """ResponseContent with format"""
        content = ResponseContent(text="Hello", format="json")
        assert content.format == "json"

    def test_response_content_with_data(self):
        """ResponseContent with data"""
        content = ResponseContent(
            text="Result",
            format="json",
            data={"result": "success"}
        )
        assert content.data == {"result": "success"}


class TestSuggestedAction:
    """Test SuggestedAction model"""

    def test_suggested_action_required_fields(self):
        """SuggestedAction with required fields"""
        action = SuggestedAction(id="action-1", type="invoke", label="Deploy")
        assert action.id == "action-1"
        assert action.type == "invoke"
        assert action.label == "Deploy"
        assert action.params is None
        assert action.confirm_required is False
        assert action.danger is False

    def test_suggested_action_all_types(self):
        """SuggestedAction all valid types"""
        types = ["invoke", "navigate", "copy", "external"]
        for t in types:
            action = SuggestedAction(id="action-1", type=t, label="Test")
            assert action.type == t

    def test_suggested_action_with_params(self):
        """SuggestedAction with params"""
        action = SuggestedAction(
            id="action-1",
            type="invoke",
            label="Deploy",
            params={"agent": "nexusops.deploy"}
        )
        assert action.params == {"agent": "nexusops.deploy"}

    def test_suggested_action_danger_flag(self):
        """SuggestedAction with danger flag"""
        action = SuggestedAction(
            id="action-1",
            type="invoke",
            label="Delete",
            danger=True
        )
        assert action.danger is True

    def test_suggested_action_confirm_required(self):
        """SuggestedAction with confirm_required"""
        action = SuggestedAction(
            id="action-1",
            type="invoke",
            label="Deploy",
            confirm_required=True
        )
        assert action.confirm_required is True


class TestRelatedResource:
    """Test RelatedResource model"""

    def test_related_resource_required_fields(self):
        """RelatedResource with required fields"""
        resource = RelatedResource(
            type="deployment",
            id="deploy-123",
            name="my-app"
        )
        assert resource.type == "deployment"
        assert resource.id == "deploy-123"
        assert resource.name == "my-app"
        assert resource.link is None

    def test_related_resource_with_link(self):
        """RelatedResource with link"""
        resource = RelatedResource(
            type="deployment",
            id="deploy-123",
            name="my-app",
            link="/deployments/deploy-123"
        )
        assert resource.link == "/deployments/deploy-123"


class TestToolCall:
    """Test ToolCall model"""

    def test_tool_call_required_fields(self):
        """ToolCall with required fields"""
        call = ToolCall(tool_id="tool-123")
        assert call.tool_id == "tool-123"
        assert call.tool_name is None
        assert call.input is None
        assert call.output is None
        assert call.status == "success"
        assert call.duration_ms is None
        assert call.error is None

    def test_tool_call_all_statuses(self):
        """ToolCall all valid statuses"""
        statuses = ["success", "error", "skipped"]
        for status in statuses:
            call = ToolCall(tool_id="tool-123", status=status)
            assert call.status == status

    def test_tool_call_with_all_fields(self):
        """ToolCall with all fields"""
        call = ToolCall(
            tool_id="tool-123",
            tool_name="kubernetes",
            input={"action": "get"},
            output={"result": "ok"},
            status="success",
            duration_ms=150
        )
        assert call.tool_name == "kubernetes"
        assert call.input == {"action": "get"}
        assert call.output == {"result": "ok"}
        assert call.duration_ms == 150

    def test_tool_call_with_error(self):
        """ToolCall with error"""
        error_detail = ErrorDetail(code="EXEC_TOOL_FAILED", message="Tool failed")
        call = ToolCall(
            tool_id="tool-123",
            status="error",
            error=error_detail
        )
        assert call.status == "error"
        assert call.error.code == "EXEC_TOOL_FAILED"


class TestTokenUsage:
    """Test TokenUsage model"""

    def test_token_usage_empty(self):
        """TokenUsage with no values"""
        usage = TokenUsage()
        assert usage.input is None
        assert usage.output is None

    def test_token_usage_with_values(self):
        """TokenUsage with values"""
        usage = TokenUsage(input=100, output=50)
        assert usage.input == 100
        assert usage.output == 50


class TestResponseMetadata:
    """Test ResponseMetadata model"""

    def test_response_metadata_empty(self):
        """ResponseMetadata with no values"""
        meta = ResponseMetadata()
        assert meta.trace_id is None
        assert meta.agent_version is None
        assert meta.latency_ms is None
        assert meta.tokens_used is None
        assert meta.retry_count is None
        assert meta.cache_hit is None
        assert meta.agent_type is None
        assert meta.execution_mode is None

    def test_response_metadata_with_all_fields(self):
        """ResponseMetadata with all fields"""
        meta = ResponseMetadata(
            trace_id="abc123def456",
            agent_version="1.0.0",
            latency_ms=250,
            tokens_used=TokenUsage(input=100, output=50),
            retry_count=2,
            cache_hit=True,
            agent_type="builtin",
            execution_mode="sync"
        )
        assert meta.trace_id == "abc123def456"
        assert meta.agent_version == "1.0.0"
        assert meta.latency_ms == 250
        assert meta.tokens_used.input == 100
        assert meta.retry_count == 2
        assert meta.cache_hit is True
        assert meta.agent_type == "builtin"
        assert meta.execution_mode == "sync"


class TestErrorDetailContract:
    """Test ErrorDetail model in contract"""

    def test_error_detail_required_fields(self):
        """ErrorDetail with required fields"""
        detail = ErrorDetail(code="INPUT_INVALID_JSON", message="Invalid JSON")
        assert detail.code == "INPUT_INVALID_JSON"
        assert detail.message == "Invalid JSON"
        assert detail.details is None
        assert detail.retry_after is None
        assert detail.doc_url is None

    def test_error_detail_code_pattern(self):
        """ErrorDetail code must match pattern"""
        valid_codes = [
            "INPUT_INVALID_JSON",
            "AGENT_NOT_FOUND",
            "EXEC_TIMEOUT",
            "A_B",  # minimum 3 chars
        ]
        for code in valid_codes:
            detail = ErrorDetail(code=code, message="Test")
            assert detail.code == code

    def test_error_detail_with_all_fields(self):
        """ErrorDetail with all fields"""
        detail = ErrorDetail(
            code="EXEC_TIMEOUT",
            message="Request timed out",
            details={"timeout_ms": 30000},
            retry_after=5,
            doc_url="https://docs.example.com/errors"
        )
        assert detail.details == {"timeout_ms": 30000}
        assert detail.retry_after == 5
        assert detail.doc_url == "https://docs.example.com/errors"


class TestInvokeResponse:
    """Test InvokeResponse model"""

    def test_invoke_response_required_fields(self):
        """InvokeResponse with required fields"""
        resp = InvokeResponse(
            request_id="req-123",
            content=ResponseContent(text="Hello")
        )
        assert resp.request_id == "req-123"
        assert resp.trace_id is None
        assert resp.status == "success"
        assert resp.content.text == "Hello"
        assert resp.structured_output is None
        assert resp.suggested_actions == []
        assert resp.related_resources == []
        assert resp.tool_calls is None
        assert resp.metadata is None
        assert resp.error is None

    def test_invoke_response_all_statuses(self):
        """InvokeResponse all valid statuses"""
        statuses = ["success", "error", "partial", "pending"]
        for status in statuses:
            resp = InvokeResponse(
                request_id="req-123",
                status=status,
                content=ResponseContent(text="Test")
            )
            assert resp.status == status

    def test_invoke_response_with_all_fields(self):
        """InvokeResponse with all fields"""
        resp = InvokeResponse(
            request_id="req-123",
            trace_id="trace-456",
            status="success",
            content=ResponseContent(text="Done", format="markdown"),
            structured_output={"result": "data"},
            suggested_actions=[
                SuggestedAction(id="a1", type="invoke", label="Action")
            ],
            related_resources=[
                RelatedResource(type="deployment", id="d1", name="app")
            ],
            tool_calls=[
                ToolCall(tool_id="t1", tool_name="k8s")
            ],
            metadata=ResponseMetadata(trace_id="trace-456", latency_ms=100),
            error=None
        )
        assert resp.request_id == "req-123"
        assert resp.trace_id == "trace-456"
        assert len(resp.suggested_actions) == 1
        assert len(resp.related_resources) == 1
        assert len(resp.tool_calls) == 1

    def test_invoke_response_error(self):
        """InvokeResponse with error"""
        resp = InvokeResponse(
            request_id="req-123",
            status="error",
            content=ResponseContent(text="Error occurred"),
            error=ErrorDetail(code="AGENT_NOT_FOUND", message="Agent not found")
        )
        assert resp.status == "error"
        assert resp.error.code == "AGENT_NOT_FOUND"


class TestExecutorContext:
    """Test ExecutorContext model"""

    def test_executor_context_required_fields(self):
        """ExecutorContext with required fields"""
        ctx = ExecutorContext(
            trace_id="trace-123",
            request_id="req-123",
            agent_id="test.agent"
        )
        assert ctx.trace_id == "trace-123"
        assert ctx.request_id == "req-123"
        assert ctx.agent_id == "test.agent"
        assert ctx.agent_version == "1.0.0"
        assert ctx.agent_type == "builtin"
        assert ctx.endpoint is None
        assert ctx.timeout_ms == 30000
        assert ctx.retry_config is None
        assert ctx.auth_context is None

    def test_executor_context_all_agent_types(self):
        """ExecutorContext all valid agent types"""
        types = ["builtin", "remote", "mock"]
        for t in types:
            ctx = ExecutorContext(
                trace_id="trace-123",
                request_id="req-123",
                agent_id="test.agent",
                agent_type=t
            )
            assert ctx.agent_type == t

    def test_executor_context_with_all_fields(self):
        """ExecutorContext with all fields"""
        ctx = ExecutorContext(
            trace_id="trace-123",
            request_id="req-123",
            agent_id="test.agent",
            agent_version="2.0.0",
            agent_type="remote",
            endpoint="https://api.example.com",
            timeout_ms=60000,
            retry_config={"max_retries": 3},
            auth_context={"token": "xxx"}
        )
        assert ctx.agent_version == "2.0.0"
        assert ctx.agent_type == "remote"
        assert ctx.endpoint == "https://api.example.com"
        assert ctx.timeout_ms == 60000
        assert ctx.retry_config == {"max_retries": 3}
        assert ctx.auth_context == {"token": "xxx"}


class TestExecutorRequest:
    """Test ExecutorRequest model"""

    def test_executor_request_required_fields(self):
        """ExecutorRequest with required fields"""
        ctx = ExecutorContext(
            trace_id="trace-123",
            request_id="req-123",
            agent_id="test.agent"
        )
        req = ExecutorRequest(context=ctx, query="Hello")
        assert req.context == ctx
        assert req.query == "Hello"
        assert req.request_context == {}
        assert req.output_config is None
        assert req.tools is None

    def test_executor_request_with_all_fields(self):
        """ExecutorRequest with all fields"""
        ctx = ExecutorContext(
            trace_id="trace-123",
            request_id="req-123",
            agent_id="test.agent"
        )
        req = ExecutorRequest(
            context=ctx,
            query="Hello",
            request_context={"user_id": "user-123"},
            output_config={"format": "json"},
            tools=[{"name": "k8s", "enabled": True}]
        )
        assert req.request_context == {"user_id": "user-123"}
        assert req.output_config == {"format": "json"}
        assert len(req.tools) == 1


class TestExecutorResult:
    """Test ExecutorResult model"""

    def test_executor_result_success(self):
        """ExecutorResult success"""
        result = ExecutorResult(
            success=True,
            content={"text": "Hello", "format": "markdown"}
        )
        assert result.success is True
        assert result.content == {"text": "Hello", "format": "markdown"}
        assert result.structured_output is None
        assert result.suggested_actions == []
        assert result.related_resources == []
        assert result.tool_calls is None
        assert result.metadata == {}
        assert result.error is None

    def test_executor_result_error(self):
        """ExecutorResult error"""
        result = ExecutorResult(
            success=False,
            content={"text": "Error", "format": "plain"},
            error={"code": "EXEC_TIMEOUT", "message": "Timeout"}
        )
        assert result.success is False
        assert result.error["code"] == "EXEC_TIMEOUT"

    def test_executor_result_to_invoke_response_success(self):
        """ExecutorResult.to_invoke_response() for success"""
        result = ExecutorResult(
            success=True,
            content={"text": "Done", "format": "markdown"},
            structured_output={"key": "value"},
            suggested_actions=[{"id": "a1", "type": "invoke", "label": "Act"}],
            related_resources=[{"type": "deployment", "id": "d1", "name": "app"}],
            tool_calls=[{"tool_id": "t1"}],
            metadata={"latency_ms": 100, "agent_version": "1.0.0"}
        )
        resp = result.to_invoke_response("req-123", "trace-456")

        assert isinstance(resp, InvokeResponse)
        assert resp.request_id == "req-123"
        assert resp.trace_id == "trace-456"
        assert resp.status == "success"
        assert resp.content.text == "Done"
        assert resp.structured_output == {"key": "value"}
        assert len(resp.suggested_actions) == 1
        assert len(resp.related_resources) == 1
        assert len(resp.tool_calls) == 1
        assert resp.metadata.trace_id == "trace-456"
        assert resp.metadata.latency_ms == 100

    def test_executor_result_to_invoke_response_error(self):
        """ExecutorResult.to_invoke_response() for error"""
        result = ExecutorResult(
            success=False,
            content={"text": "Error", "format": "plain"},
            error={"code": "AGENT_NOT_FOUND", "message": "Not found"}
        )
        resp = result.to_invoke_response("req-123", "trace-456")

        assert resp.status == "error"
        assert resp.error.code == "AGENT_NOT_FOUND"
        assert resp.error.message == "Not found"

    def test_executor_result_to_invoke_response_partial(self):
        """ExecutorResult with partial data"""
        result = ExecutorResult(
            success=True,
            content={"text": "Partial", "format": "markdown"}
        )
        resp = result.to_invoke_response("req-123", "trace-456")

        assert resp.request_id == "req-123"
        assert resp.trace_id == "trace-456"
        assert resp.suggested_actions == []
        assert resp.related_resources == []
        # When tool_calls is None, to_invoke_response returns empty list
        assert resp.tool_calls == []


class TestModelSerialization:
    """Test model serialization/deserialization"""

    def test_invoke_request_model_dump(self):
        """InvokeRequest.model_dump()"""
        req = InvokeRequest(
            request_id="req-123",
            agent_id="test.agent",
            query="Hello"
        )
        data = req.model_dump()
        assert data["request_id"] == "req-123"
        assert data["agent_id"] == "test.agent"
        assert data["query"] == "Hello"

    def test_invoke_response_model_dump(self):
        """InvokeResponse.model_dump()"""
        resp = InvokeResponse(
            request_id="req-123",
            content=ResponseContent(text="Hello")
        )
        data = resp.model_dump()
        assert data["request_id"] == "req-123"
        assert data["status"] == "success"
        assert data["content"]["text"] == "Hello"

    def test_invoke_request_model_validate(self):
        """InvokeRequest.model_validate()"""
        data = {
            "request_id": "req-123",
            "agent_id": "test.agent",
            "query": "Hello"
        }
        req = InvokeRequest.model_validate(data)
        assert req.request_id == "req-123"
        assert req.agent_id == "test.agent"
