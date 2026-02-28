"""
NexusOps Adapters

External system adapters for Agent operations.
"""

from app.adapters.base import BaseAdapter
from app.adapters.kubernetes import KubernetesAdapter

__all__ = [
    "BaseAdapter",
    "KubernetesAdapter",
]
