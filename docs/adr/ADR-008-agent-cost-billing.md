# ADR-008: Agent 成本计费

## 状态
已接受 (2024-02-16)

## 背景

Agent 的执行涉及多种资源消耗：
- LLM Token 消耗（按 Token 计费）
- 计算资源（CPU、内存）
- 外部 API 调用（Cloudflare、AWS 等）
- 网络流量
- 存储空间

需要明确的计费策略来：
- 追踪资源消耗
- 分摊成本
- 支持多租户
- 提供成本报告

## 选项

### 选项 A: 多维度计量 + 配额管理（推荐）
- 按多维度计量消耗
- 配额控制
- 成本报告

**优点**：
- 精确计量
- 成本透明
- 支持多租户

**缺点**：
- 实现复杂

### 选项 B: 固定价套餐
- 按套餐收费，不限量

**优点**：
- 简单

**缺点**：
- 资源浪费
- 成本不透明

### 选项 C: 按 Agent 计数
- 按使用的 Agent 数量收费

**优点**：
- 简单

**缺点**：
- 不公平
- 无法反映实际消耗

## 决策

**采用选项 A：多维度计量 + 配额管理**

## 详细设计

### 1. 计量维度

```typescript
// 资源消耗类型
enum MeteringDimension {
  // LLM 相关
  LLM_INPUT_TOKENS = 'llm_input_tokens',
  LLM_OUTPUT_TOKENS = 'llm_output_tokens',
  LLM_REQUESTS = 'llm_requests',

  // 计算相关
  EXECUTION_TIME_MS = 'execution_time_ms',
  CPU_SECONDS = 'cpu_seconds',
  MEMORY_MB_SECONDS = 'memory_mb_seconds',

  // 外部 API
  EXTERNAL_API_CALLS = 'external_api_calls',
  EXTERNAL_API_DATA_TRANSFER = 'external_api_data_transfer',

  // 存储
  STATE_STORAGE_BYTES = 'state_storage_bytes',
  LOG_STORAGE_BYTES = 'log_storage_bytes',

  // 网络
  NETWORK_EGRESS_BYTES = 'network_egress_bytes',
}

// 计量单位
interface MeteringUnit {
  dimension: MeteringDimension;
  quantity: number;
  unit: string;
  cost_per_unit: number;  // 单位成本（美元）
}

// 资源消耗记录
interface ResourceConsumption {
  id: string;
  timestamp: string;

  // 上下文
  agent_id: string;
  agent_version: string;
  conversation_id: string;
  request_id: string;

  // 租户
  tenant_id: string;
  user_id: string;
  project_id?: string;

  // 消耗明细
  consumption: Record<MeteringDimension, number>;

  // 成本（美元）
  cost_usd: number;

  // 元数据
  metadata?: Record<string, any>;
}
```

### 2. 计量器实现

