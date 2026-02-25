# MK-006/MK-007 Architect Review Report - UPDATED

**Reviewer**: Architect-Opus
**Date**: 2026-02-25
**Status**: ⚠️ **NEEDS CORRECTIONS**

---

## Change Log
- **2026-02-25 16:00**: Initial review - APPROVED
- **2026-02-25 16:30**: Re-review after user feedback - NEEDS CORRECTIONS

---

## Critical Issues Found (Re-review)

### 1. 🔴 HIGH: Response Contract Inconsistency

**Issue**: `AgentResponse` Schema 缺少顶层 `trace_id` 字段

**Location**: `backend/app/models/schemas.py:250`

**Current Code**:
```python
class AgentResponse(BaseModel):
    request_id: str
    status: Literal["success", "error", "partial", "pending"]
    content: AgentContent
    # ❌ 缺少 trace_id 字段！
    metadata: Optional[dict[str, Any]] = None  # trace_id 被埋在这里
```

**Expected (per MK-006 spec)**:
```python
class AgentResponse(BaseModel):
    request_id: str
    trace_id: str  # ← 必须在顶层
    status: Literal["success", "error", "partial", "pending"]
    content: AgentContent
    ...
```

**Impact**: 前端/调用方无法按契约稳定解析 trace_id，违反 MK-006 规范。

---

### 2. 🔴 HIGH: Non-Uniform Error Handling

**Issue**: API 仍直接抛 `HTTPException(detail=...)`，未使用统一错误构建器

**Locations**:
- `backend/app/api/agents.py:234` - `raise HTTPException(status_code=404, detail="Agent not found")`
- `backend/app/api/agents.py:283-292` - `raise HTTPException(detail={"code": "AGENT_NOT_INSTALLED", ...})`
- `backend/app/api/agents.py:294-301` - 同上
- `backend/app/api/agents.py:304-312` - 同上
- `backend/app/api/agents.py:322-331` - 同上

**Current Code**:
```python
if not reg:
    raise HTTPException(status_code=404, detail="Agent not found")
```

**Expected (per ADR-003)**:
```python
if not reg:
    raise agent_not_found(agent_id)  # 使用 gateway/errors.py 的统一构建器
```

**Impact**: 错误响应格式不统一，违反 ADR-003 规范。

---

### 3. 🔴 HIGH: Path vs Body agent_id Not Validated

**Issue**: `/{agent_id}/invoke` 接收 path 和 body 两个 agent_id，未校验一致性

**Location**: `backend/app/api/agents.py:252`

**Current Code**:
```python
@router.post("/{agent_id}/invoke")
async def invoke_agent(
    agent_id: str,  # ← 来自 path
    request: AgentRequest,  # ← 包含 agent_id
    ...
):
    # ❌ 未校验 request.agent_id == agent_id
```

**Risk**:
- 审计混乱：日志中记录两个不同的 agent_id
- 潜在误调用：恶意请求可指定不一致的 ID

**Fix Required**:
```python
if request.agent_id != agent_id:
    raise InputError(
        code=ErrorCode.INPUT_INVALID_AGENT_ID,
        message=f"Path agent_id '{agent_id}' does not match body agent_id '{request.agent_id}'",
        details={"path_agent_id": agent_id, "body_agent_id": request.agent_id},
    )
```

---

### 4. 🟡 MEDIUM: Test "Soft Failure" Logic

**Issue**: 测试在 500 错误时仍可通过替代断言

**Location**: `backend/tests/test_mk008_third_party_agent.py:310-328`

**Current Code**:
```python
# Note: May fail with 500 due to DB issues in test environment
if invoke_response.status_code == 200:
    # 正常断言
    assert data["structured_output"] is not None
else:
    # ❌ 500 错误时仍然"通过"测试！
    status_response = client.get(f"/api/v1/market/{agent_id}/install-status")
    assert status_response.json()["install_status"] == "installed"
```

**Impact**: P0 稳定性验收要求未满足，测试可信度降低。

---

### 5. 🟡 MEDIUM: Evidence File Quality Issues

**Issue**:
1. `MK-006-contract-evidence.md` 仍是空模板
2. `MK-006-MK-007-gateway-refactor-evidence.md` 行号引用与代码不一致

**Impact**: 证据链可复核性不足。

---

## Decision

### Status: ⚠️ **NEEDS CORRECTIONS BEFORE MERGE**

MK-006/MK-007 不能视为"完全达标完成"。

### Merge Gates (必须完成才能合并)

1. **[BLOCKING]** 修复 `AgentResponse` Schema，添加顶层 `trace_id` 字段
2. **[BLOCKING]** 替换所有 `raise HTTPException` 为统一错误构建器
3. **[BLOCKING]** 添加 path/body agent_id 一致性校验
4. **[BLOCKING]** 修复测试：500 错误必须 fail，不允许"软通过"

### Non-Blocking (可在后续迭代完成)

5. 完善 MK-006 契约测试证据文件
6. 修正 evidence 文件中的行号引用

---

## Corrective Action Plan

创建 **MK-006-MK-007-HOTFIX** 任务，仅包含契约一致性和测试严谨性修正。

| 修正项 | 文件 | 改动 |
|--------|------|------|
| Schema trace_id | `models/schemas.py:250` | 添加 `trace_id: str` 字段 |
| 统一错误处理 | `api/agents.py` | 替换 5 处 `HTTPException` |
| agent_id 校验 | `api/agents.py:252` | 添加一致性校验 |
| 测试严谨性 | `tests/test_mk008_*.py` | 移除 `if status == 200` 分支 |

---

## Sign-Off (Updated)

**Architect**: ⚠️ Needs Corrections
**Reason**: Contract consistency violations found
**Next**: Assign hotfix task to dev-agent

---

## Appendix: Issue Reproduction

### A.1 trace_id 缺失验证

```bash
# 调用 API
curl -X POST /api/v1/agents/nexusops.chat/invoke \
  -H "Content-Type: application/json" \
  -d '{"request_id": "...", "agent_id": "nexusops.chat", "query": "hi"}'

# 当前响应（trace_id 被埋在 metadata 中）
{
  "request_id": "...",
  "status": "success",
  "content": {...},
  "metadata": {"trace_id": "abc123..."}  # ← 埋在这里
}

# MK-006 规范要求（trace_id 在顶层）
{
  "request_id": "...",
  "trace_id": "abc123...",  # ← 应该在顶层
  "status": "success",
  ...
}
```

### A.2 错误格式不一致验证

```python
# 当前: HTTPException 直接抛出
raise HTTPException(status_code=404, detail="Agent not found")
# FastAPI 响应: {"detail": "Agent not found"}

# ADR-003 规范: 统一格式
raise agent_not_found(agent_id)
# 应返回: {
#   "request_id": "...",
#   "trace_id": "...",
#   "status": "error",
#   "error": {"code": "AGENT_NOT_FOUND", "message": "...", "details": {...}}
# }
```
