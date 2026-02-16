# ADR-005: Agent 错误处理

## 状态
已接受 (2024-02-16)

## 背景

Agent 在执行过程中可能遇到各种错误：
- Agent 超时
- Agent 崩溃
- 返回无效 JSON
- 外部 API 失败
- 资源不足
- 网络错误

需要统一的错误处理策略来：
- 提供一致的用户体验
- 保证系统稳定性
- 支持错误恢复
- 提供有意义的错误信息

## 选项

### 选项 A: 重试 + 降级 + 通知（推荐）
- 自动重试可恢复错误
- 降级到部分结果
- 用户通知机制

**优点**：
- 用户体验好
- 系统弹性高
- 错误可见

**缺点**：
- 实现复杂度

### 选项 B: 简单重试
- 只做重试，失败即报错

**优点**：
- 简单

**缺点**：
- 用户体验差

### 选项 C: 立即失败
- 任何错误直接返回

**优点**：
- 实现简单

**缺点**：
- 用户体验差
- 系统脆弱

## 决策

**采用选项 A：重试 + 降级 + 通知**

## 详细设计

### 1. 错误分类

```typescript
// 错误类型定义
enum AgentErrorCode {
  // 执行错误
  TIMEOUT = 'TIMEOUT',                    // 执行超时
  CRASH = 'CRASH',                        // Agent 崩溃
  RESOURCE_EXHAUSTED = 'RESOURCE_EXHAUSTED',  // 资源不足

  // 响应错误
  INVALID_JSON = 'INVALID_JSON',          // 无效 JSON
  SCHEMA_VIOLATION = 'SCHEMA_VIOLATION',  // 不符合 Schema
  PARTIAL_RESULT = 'PARTIAL_RESULT',     // 部分结果

  // 外部错误
  EXTERNAL_API_ERROR = 'EXTERNAL_API_ERROR',  // 外部 API 错误
  NETWORK_ERROR = 'NETWORK_ERROR',            // 网络错误
  AUTHENTICATION_ERROR = 'AUTHENTICATION_ERROR',  // 认证错误

  // 业务错误
  VALIDATION_ERROR = 'VALIDATION_ERROR',  // 验证错误
  NOT_FOUND = 'NOT_FOUND',               // 资源不存在
  PERMISSION_DENIED = 'PERMISSION_DENIED',  // 权限不足

  // 系统错误
  INTERNAL_ERROR = 'INTERNAL_ERROR',     // 内部错误
  UNKNOWN = 'UNKNOWN',                   // 未知错误
}

// 错误对象
interface AgentError {
  code: AgentErrorCode;
  message: string;
  details?: Record<string, any>;

  // 可恢复性
  recoverable: boolean;
  retry_after?: number;  // 建议重试等待时间（毫秒）

  // 上下文
  request_id: string;
  agent_id: string;
  timestamp: string;

  // 链路追踪
  trace_id?: string;
  span_id?: string;
}

// 错误严重级别
enum ErrorSeverity {
  LOW = 'low',          // 可忽略，降级处理
  MEDIUM = 'medium',    // 需要重试
  HIGH = 'high',        // 需要人工干预
  CRITICAL = 'critical', // 系统级问题
}

// 错误分类配置
const ERROR_CONFIG: Record<AgentErrorCode, {
  severity: ErrorSeverity;
  recoverable: boolean;
  retry_config?: RetryConfig;
}> = {
  [AgentErrorCode.TIMEOUT]: {
    severity: ErrorSeverity.MEDIUM,
    recoverable: true,
    retry_config: { max_attempts: 2, backoff: 'exponential', base_delay: 1000 },
  },
  [AgentErrorCode.CRASH]: {
    severity: ErrorSeverity.HIGH,
    recoverable: true,
    retry_config: { max_attempts: 1, backoff: 'fixed', base_delay: 2000 },
  },
  [AgentErrorCode.INVALID_JSON]: {
    severity: ErrorSeverity.MEDIUM,
    recoverable: true,
    retry_config: { max_attempts: 3, backoff: 'exponential', base_delay: 500 },
  },
  [AgentErrorCode.EXTERNAL_API_ERROR]: {
    severity: ErrorSeverity.MEDIUM,
    recoverable: true,
    retry_config: { max_attempts: 3, backoff: 'exponential', base_delay: 2000 },
  },
  [AgentErrorCode.NETWORK_ERROR]: {
    severity: ErrorSeverity.MEDIUM,
    recoverable: true,
    retry_config: { max_attempts: 3, backoff: 'exponential', base_delay: 1000 },
  },
  [AgentErrorCode.PERMISSION_DENIED]: {
    severity: ErrorSeverity.HIGH,
    recoverable: false,
  },
  [AgentErrorCode.VALIDATION_ERROR]: {
    severity: ErrorSeverity.LOW,
    recoverable: false,
  },
  // ... 其他错误配置
};
```

