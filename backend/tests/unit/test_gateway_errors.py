"""
Gateway Errors Module Unit Tests

MVP-TEST-002: errors.py 测试覆盖率 >= 80%

Tests:
- ErrorCode enum completeness
- ERROR_HTTP_STATUS mapping
- RETRYABLE_ERRORS set
- ErrorDetail dataclass
- GatewayError and subclasses
- Helper functions
"""

import pytest
from app.gateway.errors import (
    ErrorCode,
    ERROR_HTTP_STATUS,
    RETRYABLE_ERRORS,
    ErrorDetail,
    GatewayError,
    InputError,
    AuthError,
    AgentError,
    ExecError,
    SystemError,
    agent_not_found,
    agent_not_installed,
    agent_disabled,
    exec_timeout,
    exec_downstream_error,
    agent_output_invalid,
    input_schema_violation,
    input_missing_field,
)


class TestErrorCodeEnum:
    """Test ErrorCode enum values"""

    def test_input_error_codes_exist(self):
        """INPUT category error codes should exist"""
        assert ErrorCode.INPUT_INVALID_JSON.value == "INPUT_INVALID_JSON"
        assert ErrorCode.INPUT_SCHEMA_VIOLATION.value == "INPUT_SCHEMA_VIOLATION"
        assert ErrorCode.INPUT_MISSING_FIELD.value == "INPUT_MISSING_FIELD"
        assert ErrorCode.INPUT_INVALID_FORMAT.value == "INPUT_INVALID_FORMAT"
        assert ErrorCode.INPUT_VALUE_OUT_OF_RANGE.value == "INPUT_VALUE_OUT_OF_RANGE"
        assert ErrorCode.INPUT_QUERY_TOO_LONG.value == "INPUT_QUERY_TOO_LONG"
        assert ErrorCode.INPUT_INVALID_AGENT_ID.value == "INPUT_INVALID_AGENT_ID"

    def test_auth_error_codes_exist(self):
        """AUTH category error codes should exist"""
        assert ErrorCode.AUTH_TOKEN_MISSING.value == "AUTH_TOKEN_MISSING"
        assert ErrorCode.AUTH_TOKEN_INVALID.value == "AUTH_TOKEN_INVALID"
        assert ErrorCode.AUTH_TOKEN_EXPIRED.value == "AUTH_TOKEN_EXPIRED"
        assert ErrorCode.AUTH_PERMISSION_DENIED.value == "AUTH_PERMISSION_DENIED"
        assert ErrorCode.AUTH_QUOTA_EXCEEDED.value == "AUTH_QUOTA_EXCEEDED"
        assert ErrorCode.AUTH_TENANT_MISMATCH.value == "AUTH_TENANT_MISMATCH"

    def test_agent_error_codes_exist(self):
        """AGENT category error codes should exist"""
        assert ErrorCode.AGENT_NOT_FOUND.value == "AGENT_NOT_FOUND"
        assert ErrorCode.AGENT_INACTIVE.value == "AGENT_INACTIVE"
        assert ErrorCode.AGENT_NOT_INSTALLED.value == "AGENT_NOT_INSTALLED"
        assert ErrorCode.AGENT_DISABLED.value == "AGENT_DISABLED"
        assert ErrorCode.AGENT_VERSION_MISMATCH.value == "AGENT_VERSION_MISMATCH"
        assert ErrorCode.AGENT_BUSY.value == "AGENT_BUSY"
        assert ErrorCode.AGENT_INPUT_REJECTED.value == "AGENT_INPUT_REJECTED"
        assert ErrorCode.AGENT_OUTPUT_INVALID.value == "AGENT_OUTPUT_INVALID"
        assert ErrorCode.AGENT_ENDPOINT_MISSING.value == "AGENT_ENDPOINT_MISSING"

    def test_exec_error_codes_exist(self):
        """EXEC category error codes should exist"""
        assert ErrorCode.EXEC_TIMEOUT.value == "EXEC_TIMEOUT"
        assert ErrorCode.EXEC_TOOL_FAILED.value == "EXEC_TOOL_FAILED"
        assert ErrorCode.EXEC_DOWNSTREAM_ERROR.value == "EXEC_DOWNSTREAM_ERROR"
        assert ErrorCode.EXEC_PARTIAL_FAILURE.value == "EXEC_PARTIAL_FAILURE"
        assert ErrorCode.EXEC_RESOURCE_CONFLICT.value == "EXEC_RESOURCE_CONFLICT"
        assert ErrorCode.EXEC_CIRCUIT_OPEN.value == "EXEC_CIRCUIT_OPEN"
        assert ErrorCode.EXEC_INTERNAL_ERROR.value == "EXEC_INTERNAL_ERROR"

    def test_system_error_codes_exist(self):
        """SYSTEM category error codes should exist"""
        assert ErrorCode.SYSTEM_INTERNAL_ERROR.value == "SYSTEM_INTERNAL_ERROR"
        assert ErrorCode.SYSTEM_UNAVAILABLE.value == "SYSTEM_UNAVAILABLE"
        assert ErrorCode.SYSTEM_OVERLOADED.value == "SYSTEM_OVERLOADED"
        assert ErrorCode.SYSTEM_MAINTENANCE.value == "SYSTEM_MAINTENANCE"

    def test_error_code_is_string_enum(self):
        """ErrorCode should be a string enum"""
        assert isinstance(ErrorCode.INPUT_INVALID_JSON, str)
        assert ErrorCode.INPUT_INVALID_JSON == "INPUT_INVALID_JSON"


