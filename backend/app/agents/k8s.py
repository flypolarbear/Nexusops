"""
NexusOps Agents - K8s Agent Handler

nexusops.k8s: Kubernetes 资源管理、部署操作
"""

import asyncio
from typing import List, Dict, Any

from app.agents.base import BaseAgentHandler
from app.gateway.executor.base import ExecutorRequest, ExecutorResult


class K8sAgentHandler(BaseAgentHandler):
    """Kubernetes agent handler for K8s operations"""

    @property
    def agent_id(self) -> str:
        return "nexusops.k8s"

    @property
    def capabilities(self) -> List[str]:
        return ["k8s_deploy", "k8s_scale", "k8s_logs", "k8s_describe", "k8s_diagnose"]

    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        """Handle K8s requests"""
        await asyncio.sleep(0.3)

        query = request.query.lower()
        context = request.request_context

        if "logs" in query or "日志" in query:
            return self._get_logs(context)
        elif "describe" in query or "详情" in query:
            return self._describe_resource(context)
        elif "scale" in query or "扩缩容" in query:
            return self._scale_resource(context)
        elif "diagnose" in query or "诊断" in query:
            return self._diagnose(context)
        else:
            return self._query_status(context)

    def _get_logs(self, context: Dict[str, Any]) -> ExecutorResult:
        """Get pod logs"""
        pod_name = context.get("resource_name", "unknown")
        namespace = context.get("namespace", "default")

        return self._success(
            text=f"""## 📋 Pod Logs

**Pod:** {pod_name}
**Namespace:** {namespace}

```
2026-02-25 00:00:01 INFO  Starting application...
2026-02-25 00:00:02 INFO  Loading configuration
2026-02-25 00:00:03 INFO  Connecting to services
2026-02-25 00:00:05 INFO  Application started successfully
2026-02-25 00:00:10 INFO  Health check passed
```
""",
            structured_output={
                "type": "pod_logs",
                "pod_name": pod_name,
                "namespace": namespace,
                "lines": 100,
            },
            suggested_actions=[
                self._action("view-full", "invoke", "View Full Logs",
                           {"agent_id": "nexusops.k8s", "query": f"logs {pod_name} --tail 1000"}),
            ],
            metadata={"operation": "get_logs"},
        )

    def _describe_resource(self, context: Dict[str, Any]) -> ExecutorResult:
        """Describe a K8s resource"""
        resource_type = context.get("resource_type", "Pod")
        resource_name = context.get("resource_name", "unknown")
        namespace = context.get("namespace", "default")

        return self._success(
            text=f"""## 📋 Resource Description

**Type:** {resource_type}
**Name:** {resource_name}
**Namespace:** {namespace}

### Status
- **Phase:** Running
- **Ready:** 1/1
- **Restarts:** 0

### Metrics
- CPU: 250m / 500m (50%)
- Memory: 384Mi / 512Mi (75%)

### Labels
- app: {resource_name}
- version: v1.0.0

### No issues detected
""",
            structured_output={
                "type": "resource_description",
                "resource_type": resource_type,
                "resource_name": resource_name,
                "namespace": namespace,
                "status": "running",
                "health": "healthy",
            },
            metadata={"operation": "describe"},
        )

    def _scale_resource(self, context: Dict[str, Any]) -> ExecutorResult:
        """Scale a deployment"""
        resource_name = context.get("resource_name", "unknown")

        return self._success(
            text=f"""## 🔄 Scaling Operation

**Deployment:** {resource_name}

Scaling from 2 to 3 replicas...

✅ New replica created successfully
✅ Health check passed

Current replicas: 3/3 ready
""",
            structured_output={
                "type": "scale_result",
                "resource_name": resource_name,
                "replicas": 3,
                "ready": 3,
            },
            metadata={"operation": "scale"},
        )

    def _diagnose(self, context: Dict[str, Any]) -> ExecutorResult:
        """Run K8s diagnosis"""
        resource_name = context.get("resource_name", "unknown")

        return self._success(
            text=f"""## 🔍 K8s Diagnosis

**Resource:** {resource_name}

### Diagnosis Results
- ✅ Pod scheduling: OK
- ✅ Resource limits: Within bounds
- ✅ Network connectivity: OK
- ✅ Volume mounts: OK
- ✅ Health probes: Passing

### No issues detected

The resource is healthy and operating normally.
""",
            structured_output={
                "type": "diagnosis_result",
                "resource_name": resource_name,
                "issues": [],
                "healthy": True,
            },
            metadata={"operation": "diagnose"},
        )

    def _query_status(self, context: Dict[str, Any]) -> ExecutorResult:
        """Query K8s status"""
        return self._success(
            text="""## 📊 K8s Status

All resources are healthy.

### Summary
| Resource Type | Total | Healthy | Warning | Error |
|--------------|-------|---------|---------|-------|
| Pods         | 24    | 24      | 0       | 0     |
| Deployments  | 8     | 8       | 0       | 0     |
| Services     | 12    | 12      | 0       | 0     |

### Resource Usage
- CPU: 45% utilized
- Memory: 62% utilized
- Storage: 35% utilized
""",
            metadata={"operation": "status"},
        )

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "get_pod_logs",
                "description": "Get logs from a pod",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pod_name": {"type": "string"},
                        "namespace": {"type": "string", "default": "default"},
                        "tail_lines": {"type": "integer", "default": 100},
                    },
                    "required": ["pod_name"],
                },
            },
            {
                "name": "describe_resource",
                "description": "Describe a Kubernetes resource",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "resource_type": {"type": "string"},
                        "name": {"type": "string"},
                        "namespace": {"type": "string", "default": "default"},
                    },
                    "required": ["resource_type", "name"],
                },
            },
            {
                "name": "scale_deployment",
                "description": "Scale a deployment",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "namespace": {"type": "string", "default": "default"},
                        "replicas": {"type": "integer"},
                    },
                    "required": ["name", "replicas"],
                },
            },
        ]
