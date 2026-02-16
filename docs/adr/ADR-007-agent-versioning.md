# ADR-007: Agent 版本兼容性

## 状态
已接受 (2024-02-16)

## 背景

Agent 会不断演进，不同版本之间可能存在：
- 接口变更（新增/删除/修改参数）
- 行为变更（输出格式变化）
- 依赖变更（依赖的 API 版本变化）

需要明确的版本兼容性策略来解决：
- 用户升级 Agent 时如何保证兼容
- 多版本共存时的处理
- 不兼容版本的迁移路径
- 废弃策略

## 选项

### 选项 A: 语义化版本 + 多版本共存（推荐）
- 严格遵循 SemVer
- 支持多版本同时运行
- 提供迁移工具

**优点**：
- 清晰的版本语义
- 平滑升级
- 回滚容易

**缺点**：
- 维护多版本成本

### 选项 B: 单版本强制升级
- 只维护最新版本
- 强制用户升级

**优点**：
- 维护简单

**缺点**：
- 用户体验差
- 升级风险高

### 选项 C: 长期支持(LTS)版本
- 部分版本标记为 LTS
- LTS 长期维护

**优点**：
- 稳定性好

**缺点**：
- 维护成本高

## 决策

**采用选项 A：语义化版本 + 多版本共存**

## 详细设计

### 1. 版本规范

```typescript
// 版本号格式：MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]

interface AgentVersion {
  major: number;      // 主版本：不兼容的 API 变更
  minor: number;      // 次版本：向后兼容的功能新增
  patch: number;      // 补丁版本：向后兼容的问题修复
  prerelease?: string; // 预发布标识：alpha, beta, rc
  build?: string;     // 构建元数据

  // 完整版本字符串
  toString(): string;
}

// 版本解析
function parseVersion(versionString: string): AgentVersion {
  const regex = /^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.-]+))?(?:\+([a-zA-Z0-9.-]+))?$/;
  const match = versionString.match(regex);

  if (!match) {
    throw new Error(`Invalid version string: ${versionString}`);
  }

  return {
    major: parseInt(match[1]),
    minor: parseInt(match[2]),
    patch: parseInt(match[3]),
    prerelease: match[4],
    build: match[5],
    toString: () => versionString,
  };
}

// 版本比较
function compareVersions(a: AgentVersion, b: AgentVersion): number {
  if (a.major !== b.major) return a.major - b.major;
  if (a.minor !== b.minor) return a.minor - b.minor;
  return a.patch - b.patch;
}

// 版本兼容性检查
function isCompatible(consumer: AgentVersion, provider: AgentVersion): boolean {
  // 主版本必须相同
  if (consumer.major !== provider.major) return false;

  // 消费者的次版本不能高于提供者
  if (consumer.minor > provider.minor) return false;

  return true;
}
```

### 2. 变更类型定义

```typescript
// 变更类型
enum ChangeType {
  // PATCH 级别变更
  BUG_FIX = 'bug_fix',           // Bug 修复
  PERFORMANCE = 'performance',   // 性能优化
  DOCUMENTATION = 'docs',        // 文档更新

  // MINOR 级别变更
  FEATURE_ADDED = 'feature_added',       // 新增功能
  FEATURE_DEPRECATED = 'feature_deprecated', // 功能废弃
  PARAMETER_OPTIONAL = 'param_optional', // 参数变为可选

  // MAJOR 级别变更
  BREAKING_CHANGE = 'breaking',      // 破坏性变更
  FEATURE_REMOVED = 'feature_removed', // 功能移除
  PARAMETER_CHANGED = 'param_changed', // 参数变更
  OUTPUT_CHANGED = 'output_changed',   // 输出格式变更
}

// 变更记录
interface ChangeRecord {
  version: string;
  type: ChangeType;
  description: string;
  impact: 'low' | 'medium' | 'high';
  migration_guide?: string;
}

// CHANGELOG 示例
const CHANGELOG: ChangeRecord[] = [
  {
    version: '2.0.0',
    type: ChangeType.BREAKING_CHANGE,
    description: '重构 Agent 间通信协议，采用 A2A 标准',
    impact: 'high',
    migration_guide: 'docs/migration/v1-to-v2.md',
  },
  {
    version: '2.0.0',
    type: ChangeType.FEATURE_REMOVED,
    description: '移除 deprecated_api 方法',
    impact: 'medium',
  },
  {
    version: '2.1.0',
    type: ChangeType.FEATURE_ADDED,
    description: '新增批量操作支持',
    impact: 'low',
  },
  {
    version: '2.1.0',
    type: ChangeType.PARAMETER_OPTIONAL,
    description: 'timeout 参数变为可选，默认 30s',
    impact: 'low',
  },
  {
    version: '2.1.1',
    type: ChangeType.BUG_FIX,
    description: '修复并发时的内存泄漏问题',
    impact: 'low',
  },
];
```

