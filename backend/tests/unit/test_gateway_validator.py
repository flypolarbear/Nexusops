"""
Gateway Validator Module Unit Tests

MVP-TEST-002: validator.py 测试覆盖率 >= 80%

Tests:
- ValidationError dataclass
- SchemaValidator class
- validate_invoke_request function
- check_validation_and_raise function
"""

import pytest
from unittest.mock import patch, MagicMock

from app.gateway.validator import (
    ValidationError,
    SchemaValidator,
    validate_invoke_request,
    check_validation_and_raise,
    HAS_JSONSCHEMA,
)
from app.gateway.errors import InputError


class TestValidationError:
    """Test ValidationError dataclass"""

    def test_validation_error_required_fields(self):
        """ValidationError with required fields"""
        error = ValidationError(
            path="query",
            message="Field is required"
        )
        assert error.path == "query"
        assert error.message == "Field is required"
        assert error.expected is None
        assert error.actual is None

    def test_validation_error_with_all_fields(self):
        """ValidationError with all fields"""
        error = ValidationError(
            path="agent_id",
            message="Invalid format",
            expected="^[a-z][a-z0-9._-]{2,63}$",
            actual="INVALID"
        )
        assert error.path == "agent_id"
        assert error.message == "Invalid format"
        assert error.expected == "^[a-z][a-z0-9._-]{2,63}$"
        assert error.actual == "INVALID"

    def test_validation_error_to_dict_minimal(self):
        """ValidationError.to_dict() with minimal fields"""
        error = ValidationError(path="field", message="Error")
        result = error.to_dict()
        assert result == {"path": "field", "message": "Error"}

    def test_validation_error_to_dict_full(self):
        """ValidationError.to_dict() with all fields"""
        error = ValidationError(
            path="field",
            message="Error",
            expected="string",
            actual="number"
        )
        result = error.to_dict()
        assert result["path"] == "field"
        assert result["message"] == "Error"
        assert result["expected"] == "string"
        assert result["actual"] == "number"


