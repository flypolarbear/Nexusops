# ADR-004: Agent 状态管理

## 状态
已接受 (2024-02-16)

## 背景

有状态的 Agent 需要在多次调用之间保持状态，例如：
- DNS Agent 创建的域名记录
- 部署 Agent 创建的资源
- 工作流 Agent 的执行上下文

状态管理需要解决：
- 状态存储位置
- 状态生命周期
- 状态与 NexusOps 资源的关联
- 多 Agent 间状态共享

## 选项

### 选项 A: PostgreSQL + Redis（推荐）
- PostgreSQL 持久化状态
- Redis 缓存热数据

**优点**：
- 利用现有基础设施
- 可靠的持久化
- 灵活的查询能力

**缺点**：
- 需要维护两个存储

### 选项 B: 纯 Redis
- 所有状态存储在 Redis

**优点**：
- 高性能
- 简单

**缺点**：
- 数据持久化风险
- 查询能力有限

### 选项 C: 独立状态服务
- 专门的状态管理服务

**优点**：
- 职责清晰

**缺点**：
- 增加服务复杂度
- 运维成本高

## 决策

**采用选项 A：PostgreSQL + Redis**

## 详细设计

### 1. 状态数据模型

```sql
-- Agent 状态表
CREATE TABLE agent_states (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Agent 标识
  agent_id VARCHAR(255) NOT NULL,
  agent_version VARCHAR(50),

  -- 会话标识
  conversation_id VARCHAR(255) NOT NULL,
  request_id VARCHAR(255),

  -- 状态分类
  state_type VARCHAR(50) NOT NULL,  -- 'resource', 'context', 'preference', 'workflow'

  -- 状态键值
  state_key VARCHAR(255) NOT NULL,
  state_value JSONB NOT NULL,

  -- 关联资源
  related_resource_type VARCHAR(50),  -- 'version', 'deployment', 'project'
  related_resource_id VARCHAR(255),

  -- 元数据
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP,  -- 可选过期时间

  -- 索引优化
  CONSTRAINT unique_agent_state UNIQUE (agent_id, conversation_id, state_key)
);

-- 索引
CREATE INDEX idx_agent_states_agent_id ON agent_states(agent_id);
CREATE INDEX idx_agent_states_conversation_id ON agent_states(conversation_id);
CREATE INDEX idx_agent_states_resource ON agent_states(related_resource_type, related_resource_id);
CREATE INDEX idx_agent_states_expires ON agent_states(expires_at) WHERE expires_at IS NOT NULL;
```

### 2. 状态类型定义

```typescript
// Agent 状态类型
interface AgentState {
  id: string;

  // Agent 标识
  agent_id: string;
  agent_version?: string;

  // 会话标识
  conversation_id: string;
  request_id?: string;

  // 状态类型
  state_type:
    | 'resource'      // 创建的资源（如 DNS 记录）
    | 'context'       // 执行上下文
    | 'preference'    // 用户偏好
    | 'workflow';     // 工作流状态

  // 状态键值
  state_key: string;
  state_value: Record<string, any>;

  // 关联资源
  related_resource?: {
    type: 'version' | 'deployment' | 'project' | 'region' | 'alert';
    id: string;
  };

  // 生命周期
  created_at: string;
  updated_at: string;
  expires_at?: string;
}

// 状态类型示例

// 1. 资源状态
interface ResourceState extends AgentState {
  state_type: 'resource';
  state_value: {
    resource_type: 'dns_record' | 'k8s_deployment' | 'ssl_certificate';
    resource_id: string;
    resource_name: string;
    provider: string;  // 'cloudflare' | 'kubernetes' | 'letsencrypt'
    status: 'creating' | 'active' | 'deleting' | 'error';
    external_id?: string;  // 外部系统的 ID
    metadata?: Record<string, any>;
  };
}

// 2. 工作流状态
interface WorkflowState extends AgentState {
  state_type: 'workflow';
  state_value: {
    workflow_id: string;
    workflow_type: 'deployment' | 'rollback' | 'dns_setup';
    current_step: string;
    total_steps: number;
    completed_steps: string[];
    failed_step?: string;
    error_message?: string;
    context: Record<string, any>;
  };
}

// 3. 上下文状态
interface ContextState extends AgentState {
  state_type: 'context';
  state_value: {
    key: string;
    value: any;
    source: 'user' | 'agent' | 'system';
  };
}
```

