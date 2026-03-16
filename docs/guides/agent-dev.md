# Agent 开发指南

## 目录结构

```
backend/app/agents/
├── __init__.py
├── base.py           # BaseAgentHandler 基类
├── chat.py           # Chat Agent
├── k8s/              # K8s Agent (模块化)
│   ├── __init__.py
│   ├── handler.py
│   └── tools.py
└── ...
```

## Agent Handler 基类

```python
from app.agents.base import BaseAgentHandler
from app.gateway.executor.base import ExecutorRequest, ExecutorResult

class MyAgentHandler(BaseAgentHandler):
    @property
    def agent_id(self) -> str:
        return "namespace.agent_name"

    @property
    def capabilities(self) -> List[str]:
        return ["capability:read", "capability:write"]

    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        # 处理请求
        return self._success(text="处理结果")
```

## 必需实现

| 属性/方法 | 类型 | 说明 |
|-----------|------|------|
| agent_id | str | 唯一标识 (格式: `namespace.name`) |
| capabilities | List[str] | 能力列表 |
| handle(request) | async | 主处理函数 |

## 可选实现

| 方法 | 说明 |
|------|------|
| get_tools() | 返回工具定义 |
| get_manifest() | 返回完整 Manifest |

## 响应构建

```python
# 成功响应
return self._success(
    text="## 结果\n\n操作成功",
    structured_output={"key": "value"},
    suggested_actions=[
        self._action("next", "invoke", "下一步", {"query": "continue"})
    ],
    metadata={"operation": "complete"}
)

# 错误响应
return self._error(
    code="INPUT_MISSING_FIELD",
    message="Query cannot be empty",
    details={"field": "query"}
)
```

## 工具定义

```python
def get_tools(self) -> List[Dict[str, Any]]:
    return [
        {
            "name": "get_status",
            "description": "获取部署状态",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "codename": {"type": "string"},
                    "region": {"type": "string"}
                },
                "required": ["codename"]
            },
            "dangerous": False
        }
    ]
```

## 注册 Agent

1. 在 `__init__.py` 导出
2. 在 `BuiltinExecutor` 注册

```python
# backend/app/gateway/executor/builtin.py
self._handlers = {
    "nexusops.myagent": MyAgentHandler(),
}
```

## 最佳实践

1. **单一职责**: 每个 Agent 只负责一个领域
2. **幂等性**: 使用 request_id 避免重复处理
3. **超时处理**: 外部调用设置合理超时
4. **资源清理**: 使用 try/finally 确保释放资源
5. **日志记录**: 包含 trace_id 便于追踪
