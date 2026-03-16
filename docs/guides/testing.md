# 测试指南

## 测试金字塔

```
        +-------------+
        |  E2E Tests  |  (少量, 慢)
        +-------------+
       /               \
      / Integration     \  (中等)
     +-------------------+
    /                     \
   /     Unit Tests        \  (大量, 快)
  +-------------------------+
```

## 目录结构

```
backend/tests/
├── conftest.py          # 共享 fixtures
├── agents/              # Agent 单元测试
├── gateway/             # Gateway 测试
└── integration/         # 集成测试
```

## Fixtures

```python
# conftest.py

@pytest.fixture
def make_request():
    """创建 ExecutorRequest 的工厂"""
    def _make(query: str, agent_id: str = "nexusops.test"):
        return ExecutorRequest(
            context=ExecutorContext(trace_id="test", request_id="test", agent_id=agent_id),
            query=query
        )
    return _make

@pytest.fixture
def mock_redis():
    class MockRedis:
        def __init__(self): self._data = {}
        async def get(self, key): return self._data.get(key)
        async def set(self, key, value, ex=None): self._data[key] = value
    return MockRedis()
```

## 单元测试

```python
# tests/agents/test_chat.py

class TestChatAgent:
    @pytest.fixture
    def handler(self):
        return ChatAgentHandler()

    def test_agent_id(self, handler):
        assert handler.agent_id == "nexusops.chat"

    @pytest.mark.asyncio
    async def test_handle_chat(self, handler, make_request):
        request = make_request(query="Hello")
        result = await handler.handle(request)
        
        assert result.success
        assert "Hello" in result.content["text"]

    @pytest.mark.asyncio
    async def test_suggested_actions(self, handler, make_request):
        result = await handler.handle(make_request(query="/deploy v1.0"))
        assert len(result.suggested_actions) > 0
```

## 错误处理测试

```python
class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_missing_query(self, handler, make_request):
        result = await handler.handle(make_request(query=""))
        
        assert not result.success
        assert result.error["code"] == "INPUT_MISSING_FIELD"
```

## Mock 外部服务

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_with_mock(handler, make_request):
    with patch.object(handler, '_fetch_data', new_callable=AsyncMock, return_value={"status": "ok"}):
        result = await handler.handle(make_request(query="test"))
        assert result.success
```

## 集成测试

```python
# tests/integration/test_invoke.py

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_invoke_success(client):
    response = await client.post(
        "/api/v1/agents/nexusops.chat/invoke",
        json={"request_id": str(uuid.uuid4()), "agent_id": "nexusops.chat", "query": "Hello"},
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
```

## 合约测试

```python
import jsonschema

def test_valid_request():
    request = {"request_id": "uuid", "agent_id": "nexusops.chat", "query": "Hello"}
    jsonschema.validate(request, REQUEST_SCHEMA)  # 不应抛出异常

def test_invalid_request():
    request = {"request_id": "uuid", "agent_id": "nexusops.chat"}  # 缺少 query
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(request, REQUEST_SCHEMA)
```

## 运行测试

```bash
# 全部测试
pytest tests/ -v

# 单文件
pytest tests/agents/test_chat.py -v

# 带覆盖率
pytest --cov=app --cov-report=term-missing
```

## 必须通过的测试

| ID | 测试 | 说明 |
|----|------|------|
| CT-001 | test_valid_request_response | 有效请求返回成功 |
| CT-002 | test_invalid_json | 无效 JSON 返回错误 |
| CT-003 | test_missing_request_id | 缺少 request_id 返回错误 |
| CT-004 | test_agent_not_found | 未知 Agent 返回错误 |
| CT-005 | test_unauthorized | 无认证返回 401 |
| CT-006 | test_trace_id_present | 响应包含 trace_id |
