"""
NexusOps K8s Agent - Handler

Kubernetes resource management with real API integration.
"""

from typing import List, Dict, Any, Optional

from app.agents.base import BaseAgentHandler
from app.gateway.executor.base import ExecutorRequest, ExecutorResult
from app.adapters.kubernetes import KubernetesAdapter


class K8sAgentHandler(BaseAgentHandler):
    """
    Kubernetes Agent Handler.
    
    Provides K8s resource management through tool-based operations.
    All operations are executed via the KubernetesAdapter.
    """
    
    def __init__(self):
        self._adapter: Optional[KubernetesAdapter] = None
    
    # ============================================================
    # Required Properties
    # ============================================================
    
    @property
    def agent_id(self) -> str:
        return "nexusops.k8s"
    
    @property
    def capabilities(self) -> List[str]:
        return ["k8s:read", "k8s:write"]
    
    # ============================================================
    # Main Handler
    # ============================================================
    
    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        """
        Handle K8s requests.
        
        Supports two modes:
        1. Tool Call mode: request.tools contains tools to execute
        2. Query mode: returns available tools help
        """
        if request.tools:
            return await self._execute_tools(request)
        return self._get_tools_help()
    
    # ============================================================
    # Tool Execution
    # ============================================================
    
    async def _execute_tools(self, request: ExecutorRequest) -> ExecutorResult:
        """Execute requested tools"""
        adapter = self._get_adapter()
        results = []
        
        for tool_call in request.tools:
            tool_name = tool_call.get("name")
            params = tool_call.get("params", {})
            
            try:
                result = await self._dispatch_tool(adapter, tool_name, params)
                results.append({
                    "tool": tool_name,
                    "success": result.get("success", False),
                    "result": result
                })
            except Exception as e:
                results.append({
                    "tool": tool_name,
                    "success": False,
                    "error": str(e)
                })
        
        return self._format_tool_results(results)
    
    async def _dispatch_tool(
        self,
        adapter: KubernetesAdapter,
        tool_name: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Dispatch tool to adapter method"""
        
        # Tool name to adapter method mapping
        tool_map = {
            # Pod operations
            "k8s_list_pods": adapter.list_pods,
            "k8s_get_pod": adapter.get_pod,
            "k8s_delete_pod": adapter.delete_pod,
            "k8s_get_pod_logs": adapter.get_pod_logs,
            # Deployment operations
            "k8s_list_deployments": adapter.list_deployments,
            "k8s_get_deployment": adapter.get_deployment,
            "k8s_scale_deployment": adapter.scale_deployment,
            # Namespace operations
            "k8s_list_namespaces": adapter.list_namespaces,
            # Service operations
            "k8s_list_services": adapter.list_services,
            "k8s_get_service": adapter.get_service,
            # Ingress operations
            "k8s_list_ingresses": adapter.list_ingresses,
        }
        
        if tool_name not in tool_map:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        return await tool_map[tool_name](**params)
    
    # ============================================================
    # Result Formatting
    # ============================================================
    
    def _format_tool_results(self, results: List[Dict]) -> ExecutorResult:
        """Format tool execution results into ExecutorResult"""
        all_success = all(r["success"] for r in results)
        
        # Generate summary text
        summary_parts = []
        for r in results:
            if r["success"]:
                result = r["result"]
                summary_parts.append(self._format_success_summary(r["tool"], result))
            else:
                error = r.get("error", "Unknown error")
                summary_parts.append(f"❌ **{r['tool']}**: {error}")
        
        summary_text = "\n\n".join(summary_parts)
        
        return self._success(
            text=summary_text,
            structured_output={
                "type": "tool_execution_results",
                "results": results,
                "total": len(results),
                "success_count": sum(1 for r in results if r["success"])
            },
            metadata={
                "tool_count": len(results),
                "all_success": all_success
            }
        )
    
    def _format_success_summary(self, tool_name: str, result: Dict) -> str:
        """Format success result summary"""
        if "pods" in result:
            pods = result["pods"]
            if not pods:
                return f"## 📋 {tool_name}\n\nNo pods found in namespace `{result.get('namespace', 'default')}`"
            
            lines = [f"## 📋 {tool_name}\n"]
            lines.append(f"Found **{len(pods)}** pods in `{result.get('namespace', 'default')}`:\n")
            for pod in pods[:10]:  # Limit to 10
                status_icon = "🟢" if pod["status"] == "Running" else "🔴"
                lines.append(f"- {status_icon} `{pod['name']}` - {pod['status']} ({pod['ready']})")
            if len(pods) > 10:
                lines.append(f"\n_... and {len(pods) - 10} more_")
            return "\n".join(lines)
        
        elif "deployments" in result:
            deployments = result["deployments"]
            if not deployments:
                return f"## 📋 {tool_name}\n\nNo deployments found in namespace `{result.get('namespace', 'default')}`"
            
            lines = [f"## 📋 {tool_name}\n"]
            lines.append(f"Found **{len(deployments)}** deployments:\n")
            for dep in deployments[:10]:
                ready_icon = "🟢" if dep["ready"] == dep["replicas"] else "🟡"
                lines.append(f"- {ready_icon} `{dep['name']}` - {dep['ready']}/{dep['replicas']} ready")
            if len(deployments) > 10:
                lines.append(f"\n_... and {len(deployments) - 10} more_")
            return "\n".join(lines)
        
        elif "namespaces" in result:
            namespaces = result["namespaces"]
            lines = [f"## 📋 {tool_name}\n"]
            lines.append(f"Found **{len(namespaces)}** namespaces:\n")
            for ns in namespaces:
                status_icon = "🟢" if ns["status"] == "Active" else "🔴"
                lines.append(f"- {status_icon} `{ns['name']}` - {ns['status']}")
            return "\n".join(lines)
        
        elif "services" in result:
            services = result["services"]
            if not services:
                return f"## 📋 {tool_name}\n\nNo services found in namespace `{result.get('namespace', 'default')}`"
            
            lines = [f"## 📋 {tool_name}\n"]
            lines.append(f"Found **{len(services)}** services:\n")
            for svc in services[:10]:
                svc_type = svc.get('type', 'ClusterIP')
                cluster_ip = svc.get('cluster_ip', 'N/A')
                lines.append(f"- `{svc['name']}` - **{svc_type}** ({cluster_ip})")
                # Show access URLs if available
                if svc.get('access_urls'):
                    for url in svc['access_urls'][:2]:  # Limit to 2 URLs
                        lines.append(f"  - 🔗 {url}")
            if len(services) > 10:
                lines.append(f"\n_... and {len(services) - 10} more_")
            return "\n".join(lines)
        
        elif "service" in result:
            # Single service detail
            svc = result["service"]
            lines = [f"## 📋 Service: `{svc['name']}`\n"]
            lines.append(f"- **Namespace**: {svc.get('namespace', 'default')}")
            lines.append(f"- **Type**: {svc.get('type', 'ClusterIP')}")
            lines.append(f"- **Cluster IP**: {svc.get('cluster_ip', 'N/A')}")
            
            # Ports
            if svc.get('ports'):
                lines.append(f"\n**Ports:**")
                for p in svc['ports']:
                    port_str = f"- {p.get('port', '?')} -> {p.get('target_port', '?')} ({p.get('protocol', 'TCP')})"
                    if p.get('node_port'):
                        port_str += f" [NodePort: {p['node_port']}]"
                    lines.append(port_str)
            
            # External IPs
            if svc.get('external_ips'):
                lines.append(f"\n**External IPs:**")
                for ip in svc['external_ips']:
                    lines.append(f"- {ip}")
            
            # Access URLs
            if svc.get('access_urls'):
                lines.append(f"\n**Access URLs:**")
                for url in svc['access_urls']:
                    lines.append(f"- 🔗 {url}")
            
            return "\n".join(lines)
        
        elif "ingresses" in result:
            ingresses = result["ingresses"]
            if not ingresses:
                return f"## 📋 {tool_name}\n\nNo ingresses found in namespace `{result.get('namespace', 'default')}`"
            
            lines = [f"## 📋 {tool_name}\n"]
            lines.append(f"Found **{len(ingresses)}** ingresses:\n")
            for ing in ingresses[:10]:
                lines.append(f"- `{ing['name']}`")
                if ing.get('hosts'):
                    lines.append(f"  - Hosts: {', '.join(ing['hosts'])}")
                if ing.get('access_urls'):
                    for url in ing['access_urls'][:2]:
                        lines.append(f"  - 🔗 {url}")
            if len(ingresses) > 10:
                lines.append(f"\n_... and {len(ingresses) - 10} more_")
            return "\n".join(lines)
        
        elif "pod" in result:
            pod = result["pod"]
            lines = [f"## 📋 Pod Details: `{pod['name']}`\n"]
            lines.append(f"- **Status**: {pod['status']}")
            lines.append(f"- **Ready**: {pod['ready']}")
            lines.append(f"- **Restarts**: {pod.get('restarts', 0)}")
            lines.append(f"- **Node**: {pod.get('node', 'N/A')}")
            lines.append(f"- **IP**: {pod.get('ip', 'N/A')}")
            lines.append(f"- **Age**: {pod.get('age', 'unknown')}")
            if pod.get("containers"):
                lines.append(f"\n**Containers:**")
                for c in pod["containers"]:
                    lines.append(f"- `{c['name']}`: {c['image']}")
            return "\n".join(lines)
        
        elif "deployment" in result:
            dep = result["deployment"]
            lines = [f"## 📋 Deployment Details: `{dep['name']}`\n"]
            lines.append(f"- **Replicas**: {dep['ready']}/{dep['replicas']} ready")
            lines.append(f"- **Available**: {dep.get('available', 0)}")
            lines.append(f"- **Updated**: {dep.get('updated', 0)}")
            lines.append(f"- **Age**: {dep.get('age', 'unknown')}")
            if dep.get("containers"):
                lines.append(f"\n**Containers:**")
                for c in dep["containers"]:
                    lines.append(f"- `{c['name']}`: {c['image']}")
            return "\n".join(lines)
        
        elif "logs" in result:
            logs = result["logs"]
            lines = [f"## 📋 Logs: `{result.get('name')}`\n"]
            lines.append(f"Last **{result.get('tail_lines', 100)}** lines:\n")
            lines.append("```")
            lines.append(logs[:2000])  # Limit log output
            if len(logs) > 2000:
                lines.append("\n... (truncated)")
            lines.append("```")
            return "\n".join(lines)
        
        elif "message" in result:
            return f"## ✅ {tool_name}\n\n{result['message']}"
        
        else:
            return f"## ✅ {tool_name}\n\nOperation completed successfully."
    
    # ============================================================
    # Adapter Management
    # ============================================================
    
    def _get_adapter(self) -> KubernetesAdapter:
        """Get or create Kubernetes adapter"""
        if self._adapter is None:
            self._adapter = KubernetesAdapter()
        return self._adapter
    
    # ============================================================
    # Help
    # ============================================================
    
    def _get_tools_help(self) -> ExecutorResult:
        """Return available tools help"""
        return self._success(
            text="""## Kubernetes Agent

Available tools for managing Kubernetes resources:

### Pod Operations
- `k8s_list_pods` - List pods in a namespace
- `k8s_get_pod` - Get detailed pod information
- `k8s_delete_pod` - Delete a pod (requires confirmation)
- `k8s_get_pod_logs` - Get pod logs

### Deployment Operations
- `k8s_list_deployments` - List deployments
- `k8s_get_deployment` - Get deployment details
- `k8s_scale_deployment` - Scale deployment replicas

### Namespace Operations
- `k8s_list_namespaces` - List all namespaces

### Service Operations
- `k8s_list_services` - List services in a namespace with access URLs
- `k8s_get_service` - Get detailed service info including access URLs

### Ingress Operations
- `k8s_list_ingresses` - List ingresses with hosts and URLs

### Example Queries
- "List all pods in production namespace"
- "Get details of pod api-gateway-xxx"
- "Scale api-gateway deployment to 5 replicas"
- "Show logs from worker pod"
- "List all ingresses"""
        )
    
    # ============================================================
    # Tool Definitions
    # ============================================================
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Return tool definitions for Function Calling"""
        return [
            {
                "name": "k8s_list_pods",
                "description": "List pods in a Kubernetes namespace with optional label filtering",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "namespace": {
                            "type": "string",
                            "description": "Kubernetes namespace",
                            "default": "default"
                        },
                        "labels": {
                            "type": "object",
                            "description": "Label selectors, e.g. {\"app\": \"nginx\"}"
                        }
                    }
                },
                "dangerous": False
            },
            {
                "name": "k8s_get_pod",
                "description": "Get detailed information about a specific pod",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Pod name"
                        },
                        "namespace": {
                            "type": "string",
                            "description": "Kubernetes namespace",
                            "default": "default"
                        }
                    },
                    "required": ["name"]
                },
                "dangerous": False
            },
            {
                "name": "k8s_delete_pod",
                "description": "Delete a pod from the cluster",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Pod name"
                        },
                        "namespace": {
                            "type": "string",
                            "description": "Kubernetes namespace",
                            "default": "default"
                        },
                        "force": {
                            "type": "boolean",
                            "description": "Force deletion without grace period",
                            "default": False
                        }
                    },
                    "required": ["name"]
                },
                "dangerous": True
            },
            {
                "name": "k8s_get_pod_logs",
                "description": "Get logs from a pod",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Pod name"
                        },
                        "namespace": {
                            "type": "string",
                            "description": "Kubernetes namespace",
                            "default": "default"
                        },
                        "tail_lines": {
                            "type": "integer",
                            "description": "Number of lines to return",
                            "default": 100
                        },
                        "container": {
                            "type": "string",
                            "description": "Container name for multi-container pods"
                        }
                    },
                    "required": ["name"]
                },
                "dangerous": False
            },
            {
                "name": "k8s_list_deployments",
                "description": "List deployments in a namespace",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "namespace": {
                            "type": "string",
                            "description": "Kubernetes namespace",
                            "default": "default"
                        }
                    }
                },
                "dangerous": False
            },
            {
                "name": "k8s_get_deployment",
                "description": "Get detailed deployment information",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Deployment name"
                        },
                        "namespace": {
                            "type": "string",
                            "description": "Kubernetes namespace",
                            "default": "default"
                        }
                    },
                    "required": ["name"]
                },
                "dangerous": False
            },
            {
                "name": "k8s_scale_deployment",
                "description": "Scale a deployment to specified replicas",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Deployment name"
                        },
                        "namespace": {
                            "type": "string",
                            "description": "Kubernetes namespace",
                            "default": "default"
                        },
                        "replicas": {
                            "type": "integer",
                            "description": "Target replica count",
                            "minimum": 0,
                            "maximum": 100
                        }
                    },
                    "required": ["name", "replicas"]
                },
                "dangerous": False
            },
            {
                "name": "k8s_list_namespaces",
                "description": "List all Kubernetes namespaces",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                },
                "dangerous": False
            },
            {
                "name": "k8s_list_services",
                "description": "List services in a namespace",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "namespace": {
                            "type": "string",
                            "description": "Kubernetes namespace",
                            "default": "default"
                        }
                    }
                },
                "dangerous": False
            },
            {
                "name": "k8s_get_service",
                "description": "Get detailed service information including access URLs and external IPs",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Service name"
                        },
                        "namespace": {
                            "type": "string",
                            "description": "Kubernetes namespace",
                            "default": "default"
                        }
                    },
                    "required": ["name"]
                },
                "dangerous": False
            },
            {
                "name": "k8s_list_ingresses",
                "description": "List ingresses in a namespace with hosts and access URLs",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "namespace": {
                            "type": "string",
                            "description": "Kubernetes namespace",
                            "default": "default"
                        }
                    }
                },
                "dangerous": False
            }
        ]