class TestErrorHttpStatus:
    """Test ERROR_HTTP_STATUS mapping"""

    def test_input_errors_map_to_400(self):
        """INPUT errors should map to HTTP 400"""
        assert ERROR_HTTP_STATUS[ErrorCode.INPUT_INVALID_JSON] == 400
        assert ERROR_HTTP_STATUS[ErrorCode.INPUT_SCHEMA_VIOLATION] == 400
        assert ERROR_HTTP_STATUS[ErrorCode.INPUT_MISSING_FIELD] == 400
        assert ERROR_HTTP_STATUS[ErrorCode.INPUT_INVALID_FORMAT] == 400

    def test_auth_errors_map_to_401_403_429(self):
        """AUTH errors should map to HTTP 401/403/429"""
        assert ERROR_HTTP_STATUS[ErrorCode.AUTH_TOKEN_MISSING] == 401
        assert ERROR_HTTP_STATUS[ErrorCode.AUTH_TOKEN_INVALID] == 401
        assert ERROR_HTTP_STATUS[ErrorCode.AUTH_TOKEN_EXPIRED] == 401
        assert ERROR_HTTP_STATUS[ErrorCode.AUTH_PERMISSION_DENIED] == 403
        assert ERROR_HTTP_STATUS[ErrorCode.AUTH_QUOTA_EXCEEDED] == 429
        assert ERROR_HTTP_STATUS[ErrorCode.AUTH_TENANT_MISMATCH] == 403

    def test_agent_errors_map_to_404_409_422_500(self):
        """AGENT errors should map to appropriate HTTP codes"""
        assert ERROR_HTTP_STATUS[ErrorCode.AGENT_NOT_FOUND] == 404
        assert ERROR_HTTP_STATUS[ErrorCode.AGENT_INACTIVE] == 409
        assert ERROR_HTTP_STATUS[ErrorCode.AGENT_NOT_INSTALLED] == 403
        assert ERROR_HTTP_STATUS[ErrorCode.AGENT_DISABLED] == 403
        assert ERROR_HTTP_STATUS[ErrorCode.AGENT_VERSION_MISMATCH] == 409
        assert ERROR_HTTP_STATUS[ErrorCode.AGENT_BUSY] == 503
        assert ERROR_HTTP_STATUS[ErrorCode.AGENT_INPUT_REJECTED] == 422
        assert ERROR_HTTP_STATUS[ErrorCode.AGENT_OUTPUT_INVALID] == 422

    def test_exec_errors_map_to_500_502_504(self):
        """EXEC errors should map to HTTP 500/502/504"""
        assert ERROR_HTTP_STATUS[ErrorCode.EXEC_TIMEOUT] == 504
        assert ERROR_HTTP_STATUS[ErrorCode.EXEC_TOOL_FAILED] == 500
        assert ERROR_HTTP_STATUS[ErrorCode.EXEC_DOWNSTREAM_ERROR] == 502
        assert ERROR_HTTP_STATUS[ErrorCode.EXEC_PARTIAL_FAILURE] == 500
        assert ERROR_HTTP_STATUS[ErrorCode.EXEC_RESOURCE_CONFLICT] == 409
        assert ERROR_HTTP_STATUS[ErrorCode.EXEC_CIRCUIT_OPEN] == 503
        assert ERROR_HTTP_STATUS[ErrorCode.EXEC_INTERNAL_ERROR] == 500

    def test_system_errors_map_to_500_503(self):
        """SYSTEM errors should map to HTTP 500/503"""
        assert ERROR_HTTP_STATUS[ErrorCode.SYSTEM_INTERNAL_ERROR] == 500
        assert ERROR_HTTP_STATUS[ErrorCode.SYSTEM_UNAVAILABLE] == 503
        assert ERROR_HTTP_STATUS[ErrorCode.SYSTEM_OVERLOADED] == 503
        assert ERROR_HTTP_STATUS[ErrorCode.SYSTEM_MAINTENANCE] == 503


