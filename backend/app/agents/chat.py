"""
NexusOps Agents - Chat Agent Handler

nexusops.chat: 通用 AI 助手，支持快捷命令
"""

import asyncio
from typing import List, Dict, Any

from app.agents.base import BaseAgentHandler
from app.gateway.executor.base import ExecutorRequest, ExecutorResult


class ChatAgentHandler(BaseAgentHandler):
    """Chat agent handler for general conversations and quick commands"""

    @property
    def agent_id(self) -> str:
        return "nexusops.chat"

    @property
    def capabilities(self) -> List[str]:
        return ["chat", "quick_commands", "deployment_info", "status_query"]

    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        """Handle chat requests"""
        # Simulate processing delay
        await asyncio.sleep(0.2)

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
            return self._handle_general_chat(request)

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
2026-2025 00:00:03 INFO  Service ready on port 8080
...
```
""",
            suggested_actions=[
                self._action("full-logs", "invoke", "View Full Logs",
                           {"agent_id": "nexusops.logs", "query": f"logs {service} --tail 1000"}),
            ],
            metadata={"operation": "logs"},
        )

    def _handle_general_chat(self, request: ExecutorRequest) -> ExecutorResult:
        """Handle general chat"""
        return self._success(
            text=f"""I understand you're asking: "{request.query}"

Based on the current system state, here's what I found:

- All services are operational
- No critical incidents in the last 24 hours
- Resource utilization is within expected ranges

Is there anything specific you'd like me to help with?

### Quick Commands
- `/deploy <version> to <region>` - Deploy a version
- `/status <version>` - Check version status
- `/rollback <version>` - Rollback a version
- `/logs <service>` - View service logs
""",
            metadata={"operation": "chat"},
        )

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
