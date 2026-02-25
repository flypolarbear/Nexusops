# MK-008 Architect Review Report

**Reviewer**: Architect-Opus
**Date**: 2026-02-25
**Task**: MK-008 - 第三方 Agent 最小闭环（注册-安装-调用-拒绝）
**Status**: ✅ **APPROVED WITH MINOR NOTES**

---

## Executive Summary

MK-008 实现已完成并通过所有 8 个测试用例。实现符合 PRD-001 规范要求，核心流程完整。有以下 2 个轻微问题需要后续迭代处理，但不阻塞验收通过。

---

## 1. Specification Compliance Check

### 1.1 PRD-001 Requirements vs Implementation

| Requirement | Status | Evidence |
|-------------|--------|----------|
| RG-T01: 注册合法 Manifest 成功 | ✅ PASS | `test_register_valid_manifest()` |
| RG-T02: 注册非法 Manifest 失败并返回字段级错误 | ✅ PASS | `test_register_invalid_manifest_missing_required()` |
| RG-T03: 安装已注册 Agent 成功并可调用 | ✅ PASS | `test_install_and_invoke_agent()` |
| RG-T04: 下线 Agent 后调用被拒绝 | ✅ PASS | `test_uninstall_then_invoke_rejected()` |
| MK-008: 安装与启停状态管理 | ✅ PASS | `test_disable_then_invoke_rejected()`, `test_enable_disabled_agent()` |
| MK-008: 调用并返回结构化输出 | ✅ PASS | `test_invoke_returns_structured_output()` |
| MK-008: 未安装时调用拒绝 | ✅ PASS | `test_install_and_invoke_agent()` (Step 3) |
| MK-008: 禁用时调用拒绝 | ✅ PASS | `test_disable_then_invoke_rejected()` |

### 1.2 MK-006/MK-007 Contract Compliance

| Contract Requirement | Status | Notes |
|---------------------|--------|-------|
| trace_id in all responses | ✅ PASS | `agents.py:346` 生成 UUID 作为 trace_id |
| Error code format `^[A-Z][A-Z0-9_]{2,31}$` | ✅ PASS | `AGENT_NOT_INSTALLED`, `AGENT_DISABLED` 符合规范 |
| AgentResponse structure | ✅ PASS | 包含 status, content, structured_output, metadata, error |
| Request/Response Schema | ✅ PASS | 符合 MK-006 定义的 JSON Schema |

---

## 2. Code Review

### 2.1 Architecture Alignment

**ADR-001 (FastAPI 单体内核 + 可插拔执行层)**:
- ✅ 使用 FastAPI 路由实现 API
- ✅ 执行器分离：`execute_third_party_agent()` 实现第三方执行器
- ⚠️ 注意：尚未完全按 MK-007 的 `ExecutorRouter` 模式重构，但当前实现可接受

**ADR-002 (分阶段安全治理)**:
- ✅ 阶段 1：检查安装状态（`AGENT_NOT_INSTALLED`）
- ✅ 支持启用/禁用状态
- ⚠️ 注意：当前使用 `anonymous` 作为 installed_by，需在后续版本集成真实用户认证

### 2.2 Module Boundary Review

| Boundary | Status | Finding |
|----------|--------|---------|
| `api/agents.py` → `stores/agent_store.py` | ✅ OK | 通过导入函数访问共享存储 |
| `api/agent_market.py` → `stores/agent_store.py` | ✅ OK | 使用相同存储模块 |
| Error handling centralization | ⚠️ NOTE | 部分使用 `HTTPException`，应迁移到 `gateway/errors.py` |

### 2.3 Code Quality

**Positive findings**:
- ✅ 清晰的函数命名（`install_agent`, `uninstall_agent`, `enable_agent`, `disable_agent`）
- ✅ Enum 类型定义状态（`InstallStatus`）
- ✅ 测试覆盖率高（8/8 通过）
- ✅ 详细的文档字符串