### 2. 重试策略

```typescript
// 重试配置
interface RetryConfig {
  max_attempts: number;      // 最大重试次数
  backoff: 'fixed' | 'linear' | 'exponential';
  base_delay: number;        // 基础延迟（毫秒）
  max_delay?: number;        // 最大延迟
  jitter?: boolean;          // 是否添加抖动
}

// 重试执行器
class RetryExecutor {
  async execute<T>(
    fn: () => Promise<T>,
    config: RetryConfig,
    onError: (error: Error, attempt: number) => void
  ): Promise<T> {
    let lastError: Error | null = null;

    for (let attempt = 1; attempt <= config.max_attempts + 1; attempt++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error as Error;
        onError(error, attempt);

        if (attempt <= config.max_attempts) {
          const delay = this.calculateDelay(config, attempt);
          await this.sleep(delay);
        }
      }
    }

    throw lastError;
  }

  private calculateDelay(config: RetryConfig, attempt: number): number {
    let delay: number;

    switch (config.backoff) {
      case 'fixed':
        delay = config.base_delay;
        break;
      case 'linear':
        delay = config.base_delay * attempt;
        break;
      case 'exponential':
        delay = config.base_delay * Math.pow(2, attempt - 1);
        break;
    }

    if (config.max_delay) {
      delay = Math.min(delay, config.max_delay);
    }

    if (config.jitter) {
      // 添加 0-25% 的随机抖动
      delay = delay * (1 + Math.random() * 0.25);
    }

    return Math.floor(delay);
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// 使用示例
const executor = new RetryExecutor();

const result = await executor.execute(
  () => agent.invoke(request),
  {
    max_attempts: 3,
    backoff: 'exponential',
    base_delay: 1000,
    max_delay: 10000,
    jitter: true,
  },
  (error, attempt) => {
    logger.warn(`Agent call failed (attempt ${attempt}):`, error.message);
  }
);
```

### 3. 降级策略

```typescript
// 降级配置
interface FallbackConfig {
  enabled: boolean;
  strategy: 'partial_result' | 'cached_result' | 'default_result' | 'error';
  cache_ttl?: number;  // 缓存有效期（秒）
}

// 降级处理器
class FallbackHandler {
  private cache: Map<string, { result: any; timestamp: number }> = new Map();

  async handle<T>(
    error: AgentError,
    originalRequest: AgentRequest,
    config: FallbackConfig
  ): Promise<{ result: T | null; fallback_used: boolean; fallback_type?: string }> {
    if (!config.enabled) {
      return { result: null, fallback_used: false };
    }

    switch (config.strategy) {
      case 'partial_result':
        // 返回部分结果（如果 Agent 返回了部分数据）
        return this.handlePartialResult(error);

      case 'cached_result':
        // 返回缓存结果
        return this.handleCachedResult(originalRequest, config.cache_ttl);

      case 'default_result':
        // 返回默认结果
        return this.handleDefaultResult(originalRequest);

      case 'error':
      default:
        // 不降级，返回错误
        return { result: null, fallback_used: false };
    }
  }

  private handlePartialResult<T>(error: AgentError): { result: T | null; fallback_used: boolean; fallback_type?: string } {
    // 检查是否有部分结果
    if (error.details?.partial_result) {
      return {
        result: error.details.partial_result as T,
        fallback_used: true,
        fallback_type: 'partial',
      };
    }
    return { result: null, fallback_used: false };
  }

  private handleCachedResult<T>(
    request: AgentRequest,
    ttl?: number
  ): { result: T | null; fallback_used: boolean; fallback_type?: string } {
    const cacheKey = this.getCacheKey(request);
    const cached = this.cache.get(cacheKey);

    if (cached) {
      const age = (Date.now() - cached.timestamp) / 1000;
      if (!ttl || age < ttl) {
        return {
          result: cached.result as T,
          fallback_used: true,
          fallback_type: 'cached',
        };
      }
    }

    return { result: null, fallback_used: false };
  }

  private handleDefaultResult<T>(
    request: AgentRequest
  ): { result: T | null; fallback_used: boolean; fallback_type?: string } {
    // 根据请求类型返回默认结果
    const defaults: Record<string, any> = {
      'dns:query': { records: [], message: 'No records found (fallback)' },
      'k8s:status': { status: 'unknown', message: 'Status unavailable (fallback)' },
      'deploy:status': { status: 'unknown', message: 'Deployment status unavailable (fallback)' },
    };

    const defaultResult = defaults[request.context?.action || ''];
    if (defaultResult) {
      return {
        result: defaultResult as T,
        fallback_used: true,
        fallback_type: 'default',
      };
    }

    return { result: null, fallback_used: false };
  }

  // 缓存成功结果以备降级使用
  cacheResult(request: AgentRequest, result: any): void {
    const cacheKey = this.getCacheKey(request);
    this.cache.set(cacheKey, {
      result,
      timestamp: Date.now(),
    });
  }

  private getCacheKey(request: AgentRequest): string {
    return `${request.agent_id}:${request.context?.action || 'default'}:${JSON.stringify(request.context)}`;
  }
}
```

