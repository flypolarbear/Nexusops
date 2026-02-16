# ADR-006: Agent 并发控制

## 状态
已接受 (2024-02-16)

## 背景

在多 Agent 环境中，可能出现并发问题：
- 多个 Agent 同时修改同一 DNS 记录
- 多个 Agent 同时部署到同一集群
- 多个 Agent 同时操作同一 K8s 资源

需要并发控制机制来：
- 防止数据竞争
- 保证操作原子性
- 避免资源冲突
- 确保最终一致性

## 选项

### 选项 A: 分布式锁 + 乐观锁（推荐）
- Redis 分布式锁用于互斥操作
- 乐观锁（版本号）用于检测冲突

**优点**：
- 可靠的并发控制
- 支持冲突检测
- 性能较好

**缺点**：
- 实现复杂度

### 选项 B: 数据库行锁
- 使用数据库的行级锁

**优点**：
- 实现简单

**缺点**：
- 性能较差
- 不适合跨服务锁

### 选项 C: 队列串行化
- 所有操作通过队列串行执行

**优点**：
- 简单可靠

**缺点**：
- 性能差
- 延迟高

## 决策

**采用选项 A：分布式锁（Redis）+ 乐观锁（版本号）**

## 详细设计

### 1. 并发场景分类

```typescript
// 资源类型
enum ResourceType {
  DNS_RECORD = 'dns_record',
  K8S_DEPLOYMENT = 'k8s_deployment',
  K8S_SERVICE = 'k8s_service',
  PROJECT_VERSION = 'project_version',
  AGENT_STATE = 'agent_state',
}

// 并发策略配置
interface ConcurrencyConfig {
  // 资源类型
  resource_type: ResourceType;

  // 并发策略
  strategy: 'mutex' | 'optimistic' | 'none';

  // 锁配置
  lock?: {
    ttl: number;           // 锁超时时间（毫秒）
    wait_timeout: number;  // 获取锁等待超时
    retry_interval: number; // 获取锁重试间隔
  };

  // 乐观锁配置
  optimistic?: {
    version_field: string;  // 版本字段名
    max_retries: number;    // 最大重试次数
  };
}

// 默认配置
const DEFAULT_CONCURRENCY_CONFIG: Record<ResourceType, ConcurrencyConfig> = {
  [ResourceType.DNS_RECORD]: {
    resource_type: ResourceType.DNS_RECORD,
    strategy: 'mutex',
    lock: {
      ttl: 30000,       // 30 秒
      wait_timeout: 10000,  // 等待 10 秒
      retry_interval: 100,  // 每 100ms 重试
    },
  },
  [ResourceType.K8S_DEPLOYMENT]: {
    resource_type: ResourceType.K8S_DEPLOYMENT,
    strategy: 'mutex',
    lock: {
      ttl: 60000,       // 60 秒（部署可能较慢）
      wait_timeout: 30000,
      retry_interval: 200,
    },
  },
  [ResourceType.AGENT_STATE]: {
    resource_type: ResourceType.AGENT_STATE,
    strategy: 'optimistic',
    optimistic: {
      version_field: 'version',
      max_retries: 3,
    },
  },
  [ResourceType.PROJECT_VERSION]: {
    resource_type: ResourceType.PROJECT_VERSION,
    strategy: 'optimistic',
    optimistic: {
      version_field: 'version',
      max_retries: 3,
    },
  },
  [ResourceType.K8S_SERVICE]: {
    resource_type: ResourceType.K8S_SERVICE,
    strategy: 'mutex',
    lock: {
      ttl: 30000,
      wait_timeout: 10000,
      retry_interval: 100,
    },
  },
};
```

### 2. 分布式锁实现

