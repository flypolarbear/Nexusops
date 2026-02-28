"""
Unit tests for app/services/json_output.py

Tests for JSON validation, repair, generation, and formatting.
"""

import pytest
import json
from pydantic import BaseModel
from unittest.mock import AsyncMock, MagicMock

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

from app.services.json_output import (
    ValidationResult,
    JSONSchemaValidator,
    JSONRepair,
    OutputFormatter,
    JSONGenerator,
    InstructorWrapper,
    AgentResponseFormatter,
)


class TestModel(BaseModel):
    """Test Pydantic model for validation tests"""
    name: str
    age: int
    active: bool = True


class TestValidationResult:
    """Tests for ValidationResult dataclass"""

    def test_success_result(self):
        """Test creating a successful validation result"""
        result = ValidationResult(success=True, data={"key": "value"})
        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.errors == []

    def test_failure_result(self):
        """Test creating a failed validation result"""
        result = ValidationResult(success=False, errors=["Error 1", "Error 2"])
        assert result.success is False
        assert result.data is None
        assert result.errors == ["Error 1", "Error 2"]

    def test_post_init_creates_empty_errors(self):
        """Test that __post_init__ creates empty errors list"""
        result = ValidationResult(success=True, data=None)
        assert result.errors == []


class TestJSONSchemaValidator:
    """Tests for JSONSchemaValidator"""

    def test_validate_pydantic_success(self):
        """Test successful Pydantic validation"""
        data = {"name": "John", "age": 30}
        result = JSONSchemaValidator.validate_pydantic(data, TestModel)
        assert result.success is True
        assert isinstance(result.data, TestModel)
        assert result.data.name == "John"
        assert result.data.age == 30

    def test_validate_pydantic_missing_field(self):
        """Test Pydantic validation with missing required field"""
        data = {"name": "John"}  # missing age
        result = JSONSchemaValidator.validate_pydantic(data, TestModel)
        assert result.success is False
        assert len(result.errors) > 0

    def test_validate_pydantic_wrong_type(self):
        """Test Pydantic validation with wrong type"""
        data = {"name": "John", "age": "thirty"}  # age should be int
        result = JSONSchemaValidator.validate_pydantic(data, TestModel)
        assert result.success is False

    @pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
    def test_validate_with_schema(self):
        """Test validation with JSON schema"""
        data = {"name": "test", "value": 123}
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "number"}
            },
            "required": ["name"]
        }
        result = JSONSchemaValidator.validate(data, schema)
        assert result.success is True

    @pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
    def test_validate_schema_failure(self):
        """Test schema validation failure"""
        data = {"name": 123}  # should be string
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            },
            "required": ["name"]
        }
        result = JSONSchemaValidator.validate(data, schema)
        assert result.success is False


class TestJSONRepair:
    """Tests for JSONRepair"""

    def test_repair_valid_json(self):
        """Test repairing already valid JSON"""
        json_str = '{"name": "John", "age": 30}'
        data, warnings = JSONRepair.repair(json_str)
        assert data == {"name": "John", "age": 30}
        assert warnings == []

    def test_repair_single_quotes(self):
        """Test repairing JSON with single quotes"""
        json_str = "{'name': 'John', 'age': 30}"
        data, warnings = JSONRepair.repair(json_str)
        assert data == {"name": "John", "age": 30}
        assert "single quotes" in " ".join(warnings).lower()

    def test_repair_trailing_commas(self):
        """Test repairing JSON with trailing commas"""
        json_str = '{"name": "John", "age": 30,}'
        data, warnings = JSONRepair.repair(json_str)
        assert data == {"name": "John", "age": 30}

    def test_repair_markdown_code_block(self):
        """Test repairing JSON in markdown code block"""
        json_str = '''```json
{"name": "John", "age": 30}
```'''
        data, warnings = JSONRepair.repair(json_str)
        assert data == {"name": "John", "age": 30}
        assert "markdown" in " ".join(warnings).lower()

    def test_repair_python_bools(self):
        """Test repairing JSON with Python booleans"""
        json_str = '{"active": True, "disabled": False}'
        data, warnings = JSONRepair.repair(json_str)
        assert data == {"active": True, "disabled": False}

    def test_repair_python_none(self):
        """Test repairing JSON with Python None"""
        json_str = '{"value": None}'
        data, warnings = JSONRepair.repair(json_str)
        assert data == {"value": None}

    def test_repair_invalid_json(self):
        """Test repairing completely invalid JSON"""
        json_str = "this is not json at all"
        data, warnings = JSONRepair.repair(json_str)
        assert data is None
        assert len(warnings) > 0

    def test_extract_json_from_markdown(self):
        """Test extracting JSON from markdown text"""
        text = '''Here is some text:
```json
{"name": "John", "age": 30}
```
More text here.'''
        data = JSONRepair.extract_json(text)
        assert data == {"name": "John", "age": 30}

    def test_extract_json_from_text(self):
        """Test extracting JSON embedded in text"""
        text = 'The response is {"status": "ok", "code": 200} as expected'
        data = JSONRepair.extract_json(text)
        assert data == {"status": "ok", "code": 200}

    def test_extract_json_no_json(self):
        """Test extracting when no JSON present"""
        text = "This is just plain text with no JSON"
        data = JSONRepair.extract_json(text)
        assert data is None


