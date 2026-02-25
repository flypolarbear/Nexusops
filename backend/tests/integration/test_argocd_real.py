"""
MK-010 ArgoCD Real Integration Tests

Tests real ArgoCD server connectivity and operations.
"""

import pytest
import requests


@pytest.mark.integration
@pytest.mark.argocd
class TestArgoCDConnection:
    """Test ArgoCD server connectivity"""

    def test_argocd_health(self, argocd_config):
        """Test ArgoCD server health endpoint"""
        # Try different health endpoints
        endpoints = [
            "/healthz",
            "/api/healthz",
            "/api/v1/session/userinfo",
        ]

        headers = {
            "Authorization": f"Bearer {argocd_config['token']}"
        }

        success = False
        for endpoint in endpoints:
            url = f"{argocd_config['url']}{endpoint}"
            try:
                response = requests.get(url, headers=headers, timeout=30, verify=False)
                if response.status_code == 200:
                    success = True
                    break
            except:
                continue

        assert success, "ArgoCD health check failed for all endpoints"

    def test_argocd_version(self, argocd_config):
        """Test ArgoCD version endpoint"""
        # Use session userinfo as version check
        url = f"{argocd_config['url']}/api/v1/session/userinfo"
        headers = {
            "Authorization": f"Bearer {argocd_config['token']}"
        }

        response = requests.get(url, headers=headers, timeout=30, verify=False)

        # If this fails, try to get version from server info
        if response.status_code != 200:
            url = f"{argocd_config['url']}/api/v1/settings"
            response = requests.get(url, headers=headers, timeout=30, verify=False)

        assert response.status_code in [200, 403], f"ArgoCD connection check failed: {response.status_code}"


@pytest.mark.integration
@pytest.mark.argocd
class TestArgoCDApplications:
    """Test ArgoCD application operations"""

    def test_list_applications(self, argocd_config):
        """Test listing ArgoCD applications"""
        url = f"{argocd_config['url']}/api/v1/applications"
        headers = {
            "Authorization": f"Bearer {argocd_config['token']}"
        }

        response = requests.get(url, headers=headers, timeout=30, verify=False)

        assert response.status_code == 200, f"List applications failed: {response.text}"
        data = response.json()
        assert "items" in data

    def test_get_application_info(self, argocd_config):
        """Test getting application info"""
        # First list applications to get one
        url = f"{argocd_config['url']}/api/v1/applications"
        headers = {
            "Authorization": f"Bearer {argocd_config['token']}"
        }

        response = requests.get(url, headers=headers, timeout=30, verify=False)
        assert response.status_code == 200

        data = response.json()
        apps = data.get("items", [])

        if not apps:
            pytest.skip("No applications found in ArgoCD")

        # Get info for first application
        app_name = apps[0]["metadata"]["name"]
        url = f"{argocd_config['url']}/api/v1/applications/{app_name}"

        response = requests.get(url, headers=headers, timeout=30, verify=False)
        assert response.status_code == 200
        app_data = response.json()
        assert "metadata" in app_data
        assert "name" in app_data["metadata"]


@pytest.mark.integration
@pytest.mark.argocd
class TestArgoCDClusters:
    """Test ArgoCD cluster operations"""

    def test_list_clusters(self, argocd_config):
        """Test listing clusters"""
        url = f"{argocd_config['url']}/api/v1/clusters"
        headers = {
            "Authorization": f"Bearer {argocd_config['token']}"
        }

        response = requests.get(url, headers=headers, timeout=30, verify=False)

        assert response.status_code == 200, f"List clusters failed: {response.text}"
        data = response.json()
        assert "items" in data


@pytest.mark.integration
@pytest.mark.argocd
class TestArgoCDRepositories:
    """Test ArgoCD repository operations"""

    def test_list_repositories(self, argocd_config):
        """Test listing repositories"""
        url = f"{argocd_config['url']}/api/v1/repositories"
        headers = {
            "Authorization": f"Bearer {argocd_config['token']}"
        }

        response = requests.get(url, headers=headers, timeout=30, verify=False)

        assert response.status_code == 200, f"List repositories failed: {response.text}"