```typescript
// 分布式锁接口
interface DistributedLock {
  // 获取锁
  acquire(key: string, ttl: number, timeout?: number): Promise<boolean>;

  // 释放锁
  release(key: string): Promise<boolean>;

  // 延长锁
  extend(key: string, ttl: number): Promise<boolean>;

  // 检查锁
  isLocked(key: string): Promise<boolean>;
}

// Redis 实现
class RedisDistributedLock implements DistributedLock {
  private redis: RedisClient;
  private lockId: string;

  constructor(redis: RedisClient) {
    this.redis = redis;
    this.lockId = crypto.randomUUID();
  }

  async acquire(key: string, ttl: number, timeout?: number): Promise<boolean> {
    const lockKey = `lock:${key}`;
    const startTime = Date.now();
    const waitTimeout = timeout || 10000;

    while (Date.now() - startTime < waitTimeout) {
      // 尝试设置锁（使用 SET NX EX）
      const result = await this.redis.set(lockKey, this.lockId, 'NX', 'PX', ttl);

      if (result === 'OK') {
        return true;
      }

      // 等待后重试
      await this.sleep(100);
    }

    return false;
  }

  async release(key: string): Promise<boolean> {
    const lockKey = `lock:${key}`;

    // 使用 Lua 脚本确保原子性（只有锁的持有者才能释放）
    const script = `
      if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
      else
        return 0
      end
    `;

    const result = await this.redis.eval(script, 1, lockKey, this.lockId);
    return result === 1;
  }

  async extend(key: string, ttl: number): Promise<boolean> {
    const lockKey = `lock:${key}`;

    // 使用 Lua 脚本确保原子性
    const script = `
      if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("pexpire", KEYS[1], ARGV[2])
      else
        return 0
      end
    `;

    const result = await this.redis.eval(script, 1, lockKey, this.lockId, ttl);
    return result === 1;
  }

  async isLocked(key: string): Promise<boolean> {
    const lockKey = `lock:${key}`;
    const value = await this.redis.get(lockKey);
    return value !== null;
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// 锁管理器
class LockManager {
  private lock: DistributedLock;
  private activeLocks: Map<string, { acquired_at: number; ttl: number }> = new Map();
  private renewalTimers: Map<string, NodeJS.Timeout> = new Map();

  constructor(lock: DistributedLock) {
    this.lock = lock;
  }

  // 获取锁并自动续期
  async acquireWithRenewal(
    key: string,
    config: ConcurrencyConfig['lock']
  ): Promise<{ success: boolean; release: () => Promise<void> }> {
    const acquired = await this.lock.acquire(key, config!.ttl, config!.wait_timeout);

    if (!acquired) {
      return { success: false, release: () => Promise.resolve() };
    }

    // 记录活跃锁
    this.activeLocks.set(key, { acquired_at: Date.now(), ttl: config!.ttl });

    // 启动自动续期
    const renewalInterval = config!.ttl * 0.7;  // 在 70% 时续期
    const timer = setInterval(async () => {
      await this.lock.extend(key, config!.ttl);
    }, renewalInterval);

    this.renewalTimers.set(key, timer);

    // 返回释放函数
    return {
      success: true,
      release: async () => {
        // 停止续期
        const t = this.renewalTimers.get(key);
        if (t) {
          clearInterval(t);
          this.renewalTimers.delete(key);
        }

        // 释放锁
        await this.lock.release(key);
        this.activeLocks.delete(key);
      },
    };
  }

  // 获取所有活跃锁（用于监控）
  getActiveLocks(): Array<{ key: string; acquired_at: number; ttl: number }> {
    return Array.from(this.activeLocks.entries()).map(([key, value]) => ({
      key,
      ...value,
    }));
  }
}
```

### 3. 乐观锁实现