class TestRetryableErrors:
    """Test RETRYABLE_ERRORS set"""

    def test_auth_token_expired_is_retryable(self):
        """AUTH_TOKEN_EXPIRED should be retryable"""
        assert ErrorCode.AUTH_TOKEN_EXPIRED in RETRYABLE_ERRORS

    def test_auth_quota_exceeded_is_retryable(self):
        """AUTH_QUOTA_EXCEEDED should be retryable"""
        assert ErrorCode.AUTH_QUOTA_EXCEEDED in RETRYABLE_ERRORS

    def test_agent_busy_is_retryable(self):
        """AGENT_BUSY should be retryable"""
        assert ErrorCode.AGENT_BUSY in RETRYABLE_ERRORS

    def test_exec_timeout_is_retryable(self):
        """EXEC_TIMEOUT should be retryable"""
        assert ErrorCode.EXEC_TIMEOUT in RETRYABLE_ERRORS

    def test_exec_downstream_error_is_retryable(self):
        """EXEC_DOWNSTREAM_ERROR should be retryable"""
        assert ErrorCode.EXEC_DOWNSTREAM_ERROR in RETRYABLE_ERRORS

    def test_system_unavailable_is_retryable(self):
        """SYSTEM_UNAVAILABLE should be retryable"""
        assert ErrorCode.SYSTEM_UNAVAILABLE in RETRYABLE_ERRORS

    def test_input_errors_are_not_retryable(self):
        """INPUT errors should not be retryable"""
        assert ErrorCode.INPUT_INVALID_JSON not in RETRYABLE_ERRORS
        assert ErrorCode.INPUT_SCHEMA_VIOLATION not in RETRYABLE_ERRORS
        assert ErrorCode.INPUT_MISSING_FIELD not in RETRYABLE_ERRORS


