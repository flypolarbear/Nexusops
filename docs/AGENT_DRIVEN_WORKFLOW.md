# NexusOps Agent-Driven Workflow 设计

## 核心理念

**一切皆 Agent**：整个 Kubernetes 工作流都由 Agent 驱动，平台提供统一的 Agent 间通信机制。

## 业界标准选择

### MCP (Model Context Protocol) - Agent 与外部系统连接

[Model Context Protocol](https://www.anthropic.com/news/model-context-protocol) 是 Anthropic 于 2024 年 11 月提出的开放标准，用于连接 AI 模型与外部工具、数据源。

```typescript
// MCP Server 定义示例
interface MCPServer {
  name: string;
  version: string;
  tools: MCPTool[];
  resources: MCPResource[];
  prompts: MCPPrompt[];
}

interface MCPTool {
  name: string;
  description: string;
  inputSchema: JSONSchema;
  handler: (params: any) => Promise<MCPToolResult>;
}
```

### A2A (Agent-to-Agent) - Agent 间通信

[Agent-to-Agent Protocol](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/) 是 Google 于 2025 年 4 月提出的开放标准，用于 Agent 间安全通信。

```typescript
// A2A 消息格式
interface A2AMessage {
  version: "1.0";
  sender: AgentIdentity;
  recipient: AgentIdentity;
  conversation_id: string;
  message_id: string;
  timestamp: string;
  content: A2AContent;
  metadata?: Record<string, any>;
}

interface AgentIdentity {
  agent_id: string;
  agent_name: string;
  agent_version: string;
  provider: string;
}
```

## DNS 操作 Agent 示例

### 场景描述

用户想要：
1. 为测试网站生成一个随机四级域名
2. 自动配置到 Cloudflare DNS
3. 整个过程通过调用 DNS 专用 Agent 完成

### Agent 设计

```yaml
# dns-agent-manifest.yaml
agent_id: com.nexusops.agents.dns
name: DNS Operations Agent
version: 1.0.0
description: 专门处理 DNS 操作的 AI Agent，支持 Cloudflare、Route53 等

# Agent 能力声明
capabilities:
  - dns_record_create
  - dns_record_delete
  - dns_record_update
  - dns_record_query
  - random_domain_generate
  - ssl_certificate_provision

# 支持的 DNS 提供商
providers:
  - cloudflare
  - aws_route53
  - aliyun_dns
  - godaddy

# MCP Tools 定义
mcp_tools:
  - name: create_dns_record
    description: Create a DNS record
    inputSchema:
      type: object
      properties:
        zone_id:
          type: string
          description: DNS Zone ID
        record_type:
          type: string
          enum: [A, AAAA, CNAME, MX, TXT, NS]
        name:
          type: string
          description: Record name (e.g., "www" or "*.test")
        content:
          type: string
          description: Record content (IP address or domain)
        ttl:
          type: integer
          default: 3600
        proxied:
          type: boolean
          default: false
      required: [zone_id, record_type, name, content]

  - name: generate_random_subdomain
    description: Generate a random subdomain name
    inputSchema:
      type: object
      properties:
        base_domain:
          type: string
          description: Base domain (e.g., "test.example.com")
        levels:
          type: integer
          default: 4
          description: Number of subdomain levels
        prefix:
          type: string
          description: Optional prefix for the subdomain
        style:
          type: string
          enum: [random, readable, uuid, short]
          default: readable

  - name: configure_cloudflare_dns
    description: Configure Cloudflare DNS with all necessary records
    inputSchema:
      type: object
      properties:
        zone_name:
          type: string
          description: Cloudflare zone name
        subdomain:
          type: string
          description: Subdomain to configure
        target_ip:
          type: string
          description: Target IP address
        ssl_enabled:
          type: boolean
          default: true
        proxy_enabled:
          type: boolean
          default: true
      required: [zone_name, subdomain, target_ip]

# Agent 间通信支持
a2a_capabilities:
  - can_request_from: ["*"]  # 可以接收来自任何 Agent 的请求
  - can_respond_to: ["*"]
  - can_delegate_to:
    - com.nexusops.agents.ssl  # 可以委托给 SSL Agent
    - com.nexusops.agents.cloudflare

# 示例：如何调用此 Agent
examples:
  - name: "生成四级域名并配置 DNS"
    request:
      query: "为我的测试网站生成一个随机四级域名地址并配置到 cloudflare"
      context:
        project_id: "proj-001"
        target_ip: "192.168.1.100"
        cloudflare_zone: "example.com"
    response:
      structured_output:
        subdomain: "alpha-beta-gamma-delta.test.example.com"
        dns_records:
          - type: "A"
            name: "alpha-beta-gamma-delta.test"
            content: "192.168.1.100"
            proxied: true
        ssl_status: "provisioning"
        url: "https://alpha-beta-gamma-delta.test.example.com"
```

### 实现代码示例

```python
# dns_agent.py - DNS Agent 实现
from typing import Optional, Dict, Any
from dataclasses import dataclass
import secrets
import string
import dns.resolver
import cloudflare

@dataclass
class DNSAgentConfig:
    agent_id: str = "com.nexusops.agents.dns"
    agent_name: str = "DNS Operations Agent"
    version: str = "1.0.0"

class DNSAgent:
    """DNS 操作 Agent - 基于 MCP 标准"""

    def __init__(self, config: DNSAgentConfig):
        self.config = config
        self.cf_client = cloudflare.Cloudflare()

    # MCP Tool: 生成随机子域名
    async def generate_random_subdomain(
        self,
        base_domain: str,
        levels: int = 4,
        prefix: Optional[str] = None,
        style: str = "readable"
    ) -> Dict[str, Any]:
        """
        生成随机多级子域名

        MCP Tool Input Schema:
        {
            "base_domain": "test.example.com",
            "levels": 4,
            "prefix": "app",
            "style": "readable"
        }
        """
        # 可读性词汇列表
        readable_words = [
            "alpha", "beta", "gamma", "delta", "epsilon",
            "nova", "orion", "phoenix", "titan", "aurora",
            "swift", "eagle", "falcon", "hawk", "raven"
        ]

        parts = []
        if prefix:
            parts.append(prefix)

        if style == "readable":
            # 从词汇列表随机选择
            for _ in range(levels - len(parts)):
                parts.append(secrets.choice(readable_words))
        elif style == "uuid":
            # 使用 UUID
            import uuid
            parts.append(str(uuid.uuid4())[:8])
        else:
            # 完全随机
            chars = string.ascii_lowercase + string.digits
            for _ in range(levels - len(parts)):
                parts.append(''.join(secrets.choice(chars) for _ in range(6)))

        subdomain = '-'.join(parts)
        full_domain = f"{subdomain}.{base_domain}"

        return {
            "success": True,
            "subdomain": subdomain,
            "full_domain": full_domain,
            "levels": len(parts),
            "style": style
        }

    # MCP Tool: 配置 Cloudflare DNS
    async def configure_cloudflare_dns(
        self,
        zone_name: str,
        subdomain: str,
        target_ip: str,
        ssl_enabled: bool = True,
        proxy_enabled: bool = True
    ) -> Dict[str, Any]:
        """
        配置 Cloudflare DNS 记录

        MCP Tool Input Schema:
        {
            "zone_name": "example.com",
            "subdomain": "alpha-beta-gamma-delta.test",
            "target_ip": "192.168.1.100",
            "ssl_enabled": true,
            "proxy_enabled": true
        }
        """
        # 获取 Zone ID
        zones = self.cf_client.zones.list(name=zone_name)
        if not zones.result:
            return {"success": False, "error": f"Zone {zone_name} not found"}

        zone_id = zones.result[0].id

        # 创建 DNS 记录
        dns_record = self.cf_client.dns.records.create(
            zone_id=zone_id,
            type="A",
            name=subdomain,
            content=target_ip,
            ttl=3600,
            proxied=proxy_enabled
        )

        result = {
            "success": True,
            "dns_record": {
                "id": dns_record.id,
                "type": dns_record.type,
                "name": dns_record.name,
                "content": dns_record.content,
                "proxied": dns_record.proxied
            },
            "full_url": f"https://{subdomain}.{zone_name}"
        }

        # 如果启用 SSL，可以委托给 SSL Agent
        if ssl_enabled:
            # A2A 调用 SSL Agent
            ssl_result = await self.delegate_to_ssl_agent(
                domain=f"{subdomain}.{zone_name}",
                zone_id=zone_id
            )
            result["ssl_status"] = ssl_result.get("status", "unknown")

        return result

    # A2A: 委托给其他 Agent
    async def delegate_to_ssl_agent(
        self,
        domain: str,
        zone_id: str
    ) -> Dict[str, Any]:
        """
        通过 A2A 协议委托给 SSL Agent

        A2A Message Format:
        {
            "sender": {"agent_id": "com.nexusops.agents.dns", ...},
            "recipient": {"agent_id": "com.nexusops.agents.ssl", ...},
            "content": {"action": "provision_ssl", "domain": "...", "zone_id": "..."}
        }
        """
        # 实现 A2A 消息发送
        a2a_message = {
            "version": "1.0",
            "sender": {
                "agent_id": self.config.agent_id,
                "agent_name": self.config.agent_name,
                "agent_version": self.config.version,
                "provider": "nexusops"
            },
            "recipient": {
                "agent_id": "com.nexusops.agents.ssl",
                "agent_name": "SSL Certificate Agent",
                "provider": "nexusops"
            },
            "conversation_id": f"conv-{secrets.token_hex(8)}",
            "message_id": f"msg-{secrets.token_hex(8)}",
            "content": {
                "action": "provision_ssl",
                "domain": domain,
                "zone_id": zone_id,
                "certificate_type": "universal"
            }
        }

        # 发送 A2A 消息并等待响应
        response = await self.send_a2a_message(a2a_message)
        return response

    # 处理来自其他 Agent 的 A2A 请求
    async def handle_a2a_request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理来自其他 Agent 的 A2A 请求

        这是 Agent 间协作的核心接口
        """
        action = message.get("content", {}).get("action")

        if action == "create_dns_record":
            params = message["content"]["params"]
            result = await self.configure_cloudflare_dns(**params)
        elif action == "generate_subdomain":
            params = message["content"]["params"]
            result = await self.generate_random_subdomain(**params)
        else:
            result = {"success": False, "error": f"Unknown action: {action}"}

        # 返回 A2A 响应
        return {
            "version": "1.0",
            "sender": {
                "agent_id": self.config.agent_id,
                "agent_name": self.config.agent_name,
                "provider": "nexusops"
            },
            "recipient": message["sender"],
            "conversation_id": message["conversation_id"],
            "message_id": f"msg-{secrets.token_hex(8)}",
            "in_reply_to": message["message_id"],
            "content": result
        }
```

## Agent 间协作工作流

### 工作流示例：部署测试环境

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        NexusOps Workflow Orchestrator                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 1: 部署协调 Agent (nexusops.deploy)                                     │
│  ────────────────────────────────────────                                    │
│  任务: "为 Phoenix 版本部署测试环境"                                            │
│                                                                              │
│  1. 分析任务需求                                                              │
│  2. 确定需要的 Agent:                                                         │
│     - DNS Agent (配置域名)                                                    │
│     - K8s Agent (部署服务)                                                    │
│     - SSL Agent (配置证书)                                                    │
│     - Monitoring Agent (配置监控)                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
         ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
         │ A2A → DNS Agent   │ │ A2A → K8s Agent   │ │ A2A → SSL Agent   │
         │ ────────────────  │ │ ────────────────  │ │ ────────────────  │
         │                   │ │                   │ │                   │
         │ 请求:             │ │ 请求:             │ │ 请求:             │
         │ "生成四级域名     │ │ "部署 Phoenix    │ │ "为域名配置      │
         │  并配置到 CF"     │ │  到 us-east"     │ │  SSL 证书"       │
         │                   │ │                   │ │                   │
         │ 响应:             │ │ 响应:             │ │ 响应:             │
         │ {                 │ │ {                 │ │ {                 │
         │   subdomain:      │ │   deployment: {   │ │   ssl_status:     │
         │   "a-b-c-d.test"  │ │     status: "ok"  │ │   "provisioned"   │
         │   url: "https://  │ │     pods: 3       │ │   cert_issuer:    │
         │   ...example.com" │ │   service_ip:     │ │   "letsencrypt"   │
         │ }                 │ │   "10.0.0.100"    │ │ }                 │
         └──────────────────┘ └──────────────────┘ └──────────────────┘
                    │                 │                 │
                    └─────────────────┼─────────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 2: 汇总结果并返回                                                       │
│  ────────────────────────                                                    │
│  {                                                                           │
│    "status": "success",                                                      │
│    "environment": {                                                          │
│      "url": "https://alpha-beta-gamma-delta.test.example.com",               │
│      "dns_configured": true,                                                 │
│      "ssl_enabled": true,                                                    │
│      "k8s_deployment": {                                                      │
│        "namespace": "phoenix-testing",                                        │
│        "pods": 3,                                                             │
│        "service_ip": "10.0.0.100"                                            │
│      }                                                                        │
│    }                                                                          │
│  }                                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 平台内置 Agent 列表

| Agent ID | 名称 | 功能 | MCP Tools |
|----------|------|------|-----------|
| `nexusops.dns` | DNS Operations | DNS 记录管理、域名生成 | `create_dns_record`, `generate_random_subdomain`, `configure_cloudflare_dns` |
| `nexusops.k8s` | Kubernetes Operations | K8s 资源管理、部署操作 | `deploy_manifest`, `scale_deployment`, `get_pod_logs`, `describe_resource` |
| `nexusops.ssl` | SSL Certificate | SSL 证书管理 | `provision_ssl`, `renew_certificate`, `get_cert_status` |
| `nexusops.deploy` | Deployment Orchestrator | 部署流程编排 | `create_deployment`, `rollback_deployment`, `get_deployment_status` |
| `nexusops.alert` | Alert Analysis | 告警分析与根因定位 | `analyze_alert`, `find_root_cause`, `suggest_fix` |
| `nexusops.git` | Git Operations | Git 仓库操作 | `create_branch`, `create_pr`, `get_commit_info`, `compare_branches` |

## 第三方 Agent 扩展

### Agent 开发 SDK

```python
# nexusops_agent_sdk/example_agent.py
from nexusops_agent_sdk import Agent, tool, a2a_handler

class MyCustomAgent(Agent):
    """
    自定义 Agent 示例
    """
    agent_id = "com.mycompany.agents.custom"
    name = "My Custom Agent"
    version = "1.0.0"

    @tool(
        description="Do something custom",
        input_schema={
            "type": "object",
            "properties": {
                "param1": {"type": "string"},
                "param2": {"type": "integer"}
            }
        }
    )
    async def do_custom_thing(self, param1: str, param2: int):
        # 实现自定义逻辑
        return {"result": "done"}

    @a2a_handler
    async def handle_a2a_message(self, message):
        # 处理来自其他 Agent 的请求
        pass

# 启动 Agent
if __name__ == "__main__":
    agent = MyCustomAgent()
    agent.run()  # 启动 MCP Server + A2A 监听
```

## 与 NexusOps 集成

### 前端调用 Agent

```typescript
// src/services/agentService.ts
import { AgentRequest, AgentResponse } from '../types/agent';

export class AgentService {
  private baseUrl = '/api/v1/agents';

  // 调用单个 Agent
  async invoke(agentId: string, request: Partial<AgentRequest>): Promise<AgentResponse> {
    const response = await fetch(`${this.baseUrl}/${agentId}/invoke`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        request_id: crypto.randomUUID(),
        conversation_id: crypto.randomUUID(),
        agent_id: agentId,
        query: request.query,
        context: request.context,
        output_config: request.output_config,
      }),
    });
    return response.json();
  }

  // 流式调用 Agent
  async *stream(agentId: string, request: Partial<AgentRequest>): AsyncGenerator<AgentResponse> {
    const response = await fetch(`${this.baseUrl}/${agentId}/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    while (reader) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n').filter(Boolean);

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          yield JSON.parse(line.slice(6));
        }
      }
    }
  }

  // DNS Agent 专用方法
  async generateDNSDomain(params: {
    baseDomain: string;
    levels?: number;
    targetIP: string;
    cloudflareZone: string;
  }): Promise<AgentResponse> {
    return this.invoke('com.nexusops.agents.dns', {
      query: `为我的测试网站生成一个${params.levels || 4}级域名并配置到 Cloudflare`,
      context: {
        base_domain: params.baseDomain,
        target_ip: params.targetIP,
        cloudflare_zone: params.cloudflareZone,
      },
    });
  }
}
```

### React 组件示例

```tsx
// src/components/DNSAgentDemo.tsx
import { useState } from 'react';
import { Button, Input, Form, Card, Result } from 'antd';
import { AgentService } from '../services/agentService';

