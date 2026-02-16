# ADR-010: Agent 更新机制

## 状态
已接受 (2024-02-16)

## 背景

Agent 需要定期更新以：
- 修复 Bug
- 添加新功能
- 更新依赖
- 改进性能
- 修复安全问题

需要明确的更新策略来解决：
- 如何检测更新
- 如何执行更新
- 如何处理更新失败
- 如何回滚
- 如何保证服务不中断

## 选项

### 选项 A: 滚动更新 + 蓝绿部署（推荐）
- 支持零停机更新
- 自动回滚失败更新
- 分阶段发布

**优点**：
- 零停机
- 安全回滚
- 可控发布

**缺点**：
- 实现复杂
- 资源需求高

### 选项 B: 停机更新
- 停止服务 → 更新 → 启动

**优点**：
- 简单

**缺点**：
- 服务中断

### 选项 C: 仅手动更新
- 用户手动下载和安装更新

**优点**：
- 完全控制

**缺点**：
- 操作繁琐
- 安全风险

## 决策

**采用选项 A：滚动更新 + 蓝绿部署**

## 详细设计

### 1. 更新检测

```typescript
// 更新检查
interface UpdateCheck {
  agent_id: string;
  current_version: string;
  latest_version: string;
  update_available: boolean;
  update_type: 'major' | 'minor' | 'patch' | 'none';
  changelog?: ChangeLogEntry[];
  release_date?: string;
  security_update: boolean;
  mandatory: boolean;  // 是否强制更新
}

// 更新源配置
interface UpdateSource {
  type: 'registry' | 'git' | 'http';
  url: string;
  credentials?: {
    type: 'basic' | 'token' | 'oauth';
    // ...
  };
  check_interval: number;  // 检查间隔（秒）
}

// 更新检查器
class UpdateChecker {
  private sources: Map<string, UpdateSource> = new Map();

  async checkForUpdates(agentId: string, currentVersion: string): Promise<UpdateCheck> {
    // 1. 获取更新源
    const source = this.sources.get(agentId);
    if (!source) {
      return this.noUpdate(agentId, currentVersion);
    }

    // 2. 查询最新版本
    const latestVersion = await this.queryLatestVersion(source, agentId);

    // 3. 比较版本
    const comparison = this.compareVersions(currentVersion, latestVersion.version);

    if (comparison >= 0) {
      return this.noUpdate(agentId, currentVersion);
    }

    // 4. 获取变更日志
    const changelog = await this.getChangelog(source, agentId, currentVersion, latestVersion.version);

    // 5. 判断更新类型
    const updateType = this.determineUpdateType(currentVersion, latestVersion.version);

    return {
      agent_id: agentId,
      current_version: currentVersion,
      latest_version: latestVersion.version,
      update_available: true,
      update_type: updateType,
      changelog,
      release_date: latestVersion.release_date,
      security_update: latestVersion.security_update || false,
      mandatory: latestVersion.mandatory || false,
    };
  }

  private determineUpdateType(current: string, latest: string): 'major' | 'minor' | 'patch' {
    const currentParts = current.split('.').map(Number);
    const latestParts = latest.split('.').map(Number);

    if (latestParts[0] > currentParts[0]) return 'major';
    if (latestParts[1] > currentParts[1]) return 'minor';
    return 'patch';
  }
}
```

### 2. 更新策略

```typescript
// 更新策略
interface UpdateStrategy {
  // 策略类型
  type: 'rolling' | 'blue_green' | 'canary';

  // 滚动更新配置
  rolling?: {
    batch_size: number;       // 每批更新的实例数
    wait_between_batches: number;  // 批次间等待时间（秒）
    min_healthy_percent: number;   // 最小健康实例百分比
  };

  // 蓝绿部署配置
  blue_green?: {
    keep_old_version: boolean;     // 是否保留旧版本
    rollback_on_failure: boolean;  // 失败时自动回滚
    health_check_timeout: number;  // 健康检查超时（秒）
  };

  // 金丝雀发布配置
  canary?: {
    initial_percent: number;       // 初始流量百分比
    increment_percent: number;     // 增量百分比
    increment_interval: number;    // 增量间隔（秒）
    rollback_threshold: number;    // 错误率阈值（%）
  };

  // 健康检查
  health_check: {
    endpoint?: string;
    interval: number;
    timeout: number;
    retries: number;
  };

  // 回滚配置
  rollback: {
    automatic: boolean;
    failure_threshold: number;  // 失败次数阈值
    error_rate_threshold: number;  // 错误率阈值
  };
}

// 默认策略
const DEFAULT_STRATEGY: UpdateStrategy = {
  type: 'rolling',
  rolling: {
    batch_size: 1,
    wait_between_batches: 30,
    min_healthy_percent: 80,
  },
  health_check: {
    interval: 10,
    timeout: 5,
    retries: 3,
  },
  rollback: {
    automatic: true,
    failure_threshold: 3,
    error_rate_threshold: 10,
  },
};
```

