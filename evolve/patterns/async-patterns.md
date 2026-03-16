# 异步处理模式

## 问题描述

所有 I/O 操作必须使用 async/await，避免阻塞事件循环。

## 解决方案

### 异步 I/O

```python
import httpx
import asyncio

# ✅ 推荐: 异步并发
async def fetch_multiple(urls: list[str]) -> list[dict]:
    async with httpx.AsyncClient() as client:
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]

# ❌ 避免: 阻塞调用
def fetch_sync(urls: list[str]) -> list[dict]:
    results = []
    for url in urls:
        response = requests.get(url)  # 阻塞!
        results.append(response.json())
    return results
```

### 并发执行

```python
async def handle(self, request: ExecutorRequest) -> ExecutorResult:
    # 并发执行多个独立操作
    results = await asyncio.gather(
        self._fetch_status(),
        self._fetch_logs(),
        self._fetch_metrics(),
        return_exceptions=True  # 异常不中断其他任务
    )
    
    status, logs, metrics = results
    return self._success(text=self._format(status, logs, metrics))
```

### 超时控制

```python
import asyncio

async def fetch_with_timeout(url: str, timeout: float = 10.0):
    try:
        return await asyncio.wait_for(
            _fetch_internal(url),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        raise ExecError(code="EXEC_TIMEOUT", message=f"Timeout after {timeout}s")

# 在 handler 中使用
async def handle(self, request: ExecutorRequest) -> ExecutorResult:
    try:
        return await asyncio.wait_for(
            self._process(request),
            timeout=30.0
        )
    except asyncio.TimeoutError:
        return self._error(code="EXEC_TIMEOUT", message="Request timed out", retry_after=5)
```

## 注意事项

- ✅ 所有数据库操作使用 async session
- ✅ 所有 HTTP 调用使用 httpx.AsyncClient
- ✅ 设置合理的超时时间
- ❌ 不要在 async 函数中使用 time.sleep()，用 asyncio.sleep()
- ❌ 不要使用同步库（如 requests）