### 3. 兼容性声明

```yaml
# agent-manifest.yaml
agent_id: com.nexusops.agents.dns
version: 2.1.0

# 兼容性声明
compatibility:
  # 支持的 NexusOps 版本范围
  nexusops_version: ">=1.0.0 <3.0.0"

  # 依赖的其他 Agent
  agent_dependencies:
    - agent_id: com.nexusops.agents.ssl
      version_range: ">=2.0.0 <3.0.0"
    - agent_id: com.nexusops.agents.k8s
      version_range: ">=1.5.0 <2.0.0"
      optional: true

  # 外部 API 依赖
  external_dependencies:
    - name: cloudflare-api
      version_range: ">=4.0.0"
      deprecation_notice: null

    - name: route53-api
      version_range: ">=1.0.0"
      deprecation_notice: "Will be removed in v3.0.0, migrate to cloudflare-api"

  # 向后兼容
  backwards_compatibility:
    # 支持的旧版接口
    supported_legacy_versions:
      - "1.x"
    # 废弃但仍然支持的参数
    deprecated_parameters:
      - name: "old_param"
        deprecated_in: "2.0.0"
        removal_in: "3.0.0"
        replacement: "new_param"
```

### 4. 多版本共存

```typescript
// Agent 注册表中的多版本支持
interface AgentRegistry {
  // 注册 Agent 版本
  register(manifest: AgentManifest): Promise<void>;

  // 获取可用版本
  getAvailableVersions(agentId: string): Promise<AgentVersion[]>;

  // 获取特定版本
  getVersion(agentId: string, version: string): Promise<AgentManifest | null>;

  // 获取兼容版本
  getCompatibleVersion(
    agentId: string,
    requiredRange: string
  ): Promise<AgentManifest | null>;

  // 设置默认版本
  setDefaultVersion(agentId: string, version: string): Promise<void>;

  // 获取默认版本
  getDefaultVersion(agentId: string): Promise<string>;
}

// 版本选择器
class AgentVersionSelector {
  private registry: AgentRegistry;

  // 选择最佳版本
  async selectVersion(
    agentId: string,
    constraints: VersionConstraint[]
  ): Promise<string> {
    const availableVersions = await this.registry.getAvailableVersions(agentId);

    // 过滤满足所有约束的版本
    const compatibleVersions = availableVersions.filter(v =>
      constraints.every(c => this.satisfiesConstraint(v, c))
    );

    if (compatibleVersions.length === 0) {
      throw new VersionConflictError(
        `No compatible version found for ${agentId} with constraints: ${JSON.stringify(constraints)}`
      );
    }

    // 返回最新的兼容版本
    return compatibleVersions.sort((a, b) =>
      compareVersions(b, a)
    )[0].toString();
  }

  private satisfiesConstraint(version: AgentVersion, constraint: VersionConstraint): boolean {
    const targetVersion = parseVersion(constraint.version);

    switch (constraint.operator) {
      case '=':
        return compareVersions(version, targetVersion) === 0;
      case '>':
        return compareVersions(version, targetVersion) > 0;
      case '>=':
        return compareVersions(version, targetVersion) >= 0;
      case '<':
        return compareVersions(version, targetVersion) < 0;
      case '<=':
        return compareVersions(version, targetVersion) <= 0;
      case '^':
        // 兼容版本：相同主版本，且次版本 >= 目标
        return version.major === targetVersion.major &&
               compareVersions(version, targetVersion) >= 0;
      case '~':
        // 补丁兼容：相同主版本和次版本
        return version.major === targetVersion.major &&
               version.minor === targetVersion.minor &&
               version.patch >= targetVersion.patch;
      default:
        return false;
    }
  }
}

// 版本约束
interface VersionConstraint {
  version: string;
  operator: '=' | '>' | '>=' | '<' | '<=' | '^' | '~';
}
```

