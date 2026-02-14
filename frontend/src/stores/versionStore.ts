import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// 版本状态类型 - 简化为只有测试和生产
export type VersionStatus = 'testing' | 'production' | 'archived'

// 版本定义
export interface Version {
  id: string
  projectId: string
  codename: string           // 内部代号，如 "Phoenix"
  description: string        // 描述/备注
  gitBranch: string          // Git 分支/tag
  imageUrl: string           // 镜像地址
  owner: string              // 负责人
  status: VersionStatus      // 状态
  testUrl?: string           // 测试 URL (测试版本专用)
  environments: string[]     // 已部署的环境 ['dev', 'staging']
  createdAt: string
  updatedAt: string
}

// 项目定义
export interface Project {
  id: string
  name: string               // 项目名称，如 "Pipecat-App-A"
  code: string               // 项目代码，如 "pipecat-app-a"
  description: string
  owner: string
  productionVersionId: string | null  // 当前生产版本 ID
  versions: Version[]
  createdAt: string
}

// 版本切换申请
export interface VersionSwitchRequest {
  id: string
  projectId: string
  projectName: string
  fromVersionId: string
  fromVersionCodename: string
  toVersionId: string
  toVersionCodename: string
  reason: string
  status: 'pending' | 'approved' | 'rejected' | 'completed'
  requester: string
  approver: string | null
  createdAt: string
  approvedAt: string | null
}

// Mock 数据
const mockProjects: Project[] = [
  {
    id: 'proj-1',
    name: 'Pipecat-App-A',
    code: 'pipecat-app-a',
    description: 'Main chat application service',
    owner: 'John Doe',
    productionVersionId: 'ver-1',
    versions: [
      {
        id: 'ver-1',
        projectId: 'proj-1',
        codename: 'legacy',
        description: 'Original stable version',
        gitBranch: 'main',
        imageUrl: 'harbor.local/pipecat-app-a:legacy-v2.3.1',
        owner: 'John Doe',
        status: 'production',
        environments: ['dev', 'staging', 'production'],
        createdAt: '2023-06-15',
        updatedAt: '2024-01-10',
      },
      {
        id: 'ver-2',
        projectId: 'proj-1',
        codename: 'Phoenix',
        description: 'Refactored architecture with new chat engine',
        gitBranch: 'feature/phoenix-refactor',
        imageUrl: 'harbor.local/pipecat-app-a:phoenix-rc3',
        owner: 'Jane Smith',
        status: 'testing',
        testUrl: 'https://phoenix.test.pipecat.internal',
        environments: ['dev', 'staging'],
        createdAt: '2024-01-05',
        updatedAt: '2024-01-15',
      },
      {
        id: 'ver-3',
        projectId: 'proj-1',
        codename: 'Titan',
        description: 'New feature: Real-time translation',
        gitBranch: 'feature/titan-translation',
        imageUrl: 'harbor.local/pipecat-app-a:titan-beta2',
        owner: 'Bob Wilson',
        status: 'testing',
        testUrl: 'https://titan.test.pipecat.internal',
        environments: ['dev'],
        createdAt: '2024-01-12',
        updatedAt: '2024-01-15',
      },
      {
        id: 'ver-4',
        projectId: 'proj-1',
        codename: 'Nova',
        description: 'Next generation architecture',
        gitBranch: 'feature/nova-next-gen',
        imageUrl: 'harbor.local/pipecat-app-a:nova-dev1',
        owner: 'Alice Chen',
        status: 'testing',
        testUrl: 'https://nova.test.pipecat.internal',
        environments: ['dev'],
        createdAt: '2024-01-14',
        updatedAt: '2024-01-15',
      },
    ],
    createdAt: '2023-06-15',
  },
  {
    id: 'proj-2',
    name: 'Chat-Platform',
    code: 'chat-platform',
    description: 'Core chat infrastructure',
    owner: 'Jane Smith',
    productionVersionId: 'ver-5',
    versions: [
      {
        id: 'ver-5',
        projectId: 'proj-2',
        codename: 'stable',
        description: 'Current production version',
        gitBranch: 'main',
        imageUrl: 'harbor.local/chat-platform:v2.0.3',
        owner: 'Jane Smith',
        status: 'production',
        environments: ['dev', 'staging', 'production'],
        createdAt: '2023-08-20',
        updatedAt: '2024-01-08',
      },
      {
        id: 'ver-6',
        projectId: 'proj-2',
        codename: 'Aurora',
        description: 'High-performance message queue',
        gitBranch: 'feature/aurora-mq',
        imageUrl: 'harbor.local/chat-platform:aurora-beta1',
        owner: 'Bob Wilson',
        status: 'testing',
        testUrl: 'https://aurora.test.chat.internal',
        environments: ['dev', 'staging'],
        createdAt: '2024-01-10',
        updatedAt: '2024-01-14',
      },
    ],
    createdAt: '2023-08-20',
  },
]

