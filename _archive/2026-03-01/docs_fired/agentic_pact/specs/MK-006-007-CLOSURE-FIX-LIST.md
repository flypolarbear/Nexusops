# MK-006/007 Contract Closure Fix List

**Created**: 2026-02-25
**Status**: COMPLETED
**Priority**: P0 (Blocking MK-009)
**Completed**: 2026-02-25

---

## Issues Fixed

### 1. [DONE] Unified Error Response Structure
**Problem**: Some endpoints still use `HTTPException(detail=...)` instead of ADR-003 error model.

**Fix Applied**: All HTTPException calls now use structured error format with code, message, trace_id.

---

### 2. [DONE] Top-level trace_id in Responses
**Problem**: Response model should include trace_id at top level for tracing.

**Fix Applied**: InvokeResponse includes trace_id at top level and in metadata.

---

### 3. [DONE] agent_id Consistency Validation
**Problem**: invoke endpoint doesn't validate path agent_id matches body agent_id.

**Fix Applied**: Added validation in `backend/app/api/agents.py:invoke_agent()`:
- Returns 400 with `INPUT_AGENT_ID_MISMATCH` code when mismatch detected

---

### 4. [DONE] Remove Test Pass-on-500 Branches
**Problem**: Tests accept 500 as valid response, reducing verification credibility.

**Fix Applied**:
- `test_mk008_third_party_agent.py`: Removed 500 branches, strict 200 checks
- `test_mk006_mk007_p0.py`: Removed 500 from all acceptable codes
- All 25 tests pass with stricter validation

---

### 5. [DONE] Fill Empty Evidence File
**Problem**: `MK-006-contract-evidence.md` is empty template.

**Fix Applied**: Filled with 346 lines of actual test evidence including:
- Test execution results
- Request/Response samples
- Trace IDs
- Error codes implemented

---

## Verification Results

- [x] All tests pass without 500 branches (25 passed in 3.50s)
- [x] Error responses follow ADR-003 format
- [x] All responses include trace_id
- [x] agent_id mismatch returns 400, not 500

---

## Commits

1. `8912ad5e` - feat(pact): add git push and agent team rules to PACT.md
2. `4ce2868c` - fix(tests): remove 500 pass branches from test assertions

---

## Next Steps

MK-006/007 收口完成，可以放行 MK-009。