### 5. 版本迁移

```typescript
// 迁移器接口
interface AgentMigrator {
  // 从旧版本迁移到新版本
  migrate(fromVersion: string, toVersion: string, data: any): Promise<MigrationResult>;

  // 检查是否需要迁移
  needsMigration(fromVersion: string, toVersion: string): boolean;

  // 获取迁移说明
  getMigrationGuide(fromVersion: string, toVersion: string): MigrationGuide;
}

// 迁移结果
interface MigrationResult {
  success: boolean;
  migrated_data: any;
  warnings: string[];
  errors: string[];
}

// 迁移指南
interface MigrationGuide {
  from_version: string;
  to_version: string;
  breaking_changes: BreakingChange[];
  deprecated_features: DeprecatedFeature[];
  migration_steps: MigrationStep[];
  estimated_time: string;
}

// 迁移步骤
interface MigrationStep {
  order: number;
  description: string;
  automated: boolean;
  command?: string;
  manual_steps?: string[];
}

// DNS Agent 迁移器示例
class DNSAgentMigrator implements AgentMigrator {
  async migrate(fromVersion: string, toVersion: string, data: any): Promise<MigrationResult> {
    const result: MigrationResult = {
      success: true,
      migrated_data: { ...data },
      warnings: [],
      errors: [],
    };

    // v1 -> v2 迁移
    if (fromVersion.startsWith('1.') && toVersion.startsWith('2.')) {
      // 重命名参数
      if (result.migrated_data.zone) {
        result.migrated_data.zone_id = result.migrated_data.zone;
        delete result.migrated_data.zone;
        result.warnings.push('Parameter "zone" renamed to "zone_id"');
      }

      // 更新输出格式
      if (result.migrated_data.records) {
        result.migrated_data.records = result.migrated_data.records.map((r: any) => ({
          ...r,
          // v2 新增字段
          created_at: r.created_at || new Date().toISOString(),
          provider: r.provider || 'cloudflare',
        }));
      }
    }

    return result;
  }

  needsMigration(fromVersion: string, toVersion: string): boolean {
    const from = parseVersion(fromVersion);
    const to = parseVersion(toVersion);
    return from.major !== to.major;
  }

  getMigrationGuide(fromVersion: string, toVersion: string): MigrationGuide {
    return {
      from_version: fromVersion,
      to_version: toVersion,
      breaking_changes: [
        {
          description: '参数 zone 重命名为 zone_id',
          impact: '所有使用 zone 参数的调用需要更新',
        },
        {
          description: '输出格式增加 provider 字段',
          impact: '依赖输出格式的代码需要适配',
        },
      ],
      deprecated_features: [
        {
          name: 'old_api_endpoint',
          deprecated_in: '2.0.0',
          removal_in: '3.0.0',
          replacement: 'new_api_endpoint',
        },
      ],
      migration_steps: [
        {
          order: 1,
          description: '备份现有配置',
          automated: false,
          manual_steps: [
            '导出当前 Agent 配置',
            '保存到安全位置',
          ],
        },
        {
          order: 2,
          description: '更新参数名',
          automated: true,
          command: 'nexusops agent migrate dns --from v1 --to v2',
        },
        {
          order: 3,
          description: '验证迁移结果',
          automated: false,
          manual_steps: [
            '检查迁移后的配置',
            '运行测试用例',
          ],
        },
      ],
      estimated_time: '5-10 minutes',
    };
  }
}
```

