/**
 * WebSocket Service for NexusOps Frontend
 *
 * OPT-001: 实时数据推送
 * - 部署状态实时更新
 * - 告警实时推送
 * - Agent 流式响应
 */

import { useCallback, useEffect, useRef, useState } from 'react';

// ============================================
// Types
// ============================================

export type MessageType =
  | 'connect'
  | 'disconnect'
  | 'ping'
  | 'pong'
  | 'subscribe'
  | 'unsubscribe'
  | 'deployment_update'
  | 'deployment_step_update'
  | 'alert_new'
  | 'alert_update'
  | 'agent_message'
  | 'agent_stream'
  | 'version_update'
  | 'notification'
  | 'error';

export interface WebSocketMessage {
  type: MessageType;
  data?: any;
  channel?: string;
  timestamp: string;
}

export type MessageHandler = (message: WebSocketMessage) => void;

export interface WebSocketOptions {
  url?: string;
  reconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  pingInterval?: number;
}

// ============================================
// WebSocket Manager
// ============================================

class WebSocketManager {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnect: boolean;
  private reconnectInterval: number;
  private maxReconnectAttempts: number;
  private reconnectAttempts = 0;
  private subscriptions: Set<string> = new Set();
  private handlers: Map<MessageType, Set<MessageHandler>> = new Map();
  private pingTimer: NodeJS.Timeout | null = null;
  private isConnecting = false;

  constructor(options: WebSocketOptions = {}) {
    this.url = options.url || this.getDefaultUrl();
    this.reconnect = options.reconnect ?? true;
    this.reconnectInterval = options.reconnectInterval ?? 3000;
    this.maxReconnectAttempts = options.maxReconnectAttempts ?? 10;
  }

  private getDefaultUrl(): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}/ws`;
  }

  // 连接
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      if (this.isConnecting) {
        reject(new Error('Already connecting'));
        return;
      }

      this.isConnecting = true;

      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('[WS] Connected');
          this.isConnecting = false;
          this.reconnectAttempts = 0;

          // 重新订阅
          this.subscriptions.forEach(channel => {
            this.subscribe(channel);
          });

          // 启动心跳
          this.startPing();

          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (e) {
            console.error('[WS] Failed to parse message:', e);
          }
        };

        this.ws.onclose = (event) => {
          console.log('[WS] Disconnected:', event.code, event.reason);
          this.isConnecting = false;
          this.stopPing();

          // 触发断开处理
          this.handleMessage({
            type: 'disconnect',
            data: { code: event.code, reason: event.reason },
            timestamp: new Date().toISOString(),
          });

          // 自动重连
          if (this.reconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`[WS] Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            setTimeout(() => this.connect(), this.reconnectInterval);
          }
        };

        this.ws.onerror = (error) => {
          console.error('[WS] Error:', error);
          this.isConnecting = false;
          reject(error);
        };
      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  // 断开连接
  disconnect() {
    this.stopPing();
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
  }

  // 发送消息
  send(message: Partial<WebSocketMessage>) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        ...message,
        timestamp: message.timestamp || new Date().toISOString(),
      }));
    } else {
      console.warn('[WS] Cannot send: not connected');
    }
  }

  // 订阅频道
  subscribe(channel: string) {
    this.subscriptions.add(channel);
    this.send({
      type: 'subscribe',
      data: { channel },
    });
  }

  // 取消订阅
  unsubscribe(channel: string) {
    this.subscriptions.delete(channel);
    this.send({
      type: 'unsubscribe',
      data: { channel },
    });
  }

  // 注册消息处理器
  on(type: MessageType, handler: MessageHandler) {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set());
    }
    this.handlers.get(type)!.add(handler);
  }

  // 移除消息处理器
  off(type: MessageType, handler: MessageHandler) {
    this.handlers.get(type)?.delete(handler);
  }

  // 处理收到的消息
  private handleMessage(message: WebSocketMessage) {
    const handlers = this.handlers.get(message.type);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message);
        } catch (e) {
          console.error('[WS] Handler error:', e);
        }
      });
    }

    // 通用处理器
    const allHandlers = this.handlers.get('*' as MessageType);
    if (allHandlers) {
      allHandlers.forEach(handler => handler(message));
    }
  }

  // 心跳
  private startPing() {
    this.pingTimer = setInterval(() => {
      this.send({ type: 'ping' });
    }, 25000);
  }

  private stopPing() {
    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
  }

  // 获取连接状态
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// 单例
let wsManager: WebSocketManager | null = null;

export function getWebSocketManager(options?: WebSocketOptions): WebSocketManager {
  if (!wsManager) {
    wsManager = new WebSocketManager(options);
  }
  return wsManager;
}

