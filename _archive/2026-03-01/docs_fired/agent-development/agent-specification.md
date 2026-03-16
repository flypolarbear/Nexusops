# Agent 开发规范

本文档定义了 NexusOps Agent 的开发规范，确保所有 Agent 遵循统一的结构、接口和行为模式。

## 目录

- [概述](#概述)
- [Agent 包结构](#agent-包结构)
- [agent.yaml 规范](#agentyaml-规范)
- [Handler 实现](#handler-实现)
- [Tool 定义](#tool-定义)
- [Adapter 设计](#adapter-设计)
- [能力声明](#能力声明)
- [错误处理](#错误处理)
- [测试规范](#测试规范)
- [示例：K8s Agent](#示例k8s-agent)

---

## 概述

### 核心概念

| 概念 | 说明 |
|-----|------|
| **Agent** | 具备特定领域能力的智能代理，可被 LLM 调用 |
| **Tool** | Agent 暴露的可执行函数，供 LLM Function Calling |
| **Capability** | Agent 运行时需要的系统权限 |
| **Adapter** | 封装外部系统 API 调用的适配器层 |

### 设计原则

1. **单一职责**：每个 Agent 只负责一个领域
2. **工具化**：所有操作通过 Tool 暴露，支持 Function Calling
3. **权限最小化**：只声明必要的能力
4. **可测试性**：Handler 与 Adapter 分离，便于 Mock

---

## Agent 包结构

### 内置 Agent

```
backend/app/agents/
├── __init__.py              # 导出所有 Handler
├── base.py                  # BaseAgentHandler 基类
├── k8s/
│   ├── __init__.py
│   ├── handler.py           # Agent Handler
│   ├── tools.py             # Tool 定义
│   └── agent.yaml           # Agent Manifest
├── deploy/
│   ├── __init__.py
│   ├── handler.py
│   ├── tools.py
│   └── agent.yaml
└── ...
```

### 第三方 Agent（Market 发布）

```
thirdparty-dns-agent/
├── agent.yaml               # Agent Manifest（必需）
├── handler.py               # 入口 Handler（必需）
├── tools.py                 # Tool 定义（可选，可在 yaml 中定义）
├── adapter.py               # 外部系统适配器（可选）
├── config_schema.json       # 配置 Schema（可选）
├── README.md                # 文档
└── tests/
    ├── __init__.py
    └── test_handler.py
```

---

## agent.yaml 规范

### 完整Schema

```yaml
# agent.yaml
apiVersion: nexusops/v1
kind: Agent

# ====================元数据 ====================
metadata:
  # 必需字段
  id: string                    # 唯一 ID，格式: {namespace}.{name}
                                # 内置: nexusops.k8s
                                # 第三方: thirdparty.dns
  name: string                  # 显示名称
  version: string               # 语义版本，如 "1.0.0"
  description: string           # 简短描述（最多 200 字符）
  
  # 可选字段
  author: string                # 作者
  homepage: string              # 主页 URL
  repository: string            # 代码仓库 URL
  license: string               # 许可证
  keywords: [string]            # 搜索关键词
  icon: string                  # 图标 URL

# ==================== 规格定义 ====================
spec:
  # 入口配置
  entrypoint:
    type: enum [builtin, remote]# 入口类型
    module: string              # builtin: Python 模块路径
    url: string                 # remote: HTTP endpoint
    
  # 能力声明（权限）
  capabilities:
    - string                    # 如 k8s:read, dns:write
  
  # 配置 Schema（Agent 需要的配置）
  configSchema:
    type: object
    properties:
      field_name:
        type: string
        description: string
        required: boolean
    required: [field_name]
  
  # 工具定义
  tools:
    - name: string
      description: string
      inputSchema:
        type: object
        properties: {...}
        required: [...]
      outputSchema:              # 可选
        type: object
        properties: {...}
      dangerous: boolean         # 是否需要用户确认
      
  # 触发词（用于智能路由）
  triggers:
    keywords: [string]          # 触发关键词
    patterns: [string]          # 正则模式
```

### 示例

```yaml
apiVersion: nexusops/v1
kind: Agent

metadata:
  id: nexusops.k8s
  name: Kubernetes Agent
  version: 2.0.0
  description: Manage Kubernetes resources with real API integration
  author: NexusOps Team
  keywords: [kubernetes, k8s, pods, deployments]

spec:
  entrypoint:
    type: builtin
    module: app.agents.k8s.handler
    
  capabilities:
    - k8s:read
    - k8s:write
    
  configSchema:
    type: object
    properties:
      kubeconfig:
        type: string
        description: Path to kubeconfig file
      context:
        type: string
        description: Kubernetes context to use
        
  tools:
    - name: k8s_list_pods
      description: List pods in a namespace with optional label filtering
      inputSchema:
        type: object
        properties:
          namespace:
            type: string
            description: Kubernetes namespace
            default: default
          labels:
            type: object
            description: Label selectors, e.g. {"app": "nginx"}
      dangerous: false
      
    - name: k8s_scale_deployment
      description: Scale a deployment to specified replicas
      inputSchema:
        type: object
        properties:
          name:
            type: string
            description: Deployment name
          namespace:
            type: string
            default: default
          replicas:
            type: integer
            minimum: 0
            maximum: 100
            description: Target replica count
        required: [name, replicas]
      dangerous: false
      
    - name: k8s_delete_pod
      description: Delete a pod from the cluster
      inputSchema:
        type: object
        properties:
          name:
            type: string
            description: Pod name
          namespace:
            type: string
            default: default
          force:
            type: boolean
            default: false
            description: Force deletion without grace period
        required: [name]
      dangerous: true
      
  triggers:
    keywords: [pod, deployment, service, k8s, kubernetes, namespace]
```

---

## Handler 实现

### 基类接口

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.gateway.executor.base import ExecutorRequest, ExecutorResult

class BaseAgentHandler(ABC):
    """Agent Handler 基类"""
    
    @property
    @abstractmethod
    def agent_id(self) -> str:
        """Agent 唯一标识"""
        pass
    
    @property
    @abstractmethod
    def capabilities(self) -> List[str]:
        """Agent 能力列表"""
        pass
    
    @abstractmethod
    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        """处理请求"""
        pass
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """返回工具定义，默认从 agent.yaml 加载"""
        return []
    
    def get_manifest(self) -> Dict[str, Any]:
        """返回完整 Manifest"""
        pass
```

### 标准实现模板

```python
# handler.py

from typing import List, Dict, Any, Optional
from app.agents.base import BaseAgentHandler
from app.gateway.executor.base import ExecutorRequest, ExecutorResult
from app.adapters.base import BaseAdapter

class MyAgentHandler(BaseAgentHandler):
    """
    Agent Handler 标准实现模板
    
    职责：
    1. 解析请求中的 tool_calls
    2. 路由到对应的 Adapter 方法
    3. 格式化返回结果
    """
    
    def __init__(self):
        self._adapter: Optional[BaseAdapter] = None
    
    # ==================== 必需实现 ====================
    
    @property
    def agent_id(self) -> str:
        return "namespace.agent_name"
    
    @property
    def capabilities(self) -> List[str]:
        return ["capability:read", "capability:write"]
    
    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        """
        处理请求的主入口
        
        支持两种模式：
        1. Tool Call 模式：request.tools 包含要执行的工具
        2. 查询模式：根据 request.query 智能路由
        """
        if request.tools:
            return await self._execute_tools(request)
        return await self._handle_query(request)
    
    # ==================== 工具执行 ====================
    
    async def _execute_tools(self, request: ExecutorRequest) -> ExecutorResult:
        """执行工具调用"""
        adapter = self._get_adapter()
        results = []
        
        for tool_call in request.tools:
            tool_name = tool_call.get("name")
            params = tool_call.get("params", {})
            
            try:
                result = await self._dispatch_tool(adapter, tool_name, params)
                results.append({
                    "tool": tool_name,
                    "success": True,
                    "result": result
                })
            except Exception as e:
                results.append({
                    "tool": tool_name,
                    "success": False,
                    "error": str(e)
                })
        
        return self._format_results(results)
    
    async def _dispatch_tool(
        self, 
        adapter: BaseAdapter, 
        tool_name: str, 
        params: Dict[str, Any]
    ) -> Any:
        """路由工具到 Adapter 方法"""
        # 工具名到Adapter 方法的映射
        tool_map = {
            "prefix_action_name": adapter.action_name,
            # ... 其他映射
        }
        
        if tool_name not in tool_map:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        return await tool_map[tool_name](**params)
    
    # ==================== Adapter 管理 ====================
    
    def _get_adapter(self) -> BaseAdapter:
        """获取或创建 Adapter 实例"""
        if self._adapter is None:
            self._adapter = self._create_adapter()
        return self._adapter
    
    def _create_adapter(self) -> BaseAdapter:
        """创建 Adapter 实例，子类可重写"""
        raise NotImplementedError("Subclass must implement _create_adapter")
```

---

## Tool 定义

### Tool Schema 规范

```python
# tools.py

from typing import Dict, Any, List

def get_tool_definitions() -> List[Dict[str, Any]]:
    """
    返回工具定义列表
    
    每个工具必须包含：
    - name: 工具名称，格式 {agent_prefix}_{action}
    - description: 清晰的功能描述
    - inputSchema: JSON Schema格式的参数定义
    - dangerous: 是否需要用户确认（默认 false）
    """
    return [
        {
            "name": "k8s_list_pods",
            "description": "List pods in a namespace with optional label filtering",
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
                        "description": "Label selectors"
                    }
                }
            },
            "dangerous": False
        }
    ]
```

### Tool 命名规范

| 格式 | 示例 | 说明 |
|-----|------|------|
| `{prefix}_list_{resource}` | `k8s_list_pods` | 列表查询 |
| `{prefix}_get_{resource}` | `k8s_get_pod` | 单个查询 |
| `{prefix}_create_{resource}` | `dns_create_record` | 创建资源 |
| `{prefix}_update_{resource}` | `dns_update_record` | 更新资源 |
| `{prefix}_delete_{resource}` | `k8s_delete_pod` | 删除资源 |
| `{prefix}_{action}_{resource}` | `k8s_scale_deployment` | 特殊操作 |

---

## Adapter 设计

### 基类

```python
# app/adapters/base.py

from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAdapter(ABC):
    """
    Adapter 基类
    
    职责：
    1. 封装外部系统 API 调用
    2. 处理认证和配置
    3. 统一错误处理
    4. 返回标准化结果
    """
    
    @abstractmethod
    async def health_check(self) -> bool:
        """检查连接是否正常"""
        pass
    
    def _success(self, data: Any, message: str = "") -> Dict[str, Any]:
        """返回成功结果"""
        return {
            "success": True,
            "data": data,
            "message": message
        }
    
    def _error(self, error: str, code: str = "UNKNOWN") -> Dict[str, Any]:
        """返回错误结果"""
        return {
            "success": False,
            "error": error,
            "code": code
        }
```

### 实现模板

```python
# adapter.py

from typing import Dict, Any, Optional
from app.adapters.base import BaseAdapter

class MySystemAdapter(BaseAdapter):
    """
    外部系统适配器模板
    
    设计原则：
    1. 每个 Adapter 方法对应一个或多个 Tool
    2. 方法参数与 Tool inputSchema 一致
    3. 返回标准化的 Dict 结果
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化 Adapter
        
        Args:
            config: 配置字典，从系统配置或 agent.yaml 加载
        """
        self._config = config or {}
        self._client = None
    
    async def health_check(self) -> bool:
        """检查连接"""
        try:
            # 实现健康检查逻辑
            return True
        except Exception:
            return False
    
    def _get_client(self):
        """获取或创建 API 客户端"""
        if self._client is None:
            self._client = self._create_client()
        return self._client
    
    def _create_client(self):
        """创建 API 客户端"""
        # 实现客户端创建逻辑
        pass
    
    # ==================== 业务方法 ====================
    # 方法名与 Tool 名称对应（去掉前缀）
    
    async def list_resources(
        self,
        namespace: str = "default",
        **kwargs
    ) -> Dict[str, Any]:
        """
        列出资源
        
        Args:
            namespace: 命名空间
            **kwargs: 其他过滤参数
            
        Returns:
            标准化结果字典
        """
        try:
            client = self._get_client()
            # 调用 API
            resources = await client.list(namespace=namespace, **kwargs)
            
            return self._success({
                "items": [self._format_resource(r) for r in resources],
                "total": len(resources)
            })
        except Exception as e:
            return self._error(str(e), code="API_ERROR")
    
    def _format_resource(self, raw: Any) -> Dict[str, Any]:
        """格式化原始资源为标准格式"""
        return {
            "name": raw.name,
            "status": raw.status,
            # ... 其他字段
        }
```

---

## 能力声明

### 标准能力列表

| 能力 | 说明 | 配置要求 |
|-----|------|---------|
| `k8s:read` | 读取 K8s 资源 | kubeconfig |
| `k8s:write` | 修改 K8s 资源 | kubeconfig |
| `argocd:read` | 读取 ArgoCD 状态 | API token |
| `argocd:write` | 触发 ArgoCD 操作 | API token |
| `dns:read` | 读取 DNS 记录 | API token |
| `dns:write` | 修改 DNS 记录 | API token |
| `http:internal` | 访问内部 HTTP | - |
| `http:external` | 访问外部 HTTP | 白名单 |

### 能力粒度

```
{system}:{action}

system: k8s, argocd, dns, http, ...
action: read, write, delete, execute
```

---

## 错误处理

### 错误码规范

| 错误码 | 说明 |
|-------|------|
| `UNKNOWN` | 未知错误 |
| `INVALID_PARAMS` | 参数无效 |
| `UNAUTHORIZED` | 未授权 |
| `FORBIDDEN` | 权限不足 |
| `NOT_FOUND` | 资源不存在 |
| `API_ERROR` | 外部 API 错误 |
| `TIMEOUT` | 操作超时 |
| `RATE_LIMITED` | 请求限流 |

### 错误返回格式

```python
def _error(self, error: str, code: str = "UNKNOWN") -> Dict[str, Any]:
    return {
        "success": False,
        "error": error,
        "code": code,
        "details": {
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": self.agent_id
        }
    }
```

---

## 测试规范

### 测试文件结构

```
tests/
├── unit/
│   └── test_k8s_handler.py    # Handler 单元测试
├── integration/
│   └── test_k8s_adapter.py    # Adapter 集成测试
└── fixtures/
    └── k8s_mock_data.py       # Mock 数据
```

### Handler 测试模板

```python
# tests/unit/test_k8s_handler.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.agents.k8s.handler import K8sAgentHandler
from app.gateway.executor.base import ExecutorRequest, ExecutorContext

class TestK8sAgentHandler:
    """K8s Agent Handler 测试"""
    
    @pytest.fixture
    def handler(self):
        return K8sAgentHandler()
    
    @pytest.fixture
    def mock_adapter(self, monkeypatch):
        adapter = MagicMock()
        adapter.list_pods = AsyncMock(return_value={"success": True, "pods": []})
        return adapter
    
    def test_agent_id(self, handler):
        assert handler.agent_id == "nexusops.k8s"
    
    def test_capabilities(self, handler):
        caps = handler.capabilities
        assert "k8s:read" in caps
        assert "k8s:write" in caps
    
    @pytest.mark.asyncio
    async def test_list_pods_tool(self, handler, mock_adapter, monkeypatch):
        # Mock adapter
        monkeypatch.setattr(handler, "_get_adapter", lambda: mock_adapter)
        
        # 构造请求
        request = ExecutorRequest(
            context=ExecutorContext(
                trace_id="test",
                request_id="test",
                agent_id="nexusops.k8s"
            ),
            query="",
            tools=[{
                "name": "k8s_list_pods",
                "params": {"namespace": "default"}
            }]
        )
        
        # 执行
        result = await handler.handle(request)
        
        # 验证
        assert result.success
        mock_adapter.list_pods.assert_called_once_with(namespace="default")
```

---

## 示例：K8s Agent

### 目录结构

```
backend/app/agents/k8s/
├── __init__.py
├── handler.py           # K8sAgentHandler
├── tools.py             # Tool 定义
└── agent.yaml           # Manifest

backend/app/adapters/
├── __init__.py
├── base.py              # BaseAdapter
└── kubernetes.py        # KubernetesAdapter
```

### agent.yaml

```yaml
apiVersion: nexusops/v1
kind: Agent

metadata:
  id: nexusops.k8s
  name: Kubernetes Agent
  version: 2.0.0
  description: Manage Kubernetes resources with real API integration
  author: NexusOps Team
  keywords: [kubernetes, k8s, pods, deployments]

spec:
  entrypoint:
    type: builtin
    module: app.agents.k8s.handler
    
  capabilities:
    - k8s:read
    - k8s:write
    
  tools:
    - name: k8s_list_pods
      description: List pods in a namespace
      inputSchema:
        type: object
        properties:
          namespace: { type: string, default: default }
          labels: { type: object }
      dangerous: false
      
    - name: k8s_get_pod
      description: Get pod details
      inputSchema:
        type: object
        properties:
          name: { type: string }
          namespace: { type: string, default: default }
        required: [name]
      dangerous: false
      
    - name: k8s_list_deployments
      description: List deployments
      inputSchema:
        type: object
        properties:
          namespace: { type: string, default: default }
      dangerous: false
      
    - name: k8s_scale_deployment
      description: Scale deployment replicas
      inputSchema:
        type: object
        properties:
          name: { type: string }
          namespace: { type: string, default: default }
          replicas: { type: integer, minimum: 0, maximum: 100 }
        required: [name, replicas]
      dangerous: false
      
    - name: k8s_delete_pod
      description: Delete a pod
      inputSchema:
        type: object
        properties:
          name: { type: string }
          namespace: { type: string, default: default }
          force: { type: boolean, default: false }
        required: [name]
      dangerous: true
      
  triggers:
    keywords: [pod, deployment, service, k8s, kubernetes, namespace, replica]
```

### handler.py

```python
# app/agents/k8s/handler.py

from typing import List, Dict, Any, Optional
from app.agents.base import BaseAgentHandler
from app.gateway.executor.base import ExecutorRequest, ExecutorResult
from app.adapters.kubernetes import KubernetesAdapter


class K8sAgentHandler(BaseAgentHandler):
    """Kubernetes Agent Handler"""
    
    def __init__(self):
        self._adapter: Optional[KubernetesAdapter] = None
    
    @property
    def agent_id(self) -> str:
        return "nexusops.k8s"
    
    @property
    def capabilities(self) -> List[str]:
        return ["k8s:read", "k8s:write"]
    
    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        """处理请求"""
        if request.tools:
            return await self._execute_tools(request)
        return self._list_tools_help()
    
    async def _execute_tools(self, request: ExecutorRequest) -> ExecutorResult:
        """执行工具调用"""
        adapter = self._get_adapter()
        results = []
        
        for tool_call in request.tools:
            tool_name = tool_call.get("name")
            params = tool_call.get("params", {})
            
            try:
                result = await self._dispatch_tool(adapter, tool_name, params)
                results.append({
                    "tool": tool_name,
                    "success": True,
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
        """工具路由"""
        tool_map = {
            "k8s_list_pods": adapter.list_pods,
            "k8s_get_pod": adapter.get_pod,
            "k8s_list_deployments": adapter.list_deployments,
            "k8s_scale_deployment": adapter.scale_deployment,
            "k8s_delete_pod": adapter.delete_pod,
        }
        
        if tool_name not in tool_map:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        return await tool_map[tool_name](**params)
    
    def _get_adapter(self) -> KubernetesAdapter:
        if self._adapter is None:
            self._adapter = KubernetesAdapter()
        return self._adapter
    
    def _format_tool_results(self, results: List[Dict]) -> ExecutorResult:
        """格式化工具执行结果"""
        all_success = all(r["success"] for r in results)
        
        # 生成摘要文本
        summary_parts = []
        for r in results:
            if r["success"]:
                data = r["result"]
                if "pods" in data:
                    summary_parts.append(f"Found {len(data['pods'])} pods")
                elif "deployments" in data:
                    summary_parts.append(f"Found {len(data['deployments'])} deployments")
                elif "message" in data:
                    summary_parts.append(data["message"])
            else:
                summary_parts.append(f"Error in {r['tool']}: {r['error']}")
        
        return self._success(
            text="\n".join(summary_parts),
            structured_output={
                "type": "tool_execution_results",
                "results": results
            },
            metadata={"tool_count": len(results)}
        )
    
    def _list_tools_help(self) -> ExecutorResult:
        """返回工具列表帮助"""
        return self._success(
            text="""## Kubernetes Agent

Available tools:
- `k8s_list_pods` - List pods in a namespace
- `k8s_get_pod` - Get pod details
- `k8s_list_deployments` - List deployments
- `k8s_scale_deployment` - Scale a deployment
- `k8s_delete_pod` - Delete a pod (requires confirmation)

Example usage via Chat Agent:
"List all pods in production namespace"
"Scale api-gateway to 5 replicas"
"""
        )
```

### adapter.py

```python
# app/adapters/kubernetes.py

from typing import Dict, Any, List, Optional
from datetime import datetime
from kubernetes import client, config
from kubernetes.client import ApiException

from app.adapters.base import BaseAdapter


class KubernetesAdapter(BaseAdapter):
    """Kubernetes API 适配器"""
    
    def __init__(self, kubeconfig_path: Optional[str] = None, context: Optional[str] = None):
        self._kubeconfig_path = kubeconfig_path
        self._context = context
        self._core_v1 = None
        self._apps_v1 = None
        self._initialize_client()
    
    def _initialize_client(self):
        """初始化 K8s 客户端"""
        try:
            if self._kubeconfig_path:
                config.load_kube_config(
                    config_file=self._kubeconfig_path,
                    context=self._context
                )
            else:
                try:
                    config.load_incluster_config()
                except:
                    config.load_kube_config(context=self._context)
            
            self._core_v1 = client.CoreV1Api()
            self._apps_v1 = client.AppsV1Api()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Kubernetes client: {e}")
    
    async def health_check(self) -> bool:
        """检查连接"""
        try:
            self._core_v1.list_namespace(limit=1)
            return True
        except Exception:
            return False
    
    # ==================== Pod 操作 ====================
    
    async def list_pods(
        self,
        namespace: str = "default",
        labels: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """列出 Pods"""
        try:
            label_selector = None
            if labels:
                label_selector = ",".join(f"{k}={v}" for k, v in labels.items())
            
            pods = self._core_v1.list_namespaced_pod(
                namespace=namespace,
                label_selector=label_selector
            )
            
            return self._success({
                "pods": [self._format_pod(p) for p in pods.items],
                "namespace": namespace,
                "total": len(pods.items)
            })
        except ApiException as e:
            return self._error(f"K8s API error: {e.reason}", code="API_ERROR")
    
    async def get_pod(self, name: str, namespace: str = "default") -> Dict[str, Any]:
        """获取 Pod 详情"""
        try:
            pod = self._core_v1.read_namespaced_pod(name, namespace)
            return self._success({
                "pod": self._format_pod_detail(pod),
                "namespace": namespace
            })
        except ApiException as e:
            if e.status == 404:
                return self._error(f"Pod not found: {name}", code="NOT_FOUND")
            return self._error(f"K8s API error: {e.reason}", code="API_ERROR")
    
    async def delete_pod(
        self,
        name: str,
        namespace: str = "default",
        force: bool = False
    ) -> Dict[str, Any]:
        """删除 Pod"""
        try:
            grace_period = 0 if force else None
            self._core_v1.delete_namespaced_pod(
                name=name,
                namespace=namespace,
                grace_period_seconds=grace_period
            )
            return self._success({
                "message": f"Pod {name} deleted from {namespace}",
                "name": name,
                "namespace": namespace
            })
        except ApiException as e:
            if e.status == 404:
                return self._error(f"Pod not found: {name}", code="NOT_FOUND")
            return self._error(f"K8s API error: {e.reason}", code="API_ERROR")
    
    # ==================== Deployment 操作 ====================
    
    async def list_deployments(self, namespace: str = "default") -> Dict[str, Any]:
        """列出 Deployments"""
        try:
            deployments = self._apps_v1.list_namespaced_deployment(namespace)
            
            return self._success({
                "deployments": [self._format_deployment(d) for d in deployments.items],
                "namespace": namespace,
                "total": len(deployments.items)
            })
        except ApiException as e:
            return self._error(f"K8s API error: {e.reason}", code="API_ERROR")
    
    async def scale_deployment(
        self,
        name: str,
        replicas: int,
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """扩缩容 Deployment"""
        try:
            # 获取当前状态
            deployment = self._apps_v1.read_namespaced_deployment(name, namespace)
            old_replicas = deployment.spec.replicas
            
            # 更新副本数
            deployment.spec.replicas = replicas
            self._apps_v1.patch_namespaced_deployment(name, namespace, deployment)
            
            return self._success({
                "name": name,
                "namespace": namespace,
                "old_replicas": old_replicas,
                "new_replicas": replicas,
                "message": f"Scaled {name} from {old_replicas} to {replicas} replicas"
            })
        except ApiException as e:
            if e.status == 404:
                return self._error(f"Deployment not found: {name}", code="NOT_FOUND")
            return self._error(f"K8s API error: {e.reason}", code="API_ERROR")
    
    # ==================== 格式化方法 ====================
    
    def _format_pod(self, pod) -> Dict[str, Any]:
        """格式化 Pod 简要信息"""
        return {
            "name": pod.metadata.name,
            "namespace": pod.metadata.namespace,
            "status": pod.status.phase,
            "ready": self._get_ready_status(pod),
            "restarts": self._get_restart_count(pod),
            "age": self._get_age(pod.metadata.creation_timestamp),
            "ip": pod.status.pod_ip,
        }
    
    def _format_pod_detail(self, pod) -> Dict[str, Any]:
        """格式化 Pod 详细信息"""
        return {
            **self._format_pod(pod),
            "labels": pod.metadata.labels or {},
            "annotations": pod.metadata.annotations or {},
            "containers": [
                {
                    "name": c.name,
                    "image": c.image,
                    "ports": [p.container_port for p in (c.ports or [])],
                }
                for c in pod.spec.containers
            ],
            "node": pod.spec.node_name,
        }
    
    def _format_deployment(self, deployment) -> Dict[str, Any]:
        """格式化 Deployment 信息"""
        return {
            "name": deployment.metadata.name,
            "namespace": deployment.metadata.namespace,
            "replicas": deployment.spec.replicas,
            "ready": deployment.status.ready_replicas or 0,
            "available": deployment.status.available_replicas or 0,
            "age": self._get_age(deployment.metadata.creation_timestamp),
        }
    
    # ==================== 工具方法 ====================
    
    def _get_ready_status(self, pod) -> str:
        """获取 Pod Ready 状态"""
        if not pod.status.container_statuses:
            return "0/0"
        ready = sum(1 for c in pod.status.container_statuses if c.ready)
        total = len(pod.status.container_statuses)
        return f"{ready}/{total}"
    
    def _get_restart_count(self, pod) -> int:
        """获取重启次数"""
        if not pod.status.container_statuses:
            return 0
        return sum(c.restart_count for c in pod.status.container_statuses)
    
    def _get_age(self, creation_timestamp) -> str:
        """计算资源年龄"""
        if not creation_timestamp:
            return "unknown"
        age = datetime.utcnow() - creation_timestamp.replace(tzinfo=None)
        if age.days > 0:
            return f"{age.days}d"
        hours = age.seconds // 3600
        if hours > 0:
            return f"{hours}h"
        minutes = (age.seconds % 3600) // 60
        return f"{minutes}m"
```

---

## 附录

### A. 文件模板生成

```bash
# 创建新 Agent
python scripts/create_agent.py --name dns --namespace thirdparty
```

### B. 相关文档

- [Agent Contract Specification](./contract-specification.md)
- [Agent Lifecycle](./agent-lifecycle.md)
- [Testing Guide](./testing-guide.md)
