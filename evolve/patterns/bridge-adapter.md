# Bridge 适配器模式

## 问题描述

Agent 需要调用外部系统（ArgoCD、Kubernetes、云服务等），如何解耦连接配置和执行逻辑？

## 解决方案

使用 Bridge 适配器模式，分为三层：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Bridge Config (配置层)                              │
│   管理外部系统连接配置                                                        │
│   • 连接参数 (API URL, 超时等)                                               │
│   • 认证配置 (Token, 证书等)                                                  │
│   • 元数据 (标签, 环境等)                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Bridge Adapter (适配层)                             │
│   转化 Tool Call 为实际 API 调用                                             │
│   • 参数映射                                                                 │
│   • 认证注入                                                                 │
│   • 响应标准化                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          External System (外部系统)                          │
│   ArgoCD / Kubernetes / AWS / HTTP API                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 代码示例

```python
from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum

class BridgeType(Enum):
    ARGOCD = "argocd"
    KUBERNETES = "kubernetes"
    HTTP = "http"

@dataclass
class BridgeConfig:
    """外部系统连接配置"""
    id: str
    type: BridgeType
    connection_params: Dict[str, Any]  # API URL, timeout 等
    auth_config: Dict[str, Any]        # 加密存储
    metadata: Dict[str, Any]           # 标签、环境等

class BridgeAdapter:
    """适配器基类"""
    
    def __init__(self, config: BridgeConfig):
        self.config = config
    
    async def execute(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行操作"""
        raise NotImplementedError

class ArgoCDBridgeAdapter(BridgeAdapter):
    """ArgoCD 适配器"""
    
    async def execute(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        # 1. 注入认证
        headers = self._build_auth_headers()
        
        # 2. 构建请求
        url = f"{self.config.connection_params['api_url']}/api/v1/applications/{params['app_name']}"
        
        # 3. 执行操作
        if operation == "sync":
            response = await self._http_post(f"{url}/sync", headers=headers)
        elif operation == "get":
            response = await self._http_get(url, headers=headers)
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        # 4. 标准化响应
        return self._normalize_response(response)
    
    def _build_auth_headers(self) -> Dict[str, str]:
        """注入认证信息"""
        token = self._decrypt_token(self.config.auth_config["token"])
        return {"Authorization": f"Bearer {token}"}
    
    def _normalize_response(self, response: Dict) -> Dict[str, Any]:
        """标准化响应格式"""
        return {
            "success": True,
            "data": response,
            "bridge_id": self.config.id
        }
```

### 使用示例

```python
# 1. 创建 Bridge 配置
bridge_config = BridgeConfig(
    id="argocd-production",
    type=BridgeType.ARGOCD,
    connection_params={
        "api_url": "https://argocd.example.com",
        "timeout_ms": 30000
    },
    auth_config={
        "token": "encrypted:xxxxx"  # 加密存储
    },
    metadata={
        "environment": "production",
        "cluster": "us-east-1"
    }
)

# 2. 创建适配器
adapter = BridgeAdapterFactory.create(bridge_config)

# 3. 执行操作
result = await adapter.execute("sync", {"app_name": "api-gateway"})

# 4. 处理结果
if result["success"]:
    print(f"Sync succeeded: {result['data']}")
else:
    print(f"Sync failed: {result['error']}")
```

## 错误处理

```python
class BridgeError(Exception):
    """Bridge 执行错误"""
    def __init__(self, code: str, message: str, retry_after: Optional[int] = None):
        self.code = code
        self.message = message
        self.retry_after = retry_after

async def execute_with_retry(adapter: BridgeAdapter, operation: str, params: Dict, max_retries: int = 3):
    """带重试的执行"""
    for attempt in range(max_retries):
        try:
            return await adapter.execute(operation, params)
        except BridgeError as e:
            if e.retry_after and attempt < max_retries - 1:
                await asyncio.sleep(e.retry_after)
                continue
            raise
```

## 注意事项

- ✅ 敏感信息（Token）加密存储
- ✅ 统一的错误处理和重试机制
- ✅ 响应格式标准化
- ✅ 支持健康检查
- ✅ 支持多种 Bridge 类型
- ❌ 不要在代码中硬编码连接信息
- ❌ 不要明文存储认证凭据
- ❌ 不要忽略外部系统的错误响应