### 3. 滚动更新执行器

```typescript
// 更新执行器
class RollingUpdateExecutor {
  private registry: AgentRegistry;
  private containerPool: ContainerPool;
  private healthChecker: HealthChecker;

  async execute(
    agentId: string,
    targetVersion: string,
    strategy: UpdateStrategy
  ): Promise<UpdateResult> {
    const config = strategy.rolling!;
    const instances = await this.registry.getInstances(agentId);
    const totalInstances = instances.length;
    const batchSize = config.batch_size;
    const minHealthy = Math.ceil(totalInstances * config.min_healthy_percent / 100);

    const result: UpdateResult = {
      agent_id: agentId,
      from_version: instances[0].version,
      to_version: targetVersion,
      started_at: new Date().toISOString(),
      status: 'in_progress',
      updated_instances: 0,
      failed_instances: 0,
      errors: [],
    };

    // 分批更新
    for (let i = 0; i < totalInstances; i += batchSize) {
      const batch = instances.slice(i, i + batchSize);

      // 检查健康实例数
      const healthyCount = await this.countHealthy(instances);
      if (healthyCount < minHealthy) {
        result.status = 'failed';
        result.errors.push(`Not enough healthy instances: ${healthyCount} < ${minHealthy}`);
        break;
      }

      // 更新批次
      for (const instance of batch) {
        try {
          await this.updateInstance(instance, targetVersion, strategy);
          result.updated_instances++;
        } catch (error) {
          result.failed_instances++;
          result.errors.push(`Instance ${instance.id} failed: ${error.message}`);

          // 检查是否需要回滚
          if (strategy.rollback.automatic && result.failed_instances >= strategy.rollback.failure_threshold) {
            result.status = 'rolled_back';
            await this.rollback(agentId, result.from_version);
            return result;
          }
        }
      }

      // 等待批次间间隔
      if (i + batchSize < totalInstances) {
        await this.sleep(config.wait_between_batches * 1000);
      }
    }

    result.status = result.failed_instances === 0 ? 'completed' : 'partial';
    result.completed_at = new Date().toISOString();
    return result;
  }

  private async updateInstance(
    instance: AgentInstance,
    targetVersion: string,
    strategy: UpdateStrategy
  ): Promise<void> {
    // 1. 下载新版本
    const artifact = await this.downloadVersion(instance.agent_id, targetVersion);

    // 2. 验证签名
    await this.verifySignature(artifact);

    // 3. 停止旧实例
    await this.containerPool.stop(instance.id);

    // 4. 启动新实例
    await this.containerPool.start({
      agent_id: instance.agent_id,
      version: targetVersion,
      instance_id: instance.id,
    });

    // 5. 健康检查
    const healthy = await this.healthChecker.check(
      instance.id,
      strategy.health_check
    );

    if (!healthy) {
      throw new Error('Health check failed');
    }
  }

  private async rollback(agentId: string, targetVersion: string): Promise<void> {
    console.log(`Rolling back ${agentId} to ${targetVersion}`);
    // 执行回滚
  }
}
```

### 4. 蓝绿部署

