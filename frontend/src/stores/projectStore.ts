import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface Project {
  id: string
  name: string
  environments: Environment[]
}

export interface Environment {
  id: string
  name: string
  type: 'production' | 'staging' | 'development'
}

interface ProjectState {
  projects: Project[]
  currentProject: Project | null
  globalSelectedProjectId: string | 'all'
  currentEnvironment: Environment | null
  setProjects: (projects: Project[]) => void
  setCurrentProject: (project: Project | null) => void
  setGlobalSelectedProjectId: (id: string | 'all') => void
  setCurrentEnvironment: (environment: Environment | null) => void
}

// Mock projects for development
const mockProjects: Project[] = [
  {
    id: 'pipecat-app-a',
    name: 'Pipecat-App-A',
    environments: [
      { id: 'prod', name: 'Production', type: 'production' },
      { id: 'staging', name: 'Staging', type: 'staging' },
      { id: 'dev', name: 'Development', type: 'development' },
    ],
  },
  {
    id: 'chat-platform',
    name: 'Chat-Platform',
    environments: [
      { id: 'prod', name: 'Production', type: 'production' },
      { id: 'staging', name: 'Staging', type: 'staging' },
    ],
  },
  {
    id: 'infra-core',
    name: 'Infra-Core',
    environments: [
      { id: 'prod', name: 'Production', type: 'production' },
    ],
  },
]

export const useProjectStore = create<ProjectState>()(
  persist(
    (set) => ({
      projects: mockProjects,
      currentProject: mockProjects[0],
      globalSelectedProjectId: 'all',
      currentEnvironment: mockProjects[0]?.environments[0] || null,
      setProjects: (projects) => set({ projects }),
      setCurrentProject: (project) =>
        set({
          currentProject: project,
          currentEnvironment: project?.environments[0] || null,
        }),
      setGlobalSelectedProjectId: (id) => set({ globalSelectedProjectId: id }),
      setCurrentEnvironment: (environment) => set({ currentEnvironment: environment }),
    }),
    {
      name: 'nexusops-project',
    }
  )
)