### 4. 错误响应标准化

```typescript
// 标准错误响应
interface AgentErrorResponse {
  // 响应状态
  status: 'error';

  // 错误信息
  error: {
    code: AgentErrorCode;
    message: string;
    user_message: string;  // 用户友好的消息
    details?: Record<string, any>;
  };

  // 重试信息
  retry?: {
    allowed: boolean;
    after?: number;  // 建议等待时间（毫秒）
    attempt?: number;  // 当前重试次数
  };

  // 降级信息
  fallback?: {
    used: boolean;
    type?: 'partial' | 'cached' | 'default';
    result?: any;
  };

  // 上下文
  request_id: string;
  agent_id: string;
  timestamp: string;
}

// 错误响应生成器
class ErrorResponseBuilder {
  build(error: AgentError, context: {
    request_id: string;
    agent_id: string;
    retry_info?: { allowed: boolean; after?: number; attempt?: number };
    fallback_info?: { used: boolean; type?: string; result?: any };
  }): AgentErrorResponse {
    return {
      status: 'error',
      error: {
        code: error.code,
        message: error.message,
        user_message: this.getUserMessage(error),
        details: error.details,
      },
      retry: context.retry_info ? {
        allowed: context.retry_info.allowed,
        after: context.retry_info.after,
        attempt: context.retry_info.attempt,
      } : undefined,
      fallback: context.fallback_info ? {
        used: context.fallback_info.used,
        type: context.fallback_info.type as any,
        result: context.fallback_info.result,
      } : undefined,
      request_id: context.request_id,
      agent_id: context.agent_id,
      timestamp: new Date().toISOString(),
    };
  }

  private getUserMessage(error: AgentError): string {
    const messages: Record<AgentErrorCode, string> = {
      [AgentErrorCode.TIMEOUT]: '操作超时，请稍后重试',
      [AgentErrorCode.CRASH]: '服务暂时不可用，请稍后重试',
      [AgentErrorCode.INVALID_JSON]: '响应格式错误，正在尝试修复...',
      [AgentErrorCode.EXTERNAL_API_ERROR]: '外部服务暂时不可用',
      [AgentErrorCode.NETWORK_ERROR]: '网络连接失败，请检查网络',
      [AgentErrorCode.PERMISSION_DENIED]: '您没有权限执行此操作',
      [AgentErrorCode.VALIDATION_ERROR]: '请求参数无效',
      [AgentErrorCode.NOT_FOUND]: '请求的资源不存在',
      // ... 其他错误消息
    };

    return messages[error.code] || '操作失败，请稍后重试';
  }
}
```

### 5. 通知机制

