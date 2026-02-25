# Test Evidence: MK-006/MK-007 - Gateway 层实现与重构

## Environment
- Date: 2026-02-25
- Environment: Development
- Version/Commit: Gateway layer implementation

## Overview

实现了 MK-006 (Gateway 调用契约) 和 MK-007 (Gateway 插件执行边界)，并重构了 api/agents.py 使用新的 Gateway 层。

## New Modules Created

### 1. Gateway Core (`backend/app/gateway/`)

| File | Description |
|------|-------------|
| `__init__.py` | Module initialization and exports |
| `errors.py` | Standardized error codes (INPUT_*, AUTH_*, AGENT_*, EXEC_*, SYSTEM_*) |
| `trace.py` | Trace ID generation and context management |
| `contract.py` | Request/Response contract definitions |
| `response.py` | Response builder utilities |
| `validator.py` | JSON Schema validation |

### 2. Gateway Executor (`backend/app/gateway/executor/`)

| File | Description |
|------|-------------|
| `__init__.py` | Module initialization |
| `base.py` | BaseExecutor abstract class |
| `builtin.py` | BuiltinExecutor for internal agents |
| `remote.py` | RemoteExecutor for third-party agents |
| `router.py` | ExecutorRouter for agent routing |

### 3. Built-in Agents (`backend/app/agents/`)

| File | Agent ID | Description |
|------|----------|-------------|
| `base.py` | - | BaseAgentHandler base class |
| `chat.py` | nexusops.chat | General AI assistant |
| `k8s.py` | nexusops.k8s | Kubernetes operations |
| `deploy.py` | nexusops.deploy | Deployment orchestration |
| `dns.py` | nexusops.dns | DNS operations |

## Architecture

```
api/agents.py
    │
    ▼
┌─────────────────────────────────────────────────────┐
│                   Gateway Layer                      │
│  ┌─────────────────────────────────────────────┐    │
│  │  trace.py - Trace ID generation             │    │
│  │  errors.py - Error codes                    │    │
│  │  response.py - Response building            │    │
│  └─────────────────────────────────────────────┘    │
│                      │                               │
│                      ▼                               │
│  ┌─────────────────────────────────────────────┐    │
│  │              ExecutorRouter                 │    │
│  │  - Route to appropriate executor            │    │
│  │  - Check install status                     │    │
│  └─────────────────────────────────────────────┘    │
│           │                    │                    │
│           ▼                    ▼                    │
│  ┌─────────────────┐  ┌─────────────────────┐       │
│  │ BuiltinExecutor │  │   RemoteExecutor    │       │
│  │  - chat         │  │   - HTTP calls      │       │
│  │  - k8s          │  │   - Timeout handling│       │
│  │  - deploy       │  │   - Error mapping   │       │
│  │  - dns          │  │                     │       │
│  └─────────────────┘  └─────────────────────┘       │
└─────────────────────────────────────────────────────┘
```

## Error Codes Implemented

### Input Errors (HTTP 400)
- `INPUT_INVALID_JSON`
- `INPUT_SCHEMA_VIOLATION`
- `INPUT_MISSING_FIELD`
- `INPUT_INVALID_FORMAT`
- `INPUT_VALUE_OUT_OF_RANGE`
- `INPUT_QUERY_TOO_LONG`
- `INPUT_INVALID_AGENT_ID`

### Auth Errors (HTTP 401/403)
- `AUTH_TOKEN_MISSING`
- `AUTH_TOKEN_INVALID`
- `AUTH_TOKEN_EXPIRED`
- `AUTH_PERMISSION_DENIED`
- `AUTH_QUOTA_EXCEEDED`

### Agent Errors (HTTP 404/409/422)
- `AGENT_NOT_FOUND`
- `AGENT_INACTIVE`
- `AGENT_NOT_INSTALLED`
- `AGENT_DISABLED`
- `AGENT_OUTPUT_INVALID`
- `AGENT_ENDPOINT_MISSING`

### Execution Errors (HTTP 500/502/504)
- `EXEC_TIMEOUT`
- `EXEC_TOOL_FAILED`
- `EXEC_DOWNSTREAM_ERROR`
- `EXEC_INTERNAL_ERROR`

