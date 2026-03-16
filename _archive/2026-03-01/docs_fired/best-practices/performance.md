# Performance Best Practices

## Overview

This document covers performance optimization strategies for NexusOps agents. Following these guidelines ensures your agents are fast, efficient, and scalable.

---

## Asynchronous Processing

### Use Async I/O

Always use async for I/O-bound operations:

```python
import asyncio
import httpx

# Good: Async I/O
async def fetch_data(urls: list[str]) -> list[dict]:
    async with httpx.AsyncClient() as client:
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]

# Bad: Blocking I/O
def fetch_data_sync(urls: list[str]) -> list[dict]:
    results = []
    for url in urls:
        response = requests.get(url)  # Blocks!
        results.append(response.json())
    return results
```

### Concurrent Operations

Run independent operations concurrently:

```python
async def handle(self, request: ExecutorRequest) -> ExecutorResult:
    # Run multiple operations concurrently
    results = await asyncio.gather(
        self._fetch_deployment_status(),
        self._fetch_logs(),
        self._fetch_metrics()
    )

    status, logs, metrics = results

    return self._success(
        text=self._format_response(status, logs, metrics)
    )
```

### Connection Pooling

Reuse HTTP connections:

```python
import httpx

class MyAgentHandler(BaseAgentHandler):
    def __init__(self):
        # Shared client with connection pooling
        self._client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20,
                keepalive_expiry=30.0
            )
        )

    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        response = await self._client.get("https://api.example.com/data")
        return self._success(text=response.text)
```

---

## Caching

### Response Caching

Cache expensive computations:

```python
import hashlib
from functools import lru_cache

class CachedAgentHandler(BaseAgentHandler):
    def __init__(self):
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes

    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        # Check cache first
        cache_key = self._build_cache_key(request)

        cached = await self._get_cached(cache_key)
        if cached:
            cached.metadata["cache_hit"] = True
            return cached

        # Process and cache
        result = await self._process(request)
        await self._set_cached(cache_key, result)
        return result

    def _build_cache_key(self, request: ExecutorRequest) -> str:
        key_data = f"{request.query}:{request.request_context}"
        return hashlib.md5(key_data.encode()).hexdigest()

    async def _get_cached(self, key: str) -> Optional[ExecutorResult]:
        # Check Redis or in-memory cache
        pass

    async def _set_cached(self, key: str, result: ExecutorResult):
        # Store in Redis or in-memory cache
        pass
```

### Redis Caching

```python
import redis.asyncio as redis
import json

class RedisCache:
    def __init__(self, url: str):
        self._redis = redis.from_url(url)

    async def get(self, key: str) -> Optional[dict]:
        data = await self._redis.get(key)
        return json.loads(data) if data else None

    async def set(self, key: str, value: dict, ttl: int = 300):
        await self._redis.setex(key, ttl, json.dumps(value))

    async def delete(self, key: str):
        await self._redis.delete(key)

# Usage in agent
class CachedHandler(BaseAgentHandler):
    def __init__(self, cache: RedisCache):
        self._cache = cache

    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        cache_key = f"agent:{self.agent_id}:{hash(request.query)}"

        # Try cache
        cached = await self._cache.get(cache_key)
        if cached:
            return ExecutorResult(**cached)

        # Process
        result = await self._process(request)

        # Cache result
        await self._cache.set(cache_key, result.model_dump())

        return result
```

---

## Database Optimization

### Connection Pooling

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)

async def get_session() -> AsyncSession:
    async with AsyncSession(engine) as session:
        yield session
```

### Query Optimization

```python
# Good: Select only needed columns
async def get_deployment(session: AsyncSession, deployment_id: str):
    result = await session.execute(
        select(Deployment.id, Deployment.status, Deployment.version)
        .where(Deployment.id == deployment_id)
    )
    return result.scalar_one()

# Bad: Select all columns
async def get_deployment_slow(session: AsyncSession, deployment_id: str):
    result = await session.execute(
        select(Deployment).where(Deployment.id == deployment_id)
    )
    return result.scalar_one()
```

### Batch Operations

```python
# Good: Batch insert
async def batch_insert(session: AsyncSession, items: list[dict]):
    session.add_all([Item(**item) for item in items])
    await session.commit()

# Bad: Individual inserts
async def individual_inserts(session: AsyncSession, items: list[dict]):
    for item in items:
        session.add(Item(**item))
        await session.commit()  # N commits!
```

---

## Memory Management

### Generator Patterns

Use generators for large datasets:

```python
# Good: Generator (memory efficient)
async def stream_logs(deployment_id: str):
    async for log in fetch_logs_batch(deployment_id, batch_size=100):
        yield log

async def handle(self, request: ExecutorRequest) -> ExecutorResult:
    logs = []
    async for log in stream_logs(request.context.get("deployment_id")):
        logs.append(log)
        if len(logs) >= 1000:  # Limit memory
            break

    return self._success(text=format_logs(logs))

# Bad: Load all into memory
async def get_all_logs(deployment_id: str):
    all_logs = []
    while True:
        batch = await fetch_logs_batch(deployment_id)
        if not batch:
            break
        all_logs.extend(batch)  # Could OOM!
    return all_logs