```typescript
// 蓝绿部署执行器
class BlueGreenExecutor {
  private registry: AgentRegistry;
  private loadBalancer: LoadBalancer;
  private containerPool: ContainerPool;

  async execute(
    agentId: string,
    targetVersion: string,
    strategy: UpdateStrategy
  ): Promise<UpdateResult> {
    const config = strategy.blue_green!;

    // 获取当前（蓝色）环境
    const blueEnv = await this.registry.getActiveEnvironment(agentId);
    const blueVersion = blueEnv.version;

    // 创建新（绿色）环境
    const greenEnv = await this.createGreenEnvironment(agentId, targetVersion);

    // 启动绿色环境实例
    await this.startGreenInstances(greenEnv);

    // 健康检查
    const healthy = await this.healthCheck(greenEnv, strategy.health_check);

    if (!healthy) {
      // 绿色环境不健康，清理并失败
      await this.cleanupEnvironment(greenEnv);
      return {
        agent_id: agentId,
        from_version: blueVersion,
        to_version: targetVersion,
        status: 'failed',
        errors: ['Green environment health check failed'],
      };
    }

    // 切换流量到绿色环境
    await this.loadBalancer.switchTraffic(agentId, greenEnv.id);

    // 验证切换
    const verificationPassed = await this.verifySwitch(agentId, greenEnv);

    if (!verificationPassed && config.rollback_on_failure) {
      // 验证失败，回滚到蓝色环境
      await this.loadBalancer.switchTraffic(agentId, blueEnv.id);
      await this.cleanupEnvironment(greenEnv);
      return {
        agent_id: agentId,
        from_version: blueVersion,
        to_version: targetVersion,
        status: 'rolled_back',
        errors: ['Verification failed after traffic switch'],
      };
    }

    // 更新成功
    if (!config.keep_old_version) {
      // 清理蓝色环境
      await this.cleanupEnvironment(blueEnv);
    } else {
      // 标记蓝色环境为备用
      await this.registry.setStandby(blueEnv.id);
    }

    return {
      agent_id: agentId,
      from_version: blueVersion,
      to_version: targetVersion,
      status: 'completed',
    };
  }

  private async createGreenEnvironment(agentId: string, version: string): Promise<Environment> {
    return {
      id: `${agentId}-green-${Date.now()}`,
      agent_id: agentId,
      version,
      status: 'creating',
      instances: [],
    };
  }
}
```

### 5. 金丝雀发布

```typescript
// 金丝雀发布执行器
class CanaryExecutor {
  private loadBalancer: LoadBalancer;
  private metricsCollector: MetricsCollector;

  async execute(
    agentId: string,
    targetVersion: string,
    strategy: UpdateStrategy
  ): Promise<UpdateResult> {
    const config = strategy.canary!;
    let currentPercent = config.initial_percent;

    // 部署金丝雀实例
    await this.deployCanary(agentId, targetVersion, currentPercent);

    while (currentPercent < 100) {
      // 等待观察期
      await this.sleep(config.increment_interval * 1000);

      // 收集指标
      const metrics = await this.collectMetrics(agentId);

      // 检查错误率
      if (metrics.error_rate > config.rollback_threshold) {
        // 回滚
        await this.rollbackCanary(agentId);
        return {
          agent_id: agentId,
          to_version: targetVersion,
          status: 'rolled_back',
          errors: [`Error rate ${metrics.error_rate}% exceeded threshold ${config.rollback_threshold}%`],
        };
      }

      // 增加流量
      currentPercent = Math.min(100, currentPercent + config.increment_percent);
      await this.loadBalancer.setTrafficWeight(agentId, {
        canary: currentPercent,
        stable: 100 - currentPercent,
      });
    }

    // 完成发布，清理旧版本
    await this.promoteCanary(agentId);

    return {
      agent_id: agentId,
      to_version: targetVersion,
      status: 'completed',
    };
  }

  private async collectMetrics(agentId: string): Promise<CanaryMetrics> {
    const window = 60;  // 60秒窗口

    const [stableMetrics, canaryMetrics] = await Promise.all([
      this.metricsCollector.getMetrics(agentId, 'stable', window),
      this.metricsCollector.getMetrics(agentId, 'canary', window),
    ]);

    return {
      stable_error_rate: stableMetrics.errorRate,
      canary_error_rate: canaryMetrics.errorRate,
      error_rate: canaryMetrics.errorRate,
      latency_p99: canaryMetrics.latencyP99,
      throughput: canaryMetrics.throughput,
    };
  }
}
```

### 6. 更新管理 API

