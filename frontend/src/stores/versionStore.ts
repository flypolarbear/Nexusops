import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// 版本状态类型
export type VersionStatus = 'testing' | 'production' | 'archived'

// Version Definition (Now sits under a Service)
export interface Version {
  id: string
  serviceId: string          // Which service this version belongs to
  codename: string           // e.g. "Phoenix"
  description: string
  imageUrl: string           // e.g. "harbor.local/auth-service:phoenix-rc3"
  owner: string
  status: VersionStatus
  testUrl?: string
  environments: string[]
  createdAt: string
  updatedAt: string
}

// Service Definition (Now sits under a Project)
export interface Service {
  id: string
  projectId: string
  name: string               // e.g. "auth-service"
  gitRepo: string            // Repository URL bound to the service
  gitBranch: string          // Default branch
  owner: string
  productionVersionId: string | null  // The version currently running in production
  versions: Version[]
  createdAt: string
}

// Project Definition (Top Level)
export interface Project {
  id: string
  name: string               // e.g. "E-Commerce Core"
  code: string               // e.g. "ecommerce-core"
  description: string
  owner: string
  services: Service[]        // A project has multiple microservices
  createdAt: string
}

export interface VersionSwitchRequest {
  id: string
  serviceId: string
  serviceName: string
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
  gitBranch?: string
  gitCommit?: string
  imageVersion?: string
  deployRegions?: string[]
  deployStrategy?: string
  deployOrder?: string
}

const mockProjects: Project[] = [
  {
    id: 'proj-1',
    name: 'Pipecat-Platform',
    code: 'pipecat-platform',
    description: 'Main communication platform',
    owner: 'John Doe',
    createdAt: '2023-01-01',
    services: [
      {
        id: 'svc-1',
        projectId: 'proj-1',
        name: 'auth-service',
        gitRepo: 'https://github.com/company/auth-service.git',
        gitBranch: 'main',
        owner: 'John Doe',
        productionVersionId: 'ver-1',
        createdAt: '2023-01-01',
        versions: [
          {
            id: 'ver-1',
            serviceId: 'svc-1',
            codename: 'legacy',
            description: 'Stable v1',
            imageUrl: 'harbor.local/auth-service:v1.0.0',
            owner: 'John Doe',
            status: 'production',
            environments: ['production'],
            createdAt: '2023-06-15',
            updatedAt: '2024-01-10',
          },
          {
            id: 'ver-2',
            serviceId: 'svc-1',
            codename: 'Phoenix',
            description: 'OAuth2 refactor',
            imageUrl: 'harbor.local/auth-service:phoenix-rc3',
            owner: 'Jane Smith',
            status: 'testing',
            testUrl: 'https://auth-phoenix.test.pipecat.internal',
            environments: ['testing'],
            createdAt: '2024-01-05',
            updatedAt: '2024-01-15',
          }
        ]
      },
      {
        id: 'svc-2',
        projectId: 'proj-1',
        name: 'chat-engine',
        gitRepo: 'https://github.com/company/chat-engine.git',
        gitBranch: 'main',
        owner: 'Alice Chen',
        productionVersionId: 'ver-3',
        createdAt: '2023-02-01',
        versions: [
          {
            id: 'ver-3',
            serviceId: 'svc-2',
            codename: 'stable',
            description: 'v2.1 chat engine',
            imageUrl: 'harbor.local/chat-engine:v2.1.0',
            owner: 'Alice Chen',
            status: 'production',
            environments: ['production'],
            createdAt: '2023-11-15',
            updatedAt: '2024-01-10',
          },
          {
            id: 'ver-4',
            serviceId: 'svc-2',
            codename: 'Titan',
            description: 'WebRTC optimization',
            imageUrl: 'harbor.local/chat-engine:titan-beta',
            owner: 'Bob Wilson',
            status: 'testing',
            testUrl: 'https://chat-titan.test.pipecat.internal',
            environments: ['testing'],
            createdAt: '2024-01-12',
            updatedAt: '2024-01-15',
          }
        ]
      }
    ]
  },
  {
    id: 'proj-2',
    name: 'E-Commerce Core',
    code: 'ecommerce-core',
    description: 'Shopping platform backend',
    owner: 'Mark Johnson',
    createdAt: '2023-05-01',
    services: [
      {
        id: 'svc-3',
        projectId: 'proj-2',
        name: 'payment-gateway',
        gitRepo: 'https://github.com/company/payment-gateway.git',
        gitBranch: 'main',
        owner: 'Mark Johnson',
        productionVersionId: 'ver-5',
        createdAt: '2023-05-01',
        versions: [
          {
            id: 'ver-5',
            serviceId: 'svc-3',
            codename: 'v3-stable',
            description: 'Stripe integration',
            imageUrl: 'harbor.local/payment-gateway:v3.0.0',
            owner: 'Mark Johnson',
            status: 'production',
            environments: ['production'],
            createdAt: '2023-12-01',
            updatedAt: '2024-01-10',
          }
        ]
      }
    ]
  }
]

