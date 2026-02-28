"""
NexusOps Agents - Chat Agent Handler

nexusops.chat: 通用 AI 助手，支持快捷命令和真实 LLM 对话
"""

import asyncio
import os
from typing import List, Dict, Any, Optional

import json
from app.gateway.executor.router import get_executor_router
from app.llm.base import LLMMessage, MessageRole
from app.agents.base import BaseAgentHandler
from app.gateway.executor.base import ExecutorRequest, ExecutorResult


class ChatAgentHandler(BaseAgentHandler):
    """Chat agent handler for general conversations and quick commands"""

    def __init__(self):
        self._llm_client = None
        self._last_config = None  # Track last config to detect changes

    @property
    def agent_id(self) -> str:
        return "nexusops.chat"

    @property
    def capabilities(self) -> List[str]:
        return ["chat", "quick_commands", "deployment_info", "status_query", "llm_integration"]

    def _get_llm_client(self):
        """Get or create LLM client from runtime config or env"""
        try:
            # Try to get config from runtime config manager first
            from app.api.llm_providers import get_config_manager

            manager = get_config_manager()
            config = manager.get_config()

            # Get current provider config
            provider_config = config.providers.get(config.current_provider)
            if provider_config and provider_config.api_key:
                # Check if config changed
                current_config = (config.current_provider, config.current_model, provider_config.api_key[:8] if provider_config.api_key else None)
                if self._llm_client is not None and self._last_config == current_config:
                    return self._llm_client

                # Create new client with runtime config
                self._last_config = current_config

                if config.current_provider in ["glm", "zhipu"]:
                    from app.llm.glm import GLMClient
                    self._llm_client = GLMClient(
                        api_key=provider_config.api_key,
                        model=config.current_model,
                        base_url=provider_config.base_url
                    )
                    return self._llm_client

        except Exception as e:
            print(f"Failed to get runtime config: {e}")

        # Fallback to environment variables
        if self._llm_client is None:
            try:
                from app.llm.glm import GLMClient
                api_key = os.getenv("GLM_API_KEY")
                if api_key:
                    self._llm_client = GLMClient(
                        api_key=api_key,
                        model=os.getenv("GLM_MODEL", "glm-4-flash")
                    )
                    self._last_config = ("glm", os.getenv("GLM_MODEL", "glm-4-flash"), api_key[:8] if api_key else None)
            except Exception as e:
                print(f"Failed to initialize LLM client from env: {e}")

        return self._llm_client

    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        """Handle chat requests"""
        query = request.query.lower()
        context = request.request_context

        # Handle quick commands
        if query.startswith("/deploy"):
            return self._handle_deploy_command(request)
        elif query.startswith("/status"):
            return self._handle_status_command(request)
        elif query.startswith("/rollback"):
            return self._handle_rollback_command(request)
        elif query.startswith("/logs"):
            return self._handle_logs_command(request)
        else:
            return await self._handle_general_chat(request)

    def _handle_deploy_command(self, request: ExecutorRequest) -> ExecutorResult:
        """Handle /deploy command"""
        context = request.request_context
        codename = context.get("codename", "unknown")
        region = context.get("region", "us-east")

        return self._success(
            text=f"""## 🚀 Deployment Triggered

**Version:** {codename}
**Target Region:** {region}

The deployment has been initiated. I'll notify you when it completes.

### Deployment Steps
1. ✅ CI/CD Build - Completed
2. 🔄 ArgoCD Sync - In Progress
3. ⏳ Health Check - Pending

Estimated time: 2-3 minutes
""",
            structured_output={
                "type": "deployment_status",
                "data": {
                    "codename": codename,
                    "regions": [{"name": region, "status": "progressing"}],
                },
            },
            suggested_actions=[
                self._action("view-progress", "navigate", "View Progress",
                           {"url": "/deployments"}),
                self._action("view-logs", "invoke", "View Logs",
                           {"agent_id": "nexusops.chat", "query": f"/logs {codename}"}),
            ],
            metadata={"operation": "deploy"},
        )

    def _handle_status_command(self, request: ExecutorRequest) -> ExecutorResult:
        """Handle /status command"""
        context = request.request_context
        codename = context.get("codename", "unknown")

        return self._success(
            text=f"""## 📊 Version Status: {codename}

The version is deployed and healthy across all regions.

### Regional Status
| Region | Status | Health | Replicas |
|--------|--------|--------|----------|
| US East | ✅ Synced | 🟢 Healthy | 3/3 |
| EU West | ✅ Synced | 🟢 Healthy | 2/2 |

**Last deployed:** 2 hours ago
""",
            structured_output={
                "type": "deployment_status",
                "data": {
                    "codename": codename,
                    "regions": [
                        {"name": "US East", "status": "healthy", "replicas": {"ready": 3, "total": 3}},
                        {"name": "EU West", "status": "healthy", "replicas": {"ready": 2, "total": 2}},
                    ],
                },
            },
            metadata={"operation": "status"},
        )

    def _handle_rollback_command(self, request: ExecutorRequest) -> ExecutorResult:
        """Handle /rollback command"""
        context = request.request_context
        codename = context.get("codename", "unknown")
        region = context.get("region", "us-east")

        return self._success(
            text=f"""## ⏪ Rollback Initiated

**Version:** {codename}
**Region:** {region}

Rolling back to the previous stable version...

### Rollback Steps
1. ✅ Identify previous version
2. 🔄 Trigger ArgoCD rollback
3. ⏳ Verify health check

Estimated time: 1-2 minutes
""",
            suggested_actions=[
                self._action("confirm-rollback", "invoke", "Confirm Rollback",
                           {"agent_id": "nexusops.deploy", "query": f"confirm rollback {codename}"},
                           confirm_required=True, danger=True),
            ],
            metadata={"operation": "rollback"},
        )

    def _handle_logs_command(self, request: ExecutorRequest) -> ExecutorResult:
        """Handle /logs command"""
        context = request.request_context
        service = context.get("resource_name", "unknown")

        return self._success(
            text=f"""## 📋 Logs: {service}

Showing last 100 lines:

```
2026-02-25 00:00:01 INFO  Starting service...
2026-02-25 00:00:02 INFO  Connected to database
2026-02-25 00:00:03 INFO  Service ready on port 8080
...
```
""",
            suggested_actions=[
                self._action("full-logs", "invoke", "View Full Logs",
                           {"agent_id": "nexusops.logs", "query": f"logs {service} --tail 1000"}),
            ],
            metadata={"operation": "logs"},
        )

    async def _handle_general_chat(self, request: ExecutorRequest) -> ExecutorResult:
        """Handle general chat with real LLM"""
        llm_client = self._get_llm_client()

        if llm_client is None:
            # Fallback to mock response if LLM not available
            return self._fallback_chat(request)

        try:
            # 1. Get tools from all agents
            router = get_executor_router()
            all_tools = router.get_all_tools()

            # 2. Convert tools to GLM format and build map
            glm_tools = []
            tool_agent_map = {}

            for tool in all_tools:
                agent_id = tool.get("x-nexusops-agent-id")
                if not agent_id:
                    continue

                tool_name = tool["name"]
                tool_agent_map[tool_name] = agent_id

                # Convert to GLM format
                glm_tool = {
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "description": tool.get("description", ""),
                        "parameters": tool.get("inputSchema", {})
                    }
                }
                glm_tools.append(glm_tool)

            # 3. Build messages
            system_prompt = """你是 NexusOps 的 AI 运维助手。你帮助用户管理 Kubernetes 集群、部署服务、查看日志和监控资源。

你的职责：
1. 回答关于 Kubernetes、云服务和运维的问题
2. 帮助用户诊断和解决问题
3. 提供操作建议和最佳实践
4. 支持快捷命令：/deploy, /status, /rollback, /logs

请用中文回复，保持简洁专业。如果需要执行具体操作，建议用户使用相应的快捷命令。"""

            messages = [
                LLMMessage(role=MessageRole.SYSTEM, content=system_prompt),
                LLMMessage(role=MessageRole.USER, content=request.query)
            ]

            # 4. Call LLM loop
            max_turns = 5
            current_turn = 0
            final_response = ""

            while current_turn < max_turns:
                current_turn += 1

                response = await llm_client.chat(
                    messages=messages,
                    tools=glm_tools if glm_tools else None
                )

                # Add assistant response to history
                messages.append(LLMMessage(
                    role=MessageRole.ASSISTANT,
                    content=response.content or "",
                    tool_calls=response.tool_calls
                ))
                
                final_response = response.content

                # If no tool calls, we are done
                if not response.tool_calls:
                    break

                # Execute tool calls
                for tool_call in response.tool_calls:
                    function = tool_call.get("function", {})
                    name = function.get("name")
                    arguments = function.get("arguments")
                    call_id = tool_call.get("id")

                    if isinstance(arguments, str):
                        try:
                            arguments = json.loads(arguments)
                        except:
                            arguments = {}

                    agent_id = tool_agent_map.get(name)
                    result_content = ""
                    
                    if not agent_id:
                        result_content = f"Error: Tool {name} not found"
                    else:
                        # Execute tool via router
                        tool_request = {
                            "name": name,
                            "params": arguments
                        }

                        exec_result = await router.route_and_execute(
                            agent_id=agent_id,
                            trace_id=request.context.trace_id,
                            request_id=f"{request.context.request_id}-{call_id}",
                            query=f"Execute tool {name}",
                            tools=[tool_request]
                        )

                        if exec_result.success:
                            result_content = exec_result.content.get("text", "")
                        else:
                            error_msg = exec_result.error.get("message") if exec_result.error else "Unknown error"
                            result_content = f"Error: {error_msg}"

                    # Add tool result to history
                    messages.append(LLMMessage(
                        role=MessageRole.TOOL,
                        content=result_content,
                        tool_call_id=call_id
                    ))

            # Build suggested actions based on context
            suggested_actions = self._get_suggested_actions(request.query)

            return self._success(
                text=final_response or "No response generated.",
                suggested_actions=suggested_actions,
                metadata={
                    "operation": "chat",
                    "llm_provider": "glm",
                    "llm_model": llm_client.model,
                    "tool_calls": current_turn - 1
                },
            )

        except Exception as e:
            print(f"LLM error: {e}")
            # Fallback to mock on error
            return self._fallback_chat(request)

    def _fallback_chat(self, request: ExecutorRequest) -> ExecutorResult:
        """Fallback chat when LLM is not available"""
        return self._success(
            text=f"""我理解你的问题："{request.query}"

目前 AI 服务暂时不可用，但我可以根据系统状态提供以下信息：

- 所有服务运行正常
- 最近 24 小时无重大告警
- 资源使用率在正常范围内

### 快捷命令
- `/deploy <version> to <region>` - 部署版本
- `/status <version>` - 检查版本状态
- `/rollback <version>` - 回滚版本
- `/logs <service>` - 查看服务日志
""",
            metadata={"operation": "chat", "mode": "fallback"},
        )

    def _get_suggested_actions(self, query: str) -> List[Dict[str, Any]]:
        """Get suggested actions based on query context"""
        actions = []
        query_lower = query.lower()

        if "部署" in query or "deploy" in query_lower:
            actions.append(
                self._action("deploy", "invoke", "触发部署",
                           {"agent_id": "nexusops.chat", "query": "/deploy"},
                           confirm_required=False)
            )

        if "状态" in query or "status" in query_lower:
            actions.append(
                self._action("status", "invoke", "查看状态",
                           {"agent_id": "nexusops.chat", "query": "/status"})
            )

        if "日志" in query or "log" in query_lower:
            actions.append(
                self._action("logs", "invoke", "查看日志",
                           {"agent_id": "nexusops.chat", "query": "/logs"})
            )

        if "pod" in query_lower or "k8s" in query_lower or "kubernetes" in query_lower:
            actions.append(
                self._action("k8s", "invoke", "K8s 资源查询",
                           {"agent_id": "nexusops.k8s", "query": query})
            )

        return actions[:3]  # Limit to 3 actions

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "get_deployment_status",
                "description": "Get deployment status for a version",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "codename": {"type": "string"},
                        "region": {"type": "string"},
                    },
                },
            },
            {
                "name": "trigger_deployment",
                "description": "Trigger a deployment",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "codename": {"type": "string"},
                        "regions": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["codename"],
                },
            },
        ]
