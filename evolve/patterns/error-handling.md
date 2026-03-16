# 错误处理模式

## 问题描述

需要统一、可追溯的错误处理方式。

## 解决方案

### 使用 Helper 方法

```python
class MyAgentHandler(BaseAgentHandler):
    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        # 验证输入
        if not request.query:
            return self._error(
                code="INPUT_MISSING_FIELD",
                message="Query cannot be empty",
                details={"field": "query"}
            )

        # 检查权限
        if not self._check_permission(request.request_context):
            return self._error(
                code="AUTH_PERMISSION_DENIED",
                message="Permission denied",
                details={"required_role": "admin"}
            )

        # 处理请求
        try:
            result = await self._process(request.query)
            return self._success(text=result)
        except ExternalServiceError as e:
            return self._error(
                code="EXEC_DOWNSTREAM_ERROR",
                message=f"External service error: {e}",
                details={"service": "external-api"},
                retry_after=10
            )
```

### 提供可操作的详情

```python
# ✅ 好: 包含有用的上下文
return self._error(
    code="INPUT_SCHEMA_VIOLATION",
    message="Invalid date format",
    details={
        "field": "date",
        "expected_format": "YYYY-MM-DD",
        "actual_value": "25/02/2026",
        "example": "2026-02-25"
    }
)

# ✅ 好: 包含可用选项
return self._error(
    code="AGENT_NOT_FOUND",
    message="Agent not found: third-party.analytics",
    details={
        "agent_id": "third-party.analytics",
        "suggestion": "Check if the agent is installed",
        "available_agents": ["nexusops.chat", "nexusops.k8s"]
    }
)

# ✅ 好: 包含重试指导
return self._error(
    code="EXEC_TIMEOUT",
    message="Request timed out after 30 seconds",
    details={
        "timeout_ms": 30000,
        "suggestion": "Try reducing the scope of your query"
    },
    retry_after=5
)
```

### 熔断器模式

```python
from datetime import datetime, timedelta
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None

    async def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise ExecError(
                    code="EXEC_CIRCUIT_OPEN",
                    message="Circuit breaker is open",
                    retry_after=self._remaining_recovery_time()
                )

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise
```

## 错误码分类

| 类别 | 前缀 | HTTP 状态码 |
|------|------|-------------|
| Input | INPUT_ | 400 |
| Auth | AUTH_ | 401/403/429 |
| Agent | AGENT_ | 404/409/422 |
| Exec | EXEC_ | 500/502/504 |
| System | SYSTEM_ | 500/503 |

## 注意事项

- ✅ 使用具体的错误码
- ✅ 包含可操作的详情
- ✅ 为可重试错误设置 retry_after
- ✅ 记录带 trace_id 的日志
- ❌ 不要暴露内部实现细节
- ❌ 不要使用通用错误消息