```typescript
// 更新管理器
interface UpdateManager {
  // 检查更新
  checkUpdates(): Promise<Map<string, UpdateCheck>>;

  // 计划更新
  scheduleUpdate(agentId: string, version: string, scheduledAt: Date): Promise<string>;

  // 执行更新
  executeUpdate(
    agentId: string,
    version: string,
    strategy?: Partial<UpdateStrategy>
  ): Promise<UpdateResult>;

  // 取消更新
  cancelUpdate(updateId: string): Promise<boolean>;

  // 回滚
  rollback(agentId: string, targetVersion?: string): Promise<UpdateResult>;

  // 获取更新历史
  getUpdateHistory(agentId: string, limit?: number): Promise<UpdateResult[]>;

  // 获取更新状态
  getUpdateStatus(updateId: string): Promise<UpdateStatus>;
}

// API 实现
class UpdateManagerImpl implements UpdateManager {
  private scheduler: UpdateScheduler;
  private executor: UpdateExecutor;

  async checkUpdates(): Promise<Map<string, UpdateCheck>> {
    const agents = await this.registry.listAgents();
    const updates = new Map<string, UpdateCheck>();

    for (const agent of agents) {
      const check = await this.checker.checkForUpdates(agent.id, agent.version);
      if (check.update_available) {
        updates.set(agent.id, check);
      }
    }

    return updates;
  }

  async scheduleUpdate(
    agentId: string,
    version: string,
    scheduledAt: Date
  ): Promise<string> {
    const updateId = generateUUID();

    await this.scheduler.schedule({
      id: updateId,
      agent_id: agentId,
      target_version: version,
      scheduled_at: scheduledAt.toISOString(),
      status: 'scheduled',
    });

    return updateId;
  }

  async executeUpdate(
    agentId: string,
    version: string,
    strategy?: Partial<UpdateStrategy>
  ): Promise<UpdateResult> {
    const finalStrategy = { ...DEFAULT_STRATEGY, ...strategy };

    // 根据策略类型选择执行器
    switch (finalStrategy.type) {
      case 'rolling':
        return this.rollingExecutor.execute(agentId, version, finalStrategy);
      case 'blue_green':
        return this.blueGreenExecutor.execute(agentId, version, finalStrategy);
      case 'canary':
        return this.canaryExecutor.execute(agentId, version, finalStrategy);
      default:
        throw new Error(`Unknown update strategy: ${finalStrategy.type}`);
    }
  }

  async rollback(agentId: string, targetVersion?: string): Promise<UpdateResult> {
    // 获取上一个稳定版本
    const history = await this.getUpdateHistory(agentId, 5);
    const lastSuccess = history.find(h => h.status === 'completed');

    if (!lastSuccess && !targetVersion) {
      throw new Error('No previous version to rollback to');
    }

    const rollbackVersion = targetVersion || lastSuccess.from_version;

    return this.executeUpdate(agentId, rollbackVersion, {
      rollback: { automatic: false },
    });
  }
}
```

### 7. 更新通知

```typescript
// 更新通知配置
interface UpdateNotification {
  channels: ('email' | 'slack' | 'webhook' | 'ui')[];
  events: {
    update_available: boolean;
    update_started: boolean;
    update_completed: boolean;
    update_failed: boolean;
    rollback_triggered: boolean;
  };
  recipients: {
    agent_owners: boolean;
    admins: boolean;
    custom_emails?: string[];
  };
}

// 通知处理器
class UpdateNotifier {
  async notify(event: UpdateEvent): Promise<void> {
    const config = this.getNotificationConfig(event.agent_id);

    const message = this.buildMessage(event);

    for (const channel of config.channels) {
      await this.sendToChannel(channel, message, config.recipients);
    }
  }

  private buildMessage(event: UpdateEvent): NotificationMessage {
    const templates: Record<UpdateEventType, string> = {
      update_available: `
🔄 **Update Available**
Agent: {{agent_name}}
Current: {{current_version}}
Latest: {{latest_version}}
{{#security_update}}⚠️ Security Update{{/security_update}}
      `,
      update_started: `
🚀 **Update Started**
Agent: {{agent_name}}
From: {{from_version}} → To: {{to_version}}
Strategy: {{strategy}}
      `,
      update_completed: `
✅ **Update Completed**
Agent: {{agent_name}}
Version: {{to_version}}
Duration: {{duration}}
      `,
      update_failed: `
❌ **Update Failed**
Agent: {{agent_name}}
Error: {{error_message}}
{{#rollback_triggered}}↩️ Rollback triggered{{/rollback_triggered}}
      `,
      rollback_triggered: `
↩️ **Rollback Triggered**
Agent: {{agent_name}}
From: {{failed_version}} → To: {{rollback_version}}
Reason: {{reason}}
      `,
    };

    return {
      title: `Agent Update: ${event.agent_name}`,
      body: this.renderTemplate(templates[event.type], event),
      severity: event.type === 'update_failed' ? 'error' :
                event.type === 'rollback_triggered' ? 'warning' : 'info',
    };
  }
}
```

## 后果

### 正面
- 零停机更新
- 安全回滚机制
- 多种更新策略
- 自动化更新

### 负面
- 实现复杂度高
- 资源开销（蓝绿部署需要双倍资源）

## 实现

1. **Phase 3.5**: 基础更新检测和执行
2. **Phase 4**: 滚动更新和回滚
3. **Phase 5**: 蓝绿部署和金丝雀发布