class TestOutputFormatter:
    """Tests for OutputFormatter"""

    def test_to_json_dict(self):
        """Test formatting dict to JSON"""
        data = {"name": "John", "age": 30}
        result = OutputFormatter.to_json(data)
        parsed = json.loads(result)
        assert parsed == data

    def test_to_json_pydantic(self):
        """Test formatting Pydantic model to JSON"""
        model = TestModel(name="John", age=30)
        result = OutputFormatter.to_json(model)
        parsed = json.loads(result)
        assert parsed["name"] == "John"
        assert parsed["age"] == 30

    def test_to_json_with_indent(self):
        """Test JSON formatting with custom indent"""
        data = {"key": "value"}
        result = OutputFormatter.to_json(data, indent=4)
        assert "    " in result  # 4-space indent

    def test_ensure_type_no_conversion(self):
        """Test ensure_type when type already correct"""
        assert OutputFormatter.ensure_type("hello", str) == "hello"
        assert OutputFormatter.ensure_type(42, int) == 42
        assert OutputFormatter.ensure_type(3.14, float) == 3.14
        assert OutputFormatter.ensure_type(True, bool) is True

    def test_ensure_type_string_to_int(self):
        """Test converting string to int"""
        assert OutputFormatter.ensure_type("42", int) == 42

    def test_ensure_type_string_to_float(self):
        """Test converting string to float"""
        assert OutputFormatter.ensure_type("3.14", float) == 3.14

    def test_ensure_type_string_to_bool(self):
        """Test converting string to bool"""
        assert OutputFormatter.ensure_type("true", bool) is True
        assert OutputFormatter.ensure_type("True", bool) is True
        assert OutputFormatter.ensure_type("1", bool) is True
        assert OutputFormatter.ensure_type("yes", bool) is True
        assert OutputFormatter.ensure_type("false", bool) is False
        assert OutputFormatter.ensure_type("0", bool) is False

    def test_ensure_type_string_to_list(self):
        """Test converting JSON string to list"""
        assert OutputFormatter.ensure_type('[1, 2, 3]', list) == [1, 2, 3]

    def test_ensure_type_string_to_dict(self):
        """Test converting JSON string to dict"""
        assert OutputFormatter.ensure_type('{"a": 1}', dict) == {"a": 1}

    def test_ensure_type_failed_conversion(self):
        """Test ensure_type returns original on failed conversion"""
        result = OutputFormatter.ensure_type("not a number", int)
        assert result == "not a number"


class TestJSONGenerator:
    """Tests for JSONGenerator"""

    @pytest.mark.asyncio
    async def test_generate_success_first_try(self):
        """Test successful generation on first attempt"""
        async def llm_call(prompt):
            return '{"name": "John", "age": 30}'
        
        generator = JSONGenerator(model=TestModel, max_retries=3)
        result, errors = await generator.generate("Create a person", llm_call)
        
        assert result is not None
        assert result.name == "John"
        assert result.age == 30

    @pytest.mark.asyncio
    async def test_generate_with_repair(self):
        """Test generation with JSON repair"""
        async def llm_call(prompt):
            return "{'name': 'John', 'age': 30}"  # single quotes
        
        generator = JSONGenerator(model=TestModel, max_retries=3, repair_enabled=True)
        result, errors = await generator.generate("Create a person", llm_call)
        
        assert result is not None
        assert result.name == "John"

    @pytest.mark.asyncio
    async def test_generate_max_retries_exceeded(self):
        """Test generation fails after max retries"""
        call_count = 0
        async def llm_call(prompt):
            nonlocal call_count
            call_count += 1
            return "invalid json"
        
        generator = JSONGenerator(model=TestModel, max_retries=2)
        result, errors = await generator.generate("Create a person", llm_call)
        
        assert result is None
        assert call_count == 2
        assert len(errors) > 0

    def test_build_prompt_no_errors(self):
        """Test prompt building without previous errors"""
        generator = JSONGenerator(model=TestModel)
        prompt = generator._build_prompt("Test prompt", '{"type": "object"}', [])
        
        assert "Test prompt" in prompt
        assert "JSON object" in prompt

    def test_build_prompt_with_errors(self):
        """Test prompt building with previous errors"""
        generator = JSONGenerator(model=TestModel)
        prompt = generator._build_prompt("Test prompt", '{"type": "object"}', ["Error 1", "Error 2"])
        
        assert "Previous attempts failed" in prompt
        assert "Error 1" in prompt