### System Errors (HTTP 500/503)
- `SYSTEM_INTERNAL_ERROR`
- `SYSTEM_UNAVAILABLE`
- `SYSTEM_OVERLOADED`
- `SYSTEM_MAINTENANCE`

## Test Results

### MK-008 Backward Compatibility Tests
All 8 tests pass after refactoring:

```
tests/test_mk008_third_party_agent.py::TestAgentRegistration::test_register_valid_manifest PASSED
tests/test_mk008_third_party_agent.py::TestAgentRegistration::test_register_invalid_manifest_missing_required PASSED
tests/test_mk008_third_party_agent.py::TestAgentInstallFlow::test_install_and_invoke_agent PASSED
tests/test_mk008_third_party_agent.py::TestAgentInstallFlow::test_uninstall_then_invoke_rejected PASSED
tests/test_mk008_third_party_agent.py::TestAgentEnableDisable::test_disable_then_invoke_rejected PASSED
tests/test_mk008_third_party_agent.py::TestAgentEnableDisable::test_enable_disabled_agent PASSED
tests/test_mk008_third_party_agent.py::TestStructuredOutput::test_invoke_returns_structured_output PASSED
tests/test_mk008_third_party_agent.py::TestInstalledAgentsList::test_list_installed_agents PASSED

8 passed
```

## Key Implementation Details

### 1. Trace ID Propagation
```python
# Generate at request entry
trace_id = generate_trace_id()

# Initialize context
init_trace_context(
    request_id=request.request_id,
    trace_id=trace_id,
    agent_id=agent_id,
)

# Pass to executor
executor_result = await router.route_and_execute(
    agent_id=agent_id,
    trace_id=trace_id,
    ...
)
```

### 2. Executor Routing
```python
class ExecutorRouter:
    async def route_and_execute(self, agent_id, ...):
        # Resolve agent info
        agent_info = self._resolve_agent(agent_id, ...)

        # Select executor
        executor = self._select_executor(agent_type)

        # Execute with hooks
        pre_result = await executor.pre_execute(request)
        if pre_result:
            return pre_result

        result = await executor.execute(request)
        result = await executor.post_execute(request, result)
        return result
```

### 3. Error Handling
```python
# Built-in error with proper code
return ExecutorResult(
    success=False,
    content={"text": "...", "format": "plain"},
    error={
        "code": "AGENT_NOT_FOUND",
        "message": f"Agent not found: {agent_id}",
        "details": {"agent_id": agent_id},
    },
)
```

## Files Changed

### New Files
- `backend/app/gateway/__init__.py`
- `backend/app/gateway/errors.py`
- `backend/app/gateway/trace.py`
- `backend/app/gateway/contract.py`
- `backend/app/gateway/response.py`
- `backend/app/gateway/validator.py`
- `backend/app/gateway/executor/__init__.py`
- `backend/app/gateway/executor/base.py`
- `backend/app/gateway/executor/builtin.py`
- `backend/app/gateway/executor/remote.py`
- `backend/app/gateway/executor/router.py`
- `backend/app/agents/__init__.py`
- `backend/app/agents/base.py`
- `backend/app/agents/chat.py`
- `backend/app/agents/k8s.py`
- `backend/app/agents/deploy.py`
- `backend/app/agents/dns.py`

### Modified Files
- `backend/app/api/agents.py` - Refactored to use Gateway layer

## Risks & TODOs

### Risks
1. Mock handlers used for remote agents in development
2. No authentication middleware yet
3. No rate limiting middleware yet

### TODOs
1. Add TraceMiddleware for automatic trace ID injection
2. Add AuthMiddleware for authentication
3. Add RateLimitMiddleware for rate limiting
4. Implement real HTTP calls in RemoteExecutor
5. Add more built-in agents (logs, cost, cicd, manifest)

## Conclusion

**Status: PASS**

MK-006/MK-007 实现完成：
- Gateway 层架构清晰
- 错误码体系标准化
- Trace ID 追踪支持
- Executor 抽象接口统一
- 内置与第三方 Agent 共用同一调用链路
- 所有 MK-008 测试保持通过，向后兼容
