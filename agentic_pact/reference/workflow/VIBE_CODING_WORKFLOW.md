# NexusOps Vibe Coding 工作流设计

## 概述

NexusOps 是面向研发/算法的运维平台，核心目标是支持 **Vibe Coding** 工作流：

> **Vibe Coding** = 快速开发 + 快速迭代 + 快速上线

## 核心工作流

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Vibe Coding Workflow                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. 快速验证                                                              │
│  ┌─────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │ 创建版本 │ → │ 自动部署测试 │ → │ 获取测试 URL │ → │ 验证功能    │  │
│  │ (Phoenix)│    │ (dev/staging)│    │             │    │             │  │
│  └─────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│        │                                    ↓                            │
│        │                              ┌─────────┐                        │
│        │                              │ 有问题? │                        │
│        │                              └────┬────┘                        │
│        │                                   │ 是                          │
│        ↓                                   ↓                              │
│  ┌─────────────┐                    ┌─────────────┐                      │
│  │ 迭代修复    │ ←───────────────── │ 快速回滚    │                      │
│  │ 更新镜像    │                    │             │                      │
│  └─────────────┘                    └─────────────┘                      │
│        │                                                                 │
│        │ 否（验证通过）                                                   │
│        ↓                                                                 │
│  2. 快速上线                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                  │
│  │ 申请上线    │ → │ Admin 审批   │ → │ 一键上线    │                  │
│  │ (生产版本)  │    │             │    │ (多区域)    │                  │
│  └─────────────┘    └─────────────┘    └─────────────┘                  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 页面交互优化

### 1. Projects 页面 - Vibe Coding 核心入口

**当前状态**: 已实现版本管理基础功能

**优化方向**:

#### 1.1 版本卡片增强
```
┌─────────────────────────────────────────────────────────────────┐
│ [⭐] Phoenix                                    [测试版本] [运行中] │
├─────────────────────────────────────────────────────────────────┤
│ 测试链接: https://phoenix.test.pipecat.internal  [复制] [打开]   │
│ 部署区域: US-East, EU-Central, AP-Southeast                     │
│ 镜像: harbor.local/pipecat-app-a:phoenix-rc3                    │
│ Git: feature/phoenix-refactor @ a1b2c3d                          │
│ ArgoCD: [查看]   最后部署: 2小时前 by Jane                        │
├─────────────────────────────────────────────────────────────────┤
│ [🔄 重新部署] [📋 复制配置] [🚀 申请上线] [📊 查看监控]           │
└─────────────────────────────────────────────────────────────────┘
```

#### 1.2 新增操作流程
| 操作 | 描述 | 目标耗时 |
|------|------|----------|
| **创建版本** | 输入 codename + Git 分支 → 自动触发 CI/CD | < 1 分钟 |
| **获取测试 URL** | 版本创建后自动生成测试环境 URL | 自动 |
| **重新部署** | 快速重新部署最新镜像 | < 2 分钟 |
| **申请上线** | 一键发起生产上线审批 | < 1 分钟 |

#### 1.3 交互优化建议

```typescript
// 优化后的版本卡片信息
interface VersionCard {
  codename: string
  status: 'testing' | 'production' | 'archived'

  // 快速验证信息
  testUrl: string           // 测试环境 URL
  testUrlQrCode?: string    // QR 码（移动端扫码验证）
  deployedRegions: string[] // 已部署区域

  // GitOps 信息
  gitBranch: string
  gitCommit: string
  gitCommitUrl: string
  argocdApp: string
  argocdUrl: string

  // 快速操作
  actions: {
    redeploy: () => void    // 重新部署
    copyConfig: () => void  // 复制配置到新版本
    requestProd: () => void // 申请上线
    viewMetrics: () => void // 查看监控
    viewLogs: () => void    // 查看日志
  }
}
```

---

### 2. Dashboard 页面 - 全局视角

**优化方向**:

#### 2.1 测试版本概览
```
┌─────────────────────────────────────────────────────────────────┐
│ 测试版本概览                                    [查看全部 →]     │
├─────────────────────────────────────────────────────────────────┤
│ Phoenix    ● US-East (健康)  ● EU-Central (健康)  [申请上线]    │
│ Titan      ● US-East (警告)  [查看详情]                         │
│ Nova       ● US-East (部署中...)                               │
│ Aurora     ● US-East (健康)  ● AP-Southeast (健康)  [申请上线]  │
└─────────────────────────────────────────────────────────────────┘
```

#### 2.2 WorldMap 增强
- 按版本代号筛选显示
- 悬浮显示版本详情（Git 分支、镜像、测试 URL）
- 点击跳转到版本详情页

---

### 3. Deployments 页面 - 部署链追踪

**当前状态**: 已实现部署列表和时间线

**优化方向**:

#### 3.1 快速定位问题
```
┌─────────────────────────────────────────────────────────────────┐
│ 部署链: Phoenix → US-East                                       │
├─────────────────────────────────────────────────────────────────┤
│ ✅ Code Push    → a1b2c3d "feat: add new endpoint"              │
│ ✅ CI Build     → harbor.local/pipecat-app-a:phoenix-rc3       │
│ ✅ Image Scan   → 0 vulnerabilities                              │
│ ⚠️ ArgoCD Sync  → Out of Sync (manifest drift detected)         │
│    └─ [查看差异] [强制同步] [回滚]                               │
│ ⏳ Health Check → Waiting for pods to be ready...               │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.2 一键操作
- **强制同步**: 当 ArgoCD 检测到 drift 时一键同步
- **快速回滚**: 回滚到上一个稳定版本
- **查看日志**: 跳转到 Grafana/Loki 查看日志
- **进入 Pod**: 一键 kubectl exec 进入 Pod 调试

---

### 4. AI Assistant - Vibe Coding 助手

**当前状态**: 已实现基础对话

**优化方向**:

#### 4.1 上下文感知
```typescript
// AI 助手自动感知当前页面上下文
interface AIContext {
  currentPage: 'projects' | 'dashboard' | 'deployments' | 'resources'
  selectedVersion?: Version
  selectedRegion?: Region
  recentActions: Action[]
}

// 智能推荐
const recommendations = [
  "Phoenix 版本已验证通过，是否申请上线？",
  "检测到 US-East 区域 CPU 使用率过高，建议扩容",
  "Titan 版本在 AP-East 部署失败，点击查看原因",
]
```

#### 4.2 快捷命令
| 命令 | 描述 |
|------|------|
| `/deploy Phoenix to US-East` | 快速部署 |
| `/rollback Titan in AP-East` | 快速回滚 |
| `/status Phoenix` | 查看版本状态 |
| `/logs api-gateway --tail 100` | 查看日志 |
| `/compare Phoenix vs legacy` | 对比版本 |

---

## 数据模型

### 核心实体关系

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│ Project     │ 1:n │ Version     │ 1:n │ Deployment      │
│ ─────────── │     │ ─────────── │     │ ───────────────  │
│ name        │     │ codename    │     │ regionId        │
│ code        │     │ gitBranch   │     │ gitCommit       │
│ owner       │     │ imageUrl    │     │ argocdApp       │
│             │     │ testUrl     │     │ argocdUrl       │
│             │     │ status      │     │ status          │
└─────────────┘     └─────────────┘     └─────────────────┘
       │                   │                     │
       │                   │                     │
       └───────────────────┴─────────────────────┘
                           │
                    ┌──────┴──────┐
                    │ Region      │
                    │ ─────────── │
                    │ id          │
                    │ name        │
                    │ provider    │
                    └─────────────┘
```

### 查询接口

```typescript
// Vibe Coding 核心查询
interface VibeCodingQueries {
  // 获取某版本的所有部署（跨区域）
  getDeploymentsByCodename(codename: string): Deployment[]

  // 获取某区域的所有部署（多版本）
  getDeploymentsByRegion(regionId: string): Deployment[]

  // 获取某项目的生产版本
  getProductionVersion(projectId: string): Version

  // 获取测试中版本（待上线）
  getTestingVersions(): Version[]

  // 获取版本健康状态
  getVersionHealth(codename: string): 'healthy' | 'warning' | 'critical'
}
```

---

## 快速操作 API

### 前端 API 调用

```typescript
// src/services/vibeCodingApi.ts

export const vibeCodingApi = {
  // 快速部署到测试环境
  async deployToTest(projectId: string, versionId: string, regions?: string[]) {
    return post('/api/v1/deployments/test', { projectId, versionId, regions })
  },

  // 获取测试 URL
  async getTestUrl(versionId: string): Promise<string> {
    return get(`/api/v1/versions/${versionId}/test-url`)
  },

  // 申请上线
  async requestProduction(versionId: string, reason: string) {
    return post('/api/v1/versions/${versionId}/request-production', { reason })
  },

  // 快速回滚
  async rollback(deploymentId: string) {
    return post(`/api/v1/deployments/${deploymentId}/rollback`)
  },

  // 强制同步 ArgoCD
  async forceSync(argocdApp: string) {
    return post('/api/v1/argocd/${argocdApp}/sync`)
  },

  // 获取部署日志
  async getDeploymentLogs(deploymentId: string, tail?: number) {
    return get(`/api/v1/deployments/${deploymentId}/logs`, { tail })
  },
}
```

---

## 后续优化建议

### Phase 1: 完善 Vibe Coding 基础（当前）
- [x] 版本管理基础功能
- [x] WorldMap 区域展示
- [x] Deployment 数据模型
- [ ] Projects 页面版本卡片增强
- [ ] 快速操作按钮（重新部署、申请上线）
- [ ] 测试 URL 显示和复制

### Phase 2: 提升效率
- [ ] 一键部署到测试环境
- [ ] 部署状态实时推送（WebSocket）
- [ ] AI 助手快捷命令
- [ ] 批量操作（多区域同时部署）

### Phase 3: 对接真实数据
- [ ] 后端 API 接入
- [ ] ArgoCD 集成
- [ ] CI/CD 触发
- [ ] 监控数据接入

---

## 参考

- [Apache ECharts World Map](https://github.com/apache/echarts-www/blob/master/asset/map/json/world.json)
- [ArgoCD API](https://argo-cd.readthedocs.io/en/stable/developer-guide/api-docs/)
- [GitOps 最佳实践](https://opengitops.dev/)