```typescript
// 乐观锁管理器
class OptimisticLockManager {
  // 带版本检查的更新
  async updateWithVersion<T>(
    resourceType: ResourceType,
    resourceId: string,
    updateFn: (current: T) => Promise<T>
  ): Promise<{ success: boolean; retries: number; result?: T }> {
    const config = DEFAULT_CONCURRENCY_CONFIG[resourceType];
    if (config.strategy !== 'optimistic' || !config.optimistic) {
      throw new Error(`Resource type ${resourceType} does not use optimistic locking`);
    }

    const { version_field, max_retries } = config.optimistic;
    let retries = 0;

    while (retries < max_retries) {
      retries++;

      // 1. 读取当前值和版本
      const current = await this.readWithVersion<T>(resourceType, resourceId);
      if (!current) {
        return { success: false, retries };
      }

      const currentVersion = (current as any)[version_field] || 0;

      // 2. 应用更新
      const updated = await updateFn(current);
      (updated as any)[version_field] = currentVersion + 1;

      // 3. 尝试写入（带版本检查）
      const written = await this.writeWithVersion(
        resourceType,
        resourceId,
        updated,
        currentVersion
      );

      if (written) {
        return { success: true, retries, result: updated };
      }

      // 版本冲突，重试
      await this.sleep(100 * retries);  // 递增等待时间
    }

    return { success: false, retries };
  }

  private async readWithVersion<T>(
    resourceType: ResourceType,
    resourceId: string
  ): Promise<T | null> {
    // 从数据库读取
    const result = await db.query(
      `SELECT * FROM ${this.getTableName(resourceType)} WHERE id = $1`,
      [resourceId]
    );
    return result.rows[0] || null;
  }

  private async writeWithVersion<T>(
    resourceType: ResourceType,
    resourceId: string,
    data: T,
    expectedVersion: number
  ): Promise<boolean> {
    const config = DEFAULT_CONCURRENCY_CONFIG[resourceType];
    const versionField = config.optimistic!.version_field;

    // 使用 WHERE 子句检查版本
    const result = await db.query(
      `UPDATE ${this.getTableName(resourceType)}
       SET data = $1, ${versionField} = $2, updated_at = NOW()
       WHERE id = $3 AND ${versionField} = $4`,
      [JSON.stringify(data), (data as any)[versionField], resourceId, expectedVersion]
    );

    return result.rowCount > 0;
  }

  private getTableName(resourceType: ResourceType): string {
    const tableMap: Record<ResourceType, string> = {
      [ResourceType.DNS_RECORD]: 'dns_records',
      [ResourceType.K8S_DEPLOYMENT]: 'k8s_deployments',
      [ResourceType.K8S_SERVICE]: 'k8s_services',
      [ResourceType.PROJECT_VERSION]: 'project_versions',
      [ResourceType.AGENT_STATE]: 'agent_states',
    };
    return tableMap[resourceType];
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

### 4. 并发控制器

```typescript
// 并发控制器
class ConcurrencyController {
  private lockManager: LockManager;
  private optimisticManager: OptimisticLockManager;

  constructor(redis: RedisClient) {
    const lock = new RedisDistributedLock(redis);
    this.lockManager = new LockManager(lock);
    this.optimisticManager = new OptimisticLockManager();
  }

  // 执行受保护的操作
  async executeProtected<T>(
    resourceType: ResourceType,
    resourceId: string,
    operation: () => Promise<T>
  ): Promise<T> {
    const config = DEFAULT_CONCURRENCY_CONFIG[resourceType];

    switch (config.strategy) {
      case 'mutex':
        return this.executeWithMutex(resourceType, resourceId, operation, config);

      case 'optimistic':
        return this.executeWithOptimistic(resourceType, resourceId, operation, config);

      case 'none':
      default:
        return operation();
    }
  }

  private async executeWithMutex<T>(
    resourceType: ResourceType,
    resourceId: string,
    operation: () => Promise<T>,
    config: ConcurrencyConfig
  ): Promise<T> {
    const lockKey = `${resourceType}:${resourceId}`;

    const { success, release } = await this.lockManager.acquireWithRenewal(
      lockKey,
      config.lock!
    );

    if (!success) {
      throw new ConcurrencyError(
        'LOCK_ACQUIRE_FAILED',
        `Failed to acquire lock for ${resourceType}:${resourceId}`
      );
    }

    try {
      return await operation();
    } finally {
      await release();
    }
  }

  private async executeWithOptimistic<T>(
    resourceType: ResourceType,
    resourceId: string,
    operation: () => Promise<T>,
    config: ConcurrencyConfig
  ): Promise<T> {
    const result = await this.optimisticManager.updateWithVersion(
      resourceType,
      resourceId,
      async (current) => {
        // 执行操作并返回更新后的数据
        const result = await operation();
        return { ...current, last_operation_result: result };
      }
    );

    if (!result.success) {
      throw new ConcurrencyError(
        'OPTIMISTIC_LOCK_CONFLICT',
        `Version conflict for ${resourceType}:${resourceId} after ${result.retries} retries`
      );
    }

    return result.result!.last_operation_result;
  }
}

// 并发错误
class ConcurrencyError extends Error {
  constructor(
    public code: 'LOCK_ACQUIRE_FAILED' | 'LOCK_TIMEOUT' | 'OPTIMISTIC_LOCK_CONFLICT',
    message: string
  ) {
    super(message);
    this.name = 'ConcurrencyError';
  }
}
```

### 5. Agent 集成

```typescript
// Agent 基类中集成并发控制
abstract class BaseAgent {
  protected concurrencyController: ConcurrencyController;