### 6. 废弃策略

```typescript
// 废弃计划
interface DeprecationPlan {
  feature_name: string;
  deprecated_in: string;
  removal_in: string;
  replacement?: string;
  migration_guide_url?: string;
}

// 废弃警告处理器
class DeprecationHandler {
  private deprecations: Map<string, DeprecationPlan> = new Map();

  // 注册废弃计划
  register(plan: DeprecationPlan): void {
    this.deprecations.set(plan.feature_name, plan);
  }

  // 检查并发出警告
  check(featureName: string, currentVersion: string): DeprecationWarning | null {
    const plan = this.deprecations.get(featureName);
    if (!plan) return null;

    const current = parseVersion(currentVersion);
    const removal = parseVersion(plan.removal_in);
    const deprecated = parseVersion(plan.deprecated_in);

    // 已移除
    if (compareVersions(current, removal) >= 0) {
      throw new FeatureRemovedError(
        `Feature "${featureName}" was removed in version ${plan.removal_in}. Use ${plan.replacement || 'alternative'} instead.`
      );
    }

    // 已废弃
    if (compareVersions(current, deprecated) >= 0) {
      return {
        severity: this.calculateSeverity(current, deprecated, removal),
        message: `Feature "${featureName}" is deprecated since version ${plan.deprecated_in} and will be removed in ${plan.removal_in}`,
        replacement: plan.replacement,
        migration_guide: plan.migration_guide_url,
      };
    }

    return null;
  }

  private calculateSeverity(
    current: AgentVersion,
    deprecated: AgentVersion,
    removal: AgentVersion
  ): 'info' | 'warning' | 'critical' {
    // 计算距离移除的时间
    const deprecatedMajor = deprecated.major;
    const removalMajor = removal.major;
    const currentMajor = current.major;

    // 如果当前版本接近移除版本
    if (removalMajor - currentMajor <= 1) {
      return 'critical';
    }

    return 'warning';
  }
}

// 使用示例
const deprecationHandler = new DeprecationHandler();

deprecationHandler.register({
  feature_name: 'create_dns_record_v1',
  deprecated_in: '2.0.0',
  removal_in: '3.0.0',
  replacement: 'create_dns_record_v2',
  migration_guide_url: 'https://docs.nexusops.io/agents/dns/migration',
});

// 在 Agent 中检查
function createDNSRecord(params: any) {
  const warning = deprecationHandler.check('create_dns_record_v1', currentVersion);
  if (warning) {
    console.warn(`[${warning.severity.toUpperCase()}] ${warning.message}`);
    if (warning.replacement) {
      console.warn(`  Replacement: ${warning.replacement}`);
    }
  }

  // 实际逻辑
}
```

### 7. 版本生命周期

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Agent 版本生命周期                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌────────┐│
│  │  Alpha   │───▶│  Beta    │───▶│  Stable  │───▶│Deprecated│───▶│ EOL    ││
│  │          │    │          │    │          │    │          │    │        ││
│  │ 内部测试  │    │ 公开测试  │    │ 正式发布  │    │ 废弃警告  │    │ 停止支持││
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └────────┘│
│       │              │              │              │              │        │
│       │              │              │              │              │        │
│    1-2 周         2-4 周         6-12 月        3-6 月         移除      │
│                                                                              │
│  时间线示例 (DNS Agent v2.x):                                                │
│                                                                              │
│  2024-02 ──▶ 2024-03 ──▶ 2024-04 ──▶ 2025-04 ──▶ 2025-07 ──▶ 2025-10       │
│  2.0.0-alpha  2.0.0-beta  2.0.0      废弃警告     移除支持      清理        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 后果

### 正面
- 清晰的版本语义
- 平滑的升级路径
- 多版本支持
- 完善的废弃策略

### 负面
- 维护多版本成本
- 迁移工具开发
- 测试矩阵复杂度

## 实现

1. **Phase 3.5**: 实现版本解析和比较
2. **Phase 4**: 实现多版本注册表
3. **Phase 4**: 实现迁移工具
4. **Phase 5**: 实现废弃警告系统
