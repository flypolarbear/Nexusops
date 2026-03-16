# 安全实践模式

## 问题描述

确保 Agent 开发的安全性。

## 解决方案

### API 密钥管理

```python
import os

# ✅ 推荐: 从环境变量加载
api_key = os.environ.get("NEXUSOPS_API_KEY")

# ❌ 避免: 硬编码
# api_key = "sk-xxx"  # 永远不要这样做!
```

### Token 管理

```python
class TokenManager:
    def __init__(self, refresh_threshold_seconds: int = 300):
        self._token = None
        self._expires_at = None
        self._refresh_threshold = refresh_threshold_seconds

    async def get_token(self) -> str:
        if self._should_refresh():
            await self._refresh_token()
        return self._token

    def _should_refresh(self) -> bool:
        if not self._token or not self._expires_at:
            return True
        return time.time() > (self._expires_at - self._refresh_threshold)
```

### 输入验证

```python
from pydantic import BaseModel, validator, constr

class DeploymentRequest(BaseModel):
    codename: constr(min_length=1, max_length=100, regex=r"^[a-zA-Z0-9_-]+$")
    region: constr(min_length=1, max_length=50)
    replicas: int

    @validator("replicas")
    def validate_replicas(cls, v):
        if v < 1 or v > 100:
            raise ValueError("Replicas must be between 1 and 100")
        return v
```

### 敏感数据脱敏

```python
# ✅ 好: 日志前脱敏
def safe_log(data: dict) -> dict:
    sensitive_keys = {"password", "api_key", "token", "secret"}
    return {
        k: "***MASKED***" if k in sensitive_keys else v
        for k, v in data.items()
    }

logger.info("Request data", extra={"data": safe_log(request_data)})

# ✅ 好: 部分显示
def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    if len(data) <= visible_chars:
        return "*" * len(data)
    return "*" * (len(data) - visible_chars) + data[-visible_chars:]

# 示例
mask_sensitive_data("sk-1234567890")  # "*******7890"
```

### 请求白名单

```python
ALLOWED_DOMAINS = {
    "api.kubernetes.io",
    "api.aws.amazon.com",
    "logs.example.com"
}

def is_allowed_url(url: str) -> bool:
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return parsed.hostname in ALLOWED_DOMAINS

async def safe_request(url: str, **kwargs):
    if not is_allowed_url(url):
        raise ValueError(f"URL not in allowlist: {url}")
    async with httpx.AsyncClient() as client:
        return await client.get(url, **kwargs)
```

### 审计日志

```python
import structlog

audit_logger = structlog.get_logger("audit")

async def log_audit_event(
    action: str,
    user_id: str,
    resource_type: str,
    resource_id: str,
    details: dict = None
):
    await audit_logger.ainfo(
        "audit_event",
        action=action,
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        timestamp=datetime.utcnow().isoformat()
    )

# 使用
await log_audit_event(
    action="deploy",
    user_id="user-123",
    resource_type="deployment",
    resource_id="deploy-456",
    details={"region": "us-east", "version": "v1.2.3"}
)
```

## 安全检查清单

### 开发阶段
- [ ] 所有输入都经过验证
- [ ] 敏感信息从环境变量加载
- [ ] 使用 HTTPS 进行外部通信
- [ ] 设置请求超时
- [ ] 错误消息不暴露内部细节

### 部署阶段
- [ ] 密钥存储在密钥管理器中
- [ ] 配置网络策略
- [ ] 启用限流
- [ ] 日志不包含敏感数据
