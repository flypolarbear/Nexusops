/**
 * AI Assistant Drawer - Agent 架构版本
 *
 * 支持：
 * - 多 Agent 选择
 * - 快捷命令
 * - 结构化响应渲染
 * - 建议操作执行
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import {
  Drawer,
  Input,
  Button,
  Avatar,
  Spin,
  Space,
  Typography,
  Tooltip,
  message,
  Statistic,
  Row,
  Col,
  Card,
  Tag,
  Divider,
  List,
  Select,
} from 'antd';
import {
  RobotOutlined,
  UserOutlined,
  SendOutlined,
  DeleteOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import type { AgentMessage, AgentAction, AgentManifest, RelatedResource } from '../types/agent';
import { BUILTIN_AGENTS, generateRequestId, generateConversationId } from '../types/agent';
import { AgentResponseRenderer } from './AgentResponseRenderer';
import { parseCommand } from '../services/agentService';
import { useAgentContextStore } from '../stores/agentContextStore';

const { Text } = Typography;
const { TextArea } = Input;

// ============================================
// Props
// ============================================

interface AIAssistantDrawerProps {
  open: boolean;
  onClose: () => void;
}

// ============================================
// Main Component
// ============================================

export default function AIAssistantDrawer({ open, onClose }: AIAssistantDrawerProps) {
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<string>('nexusops.chat');
  const [showCommands, setShowCommands] = useState(false);
  const [conversationId] = useState(() => generateConversationId());
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<any>(null);

  // 获取上下文
  const { setConversationId: setGlobalConversationId } = useAgentContextStore();

  useEffect(() => {
    if (open && conversationId) {
      setGlobalConversationId(conversationId);
    }
  }, [open, conversationId, setGlobalConversationId]);

  // 滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 获取选中的 Agent
  const getCurrentAgent = (): AgentManifest | undefined => {
    return BUILTIN_AGENTS.find(a => a.agent_id === selectedAgent);
  };

  // 发送消息
  const handleSend = useCallback(async () => {
    if (!inputValue.trim() || loading) return;

    const userMessage: AgentMessage = {
      id: generateRequestId(),
      conversation_id: conversationId,
      role: 'user',
      content: inputValue.trim(),
      created_at: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setShowCommands(false);
    setLoading(true);

    try {
      // 检查是否是快捷命令
      const command = parseCommand(inputValue.trim());

      // 模拟 AI 响应
      await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 1000));

      const agent = getCurrentAgent();
      const response = generateMockResponse(inputValue.trim(), agent, command);

      const assistantMessage: AgentMessage = {
        id: generateRequestId(),
        conversation_id: conversationId,
        role: 'assistant',
        content: response.content || '',
        agent_id: selectedAgent,
        agent_name: agent?.name || 'AI Assistant',
        structured_output: response.structured_output,
        suggested_actions: response.suggested_actions,
        related_resources: response.related_resources,
        metadata: {
          model: 'gpt-4',
          latency_ms: 1500 + Math.random() * 1000,
          tokens_used: { input: 50, output: 200, total: 250 },
        },
        created_at: new Date().toISOString(),
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      message.error('Failed to get response');
    } finally {
      setLoading(false);
    }
  }, [inputValue, loading, conversationId, selectedAgent]);

  // 处理键盘事件
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // 处理操作点击
  const handleActionClick = (action: AgentAction) => {
    message.info(`Action: ${action.label}`);
    // 实际应该调用 executeAction
  };

  // 处理资源点击
  const handleResourceClick = (resource: RelatedResource) => {
    message.info(`Resource: ${resource.name}`);
    // 实际应该导航到资源详情
  };

  // 清除对话
  const handleClear = () => {
    setMessages([]);
    message.success('Conversation cleared');
  };

  // 选择命令
  const handleCommandSelect = (command: string) => {
    setInputValue(command);
    setShowCommands(false);
    inputRef.current?.focus();
  };

  // 过滤命令
  useEffect(() => {
    if (inputValue.startsWith('/')) {
      setShowCommands(true);
    } else {
      setShowCommands(false);
    }
  }, [inputValue]);

  return (
    <Drawer
      title={
        <div className="flex items-center gap-2">
          <RobotOutlined className="text-primary-500" />
          <span>AI Operations Assistant</span>
          <Tag color="purple" className="ml-2">Phase 3.5</Tag>
        </div>
      }
      placement="right"
      width={520}
      onClose={onClose}
      open={open}
      extra={
        <Space>
          <Select
            value={selectedAgent}
            onChange={setSelectedAgent}
            style={{ width: 180 }}
            size="small"
            options={BUILTIN_AGENTS.map(a => ({
              value: a.agent_id,
              label: a.name,
            }))}
          />
          <Tooltip title="Clear conversation">
            <Button type="text" icon={<DeleteOutlined />} onClick={handleClear} />
          </Tooltip>
        </Space>
      }
      styles={{ body: { display: 'flex', flexDirection: 'column', padding: 0 } }}
    >
      {/* Stats */}
      <div className="p-4 border-b bg-gray-50">
        <Row gutter={12}>
          <Col span={12}>
            <Card size="small" className="text-center">
              <Statistic
                title="Conversations"
                value={12847}
                prefix={<RobotOutlined className="text-blue-500" />}
                valueStyle={{ fontSize: 18, color: '#3b82f6' }}
              />
              <Tag color="green" className="mt-1">+12%</Tag>
            </Card>
          </Col>
          <Col span={12}>
            <Card size="small" className="text-center">
              <Statistic
                title="Success Rate"
                value={99.2}
                suffix="%"
                valueStyle={{ fontSize: 18, color: '#22c55e' }}
              />
              <Tag color="green" className="mt-1">+0.3%</Tag>
            </Card>
          </Col>
        </Row>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center">
            <Avatar size={64} icon={<RobotOutlined />} className="bg-primary-500 mb-4" />
            <Text strong className="text-lg mb-2">How can I help you today?</Text>
            <Text type="secondary" className="mb-4">
              Ask me about deployments, resources, or use slash commands.
            </Text>

            {/* Quick Commands */}
            <div className="w-full max-w-sm mb-4">
              <Divider className="text-xs text-gray-400">Quick Commands</Divider>
              <div className="space-y-2">
                {[
                  { cmd: '/deploy Phoenix to us-east', desc: 'Deploy version' },
                  { cmd: '/status Phoenix', desc: 'Check status' },
                  { cmd: '/logs api-gateway --tail 100', desc: 'View logs' },
                  { cmd: '/compare Phoenix vs Titan', desc: 'Compare versions' },
                ].map((item, i) => (
                  <Button
                    key={i}
                    block
                    size="small"
                    type="dashed"
                    onClick={() => handleCommandSelect(item.cmd)}
                    className="text-left"
                  >
                    <code className="text-xs">{item.cmd}</code>
                  </Button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.role === 'assistant' && (
                <Avatar icon={<RobotOutlined />} className="bg-primary-500 shrink-0" />
              )}
              <div className={`max-w-[85%] ${msg.role === 'user' ? '' : 'w-full'}`}>
                {msg.role === 'user' ? (
                  <div className="bg-primary-500 text-white px-4 py-3 rounded-lg">
                    <Text style={{ color: 'white' }}>{msg.content}</Text>
                  </div>
                ) : (
                  <AgentResponseRenderer
                    message={msg}
                    onActionClick={handleActionClick}
                    onResourceClick={handleResourceClick}
                  />
                )}
              </div>
              {msg.role === 'user' && (
                <Avatar icon={<UserOutlined />} className="bg-gray-400 shrink-0" />
              )}
            </div>
          ))
        )}

        {loading && (
          <div className="flex gap-3">
            <Avatar icon={<RobotOutlined />} className="bg-primary-500" />
            <div className="bg-gray-100 px-4 py-3 rounded-lg flex items-center gap-2">
              <Spin size="small" />
              <Text type="secondary">Thinking...</Text>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Command Autocomplete */}
      {showCommands && (
        <div className="border-t bg-white p-2 max-h-48 overflow-auto">
          <Text type="secondary" className="text-xs px-2">Available Commands</Text>
          <List
            size="small"
            dataSource={[
              { cmd: '/deploy', usage: '/deploy <version> to <region>' },
              { cmd: '/rollback', usage: '/rollback <version> in <region>' },
              { cmd: '/status', usage: '/status <version>' },
              { cmd: '/logs', usage: '/logs <service> --tail <lines>' },
              { cmd: '/compare', usage: '/compare <v1> vs <v2>' },
            ].filter(c => inputValue === '/' || c.cmd.startsWith(inputValue.split(' ')[0]))}
            renderItem={(item) => (
              <List.Item
                className="cursor-pointer hover:bg-gray-50 px-2 rounded"
                onClick={() => handleCommandSelect(item.usage)}
              >
                <div>
                  <code className="text-sm font-medium">{item.cmd}</code>
                  <Text type="secondary" className="text-xs ml-2">{item.usage}</Text>
                </div>
              </List.Item>
            )}
          />
        </div>
      )}

      {/* Input */}
      <div className="border-t p-4">
        <div className="flex gap-2 mb-2">
          <Tooltip title="Show commands">
            <Button
              icon={<ThunderboltOutlined />}
              onClick={() => {
                setInputValue('/');
                setShowCommands(true);
                inputRef.current?.focus();
              }}
            />
          </Tooltip>
        </div>
        <div className="flex gap-2">
          <TextArea
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about resources, deployments... or use /commands"
            autoSize={{ minRows: 1, maxRows: 4 }}
            className="flex-1"
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            disabled={!inputValue.trim() || loading}
          />
        </div>
        <Text type="secondary" className="text-xs mt-2 block">
          Press Enter to send • Type <code>/</code> for commands
        </Text>
      </div>
    </Drawer>
  );
}

