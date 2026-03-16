# Skill-Tool 分层模式

## 问题描述

在 AI Agent 系统中，如何组织领域知识（指导）和操作能力（执行）的关系？

## 解决方案

将系统分为两个清晰的层次：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              平台服务层                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Skills = 平台索引的知识/指导                                               │
│   • 从 skills.sh 同步                                                       │
│   • SKILL.md 格式                                                           │
│   • 领域最佳实践                                                             │
│   • 注入到 System Prompt                                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ 注入知识
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Agent 层                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Tools = Agent 定义的能力/操作                                              │
│   • JSON Schema 格式                                                        │
│   • LLM Function Calling 接口                                               │
│   • 可执行的操作                                                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 代码示例

```python
# Skill: 来自 skills.sh 的 SKILL.md
# 内容: GitOps 最佳实践、ArgoCD 部署模式等

# Tool: Agent 定义的执行接口
class GitOpsAgentHandler(BaseAgentHandler):
    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "argocd_sync_app",
                "description": "Sync an ArgoCD application",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string"},
                        "namespace": {"type": "string"}
                    },
                    "required": ["app_name"]
                }
            }
        ]
```

### 执行流程

```python
# 1. 平台层注入 Skill 内容
skill = await skill_registry.get_skill("gitops-workflow")
system_prompt = f"""
你是 GitOps 助手。

{skill.extract_guidance()}

请帮助用户管理 ArgoCD 应用。
"""

# 2. Agent 层提供 Tools
tools = router.get_all_tools()

# 3. LLM 基于知识选择 Tool
response = await llm.chat(
    messages=[{"role": "system", "content": system_prompt}, 
              {"role": "user", "content": "同步 api-gateway 应用"}],
    tools=tools
)

# 4. 执行 Tool
if response.tool_calls:
    result = await router.route_and_execute(
        agent_id="nexusops.gitops",
        tools=response.tool_calls
    )
```

## 对比

| 维度 | Skills (平台层) | Tools (Agent 层) |
|------|-----------------|------------------|
| **归属** | 平台服务索引 | 各 Agent 定义 |
| **存储** | PostgreSQL | 代码内定义 |
| **格式** | Markdown (SKILL.md) | JSON Schema |
| **作用** | 知识/指导 | 能力/操作 |
| **注入方式** | System Prompt | Function Calling |
| **来源** | skills.sh 同步 | Agent Handler 实现 |

## 注意事项

- ✅ Skills 告诉 LLM "怎么做"（知识）
- ✅ Tools 让 LLM "实际执行"（能力）
- ✅ 保持清晰的分层边界
- ✅ Skills 可以跨 Agent 复用
- ❌ 不要把操作逻辑放在 Skill 中
- ❌ 不要把知识指导硬编码在 Tool 中
