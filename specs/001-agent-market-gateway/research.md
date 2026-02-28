# Research: Agent Market and Gateway

**Feature**: 001-agent-market-gateway
**Date**: 2026-03-01

## Research Summary

This document captures research findings for implementing the Agent Market and Gateway enhancements.

---

## 1. Health Monitoring Patterns

### Decision: Async Background Tasks with FastAPI

**Rationale**: FastAPI's built-in background task system integrates seamlessly with the existing async architecture. No additional infrastructure required.

**Alternatives Considered**:
- **Celery**: Rejected - adds complexity, requires message broker (Redis/RabbitMQ)
- **APScheduler**: Rejected - synchronous by default, less integration with FastAPI
- **Custom Thread Pool**: Rejected - doesn't integrate with async event loop

**Implementation Approach**:
```python
# Use FastAPI lifespan events for health check scheduler
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: begin health check loop
    task = asyncio.create_task(health_check_loop())
    yield
    # Shutdown: cancel health check
    task.cancel()
```

---

## 2. Rate Limiting Strategy

### Decision: Redis-based Sliding Window

**Rationale**: Redis provides distributed rate limiting suitable for multi-instance deployments. Sliding window algorithm provides smoother rate limiting than fixed window.

**Alternatives Considered**:
- **In-memory**: Rejected - doesn't work with multiple backend instances
- **Database-backed**: Rejected - higher latency, more load on PostgreSQL
- **Token Bucket**: Rejected - more complex, sliding window sufficient for our use case

**Implementation Approach**:
```python
# Redis sliding window implementation
async def check_rate_limit(key: str, limit: int, window: int) -> bool:
    now = time.time()
    pipe = redis.pipeline()
    pipe.zremrangebyscore(key, 0, now - window)
    pipe.zadd(key, {str(now): now})
    pipe.zcard(key)
    pipe.expire(key, window)
    results = await pipe.execute()
    return results[2] <= limit
```

---

## 3. Circuit Breaker Pattern

### Decision: Circuit Breaker with Async Support

**Rationale**: Protect the gateway from cascading failures when third-party agents are unavailable. The circuit breaker pattern provides automatic failure detection and recovery.

**Alternatives Considered**:
- **Timeout Only**: Rejected - doesn't prevent cascading failures
- **Retry with Backoff**: Rejected - can make problems worse under load
- **External Service Mesh**: Rejected - adds infrastructure complexity

**Implementation Approach**:
- States: CLOSED (normal), OPEN (failing), HALF_OPEN (testing recovery)
- Failure threshold: 5 consecutive failures
- Recovery timeout: 30 seconds
- Half-open requests: 1 test request

```python
class CircuitBreaker:
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"
    
    async def call(self, func, *args, **kwargs):
        if self.state == self.OPEN:
            if time.time() - self.last_failure > self.recovery_timeout:
                self.state = self.HALF_OPEN
            else:
                raise CircuitOpenError()
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
```

---

## 4. Frontend State Management

### Decision: Zustand with Async Actions

**Rationale**: Zustand provides simple, type-safe state management that works well with async operations. Already used in the project for other stores.

**Alternatives Considered**:
- **Redux Toolkit**: Rejected - more boilerplate, team prefers Zustand
- **React Query Only**: Rejected - need local state for UI interactions
- **Context API**: Rejected - not suitable for complex state

**Implementation Approach**:
```typescript
interface AgentMarketState {
  agents: Agent[]
  loading: boolean
  error: string | null
  searchQuery: string
  selectedCategory: string | null
  
  fetchAgents: () => Promise<void>
  installAgent: (agentId: string) => Promise<void>
  setSearchQuery: (query: string) => void
}
```

---

## 5. WebSocket Streaming Enhancement

### Decision: Server-Sent Events for Streaming

**Rationale**: SSE is simpler than WebSocket for unidirectional streaming (server to client). Better for long-running agent responses.

**Alternatives Considered**:
- **WebSocket**: Already exists but more complex for simple streaming
- **Polling**: Rejected - higher latency, more requests
- **Chunked HTTP**: Rejected - harder to implement cancellation

**Implementation Approach**:
- Use existing WebSocket infrastructure
- Add streaming mode flag to InvokeRequest
- Send incremental chunks with sequence numbers
- Support cancellation via WebSocket message

---

## 6. Existing Codebase Analysis

### What's Already Implemented

| Component | File | Status |
|-----------|------|--------|
| Invoke Contract | `gateway/contract.py` | ✅ Complete |
| Request Validation | `gateway/validator.py` | ✅ Complete |
| Response Formatting | `gateway/response.py` | ✅ Complete |
| Trace ID Management | `gateway/trace.py` | ✅ Complete |
| Error Definitions | `gateway/errors.py` | ✅ Complete |
| Builtin Executor | `gateway/executor/builtin.py` | ✅ Complete |
| Remote Executor | `gateway/executor/remote.py` | ✅ Complete |
| Executor Router | `gateway/executor/router.py` | ✅ Complete |
| Agent Store | `stores/agent_store.py` | ✅ Complete |
| Market API | `api/agent_market.py` | ✅ Complete |
| WebSocket Endpoint | `api/ws_endpoint.py` | ✅ Complete |

### What's Missing

| Component | Priority | Complexity |
|-----------|----------|------------|
| Health Monitoring | P1 | Medium |
| Frontend Store UI | P1 | High |
| Rate Limiting | P2 | Low |
| Circuit Breaker | P2 | Medium |
| Integration Tests | P2 | Medium |

---

## 7. Dependencies

### Backend Dependencies (Already Installed)
- FastAPI 0.100+
- SQLAlchemy 2.0+
- Pydantic v2
- Redis (for rate limiting)

### Frontend Dependencies (Already Installed)
- React 18
- Zustand 4
- Ant Design 5
- TanStack Query 5

### New Dependencies Required
None - all required packages are already in the project.
