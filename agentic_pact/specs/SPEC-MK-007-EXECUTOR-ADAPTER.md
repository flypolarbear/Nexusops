# Spec: MK-007 - Gateway 插件执行边界（Executor Adapter）

## 1. Summary

定义 NexusOps Agent Gateway 的可插拔执行层架构，明确内置 Agent 与第三方 Agent 的统一执行边界、Adapter 接口契约和模块划分。本规范遵循 ADR-001 的"FastAPI 单体内核 + 可插拔执行层"决策。

## 2. Goals

1. 定义统一的 `Executor` 抽象接口，内置与第三方 Agent 共用。
2. 实现内置 Agent Adapter（BuiltinExecutor）。
3. 实现第三方 Agent Adapter（RemoteExecutor）。
4. 确保同一调用链路可同时验证内置与第三方 Agent。
5. 为后续独立 Gateway 服务拆分预留清晰边界。

## 3. Non-Goals

1. 不实现具体内置 Agent 的业务逻辑（由 Agent Squad 负责）。
2. 不实现完整的服务网格能力（如 sidecar 注入）。
3. 不实现 Agent 热更新/热加载（后续迭代）。

---

## 4. 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                        Gateway Core                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    InvokeHandler                          │  │
│  │  - 接收请求                                                │  │
│  │  - 调用 Middleware Chain (MK-006)                         │  │
│  │  - 调用 ExecutorRouter                                    │  │
│  │  - 返回响应                                                │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    ExecutorRouter                         │  │
│  │  - 根据 agent_id 查找 Agent 注册信息                       │  │
│  │  - 选择 Executor 实现                                      │  │
│  │  - 执行并收集结果                                          │  │
│  └───────────────────────────────────────────────────────────┘  │
│              │                              │                    │
│              ▼                              ▼                    │
│  ┌───────────────────┐          ┌───────────────────┐           │
│  │  BuiltinExecutor  │          │  RemoteExecutor   │           │
│  │  (内置 Agent)     │          │  (第三方 Agent)   │           │
│  └───────────────────┘          └───────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
              │                              │
              ▼                              ▼
┌───────────────────┐          ┌───────────────────────────────┐
│  Internal Agents  │          │  External Agent Endpoints     │
│  - nexusops.chat  │          │  - https://agent.example.com  │
│  - nexusops.k8s   │          │  - https://partner.agent.io   │
│  - nexusops.dns   │          └───────────────────────────────┘
│  - nexusops.deploy│
└───────────────────┘
```

---

## 5. 接口契约（Interface Contract）

### 5.1 Executor 抽象基类

```python
# backend/app/gateway/executor/base.py

from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass
from enum import Enum

class ExecutorType(str, Enum):
    BUILTIN = "builtin"
    REMOTE = "remote"
    MOCK = "mock"

@dataclass
class ExecutorContext:
    """执行上下文"""
    trace_id: str
    request_id: str
    agent_id: str
    agent_version: str
    agent_type: ExecutorType
    endpoint: Optional[str] = None
    timeout_ms: int = 30000
    retry_config: Optional[dict] = None
    auth_context: Optional[dict] = None

@dataclass
class ExecutorRequest:
    """执行请求"""
    context: ExecutorContext
    query: str
    request_context: dict  # 来自 MK-006 的 RequestContext
    output_config: Optional[dict] = None
    tools: Optional[list] = None

@dataclass
class ExecutorResult:
    """执行结果"""
    success: bool
    content: dict  # ResponseContent
    structured_output: Optional[dict] = None
    suggested_actions: list = None
    related_resources: list = None
    tool_calls: list = None
    metadata: dict = None
    error: Optional[dict] = None  # ErrorDetail

    def __post_init__(self):
        self.suggested_actions = self.suggested_actions or []
        self.related_resources = self.related_resources or []
        self.tool_calls = self.tool_calls or []
        self.metadata = self.metadata or {}