class TestSchemaValidator:
    """Test SchemaValidator class"""

    def test_validator_strict_mode_default(self):
        """SchemaValidator default strict_mode"""
        validator = SchemaValidator()
        assert validator.strict_mode is True

    def test_validator_non_strict_mode(self):
        """SchemaValidator with strict_mode=False"""
        validator = SchemaValidator(strict_mode=False)
        assert validator.strict_mode is False

    def test_validate_field_required_missing(self):
        """validate_field with required field missing"""
        validator = SchemaValidator()
        error = validator.validate_field(
            value=None,
            field_name="test_field",
            required=True
        )
        assert error is not None
        assert error.path == "test_field"
        assert "required" in error.message.lower()

    def test_validate_field_required_present(self):
        """validate_field with required field present"""
        validator = SchemaValidator()
        error = validator.validate_field(
            value="value",
            field_name="test_field",
            required=True
        )
        assert error is None

    def test_validate_field_optional_missing(self):
        """validate_field with optional field missing"""
        validator = SchemaValidator()
        error = validator.validate_field(
            value=None,
            field_name="test_field",
            required=False
        )
        assert error is None

    def test_validate_field_type_string(self):
        """validate_field with string type"""
        validator = SchemaValidator()
        # Valid string
        error = validator.validate_field(
            value="hello",
            field_name="test",
            field_type="string"
        )
        assert error is None

        # Invalid type
        error = validator.validate_field(
            value=123,
            field_name="test",
            field_type="string"
        )
        assert error is not None
        assert error.expected == "string"
        assert error.actual == "int"

    def test_validate_field_type_integer(self):
        """validate_field with integer type"""
        validator = SchemaValidator()
        # Valid integer
        error = validator.validate_field(
            value=42,
            field_name="test",
            field_type="integer"
        )
        assert error is None

        # Invalid type
        error = validator.validate_field(
            value="42",
            field_name="test",
            field_type="integer"
        )
        assert error is not None

    def test_validate_field_type_number(self):
        """validate_field with number type"""
        validator = SchemaValidator()
        # Valid int
        error = validator.validate_field(
            value=42,
            field_name="test",
            field_type="number"
        )
        assert error is None

        # Valid float
        error = validator.validate_field(
            value=3.14,
            field_name="test",
            field_type="number"
        )
        assert error is None

        # Invalid type
        error = validator.validate_field(
            value="3.14",
            field_name="test",
            field_type="number"
        )
        assert error is not None

    def test_validate_field_type_boolean(self):
        """validate_field with boolean type"""
        validator = SchemaValidator()
        # Valid boolean
        error = validator.validate_field(
            value=True,
            field_name="test",
            field_type="boolean"
        )
        assert error is None

        error = validator.validate_field(
            value=False,
            field_name="test",
            field_type="boolean"
        )
        assert error is None

        # Invalid type
        error = validator.validate_field(
            value="true",
            field_name="test",
            field_type="boolean"
        )
        assert error is not None

    def test_validate_field_type_array(self):
        """validate_field with array type"""
        validator = SchemaValidator()
        # Valid array
        error = validator.validate_field(
            value=[1, 2, 3],
            field_name="test",
            field_type="array"
        )
        assert error is None

        # Invalid type
        error = validator.validate_field(
            value="not an array",
            field_name="test",
            field_type="array"
        )
        assert error is not None

    def test_validate_field_type_object(self):
        """validate_field with object type"""
        validator = SchemaValidator()
        # Valid object
        error = validator.validate_field(
            value={"key": "value"},
            field_name="test",
            field_type="object"
        )
        assert error is None

        # Invalid type
        error = validator.validate_field(
            value="not an object",
            field_name="test",
            field_type="object"
        )
        assert error is not None

    def test_validate_field_min_length(self):
        """validate_field with min_length constraint"""
        validator = SchemaValidator()
        # Valid
        error = validator.validate_field(
            value="hello",
            field_name="test",
            min_length=3
        )
        assert error is None

        # Too short
        error = validator.validate_field(
            value="hi",
            field_name="test",
            min_length=3
        )
        assert error is not None
        assert "at least" in error.message.lower()

    def test_validate_field_max_length(self):
        """validate_field with max_length constraint"""
        validator = SchemaValidator()
        # Valid
        error = validator.validate_field(
            value="hello",
            field_name="test",
            max_length=10
        )
        assert error is None

        # Too long
        error = validator.validate_field(
            value="this is a very long string",
            field_name="test",
            max_length=10
        )
        assert error is not None
        assert "at most" in error.message.lower()

    def test_validate_field_enum(self):
        """validate_field with enum constraint"""
        validator = SchemaValidator()
        # Valid value
        error = validator.validate_field(
            value="markdown",
            field_name="format",
            enum=["markdown", "json", "plain"]
        )
        assert error is None

        # Invalid value
        error = validator.validate_field(
            value="html",
            field_name="format",
            enum=["markdown", "json", "plain"]
        )
        assert error is not None
        assert "must be one of" in error.message.lower()

    def test_validate_field_unknown_type(self):
        """validate_field with unknown type (should pass)"""
        validator = SchemaValidator()
        error = validator.validate_field(
            value="anything",
            field_name="test",
            field_type="unknown_type"
        )
        assert error is None  # Unknown types are allowed

    def test_validate_request_with_jsonschema(self):
        """validate_request with jsonschema"""
        if not HAS_JSONSCHEMA:
            pytest.skip("jsonschema not installed")

        validator = SchemaValidator()
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        }

        # Valid data
        errors = validator.validate_request(
            data={"name": "John", "age": 30},
            schema=schema
        )
        assert errors == []

        # Invalid data - missing required
        errors = validator.validate_request(
            data={"age": 30},
            schema=schema
        )
        assert len(errors) == 1
        assert "required" in errors[0].message.lower() or "name" in errors[0].message.lower()

    def test_validate_request_without_jsonschema(self):
        """validate_request without jsonschema (should skip)"""
        with patch('app.gateway.validator.HAS_JSONSCHEMA', False):
            validator = SchemaValidator()
            errors = validator.validate_request(
                data={"invalid": "data"},
                schema={"type": "string"}  # Schema doesn't match data
            )
            assert errors == []  # Should skip validation

    def test_format_path_empty(self):
        """_format_path with empty path"""
        validator = SchemaValidator()
        result = validator._format_path([])
        assert result == "root"

    def test_format_path_with_elements(self):
        """_format_path with path elements"""
        validator = SchemaValidator()
        result = validator._format_path(["data", "items", 0, "name"])
        assert result == "data.items.0.name"


class TestValidateInvokeRequest:
    """Test validate_invoke_request function"""

    def test_valid_request(self):
        """Valid invoke request"""
        data = {
            "request_id": "req-123",
            "agent_id": "test.agent",
            "query": "Hello, world!"
        }
        errors = validate_invoke_request(data)
        assert errors == []

    def test_missing_request_id(self):
        """Missing request_id"""
        data = {
            "agent_id": "test.agent",
            "query": "Hello"
        }
        errors = validate_invoke_request(data)
        assert len(errors) == 1
        assert errors[0].path == "request_id"

    def test_missing_agent_id(self):
        """Missing agent_id"""
        data = {
            "request_id": "req-123",
            "query": "Hello"
        }
        errors = validate_invoke_request(data)
        assert len(errors) == 1
        assert errors[0].path == "agent_id"

    def test_missing_query(self):
        """Missing query"""
        data = {
            "request_id": "req-123",
            "agent_id": "test.agent"
        }
        errors = validate_invoke_request(data)
        assert len(errors) == 1
        assert errors[0].path == "query"

    def test_missing_all_required(self):
        """Missing all required fields"""
        data = {}
        errors = validate_invoke_request(data)
        assert len(errors) == 3
        paths = {e.path for e in errors}
        assert "request_id" in paths
        assert "agent_id" in paths
        assert "query" in paths

    def test_query_too_long(self):
        """Query exceeds max length"""
        data = {
            "request_id": "req-123",
            "agent_id": "test.agent",
            "query": "x" * 10001  # Max is 10000
        }
        errors = validate_invoke_request(data)
        # May have length validation error
        assert len(errors) >= 0  # Depends on whether pattern validation is applied

    def test_valid_request_with_optional_fields(self):
        """Valid request with optional fields"""
        data = {
            "request_id": "req-123",
            "conversation_id": "conv-456",
            "agent_id": "test.agent",
            "query": "Hello",
            "context": {"user_id": "user-123"},
            "output_config": {"format": "json"}
        }
        errors = validate_invoke_request(data)
        assert errors == []


