# Architecture Overview

## Overview

NexusOps is a multi-agent operations platform built on a modular, extensible architecture. This document provides a comprehensive overview of the system architecture, component interactions, and design decisions.

---

## High-Level Architecture

```
+------------------------------------------------------------------+
|                          Frontend (React)                         |
|  +------------------------------------------------------------+  |
|  |                    UI Components                           |  |
|  |  - Dashboard  - Agent Chat  - Deployments  - Logs         |  |
|  +------------------------------------------------------------+  |
+------------------------------------------------------------------+
                              |
                              | HTTP/WebSocket
                              v
+------------------------------------------------------------------+
|                    API Layer (FastAPI)                           |
|  +------------------------------------------------------------+  |
|  |                    REST Endpoints                          |  |
|  |  /api/v1/agents/*  /api/v1/projects/*  /api/v1/auth/*     |  |
|  +------------------------------------------------------------+  |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|                    Gateway Core                                  |
|  +------------------------------------------------------------+  |
|  |  Middleware Chain                                          |  |
|  |  - TraceMiddleware - AuthMiddleware - SchemaMiddleware     |  |
|  +------------------------------------------------------------+  |
|                              |                                   |
|                              v                                   |
|  +------------------------------------------------------------+  |
|  |                   ExecutorRouter                           |  |
|  |  - Route to BuiltinExecutor or RemoteExecutor              |  |
|  +------------------------------------------------------------+  |
+------------------------------------------------------------------+
              |                                    |
              v                                    v
+---------------------------+    +-----------------------------------+
|    BuiltinExecutor        |    |       RemoteExecutor              |
|  +---------------------+  |    |  +-----------------------------+  |
|  |  Internal Agents    |  |    |  |  Third-Party Agent Adapters |  |
|  |  - nexusops.chat    |  |    |  |  - HTTP/gRPC Clients        |  |
|  |  - nexusops.k8s     |  |    |  +-----------------------------+  |
|  |  - nexusops.deploy  |  |    +-----------------------------------+
|  |  - nexusops.dns     |  |
|  |  - nexusops.logs    |  |
|  |  - nexusops.cost    |  |
|  +---------------------+  |
+---------------------------+
```

---

## Core Components

### 1. API Layer

The API Layer handles HTTP requests and responses, providing RESTful endpoints for all operations.

**Location**: `backend/app/api/`

**Key Files**:
- `agents.py` - Agent invocation and management endpoints
- `agent_market.py` - Agent marketplace endpoints
- `auth.py` - Authentication and authorization

**Responsibilities**:
- Request parsing and validation
- Response formatting
- Authentication/Authorization integration
- API versioning

### 2. Gateway Core

The Gateway Core orchestrates request processing through middleware chains and routes requests to appropriate executors.

**Location**: `backend/app/gateway/`

**Key Components**:

| Component | File | Purpose |
|-----------|------|---------|
| Contract | `contract.py` | Request/Response data models |
| Errors | `errors.py` | Error codes and exceptions |
| Validator | `validator.py` | JSON Schema validation |
| Trace | `trace.py` | Trace ID generation and propagation |
| Response | `response.py` | Response building utilities |

### 3. Middleware Chain

The middleware chain processes requests before they reach the executor.

```
Request -> TraceMiddleware -> AuthMiddleware -> SchemaMiddleware -> RateLimitMiddleware -> Executor
```

| Middleware | Purpose |
|------------|---------|
| TraceMiddleware | Generate and propagate trace_id |
| AuthMiddleware | Validate authentication tokens |
| SchemaMiddleware | Validate request against JSON Schema |
| RateLimitMiddleware | Enforce rate limits |
| AuditMiddleware | Log audit events |

### 4. Executor Layer

The Executor Layer provides a unified interface for executing both built-in and remote agents.

**Location**: `backend/app/gateway/executor/`

**Architecture**:

