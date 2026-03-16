# Agent 生命周期

## 状态流转

```
Uncreated → Registered → Active ↔ Inactive → Removed
                          │
                          └─→ 可接收调用
```

| 状态 | 可调用 | 说明 |
|------|--------|------|
| Active | ✓ | 正常运行 |
| Inactive | ✗ | 临时禁用 |
| Registered | ✗ | 已注册未激活 |
| Removed | ✗ | 已注销 |

## 阶段详解

### 1. 注册 (Registration)

**内置 Agent**: 在 `BuiltinExecutor` 自动注册

```python
# backend/app/gateway/executor/builtin.py
self._handlers = {
    "nexusops.chat": ChatAgentHandler(),
    "nexusops.k8s": K8sAgentHandler(),
}
```

**第三方 Agent**: 通过 Market API 注册

```http
POST /api/v1/agent-market/agents
{
  "agent_id": "third-party.analytics",
  "name": "Analytics Agent",
  "type": "remote",
  "endpoint": "https://...",
  "capabilities": ["data_analysis"]
}
```

### 2. 激活 (Activation)

内置 Agent 自动激活，第三方 Agent 需手动激活:

```http
POST /api/v1/agent-market/agents/{agent_id}/activate
```

### 3. 调用 (Invocation)

```
请求 → TraceMiddleware → AuthMiddleware → SchemaMiddleware
     → Gateway → ExecutorRouter → Executor → Agent Handler
     → 响应构建 → 返回
```

### 4. 停用 (Deactivation)

```http
POST /api/v1/agent-market/agents/{agent_id}/deactivate
```

停用的 Agent 返回 `AGENT_INACTIVE` 错误。

### 5. 注销 (Unregistration)

```http
DELETE /api/v1/agent-market/agents/{agent_id}
```

## Hooks

### pre_execute

缓存、校验、短路:

```python
async def pre_execute(self, request: ExecutorRequest) -> Optional[ExecutorResult]:
    cached = await self._cache.get(cache_key)
    if cached:
        return ExecutorResult(success=True, content=cached)
    return None  # 继续执行
```

### post_execute

日志、转换、增强:

```python
async def post_execute(self, request, result) -> ExecutorResult:
    result.metadata["processed_at"] = datetime.utcnow().isoformat()
    return result
```

## 健康检查

```python
async def health_check(self) -> bool:
    try:
        await self._check_dependencies()
        return True
    except Exception:
        return False
```

## 优雅关闭

```python
def __init__(self):
    self._shutdown = False
    signal.signal(signal.SIGTERM, lambda s, f: setattr(self, '_shutdown', True))

async def handle(self, request):
    if self._shutdown:
        return self._error(code="AGENT_BUSY", message="Shutting down")
    # 正常处理
```
