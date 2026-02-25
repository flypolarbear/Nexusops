"""
NexusOps Gateway - Executor Module

MK-007: Gateway 插件执行边界
"""

from app.gateway.executor.base import (
    ExecutorType,
    ExecutorContext,
    ExecutorRequest,
    ExecutorResult,
    BaseExecutor,
)
from app.gateway.executor.builtin import BuiltinExecutor
from app.gateway.executor.remote import RemoteExecutor
from app.gateway.executor.router import ExecutorRouter

__all__ = [
    "ExecutorType",
    "ExecutorContext",
    "ExecutorRequest",
    "ExecutorResult",
    "BaseExecutor",
    "BuiltinExecutor",
    "RemoteExecutor",
    "ExecutorRouter",
]
