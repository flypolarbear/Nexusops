# 常见错误

开发中应该避免的问题。

## 类型安全

### 使用 any

```python
# ❌ 错误
data: Any = fetch_data()
result = data.something  # 无类型检查

# ✅ 正确
from pydantic import BaseModel

class Data(BaseModel):
    something: str

data = Data(**fetch_data())
result = data.something  # 类型安全
```

```typescript
// ❌ 错误
const data: any = fetchData();

// ✅ 正确
interface Data {
  something: string;
}
const data: Data = fetchData();
```

### 忽略类型错误

```python
# ❌ 错误
result = process(data)  # type: ignore

# ✅ 正确: 修复类型定义
def process(data: dict) -> Result:
    ...
```

## 异步处理

### 阻塞事件循环

```python
# ❌ 错误
import time
time.sleep(5)  # 阻塞!

# ✅ 正确
import asyncio
await asyncio.sleep(5)  # 非阻塞
```

### 同步 I/O

```python
# ❌ 错误
import requests
response = requests.get(url)  # 同步!

# ✅ 正确
import httpx
async with httpx.AsyncClient() as client:
    response = await client.get(url)  # 异步
```

## 错误处理

### 空 catch 块

```python
# ❌ 错误
try:
    do_something()
except Exception:
    pass  # 吞掉错误!

# ✅ 正确
try:
    do_something()
except SpecificError as e:
    logger.error("Failed to do something", exc_info=True)
    raise
```

### 暴露内部错误

```python
# ❌ 错误
except DatabaseError as e:
    return self._error(message=f"Database error: {e}")  # 暴露内部细节!

# ✅ 正确
except DatabaseError as e:
    logger.error("Database error", exc_info=True)
    return self._error(
        code="SYSTEM_INTERNAL_ERROR",
        message="An internal error occurred. Please try again."
    )
```

## 资源管理

### 未释放连接

```python
# ❌ 错误
async def fetch():
    client = httpx.AsyncClient()
    return await client.get(url)  # 客户端未关闭!

# ✅ 正确
async def fetch():
    async with httpx.AsyncClient() as client:
        return await client.get(url)
```

### 未设置超时

```python
# ❌ 错误
client = httpx.AsyncClient()  # 无超时!

# ✅ 正确
client = httpx.AsyncClient(
    timeout=httpx.Timeout(connect=5.0, read=30.0, write=10.0)
)
```

## 安全问题

### 硬编码密钥

```python
# ❌ 错误
API_KEY = "sk-xxx"  # 永远不要这样做!

# ✅ 正确
import os
API_KEY = os.environ["API_KEY"]
```

### 记录敏感信息

```python
# ❌ 错误
logger.info(f"User logged in with password: {password}")

# ✅ 正确
logger.info(f"User logged in: {user_id}")
```

## 性能问题

### N+1 查询

```python
# ❌ 错误
for item in items:
    detail = await get_detail(item.id)  # N 次查询!

# ✅ 正确
details = await get_details([item.id for item in items])  # 1 次查询
```

### 无缓存重复查询

```python
# ❌ 错误
async def get_config():
    return await fetch_config()  # 每次都请求!

# ✅ 正确
_config_cache = None

async def get_config():
    global _config_cache
    if _config_cache is None:
        _config_cache = await fetch_config()
    return _config_cache
```
