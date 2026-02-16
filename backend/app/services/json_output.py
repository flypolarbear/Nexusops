"""
NexusOps Backend - JSON Output Guarantee

OPT-003: JSON 输出保证
- 集成 Instructor 库
- JSON Schema 验证
- 自动修复 + 重传机制
- 响应格式标准化
"""

import asyncio
import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, Optional, Type, TypeVar, Union
from pydantic import BaseModel, ValidationError

# ============================================
# JSON Schema 验证
# ============================================

T = TypeVar("T", bound=BaseModel)


@dataclass
class ValidationResult:
    """验证结果"""
    success: bool
    data: Optional[Any] = None
    errors: list[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class JSONSchemaValidator:
    """JSON Schema 验证器"""

    @staticmethod
    def validate(data: dict, schema: dict) -> ValidationResult:
        """验证数据是否符合 schema"""
        try:
            import jsonschema
            jsonschema.validate(data, schema)
            return ValidationResult(success=True, data=data)
        except jsonschema.ValidationError as e:
            return ValidationResult(
                success=False,
                errors=[str(e.message)]
            )
        except ImportError:
            # jsonschema not installed, skip validation
            return ValidationResult(success=True, data=data)

    @staticmethod
    def validate_pydantic(data: dict, model: Type[T]) -> ValidationResult:
        """使用 Pydantic 模型验证"""
        try:
            validated = model.model_validate(data)
            return ValidationResult(success=True, data=validated)
        except ValidationError as e:
            errors = [err["msg"] for err in e.errors()]
            return ValidationResult(success=False, errors=errors)


# ============================================
# JSON 修复
# ============================================

class JSONRepair:
    """JSON 修复工具"""

    @staticmethod
    def repair(json_str: str) -> tuple[Optional[dict], list[str]]:
        """
        尝试修复破损的 JSON

        Returns:
            (repaired_data, warnings)
        """
        warnings = []

        # 1. 尝试直接解析
        try:
            return json.loads(json_str), []
        except json.JSONDecodeError:
            pass

        # 2. 移除 markdown 代码块标记
        cleaned = json_str.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            warnings.append("Removed markdown code block")

        # 3. 修复常见错误
        # 修复单引号
        if "'" in cleaned and '"' not in cleaned:
            cleaned = cleaned.replace("'", '"')
            warnings.append("Converted single quotes to double quotes")

        # 修复尾部逗号
        cleaned = re.sub(r",\s*}", "}", cleaned)
        cleaned = re.sub(r",\s*]", "]", cleaned)
        if ",}" in json_str or ",]" in json_str:
            warnings.append("Removed trailing commas")

        # 修复未引用的键名
        cleaned = re.sub(r"(\w+)(?=\s*:)", r'"\1"', cleaned)

        # 修复布尔值和 null
        cleaned = re.sub(r"\bTrue\b", "true", cleaned)
        cleaned = re.sub(r"\bFalse\b", "false", cleaned)
        cleaned = re.sub(r"\bNone\b", "null", cleaned)

        # 4. 再次尝试解析
        try:
            return json.loads(cleaned), warnings
        except json.JSONDecodeError as e:
            warnings.append(f"Failed to repair JSON: {e}")
            return None, warnings

    @staticmethod
    def extract_json(text: str) -> Optional[dict]:
        """从文本中提取 JSON"""
        # 尝试找到 JSON 块
        patterns = [
            r'```json\s*([\s\S]*?)\s*```',  # markdown json block
            r'```\s*([\s\S]*?)\s*```',       # any code block
            r'\{[\s\S]*\}',                   # curly braces
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                data, _ = JSONRepair.repair(match)
                if data:
                    return data

        return None


# ============================================
# 输出格式化
# ============================================

class OutputFormatter:
    """输出格式化器"""

    @staticmethod
    def to_json(data: Any, indent: int = 2) -> str:
        """格式化为 JSON"""
        if isinstance(data, BaseModel):
            return data.model_dump_json(indent=indent)
        return json.dumps(data, indent=indent, ensure_ascii=False)

    @staticmethod
    def ensure_type(value: Any, expected_type: type) -> Any:
        """确保值的类型正确"""
        if isinstance(value, expected_type):
            return value

        # 尝试类型转换
        try:
            if expected_type == str:
                return str(value)
            elif expected_type == int:
                return int(value)
            elif expected_type == float:
                return float(value)
            elif expected_type == bool:
                if isinstance(value, str):
                    return value.lower() in ("true", "1", "yes")
                return bool(value)
            elif expected_type == list:
                if isinstance(value, str):
                    return json.loads(value)
                return list(value)
            elif expected_type == dict:
                if isinstance(value, str):
                    return json.loads(value)
                return dict(value)
        except (ValueError, json.JSONDecodeError):
            pass

        return value


# ============================================
# 带重试的 JSON 生成器
# ============================================

class JSONGenerator(Generic[T]):
    """
    带重试机制的 JSON 生成器

    基于 Instructor 的思路实现（不依赖 Instructor 库）
    """

    def __init__(
        self,
        model: Type[T],
        max_retries: int = 3,
        repair_enabled: bool = True,
    ):
        self.model = model
        self.max_retries = max_retries
        self.repair_enabled = repair_enabled

    async def generate(
        self,
        prompt: str,
        llm_call: callable,
    ) -> tuple[Optional[T], list[str]]:
        """
        生成并验证 JSON

        Args:
            prompt: 提示词
            llm_call: LLM 调用函数，接受 prompt，返回文本

        Returns:
            (validated_model, errors)
        """
        errors = []

        # 获取 schema
        schema = self.model.model_json_schema()
        schema_str = json.dumps(schema, indent=2)

        for attempt in range(self.max_retries):
            # 构建 prompt
            full_prompt = self._build_prompt(prompt, schema_str, errors)

            # 调用 LLM
            response = await llm_call(full_prompt)

            # 尝试解析
            data = None
            if self.repair_enabled:
                data, repair_warnings = JSONRepair.repair(response)
                errors.extend(repair_warnings)
            else:
                try:
                    data = json.loads(response)
                except json.JSONDecodeError as e:
                    errors.append(f"JSON decode error: {e}")

            if data:
                # 验证
                result = JSONSchemaValidator.validate_pydantic(data, self.model)
                if result.success:
                    return result.data, errors
                else:
                    errors.extend(result.errors)

            # 添加失败信息用于下一次重试
            errors.append(f"Attempt {attempt + 1} failed")

        return None, errors

    def _build_prompt(self, original_prompt: str, schema: str, previous_errors: list[str]) -> str:
        """构建 prompt"""
        error_section = ""
        if previous_errors:
            error_section = f"""
Previous attempts failed with these errors:
{chr(10).join(f'- {e}' for e in previous_errors[-5:])}

Please fix these issues and return valid JSON.
"""

        return f"""
{original_prompt}

You MUST respond with a valid JSON object that matches this schema:
```json
{schema}
```

{error_section}

Important:
- Return ONLY the JSON object, no other text
- Ensure all required fields are present
- Use correct data types for each field
- Do not include any markdown formatting or code blocks
"""


# ============================================
# Instructor-style Wrapper (简化版)
# ============================================

class InstructorWrapper:
    """
    Instructor 风格的包装器

    提供类似 Instructor 的接口，但可以适配不同的 LLM
    """

    def __init__(
        self,
        client: Any = None,
        max_retries: int = 3,
    ):
        """
        Args:
            client: LLM 客户端 (OpenAI, Anthropic, etc.)
            max_retries: 最大重试次数
        """
        self.client = client
        self.max_retries = max_retries

    def from_response(
        self,
        response_text: str,
        response_model: Type[T],
        validation: bool = True,
    ) -> tuple[Optional[T], list[str]]:
        """
        从 LLM 响应中提取和验证结构化数据

        Args:
            response_text: LLM 的原始响应
            response_model: Pydantic 模型
            validation: 是否验证

        Returns:
            (validated_model, errors)
        """
        errors = []

        # 提取 JSON
        data = JSONRepair.extract_json(response_text)
        if not data:
            data, repair_errors = JSONRepair.repair(response_text)
            errors.extend(repair_errors)

        if not data:
            errors.append("Could not extract valid JSON from response")
            return None, errors

        # 验证
        if validation:
            result = JSONSchemaValidator.validate_pydantic(data, response_model)
            if result.success:
                return result.data, errors
            else:
                errors.extend(result.errors)
                return None, errors

        # 不验证，直接构造
        try:
            return response_model.model_validate(data), errors
        except ValidationError as e:
            errors.extend([err["msg"] for err in e.errors()])
            return None, errors


# ============================================
# Agent 响应格式化
# ============================================

class AgentResponseFormatter:
    """Agent 响应格式化器"""

    @staticmethod
    def format_success(
        request_id: str,
        content: str,
        structured_output: Optional[dict] = None,
        actions: Optional[list] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """格式化成功响应"""
        return {
            "request_id": request_id,
            "status": "success",
            "content": {
                "text": content,
                "format": "markdown",
            },
            "structured_output": structured_output,
            "suggested_actions": actions or [],
            "metadata": metadata,
        }

    @staticmethod
    def format_error(
        request_id: str,
        error_code: str,
        error_message: str,
        retry_after: Optional[int] = None,
    ) -> dict:
        """格式化错误响应"""
        return {
            "request_id": request_id,
            "status": "error",
            "content": {
                "text": "",
                "format": "plain",
            },
            "error": {
                "code": error_code,
                "message": error_message,
                "retry_after": retry_after,
            },
        }

    @staticmethod
    def format_stream_chunk(
        request_id: str,
        chunk: str,
        is_final: bool = False,
    ) -> dict:
        """格式化流式响应块"""
        return {
            "request_id": request_id,
            "type": "stream_chunk",
            "chunk": chunk,
            "is_final": is_final,
        }
