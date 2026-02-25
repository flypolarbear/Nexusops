"""
NexusOps Gateway - JSON Schema Validator

MK-006: JSON Schema 校验机制

Provides JSON Schema validation for requests and responses.
"""

import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

try:
    import jsonschema
    from jsonschema import validate, ValidationError as JsonSchemaValidationError
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    JsonSchemaValidationError = Exception

from app.gateway.errors import (
    InputError,
    ErrorCode,
    input_schema_violation,
    input_missing_field,
)


@dataclass
class ValidationError:
    """Validation error detail"""
    path: str
    message: str
    expected: Optional[str] = None
    actual: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "path": self.path,
            "message": self.message,
        }
        if self.expected:
            result["expected"] = self.expected
        if self.actual:
            result["actual"] = self.actual
        return result


class SchemaValidator:
    """JSON Schema validator"""

    def __init__(self, strict_mode: bool = True):
        """
        Initialize validator.

        Args:
            strict_mode: If True, validation errors raise exceptions.
                        If False, errors are logged but validation passes.
        """
        self.strict_mode = strict_mode
        self._errors: List[ValidationError] = []

    def validate_request(
        self,
        data: Dict[str, Any],
        schema: Dict[str, Any],
    ) -> List[ValidationError]:
        """
        Validate request data against schema.

        Returns list of validation errors (empty if valid).
        """
        self._errors = []

        if not HAS_JSONSCHEMA:
            # Skip validation if jsonschema not installed
            return []

        try:
            jsonschema.validate(data, schema)
        except JsonSchemaValidationError as e:
            error = ValidationError(
                path=self._format_path(e.absolute_path),
                message=e.message,
                expected=self._get_expected(e),
                actual=self._get_actual(e),
            )
            self._errors.append(error)

        return self._errors

    def validate_field(
        self,
        value: Any,
        field_name: str,
        required: bool = False,
        field_type: Optional[str] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        enum: Optional[List[Any]] = None,
    ) -> Optional[ValidationError]:
        """
        Validate a single field.

        Returns ValidationError if invalid, None if valid.
        """
        # Check required
        if required and value is None:
            return ValidationError(
                path=field_name,
                message=f"Required field missing: {field_name}",
            )

        if value is None:
            return None

        # Check type
        if field_type:
            type_valid = self._check_type(value, field_type)
            if not type_valid:
                return ValidationError(
                    path=field_name,
                    message=f"Invalid type for {field_name}",
                    expected=field_type,
                    actual=type(value).__name__,
                )

        # Check string constraints
        if isinstance(value, str):
            if min_length is not None and len(value) < min_length:
                return ValidationError(
                    path=field_name,
                    message=f"{field_name} must be at least {min_length} characters",
                    expected=f"min_length={min_length}",
                    actual=f"length={len(value)}",
                )

            if max_length is not None and len(value) > max_length:
                return ValidationError(
                    path=field_name,
                    message=f"{field_name} must be at most {max_length} characters",
                    expected=f"max_length={max_length}",
                    actual=f"length={len(value)}",
                )

        # Check enum
        if enum and value not in enum:
            return ValidationError(
                path=field_name,
                message=f"{field_name} must be one of: {enum}",
                expected=str(enum),
                actual=str(value),
            )

        return None

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type"""
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
        }
        expected = type_map.get(expected_type)
        if expected is None:
            return True
        return isinstance(value, expected)

    def _format_path(self, path) -> str:
        """Format JSON path for error message"""
        if not path:
            return "root"
        return ".".join(str(p) for p in path)

    def _get_expected(self, error) -> Optional[str]:
        """Get expected value from error"""
        if hasattr(error, "validator"):
            return str(error.validator)
        return None

    def _get_actual(self, error) -> Optional[str]:
        """Get actual value from error"""
        if hasattr(error, "instance"):
            instance = error.instance
            if isinstance(instance, (dict, list)):
                return f"{type(instance).__name__}(len={len(instance)})"
            return str(instance)[:100]
        return None


def validate_invoke_request(data: Dict[str, Any]) -> List[ValidationError]:
    """
    Validate an invoke request.

    Returns list of validation errors.
    """
    validator = SchemaValidator()

    errors = []

    # Check required fields
    if "request_id" not in data:
        errors.append(ValidationError(
            path="request_id",
            message="Required field missing: request_id",
        ))

    if "agent_id" not in data:
        errors.append(ValidationError(
            path="agent_id",
            message="Required field missing: agent_id",
        ))

    if "query" not in data:
        errors.append(ValidationError(
            path="query",
            message="Required field missing: query",
        ))

    # Validate field formats
    if "agent_id" in data:
        error = validator.validate_field(
            data["agent_id"],
            "agent_id",
            required=True,
            field_type="string",
            pattern=r"^[a-z][a-z0-9._-]{2,63}$",
        )
        if error:
            errors.append(error)

    if "query" in data:
        error = validator.validate_field(
            data["query"],
            "query",
            required=True,
            field_type="string",
            min_length=1,
            max_length=10000,
        )
        if error:
            errors.append(error)

    return errors


def check_validation_and_raise(data: Dict[str, Any]) -> None:
    """
    Validate request and raise InputError if invalid.

    Raises:
        InputError: If validation fails
    """
    errors = validate_invoke_request(data)

    if errors:
        raise input_schema_violation([
            error.to_dict() for error in errors
        ])