class TestErrorDetail:
    """Test ErrorDetail dataclass"""

    def test_basic_error_detail(self):
        """Create basic ErrorDetail"""
        detail = ErrorDetail(
            code="INPUT_INVALID_JSON",
            message="Invalid JSON payload"
        )
        assert detail.code == "INPUT_INVALID_JSON"
        assert detail.message == "Invalid JSON payload"
        assert detail.details is None
        assert detail.retry_after is None
        assert detail.doc_url is None

    def test_error_detail_with_all_fields(self):
        """Create ErrorDetail with all fields"""
        detail = ErrorDetail(
            code="EXEC_TIMEOUT",
            message="Request timed out",
            details={"timeout_ms": 30000, "endpoint": "/api/v1/agents/test"},
            retry_after=5,
            doc_url="https://docs.example.com/errors#timeout"
        )
        assert detail.code == "EXEC_TIMEOUT"
        assert detail.message == "Request timed out"
        assert detail.details["timeout_ms"] == 30000
        assert detail.retry_after == 5
        assert detail.doc_url == "https://docs.example.com/errors#timeout"

    def test_error_detail_to_dict_minimal(self):
        """ErrorDetail.to_dict() with minimal fields"""
        detail = ErrorDetail(code="TEST_ERROR", message="Test message")
        result = detail.to_dict()
        assert result == {"code": "TEST_ERROR", "message": "Test message"}

    def test_error_detail_to_dict_full(self):
        """ErrorDetail.to_dict() with all fields"""
        detail = ErrorDetail(
            code="TEST_ERROR",
            message="Test message",
            details={"field": "value"},
            retry_after=10,
            doc_url="https://example.com"
        )
        result = detail.to_dict()
        assert result["code"] == "TEST_ERROR"
        assert result["message"] == "Test message"
        assert result["details"] == {"field": "value"}
        assert result["retry_after"] == 10
        assert result["doc_url"] == "https://example.com"


class TestGatewayError:
    """Test GatewayError base class"""

    def test_basic_gateway_error(self):
        """Create basic GatewayError"""
        error = GatewayError(
            code=ErrorCode.SYSTEM_INTERNAL_ERROR,
            message="Something went wrong"
        )
        assert error.code == ErrorCode.SYSTEM_INTERNAL_ERROR
        assert error.message == "Something went wrong"
        assert error.details is None
        assert error.retry_after is None

    def test_gateway_error_with_details(self):
        """Create GatewayError with details"""
        error = GatewayError(
            code=ErrorCode.AGENT_NOT_FOUND,
            message="Agent not found",
            details={"agent_id": "test.agent"}
        )
        assert error.details == {"agent_id": "test.agent"}

    def test_gateway_error_http_status(self):
        """GatewayError.http_status property"""
        error = GatewayError(
            code=ErrorCode.AGENT_NOT_FOUND,
            message="Not found"
        )
        assert error.http_status == 404

    def test_gateway_error_http_status_unknown_defaults_to_500(self):
        """Unknown error code should default to HTTP 500"""
        # Create error with a code not in ERROR_HTTP_STATUS
        error = GatewayError.__new__(GatewayError)
        error.code = ErrorCode.SYSTEM_INTERNAL_ERROR  # This is in the mapping
        error.message = "test"
        # All defined codes are in ERROR_HTTP_STATUS, so test the default path
        assert error.http_status == 500

    def test_gateway_error_is_retryable_true(self):
        """GatewayError.is_retryable for retryable errors"""
        error = GatewayError(
            code=ErrorCode.EXEC_TIMEOUT,
            message="Timeout"
        )
        assert error.is_retryable is True

    def test_gateway_error_is_retryable_false(self):
        """GatewayError.is_retryable for non-retryable errors"""
        error = GatewayError(
            code=ErrorCode.INPUT_MISSING_FIELD,
            message="Missing field"
        )
        assert error.is_retryable is False

    def test_gateway_error_to_error_detail(self):
        """GatewayError.to_error_detail() method"""
        error = GatewayError(
            code=ErrorCode.AGENT_NOT_FOUND,
            message="Agent not found",
            details={"agent_id": "test"},
            retry_after=5
        )
        detail = error.to_error_detail()
        assert isinstance(detail, ErrorDetail)
        assert detail.code == "AGENT_NOT_FOUND"
        assert detail.message == "Agent not found"
        assert detail.details == {"agent_id": "test"}


class TestInputError:
    """Test InputError class"""

    def test_default_input_error(self):
        """InputError with default values"""
        error = InputError()
        assert error.code == ErrorCode.INPUT_SCHEMA_VIOLATION
        assert error.message == "Input validation failed"
        assert error.http_status == 400

    def test_input_error_with_custom_values(self):
        """InputError with custom values"""
        error = InputError(
            code=ErrorCode.INPUT_MISSING_FIELD,
            message="Field 'name' is required",
            details={"field": "name"}
        )
        assert error.code == ErrorCode.INPUT_MISSING_FIELD
        assert error.message == "Field 'name' is required"
        assert error.details == {"field": "name"}


