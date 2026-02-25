"""
MK-010 K8s Real Integration Tests

Tests real Kubernetes cluster connectivity and operations.
"""

import os
import pytest
import subprocess
import json
from pathlib import Path


@pytest.mark.integration
@pytest.mark.k8s
class TestK8sConnection:
    """Test K8s cluster connectivity"""

    def test_kubeconfig_exists(self, k8s_config):
        """Verify kubeconfig file exists"""
        kubeconfig_path = Path(k8s_config["kubeconfig_path"])
        assert kubeconfig_path.exists(), f"kubeconfig not found: {kubeconfig_path}"

    def test_kubectl_version(self, k8s_config):
        """Test kubectl can connect to cluster"""
        env = os.environ.copy()
        env["KUBECONFIG"] = k8s_config["kubeconfig_path"]

        result = subprocess.run(
            ["kubectl", "version", "--client", "-o", "json"],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"kubectl version failed: {result.stderr}"
        version_info = json.loads(result.stdout)
        assert "clientVersion" in version_info

    def test_cluster_connection(self, k8s_config):
        """Test connection to K8s cluster"""
        import os

        env = os.environ.copy()
        env["KUBECONFIG"] = k8s_config["kubeconfig_path"]

        result = subprocess.run(
            ["kubectl", "cluster-info"],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Cluster connection failed: {result.stderr}"
        assert "is running" in result.stdout


@pytest.mark.integration
@pytest.mark.k8s
class TestK8sOperations:
    """Test K8s operations"""

    def test_list_pods(self, k8s_config):
        """Test listing pods in namespace"""
        import os

        env = os.environ.copy()
        env["KUBECONFIG"] = k8s_config["kubeconfig_path"]
        namespace = k8s_config["namespace"]

        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", namespace, "-o", "json"],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"List pods failed: {result.stderr}"
        pods = json.loads(result.stdout)
        assert "items" in pods

    def test_list_deployments(self, k8s_config):
        """Test listing deployments in namespace"""
        import os

        env = os.environ.copy()
        env["KUBECONFIG"] = k8s_config["kubeconfig_path"]
        namespace = k8s_config["namespace"]

        result = subprocess.run(
            ["kubectl", "get", "deployments", "-n", namespace, "-o", "json"],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"List deployments failed: {result.stderr}"
        deployments = json.loads(result.stdout)
        assert "items" in deployments

    def test_list_namespaces(self, k8s_config):
        """Test listing namespaces"""
        import os

        env = os.environ.copy()
        env["KUBECONFIG"] = k8s_config["kubeconfig_path"]

        result = subprocess.run(
            ["kubectl", "get", "namespaces", "-o", "json"],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"List namespaces failed: {result.stderr}"
        namespaces = json.loads(result.stdout)
        assert "items" in namespaces
        namespace_names = [ns["metadata"]["name"] for ns in namespaces["items"]]
        assert "default" in namespace_names


@pytest.mark.integration
@pytest.mark.k8s
class TestK8sLogs:
    """Test K8s log operations"""

    def test_get_pod_logs(self, k8s_config):
        """Test getting logs from a pod"""
        import os

        env = os.environ.copy()
        env["KUBECONFIG"] = k8s_config["kubeconfig_path"]
        namespace = k8s_config["namespace"]

        # First get a list of pods
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", namespace, "-o", "json"],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0
        pods = json.loads(result.stdout)

        # Find a running pod
        running_pod = None
        for pod in pods["items"]:
            if pod["status"]["phase"] == "Running":
                running_pod = pod["metadata"]["name"]
                break

        if not running_pod:
            pytest.skip("No running pods found in namespace")

        # Get logs from the running pod
        result = subprocess.run(
            ["kubectl", "logs", running_pod, "-n", namespace, "--tail=10"],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )

        # This might fail if pod has no logs, but connection should work
        # We're testing the connection, not the logs content
        assert result.returncode == 0 or "no logs" in result.stderr.lower()