export function DNSAgentDemo() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const agentService = new AgentService();

  const handleGenerateDNS = async (values: any) => {
    setLoading(true);
    try {
      const response = await agentService.generateDNSDomain({
        baseDomain: values.baseDomain,
        levels: 4,
        targetIP: values.targetIP,
        cloudflareZone: values.cloudflareZone,
      });
      setResult(response.structured_output);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title="DNS Agent Demo">
      <Form onFinish={handleGenerateDNS} layout="vertical">
        <Form.Item name="baseDomain" label="Base Domain">
          <Input placeholder="test.example.com" />
        </Form.Item>
        <Form.Item name="targetIP" label="Target IP">
          <Input placeholder="192.168.1.100" />
        </Form.Item>
        <Form.Item name="cloudflareZone" label="Cloudflare Zone">
          <Input placeholder="example.com" />
        </Form.Item>
        <Button type="primary" htmlType="submit" loading={loading}>
          生成四级域名
        </Button>
      </Form>

      {result && (
        <Result
          status="success"
          title="DNS 配置成功!"
          subTitle={
            <div>
              <p>域名: {result.full_domain}</p>
              <p>URL: <a href={result.url} target="_blank">{result.url}</a></p>
            </div>
          }
        />
      )}
    </Card>
  );
}
```

## 技术栈推荐

### JSON 输出保证

| 方案 | 库 | 说明 |
|------|-----|------|
| **首选** | [Instructor](https://github.com/instructor-ai/instructor) | 支持 `mode='tools'` 和 `mode='json'`，自动重试 |
| 状态机 | [Outlines](https://github.com/dottxt-ai/outlines) | 正则约束，保证输出格式 |
| 修复 | [json-repair](https://github.com/mangiucugna/json_repair) | 修复微小 JSON 瑕疵 |

### MCP Server 托管

| 平台 | 说明 |
|------|------|
| **[Cloudflare Workers](https://blog.cloudflare.com/model-context-protocol/)** | 官方支持远程 MCP，TypeScript，OAuth |
| Vercel | Serverless 部署 |
| 自托管 | Docker/K8s |

## 参考资料

- [Anthropic - Model Context Protocol](https://www.anthropic.com/news/model-context-protocol)
- [Google - Agent-to-Agent Protocol](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/)
- [Cloudflare - Build MCP Server on Workers](https://blog.cloudflare.com/model-context-protocol/)
- [arXiv - Which LLM Multi-Agent Protocol to Choose?](https://arxiv.org/pdf/2510.17149)
- [MCP Official Documentation](https://modelcontextprotocol.io/)
