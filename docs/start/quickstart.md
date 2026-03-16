# 10分钟快速上手

创建你的第一个 NexusOps Agent。

## Step 1: 创建 Handler

在 `backend/app/agents/` 创建新文件:

```python
# backend/app/agents/hello.py

from typing import List
from app.agents.base import BaseAgentHandler
from app.gateway.executor.base import ExecutorRequest, ExecutorResult


class HelloAgentHandler(BaseAgentHandler):
    """简单问候 Agent"""

    @property
    def agent_id(self) -> str:
        return "nexusops.hello"

    @property
    def capabilities(self) -> List[str]:
        return ["greeting", "introduction"]

    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        user_id = request.request_context.get("user_id", "Guest")

        return self._success(
            text=f"## Hello, {user_id}!\n\nHow can I help you today?",
            structured_output={"greeting": f"Hello, {user_id}!"},
            metadata={"operation": "greeting"}
        )
```

## Step 2: 注册 Agent

在 `backend/app/agents/__init__.py` 添加:

```python
from .hello import HelloAgentHandler

__all__ = [
    # ...existing...
    "HelloAgentHandler",
]
```

在 `backend/app/gateway/executor/builtin.py` 注册:

```python
from app.agents import HelloAgentHandler

# 在 _register_builtin_handlers() 中:
self._handlers = {
    # ...existing...
    "nexusops.hello": HelloAgentHandler(),
}
```

## Step 3: 测试调用

```bash
curl -X POST http://localhost:8000/api/v1/agents/nexusops.hello/invoke \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-token" \
  -d '{
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "agent_id": "nexusops.hello",
    "query": "Hello!",
    "context": {"user_id": "developer"}
  }'
```

## Step 4: 添加工具（可选）

```python
def get_tools(self) -> List[dict]:
    return [
        {
            "name": "greet_user",
            "description": "生成个性化问候",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "style": {"type": "string", "enum": ["formal", "casual"]}
                },
                "required": ["name"]
            }
        }
    ]
```

## Step 5: 错误处理

```python
async def handle(self, request: ExecutorRequest) -> ExecutorResult:
    if not request.query:
        return self._error(
            code="INPUT_MISSING_FIELD",
            message="Query cannot be empty",
            details={"field": "query"}
        )

    # 正常处理...
```

## 完整示例

参见内置 Agent 实现:
- `backend/app/agents/chat.py` - 通用对话
- `backend/app/agents/k8s.py` - Kubernetes 操作
- `backend/app/agents/deploy.py` - 部署管理