```
+-------------------+
|  ExecutorRouter   |
+---------+---------+
          |
          +------------------+------------------+
          |                  |                  |
          v                  v                  v
+----------------+  +----------------+  +----------------+
| BuiltinExecutor|  | RemoteExecutor |  | MockExecutor   |
| (Internal)     |  | (Third-Party)  |  | (Testing)      |
+----------------+  +----------------+  +----------------+
```

**Base Interface**:

```python
class BaseExecutor(ABC):
    @property
    @abstractmethod
    def executor_type(self) -> ExecutorType:
        pass

    @abstractmethod
    async def execute(self, request: ExecutorRequest) -> ExecutorResult:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass

    async def pre_execute(self, request: ExecutorRequest) -> Optional[ExecutorResult]:
        return None

    async def post_execute(self, request: ExecutorRequest, result: ExecutorResult) -> ExecutorResult:
        return result
```

### 5. Agent Handlers

Agent Handlers contain the business logic for built-in agents.

**Location**: `backend/app/agents/`

**Built-in Agents**:

| Agent ID | File | Capabilities |
|----------|------|--------------|
| `nexusops.chat` | `chat.py` | General chat, quick commands |
| `nexusops.k8s` | `k8s.py` | Kubernetes operations |
| `nexusops.deploy` | `deploy.py` | Deployment management |
| `nexusops.dns` | `dns.py` | DNS management |
| `nexusops.logs` | `logs.py` | Log aggregation and querying |
| `nexusops.cost` | `cost.py` | Cost analysis |

---

## Data Flow

### Request Processing Flow

```
1. Client Request
   |
   v
2. API Layer (FastAPI)
   | - Parse request
   | - Extract headers
   v
3. Middleware Chain
   | - Generate trace_id
   | - Validate auth
   | - Validate schema
   v
4. Gateway Core
   | - Build ExecutorRequest
   | - Call ExecutorRouter
   v
5. ExecutorRouter
   | - Resolve agent
   | - Select executor
   v
6. Executor
   | - pre_execute hook
   | - execute
   | - post_execute hook
   v
7. Agent Handler (for built-in)
   | - Process query
   | - Call external services
   | - Build result
   v
8. Response Building
   | - Convert to InvokeResponse
   | - Add metadata
   v
9. Client Response
```

### Trace ID Propagation

The trace_id is generated at the Gateway entry point and propagated through all layers:

```
Gateway Entry
    |
    +-- X-Trace-ID header
    |
    +-- ExecutorContext.trace_id
    |       |
    |       +-- Agent Handler
    |       |
    |       +-- External API calls (X-Trace-ID)
    |
    +-- Database records (trace_id column)
    |
    +-- Log entries (trace_id field)
```

---

## Design Decisions

### ADR-001: FastAPI Monolithic Kernel + Pluggable Executor Layer

**Context**: Need to balance development velocity with future scalability.

**Decision**: Start with a FastAPI monolith but design the executor layer as a pluggable interface.

**Consequences**:
- (+) Fast initial development
- (+) Easy to test
- (+) Clear boundaries for future extraction
- (-) Single deployment unit initially

**Extraction Trigger Conditions**:
- Throughput > 10,000 QPS
- Independent scaling needed
- Physical tenant isolation required

### ADR-002: Unified Invoke API Contract

**Context**: Need a consistent interface for all agents (built-in and third-party).

**Decision**: Define a single Invoke API contract (MK-006) used by all agents.

**Consequences**:
- (+) Consistent client experience
- (+) Easy to add new agents
- (+) Simplified testing
- (-) May need extension points for agent-specific features

### ADR-003: Error Code Taxonomy

**Context**: Need standardized error handling across the system.

**Decision**: Use a hierarchical error code system: `{CATEGORY}_{SUBCATEGORY}_{SPECIFIC}`

**Categories**:
- `INPUT_*` - Client input errors (HTTP 400)
- `AUTH_*` - Authentication/Authorization errors (HTTP 401/403)
- `AGENT_*` - Agent-specific errors (HTTP 404/409/422)
- `EXEC_*` - Execution errors (HTTP 500/502/504)
- `SYSTEM_*` - System errors (HTTP 500/503)

