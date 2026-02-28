# Spec: MK-006-MK-007-HOTFIX - 契约一致性修正

## 1. Summary

对 MK-006/MK-007 实现进行修正，解决契约一致性和测试严谨性问题。

## 2. Scope

**仅包含以下修正项，不添加新功能**：

1. `AgentResponse` Schema 添加顶层 `trace_id` 字段
2. 替换 `HTTPException` 为统一错误构建器
3. 添加 path/body agent_id 一致性校验
4. 修复测试"软通过"逻辑

## 3. Blocking Changes

### 3.1 修正 `AgentResponse` Schema

**File**: `backend/app/models/schemas.py`

**Current**:
```python
class AgentResponse(BaseModel):
    request_id: str
    status: Literal["success", "error", "partial", "pending"]
    content: AgentContent
    structured_output: Optional[Any] = None
    suggested_actions: list[AgentAction] = []
    related_resources: list[RelatedResource] = []
    tool_calls: Optional[list[dict[str, Any]]] = None
    metadata: Optional[dict[str, Any]] = None
    error: Optional[AgentError] = None
```

**Required**:
```python
class AgentResponse(BaseModel):
    request_id: str
    trace_id: str  # ← 新增：顶层 trace_id（MK-006 规范）
    status: Literal["success", "error", "partial", "pending"]
    content: AgentContent
    structured_output: Optional[Any] = None
    suggested_actions: list[AgentAction] = []
    related_resources: list[RelatedResource] = []
    tool_calls: Optional[list[dict[str, Any]]] = None
    metadata: Optional[dict[str, Any]] = None
    error: Optional[AgentError] = None
```

### 3.2 替换 HTTPException 为统一错误构建器

**File**: `backend/app/api/agents.py`

**Locations to fix**:

| Line | Current | Required |
|------|---------|----------|
| 234 | `raise HTTPException(status_code=404, detail="Agent not found")` | `raise agent_not_found(agent_id)` |
| 283-289 | `raise HTTPException(status_code=403, detail={...})` | `raise agent_not_installed(agent_id)` |
| 294-300 | `raise HTTPException(status_code=403, detail={...})` | `raise agent_not_installed(agent_id)` |
| 304-311 | `raise HTTPException(status_code=403, detail={...})` | `raise agent_disabled(agent_id)` |
| 322-329 | `raise HTTPException(status_code=404, detail={...})` | `raise agent_not_found(agent_id)` |

**Required Import**:
```python
from app.gateway.errors import agent_not_found, agent_not_installed, agent_disabled
```

### 3.3 添加 agent_id 一致性校验

**File**: `backend/app/api/agents.py`

**Location**: `invoke_agent` 函数入口

**Required**:
```python
@router.post("/{agent_id}/invoke", response_model=AgentResponse)
async def invoke_agent(
    agent_id: str,
    request: AgentRequest,
    db: AsyncSession = Depends(get_db),
):
    # 新增：校验 path 与 body agent_id 一致性
    if request.agent_id != agent_id:
        from app.gateway.errors import InputError, ErrorCode
        raise InputError(
            code=ErrorCode.INPUT_INVALID_AGENT_ID,
            message=f"Path agent_id '{agent_id}' does not match body agent_id '{request.agent_id}'",
            details={"path_agent_id": agent_id, "body_agent_id": request.agent_id},
        )

    # 原有逻辑...
```

### 3.4 修复测试"软通过"逻辑

**File**: `backend/tests/test_mk008_third_party_agent.py`

**Location**: `test_invoke_returns_structured_output` (line 310-328)

**Current**:
```python
# Note: May fail with 500 due to DB issues in test environment
# The key validation is that when it works, it returns structured output
if invoke_response.status_code == 200:
    data = invoke_response.json()
    assert data["structured_output"] is not None
    # ...
else:
    # ❌ 500 错误时仍然"通过"
    status_response = client.get(f"/api/v1/market/{agent_id}/install-status")
    assert status_response.json()["install_status"] == "installed"
```

**Required**:
```python
# 移除软通过逻辑，500 错误必须 fail
response = invoke_response
assert response.status_code == 200, \
    f"Expected 200, got {response.status_code}: {response.text}"

data = response.json()
assert data["structured_output"] is not None
assert data["structured_output"]["type"] == "third_party_response"
assert "trace_id" in data  # 验证顶层 trace_id 存在
assert data["metadata"]["agent_type"] == "third_party"
```

## 4. Acceptance Criteria

修正后的代码必须满足：

| AC | 验证方法 |
|----|----------|
| AC-1: `AgentResponse` 包含顶层 `trace_id` | `pytest` + Schema 检查 |
| AC-2: 所有错误响应使用统一格式 | `pytest` 错误响应测试 |
| AC-3: agent_id 不一致返回 400 错误 | `pytest` 边界测试 |
| AC-4: 所有测试 500 必须 fail | 运行完整测试套件 |
| AC-5: MK-008 测试仍保持 8/8 通过 | `pytest test_mk008_*.py` |

## 5. Files to Change

```
backend/app/
├── models/schemas.py              # 修改: AgentResponse 添加 trace_id
├── api/agents.py                  # 修改: 错误处理 + agent_id 校验
└── tests/
    └── test_mk008_third_party_agent.py  # 修改: 移除软通过逻辑
```

## 6. Test Evidence

修正完成后，更新证据文件：

1. **MK-006-contract-evidence.md** - 填写契约测试证据
2. **MK-006-MK-007-gateway-refactor-evidence.md** - 更正行号引用

## 7. Definition of Done

- [ ] 所有 Blocking Changes 已完成
- [ ] 所有测试通过（MK-008 保持 8/8）
- [ ] 证据文件已更新
- [ ] Architect re-review approved

---

## Priority

**P0 - 必须在继续 MK-009 前完成**