// ============================================
// React Hooks
// ============================================

/**
 * 使用 WebSocket 连接
 */
export function useWebSocket(options?: WebSocketOptions) {
  const managerRef = useRef<WebSocketManager | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    managerRef.current = getWebSocketManager(options);

    const connect = async () => {
      try {
        await managerRef.current!.connect();
        setIsConnected(true);
      } catch (e) {
        console.error('Failed to connect WebSocket:', e);
      }
    };

    connect();

    managerRef.current.on('connect' as MessageType, () => setIsConnected(true));
    managerRef.current.on('disconnect' as MessageType, () => setIsConnected(false));

    return () => {
      managerRef.current?.disconnect();
    };
  }, []);

  const subscribe = useCallback((channel: string) => {
    managerRef.current?.subscribe(channel);
  }, []);

  const unsubscribe = useCallback((channel: string) => {
    managerRef.current?.unsubscribe(channel);
  }, []);

  return {
    isConnected,
    subscribe,
    unsubscribe,
    manager: managerRef.current,
  };
}

/**
 * 订阅部署更新
 */
export function useDeploymentUpdates(deploymentId?: string) {
  const [updates, setUpdates] = useState<WebSocketMessage[]>([]);
  const { isConnected, subscribe, unsubscribe } = useWebSocket();

  useEffect(() => {
    if (!isConnected) return;

    const channel = deploymentId ? `deployments:${deploymentId}` : 'deployments';
    subscribe(channel);

    const handler = (message: WebSocketMessage) => {
      if (message.type === 'deployment_update' || message.type === 'deployment_step_update') {
        setUpdates(prev => [...prev.slice(-50), message]);
      }
    };

    getWebSocketManager().on('deployment_update', handler);
    getWebSocketManager().on('deployment_step_update', handler);

    return () => {
      unsubscribe(channel);
      getWebSocketManager().off('deployment_update', handler);
      getWebSocketManager().off('deployment_step_update', handler);
    };
  }, [isConnected, deploymentId, subscribe, unsubscribe]);

  return updates;
}

/**
 * 订阅告警
 */
export function useAlerts(severity?: 'critical' | 'warning' | 'info') {
  const [alerts, setAlerts] = useState<WebSocketMessage[]>([]);
  const { isConnected, subscribe, unsubscribe } = useWebSocket();

  useEffect(() => {
    if (!isConnected) return;

    const channel = severity ? `alerts:${severity}` : 'alerts';
    subscribe(channel);

    const handler = (message: WebSocketMessage) => {
      if (message.type === 'alert_new') {
        setAlerts(prev => [...prev, message]);
      }
    };

    getWebSocketManager().on('alert_new', handler);

    return () => {
      unsubscribe(channel);
      getWebSocketManager().off('alert_new', handler);
    };
  }, [isConnected, severity, subscribe, unsubscribe]);

  const clearAlerts = useCallback(() => {
    setAlerts([]);
  }, []);

  return { alerts, clearAlerts };
}

/**
 * 订阅 Agent 流式响应
 */
export function useAgentStream(conversationId: string) {
  const [chunks, setChunks] = useState<string[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const { isConnected, subscribe, unsubscribe } = useWebSocket();

  useEffect(() => {
    if (!isConnected || !conversationId) return;

    const channel = `conversations:${conversationId}`;
    subscribe(channel);

    const handler = (message: WebSocketMessage) => {
      if (message.type === 'agent_stream') {
        setIsStreaming(!message.data.is_final);
        setChunks(prev => [...prev, message.data.chunk]);
      }
    };

    getWebSocketManager().on('agent_stream', handler);

    return () => {
      unsubscribe(channel);
      getWebSocketManager().off('agent_stream', handler);
      setChunks([]);
      setIsStreaming(false);
    };
  }, [isConnected, conversationId, subscribe, unsubscribe]);

  const fullResponse = chunks.join('');

  return { chunks, fullResponse, isStreaming };
}

/**
 * 订阅版本更新
 */
export function useVersionUpdates(versionId?: string) {
  const [updates, setUpdates] = useState<WebSocketMessage[]>([]);
  const { isConnected, subscribe, unsubscribe } = useWebSocket();

  useEffect(() => {
    if (!isConnected) return;

    const channel = versionId ? `versions:${versionId}` : 'versions';
    subscribe(channel);

    const handler = (message: WebSocketMessage) => {
      if (message.type === 'version_update') {
        setUpdates(prev => [...prev.slice(-20), message]);
      }
    };

    getWebSocketManager().on('version_update', handler);

    return () => {
      unsubscribe(channel);
      getWebSocketManager().off('version_update', handler);
    };
  }, [isConnected, versionId, subscribe, unsubscribe]);

  return updates;
}
