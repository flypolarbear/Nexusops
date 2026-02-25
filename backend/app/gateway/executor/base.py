"""
NexusOps Gateway - Executor Base

MK-007: Executor 抽象基类

Defines the abstract interface for all executors.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Literal
from enum import Enum
from pydantic import BaseModel, Field


class ExecutorType(str, Enum):
    """Executor type enumeration"""
    BUILTIN = "builtin"
    REMOTE = "remote"
    MOCK = "mock"


class ExecutorContext(BaseModel):
    """Execution context"""
    trace_id: str
    request_id: str
    agent_id: str
    agent_version: str = "1.0.0"
    agent_type: ExecutorType = ExecutorType.BUILTIN
    endpoint: Optional[str] = None
    timeout_ms: int = 30000
    retry_config: Optional[Dict[str, Any]] = None
    auth_context: Optional[Dict[str, Any]] = None


class ExecutorRequest(BaseModel):
    """Execution request"""
    context: ExecutorContext
    query: str
    request_context: Dict[str, Any] = Field(default_factory=dict)
    output_config: Optional[Dict[str, Any]] = None
    tools: Optional[List[Dict[str, Any]]] = None


class ExecutorResult(BaseModel):
    """Execution result"""
    success: bool
    content: Dict[str, Any]
    structured_output: Optional[Any] = None
    suggested_actions: List[Dict[str, Any]] = Field(default_factory=list)
    related_resources: List[Dict[str, Any]] = Field(default_factory=list)
    tool_calls: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[Dict[str, Any]] = None

    class Config:
        arbitrary_types_allowed = True


class BaseExecutor(ABC):
    """
    Executor abstract base class.

    All executors (builtin, remote, mock) must implement this interface.
    """

    @property
    @abstractmethod
    def executor_type(self) -> ExecutorType:
        """Return the executor type"""
        pass

    @abstractmethod
    async def execute(self, request: ExecutorRequest) -> ExecutorResult:
        """
        Execute an agent invocation.

        Args:
            request: The execution request

        Returns:
            ExecutorResult with success/failure status and content
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the executor is healthy.

        Returns:
            True if healthy, False otherwise
        """
        pass

    async def pre_execute(self, request: ExecutorRequest) -> Optional[ExecutorResult]:
        """
        Pre-execution hook.

        Override to add logic before execution (e.g., caching, validation).

        Args:
            request: The execution request

        Returns:
            ExecutorResult to short-circuit execution, or None to continue
        """
        return None

    async def post_execute(
        self,
        request: ExecutorRequest,
        result: ExecutorResult,
    ) -> ExecutorResult:
        """
        Post-execution hook.

        Override to modify results (e.g., logging, transformation).

        Args:
            request: The execution request
            result: The execution result

        Returns:
            Modified ExecutorResult
        """
        return result

    def _make_success_result(
        self,
        text: str,
        format: str = "markdown",
        structured_output: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutorResult:
        """Helper to create a success result"""
        return ExecutorResult(
            success=True,
            content={"text": text, "format": format},
            structured_output=structured_output,
            metadata=metadata or {},
        )

    def _make_error_result(
        self,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None,
    ) -> ExecutorResult:
        """Helper to create an error result"""
        return ExecutorResult(
            success=False,
            content={"text": message, "format": "plain"},
            error={
                "code": code,
                "message": message,
                "details": details,
                "retry_after": retry_after,
            },
        )