  constructor() {
    this.concurrencyController = new ConcurrencyController(getRedisClient());
  }

  // 受保护的操作执行
  protected async executeProtected<T>(
    resourceType: ResourceType,
    resourceId: string,
    operation: () => Promise<T>
  ): Promise<T> {
    return this.concurrencyController.executeProtected(resourceType, resourceId, operation);
  }
}

// DNS Agent 示例
class DNSAgent extends BaseAgent {
  async createDNSRecord(params: DNSRecordParams): Promise<DNSRecord> {
    // 使用分布式锁保护 DNS 记录操作
    return this.executeProtected(
      ResourceType.DNS_RECORD,
      `${params.zone_id}:${params.name}`,
      async () => {
        // 实际创建逻辑
        return this.cloudflare.createRecord(params);
      }
    );
  }

  async updateDNSRecord(recordId: string, params: Partial<DNSRecordParams>): Promise<DNSRecord> {
    return this.executeProtected(
      ResourceType.DNS_RECORD,
      recordId,
      async () => {
        return this.cloudflare.updateRecord(recordId, params);
      }
    );
  }
}

// K8s Agent 示例
class K8sAgent extends BaseAgent {
  async deployManifest(manifest: K8sManifest): Promise<DeployResult> {
    // 锁定部署目标
    return this.executeProtected(
      ResourceType.K8S_DEPLOYMENT,
      `${manifest.namespace}:${manifest.name}`,
      async () => {
        return this.k8sClient.apply(manifest);
      }
    );
  }
}
```

### 6. 死锁检测和预防

```typescript
// 死锁检测器
class DeadlockDetector {
  private waitGraph: Map<string, Set<string>> = new Map();

  // 记录等待关系
  recordWait(waiter: string, waitingFor: string): void {
    if (!this.waitGraph.has(waiter)) {
      this.waitGraph.set(waiter, new Set());
    }
    this.waitGraph.get(waiter)!.add(waitingFor);

    // 检测死锁
    if (this.detectDeadlock(waiter)) {
      // 清除等待
      this.waitGraph.delete(waiter);
      throw new ConcurrencyError(
        'DEADLOCK_DETECTED',
        `Deadlock detected: ${waiter} -> ${waitingFor}`
      );
    }
  }

  // 清除等待关系
  clearWait(waiter: string): void {
    this.waitGraph.delete(waiter);
  }

  // 检测死锁（使用 DFS）
  private detectDeadlock(start: string): boolean {
    const visited = new Set<string>();
    const recursionStack = new Set<string>();

    const dfs = (node: string): boolean => {
      visited.add(node);
      recursionStack.add(node);

      const neighbors = this.waitGraph.get(node);
      if (neighbors) {
        for (const neighbor of neighbors) {
          if (!visited.has(neighbor)) {
            if (dfs(neighbor)) return true;
          } else if (recursionStack.has(neighbor)) {
            return true;  // 发现环
          }
        }
      }

      recursionStack.delete(node);
      return false;
    };

    return dfs(start);
  }
}

// 锁顺序规则（防止死锁）
const LOCK_ORDER: ResourceType[] = [
  ResourceType.PROJECT_VERSION,
  ResourceType.DNS_RECORD,
  ResourceType.K8S_DEPLOYMENT,
  ResourceType.K8S_SERVICE,
  ResourceType.AGENT_STATE,
];

// 验证锁顺序
function validateLockOrder(
  heldLocks: ResourceType[],
  requestedLock: ResourceType
): boolean {
  if (heldLocks.length === 0) return true;

  const lastHeldOrder = LOCK_ORDER.indexOf(heldLocks[heldLocks.length - 1]);
  const requestedOrder = LOCK_ORDER.indexOf(requestedLock);

  return requestedOrder > lastHeldOrder;
}
```

## 后果

### 正面
- 可靠的并发控制
- 防止数据竞争
- 死锁检测和预防
- 灵活的策略选择

### 负面
- 增加 Redis 依赖
- 实现复杂度
- 性能开销

## 实现

1. **Phase 3.5**: 实现基础分布式锁
2. **Phase 4**: 实现乐观锁和死锁检测
3. **Phase 4**: Agent 集成并发控制
