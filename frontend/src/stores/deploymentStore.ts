import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { VersionDeployment } from '../types'

// 区域定义
export const regions = [
  { id: 'us-east', name: 'US East (AWS)' },
  { id: 'us-west', name: 'US West (AWS)' },
  { id: 'eu-west', name: 'EU West (GCP)' },
  { id: 'eu-central', name: 'EU Central (AWS)' },
  { id: 'ap-east', name: 'Asia Pacific (AliCloud)' },
  { id: 'ap-southeast', name: 'AP Southeast (AWS)' },
]

// Mock 部署数据 - 展示 Project/Version 和 Region 的关联
const mockDeployments: VersionDeployment[] = [
  // US East - Phoenix 版本
  {
    id: 'dep-1',
    projectId: 'proj-1',
    projectName: 'Pipecat-Platform',
    serviceId: 'svc-1',
    serviceName: 'auth-service',
    versionId: 'ver-2',
    codename: 'Phoenix',
    imageVersion: 'v1.2.3-rc3',
    regionId: 'us-east',
    regionName: 'US East (AWS)',
    gitRepo: 'https://github.com/company/pipecat-app-a.git',
    gitBranch: 'feature/phoenix-refactor',
    gitCommit: 'a1b2c3d4e5f6',
    gitCommitUrl: 'https://github.com/company/pipecat-app-a/commit/a1b2c3d4e5f6',
    argocdApp: 'pipecat-app-a-phoenix-useast',
    argocdUrl: 'https://argocd.example.com/applications/pipecat-app-a-phoenix-useast',
    argocdSyncStatus: 'synced',
    argocdHealthStatus: 'healthy',
    argocdRevision: 'a1b2c3d4e5f6',
    replicas: 3,
    status: 'running',
    cpu: '450m',
    memory: '512Mi',
    deployedAt: '2024-01-15 10:00:00',
    deployedBy: 'Jane Smith',
  },
  {
    id: 'dep-2',
    projectId: 'proj-1',
    projectName: 'Pipecat-Platform',
    serviceId: 'svc-1',
    serviceName: 'auth-service',
    versionId: 'ver-2',
    codename: 'Phoenix',
    imageVersion: 'v1.2.3-rc3',
    regionId: 'us-east',
    regionName: 'US East (AWS)',
    gitRepo: 'https://github.com/company/pipecat-app-a.git',
    gitBranch: 'feature/phoenix-refactor',
    gitCommit: 'a1b2c3d4e5f6',
    gitCommitUrl: 'https://github.com/company/pipecat-app-a/commit/a1b2c3d4e5f6',
    argocdApp: 'chat-gateway-phoenix-useast',
    argocdUrl: 'https://argocd.example.com/applications/chat-gateway-phoenix-useast',
    argocdSyncStatus: 'synced',
    argocdHealthStatus: 'healthy',
    argocdRevision: 'a1b2c3d4e5f6',
    replicas: 2,
    status: 'running',
    cpu: '200m',
    memory: '256Mi',
    deployedAt: '2024-01-15 10:00:00',
    deployedBy: 'Jane Smith',
  },
  // US East - Titan 版本
  {
    id: 'dep-3',
    projectId: 'proj-1',
    projectName: 'Pipecat-Platform',
    serviceId: 'svc-1',
    serviceName: 'auth-service',
    versionId: 'ver-3',
    codename: 'Titan',
    imageVersion: 'v1.2.4-beta2',
    regionId: 'us-east',
    regionName: 'US East (AWS)',
    gitRepo: 'https://github.com/company/pipecat-app-a.git',
    gitBranch: 'feature/titan-translation',
    gitCommit: 'g7h8i9j0k1l2',
    gitCommitUrl: 'https://github.com/company/pipecat-app-a/commit/g7h8i9j0k1l2',
    argocdApp: 'worker-titan-useast',
    argocdUrl: 'https://argocd.example.com/applications/worker-titan-useast',
    argocdSyncStatus: 'synced',
    argocdHealthStatus: 'healthy',
    argocdRevision: 'g7h8i9j0k1l2',
    replicas: 3,
    status: 'running',
    cpu: '500m',
    memory: '1Gi',
    deployedAt: '2024-01-14 15:00:00',
    deployedBy: 'Bob Wilson',
  },
  // US West - Phoenix 版本
  {
    id: 'dep-4',
    projectId: 'proj-1',
    projectName: 'Pipecat-Platform',
    serviceId: 'svc-1',
    serviceName: 'auth-service',
    versionId: 'ver-2',
    codename: 'Phoenix',
    imageVersion: 'v1.2.3-rc3',
    regionId: 'us-west',
    regionName: 'US West (AWS)',
    gitRepo: 'https://github.com/company/pipecat-app-a.git',
    gitBranch: 'feature/phoenix-refactor',
    gitCommit: 'a1b2c3d4e5f6',
    gitCommitUrl: 'https://github.com/company/pipecat-app-a/commit/a1b2c3d4e5f6',
    argocdApp: 'pipecat-app-a-phoenix-uswest',
    argocdUrl: 'https://argocd.example.com/applications/pipecat-app-a-phoenix-uswest',
    argocdSyncStatus: 'synced',
    argocdHealthStatus: 'healthy',
    argocdRevision: 'a1b2c3d4e5f6',
    replicas: 3,
    status: 'running',
    cpu: '300m',
    memory: '384Mi',
    deployedAt: '2024-01-14 12:00:00',
    deployedBy: 'Jane Smith',
  },
  // EU West - legacy 版本 (生产)
  {
    id: 'dep-5',
    projectId: 'proj-1',
    projectName: 'Pipecat-Platform',
    serviceId: 'svc-1',
    serviceName: 'auth-service',
    versionId: 'ver-1',
    codename: 'legacy',
    imageVersion: 'v1.2.2',
    regionId: 'eu-west',
    regionName: 'EU West (GCP)',
    gitRepo: 'https://github.com/company/pipecat-app-a.git',
    gitBranch: 'main',
    gitCommit: 'm3n4o5p6q7r8',
    gitCommitUrl: 'https://github.com/company/pipecat-app-a/commit/m3n4o5p6q7r8',
    argocdApp: 'pipecat-app-a-euwest',
    argocdUrl: 'https://argocd.example.com/applications/pipecat-app-a-euwest',
    argocdSyncStatus: 'synced',
    argocdHealthStatus: 'degraded',
    argocdRevision: 'm3n4o5p6q7r8',
    replicas: 3,
    status: 'warning',
    cpu: '650m',
    memory: '780Mi',
    deployedAt: '2024-01-10 08:00:00',
    deployedBy: 'John Doe',
  },
  // EU Central - Phoenix 版本
  {
    id: 'dep-6',
    projectId: 'proj-1',
    projectName: 'Pipecat-Platform',
    serviceId: 'svc-1',
    serviceName: 'auth-service',
    versionId: 'ver-2',
    codename: 'Phoenix',
    imageVersion: 'v1.2.3-rc3',
    regionId: 'eu-central',
    regionName: 'EU Central (AWS)',
    gitRepo: 'https://github.com/company/pipecat-app-a.git',
    gitBranch: 'feature/phoenix-refactor',
    gitCommit: 'a1b2c3d4e5f6',
    gitCommitUrl: 'https://github.com/company/pipecat-app-a/commit/a1b2c3d4e5f6',
    argocdApp: 'pipecat-app-a-phoenix-eucentral',
    argocdUrl: 'https://argocd.example.com/applications/pipecat-app-a-phoenix-eucentral',
    argocdSyncStatus: 'synced',
    argocdHealthStatus: 'healthy',
    argocdRevision: 'a1b2c3d4e5f6',
    replicas: 2,
    status: 'running',
    cpu: '280m',
    memory: '320Mi',
    deployedAt: '2024-01-13 14:00:00',
    deployedBy: 'Jane Smith',
  },
  // Asia Pacific - Phoenix 版本（有问题）
  {
    id: 'dep-7',
    projectId: 'proj-1',
    projectName: 'Pipecat-Platform',
    serviceId: 'svc-1',
    serviceName: 'auth-service',
    versionId: 'ver-2',
    codename: 'Phoenix',
    imageVersion: 'v1.2.3-rc3',
    regionId: 'ap-east',
    regionName: 'Asia Pacific (AliCloud)',
    gitRepo: 'https://github.com/company/pipecat-app-a.git',
    gitBranch: 'feature/phoenix-refactor',
    gitCommit: 'a1b2c3d4e5f6',
    gitCommitUrl: 'https://github.com/company/pipecat-app-a/commit/a1b2c3d4e5f6',
    argocdApp: 'pipecat-app-a-phoenix-apeast',
    argocdUrl: 'https://argocd.example.com/applications/pipecat-app-a-phoenix-apeast',
    argocdSyncStatus: 'out-of-sync',
    argocdHealthStatus: 'degraded',
    argocdRevision: 'a1b2c3d4e5f6',
    replicas: 3,
    status: 'error',
    cpu: '950m',
    memory: '920Mi',
    deployedAt: '2024-01-12 16:00:00',
    deployedBy: 'Alice Chen',
  },
  // AP Southeast - Phoenix 版本
  {
    id: 'dep-8',
    projectId: 'proj-1',
    projectName: 'Pipecat-Platform',
    serviceId: 'svc-1',
    serviceName: 'auth-service',
    versionId: 'ver-2',
    codename: 'Phoenix',
    imageVersion: 'v1.2.3-rc3',
    regionId: 'ap-southeast',
    regionName: 'AP Southeast (AWS)',
    gitRepo: 'https://github.com/company/pipecat-app-a.git',
    gitBranch: 'feature/phoenix-refactor',
    gitCommit: 'a1b2c3d4e5f6',
    gitCommitUrl: 'https://github.com/company/pipecat-app-a/commit/a1b2c3d4e5f6',
    argocdApp: 'pipecat-app-a-phoenix-apse',
    argocdUrl: 'https://argocd.example.com/applications/pipecat-app-a-phoenix-apse',
    argocdSyncStatus: 'synced',
    argocdHealthStatus: 'healthy',
    argocdRevision: 'a1b2c3d4e5f6',
    replicas: 3,
    status: 'running',
    cpu: '150m',
    memory: '192Mi',
    deployedAt: '2024-01-14 09:00:00',
    deployedBy: 'Jane Smith',
  },
  // Chat-Platform - Aurora 版本
  {
    id: 'dep-9',
    projectId: 'proj-2',
    projectName: 'E-Commerce Core',
    serviceId: 'svc-3',
    serviceName: 'payment-gateway',
    versionId: 'ver-5',
    codename: 'Aurora',
    imageVersion: 'v2.0.1-beta1',
    regionId: 'us-east',
    regionName: 'US East (AWS)',
    gitRepo: 'https://github.com/company/chat-platform.git',
    gitBranch: 'feature/aurora-mq',
    gitCommit: 's9t0u1v2w3x4',
    gitCommitUrl: 'https://github.com/company/chat-platform/commit/s9t0u1v2w3x4',
    argocdApp: 'chat-platform-aurora-useast',
    argocdUrl: 'https://argocd.example.com/applications/chat-platform-aurora-useast',
    argocdSyncStatus: 'synced',
    argocdHealthStatus: 'healthy',
    argocdRevision: 's9t0u1v2w3x4',
    replicas: 3,
    status: 'running',
    cpu: '180m',
    memory: '220Mi',
    deployedAt: '2024-01-14 11:00:00',
    deployedBy: 'Bob Wilson',
  },
]