class BaseExecutor(ABC):
    """Executor 抽象基类"""

    @property
    @abstractmethod
    def executor_type(self) -> ExecutorType:
        """返回 Executor 类型"""
        pass

    @abstractmethod
    async def execute(self, request: ExecutorRequest) -> ExecutorResult:
        """执行 Agent 调用"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass

    async def pre_execute(self, request: ExecutorRequest) -> Optional[ExecutorResult]:
        """
        执行前钩子
        返回 ExecutorResult 表示短路，返回 None 继续执行
        """
        return None

    async def post_execute(
        self,
        request: ExecutorRequest,
        result: ExecutorResult
    ) -> ExecutorResult:
        """执行后钩子，可修改结果"""
        return result
```

### 5.2 BuiltinExecutor（内置 Agent 适配器）

```python
# backend/app/gateway/executor/builtin.py

from typing import Callable, Dict, Optional
from .base import BaseExecutor, ExecutorType, ExecutorRequest, ExecutorResult

class BuiltinExecutor(BaseExecutor):
    """内置 Agent 执行器"""

    def __init__(self):
        self._handlers: Dict[str, Callable] = {}
        self._register_builtin_handlers()

    @property
    def executor_type(self) -> ExecutorType:
        return ExecutorType.BUILTIN

    def _register_builtin_handlers(self):
        """注册内置 Agent 处理器"""
        from app.agents import (
            ChatAgentHandler,
            K8sAgentHandler,
            DeployAgentHandler,
            DnsAgentHandler,
            ManifestAgentHandler,
            LogsAgentHandler,
            CostAgentHandler,
            CicdAgentHandler,
        )

        self._handlers = {
            "nexusops.chat": ChatAgentHandler(),
            "nexusops.k8s": K8sAgentHandler(),
            "nexusops.deploy": DeployAgentHandler(),
            "nexusops.dns": DnsAgentHandler(),
            "nexusops.manifest": ManifestAgentHandler(),
            "nexusops.logs": LogsAgentHandler(),
            "nexusops.cost": CostAgentHandler(),
            "nexusops.cicd": CicdAgentHandler(),
        }

    def register_handler(self, agent_id: str, handler: Callable):
        """动态注册处理器"""
        self._handlers[agent_id] = handler

    async def execute(self, request: ExecutorRequest) -> ExecutorResult:
        agent_id = request.context.agent_id

        if agent_id not in self._handlers:
            return ExecutorResult(
                success=False,
                content={"text": f"Builtin agent not found: {agent_id}", "format": "plain"},
                error={
                    "code": "AGENT_NOT_FOUND",
                    "message": f"Builtin agent not found: {agent_id}",
                    "details": {"agent_id": agent_id}
                }
            )

        handler = self._handlers[agent_id]

        try:
            result = await handler.handle(request)
            return result
        except Exception as e:
            return ExecutorResult(
                success=False,
                content={"text": str(e), "format": "plain"},
                error={
                    "code": "EXEC_INTERNAL_ERROR",
                    "message": str(e),
                    "details": {"agent_id": agent_id, "exception": type(e).__name__}
                }
            )

    async def health_check(self) -> bool:
        return True

    def list_agents(self) -> list[str]:
        """列出所有内置 Agent"""
        return list(self._handlers.keys())
```

### 5.3 RemoteExecutor（第三方 Agent 适配器）

```python
# backend/app/gateway/executor/remote.py

import httpx
from typing import Optional
from .base import BaseExecutor, ExecutorType, ExecutorRequest, ExecutorResult

class RemoteExecutor(BaseExecutor):
    """第三方 Agent 执行器"""

    def __init__(self, http_client: Optional[httpx.AsyncClient] = None):
        self._client = http_client or httpx.AsyncClient(timeout=30.0)

    @property
    def executor_type(self) -> ExecutorType:
        return ExecutorType.REMOTE

    async def execute(self, request: ExecutorRequest) -> ExecutorResult:
        endpoint = request.context.endpoint

        if not endpoint:
            return ExecutorResult(
                success=False,
                content={"text": "No endpoint configured for remote agent", "format": "plain"},
                error={
                    "code": "AGENT_ENDPOINT_MISSING",
                    "message": "No endpoint configured for remote agent",
                    "details": {"agent_id": request.context.agent_id}
                }
            )

        # 构建远程调用请求
        remote_request = {
            "request_id": request.context.request_id,
            "trace_id": request.context.trace_id,
            "query": request.query,
            "context": request.request_context,
            "output_config": request.output_config,
            "tools": request.tools,
        }

        headers = {
            "Content-Type": "application/json",
            "X-Trace-ID": request.context.trace_id,
            "X-Request-ID": request.context.request_id,
        }

        # 添加认证信息
        if request.context.auth_context:
            if "api_key" in request.context.auth_context:
                headers["Authorization"] = f"Bearer {request.context.auth_context['api_key']}"

        try:
            response = await self._client.post(
                f"{endpoint}/invoke",
                json=remote_request,
                headers=headers,
                timeout=request.context.timeout_ms / 1000,
            )

            if response.status_code >= 400:
                return self._handle_error_response(response, request)

            data = response.json()
            return self._parse_response(data, request)

        except httpx.TimeoutException:
            return ExecutorResult(
                success=False,
                content={"text": "Remote agent timeout", "format": "plain"},
                error={
                    "code": "EXEC_TIMEOUT",
                    "message": f"Remote agent timeout after {request.context.timeout_ms}ms",
                    "details": {"endpoint": endpoint},
                    "retry_after": 5
                }
            )
        except httpx.RequestError as e:
            return ExecutorResult(
                success=False,
                content={"text": f"Remote agent connection error: {e}", "format": "plain"},
                error={
                    "code": "EXEC_DOWNSTREAM_ERROR",
                    "message": str(e),
                    "details": {"endpoint": endpoint},
                    "retry_after": 10
                }
            )

    def _handle_error_response(
        self,
        response: httpx.Response,
        request: ExecutorRequest
    ) -> ExecutorResult:
        """处理错误响应"""
        try:
            data = response.json()
            error = data.get("error", {})
        except:
            error = {
                "code": f"HTTP_{response.status_code}",
                "message": response.text[:500]
            }

        return ExecutorResult(
            success=False,
            content={"text": error.get("message", "Unknown error"), "format": "plain"},
            error={
                "code": error.get("code", "EXEC_DOWNSTREAM_ERROR"),
                "message": error.get("message", "Remote agent error"),
                "details": {
                    "http_status": response.status_code,
                    "endpoint": request.context.endpoint,
                    "original_error": error
                }
            }
        )

    def _parse_response(self, data: dict, request: ExecutorRequest) -> ExecutorResult:
        """解析远程响应"""
        # 校验响应格式
        if "content" not in data:
            return ExecutorResult(
                success=False,
                content={"text": "Invalid response: missing content", "format": "plain"},
                error={
                    "code": "AGENT_OUTPUT_INVALID",
                    "message": "Remote agent returned invalid response",
                    "details": {"missing_field": "content"}
                }
            )

        status = data.get("status", "success")

        return ExecutorResult(
            success=(status == "success"),
            content=data["content"],
            structured_output=data.get("structured_output"),
            suggested_actions=data.get("suggested_actions", []),
            related_resources=data.get("related_resources", []),
            tool_calls=data.get("tool_calls", []),
            metadata=data.get("metadata", {}),
            error=data.get("error") if status == "error" else None
        )

    async def health_check(self) -> bool:
        return True  # 实际应检查连接池状态
```

### 5.4 ExecutorRouter（路由器）

```python
# backend/app/gateway/executor/router.py

from typing import Dict, Optional
from .base import BaseExecutor, ExecutorType, ExecutorContext, ExecutorRequest, ExecutorResult
from .builtin import BuiltinExecutor
from .remote import RemoteExecutor

class ExecutorRouter:
    """Executor 路由器"""

    def __init__(self):
        self._builtin = BuiltinExecutor()
        self._remote = RemoteExecutor()
        self._agent_registry: Dict[str, dict] = {}  # agent_id -> registration info

    async def route_and_execute(
        self,
        agent_id: str,
        trace_id: str,
        request_id: str,
        query: str,
        request_context: dict,
        output_config: Optional[dict] = None,
        tools: Optional[list] = None,
    ) -> ExecutorResult:
        """路由并执行"""

        # 1. 查找 Agent 注册信息
        agent_info = await self._resolve_agent(agent_id)

        if not agent_info:
            return ExecutorResult(
                success=False,
                content={"text": f"Agent not found: {agent_id}", "format": "plain"},
                error={
                    "code": "AGENT_NOT_FOUND",
                    "message": f"Agent not found: {agent_id}",
                    "details": {"agent_id": agent_id}
                }
            )

        # 2. 构建执行上下文
        context = ExecutorContext(
            trace_id=trace_id,
            request_id=request_id,
            agent_id=agent_id,
            agent_version=agent_info.get("version", "1.0.0"),
            agent_type=ExecutorType(agent_info.get("type", "builtin")),
            endpoint=agent_info.get("endpoint"),
            timeout_ms=agent_info.get("timeout_ms", 30000),
            auth_context=agent_info.get("auth"),
        )

        request = ExecutorRequest(
            context=context,
            query=query,
            request_context=request_context,
            output_config=output_config,
            tools=tools,
        )

        # 3. 选择 Executor
        executor = self._select_executor(context.agent_type)

        # 4. 执行
        pre_result = await executor.pre_execute(request)
        if pre_result:
            return pre_result

        result = await executor.execute(request)
        result = await executor.post_execute(request, result)

        return result

    async def _resolve_agent(self, agent_id: str) -> Optional[dict]:
        """解析 Agent 注册信息"""
        # 优先检查内置 Agent
        if agent_id in self._builtin.list_agents():
            return {
                "agent_id": agent_id,
                "type": "builtin",
                "version": "1.0.0",
            }

        # 检查注册的第三方 Agent
        if agent_id in self._agent_registry:
            return self._agent_registry[agent_id]

        # TODO: 从数据库查询
        return None

    def _select_executor(self, agent_type: ExecutorType) -> BaseExecutor:
        """选择 Executor"""
        if agent_type == ExecutorType.BUILTIN:
            return self._builtin
        elif agent_type == ExecutorType.REMOTE:
            return self._remote
        else:
            raise ValueError(f"Unknown executor type: {agent_type}")

    def register_agent(self, agent_id: str, info: dict):
        """注册第三方 Agent"""
        self._agent_registry[agent_id] = info

    def unregister_agent(self, agent_id: str):
        """注销 Agent"""
        self._agent_registry.pop(agent_id, None)
```

---

## 6. Agent Handler 接口

### 6.1 基类定义

```python
# backend/app/agents/base.py

from abc import ABC, abstractmethod
from app.gateway.executor.base import ExecutorRequest, ExecutorResult

class BaseAgentHandler(ABC):
    """Agent 处理器基类"""

    @property
    @abstractmethod
    def agent_id(self) -> str:
        """Agent 标识"""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> list[str]:
        """Agent 能力列表"""
        pass

    @abstractmethod
    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        """处理请求"""
        pass

    def get_tools(self) -> list[dict]:
        """获取工具定义"""
        return []
```

### 6.2 示例实现

```python
# backend/app/agents/k8s.py

from .base import BaseAgentHandler
from app.gateway.executor.base import ExecutorRequest, ExecutorResult

class K8sAgentHandler(BaseAgentHandler):
    """Kubernetes Agent 处理器"""

    @property
    def agent_id(self) -> str:
        return "nexusops.k8s"

    @property
    def capabilities(self) -> list[str]:
        return ["k8s_deploy", "k8s_scale", "k8s_logs", "k8s_describe"]

    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        query = request.query.lower()
        context = request.request_context

        # 示例：根据 query 调用不同的 K8s 操作
        if "logs" in query or "日志" in query:
            return await self._get_logs(context)
        elif "describe" in query or "详情" in query:
            return await self._describe_resource(context)
        else:
            return await self._query_status(context)

    async def _get_logs(self, context: dict) -> ExecutorResult:
        # 实际实现调用 K8s API
        return ExecutorResult(
            success=True,
            content={
                "text": "## Pod Logs\n\n```\n2026-02-24 INFO Starting...\n```",
                "format": "markdown"
            },
            metadata={"operation": "get_logs"}
        )

    async def _describe_resource(self, context: dict) -> ExecutorResult:
        return ExecutorResult(
            success=True,
            content={
                "text": "## Resource Description\n\n...",
                "format": "markdown"
            }
        )

    async def _query_status(self, context: dict) -> ExecutorResult:
        return ExecutorResult(
            success=True,
            content={
                "text": "## K8s Status\n\nAll resources healthy.",
                "format": "markdown"
            }
        )

    def get_tools(self) -> list[dict]:
        return [
            {
                "name": "get_pod_logs",
                "description": "Get logs from a pod",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pod_name": {"type": "string"},
                        "namespace": {"type": "string", "default": "default"},
                        "tail_lines": {"type": "integer", "default": 100},
                    },
                    "required": ["pod_name"],
                },
            },
            {
                "name": "describe_resource",
                "description": "Describe a Kubernetes resource",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "resource_type": {"type": "string"},
                        "name": {"type": "string"},
                        "namespace": {"type": "string", "default": "default"},
                    },
                    "required": ["resource_type", "name"],
                },
            },
        ]
```

---

## 7. 目录结构

```
backend/app/
├── gateway/
│   ├── __init__.py
│   ├── contract.py          # MK-006: 契约定义
│   ├── errors.py            # MK-006: 错误码
│   ├── validator.py         # MK-006: Schema 校验
│   ├── trace.py             # MK-006: Trace 处理
│   ├── response.py          # MK-006: 响应构建
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── trace.py         # TraceMiddleware
│   │   ├── auth.py          # AuthMiddleware
│   │   ├── schema.py        # SchemaMiddleware
│   │   ├── ratelimit.py     # RateLimitMiddleware
│   │   └── audit.py         # AuditMiddleware
│   └── executor/            # MK-007: 执行层
│       ├── __init__.py
│       ├── base.py          # BaseExecutor
│       ├── builtin.py       # BuiltinExecutor
│       ├── remote.py        # RemoteExecutor
│       └── router.py        # ExecutorRouter
├── agents/                   # 内置 Agent 实现
│   ├── __init__.py
│   ├── base.py              # BaseAgentHandler
│   ├── chat.py              # nexusops.chat
│   ├── k8s.py               # nexusops.k8s
│   ├── deploy.py            # nexusops.deploy
│   ├── dns.py               # nexusops.dns
│   ├── manifest.py          # nexusops.manifest
│   ├── logs.py              # nexusops.logs
│   ├── cost.py              # nexusops.cost
│   └── cicd.py              # nexusops.cicd
└── api/
    └── agents.py            # 现有 API（将重构使用 gateway 层）
```

---

## 8. 模块边界规则

### 8.1 禁止项

1. **禁止**在 `api/agents.py` 中直接实现 Agent 业务逻辑
2. **禁止**在 Agent Handler 中直接构造 HTTP 响应
3. **禁止**在 RemoteExecutor 中硬编码特定第三方 Agent 逻辑
4. **禁止**跨层直接引用（如 api 层直接引用 agents 层）

### 8.2 必须项

1. **必须**通过 `ExecutorRouter.route_and_execute()` 调用 Agent
2. **必须**在 Agent Handler 中返回 `ExecutorResult`
3. **必须**在 Executor 中传播 `trace_id`
4. **必须**在 RemoteExecutor 中处理所有网络异常

### 8.3 依赖规则

```
api/ → gateway/ → executor/ → agents/
         │
         └→ middleware/
```

---

## 9. 测试必过项（Test Acceptance Criteria）

### 9.1 P0 用例（必须 100% 通过）

| ID | 用例 | 验证点 |
|----|------|--------|
| EX-001 | 内置 Agent 调用成功 | nexusops.chat 返回 success |
| EX-002 | 第三方 Agent 调用成功 | mock remote agent 返回 success |
| EX-003 | 不存在的 Agent 返回 AGENT_NOT_FOUND | 错误码正确 |
| EX-004 | RemoteExecutor 超时返回 EXEC_TIMEOUT | 模拟超时 |
| EX-005 | RemoteExecutor 连接失败返回 EXEC_DOWNSTREAM_ERROR | 模拟连接失败 |
| EX-006 | 同一 trace_id 贯穿内置 Agent 调用 | 日志检查 |
| EX-007 | 同一 trace_id 贯穿第三方 Agent 调用 | Header 检查 |
| EX-008 | Agent Handler 返回 ExecutorResult | 类型检查 |

### 9.2 P1 用例（通过率 >= 95%）

| ID | 用例 | 验证点 |
|----|------|--------|
| EX-101 | 内置与第三方 Agent 可在同一请求链路混合调用 | 集成测试 |
| EX-102 | pre_execute 钩子可短路执行 | 返回 result 时不调用 execute |
| EX-103 | post_execute 钩子可修改结果 | 结果被正确修改 |
| EX-104 | RemoteExecutor 正确解析第三方响应 | 字段映射正确 |
| EX-105 | RemoteExecutor 处理非法 JSON 响应 | 返回 AGENT_OUTPUT_INVALID |
| EX-106 | BuiltinExecutor 动态注册 Handler | 新 Handler 可被调用 |
| EX-107 | ExecutorRouter 支持 Agent 注销 | 注销后返回 NOT_FOUND |
| EX-108 | 健康检查接口正常 | health_check() 返回 True |

### 9.3 同链路验证测试

```python
# tests/integration/test_same_chain.py

async def test_builtin_and_remote_same_chain():
    """验证内置与第三方 Agent 使用同一调用链路"""
    router = ExecutorRouter()

    # 注册 mock 第三方 Agent
    router.register_agent("third-party.test", {
        "type": "remote",
        "endpoint": "http://mock-agent:8000",
        "version": "1.0.0"
    })

    trace_id = "a1b2c3d4e5f67890a1b2c3d4e5f67890"

    # 调用内置 Agent
    result1 = await router.route_and_execute(
        agent_id="nexusops.chat",
        trace_id=trace_id,
        request_id="req-001",
        query="hello",
        request_context={}
    )
    assert result1.success

    # 调用第三方 Agent（使用 mock server）
    result2 = await router.route_and_execute(
        agent_id="third-party.test",
        trace_id=trace_id,  # 同一 trace_id
        request_id="req-002",
        query="hello",
        request_context={}
    )
    # 验证 trace_id 被传递到第三方
    # (通过 mock server 记录的请求验证)
```

---

## 10. 实施约束

1. 现有 `api/agents.py` 中的 `invoke_agent()` 函数需重构为调用 `ExecutorRouter`
2. 所有内置 Agent 业务逻辑需迁移到 `agents/` 目录下的 Handler
3. 重构过程中保持 API 向后兼容（请求/响应格式不变）
4. 第一阶段可保留 mock 实现，逐步替换为真实逻辑

---

## 11. 未来拆分边界

当需要将 Gateway 拆分为独立服务时：

```
┌─────────────────────────────────────────┐
│          Gateway Service (独立)          │
│  - gateway/                              │
│  - executor/remote.py                    │
└─────────────────────────────────────────┘
           │ gRPC/HTTP
           ▼
┌─────────────────────────────────────────┐
│       Agent Service (独立或多个)         │
│  - executor/builtin.py                   │
│  - agents/                               │
└─────────────────────────────────────────┘
```

**触发条件**（ADR-001）：
- 调用量 > 10000 QPS
- 需要独立扩缩容
- 需要物理隔离不同租户

---

## 12. Rollback Plan

1. 保留原有 `api/agents.py` 实现，新旧代码可通过特性开关切换
2. ExecutorRouter 支持 fallback 到直接调用（绕过 Executor 层）
3. 逐个 Agent 迁移，每次迁移后验证再继续