const mockSwitchRequests: VersionSwitchRequest[] = [
  {
    id: 'req-1',
    projectId: 'proj-1',
    projectName: 'Pipecat-App-A',
    fromVersionId: 'ver-1',
    fromVersionCodename: 'legacy',
    toVersionId: 'ver-2',
    toVersionCodename: 'Phoenix',
    reason: 'Phoenix version passed all tests, ready for production',
    status: 'pending',
    requester: 'Jane Smith',
    approver: null,
    createdAt: '2024-01-15 14:00',
    approvedAt: null,
  },
]

interface VersionState {
  projects: Project[]
  switchRequests: VersionSwitchRequest[]
  currentProjectId: string | null
  currentVersionId: string | null

  // Actions
  setCurrentProject: (projectId: string | null) => void
  setCurrentVersion: (versionId: string | null) => void
  getCurrentProject: () => Project | null
  getCurrentVersion: () => Version | null
  addVersion: (projectId: string, version: Omit<Version, 'id' | 'projectId' | 'createdAt' | 'updatedAt' | 'status'>) => void
  updateVersionStatus: (projectId: string, versionId: string, status: VersionStatus) => void
  createSwitchRequest: (request: Omit<VersionSwitchRequest, 'id' | 'status' | 'approver' | 'approvedAt'>) => void
  approveSwitchRequest: (requestId: string, approver: string) => void
  rejectSwitchRequest: (requestId: string, approver: string) => void
}

export const useVersionStore = create<VersionState>()(
  persist(
    (set, get) => ({
      projects: mockProjects,
      switchRequests: mockSwitchRequests,
      currentProjectId: mockProjects[0]?.id || null,
      currentVersionId: mockProjects[0]?.productionVersionId || null,

      setCurrentProject: (projectId) =>
        set((state) => {
          const project = state.projects.find(p => p.id === projectId)
          return {
            currentProjectId: projectId,
            currentVersionId: project?.productionVersionId || project?.versions[0]?.id || null,
          }
        }),

      setCurrentVersion: (versionId) =>
        set({ currentVersionId: versionId }),

      getCurrentProject: () => {
        const state = get()
        return state.projects.find(p => p.id === state.currentProjectId) || null
      },

      getCurrentVersion: () => {
        const state = get()
        const project = state.projects.find(p => p.id === state.currentProjectId)
        return project?.versions.find(v => v.id === state.currentVersionId) || null
      },

      addVersion: (projectId, versionData) =>
        set((state) => ({
          projects: state.projects.map(p =>
            p.id === projectId
              ? {
                  ...p,
                  versions: [
                    ...p.versions,
                    {
                      ...versionData,
                      status: 'testing', // 新版本默认为测试状态
                      id: `ver-${Date.now()}`,
                      projectId,
                      createdAt: new Date().toISOString(),
                      updatedAt: new Date().toISOString(),
                    },
                  ],
                }
              : p
          ),
        })),

      updateVersionStatus: (projectId, versionId, status) =>
        set((state) => ({
          projects: state.projects.map(p =>
            p.id === projectId
              ? {
                  ...p,
                  versions: p.versions.map(v =>
                    v.id === versionId
                      ? { ...v, status, updatedAt: new Date().toISOString() }
                      : v
                  ),
                }
              : p
          ),
        })),

      createSwitchRequest: (requestData) =>
        set((state) => ({
          switchRequests: [
            ...state.switchRequests,
            {
              ...requestData,
              id: `req-${Date.now()}`,
              status: 'pending',
              approver: null,
              approvedAt: null,
            },
          ],
        })),

      approveSwitchRequest: (requestId, approver) =>
        set((state) => {
          const request = state.switchRequests.find(r => r.id === requestId)
          if (!request) return state

          return {
            switchRequests: state.switchRequests.map(r =>
              r.id === requestId
                ? { ...r, status: 'approved', approver, approvedAt: new Date().toISOString() }
                : r
            ),
            projects: state.projects.map(p =>
              p.id === request.projectId
                ? {
                    ...p,
                    productionVersionId: request.toVersionId,
                    versions: p.versions.map(v =>
                      v.id === request.toVersionId
                        ? { ...v, status: 'production' as VersionStatus }
                        : v.id === request.fromVersionId
                        ? { ...v, status: 'archived' as VersionStatus }
                        : v
                    ),
                  }
                : p
            ),
          }
        }),

      rejectSwitchRequest: (requestId, approver) =>
        set((state) => ({
          switchRequests: state.switchRequests.map(r =>
            r.id === requestId
              ? { ...r, status: 'rejected', approver, approvedAt: new Date().toISOString() }
              : r
          ),
        })),
    }),
    {
      name: 'nexusops-versions',
      version: 2, // 版本号，改变后会触发迁移
      migrate: (persistedState, version) => {
        // 如果版本号低于2，使用默认数据
        if (version < 2) {
          return {
            projects: mockProjects,
            switchRequests: mockSwitchRequests,
            currentProjectId: mockProjects[0]?.id || null,
            currentVersionId: mockProjects[0]?.productionVersionId || null,
          }
        }
        return persistedState as unknown as VersionState
      },
    }
  )
)
