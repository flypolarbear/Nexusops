# MK-006/007 Contract Closure Fix List

**Created**: 2026-02-25
**Status**: IN PROGRESS
**Priority**: P0 (Blocking MK-009)

---

## Issues to Fix

### 1. Unified Error Response Structure
**Problem**: Some endpoints still use `HTTPException(detail=...)` instead of ADR-003 error model.

**Location**: `backend/app/api/agents.py:240, 294, 304, 322`

**Fix**: Convert all HTTPException to use unified error structure:
```python
# Before:
raise HTTPException(status_code=404, detail="Agent not found")

# After:
raise HTTPException(
    status_code=404,
    detail={
        "code": "AGENT_NOT_FOUND",
        "message": "Agent not found",
        "trace_id": trace_id,
    }
)
```

---

### 2. Top-level trace_id in Responses
**Problem**: Response model should include trace_id at top level for tracing.

**Location**: `backend/app/gateway/response.py`, `backend/app/models/schemas.py`

**Fix**: Ensure all responses include trace_id:
- InvokeResponse.model_dump() includes trace_id
- Error responses include trace_id

---

### 3. agent_id Consistency Validation
**Problem**: invoke endpoint doesn't validate path agent_id matches body agent_id.

**Location**: `backend/app/api/agents.py:invoke_agent()`

**Fix**: Add validation:
```python
if request.agent_id != agent_id:
    raise HTTPException(
        status_code=400,
        detail={
            "code": "INPUT_AGENT_ID_MISMATCH",
            "message": f"Path agent_id '{agent_id}' does not match body agent_id '{request.agent_id}'",
            "trace_id": trace_id,
        }
    )
```

---

### 4. Remove Test Pass-on-500 Branches
**Problem**: Tests accept 500 as valid response, reducing verification credibility.

**Location**:
- `backend/tests/test_mk008_third_party_agent.py:165-166`
- `backend/tests/test_mk006_mk007_p0.py:97, 114, 135, 213, 249, 268, 348`

**Fix**: Remove 500 from acceptable status codes, fix underlying issues instead.

---

### 5. Fill Empty Evidence File
**Problem**: `MK-006-contract-evidence.md` is empty template.

**Location**: `agentic_pact/evidence/PRD-001/MK-006-contract-evidence.md`

**Fix**: Fill with actual test evidence:
- Request/Response samples
- Trace IDs
- Pass/Fail results

---

## Implementation Order

1. [x] Fix #1: Unified error responses
2. [x] Fix #2: Top-level trace_id
3. [x] Fix #3: agent_id validation
4. [x] Fix #4: Remove 500 pass branches
5. [x] Fix #5: Fill evidence file

---

## Verification

After fixes:
- [ ] All tests pass without 500 branches
- [ ] Error responses follow ADR-003 format
- [ ] All responses include trace_id
- [ ] agent_id mismatch returns 400, not 500
