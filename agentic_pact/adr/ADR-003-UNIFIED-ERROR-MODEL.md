# ADR-003: Gateway 采用统一错误模型与分类错误码体系

## 状态
Accepted

## 日期
2026-02-24

## 背景
MK-006 需要定义 Gateway 的错误处理机制。当前系统中：
1. 不同 API 返回的错误格式不一致
2. 错误码没有统一命名规范
3. 内置 Agent 与第三方 Agent 的错误处理分散
4. 缺乏可追踪性（无 trace_id）

为实现"可诊断错误信息"的产品目标，需要统一错误模型。

## 选项
1. **继续使用 HTTPException + 自由格式消息**
   - 优点：最小改动
   - 缺点：无法实现可诊断性，前端难以统一处理

2. **引入错误码枚举 + 简单消息**
   - 优点：比选项 1 更规范
   - 缺点：缺乏上下文信息，调试困难

3. **统一错误模型 + 分类错误码 + 结构化详情（推荐）**
   - 优点：完整可诊断性，前端可统一处理，支持国际化
   - 缺点：实现成本略高

## 决策
采用选项 3，建立统一错误模型：

### 错误响应结构
```json
{
  "request_id": "uuid",
  "trace_id": "32-hex",
  "status": "error",
  "content": { "text": "用户可读消息", "format": "plain" },
  "error": {
    "code": "CATEGORY_SUBCATEGORY_SPECIFIC",
    "message": "机器可读消息",
    "details": { "field": "value" },
    "retry_after": 5,
    "doc_url": "https://docs.nexusops.io/errors/CODE"
  }
}
```

### 错误码分类
| 类别 | 前缀 | HTTP 状态码 | 示例 |
|------|------|------------|------|
| 输入校验 | INPUT_ | 400 | INPUT_INVALID_JSON |
| 认证授权 | AUTH_ | 401/403 | AUTH_TOKEN_EXPIRED |
| Agent | AGENT_ | 404/409/422 | AGENT_NOT_FOUND |
| 执行 | EXEC_ | 500/502/504 | EXEC_TIMEOUT |
| 系统 | SYSTEM_ | 500/503 | SYSTEM_UNAVAILABLE |

### 强制规则
1. 所有错误必须经过 `gateway/errors.py` 的错误构建器
2. 所有响应必须包含 `trace_id`
3. 错误码必须符合 `^[A-Z][A-Z0-9_]{2,31}$` 格式
4. 新增错误码必须更新错误码文档

## 理由
1. **可诊断性**：details 字段提供上下文，doc_url 指向解决方案
2. **前端一致性**：统一结构便于 UI 层统一处理
3. **可追踪性**：trace_id 贯穿全链路，便于问题定位
4. **可扩展性**：分类前缀支持后续增加新错误类型
5. **国际化就绪**：code 稳定，message 可按 locale 翻译

## 影响
1. **开发**：需重构现有错误处理代码，引入错误构建器
2. **测试**：需新增错误码覆盖测试
3. **文档**：需维护错误码文档（可自动生成）
4. **前端**：需更新错误处理逻辑，利用 code 而非 message

## 实施约束
1. 禁止在业务代码中直接 `raise HTTPException(detail="...")`
2. 必须使用 `raise GatewayError(code=ErrorCode.XXX, details={})`
3. 错误码定义必须集中在 `gateway/errors.py`
4. 任何新增错误码需要 Code Review

## 代码示例

```python
# gateway/errors.py

from enum import Enum
from fastapi import HTTPException
from typing import Optional, Dict, Any

class ErrorCode(str, Enum):
    # Input errors
    INPUT_INVALID_JSON = "INPUT_INVALID_JSON"
    INPUT_SCHEMA_VIOLATION = "INPUT_SCHEMA_VIOLATION"
    INPUT_MISSING_FIELD = "INPUT_MISSING_FIELD"
    # ... 完整列表见 MK-006 规范

    @property
    def http_status(self) -> int:
        """根据错误码返回 HTTP 状态码"""
        prefix = self.value.split("_")[0]
        return {
            "INPUT": 400,
            "AUTH": 401,  # 或 403
            "AGENT": 404,  # 或 409/422
            "EXEC": 500,  # 或 502/504
            "SYSTEM": 500,  # 或 503
        }.get(prefix, 500)

class GatewayError(Exception):
    """Gateway 统一错误"""
    def __init__(
        self,
        code: ErrorCode,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None,
    ):
        self.code = code
        self.message = message or code.value.replace("_", " ").title()
        self.details = details
        self.retry_after = retry_after

def build_error_response(
    error: GatewayError,
    request_id: str,
    trace_id: str,
) -> dict:
    """构建统一错误响应"""
    return {
        "request_id": request_id,
        "trace_id": trace_id,
        "status": "error",
        "content": {
            "text": error.message,
            "format": "plain"
        },
        "error": {
            "code": error.code.value,
            "message": error.message,
            "details": error.details,
            "retry_after": error.retry_after,
            "doc_url": f"https://docs.nexusops.io/errors/{error.code.value}"
        }
    }
```

## 迁移路径
1. 阶段 1：创建 `gateway/errors.py` 和错误构建器
2. 阶段 2：新 API 使用统一错误模型
3. 阶段 3：逐步迁移现有 API 的错误处理
4. 阶段 4：移除直接 HTTPException 使用