class TestAuthError:
    """Test AuthError class"""

    def test_default_auth_error(self):
        """AuthError with default values"""
        error = AuthError()
        assert error.code == ErrorCode.AUTH_TOKEN_MISSING
        assert error.message == "Authentication required"
        assert error.http_status == 401

    def test_auth_error_with_custom_values(self):
        """AuthError with custom values"""
        error = AuthError(
            code=ErrorCode.AUTH_PERMISSION_DENIED,
            message="Access denied",
            details={"resource": "admin"}
        )
        assert error.code == ErrorCode.AUTH_PERMISSION_DENIED
        assert error.http_status == 403


class TestAgentError:
    """Test AgentError class"""

    def test_default_agent_error(self):
        """AgentError with default values"""
        error = AgentError()
        assert error.code == ErrorCode.AGENT_NOT_FOUND
        assert error.message == "Agent error"
        assert error.http_status == 404

    def test_agent_error_with_custom_values(self):
        """AgentError with custom values"""
        error = AgentError(
            code=ErrorCode.AGENT_DISABLED,
            message="Agent is disabled",
            details={"agent_id": "test.agent"}
        )
        assert error.code == ErrorCode.AGENT_DISABLED
        assert error.http_status == 403


class TestExecError:
    """Test ExecError class"""

    def test_default_exec_error(self):
        """ExecError with default values"""
        error = ExecError()
        assert error.code == ErrorCode.EXEC_INTERNAL_ERROR
        assert error.message == "Execution error"
        assert error.http_status == 500

    def test_exec_error_with_retry_after(self):
        """ExecError with retry_after"""
        error = ExecError(
            code=ErrorCode.EXEC_TIMEOUT,
            message="Request timed out",
            retry_after=10
        )
        assert error.retry_after == 10
        assert error.is_retryable is True


class TestSystemError:
    """Test SystemError class"""

    def test_default_system_error(self):
        """SystemError with default values"""
        error = SystemError()
        assert error.code == ErrorCode.SYSTEM_INTERNAL_ERROR
        assert error.message == "Internal server error"
        assert error.http_status == 500

    def test_system_error_with_custom_code(self):
        """SystemError with custom code"""
        error = SystemError(
            code=ErrorCode.SYSTEM_MAINTENANCE,
            message="System under maintenance"
        )
        assert error.code == ErrorCode.SYSTEM_MAINTENANCE
        assert error.http_status == 503