```typescript
// 计量器
interface Meter {
  // 记录消耗
  record(consumption: Omit<ResourceConsumption, 'id' | 'timestamp' | 'cost_usd'>): Promise<void>;

  // 查询消耗
  query(params: {
    tenant_id?: string;
    agent_id?: string;
    start_time?: Date;
    end_time?: Date;
    group_by?: ('tenant' | 'agent' | 'user' | 'day')[];
  }): Promise<MeteringReport>;
}

// 报告
interface MeteringReport {
  period: {
    start: string;
    end: string;
  };

  // 汇总
  summary: {
    total_cost_usd: number;
    total_consumption: Record<MeteringDimension, number>;
  };

  // 分组明细
  groups?: Array<{
    key: Record<string, string>;
    cost_usd: number;
    consumption: Record<MeteringDimension, number>;
  }>;
}

// PostgreSQL 实现
class PostgresMeter implements Meter {
  async record(consumption): Promise<void> {
    // 计算成本
    const costUsd = this.calculateCost(consumption.consumption);

    await db.query(`
      INSERT INTO resource_consumptions (
        id, timestamp, agent_id, agent_version,
        conversation_id, request_id, tenant_id, user_id, project_id,
        llm_input_tokens, llm_output_tokens, execution_time_ms,
        external_api_calls, cost_usd, metadata
      ) VALUES ($1, NOW(), $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
    `, [
      generateUUID(),
      consumption.agent_id,
      consumption.agent_version,
      consumption.conversation_id,
      consumption.request_id,
      consumption.tenant_id,
      consumption.user_id,
      consumption.project_id,
      consumption.consumption[MeteringDimension.LLM_INPUT_TOKENS] || 0,
      consumption.consumption[MeteringDimension.LLM_OUTPUT_TOKENS] || 0,
      consumption.consumption[MeteringDimension.EXECUTION_TIME_MS] || 0,
      consumption.consumption[MeteringDimension.EXTERNAL_API_CALLS] || 0,
      costUsd,
      JSON.stringify(consumption.metadata || {}),
    ]);
  }

  private calculateCost(consumption: Record<MeteringDimension, number>): number {
    // 成本价目表
    const pricing: Record<MeteringDimension, number> = {
      [MeteringDimension.LLM_INPUT_TOKENS]: 0.000003,    // $0.003/1K tokens
      [MeteringDimension.LLM_OUTPUT_TOKENS]: 0.000015,   // $0.015/1K tokens
      [MeteringDimension.LLM_REQUESTS]: 0.0001,
      [MeteringDimension.EXECUTION_TIME_MS]: 0.0000001,  // $0.0001/second
      [MeteringDimension.CPU_SECONDS]: 0.00001,
      [MeteringDimension.MEMORY_MB_SECONDS]: 0.000001,
      [MeteringDimension.EXTERNAL_API_CALLS]: 0.001,
      [MeteringDimension.EXTERNAL_API_DATA_TRANSFER]: 0.0000001,  // $0.10/GB
      [MeteringDimension.STATE_STORAGE_BYTES]: 0.00000000002,     // $0.02/GB/month
      [MeteringDimension.LOG_STORAGE_BYTES]: 0.00000000001,       // $0.01/GB/month
      [MeteringDimension.NETWORK_EGRESS_BYTES]: 0.0000001,        // $0.10/GB
    };

    let totalCost = 0;
    for (const [dimension, quantity] of Object.entries(consumption)) {
      const price = pricing[dimension as MeteringDimension] || 0;
      totalCost += quantity * price;
    }

    return Math.round(totalCost * 1000000) / 1000000;  // 6 位小数
  }

  async query(params): Promise<MeteringReport> {
    // 实现查询逻辑
    // ...
  }
}

// Agent 集成
class MeteringAgentWrapper {
  private meter: Meter;
  private agent: Agent;

  async invoke(request: AgentRequest): Promise<AgentResponse> {
    const startTime = Date.now();
    let inputTokens = 0;
    let outputTokens = 0;

    try {
      // 调用 Agent
      const response = await this.agent.invoke(request);

      // 提取 token 使用量
      if (response.metadata?.tokens_used) {
        inputTokens = response.metadata.tokens_used.input || 0;
        outputTokens = response.metadata.tokens_used.output || 0;
      }

      return response;
    } finally {
      // 记录消耗
      await this.meter.record({
        agent_id: request.agent_id,
        agent_version: this.agent.version,
        conversation_id: request.conversation_id,
        request_id: request.request_id,
        tenant_id: request.context?.tenant_id || 'default',
        user_id: request.context?.user_id || 'anonymous',
        project_id: request.context?.project_id,
        consumption: {
          [MeteringDimension.LLM_INPUT_TOKENS]: inputTokens,
          [MeteringDimension.LLM_OUTPUT_TOKENS]: outputTokens,
          [MeteringDimension.EXECUTION_TIME_MS]: Date.now() - startTime,
        },
      });
    }
  }
}
```

### 3. 配额管理

```typescript
// 配额定义
interface Quota {
  id: string;
  name: string;

  // 作用域
  scope: 'tenant' | 'project' | 'user';

  // 周期
  period: 'daily' | 'weekly' | 'monthly';

  // 限制
  limits: Record<MeteringDimension, number>;

  // 成本限制
  cost_limit_usd?: number;

  // 超限行为
  overage_policy: 'block' | 'warn' | 'allow_with_surcharge';
  surcharge_rate?: number;  // 超限费率

  // 通知
  notification_thresholds: number[];  // [0.5, 0.8, 0.9, 1.0]
}

// 配额检查器
class QuotaChecker {
  private meter: Meter;

  async check(quota: Quota, context: {
    tenant_id: string;
    user_id: string;
    project_id?: string;
  }): Promise<QuotaCheckResult> {
    // 获取当前周期消耗
    const consumption = await this.getCurrentConsumption(quota, context);

    // 检查各维度
    const violations: QuotaViolation[] = [];

    for (const [dimension, limit] of Object.entries(quota.limits)) {
      const used = consumption[dimension as MeteringDimension] || 0;
      if (used >= limit) {
        violations.push({
          dimension: dimension as MeteringDimension,
          limit,
          used,
          overage: used - limit,
        });
      }
    }

    // 检查成本限制
    if (quota.cost_limit_usd) {
      const costUsd = this.calculateCost(consumption);
      if (costUsd >= quota.cost_limit_usd) {
        violations.push({
          dimension: 'cost' as any,
          limit: quota.cost_limit_usd,
          used: costUsd,
          overage: costUsd - quota.cost_limit_usd,
        });
      }
    }

    // 计算使用率
    const usagePercentages: Record<MeteringDimension, number> = {};
    for (const [dimension, limit] of Object.entries(quota.limits)) {
      const used = consumption[dimension as MeteringDimension] || 0;
      usagePercentages[dimension as MeteringDimension] = (used / limit) * 100;
    }

    return {
      allowed: violations.length === 0 || quota.overage_policy !== 'block',
      violations,
      usage_percentages: usagePercentages,
      overage_policy: quota.overage_policy,
    };
  }

  private async getCurrentConsumption(
    quota: Quota,
    context: { tenant_id: string; user_id: string; project_id?: string }
  ): Promise<Record<MeteringDimension, number>> {
    // 计算周期起始时间
    const periodStart = this.getPeriodStart(quota.period);

    const report = await this.meter.query({
      tenant_id: quota.scope === 'tenant' ? context.tenant_id : undefined,
      user_id: quota.scope === 'user' ? context.user_id : undefined,
      project_id: quota.scope === 'project' ? context.project_id : undefined,
      start_time: periodStart,
      end_time: new Date(),
    });

    return report.summary.total_consumption;
  }

  private getPeriodStart(period: 'daily' | 'weekly' | 'monthly'): Date {
    const now = new Date();

    switch (period) {
      case 'daily':
        return new Date(now.getFullYear(), now.getMonth(), now.getDate());
      case 'weekly':
        const dayOfWeek = now.getDay();
        return new Date(now.getFullYear(), now.getMonth(), now.getDate() - dayOfWeek);
      case 'monthly':
        return new Date(now.getFullYear(), now.getMonth(), 1);
    }
  }
}

// 配额执行器
class QuotaEnforcer {
  private checker: QuotaChecker;

  async enforce(
    quota: Quota,
    context: { tenant_id: string; user_id: string; project_id?: string },
    estimatedConsumption: Partial<Record<MeteringDimension, number>>
  ): Promise<{ allowed: boolean; result?: QuotaCheckResult }> {
    const result = await this.checker.check(quota, context);

    if (!result.allowed) {
      return { allowed: false, result };
    }

    // 检查是否接近阈值
    const thresholds = quota.notification_thresholds;
    for (const [dimension, percentage] of Object.entries(result.usage_percentages)) {
      for (const threshold of thresholds) {
        if (percentage >= threshold * 100) {
          // 发送通知
          await this.sendUsageAlert({
            quota_id: quota.id,
            dimension,
            usage_percentage: percentage,
            threshold: threshold * 100,
            context,
          });
          break;
        }
      }
    }

    return { allowed: true, result };
  }
}
```

### 4. 成本报告

```typescript
// 成本报告
interface CostReport {
  // 报告周期
  period: {
    type: 'daily' | 'weekly' | 'monthly';
    start: string;
    end: string;
  };

  // 汇总
  summary: {
    total_cost_usd: number;
    previous_period_cost_usd: number;
    change_percent: number;

    breakdown: {
      by_dimension: Array<{
        dimension: MeteringDimension;
        cost_usd: number;
        percentage: number;
      }>;
      by_agent: Array<{
        agent_id: string;
        agent_name: string;
        cost_usd: number;
        percentage: number;
      }>;
      by_project: Array<{
        project_id: string;
        project_name: string;
        cost_usd: number;
        percentage: number;
      }>;
    };
  };

  // 趋势
  trend: Array<{
    date: string;
    cost_usd: number;
  }>;

  // 异常检测
  anomalies?: Array<{
    date: string;
    dimension: MeteringDimension;
    expected: number;
    actual: number;
    deviation_percent: number;
  }>;

  // 优化建议
  recommendations?: Array<{
    type: 'cost_saving' | 'efficiency' | 'quota_adjustment';
    description: string;
    potential_savings_usd?: number;
  }>;
}

// 报告生成器
class CostReportGenerator {
  async generate(params: {
    tenant_id: string;
    period: 'daily' | 'weekly' | 'monthly';
    end_date?: Date;
  }): Promise<CostReport> {
    const endDate = params.end_date || new Date();
    const startDate = this.getPeriodStart(params.period, endDate);
    const previousPeriodStart = this.getPeriodStart(params.period, startDate);

    // 获取当期数据
    const currentPeriod = await this.meter.query({
      tenant_id: params.tenant_id,
      start_time: startDate,
      end_time: endDate,
      group_by: ['agent', 'project', 'day'],
    });

    // 获取上期数据
    const previousPeriod = await this.meter.query({
      tenant_id: params.tenant_id,
      start_time: previousPeriodStart,
      end_time: startDate,
    });

    // 计算变化
    const changePercent = previousPeriod.summary.total_cost_usd > 0
      ? ((currentPeriod.summary.total_cost_usd - previousPeriod.summary.total_cost_usd) / previousPeriod.summary.total_cost_usd) * 100
      : 0;

    // 生成报告
    return {
      period: {
        type: params.period,
        start: startDate.toISOString(),
        end: endDate.toISOString(),
      },
      summary: {
        total_cost_usd: currentPeriod.summary.total_cost_usd,
        previous_period_cost_usd: previousPeriod.summary.total_cost_usd,
        change_percent: changePercent,
        breakdown: {
          by_dimension: this.calculateDimensionBreakdown(currentPeriod),
          by_agent: this.calculateAgentBreakdown(currentPeriod),
          by_project: this.calculateProjectBreakdown(currentPeriod),
        },
      },
      trend: this.calculateTrend(currentPeriod),
      anomalies: this.detectAnomalies(currentPeriod, previousPeriod),
      recommendations: this.generateRecommendations(currentPeriod, previousPeriod),
    };
  }

  private generateRecommendations(current: any, previous: any): any[] {
    const recommendations = [];

    // 检查高成本 Agent
    const agentCosts = current.groups?.filter(g => g.key.agent) || [];
    const highCostAgents = agentCosts.filter(a => a.cost_usd > 10);
    if (highCostAgents.length > 0) {
      recommendations.push({
        type: 'cost_saving',
        description: `发现 ${highCostAgents.length} 个高成本 Agent，建议优化提示词或减少调用频率`,
        potential_savings_usd: highCostAgents.reduce((sum, a) => sum + a.cost_usd * 0.2, 0),
      });
    }

    // 检查配额利用率
    // ...

    return recommendations;
  }
}
```

### 5. 外部 API 成本分摊

```typescript
// 外部服务成本配置
interface ExternalServiceCost {
  service_name: string;
  provider: 'cloudflare' | 'aws' | 'gcp' | 'azure' | 'custom';

  // 计费模型
  billing_model: 'per_request' | 'per_data' | 'per_hour' | 'hybrid';

  // 费率
  rates: {
    per_request?: number;
    per_gb?: number;
    per_hour?: number;
  };

  // 谁承担成本
  cost_bearer: 'platform' | 'tenant' | 'project' | 'user';

  // 包含额度（免费额度）
  included_allowance?: {
    requests_per_month?: number;
    gb_per_month?: number;
  };
}

// 外部服务成本配置
const EXTERNAL_SERVICE_COSTS: ExternalServiceCost[] = [
  {
    service_name: 'Cloudflare DNS',
    provider: 'cloudflare',
    billing_model: 'per_request',
    rates: {
      per_request: 0.00001,  // $0.01/1K requests
    },
    cost_bearer: 'platform',
    included_allowance: {
      requests_per_month: 1000000,
    },
  },
  {
    service_name: 'Cloudflare SSL',
    provider: 'cloudflare',
    billing_model: 'hybrid',
    rates: {
      per_request: 0,
      per_hour: 0,
    },
    cost_bearer: 'platform',
  },
  {
    service_name: 'AWS Route53',
    provider: 'aws',
    billing_model: 'per_request',
    rates: {
      per_request: 0.0000005,  // $0.50/1M requests
    },
    cost_bearer: 'tenant',
    included_allowance: {
      requests_per_month: 100000,
    },
  },
];

// 外部服务成本追踪
class ExternalServiceTracker {
  async track(
    serviceName: string,
    operation: string,
    params: {
      tenant_id: string;
      project_id?: string;
      user_id?: string;
      data_transfer_bytes?: number;
    }
  ): Promise<void> {
    const config = EXTERNAL_SERVICE_COSTS.find(s => s.service_name === serviceName);
    if (!config) return;

    // 计算成本
    let costUsd = 0;
    if (config.rates.per_request) {
      costUsd += config.rates.per_request;
    }
    if (config.rates.per_gb && params.data_transfer_bytes) {
      costUsd += (params.data_transfer_bytes / (1024 * 1024 * 1024)) * config.rates.per_gb;
    }

    // 记录消耗
    await this.meter.record({
      agent_id: `external:${serviceName}`,
      agent_version: '1.0.0',
      conversation_id: 'external',
      request_id: generateUUID(),
      tenant_id: params.tenant_id,
      user_id: params.user_id || 'external',
      project_id: params.project_id,
      consumption: {
        [MeteringDimension.EXTERNAL_API_CALLS]: 1,
        [MeteringDimension.EXTERNAL_API_DATA_TRANSFER]: params.data_transfer_bytes || 0,
      },
      metadata: {
        service: serviceName,
        operation,
        cost_bearer: config.cost_bearer,
      },
    });
  }
}
```

### 6. 成本仪表板数据

```typescript
// 仪表板 API
interface CostDashboardAPI {
  // 获取概览
  getOverview(tenantId: string): Promise<CostOverview>;

  // 获取趋势
  getTrend(tenantId: string, period: '7d' | '30d' | '90d'): Promise<CostTrend>;

  // 获取明细
  getDetails(tenantId: string, params: {
    start_date: Date;
    end_date: Date;
    agent_id?: string;
    project_id?: string;
  }): Promise<CostDetails>;

  // 导出报告
  exportReport(tenantId: string, format: 'csv' | 'pdf'): Promise<Blob>;
}

// 概览数据
interface CostOverview {
  // 当前周期
  current_period: {
    start: string;
    end: string;
    cost_usd: number;
    budget_usd: number | null;
    budget_used_percent: number | null;
  };

  // 与上期对比
  comparison: {
    cost_usd: number;
    change_percent: number;
    trend: 'up' | 'down' | 'stable';
  };

  // 按维度分布
  distribution: {
    by_agent: Array<{ name: string; cost_usd: number; percent: number }>;
    by_project: Array<{ name: string; cost_usd: number; percent: number }>;
    by_dimension: Array<{ name: string; cost_usd: number; percent: number }>;
  };

  // 警告
  alerts: Array<{
    type: 'budget_exceeded' | 'unusual_usage' | 'quota_warning';
    message: string;
    severity: 'info' | 'warning' | 'error';
  }>;
}
```

## 后果

### 正面
- 精确的成本追踪
- 支持多租户计费
- 成本透明度
- 优化建议

### 负面
- 实现复杂度
- 计量开销
- 定价策略维护

## 实现

1. **Phase 3.5**: 实现基础计量器
2. **Phase 4**: 实现配额管理
3. **Phase 4**: 实现成本报告
4. **Phase 5**: 实现外部服务追踪
5. **Phase 5**: 实现成本仪表板
