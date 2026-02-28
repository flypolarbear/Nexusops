"""
Unit tests for K8s Agent Handler

Tests the handler logic without actual Kubernetes API calls.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.k8s.handler import K8sAgentHandler
from app.gateway.executor.base import ExecutorRequest, ExecutorContext


class TestK8sAgentHandler:
    """K8s Agent Handler unit tests"""
    
    @pytest.fixture
    def handler(self):
        return K8sAgentHandler()
    
    @pytest.fixture
    def mock_adapter(self):
        """Create mock Kubernetes adapter"""
        adapter = MagicMock()
        adapter.list_pods = AsyncMock(return_value={
            "success": True,
            "pods": [
                {"name": "pod-1", "status": "Running", "ready": "1/1"},
                {"name": "pod-2", "status": "Running", "ready": "1/1"},
            ],
            "namespace": "default",
            "total": 2
        })
        adapter.get_pod = AsyncMock(return_value={
            "success": True,
            "pod": {
                "name": "test-pod",
                "status": "Running",
                "ready": "1/1",
                "namespace": "default"
            }
        })
        adapter.list_deployments = AsyncMock(return_value={
            "success": True,
            "deployments": [
                {"name": "dep-1", "replicas": 3, "ready": 3},
            ],
            "namespace": "default",
            "total": 1
        })
        adapter.scale_deployment = AsyncMock(return_value={
            "success": True,
            "name": "test-dep",
            "old_replicas": 2,
            "new_replicas": 5,
            "message": "Scaled test-dep from 2 to 5 replicas"
        })
        adapter.delete_pod = AsyncMock(return_value={
            "success": True,
            "message": "Pod test-pod deleted",
            "name": "test-pod",
            "namespace": "default"
        })
        return adapter
    
    def make_request(self, tools=None, query=""):
        """Helper to create ExecutorRequest"""
        return ExecutorRequest(
            context=ExecutorContext(
                trace_id="test-trace",
                request_id="test-request",
                agent_id="nexusops.k8s"
            ),
            query=query,
            tools=tools or []
        )
    
    # ==================== Basic Properties ====================
    
    def test_agent_id(self, handler):
        assert handler.agent_id == "nexusops.k8s"
    
    def test_capabilities(self, handler):
        caps = handler.capabilities
        assert "k8s:read" in caps
        assert "k8s:write" in caps
    
    def test_tools_count(self, handler):
        tools = handler.get_tools()
        assert len(tools) == 11
    
    def test_tool_names(self, handler):
        tools = handler.get_tools()
        tool_names = {t["name"] for t in tools}
        expected = {
            "k8s_list_pods",
            "k8s_get_pod",
            "k8s_delete_pod",
            "k8s_get_pod_logs",
            "k8s_list_deployments",
            "k8s_get_deployment",
            "k8s_scale_deployment",
            "k8s_list_namespaces",
            "k8s_list_services",
            "k8s_get_service",
            "k8s_list_ingresses",
        }
        assert tool_names == expected
    
    def test_dangerous_tools_marked(self, handler):
        tools = handler.get_tools()
        dangerous = [t for t in tools if t.get("dangerous")]
        assert len(dangerous) == 1
        assert dangerous[0]["name"] == "k8s_delete_pod"
    
    # ==================== Tool Execution ====================
    
    @pytest.mark.asyncio
    async def test_list_pods_tool(self, handler, mock_adapter, monkeypatch):
        monkeypatch.setattr(handler, "_get_adapter", lambda: mock_adapter)
        
        request = self.make_request(tools=[{
            "name": "k8s_list_pods",
            "params": {"namespace": "default"}
        }])
        
        result = await handler.handle(request)
        
        assert result.success
        mock_adapter.list_pods.assert_called_once_with(namespace="default")
    
    @pytest.mark.asyncio
    async def test_get_pod_tool(self, handler, mock_adapter, monkeypatch):
        monkeypatch.setattr(handler, "_get_adapter", lambda: mock_adapter)
        
        request = self.make_request(tools=[{
            "name": "k8s_get_pod",
            "params": {"name": "test-pod", "namespace": "default"}
        }])
        
        result = await handler.handle(request)
        
        assert result.success
        mock_adapter.get_pod.assert_called_once_with(name="test-pod", namespace="default")
    
    @pytest.mark.asyncio
    async def test_scale_deployment_tool(self, handler, mock_adapter, monkeypatch):
        monkeypatch.setattr(handler, "_get_adapter", lambda: mock_adapter)
        
        request = self.make_request(tools=[{
            "name": "k8s_scale_deployment",
            "params": {"name": "test-dep", "replicas": 5}
        }])
        
        result = await handler.handle(request)
        
        assert result.success
        mock_adapter.scale_deployment.assert_called_once_with(
            name="test-dep",
            replicas=5
        )
    
    @pytest.mark.asyncio
    async def test_delete_pod_tool(self, handler, mock_adapter, monkeypatch):
        monkeypatch.setattr(handler, "_get_adapter", lambda: mock_adapter)
        
        request = self.make_request(tools=[{
            "name": "k8s_delete_pod",
            "params": {"name": "test-pod", "namespace": "default"}
        }])
        
        result = await handler.handle(request)
        
        assert result.success
        mock_adapter.delete_pod.assert_called_once_with(
            name="test-pod",
            namespace="default"
        )
    
    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self, handler, mock_adapter, monkeypatch):
        monkeypatch.setattr(handler, "_get_adapter", lambda: mock_adapter)
        
        request = self.make_request(tools=[{
            "name": "k8s_unknown_tool",
            "params": {}
        }])
        
        result = await handler.handle(request)
        
        # Result should contain error for unknown tool
        assert "Unknown tool" in result.structured_output["results"][0].get("error", "")
    
    @pytest.mark.asyncio
    async def test_multiple_tools_execution(self, handler, mock_adapter, monkeypatch):
        monkeypatch.setattr(handler, "_get_adapter", lambda: mock_adapter)
        
        request = self.make_request(tools=[
            {"name": "k8s_list_pods", "params": {"namespace": "default"}},
            {"name": "k8s_list_deployments", "params": {"namespace": "default"}},
        ])
        
        result = await handler.handle(request)
        
        assert result.success
        assert result.structured_output["total"] == 2
        assert result.structured_output["success_count"] == 2
    
    # ==================== Query Mode ====================
    
    @pytest.mark.asyncio
    async def test_query_mode_returns_help(self, handler):
        request = self.make_request(query="help")
        
        result = await handler.handle(request)
        
        assert result.success
        assert "Kubernetes Agent" in result.content["text"]
        assert "k8s_list_pods" in result.content["text"]
    
    # ==================== Error Handling ====================
    
    @pytest.mark.asyncio
    async def test_adapter_error_handling(self, handler, monkeypatch):
        mock_adapter = MagicMock()
        mock_adapter.list_pods = AsyncMock(return_value={
            "success": False,
            "error": "Connection refused",
            "code": "API_ERROR"
        })
        monkeypatch.setattr(handler, "_get_adapter", lambda: mock_adapter)
        
        request = self.make_request(tools=[{
            "name": "k8s_list_pods",
            "params": {"namespace": "default"}
        }])
        
        result = await handler.handle(request)
        
        # Should still return success (tool executed)
        # but the result should indicate failure
        assert result.structured_output["results"][0]["success"] == False