```

### Resource Cleanup

```python
async def handle(self, request: ExecutorRequest) -> ExecutorResult:
    conn = None
    try:
        conn = await get_connection()
        result = await self._process(conn, request)
        return result
    finally:
        if conn:
            await conn.close()
```

---

## Timeout Management

### Set Appropriate Timeouts

```python
import httpx

# Configure timeouts
client = httpx.AsyncClient(
    timeout=httpx.Timeout(
        connect=5.0,    # Connection timeout
        read=30.0,      # Read timeout
        write=10.0,     # Write timeout
        pool=5.0        # Pool wait timeout
    )
)

# Per-request timeout
async def fetch_with_timeout(url: str):
    try:
        response = await client.get(url, timeout=10.0)
        return response.json()
    except httpx.TimeoutException:
        return None
```

### Overall Request Timeout

```python
import asyncio

async def handle_with_timeout(self, request: ExecutorRequest) -> ExecutorResult:
    try:
        # Set overall timeout for the handler
        return await asyncio.wait_for(
            self._process(request),
            timeout=30.0
        )
    except asyncio.TimeoutError:
        return self._error(
            code="EXEC_TIMEOUT",
            message="Request timed out",
            retry_after=5
        )
```

---

## Circuit Breaker

### Implementation

```python
from datetime import datetime, timedelta
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 30
    ):
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
                raise Exception("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        if not self.last_failure_time:
            return True
        return datetime.utcnow() - self.last_failure_time > timedelta(
            seconds=self.recovery_timeout
        )

    def _on_success(self):
        self.failures = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        self.failures += 1
        self.last_failure_time = datetime.utcnow()
        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN

# Usage
breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=30)

async def safe_external_call():
    return await breaker.call(external_api_call, param1, param2)
```

---

## Batching and Throttling

### Request Batching

```python
from collections import defaultdict
import asyncio

class BatchProcessor:
    def __init__(self, batch_size: int = 100, flush_interval: float = 1.0):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._batch = defaultdict(list)
        self._lock = asyncio.Lock()
        self._flush_task = None

    async def add(self, key: str, item: dict):
        async with self._lock:
            self._batch[key].append(item)

            if len(self._batch[key]) >= self.batch_size:
                await self._flush(key)

    async def _flush(self, key: str):
        items = self._batch.pop(key, [])
        if items:
            await self._process_batch(key, items)

    async def _process_batch(self, key: str, items: list[dict]):
        # Process batch
        pass
```

### Rate Limiting

```python
from asyncio import Semaphore

class RateLimiter:
    def __init__(self, rate: int, period: float = 1.0):
        self.rate = rate
        self.period = period
        self._semaphore = Semaphore(rate)
        self._tokens = rate
        self._last_update = time.time()

    async def acquire(self):
        await self._semaphore.acquire()
        self._refill()

    def _refill(self):
        now = time.time()
        elapsed = now - self._last_update
        tokens_to_add = int(elapsed / self.period * self.rate)

        if tokens_to_add > 0:
            self._tokens = min(self.rate, self._tokens + tokens_to_add)
            self._last_update = now

# Usage
limiter = RateLimiter(rate=100, period=1.0)

async def rate_limited_request(url: str):
    async with limiter:
        return await client.get(url)
```

---

## Monitoring and Metrics

### Latency Tracking

```python
import time
import structlog

logger = structlog.get_logger()

async def track_latency(operation: str):
    start = time.time()
    try:
        yield
    finally:
        latency_ms = (time.time() - start) * 1000
        logger.info(
            "operation_complete",
            operation=operation,
            latency_ms=round(latency_ms, 2)
        )

# Usage
async def handle(self, request: ExecutorRequest) -> ExecutorResult:
    async with track_latency("handle_request"):
        return await self._process(request)
```

### Performance Metrics

```python
from prometheus_client import Histogram, Counter

REQUEST_LATENCY = Histogram(
    "agent_request_latency_seconds",
    "Request latency in seconds",
    ["agent_id", "status"]
)

REQUEST_COUNT = Counter(
    "agent_requests_total",
    "Total requests",
    ["agent_id", "status"]
)

class MonitoredHandler(BaseAgentHandler):
    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        start = time.time()

        try:
            result = await self._process(request)
            status = "success" if result.success else "error"
            return result
        finally:
            latency = time.time() - start
            REQUEST_LATENCY.labels(
                agent_id=self.agent_id,
                status=status
            ).observe(latency)
            REQUEST_COUNT.labels(
                agent_id=self.agent_id,
                status=status
            ).inc()
```

---

## Performance Checklist

### Development

- [ ] Use async I/O for all external calls
- [ ] Set appropriate timeouts
- [ ] Implement caching for repeated queries
- [ ] Use connection pooling
- [ ] Process concurrently when possible

### Testing

- [ ] Load test with expected traffic
- [ ] Test with slow/timeout responses
- [ ] Monitor memory usage under load
- [ ] Verify cache hit rates

### Production

- [ ] Enable metrics collection
- [ ] Set up latency alerts
- [ ] Configure circuit breakers
- [ ] Implement rate limiting
- [ ] Regular performance reviews

---

## Next Steps

- [Security Best Practices](./security.md) - Security guidelines
- [Troubleshooting](./troubleshooting.md) - Debug performance issues
- [Agent Lifecycle](../agent-development/agent-lifecycle.md) - Lifecycle management