// ============================================
// Mock Response Generator
// ============================================

function generateMockResponse(
  query: string,
  _agent: AgentManifest | undefined,
  command: ReturnType<typeof parseCommand>
): Partial<AgentMessage> {
  // 处理快捷命令
  if (command) {
    switch (command.command) {
      case '/deploy':
        return {
          content: `## 🚀 Deployment Triggered

**Version:** ${command.params.version}
**Target Region:** ${command.params.region}

The deployment is in progress. I'll notify you when it completes.`,
          structured_output: {
            type: 'deployment_status',
            data: {
              codename: command.params.version,
              regions: [
                { name: command.params.region, status: 'progressing', replicas: { ready: 0, total: 3 } }
              ]
            }
          },
          suggested_actions: [
            { id: '1', type: 'navigate', label: 'View Progress', params: { url: '/deployments' } },
          ],
        };

      case '/status':
        return {
          content: `## 📊 Version Status: ${command.params.version}

The version is deployed and healthy across all regions.`,
          structured_output: {
            type: 'deployment_status',
            data: {
              codename: command.params.version,
              regions: [
                { name: 'US East', status: 'healthy', replicas: { ready: 3, total: 3 } },
                { name: 'EU West', status: 'healthy', replicas: { ready: 2, total: 2 } },
              ]
            }
          },
          related_resources: [
            { type: 'version', id: command.params.version, name: command.params.version },
          ],
        };

      case '/logs':
        return {
          content: `## 📋 Service Logs: ${command.params.service}

Showing last **${command.params.tail || 100}** lines:

\`\`\`log
2024-01-15 14:32:15 INFO  [main] Request received: GET /api/v1/users
2024-01-15 14:32:15 DEBUG [db] Query executed in 23ms
2024-01-15 14:32:15 INFO  [main] Response sent: 200 OK
\`\`\``,
        };

      case '/compare':
        return {
          content: `## 🔄 Version Comparison

### ${command.params.version1} vs ${command.params.version2}`,
          structured_output: {
            type: 'version_comparison',
            data: {
              version1: { codename: command.params.version1 },
              version2: { codename: command.params.version2 },
              differences: [
                { aspect: 'Deployed Regions', v1_value: '5', v2_value: '1' },
                { aspect: 'Health Status', v1_value: '4/5 Healthy', v2_value: '1/1 Healthy' },
              ],
              recommendation: `${command.params.version1} is ready for production promotion.`,
            }
          },
        };
    }
  }

  // 通用响应
  const responses: Record<string, string> = {
    default: `I understand you're asking about: "${query}"

Let me help you with that. Based on the current system state, here's what I found:

- All services are operational
- No critical incidents in the last 24 hours
- Resource utilization is within expected ranges`,
    alert: `## Current Alerts Summary

I found **3 active alerts** in the system:

| Severity | Service | Issue |
|----------|---------|-------|
| Critical | chat-service | Memory usage above 90% |
| Warning | api-gateway | CPU usage above 80% |
| Info | api-gateway | P95 latency above 500ms |

**Recommendation**: Check the Alerts page for details.`,
    deploy: `## Recent Deployments

Here's the status of recent deployments:

1. **api-gateway** v1.2.3 - Synced & Healthy
2. **chat-gateway** v2.0.1 - Out of Sync
3. **auth-service** v1.1.0 - Failed`,
  };

  const lowerQuery = query.toLowerCase();
  let content = responses.default;

  if (lowerQuery.includes('alert') || lowerQuery.includes('warning')) {
    content = responses.alert;
  } else if (lowerQuery.includes('deploy')) {
    content = responses.deploy;
  }

  return {
    content,
    suggested_actions: [
      { id: '1', type: 'query', label: 'Check Alerts', params: { query: 'Show alerts' } },
      { id: '2', type: 'navigate', label: 'View Deployments', params: { url: '/deployments' } },
    ],
  };
}
