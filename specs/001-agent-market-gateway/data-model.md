# Data Model: Agent Market and Gateway

**Feature**: 001-agent-market-gateway
**Date**: 2026-03-01

## Entity Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Agent       │────<│  AgentVersion   │>────│  AgentHealth    │
│                 │     │                 │     │                 │
│ - id            │     │ - version       │     │ - status        │
│ - name          │     │ - endpoint      │     │ - last_check    │
│ - category      │     │ - schemas       │     │ - latency_ms    │
│ - status        │     │ - is_default    │     │ - error_count   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ InstalledAgent  │     │  Invocation     │
│                 │     │                 │
│ - agent_id      │     │ - request_id    │
│ - status        │     │ - trace_id      │
│ - installed_at  │     │ - agent_id      │
│ - installed_by  │     │ - timing        │
└─────────────────┘     │ - outcome       │
                        └─────────────────┘
```

---

## Entity Definitions

### Agent (Existing: `AgentRegistration`)

Represents a registered agent in the marketplace.

| Field | Type | Description |
|-------|------|-------------|
| id | str | Unique agent identifier (e.g., "nexusops.k8s") |
| name | str | Human-readable name |
| version | str | Current version string |
| manifest | JSON | Full agent manifest |
| status | str | Agent status: active, inactive, error |
| endpoint | str | Remote endpoint URL (for third-party) |
| last_heartbeat | datetime | Last heartbeat timestamp |

**Validation Rules**:
- `id` must match pattern `^[a-z][a-z0-9._-]{2,63}$`
- `status` must be one of: active, inactive, error
- `manifest` must contain required fields: name, version, capabilities

---

### InstalledAgent (Existing)

Tracks installation status for agents.

| Field | Type | Description |
|-------|------|-------------|
| agent_id | str | FK to Agent.id |
| install_status | str | installed, disabled |
| installed_at | datetime | Installation timestamp |
| installed_by | str | User who installed |

**Validation Rules**:
- `install_status` must be: installed, disabled
- `agent_id` must exist in AgentRegistration table

---

### AgentHealth (New)

Tracks health status for agent endpoints.

| Field | Type | Description |
|-------|------|-------------|
| agent_id | str | FK to Agent.id |
| status | str | healthy, degraded, unavailable |
| last_check | datetime | Last health check timestamp |
| latency_ms | int | Response latency in milliseconds |
| error_count | int | Consecutive error count |
| last_error | str | Last error message |

**State Transitions**:
```
healthy ──(error)──> degraded ──(3 errors)──> unavailable
    ▲                                              │
    └────────────(success)─────────────────────────┘
```

**Validation Rules**:
- `status` must be: healthy, degraded, unavailable
- `latency_ms` must be >= 0
- `error_count` must be >= 0

---

### Invocation (New - Logging)

Records all agent invocations for observability.

| Field | Type | Description |
|-------|------|-------------|
| request_id | str | Client request ID |
| trace_id | str | Distributed trace ID |
| agent_id | str | Target agent |
| query | str | User query (truncated) |
| status | str | success, error, partial |
| latency_ms | int | Total latency |
| error_code | str | Error code if failed |
| created_at | datetime | Invocation timestamp |

**Validation Rules**:
- `request_id` is required
- `trace_id` is required
- `status` must be: success, error, partial

---

### RateLimitConfig (New)

Configuration for rate limiting per agent.

| Field | Type | Description |
|-------|------|-------------|
| agent_id | str | FK to Agent.id |
| requests_per_minute | int | Rate limit |
| burst_limit | int | Burst allowance |
| enabled | bool | Rate limiting enabled |

---

### CircuitState (New - In Memory)

Circuit breaker state (not persisted).

| Field | Type | Description |
|-------|------|-------------|
| agent_id | str | Agent identifier |
| state | str | closed, open, half_open |
| failure_count | int | Consecutive failures |
| last_failure | datetime | Last failure timestamp |

---

## Relationships

| Relationship | Type | Description |
|--------------|------|-------------|
| Agent → AgentHealth | 1:1 | Each agent has one health record |
| Agent → InstalledAgent | 1:0..1 | Agent may be installed |
| Agent → Invocation | 1:N | Agent has many invocations |
| Agent → RateLimitConfig | 1:0..1 | Agent may have rate limit config |

---

## Index Requirements

| Table | Index | Purpose |
|-------|-------|---------|
| invocations | (agent_id, created_at) | Query invocations by agent |
| invocations | (trace_id) | Trace lookup |
| agent_health | (agent_id) | Health lookup |
| installed_agents | (install_status) | List by status |

---

## Migration Notes

1. **New Tables**: `agent_health`, `invocations`, `rate_limit_configs`
2. **No Schema Changes**: Existing tables remain unchanged
3. **Backward Compatible**: All existing APIs continue to work