### 3. 状态存储 API

```typescript
// 状态存储服务
interface AgentStateStore {
  // 创建状态
  create(state: Omit<AgentState, 'id' | 'created_at' | 'updated_at'>): Promise<AgentState>;

  // 读取状态
  get(stateId: string): Promise<AgentState | null>;

  // 按键查询
  getByKey(
    agentId: string,
    conversationId: string,
    stateKey: string
  ): Promise<AgentState | null>;

  // 列表查询
  list(params: {
    agent_id?: string;
    conversation_id?: string;
    state_type?: string;
    related_resource_type?: string;
    related_resource_id?: string;
  }): Promise<AgentState[]>;

  // 更新状态
  update(stateId: string, value: Record<string, any>): Promise<AgentState>;

  // 删除状态
  delete(stateId: string): Promise<void>;

  // 清理过期状态
  cleanupExpired(): Promise<number>;
}

// 实现示例
class PostgresStateStore implements AgentStateStore {
  async create(state): Promise<AgentState> {
    const result = await db.query(`
      INSERT INTO agent_states (
        agent_id, agent_version, conversation_id, request_id,
        state_type, state_key, state_value,
        related_resource_type, related_resource_id, expires_at
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
      RETURNING *
    `, [
      state.agent_id,
      state.agent_version,
      state.conversation_id,
      state.request_id,
      state.state_type,
      state.state_key,
      JSON.stringify(state.state_value),
      state.related_resource?.type,
      state.related_resource?.id,
      state.expires_at,
    ]);
    return result.rows[0];
  }

  async getByKey(agentId, conversationId, stateKey): Promise<AgentState | null> {
    const result = await db.query(`
      SELECT * FROM agent_states
      WHERE agent_id = $1 AND conversation_id = $2 AND state_key = $3
      AND (expires_at IS NULL OR expires_at > NOW())
    `, [agentId, conversationId, stateKey]);
    return result.rows[0] || null;
  }

  // ... 其他方法实现
}
```

### 4. 状态与 NexusOps 资源关联

```typescript
// 状态与版本关联
interface VersionStateLink {
  version_id: string;
  states: AgentState[];
}

// 查询版本关联的所有状态
async function getVersionStates(versionId: string): Promise<AgentState[]> {
  return db.query(`
    SELECT * FROM agent_states
    WHERE related_resource_type = 'version' AND related_resource_id = $1
    ORDER BY created_at DESC
  `, [versionId]);
}

// 示例：DNS Agent 创建记录后关联到版本
async function dnsAgentCreateRecord(
  versionId: string,
  params: DNSRecordParams
): Promise<DNSRecord> {
  // 1. 调用 Cloudflare API 创建记录
  const record = await cloudflare.createRecord(params);

  // 2. 存储状态
  await stateStore.create({
    agent_id: 'com.nexusops.agents.dns',
    conversation_id: getCurrentConversationId(),
    state_type: 'resource',
    state_key: `dns_record:${record.id}`,
    state_value: {
      resource_type: 'dns_record',
      resource_id: record.id,
      resource_name: record.name,
      provider: 'cloudflare',
      status: 'active',
      external_id: record.id,
      metadata: {
        type: record.type,
        content: record.content,
        proxied: record.proxied,
      },
    },
    related_resource: {
      type: 'version',
      id: versionId,
    },
  });

  return record;
}
```

### 5. Redis 缓存层

```typescript
// Redis 缓存配置
interface StateCacheConfig {
  // 缓存键前缀
  keyPrefix: 'agent_state:';

  // 缓存时间
  ttl: 3600;  // 1 小时

  // 缓存策略
  strategy: 'write-through';  // 写入时同时更新缓存和数据库
}

// 缓存实现
class CachedStateStore implements AgentStateStore {
  private postgres: PostgresStateStore;
  private redis: RedisClient;
  private config: StateCacheConfig;

  private getCacheKey(agentId: string, conversationId: string, stateKey: string): string {
    return `${this.config.keyPrefix}${agentId}:${conversationId}:${stateKey}`;
  }

  async getByKey(agentId, conversationId, stateKey): Promise<AgentState | null> {
    const cacheKey = this.getCacheKey(agentId, conversationId, stateKey);

    // 1. 尝试从缓存读取
    const cached = await this.redis.get(cacheKey);
    if (cached) {
      return JSON.parse(cached);
    }

    // 2. 从数据库读取
    const state = await this.postgres.getByKey(agentId, conversationId, stateKey);
    if (state) {
      // 3. 写入缓存
      await this.redis.setex(cacheKey, this.config.ttl, JSON.stringify(state));
    }

    return state;
  }

  async create(state): Promise<AgentState> {
    // 1. 写入数据库
    const created = await this.postgres.create(state);

    // 2. 写入缓存
    const cacheKey = this.getCacheKey(state.agent_id, state.conversation_id, state.state_key);
    await this.redis.setex(cacheKey, this.config.ttl, JSON.stringify(created));

    return created;
  }

  async update(stateId, value): Promise<AgentState> {
    // 1. 更新数据库
    const updated = await this.postgres.update(stateId, value);

    // 2. 更新缓存
    const cacheKey = this.getCacheKey(updated.agent_id, updated.conversation_id, updated.state_key);
    await this.redis.setex(cacheKey, this.config.ttl, JSON.stringify(updated));

    return updated;
  }
}
```

### 6. 状态生命周期管理

```typescript
// 状态清理策略
interface StateCleanupPolicy {
  // 清理频率
  schedule: '0 */6 * * *';  // 每 6 小时

  // 清理规则
  rules: [
    {
      type: 'expired';      // 过期状态
      action: 'delete';
    },
    {
      type: 'old_workflow';  // 7 天前的完成工作流
      max_age_days: 7;
      action: 'archive';
    },
    {
      type: 'orphaned';     // 孤立状态（关联资源已删除）
      action: 'delete';
    },
  ];
}

// 清理任务
async function cleanupAgentStates(): Promise<{
  deleted: number;
  archived: number;
}> {
  let deleted = 0;
  let archived = 0;

  // 1. 删除过期状态
  const expiredResult = await db.query(`
    DELETE FROM agent_states
    WHERE expires_at IS NOT NULL AND expires_at < NOW()
  `);
  deleted += expiredResult.rowCount;

  // 2. 归档旧工作流状态
  const archiveResult = await db.query(`
    UPDATE agent_states
    SET state_value = jsonb_set(state_value, '{archived}', 'true')
    WHERE state_type = 'workflow'
    AND created_at < NOW() - INTERVAL '7 days'
    AND state_value->>'status' IN ('completed', 'failed')
    AND (state_value->>'archived') IS NULL
  `);
  archived += archiveResult.rowCount;

  // 3. 清理孤立状态
  // ... 实现孤立状态检测和清理

  return { deleted, archived };
}
```

## 后果

### 正面
- 利用现有 PostgreSQL 基础设施
- Redis 缓存提升性能
- 灵活的查询和关联能力

### 负面
- 需要维护两个存储系统
- 状态一致性需要处理

## 实现

1. **Phase 3.5**: 创建数据库表结构
2. **Phase 3.5**: 实现基础状态存储 API
3. **Phase 4**: 添加 Redis 缓存层
4. **Phase 4**: 实现状态清理任务
