"""
Tests for NexusOps SDK Exceptions
"""

import pytest

from sdk.exceptions import (
    NexusOpsError,
    AgentNotFoundError,
    AgentTimeoutError,
    AuthenticationError,
    AuthorizationError,
    AgentNotInstalledError,
    AgentDisabledError,
    ValidationError,
    ConnectionError,
    RateLimitError,
)


class TestNexusOpsError:
    """Tests for the base NexusOpsError exception."""

    def test_basic_error(self):
        """Test basic error creation."""
        error = NexusOpsError(message="Something went wrong")
        assert error.message == "Something went wrong"
        assert error.code == "UNKNOWN_ERROR"
        assert error.details == {}
        assert error.retry_after is None

    def test_error_with_all_fields(self):
        """Test error with all fields."""
        error = NexusOpsError(
            message="Custom error",
            code="CUSTOM_ERROR",
            details={"key": "value"},
            retry_after=60,
        )
        assert error.message == "Custom error"
        assert error.code == "CUSTOM_ERROR"
        assert error.details == {"key": "value"}
        assert error.retry_after == 60

    def test_str_representation(self):
        """Test string representation."""
        error = NexusOpsError(
            message="Test error",
            code="TEST_ERROR",
            details={"foo": "bar"},
        )
        assert "[TEST_ERROR]" in str(error)
        assert "Test error" in str(error)
        assert "Details:" in str(error)

    def test_str_with_retry_after(self):
        """Test string representation with retry_after."""
        error = NexusOpsError(
            message="Rate limited",
            code="RATE_LIMITED",
            retry_after=30,
        )
        assert "Retry after: 30s" in str(error)


class TestAgentNotFoundError:
    """Tests for AgentNotFoundError exception."""

    def test_basic_error(self):
        """Test basic agent not found error."""
        error = AgentNotFoundError(agent_id="test-agent")
        assert error.agent_id == "test-agent"
        assert error.code == "AGENT_NOT_FOUND"
        assert "test-agent" in error.message
        assert error.details["agent_id"] == "test-agent"

    def test_custom_message(self):
        """Test with custom message."""
        error = AgentNotFoundError(
            agent_id="test-agent",
            message="Custom not found message",
        )
        assert error.message == "Custom not found message"
        assert error.details["agent_id"] == "test-agent"


class TestAgentTimeoutError:
    """Tests for AgentTimeoutError exception."""

    def test_basic_error(self):
        """Test basic timeout error."""
        error = AgentTimeoutError(agent_id="test-agent", timeout_seconds=30.0)
        assert error.agent_id == "test-agent"
        assert error.timeout_seconds == 30.0
        assert error.code == "AGENT_TIMEOUT"
        assert "30.0s" in error.message

    def test_custom_message(self):
        """Test with custom message."""
        error = AgentTimeoutError(
            agent_id="test-agent",
            timeout_seconds=60.0,
            message="Request took too long",
        )
        assert error.message == "Request took too long"


class TestAuthenticationError:
    """Tests for AuthenticationError exception."""

    def test_basic_error(self):
        """Test basic authentication error."""
        error = AuthenticationError()
        assert error.code == "AUTHENTICATION_ERROR"
        assert "API key" in error.message

    def test_custom_message(self):
        """Test with custom message."""
        error = AuthenticationError(message="Invalid token")
        assert error.message == "Invalid token"


class TestAuthorizationError:
    """Tests for AuthorizationError exception."""

    def test_basic_error(self):
        """Test basic authorization error."""
        error = AuthorizationError()
        assert error.code == "AUTHORIZATION_ERROR"
        assert "permissions" in error.message.lower()

    def test_with_resource(self):
        """Test with resource specified."""
        error = AuthorizationError(resource="agent/test-agent")
        assert error.details["resource"] == "agent/test-agent"


class TestAgentNotInstalledError:
    """Tests for AgentNotInstalledError exception."""

    def test_basic_error(self):
        """Test basic not installed error."""
        error = AgentNotInstalledError(agent_id="third-party-agent")
        assert error.agent_id == "third-party-agent"
        assert error.code == "AGENT_NOT_INSTALLED"
        assert "not installed" in error.message.lower()


class TestAgentDisabledError:
    """Tests for AgentDisabledError exception."""

    def test_basic_error(self):
        """Test basic disabled error."""
        error = AgentDisabledError(agent_id="disabled-agent")
        assert error.agent_id == "disabled-agent"
        assert error.code == "AGENT_DISABLED"
        assert "disabled" in error.message.lower()


class TestValidationError:
    """Tests for ValidationError exception."""

    def test_basic_error(self):
        """Test basic validation error."""
        error = ValidationError(message="Invalid input")
        assert error.code == "VALIDATION_ERROR"
        assert error.message == "Invalid input"

    def test_with_field(self):
        """Test with field specified."""
        error = ValidationError(message="Required field missing", field="agent_id")
        assert error.details["field"] == "agent_id"


class TestConnectionError:
    """Tests for ConnectionError exception."""

    def test_basic_error(self):
        """Test basic connection error."""
        error = ConnectionError()
        assert error.code == "CONNECTION_ERROR"
        assert "connect" in error.message.lower()

    def test_with_base_url(self):
        """Test with base URL specified."""
        error = ConnectionError(base_url="https://nexusops.example.com")
        assert error.details["base_url"] == "https://nexusops.example.com"


class TestRateLimitError:
    """Tests for RateLimitError exception."""

    def test_basic_error(self):
        """Test basic rate limit error."""
        error = RateLimitError()
        assert error.code == "RATE_LIMIT_EXCEEDED"
        assert "rate limit" in error.message.lower()

    def test_with_retry_after(self):
        """Test with retry_after specified."""
        error = RateLimitError(retry_after=120)
        assert error.retry_after == 120