---

## Directory Structure

```
backend/
+-- app/
|   +-- api/                  # REST API endpoints
|   |   +-- agents.py
|   |   +-- agent_market.py
|   |   +-- auth.py
|   |
|   +-- gateway/              # Gateway core
|   |   +-- contract.py       # Request/Response models
|   |   +-- errors.py         # Error codes
|   |   +-- validator.py      # Schema validation
|   |   +-- trace.py          # Trace handling
|   |   +-- response.py       # Response builders
|   |   +-- middleware/       # Middleware chain
|   |   +-- executor/         # Executor layer
|   |       +-- base.py
|   |       +-- builtin.py
|   |       +-- remote.py
|   |       +-- router.py
|   |
|   +-- agents/               # Built-in agents
|   |   +-- base.py           # BaseAgentHandler
|   |   +-- chat.py
|   |   +-- k8s.py
|   |   +-- deploy.py
|   |   +-- dns.py
|   |   +-- logs.py
|   |   +-- cost.py
|   |
|   +-- stores/               # Data stores
|   |   +-- agent_store.py
|   |
|   +-- models/               # Database models
|   +-- services/             # Business services
|   +-- core/                 # Core utilities
|
+-- tests/                    # Test suite
|   +-- agents/
|   +-- gateway/
|   +-- api/

frontend/
+-- src/
|   +-- components/           # React components
|   +-- pages/                # Page components
|   +-- stores/               # State management
|   +-- services/             # API clients
```

---

## Scalability Considerations

### Horizontal Scaling

```
                    +------------------+
                    |  Load Balancer   |
                    +--------+---------+
                             |
         +-------------------+-------------------+
         |                   |                   |
         v                   v                   v
+----------------+  +----------------+  +----------------+
|  API Server 1  |  |  API Server 2  |  |  API Server N  |
+----------------+  +----------------+  +----------------+
         |                   |                   |
         +-------------------+-------------------+
                             |
                    +--------+---------+
                    |    Database      |
                    |  (PostgreSQL)    |
                    +------------------+
```

### Future Service Extraction

When scaling requires, extract components:

```
+------------------+     +------------------+
|  Gateway Service |     |  Agent Service   |
|  - Middleware    |     |  - BuiltinExec   |
|  - RemoteExec    |     |  - Agent Handlers|
|  - Router        |     |                  |
+--------+---------+     +--------+---------+
         |                        |
         +--------+---------------+
                  |
         gRPC/HTTP
```

---

## Security Model

### Authentication Flow

```
Client                API Gateway              Auth Service
  |                       |                         |
  |-- 1. Login Request ->|                         |
  |                       |-- 2. Validate -------->|
  |                       |<-- 3. JWT Token -------|
  |<-- 4. JWT Token -----|                         |
  |                       |                         |
  |-- 5. API Request --->|                         |
  |    (with Bearer)      |-- 6. Verify JWT ------>|
  |                       |<-- 7. Claims ----------|
  |<-- 8. Response ------|                         |
```

### Authorization Model

- **Project-level permissions**: Users have roles within projects
- **Agent-level permissions**: Some agents require specific permissions
- **Tenant isolation**: Multi-tenant data isolation

---

## Performance Considerations

### Caching Strategy

| Layer | Cache Type | TTL | Example |
|-------|------------|-----|---------|
| API | Response Cache | 60s | Agent manifests |
| Gateway | Result Cache | 300s | Repeated queries |
| Executor | Connection Pool | N/A | HTTP clients |

### Connection Pooling

```python
# RemoteExecutor uses connection pooling
class RemoteExecutor(BaseExecutor):
    def __init__(self):
        self._client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
        )
```

---

## Next Steps

- [Agent Lifecycle](../agent-development/agent-lifecycle.md) - Understand agent lifecycle management
- [Gateway API](../api-reference/gateway-api.md) - Detailed API documentation
- [Security Best Practices](../best-practices/security.md) - Security guidelines
