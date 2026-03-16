# 缓存策略

## 问题描述

重复查询应该缓存，减少延迟和外部服务压力。

## 解决方案

### 响应缓存

```python
import hashlib
from functools import lru_cache

class CachedHandler(BaseAgentHandler):
    def __init__(self):
        self._cache_ttl = 300  # 5 分钟

    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        # 构建缓存键
        cache_key = self._build_cache_key(request)
        
        # 尝试从缓存获取
        cached = await self._get_cached(cache_key)
        if cached:
            cached.metadata["cache_hit"] = True
            return cached
        
        # 处理并缓存
        result = await self._process(request)
        await self._set_cached(cache_key, result)
        return result

    def _build_cache_key(self, request: ExecutorRequest) -> str:
        key_data = f"{request.query}:{request.request_context}"
        return hashlib.md5(key_data.encode()).hexdigest()
```

### Redis 缓存

```python
import redis.asyncio as redis
import json

class RedisCache:
    def __init__(self, url: str):
        self._redis = redis.from_url(url)

    async def get(self, key: str) -> dict | None:
        data = await self._redis.get(key)
        return json.loads(data) if data else None

    async def set(self, key: str, value: dict, ttl: int = 300):
        await self._redis.setex(key, ttl, json.dumps(value))

    async def delete(self, key: str):
        await self._redis.delete(key)

# 在 Agent 中使用
class CachedAgent(BaseAgentHandler):
    def __init__(self, cache: RedisCache):
        self._cache = cache

    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        cache_key = f"agent:{self.agent_id}:{hash(request.query)}"
        
        cached = await self._cache.get(cache_key)
        if cached:
            return ExecutorResult(**cached)
        
        result = await self._process(request)
        await self._cache.set(cache_key, result.model_dump())
        return result
```

### pre_execute Hook 缓存

```python
async def pre_execute(self, request: ExecutorRequest) -> ExecutorResult | None:
    cache_key = self._build_cache_key(request)
    cached = await self._cache.get(cache_key)
    
    if cached:
        # 返回缓存结果，跳过 execute()
        return ExecutorResult(
            success=True,
            content={"text": cached, "format": "markdown"},
            metadata={"cache_hit": True}
        )
    
    return None  # 继续执行
```

## 注意事项

- ✅ 为可缓存内容设置合理的 TTL
- ✅ 使用 trace_id 作为缓存键的一部分
- ✅ 在 metadata 中标记 cache_hit
- ❌ 不要缓存包含敏感信息的响应
- ❌ 不要缓存用户特定的个性化内容
