# 连接池模式

## 问题描述

频繁创建 HTTP 连接开销大，应该复用连接。

## 解决方案

### HTTP 连接池

```python
import httpx

class MyAgentHandler(BaseAgentHandler):
    def __init__(self):
        # 共享客户端，带连接池
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=5.0,    # 连接超时
                read=30.0,       # 读取超时
                write=10.0,      # 写入超时
                pool=5.0         # 池等待超时
            ),
            limits=httpx.Limits(
                max_connections=100,           # 最大连接数
                max_keepalive_connections=20,   # 保活连接数
                keepalive_expiry=30.0           # 保活过期时间
            )
        )

    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        response = await self._client.get("https://api.example.com/data")
        return self._success(text=response.text)

    async def close(self):
        await self._client.aclose()  # 应用关闭时调用
```

### 数据库连接池

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",
    pool_size=10,           # 连接池大小
    max_overflow=20,        # 最大溢出连接
    pool_pre_ping=True,     # 连接前检查
    pool_recycle=3600       # 连接回收时间（秒）
)

async def get_session() -> AsyncSession:
    async with AsyncSession(engine) as session:
        yield session
```

### Redis 连接

```python
import redis.asyncio as redis

# 全局连接池
_redis_pool = None

async def get_redis() -> redis.Redis:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = redis.ConnectionPool.from_url(
            "redis://localhost:6379/0",
            max_connections=50
        )
    return redis.Redis(connection_pool=_redis_pool)
```

## 注意事项

- ✅ 在应用启动时创建连接池
- ✅ 在应用关闭时释放连接
- ✅ 设置合理的超时时间
- ✅ 使用 pool_pre_ping 检测坏连接
- ❌ 不要在每次请求时创建新客户端
- ❌ 不要忘记在关闭时释放资源