**Minor concerns**:
1. **内存存储** (`agent_store.py:14`): 使用内存存储，重启丢失数据。已在 evidence 中标注为 Risk。
2. **TODO 注释**: 存在多处 `# TODO: get from auth`，需后续处理。
3. **错误响应格式不一致**:
   ```python
   # 当前实现
   raise HTTPException(status_code=403, detail={"code": "...", "message": "..."})
   ```
   应在后续迭代中使用 `gateway/errors.py` 的统一错误构建器。

---

## 3. Test Evidence Review

### 3.1 Test Coverage

| Test Suite | Tests | Passed | Coverage |
|------------|-------|--------|----------|
| `TestAgentRegistration` | 2 | 2 | 注册场景 |
| `TestAgentInstallFlow` | 2 | 2 | 安装流程 |
| `TestAgentEnableDisable` | 2 | 2 | 启用/禁用 |
| `TestStructuredOutput` | 1 | 1 | 结构化输出 |
| `TestInstalledAgentsList` | 1 | 1 | 列表查询 |

### 3.2 Evidence Completeness

Evidence 文件 (`MK-008-third-party-agent-evidence.md`) 包含：
- ✅ 环境信息
- ✅ API 端点列表
- ✅ 请求/响应样例
- ✅ 测试结果汇总
- ✅ Trace IDs
- ✅ 风险与 TODO 标注

---

## 4. Risks Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| 内存存储重启丢失 | **Medium** | 已在 evidence 中标注，生产环境需迁移到数据库 |
| 无 API 认证保护 | **Medium** | 阶段 1 可接受，阶段 2 需实现（ADR-002） |
| Mock 执行器非真实 HTTP | **Low** | MVP 可接受，真实调用在后续迭代 |
| 错误处理未完全统一 | **Low** | 需迁移到 `gateway/errors.py`，不阻塞当前验收 |

---

## 5. Decision

### 5.1 Approval Status

**✅ APPROVED**

MK-008 实现已满足 PRD-001 验收标准：
- 第三方 Agent 注册功能完整
- 安装/卸载/启用/禁用状态管理完整
- 调用时正确检查安装状态
- 未安装/禁用时正确拒绝调用
- 返回符合规范的响应和 trace_id

### 5.2 Conditions for Merge

1. **必须**: 所有测试用例保持通过（8/8）
2. **建议**: 下个 Sprint 迁移内存存储到数据库
3. **建议**: 下个 Sprint 集成 API 认证
4. **建议**: 与 MK-006/MK-007 重构时统一错误处理

### 5.3 Next Steps

| Priority | Task | Owner |
|----------|------|-------|
| P0 | 继续推进 MK-009（内置 Agent 批次验收） | dev-agent |
| P1 | 迁移内存存储到数据库 | dev-agent |
| P1 | 集成 API 认证（ADR-002 阶段 2） | dev-agent |
| P2 | 重构错误处理使用 `gateway/errors.py` | dev-agent |

---

## 6. Sign-off

**Architect**: ✅ Approved
**Date**: 2026-02-25

---

## Appendix: Detailed Findings

### A. API Contract Validation

#### Install Request/Response
```json
POST /api/v1/market/{agent_id}/install
→ 200 OK {
    "agent_id": "...",
    "name": "...",
    "install_status": "installed",
    "installed_at": "2026-02-25T...",
    "message": "Agent installed successfully"
}
```
✅ 符合预期

#### Invoke with Error Response
```json
POST /api/v1/agents/{agent_id}/invoke
→ 403 Forbidden {
    "detail": {
        "code": "AGENT_NOT_INSTALLED",
        "message": "...",
        "trace_id": "..."
    }
}
```
✅ 符合 MK-006 错误码规范

### B. Trace ID Verification

检查 `agents.py:345-346`:
```python
start_time = datetime.utcnow()
trace_id = str(uuid.uuid4())
```
✅ trace_id 在请求入口处生成，符合 MK-006 规范

### C. Structured Output Verification

检查 `execute_third_party_mock()` (agents.py:758-810):
```python
structured_output={
    "type": "third_party_response",
    "agent_id": agent_id,
    "query": request.query,
    "processed": True,
}
```
✅ 结构化输出格式正确
