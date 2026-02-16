/**
 * Agent 服务层
 *
 * 提供统一的 Agent 调用接口，支持：
 * - 单次调用
 * - 流式调用
 * - A2A 通信
 */

import type {
  AgentRequest,
  AgentResponse,
  AgentManifest,
  AgentAction,
  AgentMessage,
  AgentRequestContext,
} from '../types/agent';
import { generateRequestId, generateConversationId } from '../types/agent';
import { useAgentContextStore } from '../stores/agentContextStore';

// ============================================
// 配置
// ============================================

const API_BASE_URL = '/api/v1';

// ============================================
// Agent Service
// ============================================

export class AgentService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * 获取所有可用的 Agent
   */
  async getAgents(): Promise<AgentManifest[]> {
    const response = await fetch(`${this.baseUrl}/agents`);
    if (!response.ok) {
      throw new Error(`Failed to fetch agents: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * 获取单个 Agent
   */
  async getAgent(agentId: string): Promise<AgentManifest | null> {
    const response = await fetch(`${this.baseUrl}/agents/${encodeURIComponent(agentId)}`);
    if (response.status === 404) {
      return null;
    }
    if (!response.ok) {
      throw new Error(`Failed to fetch agent: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * 调用 Agent
   */
  async invoke(
    agentId: string,
    query: string,
    context?: Partial<AgentRequestContext>,
    options?: {
      conversationId?: string;
      tools?: AgentRequest['tools'];
      outputConfig?: AgentRequest['output_config'];
    }
  ): Promise<AgentResponse> {
    // 获取全局上下文
    const globalContext = useAgentContextStore.getState().getFullContext();

    const conversationId: string = (options?.conversationId || globalContext.conversation_id) as string || generateConversationId();

    const request: AgentRequest = {
      request_id: generateRequestId(),
      conversation_id: conversationId,
      agent_id: agentId,
      query,
      context: {
        ...globalContext,
        ...context,
      },
      output_config: options?.outputConfig,
      tools: options?.tools,
    };

    const response = await fetch(
      `${this.baseUrl}/agents/${encodeURIComponent(agentId)}/invoke`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: response.statusText }));
      return {
        request_id: request.request_id,
        status: 'error',
        content: { text: '', format: 'plain' },
        error: {
          code: 'INTERNAL_ERROR' as any,
          message: error.message || 'Failed to invoke agent',
        },
      };
    }

    return response.json();
  }

  /**
   * 流式调用 Agent (SSE)
   */
  async *stream(
    agentId: string,
    query: string,
    context?: Partial<AgentRequestContext>,
    options?: {
      conversationId?: string;
      tools?: AgentRequest['tools'];
    }
  ): AsyncGenerator<AgentResponse> {
    // 获取全局上下文
    const globalContext = useAgentContextStore.getState().getFullContext();

    const conversationId: string = (options?.conversationId || globalContext.conversation_id) as string || generateConversationId();

    const request: AgentRequest = {
      request_id: generateRequestId(),
      conversation_id: conversationId,
      agent_id: agentId,
      query,
      context: {
        ...globalContext,
        ...context,
      },
      tools: options?.tools,
    };

    const response = await fetch(
      `${this.baseUrl}/agents/${encodeURIComponent(agentId)}/stream`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      }
    );

    if (!response.ok) {
      yield {
        request_id: request.request_id,
        status: 'error',
        content: { text: '', format: 'plain' },
        error: {
          code: 'INTERNAL_ERROR' as any,
          message: `Failed to stream agent: ${response.statusText}`,
        },
      };
      return;
    }

    const reader = response.body?.getReader();
    if (!reader) {
      return;
    }

    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n').filter(Boolean);

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            yield data;
          } catch {
            // Ignore parse errors
          }
        }
      }
    }
  }

  /**
   * 执行 Agent 操作
   */
  async executeAction(
    agentId: string,
    action: AgentAction
  ): Promise<{ success: boolean; result?: unknown; error?: string }> {
    const response = await fetch(
      `${this.baseUrl}/agents/${encodeURIComponent(agentId)}/actions/${encodeURIComponent(action.id)}/execute`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action_type: action.type,
          params: action.params,
        }),
      }
    );

    if (!response.ok) {
      return {
        success: false,
        error: response.statusText,
      };
    }

    return response.json();
  }

  /**
   * A2A 通信
   */
  async delegate(
    fromAgentId: string,
    toAgentId: string,
    query: string,
    context?: Partial<AgentRequestContext>
  ): Promise<AgentResponse> {
    const globalContext = useAgentContextStore.getState().getFullContext();

    const response = await fetch(
      `${this.baseUrl}/agents/${encodeURIComponent(toAgentId)}/delegate`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-From-Agent': fromAgentId,
        },
        body: JSON.stringify({
          query,
          context: {
            ...globalContext,
            ...context,
          },
        }),
      }
    );

    if (!response.ok) {
      return {
        request_id: generateRequestId(),
        status: 'error',
        content: { text: '', format: 'plain' },
        error: {
          code: 'INTERNAL_ERROR' as any,
          message: `Failed to delegate: ${response.statusText}`,
        },
      };
    }

    return response.json();
  }
}

// ============================================
// 快捷命令解析
// ============================================

export interface ParsedCommand {
  command: string;
  params: Record<string, string>;
  raw: string;
}

/**
 * 解析快捷命令
 *
 * 支持的命令：
 * - /deploy <version> to <region>
 * - /rollback <version> in <region>
 * - /status <version>
 * - /logs <service> --tail <lines>
 * - /compare <v1> vs <v2>
 */