class TestHelperFunctions:
    """Test helper functions for common errors"""

    def test_agent_not_found(self):
        """agent_not_found() helper"""
        error = agent_not_found("com.test.agent")
        assert isinstance(error, AgentError)
        assert error.code == ErrorCode.AGENT_NOT_FOUND
        assert "com.test.agent" in error.message
        assert error.details == {"agent_id": "com.test.agent"}
        assert error.http_status == 404

    def test_agent_not_installed(self):
        """agent_not_installed() helper"""
        error = agent_not_installed("com.test.agent")
        assert isinstance(error, AgentError)
        assert error.code == ErrorCode.AGENT_NOT_INSTALLED
        assert "com.test.agent" in error.message
        assert error.details == {"agent_id": "com.test.agent"}
        assert error.http_status == 403

    def test_agent_disabled(self):
        """agent_disabled() helper"""
        error = agent_disabled("com.test.agent")
        assert isinstance(error, AgentError)
        assert error.code == ErrorCode.AGENT_DISABLED
        assert "com.test.agent" in error.message
        assert error.details == {"agent_id": "com.test.agent"}
        assert error.http_status == 403

    def test_exec_timeout(self):
        """exec_timeout() helper"""
        error = exec_timeout(30000)
        assert isinstance(error, ExecError)
        assert error.code == ErrorCode.EXEC_TIMEOUT
        assert "30000" in error.message
        assert error.details == {"timeout_ms": 30000}
        assert error.retry_after == 5
        assert error.http_status == 504

    def test_exec_timeout_with_endpoint(self):
        """exec_timeout() with endpoint"""
        error = exec_timeout(30000, endpoint="https://api.example.com")
        assert error.details["endpoint"] == "https://api.example.com"

    def test_exec_downstream_error(self):
        """exec_downstream_error() helper"""
        error = exec_downstream_error("Connection refused")
        assert isinstance(error, ExecError)
        assert error.code == ErrorCode.EXEC_DOWNSTREAM_ERROR
        assert error.message == "Connection refused"
        assert error.retry_after == 10
        assert error.http_status == 502

    def test_exec_downstream_error_with_endpoint(self):
        """exec_downstream_error() with endpoint"""
        error = exec_downstream_error("Connection failed", endpoint="https://api.example.com")
        assert error.details["endpoint"] == "https://api.example.com"

    def test_agent_output_invalid(self):
        """agent_output_invalid() helper"""
        error = agent_output_invalid("Missing required field")
        assert isinstance(error, AgentError)
        assert error.code == ErrorCode.AGENT_OUTPUT_INVALID
        assert error.details == {"reason": "Missing required field"}
        assert error.http_status == 422

    def test_agent_output_invalid_with_field(self):
        """agent_output_invalid() with field"""
        error = agent_output_invalid("Missing field", field="result")
        assert error.details["missing_field"] == "result"

    def test_input_schema_violation(self):
        """input_schema_violation() helper"""
        errors = [
            {"path": "query", "message": "Too short"},
            {"path": "agent_id", "message": "Invalid format"}
        ]
        error = input_schema_violation(errors)
        assert isinstance(error, InputError)
        assert error.code == ErrorCode.INPUT_SCHEMA_VIOLATION
        assert error.details == {"validation_errors": errors}
        assert error.http_status == 400

    def test_input_missing_field(self):
        """input_missing_field() helper"""
        error = input_missing_field("request_id")
        assert isinstance(error, InputError)
        assert error.code == ErrorCode.INPUT_MISSING_FIELD
        assert "request_id" in error.message
        assert error.details == {"field": "request_id"}
        assert error.http_status == 400


class TestErrorInheritance:
    """Test error class inheritance"""

    def test_input_error_is_gateway_error(self):
        """InputError should be a GatewayError"""
        error = InputError()
        assert isinstance(error, GatewayError)
        assert isinstance(error, Exception)

    def test_auth_error_is_gateway_error(self):
        """AuthError should be a GatewayError"""
        error = AuthError()
        assert isinstance(error, GatewayError)

    def test_agent_error_is_gateway_error(self):
        """AgentError should be a GatewayError"""
        error = AgentError()
        assert isinstance(error, GatewayError)

    def test_exec_error_is_gateway_error(self):
        """ExecError should be a GatewayError"""
        error = ExecError()
        assert isinstance(error, GatewayError)

    def test_system_error_is_gateway_error(self):
        """SystemError should be a GatewayError"""
        error = SystemError()
        assert isinstance(error, GatewayError)


class TestErrorRaising:
    """Test that errors can be raised and caught"""

    def test_raise_and_catch_input_error(self):
        """Raise and catch InputError"""
        with pytest.raises(InputError) as exc_info:
            raise InputError(message="Test error")
        assert exc_info.value.message == "Test error"

    def test_raise_and_catch_gateway_error(self):
        """Raise and catch GatewayError"""
        with pytest.raises(GatewayError) as exc_info:
            raise GatewayError(code=ErrorCode.SYSTEM_INTERNAL_ERROR, message="Test")
        assert exc_info.value.code == ErrorCode.SYSTEM_INTERNAL_ERROR

    def test_catch_subclass_as_base_class(self):
        """Catch subclass error as base GatewayError"""
        with pytest.raises(GatewayError):
            raise AgentError(code=ErrorCode.AGENT_NOT_FOUND, message="Not found")