interface VersionState {
  projects: Project[]
  switchRequests: VersionSwitchRequest[]
  currentProjectId: string | null
  currentServiceId: string | null
  currentVersionId: string | null
  
  setCurrentProject: (id: string | null) => void
  setCurrentService: (id: string | null) => void
  setCurrentVersion: (id: string | null) => void
  
  addProject: (project: Omit<Project, 'id' | 'createdAt' | 'services'>, customId?: string) => void
  addService: (projectId: string, service: Omit<Service, 'id' | 'createdAt' | 'versions' | 'projectId' | 'productionVersionId'>) => void
  addVersion: (projectId: string, serviceId: string, version: Omit<Version, 'id' | 'createdAt' | 'updatedAt' | 'serviceId' | 'status'>) => void
  
  createSwitchRequest: (req: Omit<VersionSwitchRequest, 'id' | 'createdAt' | 'approvedAt' | 'status' | 'approver'>) => void
  approveSwitchRequest: (id: string, approver: string) => void
  rejectSwitchRequest: (id: string, approver: string) => void
}

export const useVersionStore = create<VersionState>()(
  persist(
    (set) => ({
      projects: mockProjects,
      switchRequests: [],
      currentProjectId: mockProjects[0].id,
      currentServiceId: null,
      currentVersionId: null,

      setCurrentProject: (id) => set({ currentProjectId: id, currentServiceId: null, currentVersionId: null }),
      setCurrentService: (id) => set({ currentServiceId: id, currentVersionId: null }),
      setCurrentVersion: (id) => set({ currentVersionId: id }),

      addProject: (project, customId) => set((state) => ({
        projects: [
          ...state.projects,
          {
            ...project,
            id: customId || `proj-${Date.now()}`,
            services: [],
            createdAt: new Date().toISOString().split('T')[0],
          }
        ]
      })),

      addService: (projectId, service) => set((state) => ({
        projects: state.projects.map(p => {
          if (p.id !== projectId) return p;
          return {
            ...p,
            services: [
              ...p.services,
              {
                ...service,
                id: `svc-${Date.now()}`,
                projectId,
                productionVersionId: null,
                versions: [],
                createdAt: new Date().toISOString().split('T')[0]
              }
            ]
          }
        })
      })),

      addVersion: (projectId, serviceId, versionData) => set((state) => ({
        projects: state.projects.map(p => {
          if (p.id !== projectId) return p;
          return {
            ...p,
            services: p.services.map(s => {
              if (s.id !== serviceId) return s;
              return {
                ...s,
                versions: [
                  ...s.versions,
                  {
                    ...versionData,
                    id: `ver-${Date.now()}`,
                    serviceId,
                    status: 'testing',
                    createdAt: new Date().toISOString().split('T')[0],
                    updatedAt: new Date().toISOString().split('T')[0],
                  }
                ]
              }
            })
          }
        })
      })),

      createSwitchRequest: (req) => set((state) => ({
        switchRequests: [
          {
            ...req,
            id: `req-${Date.now()}`,
            status: 'pending',
            createdAt: new Date().toISOString(),
            approver: null,
            approvedAt: null,
          },
          ...state.switchRequests,
        ],
      })),

      approveSwitchRequest: (id, approver) => set((state) => {
        const req = state.switchRequests.find(r => r.id === id)
        if (!req) return state

        // Switch the production version in the target service
        const newProjects = state.projects.map(p => ({
          ...p,
          services: p.services.map(s => {
            if (s.id !== req.serviceId) return s;
            return {
              ...s,
              productionVersionId: req.toVersionId,
              versions: s.versions.map(v => {
                if (v.id === req.toVersionId) return { ...v, status: 'production' as const }
                if (v.id === req.fromVersionId) return { ...v, status: 'archived' as const }
                return v
              })
            }
          })
        }))

        return {
          projects: newProjects,
          switchRequests: state.switchRequests.map(r =>
            r.id === id ? { ...r, status: 'approved', approver, approvedAt: new Date().toISOString() } : r
          ),
        }
      }),

      rejectSwitchRequest: (id, approver) => set((state) => ({
        switchRequests: state.switchRequests.map(r =>
          r.id === id ? { ...r, status: 'rejected', approver, approvedAt: new Date().toISOString() } : r
        ),
      })),
    }),
    {
      name: 'nexusops-versions',
      version: 4, // Bumped version to flush old localstorage state
      migrate: (persistedState, version) => {
        if (version < 4) {
          return {
            projects: mockProjects,
            switchRequests: [],
            currentProjectId: mockProjects[0]?.id || null,
            currentServiceId: null,
            currentVersionId: null,
          }
        }
        return persistedState as unknown as VersionState
      },
    }
  )
)