interface DeploymentState {
  deployments: VersionDeployment[]
  regions: typeof regions

  // Actions
  getDeploymentsByRegion: (regionId: string) => VersionDeployment[]
  getDeploymentsByProject: (projectId: string) => VersionDeployment[]
  getDeploymentsByVersion: (versionId: string) => VersionDeployment[]
  getDeploymentsByCodename: (codename: string) => VersionDeployment[]
  getRegionStatus: (regionId: string) => 'healthy' | 'warning' | 'critical'
}

export const useDeploymentStore = create<DeploymentState>()(
  persist(
    (_set, get) => ({
      deployments: mockDeployments,
      regions: regions,

      getDeploymentsByRegion: (regionId) => {
        return get().deployments.filter(d => d.regionId === regionId)
      },

      getDeploymentsByProject: (projectId) => {
        return get().deployments.filter(d => d.projectId === projectId)
      },

      getDeploymentsByVersion: (versionId) => {
        return get().deployments.filter(d => d.versionId === versionId)
      },

      getDeploymentsByCodename: (codename) => {
        return get().deployments.filter(d => d.codename === codename)
      },

      getRegionStatus: (regionId) => {
        const deployments = get().deployments.filter(d => d.regionId === regionId)
        if (deployments.length === 0) return 'healthy'

        const hasError = deployments.some(d => d.status === 'error')
        const hasWarning = deployments.some(d => d.status === 'warning')

        if (hasError) return 'critical'
        if (hasWarning) return 'warning'
        return 'healthy'
      },
    }),
    {
      name: 'nexusops-deployments',
      version: 1,
    }
  )
)