class TestInstructorWrapper:
    """Tests for InstructorWrapper"""

    def test_from_response_success(self):
        """Test extracting valid JSON from response"""
        wrapper = InstructorWrapper()
        response_text = '{"name": "John", "age": 30}'
        
        result, errors = wrapper.from_response(response_text, TestModel)
        
        assert result is not None
        assert result.name == "John"
        assert result.age == 30

    def test_from_response_with_markdown(self):
        """Test extracting JSON from markdown response"""
        wrapper = InstructorWrapper()
        response_text = '''```json
{"name": "John", "age": 30}
```'''
        
        result, errors = wrapper.from_response(response_text, TestModel)
        
        assert result is not None

    def test_from_response_invalid_json(self):
        """Test handling invalid JSON response"""
        wrapper = InstructorWrapper()
        response_text = "This is not JSON"
        
        result, errors = wrapper.from_response(response_text, TestModel)
        
        assert result is None
        assert len(errors) > 0

    def test_from_response_validation_failure(self):
        """Test handling validation failure"""
        wrapper = InstructorWrapper()
        response_text = '{"name": "John"}'  # missing required age
        
        result, errors = wrapper.from_response(response_text, TestModel)
        
        assert result is None
        assert len(errors) > 0

    def test_from_response_skip_validation(self):
        """Test skipping validation"""
        wrapper = InstructorWrapper()
        response_text = '{"name": "John", "age": 30}'
        
        result, errors = wrapper.from_response(response_text, TestModel, validation=False)
        
        assert result is not None


class TestAgentResponseFormatter:
    """Tests for AgentResponseFormatter"""

    def test_format_success_minimal(self):
        """Test formatting minimal success response"""
        result = AgentResponseFormatter.format_success(
            request_id="req-123",
            content="Hello, world!"
        )
        
        assert result["request_id"] == "req-123"
        assert result["status"] == "success"
        assert result["content"]["text"] == "Hello, world!"
        assert result["structured_output"] is None
        assert result["suggested_actions"] == []

    def test_format_success_full(self):
        """Test formatting full success response"""
        result = AgentResponseFormatter.format_success(
            request_id="req-123",
            content="Hello!",
            structured_output={"type": "greeting"},
            actions=[{"label": "Click me"}],
            metadata={"source": "test"}
        )
        
        assert result["structured_output"] == {"type": "greeting"}
        assert result["suggested_actions"] == [{"label": "Click me"}]
        assert result["metadata"] == {"source": "test"}

    def test_format_error(self):
        """Test formatting error response"""
        result = AgentResponseFormatter.format_error(
            request_id="req-123",
            error_code="INVALID_INPUT",
            error_message="Invalid input provided"
        )
        
        assert result["request_id"] == "req-123"
        assert result["status"] == "error"
        assert result["error"]["code"] == "INVALID_INPUT"
        assert result["error"]["message"] == "Invalid input provided"
        assert result["error"]["retry_after"] is None

    def test_format_error_with_retry(self):
        """Test formatting error response with retry"""
        result = AgentResponseFormatter.format_error(
            request_id="req-123",
            error_code="RATE_LIMITED",
            error_message="Too many requests",
            retry_after=60
        )
        
        assert result["error"]["retry_after"] == 60

    def test_format_stream_chunk(self):
        """Test formatting stream chunk"""
        result = AgentResponseFormatter.format_stream_chunk(
            request_id="req-123",
            chunk="Hello",
            is_final=False
        )
        
        assert result["request_id"] == "req-123"
        assert result["type"] == "stream_chunk"
        assert result["chunk"] == "Hello"
        assert result["is_final"] is False

    def test_format_stream_chunk_final(self):
        """Test formatting final stream chunk"""
        result = AgentResponseFormatter.format_stream_chunk(
            request_id="req-123",
            chunk="",
            is_final=True
        )
        
        assert result["is_final"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