```typescript
// 通知配置
interface NotificationConfig {
  channels: ('ui' | 'email' | 'slack' | 'webhook')[];
  severity_filter: ErrorSeverity[];  // 哪些级别的错误需要通知
  throttle_seconds: number;  // 相同错误的通知间隔
}

// 通知处理器
class NotificationHandler {
  private notificationHistory: Map<string, number> = new Map();

  async notify(error: AgentError, context: {
    user_id?: string;
    request_id: string;
    agent_id: string;
  }): Promise<void> {
    const config = this.getConfigForError(error);
    const severity = ERROR_CONFIG[error.code]?.severity || ErrorSeverity.MEDIUM;

    // 检查是否需要通知
    if (!config.severity_filter.includes(severity)) {
      return;
    }

    // 检查节流
    const throttleKey = `${error.code}:${context.agent_id}`;
    const lastNotified = this.notificationHistory.get(throttleKey);
    if (lastNotified && Date.now() - lastNotified < config.throttle_seconds * 1000) {
      return;
    }

    // 发送通知
    const notification = this.buildNotification(error, context);

    for (const channel of config.channels) {
      await this.sendToChannel(channel, notification);
    }

    // 记录通知历史
    this.notificationHistory.set(throttleKey, Date.now());
  }

  private buildNotification(error: AgentError, context: any): Notification {
    return {
      title: `Agent 错误: ${error.code}`,
      message: error.message,
      severity: ERROR_CONFIG[error.code]?.severity || ErrorSeverity.MEDIUM,
      details: {
        request_id: context.request_id,
        agent_id: context.agent_id,
        timestamp: new Date().toISOString(),
        error_details: error.details,
      },
      actions: [
        { label: '查看详情', url: `/agents/${context.agent_id}/errors/${context.request_id}` },
        { label: '重试', action: 'retry' },
      ],
    };
  }

  private async sendToChannel(channel: string, notification: Notification): Promise<void> {
    switch (channel) {
      case 'ui':
        // 通过 WebSocket 推送到前端
        await this.pushToUI(notification);
        break;
      case 'email':
        await this.sendEmail(notification);
        break;
      case 'slack':
        await this.sendSlack(notification);
        break;
      case 'webhook':
        await this.sendWebhook(notification);
        break;
    }
  }

  private getConfigForError(error: AgentError): NotificationConfig {
    // 根据错误类型返回不同的通知配置
    const severity = ERROR_CONFIG[error.code]?.severity;

    if (severity === ErrorSeverity.CRITICAL) {
      return {
        channels: ['ui', 'email', 'slack'],
        severity_filter: [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH],
        throttle_seconds: 60,
      };
    }

    return {
      channels: ['ui'],
      severity_filter: [ErrorSeverity.HIGH, ErrorSeverity.MEDIUM],
      throttle_seconds: 300,
    };
  }
}
```

### 6. 完整错误处理流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Agent 错误处理流程                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐                                                            │
│  │ Agent 调用  │                                                            │
│  └──────┬──────┘                                                            │
│         │                                                                    │
│         ▼                                                                    │
│  ┌─────────────┐     成功      ┌─────────────┐                               │
│  │   执行     │──────────────▶│  返回结果   │                               │
│  └──────┬──────┘              └─────────────┘                               │
│         │ 错误                                                               │
│         ▼                                                                    │
│  ┌─────────────┐                                                            │
│  │ 分类错误    │                                                            │
│  └──────┬──────┘                                                            │
│         │                                                                    │
│         ├──────────────▶ 不可恢复 ──────▶ 降级处理 ─────▶ 返回降级结果       │
│         │                                                                    │
│         ├──────────────▶ 可重试 ──────▶ 重试执行                             │
│         │                                      │                             │
│         │                                      ├── 成功 ──▶ 返回结果         │
│         │                                      │                             │
│         │                                      └── 失败 ──▶ 降级处理         │
│         │                                                                    │
│         └──────────────▶ 降级失败 ──▶ 通知用户 ──▶ 返回错误                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 后果

### 正面
- 统一的错误处理体验
- 自动恢复可恢复错误
- 用户友好的错误消息
- 完善的通知机制

### 负面
- 实现复杂度增加
- 需要维护缓存

## 实现

1. **Phase 3.5**: 实现基础错误分类和重试
2. **Phase 4**: 实现降级策略和通知
