# Quickstart: Agent Market and Gateway

**Feature**: 001-agent-market-gateway
**Date**: 2026-03-01

## Prerequisites

- Docker & Docker Compose running
- PostgreSQL database initialized
- Redis running (for rate limiting)
- Backend server running on port 8000
- Frontend server running on port 3000

---

## Quick Start Commands

```bash
# Start infrastructure
cd docker && docker-compose -f docker-compose.middleware.yml up -d

# Start backend
cd backend && uvicorn app.main:app --reload --port 8000

# Start frontend
cd frontend && npm run dev
```

---

## Test Scenarios

### Scenario 1: Invoke Built-in Agent (US1)

**Goal**: Verify K8s diagnostic agent invocation

```bash
# 1. Invoke K8s agent
curl -X POST http://localhost:8000/api/v1/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "test-001",
    "agent_id": "nexusops.k8s",
    "query": "Get pod status for my-app in production namespace",
    "context": {
      "namespace": "production"
    }
  }'

# Expected: Structured response with pod status
# Verify:
# - Response has request_id matching input
# - Response has trace_id
# - Response status is "success" or "error" with details
```

**Success Criteria**:
- Response received within 5 seconds
- Structured response format
- Trace ID present for debugging

---

### Scenario 2: Register Third-party Agent (US2)

**Goal**: Verify agent registration and invocation

```bash
# 1. Register a test agent
curl -X POST http://localhost:8000/api/v1/market \
  -H "Content-Type: application/json" \
  -d '{
    "manifest": {
      "agent_id": "test.example-agent",
      "name": "Example Agent",
      "version": "1.0.0",
      "description": "Test agent for verification",
      "category": "testing",
      "capabilities": ["test"]
    },
    "endpoint": "https://example.com/agent",
    "visibility": "public"
  }'

# Expected: Agent created with 201 status

# 2. Install the agent
curl -X POST http://localhost:8000/api/v1/market/test.example-agent/install

# Expected: Agent installed successfully

# 3. Verify installation
curl http://localhost:8000/api/v1/market/installed

# Expected: List includes test.example-agent
```

**Success Criteria**:
- Registration returns 201
- Install returns success
- Agent appears in installed list

---

### Scenario 3: Browse Agent Store (US3)

**Goal**: Verify store UI functionality

```bash
# 1. List all agents
curl http://localhost:8000/api/v1/market

# 2. Search agents
curl "http://localhost:8000/api/v1/market?query=kubernetes"

# 3. Get agent details
curl http://localhost:8000/api/v1/market/nexusops.k8s

# 4. Frontend test
# Open http://localhost:3000/market
# Verify:
# - Agent cards display correctly
# - Search works
# - Install button functional
```

**Success Criteria**:
- API returns paginated results
- Search filters correctly
- Frontend displays agents

---

### Scenario 4: Health Monitoring (US4)

**Goal**: Verify health status tracking

```bash
# 1. Check agent health
curl http://localhost:8000/api/v1/market/nexusops.k8s/install-status

# Expected: Response includes agent_status and last_heartbeat

# 2. Send heartbeat
curl -X POST http://localhost:8000/api/v1/market/nexusops.k8s/heartbeat

# Expected: Status ok
```

**Success Criteria**:
- Health status returned
- Heartbeat updates timestamp

---

### Scenario 5: Streaming Response (US5)

**Goal**: Verify streaming support

```bash
# Connect to WebSocket
wscat -c ws://localhost:8000/ws

# Send streaming request
{
  "type": "invoke",
  "request_id": "stream-001",
  "agent_id": "nexusops.logs",
  "query": "Stream logs for my-app",
  "streaming": true
}

# Expected: Multiple response chunks
```

**Success Criteria**:
- Chunks received progressively
- Final chunk indicates completion
- Cancellation works

---

## Error Scenarios

### Invalid Agent ID

```bash
curl -X POST http://localhost:8000/api/v1/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "err-001",
    "agent_id": "nonexistent.agent",
    "query": "test"
  }'

# Expected: 404 error with AGENT_NOT_FOUND code
```

### Rate Limit Exceeded

```bash
# Send many requests quickly
for i in {1..100}; do
  curl -X POST http://localhost:8000/api/v1/invoke \
    -H "Content-Type: application/json" \
    -d '{"request_id": "'$i'", "agent_id": "nexusops.k8s", "query": "test"}'
done

# Expected: 429 error after limit exceeded
```

### Circuit Breaker Open

```bash
# When agent is failing repeatedly
# Expected: Immediate response with CIRCUIT_OPEN error
```

---

## Validation Checklist

- [ ] All built-in agents invocable
- [ ] Agent registration works
- [ ] Agent installation works
- [ ] Store UI displays agents
- [ ] Search functionality works
- [ ] Health status updates
- [ ] Rate limiting enforced
- [ ] Circuit breaker protects failing agents
- [ ] Streaming responses work
- [ ] Error responses include trace IDs
