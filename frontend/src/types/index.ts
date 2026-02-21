// User & Auth types
export interface User {
  id: string
  username: string
  email: string
  fullName: string
  role: 'admin' | 'internal' | 'vendor'
  isActive: boolean
  allowedProjects: string[] // List of project IDs the user has access to
}

// Project types
export interface Project {
  id: string
  name: string
  description: string
  ownerId: string
  createdAt: string
  updatedAt: string
}

// Region & Cluster types
export interface Region {
  id: string
  name: string
  code: string
}

export interface Cluster {
  id: string
  name: string
  regionId: string
  provider: string
  endpoint: string
  status: 'active' | 'inactive' | 'maintenance'
}

export interface Namespace {
  id: string
  name: string
  clusterId: string
  projectId: string
}

// Service types
export interface Service {
  id: string
  name: string
  namespaceId: string
  projectId: string
  replicas: number
  status: 'running' | 'stopped' | 'error' | 'unknown'
  createdAt: string
  updatedAt: string
}

// Build & Deployment types
export interface Build {
  id: string
  jobName: string
  buildNumber: number
  status: 'success' | 'failed' | 'running' | 'aborted'
  commitSha: string
  branch: string
  duration: number
  startedAt: string
  finishedAt: string | null
}

export interface Image {
  id: string
  registry: string
  repository: string
  tag: string
  digest: string
  buildId: string | null
  size: number
  vulnerabilities: number
  createdAt: string
  pushedAt: string
}

// Version Deployment - 记录某个 Project 的某个 Version 部署到哪个 Region
export interface VersionDeployment {
  id: string
  projectId: string
  projectName: string
  serviceId: string
  serviceName: string
  versionId: string
  codename: string           // 版本代号，如 Phoenix, Titan
  imageVersion: string       // 镜像版本，如 v1.2.3
  regionId: string           // 部署区域 ID
  regionName: string         // 区域名称，如 US East (AWS)

  // GitOps 信息
  gitRepo: string            // Git 仓库地址
  gitBranch: string          // Git 分支
  gitCommit: string          // Git Commit SHA
  gitCommitUrl: string       // Git Commit 链接

  // ArgoCD 信息
  argocdApp: string          // ArgoCD Application 名称
  argocdUrl: string          // ArgoCD 应用链接
  argocdSyncStatus: 'synced' | 'out-of-sync' | 'unknown'
  argocdHealthStatus: 'healthy' | 'degraded' | 'progressing' | 'unknown'
  argocdRevision: string     // ArgoCD 同步的 Git revision

  // 服务状态
  replicas: number           // 副本数
  status: 'running' | 'warning' | 'error' | 'unknown'
  cpu: string                // CPU 使用
  memory: string             // 内存使用

  // 元数据
  deployedAt: string
  deployedBy: string
}

// Legacy Deployment (保留兼容)
export interface Deployment {
  id: string
  serviceId: string
  imageId: string
  argocdApp: string
  syncStatus: 'synced' | 'out-of-sync' | 'unknown'
  healthStatus: 'healthy' | 'degraded' | 'progressing' | 'unknown'
  revision: string
  deployedAt: string
  deployedBy: string
}

// Alert types
export interface Alert {
  id: string
  source: string
  alertName: string
  severity: 'critical' | 'warning' | 'info'
  status: 'firing' | 'resolved'
  serviceId: string | null
  projectId: string | null
  summary: string
  description: string
  labels: Record<string, string>
  firedAt: string
  resolvedAt: string | null
}

// Ticket types
export interface Ticket {
  id: string
  title: string
  description: string
  type: 'request' | 'bug' | 'change' | 'vendor_task'
  status: 'open' | 'in_progress' | 'resolved' | 'closed'
  priority: 'low' | 'medium' | 'high' | 'critical'
  projectId: string
  reporterId: string
  assigneeId: string | null
  externalId: string
  externalUrl: string
  createdAt: string
  updatedAt: string
  resolvedAt: string | null
}

// AI Chat types
export interface Conversation {
  id: string
  projectId: string | null
  agentId: string
  userId: string
  title: string
  createdAt: string
  updatedAt: string
}

export interface Message {
  id: string
  conversationId: string
  role: 'user' | 'assistant' | 'system'
  content: string
  createdAt: string
}

// API Response types
export interface ApiResponse<T> {
  data: T
  error?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

// Dashboard types
export interface OverviewStats {
  services: {
    total: number
    healthy: number
    warning: number
    critical: number
  }
  clusters: {
    total: number
    healthy: number
  }
  alerts: {
    total: number
    critical: number
    warning: number
  }
}

export interface ResourceUsage {
  cpu: number
  memory: number
  storage: number
  bandwidth: number
}
