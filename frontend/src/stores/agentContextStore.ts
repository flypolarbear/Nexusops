/**
 * Agent 上下文管理 Store
 *
 * 管理当前 Agent 执行的上下文信息，包括：
 * - 项目/版本上下文
 * - 区域上下文
 * - 资源上下文
 * - 用户/租户上下文
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type {
  AgentContextState,
  AgentRequestContext,
  AgentResourceContext,
} from '../types/agent';

interface AgentContextStore extends AgentContextState {}

const initialState = {
  current_project_id: null,
  current_version_id: null,
  current_codename: null,
  current_region: null,
  current_resource: null,
  user_id: null,
  tenant_id: null,
  conversation_id: null,
};

export const useAgentContextStore = create<AgentContextStore>()(
  persist(
    (set, get) => ({
      ...initialState,

      setProject: (id: string) => {
        set({
          current_project_id: id,
          // 切换项目时清除版本上下文
          current_version_id: null,
          current_codename: null,
        });
      },

      setVersion: (id: string, codename?: string) => {
        set({
          current_version_id: id,
          current_codename: codename || null,
        });
      },

      setRegion: (id: string) => {
        set({ current_region: id });
      },

      setResource: (resource: AgentResourceContext) => {
        set({ current_resource: resource });
      },

      setUserId: (id: string) => {
        set({ user_id: id });
      },

      setTenantId: (id: string) => {
        set({ tenant_id: id });
      },

      setConversationId: (id: string) => {
        set({ conversation_id: id });
      },

      clearContext: () => {
        set(initialState);
      },

      getFullContext: (): AgentRequestContext => {
        const state = get();
        return {
          user_id: state.user_id || undefined,
          tenant_id: state.tenant_id || undefined,
          project_id: state.current_project_id || undefined,
          version_id: state.current_version_id || undefined,
          codename: state.current_codename || undefined,
          region: state.current_region || undefined,
          resource_type: state.current_resource?.type,
          resource_name: state.current_resource?.name,
          namespace: state.current_resource?.namespace,
        };
      },
    }),
    {
      name: 'nexusops-agent-context',
      // 只持久化部分字段
      partialize: (state) => ({
        current_project_id: state.current_project_id,
        current_version_id: state.current_version_id,
        current_codename: state.current_codename,
        current_region: state.current_region,
        tenant_id: state.tenant_id,
      }),
    }
  )
);

// ============================================
// Hooks
// ============================================

/**
 * 获取当前 Agent 请求上下文
 */
export function useAgentContext(): AgentRequestContext {
  return useAgentContextStore((state) => state.getFullContext());
}

/**
 * 获取当前项目 ID
 */
export function useCurrentProjectId(): string | null {
  return useAgentContextStore((state) => state.current_project_id);
}

/**
 * 获取当前版本 ID
 */
export function useCurrentVersionId(): string | null {
  return useAgentContextStore((state) => state.current_version_id);
}

/**
 * 获取当前版本代号
 */
export function useCurrentCodename(): string | null {
  return useAgentContextStore((state) => state.current_codename);
}

/**
 * 获取当前区域
 */
export function useCurrentRegion(): string | null {
  return useAgentContextStore((state) => state.current_region);
}

/**
 * 获取当前资源上下文
 */
export function useCurrentResource(): AgentResourceContext | null {
  return useAgentContextStore((state) => state.current_resource);
}

/**
 * 获取当前会话 ID（用于 Agent 对话）
 */
export function useConversationId(): string | null {
  return useAgentContextStore((state) => state.conversation_id);
}

// ============================================
// 工具函数
// ============================================

/**
 * 创建新的会话上下文
 */
export function createNewConversation(): string {
  const conversationId = `conv-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  useAgentContextStore.getState().setConversationId(conversationId);
  return conversationId;
}

/**
 * 从 URL 参数同步上下文
 */
export function syncContextFromUrl(params: {
  projectId?: string;
  versionId?: string;
  codename?: string;
  region?: string;
}) {
  const { setProject, setVersion, setRegion } = useAgentContextStore.getState();

  if (params.projectId) {
    setProject(params.projectId);
  }
  if (params.versionId) {
    setVersion(params.versionId, params.codename);
  }
  if (params.region) {
    setRegion(params.region);
  }
}

/**
 * 设置资源上下文（用于从资源列表点击进入）
 */
export function setResourceContext(resource: AgentResourceContext) {
  useAgentContextStore.getState().setResource(resource);
}

/**
 * 清除所有上下文
 */
export function clearAllContext() {
  useAgentContextStore.getState().clearContext();
}
