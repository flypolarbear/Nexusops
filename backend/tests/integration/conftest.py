"""
MK-010 Integration Test Configuration

Loads real credentials from .env.integration file.
"""

import os
import pytest
from pathlib import Path
from dotenv import load_dotenv

# Load integration test environment variables
env_path = Path(__file__).parent.parent.parent / ".env.integration"
if env_path.exists():
    load_dotenv(env_path)


def get_env(key: str, default: str = None) -> str:
    """Get environment variable or raise error"""
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"Missing required environment variable: {key}")
    return value


def has_k8s_config() -> bool:
    """Check if K8s configuration is available"""
    kubeconfig = os.getenv("KUBECONFIG_PATH")
    if not kubeconfig:
        return False
    return Path(kubeconfig).exists()


def has_argocd_config() -> bool:
    """Check if ArgoCD configuration is available"""
    return bool(os.getenv("ARGOCD_URL") and os.getenv("ARGOCD_TOKEN"))


def has_cloudflare_config() -> bool:
    """Check if Cloudflare configuration is available"""
    return bool(os.getenv("CLOUDFLARE_API_TOKEN") and os.getenv("CLOUDFLARE_ZONE_ID"))


# K8s fixtures
@pytest.fixture(scope="session")
def k8s_config():
    """K8s configuration"""
    if not has_k8s_config():
        pytest.skip("K8s configuration not available")
    return {
        "kubeconfig_path": get_env("KUBECONFIG_PATH"),
        "namespace": os.getenv("K8S_NAMESPACE", "default"),
    }


# ArgoCD fixtures
@pytest.fixture(scope="session")
def argocd_config():
    """ArgoCD configuration"""
    if not has_argocd_config():
        pytest.skip("ArgoCD configuration not available")
    return {
        "url": get_env("ARGOCD_URL"),
        "token": get_env("ARGOCD_TOKEN"),
    }


# Cloudflare fixtures
@pytest.fixture(scope="session")
def cloudflare_config():
    """Cloudflare DNS configuration"""
    if not has_cloudflare_config():
        pytest.skip("Cloudflare configuration not available")
    return {
        "api_token": get_env("CLOUDFLARE_API_TOKEN"),
        "zone_id": get_env("CLOUDFLARE_ZONE_ID"),
    }


# Markers
def pytest_configure(config):
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "k8s: mark test as K8s integration test")
    config.addinivalue_line("markers", "argocd: mark test as ArgoCD integration test")
    config.addinivalue_line("markers", "cloudflare: mark test as Cloudflare integration test")