export function parseCommand(input: string): ParsedCommand | null {
  const trimmed = input.trim();

  if (!trimmed.startsWith('/')) {
    return null;
  }

  // /deploy <version> to <region>
  const deployMatch = trimmed.match(/^\/deploy\s+(\S+)\s+to\s+(\S+)$/i);
  if (deployMatch) {
    return {
      command: '/deploy',
      params: {
        version: deployMatch[1],
        region: deployMatch[2],
      },
      raw: trimmed,
    };
  }

  // /rollback <version> in <region>
  const rollbackMatch = trimmed.match(/^\/rollback\s+(\S+)\s+in\s+(\S+)$/i);
  if (rollbackMatch) {
    return {
      command: '/rollback',
      params: {
        version: rollbackMatch[1],
        region: rollbackMatch[2],
      },
      raw: trimmed,
    };
  }

  // /status <version>
  const statusMatch = trimmed.match(/^\/status\s+(\S+)$/i);
  if (statusMatch) {
    return {
      command: '/status',
      params: {
        version: statusMatch[1],
      },
      raw: trimmed,
    };
  }

  // /logs <service> --tail <lines>
  const logsMatch = trimmed.match(/^\/logs\s+(\S+)(?:\s+--tail\s+(\d+))?$/i);
  if (logsMatch) {
    return {
      command: '/logs',
      params: {
        service: logsMatch[1],
        tail: logsMatch[2] || '100',
      },
      raw: trimmed,
    };
  }

  // /compare <v1> vs <v2>
  const compareMatch = trimmed.match(/^\/compare\s+(\S+)\s+vs\s+(\S+)$/i);
  if (compareMatch) {
    return {
      command: '/compare',
      params: {
        version1: compareMatch[1],
        version2: compareMatch[2],
      },
      raw: trimmed,
    };
  }

  return null;
}

/**
 * 执行快捷命令
 */
export async function executeCommand(
  service: AgentService,
  command: ParsedCommand,
  context?: Partial<AgentRequestContext>
): Promise<AgentResponse> {
  switch (command.command) {
    case '/deploy':
      return service.invoke(
        'nexusops.deploy',
        `Deploy ${command.params.version} to ${command.params.region}`,
        {
          ...context,
          codename: command.params.version,
          region: command.params.region,
        }
      );

    case '/rollback':
      return service.invoke(
        'nexusops.deploy',
        `Rollback ${command.params.version} in ${command.params.region}`,
        {
          ...context,
          codename: command.params.version,
          region: command.params.region,
        }
      );

    case '/status':
      return service.invoke(
        'nexusops.chat',
        `Get status for ${command.params.version}`,
        {
          ...context,
          codename: command.params.version,
        }
      );

    case '/logs':
      return service.invoke(
        'nexusops.k8s',
        `Get logs for ${command.params.service}, tail ${command.params.tail || '100'} lines`,
        {
          ...context,
          resource_type: 'pod',
          resource_name: command.params.service,
        }
      );

    case '/compare':
      return service.invoke(
        'nexusops.chat',
        `Compare ${command.params.version1} vs ${command.params.version2}`,
        context
      );

    default:
      return {
        request_id: generateRequestId(),
        status: 'error',
        content: { text: `Unknown command: ${command.command}`, format: 'plain' },
        error: {
          code: 'VALIDATION_ERROR' as any,
          message: `Unknown command: ${command.command}`,
        },
      };
  }
}

// ============================================
// 单例实例
// ============================================

export const agentService = new AgentService();

// ============================================
// React Hook
// ============================================

import { useState, useCallback } from 'react';

interface UseAgentOptions {
  agentId: string;
  context?: Partial<AgentRequestContext>;
  onComplete?: (response: AgentResponse) => void;
  onError?: (error: Error) => void;
}

interface UseAgentReturn {
  invoke: (query: string) => Promise<AgentResponse | null>;
  loading: boolean;
  error: Error | null;
  response: AgentResponse | null;
  messages: AgentMessage[];
  clearMessages: () => void;
}

export function useAgent(options: UseAgentOptions): UseAgentReturn {
  const { agentId, context, onComplete, onError } = options;

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [response, setResponse] = useState<AgentResponse | null>(null);
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [conversationId] = useState(() => generateConversationId());

  const invoke = useCallback(async (query: string) => {
    setLoading(true);
    setError(null);

    // 添加用户消息
    const userMessage: AgentMessage = {
      id: generateRequestId(),
      conversation_id: conversationId,
      role: 'user',
      content: query,
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      const result = await agentService.invoke(agentId, query, context, {
        conversationId,
      });

      // 添加助手消息
      const assistantMessage: AgentMessage = {
        id: result.request_id,
        conversation_id: conversationId,
        role: 'assistant',
        content: result.content.text,
        agent_id: agentId,
        suggested_actions: result.suggested_actions,
        related_resources: result.related_resources,
        metadata: result.metadata,
        created_at: new Date().toISOString(),
      };
      setMessages(prev => [...prev, assistantMessage]);

      setResponse(result);
      onComplete?.(result);
      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      onError?.(error);
      return null;
    } finally {
      setLoading(false);
    }
  }, [agentId, context, conversationId, onComplete, onError]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setResponse(null);
    setError(null);
  }, []);

  return {
    invoke,
    loading,
    error,
    response,
    messages,
    clearMessages,
  };
}