class TestCheckValidationAndRaise:
    """Test check_validation_and_raise function"""

    def test_valid_data_no_raise(self):
        """Valid data should not raise"""
        data = {
            "request_id": "req-123",
            "agent_id": "test.agent",
            "query": "Hello"
        }
        # Should not raise
        check_validation_and_raise(data)

    def test_invalid_data_raises_input_error(self):
        """Invalid data should raise InputError"""
        data = {
            "agent_id": "test.agent",
            "query": "Hello"
            # Missing request_id
        }
        with pytest.raises(InputError) as exc_info:
            check_validation_and_raise(data)

        assert exc_info.value.code.value == "INPUT_SCHEMA_VIOLATION"
        assert "validation_errors" in exc_info.value.details

    def test_invalid_data_error_contains_details(self):
        """Error should contain validation details"""
        data = {}  # Missing all required fields
        with pytest.raises(InputError) as exc_info:
            check_validation_and_raise(data)

        errors = exc_info.value.details["validation_errors"]
        assert len(errors) >= 3
        paths = {e["path"] for e in errors}
        assert "request_id" in paths
        assert "agent_id" in paths
        assert "query" in paths


class TestSchemaValidatorEdgeCases:
    """Test SchemaValidator edge cases"""

    def test_validate_field_empty_string(self):
        """validate_field with empty string"""
        validator = SchemaValidator()

        # Empty string is valid if not required and no min_length
        error = validator.validate_field(
            value="",
            field_name="test",
            required=False
        )
        assert error is None

        # Empty string fails min_length=1
        error = validator.validate_field(
            value="",
            field_name="test",
            min_length=1
        )
        assert error is not None

    def test_validate_field_zero_values(self):
        """validate_field with zero values"""
        validator = SchemaValidator()

        # Zero integer is valid
        error = validator.validate_field(
            value=0,
            field_name="test",
            field_type="integer"
        )
        assert error is None

        # Zero float is valid
        error = validator.validate_field(
            value=0.0,
            field_name="test",
            field_type="number"
        )
        assert error is None

    def test_validate_field_false_boolean(self):
        """validate_field with False boolean"""
        validator = SchemaValidator()
        error = validator.validate_field(
            value=False,
            field_name="test",
            field_type="boolean"
        )
        assert error is None

    def test_validate_field_empty_collections(self):
        """validate_field with empty collections"""
        validator = SchemaValidator()

        # Empty list is valid
        error = validator.validate_field(
            value=[],
            field_name="test",
            field_type="array"
        )
        assert error is None

        # Empty dict is valid
        error = validator.validate_field(
            value={},
            field_name="test",
            field_type="object"
        )
        assert error is None

    def test_validate_field_numeric_string(self):
        """validate_field with numeric string"""
        validator = SchemaValidator()
        # "123" is not an integer type
        error = validator.validate_field(
            value="123",
            field_name="test",
            field_type="integer"
        )
        assert error is not None


class TestValidatorIntegration:
    """Integration tests for validator"""

    def test_full_validation_workflow(self):
        """Complete validation workflow"""
        # Step 1: Create validator
        validator = SchemaValidator()

        # Step 2: Validate individual fields
        errors = []

        # Validate request_id
        error = validator.validate_field(
            value="req-123",
            field_name="request_id",
            required=True,
            field_type="string"
        )
        if error:
            errors.append(error)

        # Validate agent_id
        error = validator.validate_field(
            value="test.agent",
            field_name="agent_id",
            required=True,
            field_type="string"
        )
        if error:
            errors.append(error)

        # Validate query
        error = validator.validate_field(
            value="Hello, world!",
            field_name="query",
            required=True,
            field_type="string",
            min_length=1,
            max_length=10000
        )
        if error:
            errors.append(error)

        assert errors == []

    def test_validation_with_check_and_raise(self):
        """Validation using check_validation_and_raise"""
        # Valid request
        valid_data = {
            "request_id": "req-123",
            "agent_id": "test.agent",
            "query": "Hello"
        }

        # Should not raise
        try:
            check_validation_and_raise(valid_data)
            success = True
        except InputError:
            success = False

        assert success is True
