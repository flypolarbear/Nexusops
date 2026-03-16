# 限流熔断模式

## 问题描述

保护下游服务，防止过载和级联故障。

## 解决方案

### 简单限流器

```python
from datetime import datetime, timedelta
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self.requests = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        now = datetime.utcnow()
        # 清理过期请求
        self.requests[key] = [
            t for t in self.requests[key]
            if now - t < self.window
        ]

        if len(self.requests[key]) >= self.max_requests:
            return False

        self.requests[key].append(now)
        return True

    def retry_after(self, key: str) -> int:
        if not self.requests[key]:
            return 0
        oldest = min(self.requests[key])
        return int((oldest + self.window - datetime.utcnow()).total_seconds())

# 使用
limiter = RateLimiter(max_requests=100, window_seconds=60)

if not limiter.is_allowed(user_id):
    return self._error(
        code="AUTH_QUOTA_EXCEEDED",
        message="Rate limit exceeded",
        retry_after=limiter.retry_after(user_id)
    )
```

### 信号量限流

```python
from asyncio import Semaphore

class ConcurrentLimiter:
    def __init__(self, max_concurrent: int):
        self._semaphore = Semaphore(max_concurrent)

    async def __aenter__(self):
        await self._semaphore.acquire()
        return self

    async def __aexit__(self, *args):
        self._semaphore.release()

# 使用
limiter = ConcurrentLimiter(max_concurrent=10)

async def handle(self, request: ExecutorRequest) -> ExecutorResult:
    async with limiter:
        return await self._process(request)
```

### 熔断器

```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.state = "closed"
        self.last_failure_time = None

    async def call(self, func, *args, **kwargs):
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half_open"
            else:
                raise Exception("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        if not self.last_failure_time:
            return True
        return datetime.utcnow() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)

    def _on_success(self):
        self.failures = 0
        self.state = "closed"

    def _on_failure(self):
        self.failures += 1
        self.last_failure_time = datetime.utcnow()
        if self.failures >= self.failure_threshold:
            self.state = "open"
```

## 注意事项

- ✅ 为所有外部调用设置超时
- ✅ 使用熔断器保护不稳定的服务
- ✅ 在错误响应中包含 retry_after
- ✅ 监控熔断器状态
- ❌ 不要在熔断器打开时继续重试
- ❌ 不要忘记重置成功后的失败计数
